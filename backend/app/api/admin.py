
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import aiofiles
from datetime import datetime

from app.models.schemas import DocumentUploadResponse, DocumentInfo
from app.services.document_processor import DocumentProcessor
from app.services.llm_chunker import LLMChunker
from app.services.ollama_client import OllamaClient
from app.services.vector_store import FAISSVectorStore
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

# Initialize services
document_processor = DocumentProcessor()
llm_chunker = LLMChunker()
ollama_client = OllamaClient()
vector_store = FAISSVectorStore()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document
    
    Steps:
    1. Save uploaded file
    2. Extract text from document
    3. Chunk text using LLM for semantic coherence
    4. Generate embeddings for each chunk
    5. Store in FAISS vector database
    """
    try:
        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content) / (1024 * 1024)  # Convert to MB
        
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.max_upload_size}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save file to disk
        file_path = Path(settings.upload_dir) / f"{document_id}_{file.filename}"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Extract text from document
        text = await document_processor.extract_text(str(file_path))
        
        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from document"
            )
        
        # Chunk document using LLM
        chunks = await llm_chunker.chunk_document(text, file.filename)
        
        if not chunks:
            raise HTTPException(
                status_code=500,
                detail="Failed to chunk document"
            )
        
        # Generate embeddings for each chunk
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await ollama_client.embed_batch(chunk_texts)
        
        # Store in vector database
        await vector_store.add_documents(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id,
            filename=file.filename
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="success",
            message=f"Document processed successfully with {len(chunks)} chunks",
            chunks_created=len(chunks),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    stats = vector_store.get_stats()
    documents = stats.get("documents", [])
    
    return [
        DocumentInfo(
            document_id=doc_id,
            filename=doc["filename"],
            upload_date=doc["upload_date"],
            chunk_count=doc["chunk_count"]
        )
        for doc_id, doc in vector_store.document_info.items()
    ]

