from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime
import logging

from app.database import get_db, engine, Base
from app.models import Document
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService
from app.schemas import DocumentResponse, QueryRequest, QueryResponse

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Document Processing API",
    description="A Retrieval-Augmented Generation pipeline for document processing and querying",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
vector_store = VectorStoreService()
llm_service = LLMService()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "RAG Document Processing API", "version": "1.0.0"}

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document for RAG system.
    Supports up to 20 documents, each with maximum 1000 pages.
    """
    try:
        # Validate file type
        allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Check document count limit
        doc_count = db.query(Document).count()
        if doc_count >= 20:
            raise HTTPException(status_code=400, detail="Maximum document limit (20) reached")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_extension}"
        
        # Save file temporarily
        file_path = f"uploads/{filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        logger.info(f"Processing document: {file.filename}")
        chunks = await document_processor.process_document(file_path, file.filename)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to extract content from document")
        
        # Validate page limit (approximate based on chunk count)
        if len(chunks) > 1000:  # Assuming 1 chunk per page approximately
            raise HTTPException(status_code=400, detail="Document exceeds maximum page limit (1000)")
        
        # Store in vector database
        logger.info(f"Storing {len(chunks)} chunks in vector database")
        doc_id = await vector_store.store_document(file_id, chunks)
        
        # Save metadata to database
        db_document = Document(
            id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            content_type=file.content_type,
            chunk_count=len(chunks),
            status="processed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(f"Document {file.filename} processed successfully")
        
        return DocumentResponse(
            id=file_id,
            filename=file.filename,
            file_size=len(content),
            chunk_count=len(chunks),
            status="processed",
            created_at=db_document.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(
    query: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the RAG system with a user question.
    Retrieves relevant document chunks and generates a response.
    """
    try:
        # Check if any documents are available
        doc_count = db.query(Document).filter(Document.status == "processed").count()
        if doc_count == 0:
            raise HTTPException(status_code=400, detail="No processed documents available for querying")
        
        logger.info(f"Processing query: {query.question[:100]}...")
        
        # Retrieve relevant chunks
        relevant_chunks = await vector_store.similarity_search(query.question, k=query.max_results)
        
        if not relevant_chunks:
            return QueryResponse(
                question=query.question,
                answer="I couldn't find any relevant information in the uploaded documents to answer your question.",
                sources=[],
                confidence=0.0
            )
        
        # Generate response using LLM
        response = await llm_service.generate_response(query.question, relevant_chunks)
        
        # Format sources
        sources = []
        for chunk in relevant_chunks[:5]:  # Limit to top 5 sources
            doc = db.query(Document).filter(Document.id == chunk.get('document_id')).first()
            if doc:
                sources.append({
                    "document_id": doc.id,
                    "document_name": doc.filename,
                    "chunk_id": chunk.get('id', ''),
                    "relevance_score": chunk.get('score', 0.0)
                })
        
        return QueryResponse(
            question=query.question,
            answer=response,
            sources=sources,
            confidence=max([chunk.get('score', 0.0) for chunk in relevant_chunks]) if relevant_chunks else 0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """
    Get list of all processed documents with metadata.
    """
    try:
        documents = db.query(Document).all()
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                file_size=doc.file_size,
                chunk_count=doc.chunk_count,
                status=doc.status,
                created_at=doc.created_at
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document and its associated chunks from the system.
    """
    try:
        # Find document in database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector store
        await vector_store.delete_document(document_id)
        
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"message": f"Document {document.filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
