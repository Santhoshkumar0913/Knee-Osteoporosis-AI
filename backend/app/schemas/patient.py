from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PatientCreate(BaseModel):
    name: str


class PatientResponse(BaseModel):
    id: int
    patient_code: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientWithAnalyses(PatientResponse):
    analyses_count: int
    
    class Config:
        from_attributes = True
