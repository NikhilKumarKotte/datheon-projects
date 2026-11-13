import time
import re
from typing import List, Dict, Any, Iterator, Tuple, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from src.agent.tools import web_search, python_calc, rag_search
from src.rag.vector_store import RAGManager


def detect_tool_need(query: str, has_docs: bool) -> List[str]:
    """Autonomous routing to determine which tools are required for the query."""
    q_lower = query.lower()
    tools = []

    # Check for Document RAG need
    if has_docs:
        rag_keywords = ["document", "pdf", "file", "uploaded", "chunk", "text", "summary", "contract", "paper"]
        if any(k in q_lower for k in rag_keywords) or len(query.split()) > 4:
            tools.append("rag_search")

    # Check for Live Web Search need
    search_keywords = [
        "search", "latest", "recent", "news", "today", "current", "weather",
        "who is", "what happened", "stock", "price", "release", "2024", "2025", "2026"
    ]
    if any(k in q_lower for k in search_keywords):
        tools.append("web_search")

    # Check for Mathematical / Calculation need
    math_pattern = r"[\d\.]+\s*[\+\-\*\/\^]\s*[\d\.]+"
    if re.search(math_pattern, query) or any(k in q_lower for k in ["calculate", "compute", "solve", "sqrt", "equation"]):
        tools.append("python_calc")

    return tools


def run_agentic_loop(
    model: Any,
    messages: List[BaseMessage],
    user_query: str,
    rag_manager: Optional[RAGManager] = None,
    system_prompt: Optional[str] = None,
    agent_mode: bool = True,
) -> Tuple[Iterator[str], str, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Execute an autonomous agent loop with Chain-of-Thought (CoT) reasoning,
    tool execution, and streaming response synthesis.
    """
    start_time = time.perf_counter()
    has_docs = bool(rag_manager and rag_manager.has_documents())
    
    thought_steps: List[str] = []
    combined_sources: List[Dict[str, Any]] = []
    tool_observations: List[str] = []
    tools_used: List[str] = []

    if agent_mode:
        thought_steps.append("🎯 **Query Analysis**: Evaluating prompt intent and determining optimal tool routing...")
        tools_to_run = detect_tool_need(user_query, has_docs)

        # 1. RAG Search Tool Execution
        if "rag_search" in tools_to_run and rag_manager:
            thought_steps.append("📑 **Tool: Document Retriever**: Querying uploaded knowledge vectors for semantic matches...")
            rag_results = rag_search(user_query, top_k=3)
            if rag_results:
                tools_used.append("Document Retriever")
                combined_sources.extend(rag_results)
                tool_observations.append(
                    f"Retrieved {len(rag_results)} document chunks with high relevance from {rag_results[0].get('source')}."
                )
                thought_steps.append(f"✅ Found {len(rag_results)} relevant document excerpts.")
            else:
                thought_steps.append("ℹ️ Document vector query returned no high-confidence chunks.")

        # 2. Web Search Tool Execution
        if "web_search" in tools_to_run:
            thought_steps.append(f"🌐 **Tool: Live Web Search**: Querying DuckDuckGo for *\"{user_query[:50]}\"*...")
            web_results = web_search(user_query, max_results=3)
            if web_results and web_results[0].get("url"):
                tools_used.append("Web Search")
                for w in web_results:
                    combined_sources.append({
                        "source": w.get("title", "Web Result"),
                        "page": 1,
                        "content": w.get("snippet", ""),
                        "url": w.get("url", ""),
                        "score": 0.90,
                    })
                tool_observations.append(f"Retrieved {len(web_results)} live web search results.")
                thought_steps.append(f"✅ Acquired live web context from {len(web_results)} sources.")

        # 3. Python Math Tool Execution
        if "python_calc" in tools_to_run:
            thought_steps.append("🧮 **Tool: Python Calculator**: Parsing numerical expressions for precision math...")
            # Extract expression
            math_match = re.search(r"[\d\.\s\+\-\*\/\(\)\^]+", user_query)
            if math_match:
                expr = math_match.group(0).strip()
                calc_val = python_calc(expr)
                tools_used.append("Python Math Engine")
                tool_observations.append(f"Computed `{expr}` = {calc_val}")
                thought_steps.append(f"✅ Executed precision computation: `{expr}` = **{calc_val}**")

        thought_steps.append("💡 **Final Synthesis Strategy**: Integrating tool observations with parametric knowledge to formulate verified answer.")

    # Assemble contextual prompt
    context_blocks = []
    if combined_sources:
        context_blocks.append("[GROUNDED TOOL CONTEXT & CITATIONS]:")
        for i, s in enumerate(combined_sources, 1):
            source_tag = s.get('url') or s.get('source') or 'Knowledge Base'
            context_blocks.append(f"\n--- Excerpt {i} (Source: {source_tag}) ---\n{s.get('content')}\n")
    
    if tool_observations:
        context_blocks.append("\n[INTERMEDIATE TOOL OBSERVATIONS]:\n" + "\n".join(f"- {o}" for o in tool_observations))

    augmented_query = user_query
    if context_blocks:
        augmented_query = "\n".join(context_blocks) + f"\n\nUser Question: {user_query}\nPlease provide a clear, comprehensive answer citing the sources."

    # Prepare LangChain sequence
    prepared_messages: List[BaseMessage] = []
    if system_prompt:
        prepared_messages.append(SystemMessage(content=system_prompt))
    prepared_messages.extend(messages)
    prepared_messages.append(HumanMessage(content=augmented_query))

    metadata: Dict[str, Any] = {
        "start_time": start_time,
        "token_count": 0,
        "latency_ms": 0.0,
        "tools_used": tools_used,
    }

    thought_trace_str = "\n".join(f"- {step}" for step in thought_steps)

    def token_generator() -> Iterator[str]:
        full_text = []
        try:
            for chunk in model.stream(prepared_messages):
                txt = ""
                if hasattr(chunk, "content"):
                    txt = chunk.content
                    if isinstance(txt, list):
                        txt = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in txt)
                elif isinstance(chunk, str):
                    txt = chunk
                
                if txt:
                    full_text.append(txt)
                    yield txt
        except Exception as e:
            err_msg = f"\n\n⚠️ **Inference Error**: {str(e)}"
            yield err_msg
            full_text.append(err_msg)
        finally:
            end_time = time.perf_counter()
            metadata["latency_ms"] = round((end_time - metadata["start_time"]) * 1000, 1)
            metadata["token_count"] = max(1, len("".join(full_text)) // 4)

    return token_generator(), thought_trace_str, combined_sources, metadata
