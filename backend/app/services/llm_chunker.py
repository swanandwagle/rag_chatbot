
import json
import tiktoken
from typing import List, Dict
from transformers import AutoTokenizer
from app.services.ollama_client import OllamaClient
from app.config import settings


class LLMChunker:
    """Service for chunking documents using LLM to maintain semantic meaning"""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        # Prefer a Llama tokenizer for accurate token counts; fall back to tiktoken if unavailable.
        self.tokenizer = None
        self.encoding = None
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                getattr(settings, "tokenizer_model_name", "meta-llama/Meta-Llama-3.1-8B"),
                use_fast=True,
                local_files_only=getattr(settings, "hf_local_files_only", False),
            )
        except Exception as e:
            # Fallback to tiktoken approximation
            print(f"Tokenizer load failed, falling back to tiktoken: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def _encode_tokens(self, text: str) -> List[int]:
        if self.tokenizer is not None:
            return self.tokenizer.encode(text, add_special_tokens=False)
        # tiktoken fallback
        return self.encoding.encode(text)

    def _decode_tokens(self, token_ids: List[int]) -> str:
        if self.tokenizer is not None:
            return self.tokenizer.decode(token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        return self.encoding.decode(token_ids)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using available tokenizer."""
        return len(self._encode_tokens(text))
    
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
            # Use windowed semantic splitting to avoid truncation and respect model context
            chunks = await self._semantic_split_windowed(text)
        else:
            if getattr(settings, "use_sentence_aware_split", True):
                chunks = self._sentence_aware_split(text)
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
        
        # Create prompt for LLM to split intelligently (no truncation here; upstream is windowed)
        prompt = f"""Analyze the following document and split it into {num_chunks} coherent sections.

IMPORTANT RULES:
1. Each section should contain a complete thought or topic
2. Maintain semantic coherence - don't break in the middle of concepts
3. Each section should be roughly {self.chunk_size} tokens but can vary for semantic completeness
4. Preserve all original text - do not summarize or modify content
5. Return ONLY a valid JSON array with each section as a string element

Document to split:
{text}

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

    def _token_windows(self, text: str, window_tokens: int = 8000, overlap_tokens: int = 200) -> List[str]:
        """
        Create token-based windows to keep prompts within model context.
        Uses a small overlap to reduce boundary artifacts.
        """
        # Allow overriding via settings to compensate for tokenizer mismatches
        window_tokens = int(getattr(settings, "llm_window_tokens", window_tokens))
        overlap_tokens = int(getattr(settings, "llm_window_overlap_tokens", overlap_tokens))
        tokens = self._encode_tokens(text)
        if not tokens:
            return []
        window = max(window_tokens, 1)
        step = max(window_tokens - overlap_tokens, 1)
        windows: List[str] = []
        for start in range(0, len(tokens), step):
            end = start + window
            chunk_tokens = tokens[start:end]
            if not chunk_tokens:
                continue
            windows.append(self._decode_tokens(chunk_tokens))
        return windows

    async def _semantic_split_windowed(self, text: str) -> List[str]:
        """
        Run semantic split over token windows to avoid truncation and fit the LLM context window.
        Deduplicates overlapping outputs.
        """
        # Heuristic: window ~ 8k tokens with ~200 token overlap
        windows = self._token_windows(text, window_tokens=8000, overlap_tokens=200)
        if not windows:
            return []

        seen: set[int] = set()
        merged: List[str] = []
        for w in windows:
            parts = await self._semantic_split(w)
            for p in parts:
                s = p.strip()
                if not s:
                    continue
                h = hash(s)
                if h in seen:
                    continue
                seen.add(h)
                merged.append(s)
        return merged
    
    def _naive_split(self, text: str) -> List[str]:
        """
        Fallback method: Token-based sliding window split with overlap.
        Uses tiktoken to create chunks of up to chunk_size tokens with
        chunk_overlap tokens of context overlap.
        """
        tokens = self._encode_tokens(text)
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
            chunk_text = self._decode_tokens(chunk_tokens)
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        return chunks

    def _sentence_aware_split(self, text: str) -> List[str]:
        """
        Token-budgeted split that respects sentence boundaries and applies sentence overlap.
        Uses a regex sentence splitter as a lightweight fallback.
        """
        import re

        # Rough sentence split; handles ., !, ? followed by space and capital letter.
        # Not perfect (abbreviations/quotes), but sufficient without heavy dependencies.
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        sentences = [s.strip() for s in sentences if s and s.strip()]
        if not sentences:
            return []

        chunks: List[str] = []
        current_sentences: List[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            if sentence_tokens <= 0:
                continue

            # If adding this sentence exceeds chunk_size and we have content, finalize chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                if chunk_text.strip():
                    chunks.append(chunk_text)

                # 25% sentence overlap (min 2 sentences) to preserve context
                overlap_sentence_count = max(2, len(current_sentences) // 4)
                current_sentences = current_sentences[-overlap_sentence_count:]
                current_tokens = sum(self.count_tokens(s) for s in current_sentences)

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks

