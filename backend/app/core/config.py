from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Database
    POSTGRES_DB: str = "osteoporosis_ai"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Storage
    STORAGE_PATH: str = str(PROJECT_ROOT / "storage" / "uploads")
    
    # Model settings
    MODEL_PATH: str = str(PROJECT_ROOT / "backend" / "models")
    DINOV2_MODEL_NAME: str = "dinov2_experiment2_best.pth"
    T_SCORE_MODEL_NAME: str = "t_score_random_forest.joblib"
    Z_SCORE_MODEL_NAME: str = "z_score_gradient_boosting.joblib"
    MODEL_METADATA_NAME: str = "model_metadata.json"
    
    # Model parameters
    DINOV2_INPUT_SIZE: int = 518
    DINOV2_FEATURE_DIM: int = 384
    DINOV2_NUM_CLASSES: int = 3
    
    # Score margins (from trained model metadata)
    T_SCORE_MARGIN: float = 0.37151470129482217
    Z_SCORE_MARGIN: float = 1.223247423942022
    
    # API
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
settings.MODEL_PATH = str((PROJECT_ROOT / settings.MODEL_PATH).resolve()) if not Path(settings.MODEL_PATH).is_absolute() else settings.MODEL_PATH
settings.STORAGE_PATH = str((PROJECT_ROOT / settings.STORAGE_PATH).resolve()) if not Path(settings.STORAGE_PATH).is_absolute() else settings.STORAGE_PATH
