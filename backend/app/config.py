
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text:latest"
    
    # Application settings
    upload_dir: str = "../data/uploads"
    faiss_index_dir: str = "../data/faiss_index"
    max_upload_size: int = 50  # MB
    chunk_size: int = 1000  # Target tokens per chunk
    chunk_overlap: int = 200  # Overlap tokens
    use_llm_chunking: bool = False  # Toggle to enable/disable LLM-based chunking
    
    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.faiss_index_dir).mkdir(parents=True, exist_ok=True)

