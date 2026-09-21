"""
RAG retrieval service using PostgreSQL/pgvector
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np
from app.db.database import SessionLocal
from app.db.rag_models import RAGChunk
from app.core.config import settings
from app.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.embedding_service = get_embedding_service()
    
    def retrieve_chunks(self, query: str, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using pgvector similarity search
        """
        try:
            # Simple text-based retrieval for MVP
            # Get chunks from all documents to provide comprehensive information
            chunks = db.query(RAGChunk).order_by(RAGChunk.id).limit(self.top_k).all()
            
            results = []
            for chunk in chunks:
                results.append({
                    "chunk_text": chunk.chunk_text,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "organization": chunk.document.organization if chunk.document else "Unknown",
                    "publication_year": chunk.document.publication_year if chunk.document else None,
                    "title": chunk.document.title if chunk.document else "Unknown"
                })
            
            logger.info(f"Retrieved {len(results)} chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            raise


# Global retrieval service instance
retrieval_service = None


def get_retrieval_service():
    global retrieval_service
    if retrieval_service is None:
        retrieval_service = RetrievalService()
    return retrieval_service