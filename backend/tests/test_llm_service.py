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
            "age": 65,
            "gender": "Female",
            "bmi": 22.7,
            "menopausal_status": "Post-menopausal",
            "previous_fracture": "No",
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
        self.assertIn("The JSON \"explanation\" value must contain only the additional RAG-grounded interpretation", prompt)
        self.assertIn("Do not repeat the prediction/class, either score value", prompt)
        self.assertIn("refer to perimenopausal status only if the saved context says perimenopausal", prompt)
        self.assertIn("refer to a history of fracture only if the saved context says a previous fracture occurred", prompt)
        self.assertIn("careful interpretation of the model estimates and further assessment of fracture risk", prompt)
        self.assertIn("Age (years): 65", prompt)
        self.assertIn("Menopausal status: Post-menopausal", prompt)
        self.assertIn("Do not include source names or publication years in the explanation", prompt)

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

        self.assertIn("The DINOv2 image model predicted Osteopenia", result["explanation"])
        self.assertIn("The application's model-estimated T-score is -1.74", result["explanation"])
        self.assertIn("model-estimated Z-score is -1.71", result["explanation"])
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

    def test_rag_interpretation_can_discuss_confirmatory_dxa_without_repeating_estimates(self):
        result = self.service._parse_clinical_support_response(
            """{"explanation":"A clinician may discuss DXA testing separately if clinically appropriate."}""",
            self.retrieved_chunks,
            self.analysis_context,
        )

        self.assertIn("DXA testing separately", result["explanation"])
        self.assertEqual(result["explanation"].lower().count("model-estimated t-score"), 1)

    def test_analysis_context_is_added_as_explicit_distinct_summary(self):
        result = self.service._parse_clinical_support_response(
            '{"explanation":"Retrieved guidance explains that T-score categories are used with measured BMD only in relevant adult populations, so the application estimate requires clinical interpretation and is not a measured diagnosis."}',
            self.retrieved_chunks,
            self.analysis_context,
        )

        explanation = result["explanation"]
        self.assertIn("The DINOv2 image model predicted Osteopenia.", explanation)
        self.assertIn("The application's model-estimated T-score is -1.74", explanation)
        self.assertIn("model-estimated Z-score is -1.71", explanation)
        self.assertIn("Retrieved guidance explains that T-score categories are used with measured BMD", explanation)
        self.assertIn("the application estimate requires clinical interpretation", explanation)
        self.assertEqual(explanation.lower().count("model-estimated t-score"), 1)
        self.assertEqual(explanation.lower().count("model-estimated z-score"), 1)
        self.assertEqual(explanation.count("DINOv2"), 1)
        self.assertGreaterEqual(len(explanation.split()), 60)
        self.assertLessEqual(len(explanation.split()), 100)
        self.assertEqual(len(explanation.split(". ")), 3)

    def test_younger_patient_interpretation_uses_retrieved_age_limitation(self):
        context = {
            **self.analysis_context,
            "predicted_diagnosis": "Normal",
            "predicted_class": 0,
            "t_score": -0.73,
            "z_score": -1.62,
            "age": 35,
            "menopausal_status": "Pre-menopausal",
        }
        chunks = [{
            "organization": "BHOF",
            "publication_year": 2022,
            "chunk_text": "Premenopausal women and men less than 50 years of age should be assessed with an age-matched reference population (Z-score).",
        }]
        result = self.service._parse_clinical_support_response(
            '{"explanation":"The retrieved guidance identifies age-matched reference interpretation as relevant for premenopausal adults, so standard adult T-score categories alone should not be used to diagnose a younger patient."}',
            chunks,
            context,
            query="Age: 35 years. Gender: Female. Menopausal status: Pre-menopausal.",
        )

        explanation = result["explanation"]
        self.assertIn("The DINOv2 image model predicted Normal.", explanation)
        self.assertIn("age-matched reference interpretation", explanation)
        self.assertIn("standard adult T-score categories alone should not be used", explanation)
        self.assertEqual(explanation.count("DINOv2"), 1)
        self.assertEqual(explanation.count("-0.73"), 1)
        self.assertEqual(explanation.count("-1.62"), 1)
        self.assertNotIn("BHOF", explanation)

    def test_younger_patient_interpretation_does_not_repeat_score_or_overstate_evidence(self):
        context = {
            **self.analysis_context,
            "predicted_diagnosis": "Normal",
            "predicted_class": 1,
            "t_score": -0.73,
            "z_score": -1.62,
            "age": 19,
            "gender": "Male",
            "menopausal_status": "Not applicable",
        }
        chunks = [{
            "organization": "Synthetic guidance",
            "publication_year": "synthetic",
            "chunk_text": (
                "Standard adult T-score categories should not be applied alone to younger patients; "
                "Z-score interpretation is relevant to younger populations where applicable."
            ),
        }]
        generated = (
            '{"explanation":"The model-estimated Z-score of -1.62 suggests considering '
            'age-appropriate interpretation, as standard adult T-score categories are not '
            'validated for this 19-year-old; further clinical evaluation is needed."}'
        )

        result = self.service._parse_clinical_support_response(
            generated,
            chunks,
            context,
            query="Age: 19. Gender: Male. Menopausal status: Not applicable.",
        )
        explanation = result["explanation"]

        self.assertEqual(explanation.count("The DINOv2 image model predicted Normal."), 1)
        self.assertEqual(explanation.lower().count("model-estimated t-score"), 1)
        self.assertEqual(explanation.lower().count("model-estimated z-score"), 1)
        self.assertEqual(explanation.count("-0.73"), 1)
        self.assertEqual(explanation.count("-1.62"), 1)
        self.assertIn("standard adult categories should not be used alone", explanation)
        self.assertIn("age-appropriate clinical interpretation is important", explanation)
        self.assertNotIn("not validated", explanation.lower())

    def test_perimenopausal_fracture_interpretation_uses_saved_context_and_retrieved_evidence(self):
        context = {
            **self.analysis_context,
            "predicted_diagnosis": "Normal",
            "predicted_class": 1,
            "t_score": -0.73,
            "z_score": -1.62,
            "age": 52,
            "menopausal_status": "Perimenopausal",
            "previous_fracture": "Yes",
        }
        chunks = [{
            "organization": "Synthetic guidance",
            "publication_year": "synthetic",
            "chunk_text": (
                "For perimenopausal adults with a previous fracture, guidance supports careful clinical "
                "interpretation, assessment of fracture risk, and evaluation of possible underlying causes."
            ),
        }]
        generated = json.dumps({
            "explanation": "Retrieved guidance is relevant to the supplied context.",
            "what_you_can_do_now": ["Keep this recommendation."],
            "talk_to_your_doctor_about": ["Keep this discussion topic."],
            "testing_and_follow_up": ["Keep this follow-up item."],
            "treatment_information": [],
        })

        result = self.service._parse_clinical_support_response(
            generated,
            chunks,
            context,
            query="Menopausal status: Perimenopausal. Previous fracture: Yes.",
        )
        explanation = result["explanation"]

        self.assertIn("perimenopausal status and history of fracture", explanation)
        self.assertIn("retrieved guidance supports careful clinical interpretation of the model estimates", explanation)
        self.assertIn("further assessment of fracture risk and possible underlying causes", explanation)
        self.assertEqual(explanation.count("The DINOv2 image model predicted Normal."), 1)
        self.assertEqual(explanation.count("-0.73"), 1)
        self.assertEqual(explanation.count("-1.62"), 1)
        self.assertEqual(result["what_you_can_do_now"], ["Keep this recommendation."])
        self.assertEqual(result["talk_to_your_doctor_about"], ["Keep this discussion topic."])
        self.assertEqual(result["testing_and_follow_up"], ["Keep this follow-up item."])
        self.assertEqual(result["treatment_information"], [])
        self.assertEqual(result["sources"], self.service._build_sources(chunks))

    def test_perimenopausal_status_and_fracture_history_are_not_inferred(self):
        context = {
            **self.analysis_context,
            "menopausal_status": "Post-menopausal",
            "previous_fracture": "No",
        }
        chunks = [{
            "organization": "Synthetic guidance",
            "publication_year": "synthetic",
            "chunk_text": (
                "Assessment of fracture risk and possible underlying causes can be relevant in clinical guidance."
            ),
        }]
        generated = json.dumps({
            "explanation": (
                "Because the patient is perimenopausal and has a history of fracture, "
                "the retrieved guidance supports further assessment."
            ),
            "what_you_can_do_now": ["Preserve this existing section."],
        })

        result = self.service._parse_clinical_support_response(
            generated,
            chunks,
            context,
            query="Menopausal status: Post-menopausal. Previous fracture: No.",
        )

        self.assertNotIn("perimenopaus", result["explanation"].lower())
        self.assertNotIn("history of fracture", result["explanation"].lower())
        self.assertEqual(
            result["what_you_can_do_now"], ["Preserve this existing section."]
        )

    def test_unsupported_family_history_is_removed_from_explanation_only(self):
        generated = json.dumps({
            "explanation": "The patient's family history increases concern.",
            "what_you_can_do_now": ["Detailed saved recommendation one", "Detailed saved recommendation two", "Detailed saved recommendation three", "Detailed saved recommendation four"],
            "talk_to_your_doctor_about": ["Topic one", "Topic two", "Topic three", "Topic four"],
            "testing_and_follow_up": ["Test one", "Test two", "Test three", "Test four"],
            "treatment_information": ["Treatment one", "Treatment two", "Treatment three"],
        })
        result = self.service._parse_clinical_support_response(
            generated,
            [{
                "organization": "BHOF",
                "publication_year": 2022,
                "chunk_text": "Family history is a known risk factor in general guidance.",
            }],
            self.analysis_context,
            query="Age: 65 years. Gender: Female.",
        )

        self.assertNotIn("family history", result["explanation"].lower())
        self.assertEqual(len(result["what_you_can_do_now"]), 4)
        self.assertEqual(len(result["talk_to_your_doctor_about"]), 4)
        self.assertEqual(len(result["testing_and_follow_up"]), 4)
        self.assertEqual(len(result["treatment_information"]), 3)

    def test_patient_is_not_described_as_having_or_diagnosed_with_osteopenia(self):
        for claim in (
            "The patient has Osteopenia.",
            "The patient is having Osteoporosis.",
            "The patient was diagnosed with Osteopenia.",
            "The patient was diagnosed with Osteoporosis.",
        ):
            with self.subTest(claim=claim):
                result = self.service._parse_clinical_support_response(
                    json.dumps({"explanation": claim}),
                    self.retrieved_chunks,
                    self.analysis_context,
                )
                self.assertNotIn(claim, result["explanation"])
                self.assertIn("The DINOv2 image model predicted Osteopenia", result["explanation"])

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
