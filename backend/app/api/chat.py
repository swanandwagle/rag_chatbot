
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import AsyncGenerator

from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.ollama_client import OllamaClient
from app.services.vector_store import FAISSVectorStore
from app.config import settings

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
            top_k=min(request.top_k, getattr(settings, "max_top_k", 20))
        )
        
        # Apply similarity threshold filtering
        threshold = float(getattr(settings, "similarity_threshold", 0.6))
        filtered_results = [r for r in results if r.get("similarity_score", 0) >= threshold]

        if not filtered_results:
            return ChatResponse(
                answer="I don't have any information in my knowledge base to answer this question.",
                sources=[],
                query=request.query,
                timestamp=datetime.utcnow()
            )
        
        # Cap and diversify context to avoid exceeding model window
        # Sort by similarity then select top unique chunks by filename/chunk id
        unique = []
        seen_keys = set()
        for r in sorted(filtered_results, key=lambda x: x.get("similarity_score", 0), reverse=True):
            key = (r.get("filename"), r.get("chunk_index"))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique.append(r)
        # Token/char cap: keep the context within ~10k chars
        context_parts = []
        total_chars = 0
        for r in unique:
            part = f"[Source: {r['filename']}, Chunk {r['chunk_index']+1}/{r['total_chunks']}]\n{r['content']}"
            if total_chars + len(part) > 10000:
                break
            context_parts.append(part)
            total_chars += len(part)
        context = "\n\n---\n\n".join(context_parts)
        
        # Build prompt for LLM per user's style guidelines
        prompt = f"""You are a helpful assistant answering questions based on provided documents.

Context:
{context}

Question: {request.query}

Instructions:
- Answer directly and naturally, as if you're an expert on this topic
- Use 2-4 clear, concise sentences
- If the information needed to answer isn't in the context above, respond with: "I don't have enough information to answer this question."
- Never mention "the context", "the documents", "based on the text", or similar meta-references
- Present information as facts, not as "according to" or "the text states"
- Be confident and direct in your response

Final Answer:"""
        
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
            for r in unique
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
                top_k=min(request.top_k, getattr(settings, "max_top_k", 20))
            )
            
            threshold = float(getattr(settings, "similarity_threshold", 0.6))
            filtered_results = [r for r in results if r.get("similarity_score", 0) >= threshold]
            if not filtered_results:
                yield "I don't have any information in my knowledge base to answer this question."
                return
            
            # Cap and diversify context
            unique = []
            seen_keys = set()
            for r in sorted(filtered_results, key=lambda x: x.get("similarity_score", 0), reverse=True):
                key = (r.get("filename"), r.get("chunk_index"))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                unique.append(r)
            context_parts = []
            total_chars = 0
            for r in unique:
                part = f"[Source: {r['filename']}, Chunk {r['chunk_index']+1}/{r['total_chunks']}]\n{r['content']}"
                if total_chars + len(part) > 10000:
                    break
                context_parts.append(part)
                total_chars += len(part)
            context = "\n\n---\n\n".join(context_parts)
            
            # Build prompt (streaming; same as non-streaming)
            prompt = f"""You are a helpful assistant answering questions based on provided documents.

Context:
{context}

Question: {request.query}

Instructions:
- Answer directly and naturally, as if you're an expert on this topic
- Use 2-4 clear, concise sentences
- If the information needed to answer isn't in the context above, respond with: "I don't have enough information to answer this question."
- Never mention "the context", "the documents", "based on the text", or similar meta-references
- Present information as facts, not as "according to" or "the text states"
- Be confident and direct in your response

Final Answer:"""
            
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

