import streamlit as st
from typing import Dict, Any, List
from src.config import THEMES, SUPPORTED_PROVIDERS, SYSTEM_PERSONAS
from src.database.db import DatabaseManager, get_db
from src.rag.document_loader import process_uploaded_files
from src.rag.vector_store import get_rag_manager


def render_sidebar(db: DatabaseManager, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Render complete sidebar with:
    - User Profile & Admin Navigation
    - Session management (New, Switch, Rename, Delete)
    - Theme changer
    - AI Provider & Model configuration
    - Online Cloud Database settings
    - Document Knowledge Base / RAG uploads
    - Export tools
    """
    # --- 0. User Profile & Role Navigation ---
    username = current_user.get("username", "guest") if current_user else "guest"
    role = current_user.get("role", "user") if current_user else "user"
    is_admin = (role == "admin")

    st.sidebar.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px 14px; margin-bottom: 0.8rem;">
            <div style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 700;">Account</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
                👤 {username} <span style="font-size: 0.75rem; color: var(--accent); font-weight: 600;">({role.upper()})</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_out, col_adm = st.sidebar.columns([0.5, 0.5] if is_admin else [1.0, 0.001])
    with col_out:
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            st.session_state.is_authenticated = False
            st.session_state.authenticated_user = None
            st.session_state.current_view = "login"
            st.rerun()

    if is_admin:
        with col_adm:
            curr_view = st.session_state.get("current_view", "chat")
            target_view = "chat" if curr_view == "admin" else "admin"
            btn_label = "💬 Chat" if curr_view == "admin" else "🛡️ Audit"
            if st.button(btn_label, key="admin_nav_btn", use_container_width=True, type="primary" if curr_view != "admin" else "secondary"):
                st.session_state.current_view = target_view
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💬 Conversations")

    # --- 1. New Chat Button ---
    if st.sidebar.button("➕ New Conversation", type="primary", use_container_width=True):
        new_id = db.create_session(
            title="New Conversation",
            provider=st.session_state.get("provider", "google"),
            model=st.session_state.get("model", "gemini-2.5-flash"),
            username=username,
        )
        st.session_state.current_session_id = new_id
        st.session_state.messages = []
        st.session_state.current_view = "chat"
        st.rerun()

    # --- 2. Chat Sessions List ---
    sessions = db.list_sessions(username=username)
    if not sessions:
        init_id = db.create_session(username=username)
        st.session_state.current_session_id = init_id
        sessions = db.list_sessions(username=username)

    valid_ids = [s["session_id"] for s in sessions]
    if st.session_state.get("current_session_id") not in valid_ids:
        st.session_state.current_session_id = valid_ids[0]

    current_id = st.session_state.current_session_id

    # Session Selector Container
    with st.sidebar.container(height=180):
        for s in sessions:
            s_id = s["session_id"]
            is_active = (s_id == current_id)
            title = s["title"]
            col_sess, col_del = st.columns([0.82, 0.18])
            with col_sess:
                button_label = f"▸ {title}" if is_active else title
                if st.button(
                    button_label,
                    key=f"sess_btn_{s_id}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.current_session_id = s_id
                    st.session_state.messages = db.get_messages(s_id)
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_sess_{s_id}", help="Delete conversation"):
                    db.delete_session(s_id)
                    remaining = db.list_sessions()
                    if remaining:
                        st.session_state.current_session_id = remaining[0]["session_id"]
                        st.session_state.messages = db.get_messages(remaining[0]["session_id"])
                    else:
                        brand_new = db.create_session()
                        st.session_state.current_session_id = brand_new
                        st.session_state.messages = []
                    st.rerun()

    st.sidebar.markdown("---")

    # --- 3. Dynamic Theme Changer ---
    st.sidebar.markdown("### 🎨 Visual Theme")
    selected_theme = st.sidebar.selectbox(
        "Theme Style",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.get("theme_key", "midnight")),
        format_func=lambda k: f"{THEMES[k]['icon']} {THEMES[k]['name']}",
        key="theme_selector",
    )
    if selected_theme != st.session_state.get("theme_key"):
        st.session_state.theme_key = selected_theme
        st.rerun()

    st.sidebar.markdown("---")

    # --- 4. AI Provider & Model Configuration ---
    st.sidebar.markdown("### ⚙️ AI Engine Settings")
    provider_keys = list(SUPPORTED_PROVIDERS.keys())
    current_provider = st.session_state.get("provider", "google")
    prov_idx = provider_keys.index(current_provider) if current_provider in provider_keys else 0

    chosen_provider = st.sidebar.selectbox(
        "Provider",
        options=provider_keys,
        index=prov_idx,
        format_func=lambda k: f"{SUPPORTED_PROVIDERS[k]['icon']} {SUPPORTED_PROVIDERS[k]['name']}",
    )
    st.session_state.provider = chosen_provider

    provider_info = SUPPORTED_PROVIDERS[chosen_provider]
    available_models = provider_info["models"]
    current_model = st.session_state.get("model", provider_info["default_model"])
    model_idx = available_models.index(current_model) if current_model in available_models else 0

    chosen_model = st.sidebar.selectbox("Model", options=available_models, index=model_idx)
    st.session_state.model = chosen_model

    # API Key Input (if required)
    custom_api_key = ""
    if provider_info["api_key_env"]:
        env_key_name = provider_info["api_key_env"]
        placeholder_text = f"Using {env_key_name} from env" if os_has_env(env_key_name) else f"Paste {env_key_name}"
        custom_api_key = st.sidebar.text_input(
            f"{provider_info['name']} API Key",
            type="password",
            value=st.session_state.get(f"{chosen_provider}_api_key", ""),
            placeholder=placeholder_text,
            help=f"Optionally provide an API key for {provider_info['name']}. Leave blank to use environment variable.",
        )
        st.session_state[f"{chosen_provider}_api_key"] = custom_api_key

    # Persona & Parameters
    persona_choice = st.sidebar.selectbox("System Persona", options=list(SYSTEM_PERSONAS.keys()))
    system_prompt = SYSTEM_PERSONAS[persona_choice]

    with st.sidebar.expander("🛠️ Advanced Model Parameters", expanded=False):
        temperature = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.7, 0.05)
        max_tokens = st.slider("Max Output Tokens", 512, 4096, 2048, 256)
        custom_system = st.text_area("Custom System Prompt Override", value="", placeholder="Leave blank to use selected persona")
        if custom_system.strip():
            system_prompt = custom_system.strip()

    # Agent Mode Toggle
    agent_mode = st.sidebar.toggle(
        "⚡ Autonomous Agent Mode",
        value=st.session_state.get("agent_mode", True),
        help="Enable tool routing (DuckDuckGo Web Search, Python Math Engine, Document RAG) with CoT reasoning.",
    )
    st.session_state.agent_mode = agent_mode

    st.sidebar.markdown("---")

    # --- 5. Online Cloud Database Integration ---
    st.sidebar.markdown("### 🗄️ Database & Memory")
    is_ok, db_msg = db.test_connection()
    if is_ok:
        st.sidebar.success(db_msg, icon="✅")
    else:
        st.sidebar.error(db_msg, icon="⚠️")

    with st.sidebar.expander("☁️ Cloud Database Settings", expanded=False):
        st.markdown(
            "Connect an online database (PostgreSQL, Supabase, Neon) to sync chat sessions across devices and deployments."
        )
        new_db_url = st.text_input(
            "Database Connection URL",
            value=st.session_state.get("custom_db_url", ""),
            placeholder="postgresql+psycopg://user:pass@ep-xyz.neon.tech/neondb",
            type="password",
        )
        if st.button("Connect & Migrate Database", use_container_width=True):
            if new_db_url.strip():
                try:
                    new_mgr = get_db(new_db_url.strip())
                    ok, msg = new_mgr.test_connection()
                    if ok:
                        st.session_state.custom_db_url = new_db_url.strip()
                        st.sidebar.success(f"Connected: {msg}")
                        st.rerun()
                    else:
                        st.sidebar.error(msg)
                except Exception as err:
                    st.sidebar.error(f"Failed to connect: {err}")
            else:
                st.sidebar.warning("Enter a valid database connection string.")

    st.sidebar.markdown("---")

    # --- 6. RAG Document Knowledge Base ---
    st.sidebar.markdown("### 📚 Knowledge Base (RAG)")
    rag_mgr = get_rag_manager()
    
    uploaded_files = st.sidebar.file_uploader(
        "Upload Documents for Contextual Q&A",
        type=["pdf", "txt", "md", "csv"],
        accept_multiple_files=True,
        help="Upload files to query with full source citations",
    )

    if uploaded_files and st.sidebar.button("⚡ Index Uploaded Documents", use_container_width=True):
        with st.spinner("Processing & vectorizing documents..."):
            chunks = process_uploaded_files(uploaded_files)
            if chunks:
                rag_mgr.add_chunks(chunks)
                for f in uploaded_files:
                    f_name = getattr(f, "name", "unknown")
                    db.add_document_record(f_name, f_name.split(".")[-1], len(chunks))
                st.sidebar.success(f"Indexed {len(chunks)} chunks across {len(uploaded_files)} files!")
                st.rerun()
            else:
                st.sidebar.warning("No readable text found in uploaded files.")

    indexed_docs = rag_mgr.get_indexed_files()
    if indexed_docs:
        st.sidebar.markdown(f"**Indexed Documents ({len(indexed_docs)}):**")
        for doc in indexed_docs:
            st.sidebar.caption(f"• 📄 {doc}")
        if st.sidebar.button("🗑️ Clear Indexed Documents", use_container_width=True):
            rag_mgr.clear()
            st.sidebar.info("Knowledge base cleared.")
            st.rerun()
    else:
        st.sidebar.caption("No documents currently indexed.")

    st.sidebar.markdown("---")

    # --- 7. Export Tools ---
    st.sidebar.markdown("### 📥 Export Chat")
    current_msgs = db.get_messages(current_id)
    curr_sess = db.get_session(current_id) or {"title": "Conversation"}

    from src.database.memory import ConversationMemoryManager
    mem_mgr = ConversationMemoryManager(db)

    md_export = mem_mgr.export_as_markdown(curr_sess.get("title", "Conversation"), current_msgs)
    json_export = mem_mgr.export_as_json(curr_sess, current_msgs)

    c1, c2 = st.sidebar.columns(2)
    with c1:
        st.download_button(
            "📝 Markdown",
            data=md_export,
            file_name=f"chat_{current_id[:8]}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "📦 JSON",
            data=json_export,
            file_name=f"chat_{current_id[:8]}.json",
            mime="application/json",
            use_container_width=True,
        )

    return {
        "current_session_id": current_id,
        "provider": chosen_provider,
        "model": chosen_model,
        "api_key": custom_api_key,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "agent_mode": agent_mode,
        "db_status": db_msg,
        "doc_count": len(indexed_docs),
    }


def os_has_env(env_var_name: str) -> bool:
    """Helper to check if an environment variable is populated."""
    import os
    val = os.getenv(env_var_name)
    return bool(val and val.strip())
