"""
RAG document ingestion pipeline
Processes PDF documents, extracts text, chunks with metadata, and stores in PostgreSQL with pgvector
"""
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional
from pypdf import PdfReader
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.rag_models import RAGDocument, RAGChunk
from app.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

# Document metadata for the four approved PDFs
DOCUMENT_METADATA = {
    "WHO_Fragility_Fractures.pdf": {
        "title": "WHO Fragility Fractures",
        "organization": "WHO",
        "publication_year": 2022,
        "source_url": "https://www.who.int/publications/i/item/9789241503229"
    },
    "ISBMR_Osteoporosis_Adults.pdf": {
        "title": "ISBMR Guidelines for Osteoporosis in Adults",
        "organization": "ISBMR",
        "publication_year": 2020,
        "source_url": "https://www.isbmr.org/guidelines/"
    },
    "IMS_Postmenopausal_Osteoporosis.pdf": {
        "title": "IMS Postmenopausal Osteoporosis Guidelines",
        "organization": "IMS",
        "publication_year": 2021,
        "source_url": "https://www.imshealth.com/"
    },
    "BHOF_Clinicians_Guide.pdf": {
        "title": "BHOF Clinicians Guide to Osteoporosis",
        "organization": "BHOF",
        "publication_year": 2023,
        "source_url": "https://www.bonehealthandosteoporosis.org/"
    }
}


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF file"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {str(e)}")
        raise


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        start = end - overlap if end < text_length else text_length
    
    return chunks


def ingest_document(
    pdf_path: Path,
    db: SessionLocal,
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> Dict[str, int]:
    """Ingest a single PDF document"""
    filename = pdf_path.name
    checksum = calculate_checksum(pdf_path)
    
    # Check if document already exists
    existing_doc = db.query(RAGDocument).filter(RAGDocument.filename == filename).first()
    if existing_doc:
        if existing_doc.checksum == checksum:
            logger.info(f"Document {filename} already ingested with same checksum, skipping")
            return {"skipped": 1, "chunks": 0}
        else:
            logger.info(f"Document {filename} exists with different checksum, reingesting")
            # Delete old chunks
            db.query(RAGChunk).filter(RAGChunk.document_id == existing_doc.id).delete()
            db.delete(existing_doc)
            db.commit()
    
    # Get document metadata
    metadata = DOCUMENT_METADATA.get(filename, {})
    title = metadata.get("title", filename)
    organization = metadata.get("organization", "Unknown")
    publication_year = metadata.get("publication_year", None)
    source_url = metadata.get("source_url", "")
    
    # Extract text
    logger.info(f"Extracting text from {filename}")
    text = extract_text_from_pdf(pdf_path)
    
    if not text.strip():
        logger.warning(f"No text extracted from {filename}")
        return {"error": "no_text", "chunks": 0}
    
    # Chunk text
    logger.info(f"Chunking text from {filename}")
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    
    if not chunks:
        logger.warning(f"No chunks created from {filename}")
        return {"error": "no_chunks", "chunks": 0}
    
    # Create document record
    doc_record = RAGDocument(
        filename=filename,
        checksum=checksum,
        title=title,
        organization=organization,
        publication_year=publication_year,
        source_url=source_url
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)
    
    # Generate embeddings and store chunks
    logger.info(f"Generating embeddings for {len(chunks)} chunks from {filename}")
    embedding_service = get_embedding_service()
    
    for i, chunk in enumerate(chunks):
        embedding = embedding_service.embed_text(chunk)
        
        chunk_record = RAGChunk(
            document_id=doc_record.id,
            chunk_text=chunk,
            embedding=embedding.tobytes(),  # Store as bytes
            chunk_index=i
        )
        db.add(chunk_record)
    
    db.commit()
    logger.info(f"Successfully ingested {filename}: {len(chunks)} chunks")
    
    return {"ingested": 1, "chunks": len(chunks)}


def ingest_all_documents():
    """Ingest all PDF documents from the RAG documents directory"""
    rag_documents_path = Path(settings.RAG_DOCUMENTS_PATH)
    
    if not rag_documents_path.exists():
        logger.error(f"RAG documents directory not found: {rag_documents_path}")
        return
    
    pdf_files = list(rag_documents_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {rag_documents_path}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to ingest")
    
    with SessionLocal() as db:
        results = {}
        for pdf_path in pdf_files:
            try:
                result = ingest_document(pdf_path, db)
                results[pdf_path.name] = result
            except Exception as e:
                logger.error(f"Failed to ingest {pdf_path.name}: {str(e)}")
                results[pdf_path.name] = {"error": str(e), "chunks": 0}
        
        logger.info(f"Ingestion complete. Results: {results}")
        return results


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    print("Starting RAG document ingestion...")
    results = ingest_all_documents()
    
    if results:
        print("\nIngestion Results:")
        for filename, result in results.items():
            if "error" in result:
                print(f"  {filename}: ERROR - {result['error']}")
            elif "skipped" in result:
                print(f"  {filename}: SKIPPED (already ingested)")
            else:
                print(f"  {filename}: INGESTED ({result['chunks']} chunks)")
    else:
        print("No documents to ingest")