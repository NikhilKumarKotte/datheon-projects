"""
Utility functions for text formatting, citation formatting, and logging.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
from langchain_core.documents import Document


def format_citation_markdown(citations: List[Dict[str, Any]]) -> str:
    """Formats a list of retrieved chunk citations into clean GitHub Markdown.

    Args:
        citations: List of citation dictionaries containing source, page, confidence, excerpt.

    Returns:
        Formatted Markdown text.
    """
    if not citations:
        return "*No sources were cited for this response.*"

    md_lines = ["\n### 📚 Verified Source Citations\n"]
    for idx, cite in enumerate(citations, 1):
        source_name = cite.get("file_name", "Unknown File")
        page = cite.get("page", 1)
        confidence = cite.get("confidence", 0.0)
        confidence_str = f"{confidence * 100:.1f}%" if isinstance(confidence, (int, float)) else "N/A"
        excerpt = cite.get("excerpt", "").strip()

        md_lines.append(f"**[{idx}] `{source_name}` (Page {page})** — *Confidence: {confidence_str}*")
        if excerpt:
            # Format excerpt with blockquote
            clean_excerpt = excerpt.replace("\n", " ")
            if len(clean_excerpt) > 280:
                clean_excerpt = clean_excerpt[:277] + "..."
            md_lines.append(f"> \"{clean_excerpt}\"\n")

    return "\n".join(md_lines)


def extract_citations_from_docs(
    docs_with_scores: List[Tuple[Document, float]]
) -> List[Dict[str, Any]]:
    """Converts retrieved documents with scores into standardized citation dicts.

    Args:
        docs_with_scores: List of (Document, confidence_score) tuples.

    Returns:
        List of structured citation dictionaries.
    """
    citations = []
    seen = set()

    for doc, score in docs_with_scores:
        meta = doc.metadata or {}
        file_name = meta.get("file_name") or Path(meta.get("source", "document")).name
        page = meta.get("page", 1)
        chunk_id = meta.get("chunk_id", f"{file_name}_p{page}")

        # Deduplicate identical chunks
        if chunk_id in seen:
            continue
        seen.add(chunk_id)

        citations.append({
            "chunk_id": chunk_id,
            "file_name": file_name,
            "source_path": meta.get("source", ""),
            "page": page,
            "confidence": score,
            "excerpt": doc.page_content,
        })

    return citations


def build_system_context_string(docs: List[Document]) -> str:
    """Builds a formatted context block with clear citation markers for the LLM.

    Args:
        docs: Retrieved context documents.

    Returns:
        Structured string to pass into prompt template.
    """
    context_blocks = []
    for idx, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        file_name = meta.get("file_name") or Path(meta.get("source", "document")).name
        page = meta.get("page", 1)

        block = (
            f"--- [Document: {file_name} | Page: {page}] ---\n"
            f"{doc.page_content.strip()}"
        )
        context_blocks.append(block)

    return "\n\n".join(context_blocks)
