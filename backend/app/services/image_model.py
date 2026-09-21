import torch
import torch.nn as nn
import torch.nn.functional as F
import timm
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Tuple, Dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ResizeAndPad:
    """
    Custom ResizeAndPad transform matching training notebook:
    - Aspect-ratio-preserving resize using LANCZOS
    - Centered zero padding to target size
    """
    def __init__(self, size: int, fill: int = 0):
        self.size = size
        self.fill = fill
    
    def __call__(self, image: Image.Image) -> Image.Image:
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = image.size
        
        # Calculate scaling factor to fit within target size while preserving aspect ratio
        scale = min(self.size / original_width, self.size / original_height)
        
        # Calculate new dimensions
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        # Resize using LANCZOS interpolation
        image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Create new image with target size and fill value (black)
        padded_image = Image.new('RGB', (self.size, self.size), (self.fill, self.fill, self.fill))
        
        # Calculate centered position
        paste_x = (self.size - new_width) // 2
        paste_y = (self.size - new_height) // 2
        
        # Paste resized image onto padded background
        padded_image.paste(image, (paste_x, paste_y))
        
        return padded_image


class DINOv2Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model(
            'vit_small_patch14_dinov2',
            num_classes=0,
            pretrained=False
        )
        # Correct architecture matching training: LayerNorm(384) -> Dropout(0.40) -> Linear(384, 128) -> GELU -> Dropout(0.30) -> Linear(128, 3)
        self.classifier = nn.Sequential(
            nn.LayerNorm(384),
            nn.Dropout(0.40),
            nn.Linear(384, 128),
            nn.GELU(),
            nn.Dropout(0.30),
            nn.Linear(128, 3)
        )

    def forward(self, image_tensor: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.backbone(image_tensor))


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
            
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            state_dict = checkpoint['model_state_dict']

            self.model = DINOv2Classifier()
            self.model.load_state_dict(state_dict, strict=True)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"DINOv2 model loaded successfully from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load DINOv2 model: {str(e)}")
            raise
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for DINOv2 inference
        Exact training pipeline: RGB → ResizeAndPad(518, fill=0) → LANCZOS aspect-ratio-preserving resize → centered zero padding → ToTensor → ImageNet normalization
        """
        import torchvision.transforms as transforms
        
        # Apply exact training preprocessing
        transform = transforms.Compose([
            ResizeAndPad(size=settings.DINOV2_INPUT_SIZE, fill=0),
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
                    "normal": float(probabilities[0]),
                    "osteopenia": float(probabilities[1]),
                    "osteoporosis": float(probabilities[2])
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
