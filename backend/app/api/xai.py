"""On-demand, research-only Grad-CAM visualization for a saved analysis."""
import base64
import logging
from io import BytesIO

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Analysis
from app.services.image_model import get_dinov2_model
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()

EXPLANATION_NOTE = (
    "Grad-CAM visualization showing image regions that contributed to the model's selected prediction."
)
RESEARCH_ONLY_WARNING = (
    "This visualization is for research/explainability purposes only and is not a confirmed anatomical disease localization."
)


def _make_overlay(original: Image.Image, heatmap: np.ndarray) -> str:
    """Color and blend the complete, unmasked CAM with the original image."""
    if heatmap.ndim != 2 or not np.isfinite(heatmap).all():
        raise ValueError("Grad-CAM returned an invalid heatmap")

    grayscale = Image.fromarray((np.clip(heatmap, 0.0, 1.0) * 255).astype(np.uint8))
    grayscale = grayscale.resize(original.size, Image.Resampling.BILINEAR)
    values = np.asarray(grayscale, dtype=np.float32) / 255.0

    red = np.clip(1.5 - np.abs(4.0 * values - 3.0), 0.0, 1.0)
    green = np.clip(1.5 - np.abs(4.0 * values - 2.0), 0.0, 1.0)
    blue = np.clip(1.5 - np.abs(4.0 * values - 1.0), 0.0, 1.0)
    colors = np.stack((red, green, blue), axis=-1)
    colored_heatmap = Image.fromarray((colors * 255).astype(np.uint8))
    overlay = Image.blend(original, colored_heatmap, alpha=0.4)

    image_buffer = BytesIO()
    overlay.save(image_buffer, format="PNG")
    encoded_image = base64.b64encode(image_buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


@router.get("/{analysis_id}/xai")
def get_analysis_xai(analysis_id: int, db: Session = Depends(get_db)):
    """Generate an experimental overlay for the saved analysis image on demand."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if not analysis.image_path or not analysis.patient or not analysis.patient.patient_code:
        raise HTTPException(status_code=404, detail="Analysis image not found")

    try:
        image_path = storage_service.resolve_analysis_image_path(
            analysis.image_path,
            analysis.patient.patient_code,
            analysis.id,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Analysis image not found")

    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis image not found")

    try:
        with Image.open(image_path) as source:
            original_image = source.convert("RGB")

        gradcam = get_dinov2_model().generate_gradcam(original_image)
        predicted_class = int(gradcam["predicted_class"])
        if predicted_class != int(analysis.predicted_class):
            raise HTTPException(
                status_code=409,
                detail="Grad-CAM prediction does not match the saved analysis prediction",
            )

        overlay_data_url = _make_overlay(original_image, np.asarray(gradcam["heatmap"]))
    except HTTPException:
        raise
    except (OSError, UnidentifiedImageError, KeyError, TypeError, ValueError) as exc:
        logger.exception("Invalid image or Grad-CAM result for analysis %s", analysis_id)
        raise HTTPException(status_code=500, detail="Failed to generate Grad-CAM visualization") from exc
    except Exception as exc:
        logger.exception("Grad-CAM generation failed for analysis %s", analysis_id)
        raise HTTPException(status_code=500, detail="Failed to generate Grad-CAM visualization") from exc

    return {
        "analysis_id": analysis_id,
        "predicted_class": predicted_class,
        "predicted_diagnosis": gradcam.get("predicted_diagnosis", analysis.predicted_diagnosis),
        "confidence": float(gradcam["confidence"]),
        "explanation_note": EXPLANATION_NOTE,
        "research_only_warning": RESEARCH_ONLY_WARNING,
        "overlay_image_data_url": overlay_data_url,
    }
