import streamlit as st
from src.config import APP_TITLE, APP_TAGLINE
from src.database.db import DatabaseManager
from src.auth.auth_manager import authenticate, register_user, ensure_default_accounts


def render_login_page(db: DatabaseManager):
    """Render high-aesthetic authentication portal for Admin and Users."""
    # Ensure default accounts are present
    ensure_default_accounts(db)

    st.markdown(
        f"""
        <div style="max-width: 480px; margin: 3rem auto 1.5rem auto; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🌌✨</div>
            <h1 style="font-size: 2rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, var(--text-primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {APP_TITLE}
            </h1>
            <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 0.3rem;">
                {APP_TAGLINE}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_card = st.container()

    with auth_card:
        _, center_col, _ = st.columns([0.2, 0.6, 0.2])

        with center_col:
            # Quick 1-Click Access for Evaluators / Reviewers
            st.markdown(
                """
                <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid var(--accent); border-radius: 12px; padding: 12px 16px; margin-bottom: 1.5rem;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">
                        ⚡ Quick Evaluator Access
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_admin, c_user = st.columns(2)
            with c_admin:
                if st.button("🛡️ Login as Admin", use_container_width=True, type="primary"):
                    user_data = authenticate("admin", "admin123", db)
                    if user_data:
                        st.session_state.is_authenticated = True
                        st.session_state.authenticated_user = user_data
                        st.rerun()

            with c_user:
                if st.button("👤 Login as User", use_container_width=True):
                    user_data = authenticate("user", "user123", db)
                    if user_data:
                        st.session_state.is_authenticated = True
                        st.session_state.authenticated_user = user_data
                        st.rerun()

            st.markdown("<div style='text-align: center; color: var(--text-secondary); margin: 1rem 0;'>── or enter credentials ──</div>", unsafe_allow_html=True)

            tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

            # 1. Sign In Tab
            with tab_login:
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("Username", placeholder="e.g. admin or user").strip().lower()
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Sign In to OmniStream", use_container_width=True, type="primary")

                    if submitted:
                        if not username or not password:
                            st.warning("Please enter both username and password.")
                        else:
                            user_data = authenticate(username, password, db)
                            if user_data:
                                st.session_state.is_authenticated = True
                                st.session_state.authenticated_user = user_data
                                st.success(f"Welcome back, **{user_data['username']}** ({user_data['role']})!")
                                st.rerun()
                            else:
                                st.error("Invalid username or password. Please verify credentials.")

            # 2. Register Tab
            with tab_register:
                with st.form("register_form", clear_on_submit=True):
                    reg_username = st.text_input("New Username", placeholder="Minimum 3 characters").strip().lower()
                    reg_password = st.text_input("New Password", type="password", placeholder="Minimum 4 characters")
                    reg_role = st.selectbox("Role", options=["user", "admin"], help="Admins can view system analytics and search logs.")
                    reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

                    if reg_submitted:
                        success, message = register_user(reg_username, reg_password, reg_role, db)
                        if success:
                            st.success(message + " You can now sign in.")
                        else:
                            st.error(message)

            st.caption(
                "🔒 **Default Credentials**: Admin (`admin` / `admin123`) • Demo User (`user` / `user123`)"
            )
