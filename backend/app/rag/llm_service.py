"""
OpenRouter LLM service for clinical support generation
"""
import logging
import httpx
import json
import re
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

GROUNDING_NOTE = "This response is based on retrieved medical evidence and the analysis results."
DISCLAIMER = "AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor."
SECTION_FIELDS = (
    "what_you_can_do_now",
    "talk_to_your_doctor_about",
    "testing_and_follow_up",
    "treatment_information",
)


class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = settings.LLM_MODEL
        self.timeout = 30.0
        self.max_retries = 2
    
    def generate_clinical_support(
        self,
        query: str,
        retrieved_chunks: list,
        analysis_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate clinical support response using OpenRouter API
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not configured, returning mock response")
            return self._generate_mock_response(retrieved_chunks, analysis_context)
        
        # Retry logic for null/empty responses
        for attempt in range(self.max_retries):
            try:
                # Build retrieved evidence context
                evidence_context = "\n\n".join([
                    f"Source: {chunk.get('organization', 'Unknown')} ({chunk.get('publication_year', 'Unknown')})\n{chunk.get('chunk_text', '')}"
                    for chunk in retrieved_chunks
                ])
                
                # Build the prompt
                prompt = self._build_clinical_support_prompt(
                    query=query,
                    evidence_context=evidence_context,
                    analysis_context=analysis_context
                )
                
                # Make API request
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "Knee Osteoporosis AI"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You provide evidence-based educational information about osteoporosis. Keep the DINOv2 image-model prediction, the application's model-estimated T-score, the application's model-estimated Z-score, and retrieved RAG evidence distinct. The given DINOv2 class is authoritative for this response: do not reclassify or contradict it based on either model-estimated score. The T-score and Z-score are model estimates only, never measured DXA/QUS, bone-density test, or laboratory results. Always base medical information on supplied evidence, do not invent facts or citations, do not prescribe medications or dosages, and recommend consulting a doctor for medical decisions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 3000  # Increased to avoid length truncation
                }
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(self.base_url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Extract the generated response with null/empty check
                    if "choices" in result and len(result["choices"]) > 0:
                        message = result["choices"][0].get("message", {})
                        generated_text = message.get("content")
                        
                        # Some models put content in 'reasoning' field instead of 'content'
                        if not generated_text or not generated_text.strip():
                            reasoning = message.get("reasoning")
                            if reasoning and reasoning.strip():
                                logger.info("Using 'reasoning' field as content (content field was null)")
                                generated_text = reasoning
                            else:
                                logger.error(f"OpenRouter returned null or empty content (attempt {attempt + 1}/{self.max_retries})")
                                if attempt < self.max_retries - 1:
                                    continue  # Retry
                                else:
                                    raise ValueError("OpenRouter returned null or empty content after retries")
                        
                        try:
                            return self._parse_clinical_support_response(
                                generated_text,
                                retrieved_chunks,
                                analysis_context,
                                query=query,
                            )
                        except ValueError as e:
                            logger.warning(f"Structured parsing failed; using a safe explanation: {e}")
                            return self._safe_score_claim_fallback(retrieved_chunks, analysis_context)
                    else:
                        raise ValueError("Invalid response format from OpenRouter")
                        
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
                raise
            except ValueError as e:
                if "null or empty content" in str(e) and attempt < self.max_retries - 1:
                    continue  # Retry on null/empty content
                raise
            except Exception as e:
                logger.error(f"Failed to generate clinical support: {str(e)}")
                raise
    
    def _build_clinical_support_prompt(
        self,
        query: str,
        evidence_context: str,
        analysis_context: Dict[str, Any]
    ) -> str:
        """Build the prompt for clinical support generation"""
        patient_context = self._format_patient_context(analysis_context)
        prompt = f"""Provide evidence-based clinical support using the patient case and retrieved medical evidence below. Keep the DINOv2 image-model prediction, the application's model-estimated scores, and retrieved RAG evidence distinct.

1. DINOv2 image-model prediction: {analysis_context.get('predicted_diagnosis', 'Unknown')} (predicted class {analysis_context.get('predicted_class', 'Unknown')}). Report this class as given.
2. The application's model-estimated T-score: {analysis_context.get('t_score', 'Unknown')} (model estimate, not a measurement).
3. The application's model-estimated Z-score: {analysis_context.get('z_score', 'Unknown')} (model estimate, not a measurement).
4. Retrieved RAG evidence: the source excerpts below. Use these as evidence, not as patient test results.

The DINOv2 image-model prediction is the application's predicted class. Do not use either score to independently diagnose, reclassify, override, or contradict that prediction. Do not infer a diagnosis or severity category from either score. When mentioning either score, explicitly call it "the application's model-estimated T-score" or "the application's model-estimated Z-score" (or say "the model estimated ..."). Never describe either estimate as measured, as a DXA or QUS result, as a bone-density test result, or as a laboratory measurement. Do not imply that this application measured bone density.

EXPLANATION FIELD:
The backend will prepend the deterministic DINOv2 prediction and model-estimated T-score/Z-score summary to your explanation. The JSON "explanation" value must contain only the additional RAG-grounded interpretation that follows that summary. Do not repeat the prediction/class, either score value, or the model-estimate/measurement clarification.

Write 1–2 sentences, preferably 25–45 words. Do not mention or repeat either score or its value in the interpretation. Use retrieved evidence to explain a relevant meaning or limitation in the context of the supplied patient's age, gender, menopausal status, BMI, previous fracture, or other context only when that field is actually supplied and the evidence supports its relevance. In particular, refer to perimenopausal status only if the saved context says perimenopausal, and refer to a history of fracture only if the saved context says a previous fracture occurred. When both are present and retrieved evidence supports assessment, connect them to careful interpretation of the model estimates and further assessment of fracture risk or possible underlying causes. If evidence says adult categories should not be used alone for younger patients, state that limitation without saying they are "not validated." Explain meaning, not a literature summary. Do not include source names or publication years in the explanation; the application displays retrieved sources separately. Avoid generic filler. If evidence does not support a meaningful patient-specific interpretation, say so briefly without speculation.

PATIENT CASE:
{query}

SAVED PATIENT CONTEXT:
{patient_context or 'No additional patient context fields were supplied.'}

RETRIEVED EVIDENCE:
{evidence_context}

INSTRUCTIONS:
1. Keep the prediction, model-estimated scores, and retrieved evidence distinct in the response. For the Explanation, follow the EXPLANATION FIELD instructions and do not repeat the backend summary.
2. Provide specific "What you can do now" recommendations
3. List topics to "Talk to your doctor about"
4. Include "Testing and follow-up considerations" if relevant
5. Mention treatment information only if supported by the evidence
6. Do not invent citations or evidence not present in the retrieved context
7. Do not prescribe medications or dosages
8. Always recommend consulting a doctor for medical decisions
9. If evidence is insufficient, provide general educational information but clearly identify it as such

Provide your response in this exact JSON format:
{{
  "explanation": "your explanation here",
  "what_you_can_do_now": ["item 1", "item 2"],
  "talk_to_your_doctor_about": ["item 1", "item 2"],
  "testing_and_follow_up": ["item 1", "item 2"],
  "treatment_information": ["item 1", "item 2"]
}}

Return ONLY valid JSON. Do not include any text outside the JSON structure."""
        return prompt
    
    def _parse_clinical_support_response(
        self,
        generated_text: str,
        retrieved_chunks: list,
        analysis_context: Optional[Dict[str, Any]] = None,
        query: str = "",
    ) -> Dict[str, Any]:
        """Parse the generated response into structured format"""
        parsed = self._extract_json_object(generated_text)
        raw_text = generated_text.strip() if isinstance(generated_text, str) else ""

        if parsed is None:
            logger.warning("No valid JSON object found in LLM response; returning safe partial response")
            parsed = {}

        explanation = parsed.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            explanation = raw_text or "No structured explanation was provided."

        response = {
            "explanation": explanation.strip(),
            **{
                field: self._normalize_string_list(parsed.get(field))
                for field in SECTION_FIELDS
            },
            "sources": self._build_sources(retrieved_chunks),
            "grounding_note": GROUNDING_NOTE,
            "disclaimer": DISCLAIMER,
        }

        response_text = " ".join(
            [response["explanation"]]
            + [item for field in SECTION_FIELDS for item in response[field]]
        )
        if (
            self._contains_unsafe_score_claim(response_text)
            or self._contradicts_prediction(response_text, analysis_context or {})
        ):
            logger.warning("Unsafe score or prediction wording in generated clinical support; using a safe explanation")
            return self._safe_score_claim_fallback(retrieved_chunks, analysis_context or {})

        if analysis_context:
            interpretation = response["explanation"]
            if self._contains_unsupported_family_history_claim(
                interpretation, query, analysis_context
            ) or self._contains_patient_diagnosis_claim(
                interpretation
            ) or self._contains_unsupported_patient_context_claim(
                interpretation, analysis_context, retrieved_chunks
            ):
                interpretation = (
                    "Retrieved evidence provides educational context; it does not establish a patient diagnosis."
                )
            elif not retrieved_chunks:
                interpretation = (
                    "No retrieved evidence supports a meaningful patient-specific interpretation."
                )
            elif self._has_perimenopausal_fracture_guidance(
                analysis_context, retrieved_chunks
            ):
                interpretation = self._build_perimenopausal_fracture_interpretation(
                    analysis_context
                )
            elif self._has_young_patient_category_guidance(
                analysis_context, retrieved_chunks
            ) and self._contains_score_reference_or_value(interpretation, analysis_context):
                interpretation = (
                    "Retrieved guidance indicates that standard adult categories should not be used alone "
                    "to diagnose younger patients, so age-appropriate clinical interpretation is important."
                )

            response["explanation"] = self._prepend_analysis_summary(
                interpretation,
                analysis_context,
                retrieved_chunks,
            )

        if parsed:
            logger.info("Successfully parsed structured LLM response")
        return response

    @staticmethod
    def _contradicts_prediction(text: str, analysis_context: Dict[str, Any]) -> bool:
        """Detect an explicit generated statement that assigns a different predicted class."""
        expected = str(analysis_context.get("predicted_diagnosis", "")).strip().lower()
        if not expected:
            return False
        prediction_claim = re.compile(
            r"\b(?:predicted(?:\s+(?:class|diagnosis))?|prediction\s+(?:is|was|of)|classified\s+as|diagnosed\s+with)"
            r"\s*(?:(?:is|was|:)\s+)?"
            r"(?:a\s+diagnosis\s+of\s+)?(normal|osteopenia|osteoporosis)\b",
            re.IGNORECASE,
        )
        return any(
            match.group(1).lower() != expected
            for match in prediction_claim.finditer(text or "")
        )

    def _prepend_analysis_summary(
        self,
        explanation: str,
        analysis_context: Dict[str, Any],
        retrieved_chunks: list,
    ) -> str:
        """Make the four evidence sources explicit using values from the saved analysis."""
        diagnosis = analysis_context.get("predicted_diagnosis", "the recorded class")
        t_score = self._format_model_estimate(analysis_context.get("t_score"))
        z_score = self._format_model_estimate(analysis_context.get("z_score"))
        summary = (
            f"The DINOv2 image model predicted {diagnosis}. The application's "
            f"model-estimated T-score is {t_score} and model-estimated Z-score is "
            f"{z_score}; these are model estimates, not measured bone-density results "
            "and do not override the image-model prediction. "
        )
        return summary + explanation.strip()

    @staticmethod
    def _has_perimenopausal_fracture_guidance(
        analysis_context: Dict[str, Any], retrieved_chunks: list
    ) -> bool:
        menopausal_status = str(analysis_context.get("menopausal_status", "")).strip().lower()
        previous_fracture = str(analysis_context.get("previous_fracture", "")).strip().lower()
        if menopausal_status not in {"perimenopausal", "peri-menopausal"} or previous_fracture != "yes":
            return False

        evidence = " ".join(
            str(chunk.get("chunk_text", "")) for chunk in retrieved_chunks or []
        ).lower()
        return all((
            re.search(r"\bfractur\w*\b", evidence),
            re.search(r"\brisk\b", evidence),
            re.search(r"\b(?:assess\w*|evaluat\w*)\b", evidence),
            re.search(r"\b(?:underlying|secondary|cause\w*)\b", evidence),
        ))

    @staticmethod
    def _build_perimenopausal_fracture_interpretation(
        analysis_context: Dict[str, Any]
    ) -> str:
        factors = []
        if str(analysis_context.get("menopausal_status", "")).strip().lower() in {
            "perimenopausal", "peri-menopausal"
        }:
            factors.append("perimenopausal status")
        if str(analysis_context.get("previous_fracture", "")).strip().lower() == "yes":
            factors.append("history of fracture")
        factor_text = " and ".join(factors)
        return (
            f"Given the saved {factor_text}, retrieved guidance supports careful clinical "
            "interpretation of the model estimates and further assessment of fracture risk "
            "and possible underlying causes."
        )

    @staticmethod
    def _contains_unsupported_patient_context_claim(
        text: str, analysis_context: Dict[str, Any], retrieved_chunks: list
    ) -> bool:
        text = text or ""
        evidence = " ".join(
            str(chunk.get("chunk_text", "")) for chunk in retrieved_chunks or []
        )
        if re.search(r"\bperi[- ]?menopaus\w*\b", text, re.IGNORECASE):
            menopausal_status = str(
                analysis_context.get("menopausal_status", "")
            ).strip().lower()
            if menopausal_status not in {"perimenopausal", "peri-menopausal"}:
                return True

        claims_fracture_history = re.search(
            r"\b(?:history of|previous|prior|past)\s+(?:a\s+)?(?:fragility\s+)?fracture\b"
            r"|\bfracture history\b",
            text,
            re.IGNORECASE,
        )
        if claims_fracture_history:
            previous_fracture = str(
                analysis_context.get("previous_fracture", "")
            ).strip().lower()
            if previous_fracture != "yes" or not re.search(
                r"\bfractur\w*\b", evidence, re.IGNORECASE
            ):
                return True
        return False

    @staticmethod
    def _has_young_patient_category_guidance(
        analysis_context: Dict[str, Any], retrieved_chunks: list
    ) -> bool:
        try:
            age = float(analysis_context.get("age"))
        except (TypeError, ValueError):
            return False
        if age >= 50:
            return False

        evidence = " ".join(
            str(chunk.get("chunk_text", "")) for chunk in retrieved_chunks or []
        ).lower()
        mentions_young_population = bool(
            re.search(r"\b(?:younger|under\s+50|less\s+than\s+50|below\s+50)\b", evidence)
        )
        mentions_t_score = bool(re.search(r"\bt[ -]?score\b", evidence))
        limits_adult_categories = bool(
            re.search(r"\b(?:alone|should not|not be|do not|avoid)\b", evidence)
        )
        return mentions_young_population and mentions_t_score and limits_adult_categories

    @classmethod
    def _contains_score_reference_or_value(
        cls, explanation: str, analysis_context: Dict[str, Any]
    ) -> bool:
        if re.search(r"\b[tz][ -]?scores?\b", explanation or "", re.IGNORECASE):
            return True
        values = (
            cls._format_model_estimate(analysis_context.get("t_score")),
            cls._format_model_estimate(analysis_context.get("z_score")),
        )
        return any(
            value != "unavailable"
            and re.search(rf"(?<!\d){re.escape(value)}(?!\d)", explanation or "")
            for value in values
        )

    @staticmethod
    def _format_patient_context(analysis_context: Dict[str, Any]) -> str:
        """Render only saved clinical fields that have meaningful supplied values."""
        fields = (
            ("Age (years)", "age"),
            ("Gender", "gender"),
            ("Height (m)", "height"),
            ("Weight (kg)", "weight"),
            ("BMI", "bmi"),
            ("Joint pain", "joint_pain"),
            ("Number of pregnancies", "pregnancies"),
            ("Menopausal status", "menopausal_status"),
            ("Smoking", "smoking"),
            ("Alcohol", "alcohol"),
            ("Previous fracture", "previous_fracture"),
            ("Long-term steroid use", "long_term_steroid_use"),
        )
        lines = []
        for label, key in fields:
            value = analysis_context.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            if isinstance(value, str) and value.strip().lower() in {"unknown", "not specified"}:
                continue
            lines.append(f"{label}: {value}")
        return "\n".join(lines)

    @staticmethod
    def _contains_unsupported_family_history_claim(
        text: str,
        query: str,
        analysis_context: Dict[str, Any],
    ) -> bool:
        if not re.search(r"\bfamily history\b", text or "", re.IGNORECASE):
            return False
        supplied_context = "\n".join(
            str(analysis_context.get(key, ""))
            for key in ("family_history", "family_history_of_osteoporosis")
        )
        return not re.search(
            r"\bfamily history\b",
            f"{query}\n{supplied_context}",
            re.IGNORECASE,
        )

    @staticmethod
    def _contains_patient_diagnosis_claim(text: str) -> bool:
        return bool(
            re.search(
                r"\b(?:the\s+)?patient\s+(?:has|have|is having|was diagnosed with|has been diagnosed with)\s+(?:a diagnosis of\s+)?(?:osteopenia|osteoporosis)\b"
                r"|\bdiagnosed with\s+(?:osteopenia|osteoporosis)\b"
                r"|\bhaving\s+(?:osteopenia|osteoporosis)\b",
                text or "",
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _contains_unsafe_score_claim(text: str) -> bool:
        """Detect direct measurement claims or score-based reclassification."""
        score = r"(?:model[- ]estimated\s+)?[tz][ -]?score"
        measurement = r"(?:measured|measurement|laboratory(?:[- ]based)?|dxa|qus|bone[- ]density test|bone density test)"
        decision = r"(?:indicates?|means?|proves?|shows?|confirms?|establishes?|classifies?|reclassifies?)"
        classes = r"(?:normal|osteopenia|osteoporosis)"

        for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
            lowered = sentence.lower()
            has_negated_measurement = bool(
                re.search(r"\b(?:not|never|isn't|aren't|wasn't|weren't)\b.{0,35}\b" + measurement, lowered)
                or re.search(r"\b" + measurement + r"\b.{0,25}\b(?:not|never)\b", lowered)
            )
            measurement_claim = (
                re.search(r"\b" + score + r"\b[^.!?]{0,80}\b" + measurement + r"\b", lowered)
                or re.search(r"\b" + measurement + r"\b[^.!?]{0,80}\b" + score + r"\b", lowered)
            )
            if measurement_claim and not has_negated_measurement:
                return True
            if re.search(r"\b" + score + r"\b[^.!?]{0,80}\b" + decision + r"\b[^.!?]{0,50}\b" + classes + r"\b", lowered):
                return True
        return False

    def _safe_score_claim_fallback(
        self,
        retrieved_chunks: list,
        analysis_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Fail closed if generated text conflates estimates with measurements or classification."""
        context = analysis_context or {}
        diagnosis = context.get("predicted_diagnosis", "the recorded class")
        t_score = self._format_model_estimate(context.get("t_score"))
        z_score = self._format_model_estimate(context.get("z_score"))
        evidence_summary = (
            "No patient-specific RAG interpretation could be safely generated; retrieved sources are listed separately."
            if retrieved_chunks
            else "No RAG evidence was retrieved, so no patient-specific evidence interpretation is available."
        )
        explanation = (
            f"The DINOv2 image model predicted {diagnosis}. The application's "
            f"model-estimated T-score is {t_score} and model-estimated Z-score is "
            f"{z_score}; these are model estimates, not measured bone-density results "
            f"and do not override the image-model prediction. {evidence_summary}"
        )
        return {
            "explanation": explanation,
            **{field: [] for field in SECTION_FIELDS},
            "sources": self._build_sources(retrieved_chunks),
            "grounding_note": GROUNDING_NOTE,
            "disclaimer": DISCLAIMER,
        }

    @staticmethod
    def _format_model_estimate(value: Any) -> str:
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "unavailable"

    @staticmethod
    def _extract_json_object(value: Any) -> Optional[Dict[str, Any]]:
        """Return the first decodable JSON object in an LLM response."""
        if not isinstance(value, str) or not value.strip():
            return None

        decoder = json.JSONDecoder()
        for index, character in enumerate(value):
            if character != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(value[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    @staticmethod
    def _normalize_string_list(value: Any) -> list[str]:
        """Keep only non-empty strings so malformed model fields cannot leak through."""
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    @staticmethod
    def _build_sources(retrieved_chunks: list) -> list[Dict[str, Any]]:
        """Build display sources exclusively from retrieved evidence metadata."""
        sources = []
        seen_sources = set()
        for chunk in retrieved_chunks or []:
            org = chunk.get("organization") or "Unknown"
            year = chunk.get("publication_year") or "Unknown"
            source_key = f"{org} — {year}"
            if source_key not in seen_sources:
                sources.append({"organization": str(org), "year": year})
                seen_sources.add(source_key)
        return sources
    
    def _generate_mock_response(
        self,
        retrieved_chunks: list,
        analysis_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a mock response for testing when API key is not configured"""
        diagnosis = analysis_context.get('predicted_diagnosis', 'Unknown')
        t_score = analysis_context.get('t_score', 0)
        z_score = analysis_context.get('z_score', 0)
        
        # Extract sources from retrieved chunks
        sources = []
        seen_sources = set()
        for chunk in retrieved_chunks:
            org = chunk.get('organization', 'Unknown')
            year = chunk.get('publication_year', 'Unknown')
            source_key = f"{org} — {year}"
            if source_key not in seen_sources:
                sources.append({"organization": org, "year": year})
                seen_sources.add(source_key)

        evidence_summary = (
            "No patient-specific RAG interpretation was generated because OpenRouter is not configured; retrieved sources are listed separately."
            if sources
            else "No RAG evidence was retrieved, so no patient-specific evidence interpretation is available."
        )
        
        return {
            "explanation": (
                f"The DINOv2 image model predicted {diagnosis}. The application's "
                f"model-estimated T-score is {t_score:.2f} and model-estimated Z-score is "
                f"{z_score:.2f}; these are model estimates, not measured bone-density "
                f"results and do not override the image-model prediction. {evidence_summary}"
            ),
            "what_you_can_do_now": [
                "Maintain a balanced diet rich in calcium and vitamin D",
                "Engage in regular weight-bearing and muscle-strengthening exercises",
                "Avoid smoking and excessive alcohol consumption",
                "Maintain a healthy body weight"
            ],
            "talk_to_your_doctor_about": [
                "Getting a bone density scan (DXA) for accurate diagnosis",
                "Reviewing your current medications that may affect bone health",
                "Discussing calcium and vitamin D supplementation",
                "Considering bone health medications if appropriate"
            ],
            "testing_and_follow_up": [
                "Regular bone density monitoring as recommended by your doctor",
                "Follow-up appointments to track bone health over time",
                "Blood tests to check calcium and vitamin D levels"
            ],
            "treatment_information": [
                "Treatment options depend on your actual bone density test results",
                "Your doctor may recommend lifestyle changes, supplements, or medications"
            ],
            "sources": sources,
            "grounding_note": "This response is based on the retrieved medical evidence and your analysis results. OpenRouter API integration is not configured.",
            "disclaimer": "AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor."
        }


# Global LLM service instance
llm_service = None


def get_llm_service():
    global llm_service
    if llm_service is None:
        llm_service = OpenRouterService()
    return llm_service
