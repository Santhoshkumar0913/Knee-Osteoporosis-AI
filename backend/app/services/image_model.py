import torch
import torch.nn as nn
import timm
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Tuple, Dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DINOv2Model:
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = {1: "Normal", 2: "Osteopenia", 3: "Osteoporosis"}
        self._load_model()
    
    def _load_model(self):
        """Load the DINOv2 model from checkpoint"""
        try:
            model_path = Path(settings.MODEL_PATH) / settings.DINOV2_MODEL_NAME
            
            if not model_path.exists():
                raise FileNotFoundError(f"DINOv2 model not found at {model_path}")
            
            # Load the checkpoint
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # Initialize DINOv2 ViT-S/14 model
            self.model = timm.create_model(
                'vit_small_patch14_224.dinov2',
                num_classes=settings.DINOV2_NUM_CLASSES,
                pretrained=False
            )
            
            # Load state dict
            if 'model' in checkpoint:
                self.model.load_state_dict(checkpoint['model'])
            elif 'state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"DINOv2 model loaded successfully from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load DINOv2 model: {str(e)}")
            raise
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for DINOv2 inference
        Expected input size: 518x518
        """
        # Resize to expected input size
        image = image.resize((settings.DINOV2_INPUT_SIZE, settings.DINOV2_INPUT_SIZE), Image.LANCZOS)
        
        # Convert to tensor and normalize
        # DINOv2 uses ImageNet normalization
        import torchvision.transforms as transforms
        
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        image_tensor = transform(image).unsqueeze(0).to(self.device)
        return image_tensor
    
    def predict(self, image: Image.Image) -> Dict:
        """
        Run DINOv2 inference on an image
        Returns predicted class, diagnosis, and probabilities
        """
        try:
            # Preprocess image
            image_tensor = self.preprocess_image(image)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted_class = torch.max(probabilities, 1)
            
            # Convert to numpy for easier handling
            predicted_class = predicted_class.item() + 1  # Convert 0-indexed to 1-indexed
            confidence = confidence.item()
            probabilities = probabilities.cpu().numpy()[0]
            
            # Map to class names
            diagnosis = self.class_names.get(predicted_class, "Unknown")
            
            return {
                "predicted_class": predicted_class,
                "predicted_diagnosis": diagnosis,
                "confidence": confidence,
                "probabilities": {
                    "normal": probabilities[0],
                    "osteopenia": probabilities[1],
                    "osteoporosis": probabilities[2]
                }
            }
            
        except Exception as e:
            logger.error(f"DINOv2 inference failed: {str(e)}")
            raise


# Global model instance
dinov2_model = None


def get_dinov2_model():
    global dinov2_model
    if dinov2_model is None:
        dinov2_model = DINOv2Model()
    return dinov2_model
