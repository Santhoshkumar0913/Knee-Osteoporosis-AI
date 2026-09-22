from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Patient, Analysis
from app.schemas.analysis import AnalysisCreate, AnalysisResponse, AnalysisListResponse
from app.services.storage_service import storage_service
from app.services.prediction_service import get_prediction_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_analysis_code(analysis_id: int) -> str:
    """Generate analysis code in format A0001"""
    return f"A{analysis_id:04d}"


@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    patient_id: int = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    joint_pain: str = Form(...),
    pregnancies: int = Form(...),
    # Phase 2 additional clinical fields
    menopausal_status: str = Form(None),
    smoking: str = Form(None),
    alcohol: str = Form(None),
    previous_fracture: str = Form(None),
    long_term_steroid_use: str = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create a new analysis with image upload and ML inference"""
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Validate image format
        allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        file_extension = "." + image.filename.split(".")[-1].lower() if "." in image.filename else ""
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        # Read image data
        image_data = await image.read()
        
        # Validate image size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit")
        
        # Run ML prediction
        prediction_service = get_prediction_service()
        prediction_result = prediction_service.run_analysis(
            image_data=image_data,
            age=age,
            gender=gender,
            height=height,
            weight=weight,
            joint_pain=joint_pain,
            pregnancies=pregnancies,
            menopausal_status=menopausal_status,
            smoking=smoking,
            alcohol=alcohol,
            previous_fracture=previous_fracture,
            long_term_steroid_use=long_term_steroid_use
        )
        
        # Create analysis record
        db_analysis = Analysis(
            patient_id=patient_id,
            image_path="",  # Will be set after saving image
            age=prediction_result['age'],
            gender=prediction_result['gender'],
            height=prediction_result['height'],
            weight=prediction_result['weight'],
            bmi=prediction_result['bmi'],
            joint_pain=prediction_result['joint_pain'],
            pregnancies=prediction_result['pregnancies'],
            # Phase 2 additional clinical fields
            menopausal_status=prediction_result.get('menopausal_status'),
            smoking=prediction_result.get('smoking'),
            alcohol=prediction_result.get('alcohol'),
            previous_fracture=prediction_result.get('previous_fracture'),
            long_term_steroid_use=prediction_result.get('long_term_steroid_use'),
            predicted_class=prediction_result['predicted_class'],
            predicted_diagnosis=prediction_result['predicted_diagnosis'],
            normal_probability=prediction_result['normal_probability'],
            osteopenia_probability=prediction_result['osteopenia_probability'],
            osteoporosis_probability=prediction_result['osteoporosis_probability'],
            confidence=prediction_result['confidence'],
            t_score=prediction_result['t_score'],
            t_score_lower=prediction_result['t_score_lower'],
            t_score_upper=prediction_result['t_score_upper'],
            z_score=prediction_result['z_score'],
            z_score_lower=prediction_result['z_score_lower'],
            z_score_upper=prediction_result['z_score_upper'],
            model_version=prediction_result['model_version']
        )
        
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        # Save image with analysis ID
        image_path = storage_service.save_analysis_image(
            patient_code=patient.patient_code,
            analysis_id=db_analysis.id,
            image_data=image_data,
            file_extension=file_extension
        )
        
        # Update analysis with image path
        db_analysis.image_path = image_path
        db.commit()
        db.refresh(db_analysis)
        
        logger.info(f"Analysis {db_analysis.id} created for patient {patient_id}")
        return db_analysis
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")


@router.get("/patient/{patient_id}", response_model=List[AnalysisListResponse])
async def get_patient_analyses(patient_id: int, db: Session = Depends(get_db)):
    """Get all analyses for a specific patient"""
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    analyses = db.query(Analysis).filter(
        Analysis.patient_id == patient_id
    ).order_by(Analysis.created_at.desc()).all()
    
    return analyses


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Get a specific analysis with full details"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete a specific analysis and its image"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Delete associated image
    if analysis.image_path:
        try:
            storage_service.delete_analysis_image(analysis.image_path)
        except Exception as e:
            logger.error(f"Failed to delete image {analysis.image_path}: {str(e)}")
    
    # Delete analysis
    db.delete(analysis)
    db.commit()
    
    logger.info(f"Analysis {analysis_id} deleted")
    return {"message": "Analysis deleted successfully"}
