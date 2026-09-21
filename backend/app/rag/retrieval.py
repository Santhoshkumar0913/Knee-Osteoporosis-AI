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
            # Generate embedding for query
            query_embedding = self.embedding_service.embed_text(query)
            embedding_array = query_embedding.tolist()
            
            # Convert embedding array to PostgreSQL vector format
            embedding_str = "[" + ",".join(map(str, embedding_array)) + "]"
            
            # Use pgvector's cosine similarity search (cosine distance <=>)
            # Build the SQL with literal embedding value
            sql = f"""
                SELECT 
                    rc.id,
                    rc.chunk_text,
                    rc.document_id,
                    rc.chunk_index,
                    rd.title,
                    rd.organization,
                    rd.publication_year,
                    1 - (rc.embedding <=> '{embedding_str}'::vector) as similarity
                FROM rag_chunks rc
                JOIN rag_documents rd ON rc.document_id = rd.id
                ORDER BY rc.embedding <=> '{embedding_str}'::vector
                LIMIT {self.top_k}
            """
            
            result = db.execute(text(sql))
            
            rows = result.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "chunk_text": row.chunk_text,
                    "document_id": row.document_id,
                    "chunk_index": row.chunk_index,
                    "organization": row.organization,
                    "publication_year": row.publication_year,
                    "title": row.title,
                    "similarity": row.similarity
                })
            
            logger.info(f"Retrieved {len(results)} chunks with pgvector similarity search")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks with pgvector: {str(e)}")
            raise


# Global retrieval service instance
retrieval_service = None


def get_retrieval_service():
    global retrieval_service
    if retrieval_service is None:
        retrieval_service = RetrievalService()
    return retrieval_service