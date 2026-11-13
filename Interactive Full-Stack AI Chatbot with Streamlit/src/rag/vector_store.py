import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.rag.document_loader import DocumentChunk


class RAGManager:
    """In-memory high-performance vector retrieval engine for RAG knowledge augmentation."""

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[Any] = None
        self.indexed_files: set = set()

    def has_documents(self) -> bool:
        """Check if any documents are indexed."""
        return len(self.chunks) > 0

    def get_indexed_files(self) -> List[str]:
        """Return list of distinct indexed filenames."""
        return sorted(list(self.indexed_files))

    def add_chunks(self, new_chunks: List[DocumentChunk]):
        """Index new document chunks and rebuild vector index."""
        if not new_chunks:
            return

        # Avoid duplicate chunks by chunk_id
        existing_ids = {c.chunk_id for c in self.chunks}
        filtered_chunks = [c for c in new_chunks if c.chunk_id not in existing_ids]

        if not filtered_chunks:
            return

        self.chunks.extend(filtered_chunks)
        for c in filtered_chunks:
            self.indexed_files.add(c.source)

        corpus = [c.page_content for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=10000,
            sublinear_tf=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 4, threshold: float = 0.05) -> List[Dict[str, Any]]:
        """Retrieve most relevant document chunks for query."""
        if not self.has_documents() or not self.vectorizer or self.tfidf_matrix is None:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

            top_indices = np.argsort(scores)[::-1][:top_k]
            results = []

            for idx in top_indices:
                score = float(scores[idx])
                if score >= threshold:
                    chunk = self.chunks[idx]
                    results.append(
                        {
                            "source": chunk.source,
                            "page": chunk.page_number,
                            "content": chunk.page_content,
                            "score": round(score, 3),
                            "chunk_id": chunk.chunk_id,
                        }
                    )
            return results
        except Exception as e:
            print(f"Error during RAG vector search: {e}")
            return []

    def clear(self):
        """Reset the vector store index."""
        self.chunks.clear()
        self.indexed_files.clear()
        self.vectorizer = None
        self.tfidf_matrix = None


_rag_instance: Optional[RAGManager] = None


def get_rag_manager() -> RAGManager:
    """Get singleton RAGManager instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGManager()
    return _rag_instance
