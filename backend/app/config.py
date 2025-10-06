
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import json

# Resolve .env path robustly so running from repo root or backend works
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
ENV_CANDIDATES = [
    BACKEND_DIR / ".env",   # backend/.env
    ROOT_DIR / ".env",      # repo-root/.env
    Path.cwd() / ".env",    # current working directory
]
ENV_FILE = next((p for p in ENV_CANDIDATES if p.exists()), BACKEND_DIR / ".env")


class Settings(BaseSettings):
    """Application settings loaded strictly from environment variables (.env)."""

    # Ollama settings
    ollama_base_url: str
    llm_model: str
    embedding_model: str
    ollama_timeout: float

    # Application settings
    upload_dir: str
    faiss_index_dir: str
    max_upload_size: int  # MB
    chunk_size: int  # Target tokens per chunk
    chunk_overlap: int  # Overlap tokens
    use_llm_chunking: bool  # Toggle to enable/disable LLM-based chunking

    # API settings
    api_prefix: str
    cors_origins: str

    # Settings config
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_origins
        if isinstance(value, str):
            s = value.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(v) for v in parsed]
                except Exception:
                    # Fall back to CSV if JSON parsing fails
                    pass
            return [v.strip() for v in s.split(",") if v.strip()]
        # Fallback for unexpected types
        try:
            return list(value)
        except Exception:
            return []


# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.faiss_index_dir).mkdir(parents=True, exist_ok=True)

