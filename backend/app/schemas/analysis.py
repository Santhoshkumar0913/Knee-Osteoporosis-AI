from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AnalysisCreate(BaseModel):
    patient_id: int
    age: int
    gender: str
    height: float
    weight: float
    joint_pain: str
    pregnancies: int


class AnalysisResponse(BaseModel):
    id: int
    patient_id: int
    image_path: str
    created_at: datetime
    
    # Clinical inputs
    age: int
    gender: str
    height: float
    weight: float
    bmi: float
    joint_pain: str
    pregnancies: int
    
    # DINOv2 results
    predicted_class: int
    predicted_diagnosis: str
    normal_probability: float
    osteopenia_probability: float
    osteoporosis_probability: float
    confidence: float
    
    # T-score results
    t_score: float
    t_score_lower: float
    t_score_upper: float
    
    # Z-score results
    z_score: float
    z_score_lower: float
    z_score_upper: float
    
    # Model version
    model_version: str
    
    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    id: int
    patient_id: int
    created_at: datetime
    predicted_diagnosis: str
    confidence: float
    t_score: float
    z_score: float
    
    class Config:
        from_attributes = True
