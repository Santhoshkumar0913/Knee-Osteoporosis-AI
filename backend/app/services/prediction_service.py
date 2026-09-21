from PIL import Image
import io
from typing import Dict, Tuple
from app.services.image_model import get_dinov2_model
from app.services.clinical_model import get_clinical_model
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self):
        self.dinov2_model = None
        self.clinical_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models (lazy loading)"""
        try:
            self.dinov2_model = get_dinov2_model()
            self.clinical_model = get_clinical_model()
            logger.info("ML models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {str(e)}")
            raise
    
    def calculate_bmi(self, height: float, weight: float) -> float:
        """Calculate BMI from height (m) and weight (kg)"""
        if height <= 0 or weight <= 0:
            raise ValueError("Height and weight must be positive values")
        return round(weight / (height ** 2), 2)
    
    def run_analysis(
        self,
        image_data: bytes,
        age: int,
        gender: str,
        height: float,
        weight: float,
        joint_pain: str,
        pregnancies: int,
        # Phase 2 additional clinical fields (not used in ML, but returned for storage)
        menopausal_status: str = None,
        smoking: str = None,
        alcohol: str = None,
        previous_fracture: str = None,
        long_term_steroid_use: str = None
    ) -> Dict:
        """
        Run complete analysis pipeline:
        1. Validate inputs
        2. Load and preprocess image
        3. Run DINOv2 inference
        4. Recalculate BMI
        5. Build clinical feature vector
        6. Run T-score and Z-score prediction
        7. Return complete results
        """
        try:
            # Step 1: Validate inputs
            self._validate_inputs(age, gender, height, weight, joint_pain, pregnancies, menopausal_status, smoking, alcohol, previous_fracture, long_term_steroid_use)
            
            # Step 2: Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Step 3: Run DINOv2 inference
            dinov2_result = self.dinov2_model.predict(image)
            
            # Step 4: Recalculate BMI (don't trust client value)
            bmi = self.calculate_bmi(height, weight)
            
            # Step 5: Build clinical feature vector
            feature_vector = self.clinical_model.build_feature_vector(
                age=age,
                gender=gender,
                height=height,
                weight=weight,
                bmi=bmi,
                joint_pain=joint_pain,
                pregnancies=pregnancies,
                predicted_class=dinov2_result['predicted_class'],
                menopausal_status=menopausal_status,
                smoking=smoking,
                alcohol=alcohol,
                previous_fracture=previous_fracture,
                long_term_steroid_use=long_term_steroid_use
            )
            
            # Step 6: Run clinical model predictions
            clinical_result = self.clinical_model.predict(feature_vector)
            
            # Step 7: Combine results
            result = {
                # Clinical inputs (with recalculated BMI)
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "bmi": bmi,
                "joint_pain": joint_pain,
                "pregnancies": pregnancies,
                # Phase 2 additional clinical fields
                "menopausal_status": menopausal_status,
                "smoking": smoking,
                "alcohol": alcohol,
                "previous_fracture": previous_fracture,
                "long_term_steroid_use": long_term_steroid_use,
                
                # DINOv2 results
                "predicted_class": dinov2_result['predicted_class'],
                "predicted_diagnosis": dinov2_result['predicted_diagnosis'],
                "normal_probability": dinov2_result['probabilities']['normal'],
                "osteopenia_probability": dinov2_result['probabilities']['osteopenia'],
                "osteoporosis_probability": dinov2_result['probabilities']['osteoporosis'],
                "confidence": dinov2_result['confidence'],
                
                # Clinical model results
                "t_score": clinical_result['t_score'],
                "t_score_lower": clinical_result['t_score_lower'],
                "t_score_upper": clinical_result['t_score_upper'],
                "z_score": clinical_result['z_score'],
                "z_score_lower": clinical_result['z_score_lower'],
                "z_score_upper": clinical_result['z_score_upper'],
                
                # Model version
                "model_version": "v1.0"
            }
            
            logger.info(f"Analysis completed successfully for gender={gender}, age={age}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def _validate_inputs(
        self,
        age: int,
        gender: str,
        height: float,
        weight: float,
        joint_pain: str,
        pregnancies: int,
        menopausal_status: str = None,
        smoking: str = None,
        alcohol: str = None,
        previous_fracture: str = None,
        long_term_steroid_use: str = None
    ):
        """Validate input parameters"""
        if age <= 0 or age > 150:
            raise ValueError("Age must be between 1 and 150")
        
        if gender.lower() not in ["male", "female"]:
            raise ValueError("Gender must be 'male' or 'female'")
        
        if height <= 0 or height > 3:
            raise ValueError("Height must be between 0 and 3 meters")
        
        if weight <= 0 or weight > 300:
            raise ValueError("Weight must be between 0 and 300 kg")
        
        if joint_pain.lower() not in ["no", "yes"]:
            raise ValueError("Joint pain must be one of: no, yes")
        
        if pregnancies < 0 or pregnancies > 20:
            raise ValueError("Pregnancies must be between 0 and 20")
        
        # Gender-specific validation
        if gender.lower() == "male" and pregnancies != 0:
            raise ValueError("Pregnancies must be 0 for male patients")
        
        if gender.lower() == "female" and pregnancies < 0:
            raise ValueError("Pregnancies is required for female patients")
        
        # Phase 2 field validation (all optional, but if provided must be valid)
        valid_yes_no = ["yes", "no", "yes", "no", None]
        if smoking and smoking.lower() not in ["yes", "no"]:
            raise ValueError("Smoking must be 'yes' or 'no'")
        
        if alcohol and alcohol.lower() not in ["yes", "no"]:
            raise ValueError("Alcohol must be 'yes' or 'no'")
        
        if previous_fracture and previous_fracture.lower() not in ["yes", "no"]:
            raise ValueError("Previous fracture must be 'yes' or 'no'")
        
        if long_term_steroid_use and long_term_steroid_use.lower() not in ["yes", "no"]:
            raise ValueError("Long-term steroid use must be 'yes' or 'no'")
        
        # Menopausal status validation (controlled selection)
        valid_menopausal = ["premenopausal", "perimenopausal", "postmenopausal", None]
        if menopausal_status and menopausal_status.lower() not in ["premenopausal", "perimenopausal", "postmenopausal"]:
            raise ValueError("Menopausal status must be one of: premenopausal, perimenopausal, postmenopausal")


# Global service instance
prediction_service = None


def get_prediction_service():
    global prediction_service
    if prediction_service is None:
        prediction_service = PredictionService()
    return prediction_service
