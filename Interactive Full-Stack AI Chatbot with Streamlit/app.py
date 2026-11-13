import os
import streamlit as st
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from src.config import APP_TITLE, THEMES
from src.database.db import get_db
from src.database.memory import ConversationMemoryManager
from src.auth.auth_manager import ensure_default_accounts
from src.llm.providers import get_chat_model, is_provider_configured
from src.llm.chains import stream_chat_response
from src.agent.orchestrator import run_agentic_loop
from src.rag.vector_store import get_rag_manager
from src.ui.styles import apply_theme
from src.ui.components import (
    render_header,
    render_sources_expander,
    render_thought_process,
    render_message_actions,
    render_message_telemetry,
    render_empty_state,
)
from src.ui.sidebar import render_sidebar
from src.ui.auth_page import render_login_page
from src.ui.admin_dashboard import render_admin_dashboard

# 1. Page Configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. State Initialization
if "theme_key" not in st.session_state:
    st.session_state.theme_key = os.getenv("DEFAULT_THEME", "midnight")

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

# Apply dynamic CSS styles for current theme
apply_theme(st.session_state.theme_key)

# 3. Database & Memory Setup
db = get_db(st.session_state.get("custom_db_url"))
ensure_default_accounts(db)
memory_mgr = ConversationMemoryManager(db)
rag_mgr = get_rag_manager()

# 4. Authentication Gate
if not st.session_state.get("is_authenticated", False):
    render_login_page(db)
    st.stop()

# Get authenticated user profile
current_user = st.session_state.get("authenticated_user", {"username": "guest", "role": "user"})
active_username = current_user.get("username", "guest")

# 5. Route to Admin Dashboard if selected
if st.session_state.get("current_view") == "admin" and current_user.get("role") == "admin":
    # Render sidebar with admin controls
    sidebar_config = render_sidebar(db, current_user=current_user)
    # Render Admin Search History & Audit Dashboard
    render_admin_dashboard(db)
    st.stop()

# 6. Render Sidebar for Main Chat View
sidebar_config = render_sidebar(db, current_user=current_user)
current_session_id = sidebar_config["current_session_id"]
agent_mode = sidebar_config.get("agent_mode", True)

# Load messages for the active conversation
if "messages" not in st.session_state or st.session_state.get("loaded_session_id") != current_session_id:
    st.session_state.messages = db.get_messages(current_session_id)
    st.session_state.loaded_session_id = current_session_id

# 7. Header Banner
render_header(
    provider=sidebar_config["provider"],
    model=sidebar_config["model"],
    message_count=len(st.session_state.messages),
    db_status=sidebar_config["db_status"],
    doc_count=sidebar_config["doc_count"],
    agent_mode=agent_mode,
)

# 8. Display Chat Message History
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources")
        thought = msg.get("thought_process")
        feedback = msg.get("feedback")
        latency = msg.get("latency_ms", 0.0)
        tokens = msg.get("tokens", 0)
        msg_id = msg.get("id", 0)

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="✨"):
                # Render CoT thought trace if available
                if thought:
                    render_thought_process(thought)

                # Render main response
                st.markdown(content)

                # Render sources & citations if available
                if sources:
                    render_sources_expander(sources)

                # Telemetry and micro-interactions
                render_message_telemetry(latency, tokens)
                render_message_actions(msg_id, content, feedback, db)

# 9. Render Empty State & Suggestions if conversation is fresh
quick_prompt = ""
if not st.session_state.messages:
    quick_prompt = render_empty_state()

# 10. User Chat Input Handling
user_input = st.chat_input("Ask a question, request web search, or compute math...")

# If user clicked a quick prompt card, prioritize it
prompt_to_process = user_input or quick_prompt

if prompt_to_process:
    # A. Check Provider Key Availability with Graceful Fallback
    if not is_provider_configured(sidebar_config["provider"], sidebar_config["api_key"]):
        st.warning(
            f"⚠️ **{sidebar_config['provider'].capitalize()} API Key not configured.** "
            f"You can enter your API key in the sidebar, or click below to run with **Demo Mode** instantly."
        )
        if st.button("🚀 Switch to Demo Mode & Continue", use_container_width=True):
            st.session_state.provider = "demo"
            st.session_state.model = "interactive-demo-agent"
            st.rerun()
        st.stop()

    # B. Render User Message Instantly
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt_to_process)

    # C. Persist User Message (linked to authenticated user)
    db.add_message(
        session_id=current_session_id,
        role="user",
        content=prompt_to_process,
        username=active_username,
    )

    # D. Auto-update Session Title on first user turn
    if len(st.session_state.messages) == 0:
        new_title = memory_mgr.generate_session_title(prompt_to_process)
        db.update_session_title(current_session_id, new_title)

    # Refresh session state messages
    st.session_state.messages = db.get_messages(current_session_id)

    # E. Stream Assistant Response
    with st.chat_message("assistant", avatar="✨"):
        try:
            # Instantiate configured LLM
            llm = get_chat_model(
                provider=sidebar_config["provider"],
                model_name=sidebar_config["model"],
                temperature=sidebar_config["temperature"],
                max_tokens=sidebar_config["max_tokens"],
                api_key=sidebar_config["api_key"],
            )

            # Convert history to LangChain messages
            past_lc_messages = memory_mgr.to_langchain_messages(
                st.session_state.messages[:-1],  # exclude current query
                system_prompt=sidebar_config["system_prompt"],
            )

            # Execute Agentic Loop or Standard Stream
            if agent_mode:
                token_iter, thought_trace, retrieved_sources, meta = run_agentic_loop(
                    model=llm,
                    messages=past_lc_messages,
                    user_query=prompt_to_process,
                    rag_manager=rag_mgr,
                    system_prompt=sidebar_config["system_prompt"],
                    agent_mode=True,
                )
            else:
                token_iter, retrieved_sources, meta = stream_chat_response(
                    model=llm,
                    messages=past_lc_messages,
                    user_query=prompt_to_process,
                    rag_manager=rag_mgr,
                    system_prompt=sidebar_config["system_prompt"],
                )
                thought_trace = None

            # Real-time token streaming using Streamlit native write_stream
            full_response_text = st.write_stream(token_iter)

            # Show thought process if agentic
            if thought_trace:
                render_thought_process(thought_trace)

            # Show citations if RAG or Web Search retrieved context
            if retrieved_sources:
                render_sources_expander(retrieved_sources)

            # Show response telemetry
            render_message_telemetry(meta.get("latency_ms", 0.0), meta.get("token_count", 0))

            # Persist assistant message to database (linked to authenticated user)
            new_msg_id = db.add_message(
                session_id=current_session_id,
                role="assistant",
                content=full_response_text,
                username=active_username,
                sources=retrieved_sources,
                thought_process=thought_trace,
                latency_ms=meta.get("latency_ms", 0.0),
                tokens=meta.get("token_count", 0),
            )

            # Update session state & rerun to sync all badges
            st.session_state.messages = db.get_messages(current_session_id)
            st.rerun()

        except Exception as e:
            st.error(f"❌ **Error generating response:** {str(e)}")
            st.info("💡 *Tip: If your cloud API quota is exhausted, you can switch to Demo Mode in the sidebar.*")
