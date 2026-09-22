import unittest

from app.rag.llm_service import DISCLAIMER, GROUNDING_NOTE, OpenRouterService


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


if __name__ == "__main__":
    unittest.main()