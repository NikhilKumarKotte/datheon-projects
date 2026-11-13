"""
Configuration module for the Document Q&A Assistant.
Handles environment variables, storage paths, and model hyperparameters.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
FAISS_PERSIST_DIR = DATA_DIR / "faiss_db"
SAMPLE_DOCS_DIR = BASE_DIR / "sample_docs"

# Ensure runtime directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
FAISS_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Application configuration and hyperparameter settings."""

    # Chunking Configuration
    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "600"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

    # Vector Store Configuration ('chroma' or 'faiss')
    vector_store_type: str = os.getenv("RAG_VECTOR_STORE", "chroma").lower()
    chroma_dir: Path = CHROMA_PERSIST_DIR
    faiss_dir: Path = FAISS_PERSIST_DIR

    # Embeddings Configuration ('huggingface', 'openai', 'gemini')
    embedding_provider: str = os.getenv("RAG_EMBEDDING_PROVIDER", "huggingface").lower()
    embedding_model_name: str = os.getenv(
        "RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # LLM Configuration ('openai', 'gemini', 'groq', 'ollama', 'local')
    llm_provider: str = os.getenv("RAG_LLM_PROVIDER", "local").lower()
    llm_model_name: str = os.getenv("RAG_LLM_MODEL", "gpt-4o-mini")
    llm_temperature: float = float(os.getenv("RAG_LLM_TEMPERATURE", "0.0"))

    # Retrieval Configuration
    top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    score_threshold: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.2"))

    # API Keys
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    google_api_key: str = field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", "")
    )
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    def validate(self) -> None:
        """Validates configuration parameters."""
        if self.chunk_size <= self.chunk_overlap:
            raise ValueError(
                f"chunk_size ({self.chunk_size}) must be strictly greater than chunk_overlap ({self.chunk_overlap})"
            )
        if self.vector_store_type not in ["chroma", "faiss"]:
            raise ValueError(
                f"vector_store_type must be 'chroma' or 'faiss', got '{self.vector_store_type}'"
            )


# Default global instance
default_config = AppConfig()
