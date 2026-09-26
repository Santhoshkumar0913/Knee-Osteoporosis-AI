from io import BytesIO
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pypdf import PdfReader
from PIL import Image as PILImage

from app.api.clinical_support_pdf import download_clinical_support_pdf
from app.schemas.clinical_support import ClinicalSupportResponse
from app.services.pdf_service import generate_clinical_support_report


class PdfReportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image_path = Path(self.temp_dir.name) / "original_xray.png"
        PILImage.new("L", (16, 20), color=80).save(self.image_path)

        self.patient = SimpleNamespace(
            id=7,
            patient_code="P0007",
            name="Example Patient",
        )
        self.analysis = SimpleNamespace(
            id=31,
            patient_id=7,
            image_path="unused_for_service_test.png",
            created_at=datetime(2026, 9, 26, 9, 30, tzinfo=timezone.utc),
            age=45,
            gender="Female",
            height=1.73,
            weight=68.0,
            bmi=22.7,
            joint_pain="Yes",
            pregnancies=0,
            menopausal_status="Not applicable",
            smoking="No",
            alcohol="No",
            previous_fracture="No",
            long_term_steroid_use="No",
            predicted_class=2,
            predicted_diagnosis="Osteopenia",
            confidence=0.724,
            normal_probability=0.113,
            osteopenia_probability=0.724,
            osteoporosis_probability=0.163,
            t_score=-1.74,
            t_score_lower=-2.11,
            t_score_upper=-1.37,
            z_score=-1.71,
            z_score_lower=-2.93,
            z_score_upper=-0.49,
        )
        self.analysis.patient = self.patient
        self.support = ClinicalSupportResponse(
            analysis_id=31,
            prediction_summary={
                "class": "Osteopenia",
                "confidence": 0.724,
                "t_score": -1.74,
                "t_score_lower": -2.11,
                "t_score_upper": -1.37,
                "z_score": -1.71,
                "z_score_lower": -2.93,
                "z_score_upper": -0.49,
            },
            explanation="Current displayed explanation from the Clinical Support response.",
            what_you_can_do_now=["Discuss bone health with your clinician."],
            talk_to_your_doctor_about=["Ask about appropriate follow-up."],
            testing_and_follow_up=["Discuss testing with your clinician."],
            treatment_information=["Treatment decisions depend on clinical evaluation."],
            sources=[{"organization": "BHOF", "year": 2023}],
            grounding_note="Based on retrieved medical evidence and this analysis.",
            disclaimer=(
                "AI-assisted guidance for informational purposes. This does not replace a doctor's "
                "diagnosis or treatment decision. Discuss medical decisions with your doctor."
            ),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_report_contains_required_content_and_embedded_original_image(self):
        pdf_bytes = generate_clinical_support_report(
            self.analysis,
            self.patient,
            self.support,
            self.image_path,
        )

        reader = PdfReader(BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreaterEqual(len(reader.pages), 1)
        self.assertTrue(any(page.images for page in reader.pages), "Expected the saved X-ray to be embedded")

        required_content = (
            "Knee Osteoporosis AI",
            "Clinical Support Report",
            "Patient Information",
            "Patient ID",
            "P0007",
            "Example Patient",
            "45 years",
            "26 Sep 2026",
            "Clinical Context",
            "1.73 m",
            "68 kg",
            "22.7",
            "Joint Pain",
            "Number of Pregnancies",
            "Menopausal Status",
            "Smoking",
            "Alcohol",
            "Previous Fracture",
            "Long-term Steroid Use",
            "Original X-ray",
            "Model Prediction",
            "Osteopenia",
            "72.4%",
            "11.3%",
            "16.3%",
            "Model-estimated T-score",
            "-1.74",
            "-2.11 to -1.37",
            "Model-estimated Z-score",
            "-1.71",
            "-2.93 to -0.49",
            "Current displayed explanation",
            "What You Can Do Now",
            "Talk to Your Doctor About",
            "Testing and Follow-up",
            "Treatment Information",
            "BHOF",
            "2023",
            "Based on retrieved medical evidence",
            "AI-assisted guidance for informational purposes",
            "Discuss medical decisions with your doctor.",
        )
        for expected in required_content:
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        for forbidden in ("Grad-CAM", "Phone", "Email", "Address", "Dr. User", "Notification"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_missing_original_image_fails(self):
        with self.assertRaises(FileNotFoundError):
            generate_clinical_support_report(
                self.analysis,
                self.patient,
                self.support,
                Path(self.temp_dir.name) / "missing.png",
            )

    def test_pdf_endpoint_uses_posted_current_support_response(self):
        class DbStub:
            def query(_self, _model):
                return _self

            def filter(_self, _criterion):
                return _self

            def first(_self):
                return self.analysis

        with patch(
            "app.api.clinical_support_pdf.storage_service.resolve_analysis_image_path",
            return_value=self.image_path,
        ):
            response = download_clinical_support_pdf(31, self.support, DbStub())

        self.assertEqual(response.media_type, "application/pdf")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(
            response.headers["content-disposition"],
            'attachment; filename="clinical_support_report_P0007_31.pdf"',
        )
        response_text = "\n".join(
            page.extract_text() or ""
            for page in PdfReader(BytesIO(response.body)).pages
        )
        self.assertIn("Current displayed explanation", response_text)

    def test_pdf_endpoint_rejects_support_for_another_analysis(self):
        self.support.analysis_id = 32
        with self.assertRaises(HTTPException) as error:
            download_clinical_support_pdf(31, self.support, object())

        self.assertEqual(error.exception.status_code, 400)

    def test_pdf_endpoint_returns_not_found_for_missing_analysis(self):
        class DbStub:
            def query(_self, _model):
                return _self

            def filter(_self, _criterion):
                return _self

            def first(_self):
                return None

        with self.assertRaises(HTTPException) as error:
            download_clinical_support_pdf(31, self.support, DbStub())

        self.assertEqual(error.exception.status_code, 404)

    def test_pdf_endpoint_returns_not_found_for_missing_image(self):
        class DbStub:
            def query(_self, _model):
                return _self

            def filter(_self, _criterion):
                return _self

            def first(_self):
                return self.analysis

        missing_image = Path(self.temp_dir.name) / "missing.png"
        with patch(
            "app.api.clinical_support_pdf.storage_service.resolve_analysis_image_path",
            return_value=missing_image,
        ):
            with self.assertRaises(HTTPException) as error:
                download_clinical_support_pdf(31, self.support, DbStub())

        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
