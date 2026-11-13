"""
Text splitting and chunking module using RecursiveCharacterTextSplitter.
Divides long document passages into semantically coherent overlapping segments
with enriched metadata for citation precision.
"""

from typing import List, Dict, Any, Optional
import logging
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunkerService:
    """Manages recursive chunking of documents into vector-ready segments."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None,
    ):
        """Initializes the text chunker.

        Args:
            chunk_size: Maximum character length per chunk.
            chunk_overlap: Overlapping characters between consecutive chunks.
            separators: Hierarchical list of separators to split on.
        """
        if chunk_size <= chunk_overlap:
            raise ValueError(
                f"chunk_size ({chunk_size}) must be greater than chunk_overlap ({chunk_overlap})."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits raw documents into smaller, overlapping chunks with enriched metadata.

        Args:
            documents: Raw document objects from document loader.

        Returns:
            List of chunked Document instances with citation tags.
        """
        if not documents:
            logger.warning("No documents provided for text splitting.")
            return []

        logger.info(
            f"Chunking {len(documents)} document pages with chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}..."
        )

        raw_chunks = self.splitter.split_documents(documents)
        enriched_chunks: List[Document] = []

        for idx, chunk in enumerate(raw_chunks):
            # Clean excess whitespace
            cleaned_text = chunk.page_content.strip()
            if not cleaned_text:
                continue

            metadata = dict(chunk.metadata)
            file_name = metadata.get("file_name", "document")
            page_num = metadata.get("page", 1)

            # Assign deterministic unique chunk ID and metrics
            metadata["chunk_id"] = f"{file_name}_p{page_num}_c{idx}"
            metadata["char_count"] = len(cleaned_text)
            metadata["word_count"] = len(cleaned_text.split())

            enriched_chunks.append(
                Document(page_content=cleaned_text, metadata=metadata)
            )

        stats = self.get_chunk_statistics(enriched_chunks)
        logger.info(
            f"Splitting complete: Generated {stats['total_chunks']} chunks. "
            f"Avg length: {stats['avg_chars']} chars."
        )
        return enriched_chunks

    @staticmethod
    def get_chunk_statistics(chunks: List[Document]) -> Dict[str, Any]:
        """Calculates useful diagnostics on the resulting chunks."""
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chars": 0,
                "min_chars": 0,
                "max_chars": 0,
            }

        lengths = [len(c.page_content) for c in chunks]
        return {
            "total_chunks": len(chunks),
            "avg_chars": round(sum(lengths) / len(lengths), 1),
            "min_chars": min(lengths),
            "max_chars": max(lengths),
        }
