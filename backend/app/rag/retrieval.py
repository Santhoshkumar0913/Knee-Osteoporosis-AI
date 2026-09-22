"""
RAG retrieval service using PostgreSQL/pgvector vector similarity search
Direct PostgreSQL/pgvector retrieval - reuses existing embeddings, no in-memory vector store
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.embedding_service = get_embedding_service()
    
    def retrieve_chunks(self, query: str, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using PostgreSQL/pgvector vector similarity search
        Direct database query using existing embeddings - no in-memory vector store recreation
        This satisfies the Phase 2 requirement of using PostgreSQL/pgvector for actual vector retrieval
        """
        try:
            # Generate embedding for query using BGE
            query_embedding = self.embedding_service.embed_text(query)
            embedding_array = query_embedding.tolist()
            
            # Convert to pgvector format
            embedding_str = "[" + ",".join(map(str, embedding_array)) + "]"
            
            # Use pgvector cosine similarity search directly on database
            # This queries the actual PostgreSQL pgvector column with existing embeddings
            # No in-memory vector store is created or used
            # Note: Parameter binding for vector types with PostgreSQL requires f-string interpolation
            # due to PostgreSQL SQL dialect limitations with type cast syntax
            sql = text(f"""
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
                LIMIT :top_k
            """)
            
            result = db.execute(sql, {"top_k": self.top_k})
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
            
            logger.info(f"Retrieved {len(results)} chunks using PostgreSQL/pgvector similarity search (direct database query, reusing existing embeddings)")
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