from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Patient, Analysis
from app.schemas.patient import PatientCreate, PatientResponse, PatientWithAnalyses
from app.services.storage_service import storage_service

router = APIRouter()


def generate_patient_code(patient_id: int) -> str:
    """Generate patient code in format P0001"""
    return f"P{patient_id:04d}"


@router.post("/", response_model=PatientResponse)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    # Check if name is provided
    if not patient.name or not patient.name.strip():
        raise HTTPException(status_code=400, detail="Patient name is required")
    
    # Create patient with temporary patient_code
    import random
    temp_code = f"TEMP{random.randint(1000, 9999)}"
    db_patient = Patient(name=patient.name.strip(), patient_code=temp_code)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    # Generate final patient code
    db_patient.patient_code = generate_patient_code(db_patient.id)
    db.commit()
    db.refresh(db_patient)
    
    return db_patient


@router.get("/", response_model=List[PatientResponse])
async def get_patients(db: Session = Depends(get_db)):
    """Get all patients"""
    patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
    return patients


@router.get("/{patient_id}", response_model=PatientWithAnalyses)
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get a specific patient with analysis count"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Count analyses
    analyses_count = db.query(Analysis).filter(Analysis.patient_id == patient_id).count()
    
    return PatientWithAnalyses(
        id=patient.id,
        patient_code=patient.patient_code,
        name=patient.name,
        created_at=patient.created_at,
        analyses_count=analyses_count
    )


@router.delete("/{patient_id}")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Delete a patient and all associated analyses and images"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get all analyses for this patient
    analyses = db.query(Analysis).filter(Analysis.patient_id == patient_id).all()
    
    # Delete associated images
    for analysis in analyses:
        if analysis.image_path:
            try:
                storage_service.delete_analysis_image(analysis.image_path)
            except Exception as e:
                # Log but continue with deletion
                print(f"Failed to delete image {analysis.image_path}: {str(e)}")
    
    # Delete patient (cascade will delete analyses)
    db.delete(patient)
    db.commit()
    
    # Delete patient image directory
    try:
        storage_service.delete_patient_images(patient.patient_code)
    except Exception as e:
        print(f"Failed to delete patient image directory: {str(e)}")
    
    return {"message": "Patient deleted successfully"}
