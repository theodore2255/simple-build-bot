from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    chunk_count: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to ask about the documents")
    max_results: int = Field(default=5, description="Maximum number of relevant chunks to retrieve")
    
class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float = Field(..., description="Confidence score of the response")

class ChunkMetadata(BaseModel):
    document_id: str
    chunk_index: int
    start_char: int
    end_char: int
    page_number: Optional[int] = None
