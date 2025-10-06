
import json
import tiktoken
from typing import List, Dict
from app.services.ollama_client import OllamaClient
from app.config import settings


class LLMChunker:
    """Service for chunking documents using LLM to maintain semantic meaning"""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    async def chunk_document(self, text: str, filename: str) -> List[Dict[str, str]]:
        """
        Chunk document while maintaining semantic meaning using LLM
        
        Args:
            text: The document text to chunk
            filename: Original filename for metadata
            
        Returns:
            List of chunks with metadata
        """
        # If document is small enough, return as single chunk
        if self.count_tokens(text) <= self.chunk_size:
            return [{
                "content": text,
                "chunk_index": 0,
                "filename": filename,
                "total_chunks": 1
            }]
        
        # Choose splitting strategy
        if getattr(settings, "use_llm_chunking", False):
            chunks = await self._semantic_split(text)
        else:
            chunks = self._naive_split(text)
        
        # Add metadata to chunks
        chunk_dicts = []
        for idx, chunk in enumerate(chunks):
            chunk_dicts.append({
                "content": chunk,
                "chunk_index": idx,
                "filename": filename,
                "total_chunks": len(chunks)
            })
        
        return chunk_dicts
    
    async def _semantic_split(self, text: str) -> List[str]:
        """
        Split text semantically using LLM
        
        Args:
            text: Text to split
            
        Returns:
            List of semantic chunks
        """
        total_tokens = self.count_tokens(text)
        
        # If small enough, return as is
        if total_tokens <= self.chunk_size:
            return [text]
        
        # Calculate approximate number of chunks needed
        num_chunks = (total_tokens // self.chunk_size) + 1
        
        # Create prompt for LLM to split intelligently
        prompt = f"""Analyze the following document and split it into {num_chunks} coherent sections.

IMPORTANT RULES:
1. Each section should contain a complete thought or topic
2. Maintain semantic coherence - don't break in the middle of concepts
3. Each section should be roughly {self.chunk_size} tokens but can vary for semantic completeness
4. Preserve all original text - do not summarize or modify content
5. Return ONLY a valid JSON array with each section as a string element

Document to split:
{text[:10000]}{"..." if len(text) > 10000 else ""}

Return format:
["section 1 full text here", "section 2 full text here", ...]

JSON array:"""

        try:
            response = await self.ollama_client.generate(prompt)
            
            # Try to parse JSON response
            chunks = json.loads(response)
            
            # Validate that we got a list
            if isinstance(chunks, list) and len(chunks) > 0:
                return chunks
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"LLM chunking failed, falling back to naive split: {e}")
        
        # Fallback to naive chunking if LLM fails
        return self._naive_split(text)
    
    def _naive_split(self, text: str) -> List[str]:
        """
        Fallback method: Token-based sliding window split with overlap.
        Uses tiktoken to create chunks of up to chunk_size tokens with
        chunk_overlap tokens of context overlap.
        """
        tokens = self.encoding.encode(text)
        if not tokens:
            return []
        window_size = max(self.chunk_size, 1)
        step_size = max(self.chunk_size - self.chunk_overlap, 1)
        chunks: List[str] = []
        for start in range(0, len(tokens), step_size):
            end = start + window_size
            chunk_tokens = tokens[start:end]
            if not chunk_tokens:
                continue
            chunk_text = self.encoding.decode(chunk_tokens)
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        return chunks

