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
        prompt = f"""Provide evidence-based clinical support using the patient case and retrieved medical evidence below. Keep these four information sources distinct:

1. DINOv2 image-model prediction: {analysis_context.get('predicted_diagnosis', 'Unknown')} (predicted class {analysis_context.get('predicted_class', 'Unknown')}). Report this class as given.
2. The application's model-estimated T-score: {analysis_context.get('t_score', 'Unknown')} (model estimate, not a measurement).
3. The application's model-estimated Z-score: {analysis_context.get('z_score', 'Unknown')} (model estimate, not a measurement).
4. Retrieved RAG evidence: the source excerpts below. Use these as evidence, not as patient test results.

The DINOv2 image-model prediction is the application's predicted class. Do not use either score to independently diagnose, reclassify, override, or contradict that prediction. Do not infer a diagnosis or severity category from either score. When mentioning either score, explicitly call it "the application's model-estimated T-score" or "the application's model-estimated Z-score" (or say "the model estimated ..."). Never describe either estimate as measured, as a DXA or QUS result, as a bone-density test result, or as a laboratory measurement. Do not imply that this application measured bone density.

The explanation must explicitly distinguish the supplied DINOv2 prediction, both model-estimated scores, and the retrieved RAG evidence. Name each score using the model-estimated terminology above.

PATIENT CASE:
{query}

RETRIEVED EVIDENCE:
{evidence_context}

INSTRUCTIONS:
1. Explain the DINOv2 image-model prediction separately from both model-estimated scores and retrieved evidence.
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
            response["explanation"] = self._prepend_analysis_summary(
                response["explanation"],
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
        evidence_summary = (
            "Retrieved RAG evidence is listed in the sources and provides the evidence context for the guidance below."
            if retrieved_chunks
            else "No RAG evidence was retrieved for this response."
        )
        summary = (
            f"DINOv2 image-model prediction: {diagnosis}. Separately, the application's "
            f"model-estimated T-score is {t_score}, and the application's model-estimated "
            f"Z-score is {z_score}. These values are model estimates, not measured "
            "bone-density results, and neither score independently changes or overrides "
            f"the DINOv2 prediction. {evidence_summary} "
        )
        return summary + explanation.strip()

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
            "Retrieved RAG evidence is listed in the sources."
            if retrieved_chunks
            else "No RAG evidence was retrieved for this response."
        )
        explanation = (
            f"The DINOv2 image model predicted {diagnosis}. Separately, the application's "
            f"model-estimated T-score is {t_score}, and the application's model-estimated "
            f"Z-score is {z_score}. These are model estimates; they are not measured "
            "bone-density results and do not independently change or override the DINOv2 "
            f"prediction. {evidence_summary} It does not replace the image-model prediction."
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
            "Retrieved RAG evidence is listed in the sources and is separate from the image-model prediction and score estimates."
            if sources
            else "No RAG evidence was retrieved for this response."
        )
        
        return {
            "explanation": (
                f"The DINOv2 image model predicted {diagnosis}. Separately, the application's "
                f"model-estimated T-score is {t_score:.2f}, and the application's "
                f"model-estimated Z-score is {z_score:.2f}. These are model estimates from "
                "the application's clinical models, not measured bone-density results, and "
                "they do not independently change or override the DINOv2 prediction. "
                f"{evidence_summary} The displayed ranges represent "
                "empirical prediction-error margins."
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
