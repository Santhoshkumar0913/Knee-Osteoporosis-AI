from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Analysis
from app.schemas.clinical_support import ClinicalSupportResponse
from app.rag.query_builder import get_query_builder
from app.rag.retrieval import get_retrieval_service
from app.rag.llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{analysis_id}/clinical-support", response_model=ClinicalSupportResponse)
async def generate_clinical_support(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Generate clinical support for an analysis using RAG and LLM"""
    try:
        # Load analysis from database
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Convert analysis to dict for query building
        analysis_dict = {
            "id": analysis.id,
            "patient_id": analysis.patient_id,
            "age": analysis.age,
            "gender": analysis.gender,
            "height": analysis.height,
            "weight": analysis.weight,
            "bmi": analysis.bmi,
            "joint_pain": analysis.joint_pain,
            "pregnancies": analysis.pregnancies,
            "predicted_class": analysis.predicted_class,
            "predicted_diagnosis": analysis.predicted_diagnosis,
            "confidence": analysis.confidence,
            "t_score": analysis.t_score,
            "t_score_lower": analysis.t_score_lower,
            "t_score_upper": analysis.t_score_upper,
            "z_score": analysis.z_score,
            "z_score_lower": analysis.z_score_lower,
            "z_score_upper": analysis.z_score_upper,
            "menopausal_status": analysis.menopausal_status,
            "smoking": analysis.smoking,
            "alcohol": analysis.alcohol,
            "previous_fracture": analysis.previous_fracture,
            "long_term_steroid_use": analysis.long_term_steroid_use
        }
        
        # Build retrieval query
        query_builder = get_query_builder()
        query = query_builder.build_retrieval_query(analysis_dict)
        
        # Retrieve relevant chunks
        retrieval_service = get_retrieval_service()
        retrieved_chunks = retrieval_service.retrieve_chunks(query, db)
        
        # Generate clinical support using LLM
        llm_service = get_llm_service()
        clinical_support = llm_service.generate_clinical_support(
            query=query,
            retrieved_chunks=retrieved_chunks,
            analysis_context=analysis_dict
        )
        
        # Add analysis_id to response
        clinical_support["analysis_id"] = analysis_id
        clinical_support["prediction_summary"] = {
            "class": analysis.predicted_diagnosis,
            "confidence": analysis.confidence,
            "t_score": analysis.t_score,
            "t_score_lower": analysis.t_score_lower,
            "t_score_upper": analysis.t_score_upper,
            "z_score": analysis.z_score,
            "z_score_lower": analysis.z_score_lower,
            "z_score_upper": analysis.z_score_upper
        }
        
        logger.info(f"Generated clinical support for analysis {analysis_id}")
        return clinical_support
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate clinical support: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate clinical support")