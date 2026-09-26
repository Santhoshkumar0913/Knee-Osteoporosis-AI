import json
import unittest

from app.rag.llm_service import DISCLAIMER, GROUNDING_NOTE, OpenRouterService
from app.rag.query_builder import QueryBuilder


class ClinicalSupportParserTests(unittest.TestCase):
    def setUp(self):
        self.service = OpenRouterService()
        self.retrieved_chunks = [
            {
                "organization": "BHOF",
                "publication_year": 2022,
                "chunk_text": "Retrieved evidence",
            },
            {
                "organization": "BHOF",
                "publication_year": 2022,
                "chunk_text": "Duplicate source metadata",
            },
            {
                "organization": "WHO",
                "publication_year": 2024,
                "chunk_text": "Second retrieved source",
            },
        ]
        self.analysis_context = {
            "predicted_class": 2,
            "predicted_diagnosis": "Osteopenia",
            "t_score": -1.74,
            "z_score": -1.71,
        }

    def test_valid_structured_json_populates_all_sections(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"Explanation",'
            '"what_you_can_do_now":["Action"],'
            '"talk_to_your_doctor_about":["Doctor topic"],'
            '"testing_and_follow_up":["Follow up"],'
            '"treatment_information":["Treatment"]}',
            self.retrieved_chunks,
        )

        self.assertEqual(result["explanation"], "Explanation")
        self.assertEqual(result["what_you_can_do_now"], ["Action"])
        self.assertEqual(result["talk_to_your_doctor_about"], ["Doctor topic"])
        self.assertEqual(result["testing_and_follow_up"], ["Follow up"])
        self.assertEqual(result["treatment_information"], ["Treatment"])
        self.assertEqual(
            result["sources"],
            [
                {"organization": "BHOF", "year": 2022},
                {"organization": "WHO", "year": 2024},
            ],
        )
        self.assertEqual(result["grounding_note"], GROUNDING_NOTE)
        self.assertEqual(result["disclaimer"], DISCLAIMER)

    def test_partial_json_defaults_missing_sections_safely(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"Partial explanation",'
            '"what_you_can_do_now":["One action"]}',
            self.retrieved_chunks,
        )

        self.assertEqual(result["explanation"], "Partial explanation")
        self.assertEqual(result["what_you_can_do_now"], ["One action"])
        self.assertEqual(result["talk_to_your_doctor_about"], [])
        self.assertEqual(result["testing_and_follow_up"], [])
        self.assertEqual(result["treatment_information"], [])
        self.assertEqual(len(result["sources"]), 2)

    def test_malformed_json_returns_safe_structured_response(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"Incomplete"',
            self.retrieved_chunks,
        )

        self.assertEqual(result["explanation"], '{"explanation":"Incomplete"')
        for field in (
            "what_you_can_do_now",
            "talk_to_your_doctor_about",
            "testing_and_follow_up",
            "treatment_information",
        ):
            self.assertEqual(result[field], [])
        self.assertEqual(result["sources"][0]["organization"], "BHOF")

    def test_empty_and_null_responses_do_not_crash(self):
        for generated_text in (None, "", "   "):
            with self.subTest(generated_text=generated_text):
                result = self.service._parse_clinical_support_response(
                    generated_text,
                    self.retrieved_chunks,
                )
                self.assertEqual(
                    result["explanation"],
                    "No structured explanation was provided.",
                )
                self.assertEqual(len(result["sources"]), 2)

    def test_unexpected_field_types_are_normalized_and_sources_are_grounded(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":42,'
            '"what_you_can_do_now":"not a list",'
            '"talk_to_your_doctor_about":["valid", 4, "", null],'
            '"testing_and_follow_up":{"unexpected":"object"},'
            '"treatment_information":[true, "kept"],'
            '"sources":[{"organization":"Invented","year":1900}]}',
            self.retrieved_chunks,
        )

        self.assertEqual(result["explanation"], '{"explanation":42,'
                         '"what_you_can_do_now":"not a list",'
                         '"talk_to_your_doctor_about":["valid", 4, "", null],'
                         '"testing_and_follow_up":{"unexpected":"object"},'
                         '"treatment_information":[true, "kept"],'
                         '"sources":[{"organization":"Invented","year":1900}]}')
        self.assertEqual(result["what_you_can_do_now"], [])
        self.assertEqual(result["talk_to_your_doctor_about"], ["valid"])
        self.assertEqual(result["testing_and_follow_up"], [])
        self.assertEqual(result["treatment_information"], ["kept"])
        self.assertNotIn("Invented", str(result["sources"]))

    def test_prompt_keeps_prediction_estimates_and_retrieved_evidence_distinct(self):
        prompt = self.service._build_clinical_support_prompt(
            query="DINOv2 image-model prediction: Osteopenia",
            evidence_context="Retrieved guidance excerpt",
            analysis_context=self.analysis_context,
        )

        self.assertIn("DINOv2 image-model prediction", prompt)
        self.assertIn("the application's model-estimated T-score", prompt)
        self.assertIn("the application's model-estimated Z-score", prompt)
        self.assertIn("Retrieved RAG evidence", prompt)
        self.assertIn("Do not use either score to independently diagnose, reclassify, override, or contradict", prompt)
        self.assertIn("Never describe either estimate as measured", prompt)

    def test_retrieval_query_labels_scores_as_model_estimates(self):
        query = QueryBuilder().build_retrieval_query(self.analysis_context)

        self.assertIn("DINOv2 image-model prediction (classification): Osteopenia", query)
        self.assertIn("Model-estimated T-score: -1.74", query)
        self.assertIn("Model-estimated Z-score: -1.71", query)
        self.assertNotIn(". T-score:", query)
        self.assertNotIn(". Z-score:", query)

    def test_measured_dxa_score_claim_fails_closed_to_safe_explanation(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"The measured T-score from the DXA test is -1.74."}',
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DINOv2 image model predicted Osteopenia", result["explanation"])
        self.assertIn("the application's model-estimated T-score is -1.74", result["explanation"])
        self.assertIn("the application's model-estimated Z-score is -1.71", result["explanation"])
        self.assertNotIn("DXA test is", result["explanation"])
        self.assertEqual(result["what_you_can_do_now"], [])
        self.assertEqual(result["grounding_note"], GROUNDING_NOTE)
        self.assertEqual(result["disclaimer"], DISCLAIMER)

    def test_qus_bone_density_and_laboratory_score_claims_fail_closed(self):
        unsafe_explanations = (
            "The Z-score is a QUS result.",
            "The bone density test result includes the T-score of -1.74.",
            "Laboratory measurement of the Z-score was -1.71.",
        )
        for explanation in unsafe_explanations:
            with self.subTest(explanation=explanation):
                result = self.service._parse_clinical_support_response(
                    json.dumps({"explanation": explanation}),
                    self.retrieved_chunks,
                    self.analysis_context,
                )
                self.assertIn("DINOv2 image model predicted Osteopenia", result["explanation"])
                self.assertNotIn(explanation, result["explanation"])

    def test_score_cannot_be_used_to_reclassify_prediction(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"The model-estimated T-score indicates osteoporosis."}',
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DINOv2 image model predicted Osteopenia", result["explanation"])
        self.assertNotIn("indicates osteoporosis", result["explanation"])

    def test_unsafe_score_wording_in_structured_sections_fails_closed(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"The image prediction is Osteopenia.",'
            '"treatment_information":["The measured Z-score is a QUS result."]}',
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DINOv2 image model predicted Osteopenia", result["explanation"])
        self.assertEqual(result["treatment_information"], [])

    def test_explicitly_unmeasured_estimate_and_confirmatory_dxa_discussion_is_allowed(self):
        result = self.service._parse_clinical_support_response(
            """{"explanation":"The application's model-estimated T-score is -1.74; it is not measured. A clinician may discuss DXA testing separately."}""",
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("model-estimated T-score", result["explanation"])
        self.assertIn("DXA testing separately", result["explanation"])

    def test_analysis_context_is_added_as_explicit_distinct_summary(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"Retrieved evidence provides general educational context."}',
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DINOv2 image-model prediction: Osteopenia", result["explanation"])
        self.assertIn("the application's model-estimated T-score is -1.74", result["explanation"])
        self.assertIn("the application's model-estimated Z-score is -1.71", result["explanation"])
        self.assertIn("Retrieved RAG evidence is listed in the sources", result["explanation"])
        self.assertIn("Retrieved evidence provides general educational context.", result["explanation"])

    def test_explicit_different_prediction_fails_closed(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"The predicted class is Osteoporosis."}',
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DINOv2 image model predicted Osteopenia", result["explanation"])
        self.assertNotIn("The predicted class is Osteoporosis", result["explanation"])

    def test_mock_response_uses_model_estimate_terminology(self):
        result = self.service._generate_mock_response(
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DINOv2 image model predicted Osteopenia", result["explanation"])
        self.assertIn("model-estimated T-score is -1.74", result["explanation"])
        self.assertIn("model-estimated Z-score is -1.71", result["explanation"])
        self.assertIn("not measured bone-density results", result["explanation"])

    def test_mock_response_does_not_invent_a_rag_source_when_none_was_retrieved(self):
        result = self.service._generate_mock_response([], self.analysis_context)

        self.assertEqual(result["sources"], [])
        self.assertIn("No RAG evidence was retrieved", result["explanation"])


if __name__ == "__main__":
    unittest.main()
