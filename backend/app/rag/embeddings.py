"""
Embedding service using BAAI/bge-base-en-v1.5 via sentence-transformers
"""
import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.device = "cpu"  # BGE model runs on CPU
        self._load_model()
    
    def _load_model(self):
        """Load the BGE embedding model"""
        try:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Return the embedding dimension"""
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 768  # BGE base embedding dimension


# Global embedding service instance
embedding_service = None


def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service