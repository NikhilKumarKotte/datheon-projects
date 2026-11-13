"""
Vector store management module supporting both ChromaDB and FAISS.
Provides unified indexing, persistence, retrieval, and similarity scoring.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Union
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever

from src.config import CHROMA_PERSIST_DIR, FAISS_PERSIST_DIR, default_config
from src.embeddings import EmbeddingFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_chroma_class():
    """Dynamically loads the preferred Chroma class."""
    try:
        from langchain_chroma import Chroma
        return Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma
        return Chroma


def get_faiss_class():
    """Loads the FAISS vectorstore class."""
    from langchain_community.vectorstores import FAISS
    return FAISS


class VectorStoreManager:
    """Unified manager for ChromaDB and FAISS vector indices."""

    def __init__(
        self,
        chroma_dir: Optional[Path] = None,
        faiss_dir: Optional[Path] = None,
        embeddings: Optional[Embeddings] = None,
    ):
        self.chroma_dir = Path(chroma_dir or CHROMA_PERSIST_DIR)
        self.faiss_dir = Path(faiss_dir or FAISS_PERSIST_DIR)
        self._embeddings = embeddings

        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)

    @property
    def embeddings(self) -> Embeddings:
        """Lazily obtains embeddings if not explicitly injected."""
        if self._embeddings is None:
            self._embeddings = EmbeddingFactory.get_embeddings(
                provider=default_config.embedding_provider,
                model_name=default_config.embedding_model_name,
            )
        return self._embeddings

    def create_or_add_documents(
        self,
        documents: List[Document],
        store_type: str = "chroma",
        collection_name: str = "document_qa_collection",
    ) -> Any:
        """Indexes documents into the selected vector store and persists to disk.

        Args:
            documents: List of chunked Document instances.
            store_type: 'chroma' or 'faiss'.
            collection_name: Collection name for ChromaDB.

        Returns:
            The instantiated vector store.
        """
        if not documents:
            raise ValueError("No documents provided to index into vector store.")

        store_type = store_type.lower().strip()
        logger.info(
            f"Indexing {len(documents)} chunks into {store_type.upper()} vector store..."
        )

        if store_type == "chroma":
            ChromaClass = get_chroma_class()
            vector_store = ChromaClass.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.chroma_dir),
                collection_name=collection_name,
            )
            logger.info(f"Successfully persisted ChromaDB index at '{self.chroma_dir}'.")
            return vector_store

        elif store_type == "faiss":
            FAISSClass = get_faiss_class()
            # If an existing FAISS index exists on disk, append to it; otherwise create new
            index_file = self.faiss_dir / "index.faiss"
            if index_file.exists():
                try:
                    existing_store = FAISSClass.load_local(
                        folder_path=str(self.faiss_dir),
                        embeddings=self.embeddings,
                        allow_dangerous_deserialization=True,
                    )
                    existing_store.add_documents(documents)
                    existing_store.save_local(str(self.faiss_dir))
                    logger.info(f"Appended {len(documents)} chunks to existing FAISS index.")
                    return existing_store
                except Exception as e:
                    logger.warning(f"Could not append to FAISS, rebuilding index: {e}")

            vector_store = FAISSClass.from_documents(
                documents=documents,
                embedding=self.embeddings,
            )
            vector_store.save_local(str(self.faiss_dir))
            logger.info(f"Successfully persisted FAISS index at '{self.faiss_dir}'.")
            return vector_store

        else:
            raise ValueError(f"Unsupported vector store type: '{store_type}'. Choose 'chroma' or 'faiss'.")

    def load_store(
        self,
        store_type: str = "chroma",
        collection_name: str = "document_qa_collection",
    ) -> Optional[Any]:
        """Loads an existing persisted vector store from disk.

        Args:
            store_type: 'chroma' or 'faiss'.
            collection_name: Collection name for ChromaDB.

        Returns:
            Instantiated vector store or None if not found/empty.
        """
        store_type = store_type.lower().strip()

        if store_type == "chroma":
            # Check if directory has contents
            if not any(self.chroma_dir.iterdir()):
                logger.info(f"No existing ChromaDB index found at '{self.chroma_dir}'.")
                return None
            try:
                ChromaClass = get_chroma_class()
                store = ChromaClass(
                    persist_directory=str(self.chroma_dir),
                    embedding_function=self.embeddings,
                    collection_name=collection_name,
                )
                # Verify collection is non-empty
                count = store._collection.count() if hasattr(store, "_collection") else 1
                if count == 0:
                    logger.info("ChromaDB collection exists but is currently empty.")
                    return None
                return store
            except Exception as e:
                logger.warning(f"Error loading ChromaDB store: {e}")
                return None

        elif store_type == "faiss":
            index_file = self.faiss_dir / "index.faiss"
            if not index_file.exists():
                logger.info(f"No existing FAISS index file found at '{index_file}'.")
                return None
            try:
                FAISSClass = get_faiss_class()
                store = FAISSClass.load_local(
                    folder_path=str(self.faiss_dir),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                return store
            except Exception as e:
                logger.warning(f"Error loading FAISS store: {e}")
                return None

        else:
            raise ValueError(f"Unknown store type: '{store_type}'")

    def as_retriever(
        self,
        store_type: str = "chroma",
        k: int = 4,
        search_type: str = "similarity",
    ) -> VectorStoreRetriever:
        """Returns a LangChain retriever for the given vector store."""
        store = self.load_store(store_type=store_type)
        if store is None:
            raise RuntimeError(
                f"Cannot create retriever: {store_type.upper()} index does not exist. "
                "Please load and index documents first."
            )
        return store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k},
        )

    def similarity_search_with_confidence(
        self,
        query: str,
        k: int = 4,
        store_type: str = "chroma",
    ) -> List[Tuple[Document, float]]:
        """Performs similarity search and returns documents with normalized confidence scores.

        Args:
            query: The question or query string.
            k: Number of chunks to retrieve.
            store_type: 'chroma' or 'faiss'.

        Returns:
            List of (Document, confidence_score) where confidence_score is between 0.0 and 1.0.
        """
        store = self.load_store(store_type=store_type)
        if store is None:
            return []

        results_with_scores = store.similarity_search_with_score(query, k=k)
        normalized: List[Tuple[Document, float]] = []

        for doc, raw_score in results_with_scores:
            # Score normalization:
            # Chroma returns L2 squared distance (lower is closer; 0 is exact match) or cosine distance.
            # FAISS returns L2 distance by default.
            # Convert distance d to confidence score: s = 1.0 / (1.0 + d) or max(0, 1 - d/2)
            try:
                score_val = float(raw_score)
                if score_val >= 0:
                    confidence = round(1.0 / (1.0 + score_val), 4)
                else:
                    # Cosine similarity in [-1, 1]
                    confidence = round(max(0.0, min(1.0, (score_val + 1.0) / 2.0)), 4)
            except Exception:
                confidence = 0.85

            normalized.append((doc, confidence))

        return normalized

    def clear_store(self, store_type: str = "chroma") -> bool:
        """Clears/resets the persisted index on disk."""
        target_dir = self.chroma_dir if store_type.lower() == "chroma" else self.faiss_dir
        logger.info(f"Clearing vector store directory: {target_dir}")
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
                target_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store at {target_dir}: {e}")
            return False

    def get_stats(self, store_type: str = "chroma") -> Dict[str, Any]:
        """Returns statistics regarding index status and vector counts."""
        store_type = store_type.lower().strip()
        store = self.load_store(store_type=store_type)

        if store is None:
            return {
                "store_type": store_type,
                "is_indexed": False,
                "vector_count": 0,
                "path": str(self.chroma_dir if store_type == "chroma" else self.faiss_dir),
            }

        count = 0
        try:
            if store_type == "chroma":
                count = store._collection.count()
            elif store_type == "faiss":
                count = store.index.ntotal
        except Exception:
            count = "Active"

        return {
            "store_type": store_type,
            "is_indexed": True,
            "vector_count": count,
            "path": str(self.chroma_dir if store_type == "chroma" else self.faiss_dir),
        }
