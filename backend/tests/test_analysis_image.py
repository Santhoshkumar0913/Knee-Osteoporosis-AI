import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException

from app.api.analyses import get_analysis_image
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


class AnalysisImageEndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.original_storage_path = storage_service.storage_path
        storage_service.storage_path = self.project_root / "storage" / "uploads"
        self.storage_path.mkdir(parents=True)
        self.patient_code = "P0001"
        self.analysis_id = 7
        self.patient_dir = self.storage_path / self.patient_code
        self.patient_dir.mkdir()

    def tearDown(self):
        storage_service.storage_path = self.original_storage_path
        self.temp_dir.cleanup()

    @property
    def storage_path(self):
        return self.project_root / "storage" / "uploads"

    def analysis(self, image_path="storage/uploads/P0001/7_xray.png"):
        return SimpleNamespace(
            id=self.analysis_id,
            image_path=image_path,
            patient=SimpleNamespace(patient_code=self.patient_code),
        )

    def test_serves_supported_image_types_with_correct_media_type(self):
        for extension, media_type in (
            (".png", "image/png"),
            (".jpg", "image/jpeg"),
            (".jpeg", "image/jpeg"),
            (".webp", "image/webp"),
        ):
            with self.subTest(extension=extension):
                expected_path = self.patient_dir / f"7_xray{extension}"
                expected_path.write_bytes(b"image bytes")
                relative_path = f"storage/uploads/P0001/7_xray{extension}"

                response = get_analysis_image(
                    self.analysis_id,
                    FakeSession(self.analysis(image_path=relative_path)),
                )

                self.assertEqual(Path(response.path).resolve(), expected_path.resolve())
                self.assertEqual(response.media_type, media_type)

    def test_missing_analysis_returns_404(self):
        with self.assertRaises(HTTPException) as raised:
            get_analysis_image(self.analysis_id, FakeSession(None))

        self.assertEqual(raised.exception.status_code, 404)

    def test_missing_image_path_returns_404(self):
        analysis = self.analysis(image_path="")

        with self.assertRaises(HTTPException) as raised:
            get_analysis_image(self.analysis_id, FakeSession(analysis))

        self.assertEqual(raised.exception.status_code, 404)

    def test_missing_image_file_returns_404(self):
        with self.assertRaises(HTTPException) as raised:
            get_analysis_image(self.analysis_id, FakeSession(self.analysis()))

        self.assertEqual(raised.exception.status_code, 404)

    def test_unsupported_image_type_returns_415(self):
        analysis = self.analysis(image_path="storage/uploads/P0001/7_xray.gif")

        with self.assertRaises(HTTPException) as raised:
            get_analysis_image(self.analysis_id, FakeSession(analysis))

        self.assertEqual(raised.exception.status_code, 415)

    def test_path_traversal_is_rejected(self):
        analysis = self.analysis(
            image_path="storage/uploads/P0001/../../../../outside/7_xray.png"
        )

        with self.assertRaises(HTTPException) as raised:
            get_analysis_image(self.analysis_id, FakeSession(analysis))

        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
