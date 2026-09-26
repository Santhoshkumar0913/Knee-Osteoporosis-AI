"""
Clinical context query builder for RAG retrieval
"""
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class QueryBuilder:
    def build_retrieval_query(self, analysis: Dict[str, Any]) -> str:
        """
        Build a concise clinical evidence query from analysis context
        """
        try:
            # Extract relevant clinical information
            age = analysis.get('age', 0)
            gender = analysis.get('gender', 'unknown')
            bmi = analysis.get('bmi', 0)
            predicted_class = analysis.get('predicted_class', 0)
            predicted_diagnosis = analysis.get('predicted_diagnosis', 'unknown')
            t_score = analysis.get('t_score', 0)
            z_score = analysis.get('z_score', 0)
            
            # Phase 2 additional fields
            menopausal_status = analysis.get('menopausal_status', 'not specified')
            smoking = analysis.get('smoking', 'not specified')
            alcohol = analysis.get('alcohol', 'not specified')
            previous_fracture = analysis.get('previous_fracture', 'not specified')
            long_term_steroid_use = analysis.get('long_term_steroid_use', 'not specified')
            
            # Build query focusing on the diagnosis and key risk factors
            query_parts = [
                f"DINOv2 image-model prediction (classification): {predicted_diagnosis}",
                f"Age: {age} years",
                f"Gender: {gender}",
                f"BMI: {bmi:.1f}",
                f"Model-estimated T-score: {t_score:.2f}",
                f"Model-estimated Z-score: {z_score:.2f}"
            ]
            
            # Add relevant risk factors if present
            if smoking and smoking.lower() == 'yes':
                query_parts.append("Smoking risk factor")
            
            if previous_fracture and previous_fracture.lower() == 'yes':
                query_parts.append("Previous fracture history")
            
            if long_term_steroid_use and long_term_steroid_use.lower() == 'yes':
                query_parts.append("Long-term steroid use")
            
            if menopausal_status and menopausal_status.lower() != 'not specified':
                query_parts.append(f"Menopausal status: {menopausal_status}")
            
            query = ". ".join(query_parts)
            logger.info(f"Built retrieval query: {query[:100]}...")
            
            return query
            
        except Exception as e:
            logger.error(f"Failed to build retrieval query: {str(e)}")
            raise


# Global query builder instance
query_builder = QueryBuilder()


def get_query_builder():
    return query_builder
