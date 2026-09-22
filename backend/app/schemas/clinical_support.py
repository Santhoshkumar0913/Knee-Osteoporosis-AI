from pydantic import BaseModel
from typing import List, Optional


class ClinicalSupportRequest(BaseModel):
    """Request model for clinical support generation"""
    # Only analysis_id is required; context is loaded from database
    pass


class ClinicalSupportResponse(BaseModel):
    """Response model for clinical support"""
    analysis_id: int
    prediction_summary: dict
    explanation: str
    what_you_can_do_now: List[str] = []
    talk_to_your_doctor_about: List[str] = []
    testing_and_follow_up: List[str] = []
    treatment_information: List[str] = []
    sources: List[dict] = []
    grounding_note: str
    disclaimer: str