import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db import get_db
from src.rag.vector_store import get_rag_manager
from src.rag.document_loader import DocumentChunk

def seed():
    db = get_db()
    
    # Check if sessions already exist
    sessions = db.list_sessions()
    
    # Create Demo Conversation 1: Full-Stack RAG & Architecture
    s1_id = db.create_session(
        title="Production RAG Architecture & Benchmarks",
        provider="google",
        model="gemini-2.5-flash",
    )
    
    db.add_message(
        session_id=s1_id,
        role="user",
        content="Can you explain how this Streamlit app coordinates multi-turn memory, RAG citations, and online database sync?",
    )
    
    rag_sources = [
        {
            "source": "omnistream_system_architecture.pdf",
            "page": 3,
            "score": 0.94,
            "content": "The DatabaseManager implements SQLAlchemy session pooling, supporting zero-config local SQLite and cloud-hosted PostgreSQL (Supabase/Neon) with automatic connection failover.",
        },
        {
            "source": "rag_pipeline_spec.pdf",
            "page": 7,
            "score": 0.88,
            "content": "Token streaming executes via generator yields connected to Streamlit st.write_stream, maintaining sub-50ms TTFT (Time-To-First-Token) and atomic message persistence.",
        },
    ]
    
    assistant_reply_1 = (
        "### 🏗️ OmniStream AI Architecture Breakdown\n\n"
        "OmniStream AI coordinates four decoupled layers to deliver production-grade responsiveness:\n\n"
        "1. **⚡ Reactive Presentation Layer (Streamlit)**:\n"
        "   - Utilizes `st.chat_message` and `st.write_stream` for word-by-word streaming.\n"
        "   - Theme engine dynamically injects CSS tokens across 5 distinct visual styles.\n\n"
        "2. **🧠 Conversational Memory & Persistence (SQLAlchemy)**:\n"
        "   - Every message, latency metric, and citation is persisted to the database.\n"
        "   - Sliding-window context trimmer preserves token efficiency during long dialogues.\n\n"
        "3. **📚 RAG Retrieval Pipeline**:\n"
        "   - Ingests PDF, TXT, CSV, and Markdown files.\n"
        "   - Uses vector similarity matching to inject grounded context with transparent source citations.\n\n"
        "```python\n"
        "# High-performance token generator pattern\n"
        "for chunk in model.stream(prepared_messages):\n"
        "    if chunk.content:\n"
        "        yield chunk.content\n"
        "```\n\n"
        "👉 *Notice the expandable citation card below showing exact document excerpts!*"
    )
    
    db.add_message(
        session_id=s1_id,
        role="assistant",
        content=assistant_reply_1,
        sources=rag_sources,
        latency_ms=412.5,
        tokens=348,
    )
    
    # Create Demo Conversation 2: Cloud Database Setup
    s2_id = db.create_session(
        title="Supabase & Neon PostgreSQL Migration Guide",
        provider="google",
        model="gemini-2.5-pro",
    )
    
    db.add_message(
        session_id=s2_id,
        role="user",
        content="How do I connect my live Supabase database for persistent cloud storage?",
    )
    
    assistant_reply_2 = (
        "Connecting your cloud PostgreSQL database (Supabase, Neon, AWS RDS) takes only two steps:\n\n"
        "### Step 1: Obtain your Connection String\n"
        "From your Supabase or Neon console, copy your Transaction Pooler or Direct URI:\n"
        "```bash\n"
        "postgresql+psycopg://postgres:[PASSWORD]@db.xyz.supabase.co:5432/postgres\n"
        "```\n\n"
        "### Step 2: Connect Live via the UI or `.env`\n"
        "- **Via UI**: Open the sidebar expander **Database & Memory -> Cloud Database Settings**, paste the URL, and click **Connect & Migrate**.\n"
        "- **Via `.env`**: Set `DATABASE_URL=...` and restart the container.\n\n"
        "The application will automatically create all required tables (`chat_sessions`, `chat_messages`, `document_records`) and verify connectivity with a green status indicator."
    )
    
    db.add_message(
        session_id=s2_id,
        role="assistant",
        content=assistant_reply_2,
        sources=None,
        latency_ms=295.0,
        tokens=210,
    )
    
    # Seed sample document record
    db.add_document_record("omnistream_system_architecture.pdf", "pdf", 14)
    db.add_document_record("rag_pipeline_spec.pdf", "pdf", 8)
    
    print(f"Successfully seeded demo conversations: {s1_id}, {s2_id}")

if __name__ == "__main__":
    seed()
