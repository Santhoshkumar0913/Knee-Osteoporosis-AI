"""Download a report using the Clinical Support response currently shown in the UI."""
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Analysis
from app.schemas.clinical_support import ClinicalSupportResponse
from app.services.pdf_service import generate_clinical_support_report
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{analysis_id}/clinical-support/pdf")
def download_clinical_support_pdf(
    analysis_id: int,
    clinical_support: ClinicalSupportResponse,
    db: Session = Depends(get_db),
):
    """Create and stream an in-memory PDF for the saved analysis and posted response."""
    if clinical_support.analysis_id != analysis_id:
        raise HTTPException(status_code=400, detail="Clinical Support does not match this analysis")

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    patient = analysis.patient
    if not patient or not patient.patient_code or not analysis.image_path:
        raise HTTPException(status_code=404, detail="Analysis image or patient was not found")

    try:
        image_path = storage_service.resolve_analysis_image_path(
            analysis.image_path,
            patient.patient_code,
            analysis.id,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Analysis image was not found")

    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis image was not found")

    try:
        pdf_bytes = generate_clinical_support_report(
            analysis=analysis,
            patient=patient,
            clinical_support=clinical_support,
            image_path=image_path,
        )
    except Exception as exc:
        logger.exception("Failed to generate Clinical Support PDF for analysis %s", analysis_id)
        raise HTTPException(status_code=500, detail="Failed to generate Clinical Support PDF") from exc

    patient_code = re.sub(r"[^A-Za-z0-9._-]+", "_", patient.patient_code)
    filename = f"clinical_support_report_{patient_code}_{analysis_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
