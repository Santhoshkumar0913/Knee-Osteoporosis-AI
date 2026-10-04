import base64
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from fastapi import HTTPException
from PIL import Image

from app.api.xai import (
    EXPLANATION_NOTE,
    RESEARCH_ONLY_WARNING,
    get_analysis_xai,
)
from app.services.storage_service import storage_service


class FakeQuery:
    def __init__(self, analysis):
        self.analysis = analysis

    def filter(self, *_args):
        return self

    def first(self):
        return self.analysis


class FakeSession:
    def __init__(self, analysis):
        self.analysis = analysis

    def query(self, *_args):
        return FakeQuery(self.analysis)


class AnalysisXaiEndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.original_storage_path = storage_service.storage_path
        storage_service.storage_path = self.project_root / "storage" / "uploads"
        self.image_dir = storage_service.storage_path / "P0001"
        self.image_dir.mkdir(parents=True)
        self.image_path = self.image_dir / "7_xray.png"
        Image.new("RGB", (80, 40), (80, 100, 120)).save(self.image_path)
        self.analysis = SimpleNamespace(
            id=7,
            patient_id=2,
            patient=SimpleNamespace(patient_code="P0001"),
            image_path="storage/uploads/P0001/7_xray.png",
            predicted_class=2,
            predicted_diagnosis="Osteopenia",
        )
        self.gradcam = {
            "predicted_class": 2,
            "predicted_diagnosis": "Osteopenia",
            "confidence": 0.72,
            "heatmap": np.array([[0.0, 0.25], [0.75, 1.0]], dtype=np.float32),
        }

    def tearDown(self):
        storage_service.storage_path = self.original_storage_path
        self.temp_dir.cleanup()

    def request_xai(self, analysis=None):
        model = Mock()
        model.generate_gradcam.return_value = self.gradcam
        with patch("app.api.xai.get_dinov2_model", return_value=model):
            response = get_analysis_xai(7, FakeSession(self.analysis if analysis is None else analysis))
        return response, model

    def test_valid_analysis_generates_overlay_aligned_to_original_dimensions(self):
        response, model = self.request_xai()

        model.generate_gradcam.assert_called_once()
        self.assertEqual(response["analysis_id"], 7)
        self.assertEqual(response["predicted_class"], self.analysis.predicted_class)
        self.assertEqual(response["predicted_diagnosis"], "Osteopenia")
        self.assertAlmostEqual(response["confidence"], 0.72)

        data_url = response["overlay_image_data_url"]
        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        png_bytes = base64.b64decode(data_url.split(",", 1)[1])
        with Image.open(BytesIO(png_bytes)) as overlay:
            self.assertEqual(overlay.size, (80, 40))
            self.assertEqual(overlay.mode, "RGB")

    def test_missing_analysis_returns_404(self):
        model = Mock()
        with patch("app.api.xai.get_dinov2_model", return_value=model):
            with self.assertRaises(HTTPException) as raised:
                get_analysis_xai(7, FakeSession(None))

        self.assertEqual(raised.exception.status_code, 404)

    def test_missing_saved_image_returns_404(self):
        missing = SimpleNamespace(**{**vars(self.analysis), "image_path": ""})

        with self.assertRaises(HTTPException) as raised:
            self.request_xai(analysis=missing)

        self.assertEqual(raised.exception.status_code, 404)

    def test_missing_image_file_returns_404(self):
        self.image_path.unlink()

        with self.assertRaises(HTTPException) as raised:
            self.request_xai()

        self.assertEqual(raised.exception.status_code, 404)

    def test_path_traversal_is_rejected_before_gradcam(self):
        traversal = SimpleNamespace(
            **{
                **vars(self.analysis),
                "image_path": "storage/uploads/P0001/../../../../outside/7_xray.png",
            }
        )
        model = Mock()
        with patch("app.api.xai.get_dinov2_model", return_value=model):
            with self.assertRaises(HTTPException) as raised:
                get_analysis_xai(7, FakeSession(traversal))

        self.assertEqual(raised.exception.status_code, 404)
        model.generate_gradcam.assert_not_called()

    def test_mismatched_selected_class_returns_conflict(self):
        self.gradcam["predicted_class"] = 3
        with self.assertRaises(HTTPException) as raised:
            self.request_xai()

        self.assertEqual(raised.exception.status_code, 409)

    def test_response_contains_fixed_explanation_and_research_warning(self):
        response, _model = self.request_xai()

        self.assertEqual(response["explanation_note"], EXPLANATION_NOTE)
        self.assertEqual(response["research_only_warning"], RESEARCH_ONLY_WARNING)


if __name__ == "__main__":
    unittest.main()
