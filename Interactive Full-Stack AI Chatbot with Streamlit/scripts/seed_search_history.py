import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db import get_db
from src.auth.auth_manager import register_user, ensure_default_accounts

def seed_searches():
    db = get_db()
    ensure_default_accounts(db)
    
    # Register demo users
    register_user("alice_dev", "alice123", "user", db)
    register_user("bob_analyst", "bob123", "user", db)
    
    # Sample queries and replies
    searches = [
        {
            "username": "alice_dev",
            "query": "How do I optimize Docker container sizes for Streamlit Python applications?",
            "reply": "To optimize Docker container sizes: use a multi-stage build, choose python:3.11-slim, avoid caching pip wheels with --no-cache-dir, and remove build-essential after compiling.",
            "latency_ms": 340.5,
            "tokens": 280,
            "feedback": "like",
            "sources": [{"source": "docker_best_practices.pdf", "page": 4, "score": 0.95}],
        },
        {
            "username": "bob_analyst",
            "query": "Calculate the compound annual growth rate (CAGR) from $50,000 to $120,000 over 5 years",
            "reply": "Using the CAGR formula: (120000 / 50000)**(1/5) - 1 = 19.14% annual growth rate.",
            "latency_ms": 185.0,
            "tokens": 140,
            "feedback": "like",
            "sources": None,
        },
        {
            "username": "alice_dev",
            "query": "What are the latest 2026 AI agent frameworks with multi-modal reasoning?",
            "reply": "The prominent frameworks include LangGraph 1.2+, Google Gemini Live agents, and CrewAI enterprise orchestrators with asynchronous tool routing.",
            "latency_ms": 420.0,
            "tokens": 310,
            "feedback": None,
            "sources": [{"source": "https://duckduckgo.com/?q=ai+agents+2026", "page": 1, "score": 0.89, "url": "https://duckduckgo.com"}],
        },
        {
            "username": "user",
            "query": "Summarize the key findings in our uploaded financial reports",
            "reply": "According to the uploaded financial report (Page 12), operating margin expanded by 340 basis points year-over-year.",
            "latency_ms": 290.0,
            "tokens": 230,
            "feedback": "like",
            "sources": [{"source": "financial_q3_report.pdf", "page": 12, "score": 0.92}],
        },
        {
            "username": "user",
            "query": "Can you debug this recursive function stack overflow?",
            "reply": "The issue is a missing base case condition when n <= 0, causing infinite recursive calls until recursion limit is reached.",
            "latency_ms": 210.0,
            "tokens": 190,
            "feedback": "like",
            "sources": None,
        },
    ]

    for item in searches:
        s_id = db.create_session(f"Search: {item['query'][:25]}...", username=item["username"])
        db.add_message(
            session_id=s_id,
            role="user",
            content=item["query"],
            username=item["username"],
        )
        db.add_message(
            session_id=s_id,
            role="assistant",
            content=item["reply"],
            username=item["username"],
            sources=item["sources"],
            feedback=item["feedback"],
            latency_ms=item["latency_ms"],
            tokens=item["tokens"],
        )

    print("Successfully seeded search audit history!")

if __name__ == "__main__":
    seed_searches()
