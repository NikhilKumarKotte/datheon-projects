import time
from typing import List, Dict, Any, Iterator, Tuple, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from src.rag.vector_store import RAGManager


def build_rag_context_block(sources: List[Dict[str, Any]]) -> str:
    """Format retrieved document chunks into clean prompt context."""
    if not sources:
        return ""

    context_parts = ["\n[RELEVANT DOCUMENT CONTEXT FROM KNOWLEDGE BASE]:"]
    for i, s in enumerate(sources, 1):
        context_parts.append(
            f"\n--- Excerpt {i} (Source: {s.get('source')}, Page: {s.get('page', 1)}, Match Score: {s.get('score')}) ---\n"
            f"{s.get('content')}\n"
        )
    context_parts.append(
        "\nINSTRUCTIONS: Synthesize your answer accurately using the facts from the above excerpts when relevant. "
        "Cite the document name and page number when referencing specific details.\n"
    )
    return "\n".join(context_parts)


def stream_chat_response(
    model: Any,
    messages: List[BaseMessage],
    user_query: str,
    rag_manager: Optional[RAGManager] = None,
    system_prompt: Optional[str] = None,
) -> Tuple[Iterator[str], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Execute streaming inference, returning:
    - Token chunk iterator
    - List of retrieved RAG sources (if any)
    - Metadata dict (to be populated with latency and tokens)
    """
    retrieved_sources: List[Dict[str, Any]] = []

    # 1. Retrieve RAG context if documents are present
    if rag_manager and rag_manager.has_documents():
        retrieved_sources = rag_manager.search(user_query, top_k=3)

    # 2. Build final prompt payload
    augmented_user_query = user_query
    if retrieved_sources:
        rag_context = build_rag_context_block(retrieved_sources)
        augmented_user_query = f"{rag_context}\nUser Question: {user_query}"

    # 3. Assemble message sequence
    prepared_messages: List[BaseMessage] = []
    if system_prompt:
        prepared_messages.append(SystemMessage(content=system_prompt))

    # Append past history (excluding the current user turn which will be appended augmented)
    prepared_messages.extend(messages)
    prepared_messages.append(HumanMessage(content=augmented_user_query))

    metadata: Dict[str, Any] = {
        "start_time": time.perf_counter(),
        "token_count": 0,
        "latency_ms": 0.0,
        "sources": retrieved_sources,
    }

    def token_generator() -> Iterator[str]:
        full_response = []
        try:
            for chunk in model.stream(prepared_messages):
                token_text = ""
                if hasattr(chunk, "content"):
                    token_text = chunk.content
                    # Sometimes content is a list of dicts (multimodal/gemini)
                    if isinstance(token_text, list):
                        token_text = "".join(
                            item.get("text", "") if isinstance(item, dict) else str(item)
                            for item in token_text
                        )
                elif isinstance(chunk, str):
                    token_text = chunk

                if token_text:
                    full_response.append(token_text)
                    yield token_text
        except Exception as e:
            err_msg = f"\n\n⚠️ **Inference Error**: {str(e)}"
            yield err_msg
            full_response.append(err_msg)
        finally:
            end_time = time.perf_counter()
            metadata["latency_ms"] = round((end_time - metadata["start_time"]) * 1000, 1)
            # Estimate token count (~4 characters per token average)
            joined_text = "".join(full_response)
            metadata["token_count"] = max(1, len(joined_text) // 4)

    return token_generator(), retrieved_sources, metadata
