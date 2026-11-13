import html
import streamlit as st
from typing import List, Dict, Any, Optional
from src.config import APP_TITLE, APP_TAGLINE, SUPPORTED_PROVIDERS


def render_header(
    provider: str,
    model: str,
    message_count: int,
    db_status: str,
    doc_count: int,
    agent_mode: bool = True,
):
    """Render the top banner with application title and live telemetry badges."""
    provider_info = SUPPORTED_PROVIDERS.get(provider, {})
    provider_icon = provider_info.get("icon", "✨")
    provider_name = provider_info.get("name", provider)

    # Determine DB badge text
    db_badge = "🟢 SQLite" if "SQLite" in db_status else ("🟢 Cloud DB" if "🟢" in db_status else "🔴 DB Offline")
    mode_badge = "⚡ Agent Mode (Tools Active)" if agent_mode else "💬 Standard Chat"

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title-box">
                <h1>{APP_TITLE}</h1>
                <p>{APP_TAGLINE}</p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; align-items: center;">
                <span class="badge-pill" style="border-color: var(--accent); color: var(--accent);">{mode_badge}</span>
                <span class="badge-pill">{provider_icon} {provider_name}: <b>{model}</b></span>
                <span class="badge-pill">💬 {message_count} msgs</span>
                <span class="badge-pill">📂 {doc_count} docs</span>
                <span class="badge-pill">{db_badge}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_thought_process(thought_process: Optional[str]):
    """Render expandable CoT / Agent reasoning trace."""
    if not thought_process:
        return

    with st.expander("🧠 Agent Reasoning & Tool Trace", expanded=False):
        st.markdown(
            f"""
            <div style="font-size: 0.83rem; line-height: 1.6; color: var(--text-secondary); background: rgba(0,0,0,0.15); padding: 12px 16px; border-radius: 8px; border-left: 3px solid var(--accent);">
                {thought_process}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sources_expander(sources: List[Dict[str, Any]]):
    """Render collapsible citations drawer for RAG and web search responses."""
    if not sources:
        return

    with st.expander(f"📑 Sources & Citations ({len(sources)} references)", expanded=False):
        for s in sources:
            source_file = s.get("source", "Reference")
            page_num = s.get("page", 1)
            score = s.get("score", 0.0)
            content = s.get("content", "").strip()
            url = s.get("url", "")
            
            url_link = f"<a href='{url}' target='_blank' style='color: var(--accent); margin-left: 6px; font-size: 0.75rem;'>[Open Link ↗]</a>" if url else ""

            st.markdown(
                f"""
                <div class="citation-card">
                    <div class="citation-title">
                        <span>📄 {source_file} {f'(Page {page_num})' if not url else ''} {url_link}</span>
                        <span>Relevance: <code>{int(score * 100)}%</code></span>
                    </div>
                    <div class="citation-snippet">"{content[:260]}..."</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_message_actions(message_id: int, content: str, current_feedback: Optional[str] = None, db = None):
    """Render micro-interaction action bar (Copy, Read Aloud, Like, Dislike)."""
    col_tele, col_act = st.columns([0.65, 0.35])
    
    with col_act:
        c_copy, c_tts, c_like, c_dislike = st.columns(4)
        
        # 1. Copy snippet
        with c_copy:
            escaped_content = html.escape(content).replace('"', '&quot;').replace('\n', ' ')
            st.markdown(
                f"""
                <button onclick="navigator.clipboard.writeText(`{escaped_content}`); alert('Copied to clipboard!');" 
                        class="action-btn" title="Copy to clipboard">
                    📋
                </button>
                """,
                unsafe_allow_html=True,
            )
            
        # 2. Text-to-Speech (Web Speech API)
        with c_tts:
            clean_speech = html.escape(content.replace("`", "").replace("*", "")).replace('"', '\\"').replace('\n', ' ')[:400]
            st.markdown(
                f"""
                <button onclick="window.speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(`{clean_speech}`); window.speechSynthesis.speak(u);" 
                        class="action-btn" title="Read Aloud">
                    🔊
                </button>
                """,
                unsafe_allow_html=True,
            )

        # 3. Like feedback
        with c_like:
            like_icon = "👍" if current_feedback != "like" else "💚"
            if st.button(like_icon, key=f"like_{message_id}", help="Helpful response"):
                if db:
                    new_val = None if current_feedback == "like" else "like"
                    db.update_message_feedback(message_id, new_val)
                    st.rerun()

        # 4. Dislike feedback
        with c_dislike:
            dislike_icon = "👎" if current_feedback != "dislike" else "💔"
            if st.button(dislike_icon, key=f"dislike_{message_id}", help="Needs improvement"):
                if db:
                    new_val = None if current_feedback == "dislike" else "dislike"
                    db.update_message_feedback(message_id, new_val)
                    st.rerun()


def render_message_telemetry(latency_ms: float = 0.0, tokens: int = 0):
    """Render subtle latency and token stats below assistant messages."""
    if latency_ms > 0 or tokens > 0:
        st.markdown(
            f"""
            <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 4px; display: flex; gap: 12px; align-items: center;">
                <span>⏱️ {latency_ms:.0f} ms</span>
                <span>🔢 ~{tokens} tokens</span>
                <span>⚡ Real-time Streamed</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state() -> str:
    """Render welcome card with quick prompt suggestions for fresh chats."""
    st.markdown(
        """
        <div style="text-align: center; padding: 2.2rem 1rem; border-radius: 14px; border: 1px dashed var(--border-color); background: rgba(255, 255, 255, 0.02); margin: 1.2rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.4rem;">🤖✨</div>
            <h3 style="margin: 0; color: var(--text-primary); font-size: 1.35rem;">How can I assist you today?</h3>
            <p style="color: var(--text-secondary); max-width: 540px; margin: 0.4rem auto 1.4rem auto; font-size: 0.88rem;">
                Select a topic below, upload documents in the sidebar for RAG Q&A, or ask anything to get real-time streaming AI answers with persistent memory.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    selected_prompt = ""

    with col1:
        if st.button("💡 Explain Modern LLM RAG Architecture", use_container_width=True):
            selected_prompt = "Can you explain how modern Retrieval-Augmented Generation (RAG) works from document chunking to vector similarity search and prompt synthesis?"
        if st.button("🌐 Search Latest 2026 AI Agent Breakthroughs", use_container_width=True):
            selected_prompt = "Search the web for the latest artificial intelligence agent and reasoning model breakthroughs in 2026."

    with col2:
        if st.button("🧮 Compute Complex Scientific Equation", use_container_width=True):
            selected_prompt = "Calculate the compound interest on $25,000 invested at 7.5% annual rate compounded monthly for 10 years: calculate 25000 * (1 + 0.075/12)**(12 * 10)"
        if st.button("💻 Draft a Production Python FastAPI Service", use_container_width=True):
            selected_prompt = "Write a production-ready Python FastAPI microservice with Pydantic v2 schemas, JWT authentication, and structured logging."

    return selected_prompt
