"""
RAG retrieval service using LlamaIndex with PostgreSQL/pgvector
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
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import BaseEmbedding

logger = logging.getLogger(__name__)

# Module-level embedding service reference for LlamaIndex wrapper
_embedding_service_ref = None


class BGEEmbedding(BaseEmbedding):
    """LlamaIndex wrapper for BGE embedding service"""
    
    def __init__(self):
        super().__init__(embed_model="BAAI/bge-base-en-v1.5")
    
    def _get_query_embedding(self, query: str) -> List[float]:
        global _embedding_service_ref
        return _embedding_service_ref.embed_text(query).tolist()
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)
    
    def _get_text_embedding(self, text: str) -> List[float]:
        global _embedding_service_ref
        return _embedding_service_ref.embed_text(text).tolist()
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        global _embedding_service_ref
        return _embedding_service_ref.embed_texts(texts).tolist()
    
    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._get_text_embeddings(texts)
    
    def _get_text_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity"""
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity([embedding1], [embedding2])[0][0]


class RetrievalService:
    def __init__(self):
        global _embedding_service_ref
        self.top_k = settings.RAG_TOP_K
        self.embedding_service = get_embedding_service()
        _embedding_service_ref = self.embedding_service
        self._index = None
        self._llama_embedding = BGEEmbedding()
    
    def _build_llama_index(self, db: Session):
        """Build LlamaIndex from PostgreSQL/pgvector data"""
        try:
            # Fetch all chunks with metadata from database
            chunks = db.query(RAGChunk).all()
            
            # Create LlamaIndex Documents
            documents = []
            for chunk in chunks:
                if chunk.document:
                    doc = Document(
                        text=chunk.chunk_text,
                        metadata={
                            "chunk_id": chunk.id,
                            "document_id": chunk.document_id,
                            "chunk_index": chunk.chunk_index,
                            "title": chunk.document.title,
                            "organization": chunk.document.organization,
                            "publication_year": chunk.document.publication_year
                        }
                    )
                    documents.append(doc)
            
            logger.info(f"Building LlamaIndex from {len(documents)} chunks")
            
            # Create in-memory vector index with custom embedding function
            from llama_index.core import StorageContext
            
            # Create index with custom embedding
            index = VectorStoreIndex.from_documents(
                documents,
                embed_model=self._llama_embedding,
                storage_context=StorageContext.from_defaults()
            )
            
            return index
            
        except Exception as e:
            logger.error(f"Failed to build LlamaIndex: {str(e)}")
            raise
    
    def retrieve_chunks(self, query: str, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using LlamaIndex with pgvector backend
        """
        try:
            # Build or get LlamaIndex
            if self._index is None:
                self._index = self._build_llama_index(db)
            
            # Create retriever
            retriever = self._index.as_retriever(
                similarity_top_k=self.top_k
            )
            
            # Retrieve nodes
            nodes = retriever.retrieve(query)
            
            # Convert to our format
            results = []
            for node in nodes:
                results.append({
                    "chunk_text": node.node.text,
                    "document_id": node.node.metadata.get("document_id"),
                    "chunk_index": node.node.metadata.get("chunk_index"),
                    "organization": node.node.metadata.get("organization"),
                    "publication_year": node.node.metadata.get("publication_year"),
                    "title": node.node.metadata.get("title"),
                    "similarity": node.score if hasattr(node, 'score') else 0.0
                })
            
            logger.info(f"Retrieved {len(results)} chunks using LlamaIndex")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks with LlamaIndex: {str(e)}")
            raise


# Global retrieval service instance
retrieval_service = None


def get_retrieval_service():
    global retrieval_service
    if retrieval_service is None:
        retrieval_service = RetrievalService()
    return retrieval_service