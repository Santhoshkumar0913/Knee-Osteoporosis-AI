import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ClinicalModel:
    def __init__(self):
        self.t_score_model = None
        self.z_score_model = None
        self._load_models()
    
    def _load_models(self):
        """Load T-score and Z-score models"""
        try:
            # Load T-score model
            t_score_path = Path(settings.MODEL_PATH) / settings.T_SCORE_MODEL_NAME
            if not t_score_path.exists():
                raise FileNotFoundError(f"T-score model not found at {t_score_path}")
            
            self.t_score_model = joblib.load(t_score_path)
            logger.info(f"T-score model loaded from {t_score_path}")
            
            # Load Z-score model
            z_score_path = Path(settings.MODEL_PATH) / settings.Z_SCORE_MODEL_NAME
            if not z_score_path.exists():
                raise FileNotFoundError(f"Z-score model not found at {z_score_path}")
            
            self.z_score_model = joblib.load(z_score_path)
            logger.info(f"Z-score model loaded from {z_score_path}")
            
        except Exception as e:
            logger.error(f"Failed to load clinical models: {str(e)}")
            raise
    
    def build_feature_vector(
        self,
        age: int,
        gender: str,
        height: float,
        weight: float,
        bmi: float,
        joint_pain: str,
        pregnancies: int,
        predicted_class: int
    ) -> List[float]:
        """
        Build the clinical feature vector in the exact order expected by the models:
        [Age, Gender, BMI, Weight, Height, Joint Pain, Number of Pregnancies, Class, Pregnancy_Missing]
        """
        # Convert gender to numeric (Male=0, Female=1)
        gender_numeric = 1 if gender.lower() == "female" else 0
        
        # Convert joint pain to numeric (matching trained model encoding)
        joint_pain_mapping = {
            "no": 0,
            "yes": 1
        }
        joint_pain_numeric = joint_pain_mapping.get(joint_pain.lower(), 0)
        
        # Pregnancy missing is always 0 in V1 (we always have pregnancy data)
        pregnancy_missing = 0
        
        feature_vector = [
            float(age),
            float(gender_numeric),
            float(bmi),
            float(weight),
            float(height),
            float(joint_pain_numeric),
            float(pregnancies),
            float(predicted_class),
            float(pregnancy_missing)
        ]
        
        return feature_vector
    
    def predict_t_score(self, feature_vector: List[float]) -> Dict:
        """Predict T-score using Random Forest model"""
        try:
            # Reshape for single sample prediction
            features = np.array(feature_vector).reshape(1, -1)
            
            # Predict
            prediction = self.t_score_model.predict(features)[0]
            
            # Calculate range
            lower = prediction - settings.T_SCORE_MARGIN
            upper = prediction + settings.T_SCORE_MARGIN
            
            return {
                "t_score": float(prediction),
                "t_score_lower": float(lower),
                "t_score_upper": float(upper)
            }
            
        except Exception as e:
            logger.error(f"T-score prediction failed: {str(e)}")
            raise
    
    def predict_z_score(self, feature_vector: List[float]) -> Dict:
        """Predict Z-score using Gradient Boosting model"""
        try:
            # Reshape for single sample prediction
            features = np.array(feature_vector).reshape(1, -1)
            
            # Predict
            prediction = self.z_score_model.predict(features)[0]
            
            # Calculate range
            lower = prediction - settings.Z_SCORE_MARGIN
            upper = prediction + settings.Z_SCORE_MARGIN
            
            return {
                "z_score": float(prediction),
                "z_score_lower": float(lower),
                "z_score_upper": float(upper)
            }
            
        except Exception as e:
            logger.error(f"Z-score prediction failed: {str(e)}")
            raise
    
    def predict(self, feature_vector: List[float]) -> Dict:
        """Predict both T-score and Z-score"""
        t_score_result = self.predict_t_score(feature_vector)
        z_score_result = self.predict_z_score(feature_vector)
        
        return {
            **t_score_result,
            **z_score_result
        }


# Global model instance
clinical_model = None


def get_clinical_model():
    global clinical_model
    if clinical_model is None:
        clinical_model = ClinicalModel()
    return clinical_model
