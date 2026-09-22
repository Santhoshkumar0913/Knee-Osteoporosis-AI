from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.database import Base


class RAGDocument(Base):
    """RAG document registry for idempotent ingestion"""
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False, index=True)
    checksum = Column(String(64), nullable=False, index=True)
    title = Column(String(500))
    organization = Column(String(255))
    publication_year = Column(Integer)
    source_url = Column(Text)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with chunks
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")


class RAGChunk(Base):
    """RAG text chunks with vector embeddings"""
    __tablename__ = "rag_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)  # PostgreSQL vector(768) column
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with document
    document = relationship("RAGDocument", back_populates="chunks")