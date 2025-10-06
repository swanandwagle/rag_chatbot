
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str
    filename: str
    status: str
    message: str
    chunks_created: int
    timestamp: datetime


class ChatRequest(BaseModel):
    """Request model for chat queries"""
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """Response model for chat queries"""
    answer: str
    sources: List[dict]
    query: str
    timestamp: datetime


class DocumentInfo(BaseModel):
    """Model for document information"""
    document_id: str
    filename: str
    upload_date: datetime
    chunk_count: int


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    ollama_connected: bool
    llm_model: str
    embedding_model: str
    total_documents: int
    total_chunks: int

