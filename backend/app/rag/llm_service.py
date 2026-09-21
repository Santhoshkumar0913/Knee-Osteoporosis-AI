"""
OpenRouter LLM service for clinical support generation
"""
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


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
                            "content": "You are a helpful medical assistant providing evidence-based information about osteoporosis. Always base your responses on the provided evidence. Do not invent facts, citations, or medical advice. Do not prescribe medications or dosages. Always recommend consulting a doctor for medical decisions."
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
                        
                        return self._parse_clinical_support_response(generated_text, retrieved_chunks)
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
        prompt = f"""
Based on the following patient case and retrieved medical evidence, provide evidence-based clinical support:

PATIENT CASE:
{query}

RETRIEVED EVIDENCE:
{evidence_context}

INSTRUCTIONS:
1. Explain the prediction in simple, patient-friendly language
2. Provide specific "What you can do now" recommendations
3. List topics to "Talk to your doctor about"
4. Include "Testing and follow-up considerations" if relevant
5. Mention treatment information only if supported by the evidence
6. Do not invent citations or evidence not present in the retrieved context
7. Do not prescribe medications or dosages
8. Always recommend consulting a doctor for medical decisions
9. If evidence is insufficient, provide general educational information but clearly identify it as such

Provide your response in a structured format that can be easily parsed into JSON sections:
- explanation
- what_you_can_do_now
- talk_to_your_doctor_about
- testing_and_follow_up
- treatment_information (only if supported by evidence)
"""
        return prompt
    
    def _parse_clinical_support_response(
        self,
        generated_text: str,
        retrieved_chunks: list
    ) -> Dict[str, Any]:
        """Parse the generated response into structured format"""
        # For MVP, we'll return the raw text and let the frontend handle display
        # In production, this would parse the structured response
        
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
        
        return {
            "explanation": generated_text,
            "what_you_can_do_now": [],
            "talk_to_your_doctor_about": [],
            "testing_and_follow_up": [],
            "treatment_information": [],
            "sources": sources,
            "grounding_note": "This response is based on retrieved medical evidence and the analysis results.",
            "disclaimer": "AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor."
        }
    
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
        
        return {
            "explanation": f"Based on your analysis, the model predicted a diagnosis of {diagnosis}. Your estimated T-score is {t_score:.2f} and Z-score is {z_score:.2f}. These scores are estimates based on the ML model and clinical inputs, not measured DXA/QUS values. The ranges provided represent empirical prediction-error margins.",
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
            "sources": sources if sources else [{"organization": "BHOF", "year": 2023}],
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