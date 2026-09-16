from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String(20), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with analyses
    analyses = relationship("Analysis", back_populates="patient", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    image_path = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Clinical inputs
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)
    joint_pain = Column(String(50), nullable=False)
    pregnancies = Column(Integer, nullable=False)
    
    # DINOv2 results
    predicted_class = Column(Integer, nullable=False)
    predicted_diagnosis = Column(String(50), nullable=False)
    normal_probability = Column(Float, nullable=False)
    osteopenia_probability = Column(Float, nullable=False)
    osteoporosis_probability = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # T-score results
    t_score = Column(Float, nullable=False)
    t_score_lower = Column(Float, nullable=False)
    t_score_upper = Column(Float, nullable=False)
    
    # Z-score results
    z_score = Column(Float, nullable=False)
    z_score_lower = Column(Float, nullable=False)
    z_score_upper = Column(Float, nullable=False)
    
    # Model version
    model_version = Column(String(50), nullable=False)
    
    # Relationship with patient
    patient = relationship("Patient", back_populates="analyses")
