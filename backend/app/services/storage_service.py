import os
import shutil
from pathlib import Path
from typing import Optional
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.storage_path = Path(settings.STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def get_patient_storage_path(self, patient_code: str) -> Path:
        """Get storage path for a specific patient"""
        patient_path = self.storage_path / patient_code
        patient_path.mkdir(parents=True, exist_ok=True)
        return patient_path
    
    def save_analysis_image(self, patient_code: str, analysis_id: int, image_data: bytes, file_extension: str) -> str:
        """
        Save an analysis image and return the relative path
        """
        patient_path = self.get_patient_storage_path(patient_code)
        filename = f"{analysis_id}_xray{file_extension}"
        file_path = patient_path / filename
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Return relative path from storage root
        return str(file_path.relative_to(self.storage_path.parent.parent))
    
    def delete_patient_images(self, patient_code: str) -> bool:
        """Delete all images for a patient"""
        patient_path = self.get_patient_storage_path(patient_code)
        if patient_path.exists():
            shutil.rmtree(patient_path)
            return True
        return False
    
    def delete_analysis_image(self, image_path: str) -> bool:
        """Delete a specific analysis image"""
        full_path = Path(image_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def get_full_image_path(self, relative_path: str) -> Path:
        """Convert relative path to absolute path"""
        return Path(relative_path)


storage_service = StorageService()
