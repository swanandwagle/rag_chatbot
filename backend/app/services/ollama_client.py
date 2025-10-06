
import httpx
import json
from typing import List, AsyncGenerator
from app.config import settings


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.llm_model = settings.llm_model
        self.embedding_model = settings.embedding_model
        self.timeout = float(settings.ollama_timeout)
    
    async def generate(self, prompt: str) -> str:
        """
        Generate a complete text response using the LLM model (non-streaming).
        
        Args:
            prompt: The input prompt
            
        Returns:
            Complete generated text
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()["response"]

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream generated text chunks from the LLM model.
        
        Args:
            prompt: The input prompt
            
        Yields:
            Generated text chunks
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text using embedding model
        
        Args:
            text: The input text to embed
            
        Returns:
            List of embedding values
        """
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.embedding_model,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()["embedding"]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings
    
    async def health_check(self) -> bool:
        """
        Check if Ollama server is accessible
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                return response.status_code == 200
        except:
            return False

