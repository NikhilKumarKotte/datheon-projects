"""
Embedding models factory and manager.
Supports local open-source HuggingFace models (100% free & offline),
as well as cloud providers (OpenAI, Google Gemini).
"""

import os
import logging
from typing import Optional
from langchain_core.embeddings import Embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """Factory to instantiate and cache embedding models."""

    _cached_instance: Optional[Embeddings] = None
    _cached_key: Optional[str] = None

    @classmethod
    def get_embeddings(
        cls,
        provider: str = "huggingface",
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Embeddings:
        """Returns an Embeddings instance based on provider.

        Args:
            provider: 'huggingface', 'openai', or 'gemini'.
            model_name: Optional specific model identifier.
            api_key: Optional API key override.

        Returns:
            LangChain Embeddings instance.
        """
        provider = (provider or "huggingface").lower().strip()
        cache_key = f"{provider}_{model_name}"

        if cls._cached_instance and cls._cached_key == cache_key:
            return cls._cached_instance

        logger.info(f"Initializing embedding model: provider='{provider}', model='{model_name}'")

        if provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                logger.warning(
                    "OPENAI_API_KEY is missing! Falling back to local HuggingFace embeddings."
                )
                return cls.get_embeddings(provider="huggingface")

            target_model = model_name or "text-embedding-3-small"
            instance = OpenAIEmbeddings(model=target_model, openai_api_key=key)

        elif provider in {"gemini", "google"}:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            key = api_key or os.getenv("GOOGLE_API_KEY")
            if not key:
                logger.warning(
                    "GOOGLE_API_KEY is missing! Falling back to local HuggingFace embeddings."
                )
                return cls.get_embeddings(provider="huggingface")

            target_model = model_name or "models/text-embedding-004"
            instance = GoogleGenerativeAIEmbeddings(
                model=target_model, google_api_key=key
            )

        else:
            # HuggingFace (Local & Free)
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings

            target_model = model_name or "sentence-transformers/all-MiniLM-L6-v2"
            instance = HuggingFaceEmbeddings(
                model_name=target_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

        cls._cached_instance = instance
        cls._cached_key = cache_key
        return instance
