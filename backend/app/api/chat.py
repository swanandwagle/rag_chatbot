
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import AsyncGenerator

from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.ollama_client import OllamaClient
from app.services.vector_store import FAISSVectorStore

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
ollama_client = OllamaClient()
vector_store = FAISSVectorStore()


@router.post("/query", response_model=ChatResponse)
async def query(request: ChatRequest):
    """
    Query the RAG system with a question
    
    Steps:
    1. Generate embedding for the query
    2. Search vector database for relevant chunks
    3. Build context from retrieved chunks
    4. Generate answer using LLM with context
    """
    try:
        # Generate query embedding
        query_embedding = await ollama_client.embed(request.query)
        
        # Search vector store for relevant chunks
        results = await vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k
        )
        
        if not results:
            return ChatResponse(
                answer="I don't have any information in my knowledge base to answer this question.",
                sources=[],
                query=request.query,
                timestamp=datetime.utcnow()
            )
        
        # Build context from retrieved chunks
        context = "\n\n---\n\n".join([
            f"[Source: {r['filename']}, Chunk {r['chunk_index']+1}/{r['total_chunks']}]\n{r['content']}"
            for r in results
        ])
        
        # Build prompt for LLM (concise, single-sentence answer)
        prompt = f"""You are a precise assistant. Answer the user's question using ONLY the context.

Context:
{context}

Question: {request.query}

Rules:
- If the context is insufficient, reply exactly: "I don't have enough information in the provided documents to answer this question."
- Otherwise, reply with a SINGLE short sentence. Do not include explanations, citations, or extra details.

Final answer:"""
        
        # Generate answer using LLM
        answer = await ollama_client.generate(prompt)
        
        # Prepare sources
        sources = [
            {
                "filename": r["filename"],
                "chunk_index": r["chunk_index"],
                "total_chunks": r["total_chunks"],
                "similarity_score": r["similarity_score"],
                "content_preview": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
            }
            for r in results
        ]
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            query=request.query,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/query/stream")
async def query_stream(request: ChatRequest):
    """
    Query the RAG system with streaming response
    
    Returns:
        Streaming response with answer chunks
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            # Generate query embedding
            query_embedding = await ollama_client.embed(request.query)
            
            # Search vector store
            results = await vector_store.search(
                query_embedding=query_embedding,
                top_k=request.top_k
            )
            
            if not results:
                yield "I don't have any information in my knowledge base to answer this question."
                return
            
            # Build context
            context = "\n\n---\n\n".join([
                f"[Source: {r['filename']}, Chunk {r['chunk_index']+1}/{r['total_chunks']}]\n{r['content']}"
                for r in results
            ])
            
            # Build prompt (concise streaming answer)
            prompt = f"""You are a precise assistant. Answer the user's question using ONLY the context.

Context:
{context}

Question: {request.query}

Rules:
- If the context is insufficient, reply exactly: "I don't have enough information in the provided documents."
- Otherwise, reply with a SINGLE short sentence. Do not include explanations, citations, or extra details.

Final answer:"""
            
            # Stream answer
            async for chunk in ollama_client.generate_stream(prompt):
                yield chunk
                
        except Exception as e:
            yield f"\n\nError: {str(e)}"
    
    return StreamingResponse(generate_stream(), media_type="text/plain")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and statistics"""
    ollama_connected = await ollama_client.health_check()
    stats = vector_store.get_stats()
    
    return HealthResponse(
        status="healthy" if ollama_connected else "degraded",
        ollama_connected=ollama_connected,
        llm_model=ollama_client.llm_model,
        embedding_model=ollama_client.embedding_model,
        total_documents=stats["total_documents"],
        total_chunks=stats["total_vectors"]
    )

