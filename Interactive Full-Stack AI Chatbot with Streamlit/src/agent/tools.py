import math
from typing import List, Dict, Any, Optional
from src.rag.vector_store import get_rag_manager


def web_search(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Execute live DuckDuckGo web search to retrieve real-time factual information."""
    results = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            for r in raw_results:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    }
                )
    except Exception as e:
        results.append(
            {
                "title": "Search Query Note",
                "snippet": f"Web search could not retrieve live results: {str(e)}",
                "url": "",
            }
        )
    return results


def python_calc(expression: str) -> str:
    """Safely evaluate mathematical and algorithmic expressions."""
    # Whitelist safe mathematical functions
    safe_dict = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "math": math,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }

    # Clean expression
    clean_expr = expression.strip()
    if clean_expr.startswith("print(") and clean_expr.endswith(")"):
        clean_expr = clean_expr[6:-1]

    try:
        result = eval(clean_expr, {"__builtins__": {}}, safe_dict)
        return str(result)
    except Exception as e:
        return f"Calculation Error: {str(e)}"


def rag_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search uploaded knowledge documents."""
    rag_mgr = get_rag_manager()
    if not rag_mgr.has_documents():
        return []
    return rag_mgr.search(query, top_k=top_k)
