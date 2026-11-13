import streamlit as st
import pandas as pd
from typing import Optional
from src.database.db import DatabaseManager


def render_admin_dashboard(db: DatabaseManager):
    """
    Render Administrator Command Center showing search history audit logs,
    user queries, latency metrics, and system analytics.
    """
    # 1. Top Header & Navigation
    col_title, col_nav = st.columns([0.7, 0.3])
    with col_title:
        st.markdown(
            """
            <div style="margin-bottom: 1.2rem;">
                <h1 style="font-size: 1.8rem; font-weight: 800; margin: 0; color: var(--text-primary);">
                    🛡️ Admin Search History & Audit Dashboard
                </h1>
                <p style="color: var(--text-secondary); margin: 0.2rem 0 0 0; font-size: 0.9rem;">
                    Monitor, inspect, and analyze all user searches, tool invocations, and conversation queries.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_nav:
        if st.button("💬 Return to Chat Application", type="primary", use_container_width=True):
            st.session_state.current_view = "chat"
            st.rerun()

    # 2. Key System Metrics / KPIs
    analytics = db.get_system_analytics()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔍 Total Searches", analytics["total_searches"])
    c2.metric("👥 Total Users", analytics["total_users"])
    c3.metric("💬 Chat Sessions", analytics["total_sessions"])
    c4.metric("⏱️ Avg Latency", f"{analytics['avg_latency']} ms")
    c5.metric("💚 Positive Ratings", analytics["total_likes"])

    st.markdown("---")

    # 3. Search History Filters
    st.markdown("### 📋 Historical User Searches & Prompts")
    users = db.list_users()
    user_options = ["All Users"] + [u["username"] for u in users]

    f_col1, f_col2, f_col3 = st.columns([0.35, 0.45, 0.2])
    with f_col1:
        selected_user = st.selectbox("Filter by User", options=user_options)
    with f_col2:
        search_query = st.text_input("Search query text", placeholder="Type keywords to filter...")
    with f_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh Logs", use_container_width=True)

    # 4. Fetch Logs
    search_records = db.get_admin_search_history(
        filter_user=selected_user if selected_user != "All Users" else None,
        search_keyword=search_query,
    )

    if not search_records:
        st.info("No search queries match the active filters.")
        return

    # Convert to Pandas DataFrame for high-performance sorting and inspection
    df_data = []
    for r in search_records:
        feedback_display = "👍 Helpful" if r["feedback"] == "like" else ("👎 Needs work" if r["feedback"] == "dislike" else "—")
        df_data.append({
            "Timestamp (UTC)": r["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(r["timestamp"], "strftime") else str(r["timestamp"])[:19],
            "User": r["username"],
            "Search Query": r["query"],
            "Assistant Reply Excerpt": r["reply_preview"],
            "Latency (ms)": f"{r['latency_ms']:.0f}",
            "Tokens": r["tokens"],
            "Feedback": feedback_display,
            "Citations": "Yes 📑" if r["has_citations"] else "No",
        })

    df = pd.DataFrame(df_data)

    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Timestamp (UTC)": st.column_config.TextColumn("Timestamp", width="medium"),
            "User": st.column_config.TextColumn("User", width="small"),
            "Search Query": st.column_config.TextColumn("Search Query", width="large"),
            "Assistant Reply Excerpt": st.column_config.TextColumn("Response Preview", width="large"),
            "Latency (ms)": st.column_config.TextColumn("Latency", width="small"),
            "Tokens": st.column_config.NumberColumn("Tokens", width="small"),
            "Feedback": st.column_config.TextColumn("Rating", width="small"),
            "Citations": st.column_config.TextColumn("Citations", width="small"),
        },
        hide_index=True,
    )

    # 5. Expandable Query Details Viewer
    with st.expander("🔎 Deep Inspect Individual Query Logs", expanded=False):
        for idx, rec in enumerate(search_records[:15]):
            st.markdown(
                f"""
                <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--accent); margin-bottom: 6px;">
                        <span>👤 <b>{rec['username']}</b> • 📅 {str(rec['timestamp'])[:19]}</span>
                        <span>⏱️ {rec['latency_ms']:.0f} ms | 🔢 {rec['tokens']} tokens</span>
                    </div>
                    <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 4px; color: var(--text-primary);">
                        Query: "{rec['query']}"
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4;">
                        Response: {rec['reply_preview']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 6. Analytics Charts
    st.markdown("### 📊 Query Analytics & Distribution")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Searches per User**")
        user_counts = df["User"].value_counts()
        st.bar_chart(user_counts)

    with chart_col2:
        st.markdown("**User Feedback Sentiment**")
        feedback_counts = df["Feedback"].value_counts()
        st.bar_chart(feedback_counts)

    # 7. CSV Audit Export
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Full Search History Audit Log (CSV)",
        data=csv_bytes,
        file_name="omnistream_search_audit.csv",
        mime="text/csv",
        type="primary",
    )
