import streamlit as st
from src.config import THEMES


def get_theme_css(theme_key: str = "midnight") -> str:
    """Generate comprehensive modern CSS tokens and styles for chosen theme."""
    t = THEMES.get(theme_key, THEMES["midnight"])

    return f"""
    <style>
    /* Global Root Variables */
    :root {{
        --bg-primary: {t['bg_primary']};
        --bg-secondary: {t['bg_secondary']};
        --bg-card: {t['bg_card']};
        --text-primary: {t['text_primary']};
        --text-secondary: {t['text_secondary']};
        --accent: {t['accent']};
        --accent-hover: {t['accent_hover']};
        --user-msg-bg: {t['user_msg_bg']};
        --assistant-msg-bg: {t['assistant_msg_bg']};
        --border-color: {t['border']};
        --code-bg: {t['code_bg']};
    }}

    /* Main Container & Background */
    .stApp {{
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color) !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {{
        color: var(--text-primary) !important;
    }}

    /* Header & Branding */
    .app-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.2rem 1.6rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }}

    .app-title-box h1 {{
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, var(--text-primary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }}

    .app-title-box p {{
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin: 0.2rem 0 0 0;
    }}

    .badge-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid var(--border-color);
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-primary);
    }}

    /* Chat Messages */
    .stChatMessage {{
        padding: 1rem 1.25rem !important;
        border-radius: 12px !important;
        margin-bottom: 1rem !important;
        border: 1px solid var(--border-color) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    
    .stChatMessage:hover {{
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }}

    /* User Message Bubble */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
        background-color: var(--user-msg-bg) !important;
        border-color: var(--accent) !important;
    }}

    /* Assistant Message Bubble */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
        background-color: var(--assistant-msg-bg) !important;
    }}

    /* Code Blocks */
    pre, code {{
        background-color: var(--code-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }}

    /* Chat Input Bar */
    .stChatInputContainer {{
        padding-top: 10px;
    }}
    
    .stChatInput {{
        border-radius: 12px !important;
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
    }}

    .stChatInput textarea {{
        color: var(--text-primary) !important;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}

    .stButton > button:hover {{
        background-color: var(--accent) !important;
        color: #ffffff !important;
        border-color: var(--accent-hover) !important;
        transform: translateY(-1px);
    }}

    /* Primary Buttons */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--accent), var(--accent-hover)) !important;
        color: #ffffff !important;
        border: none !important;
    }}

    /* Micro-interaction Action Buttons */
    .action-btn {{
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        padding: 3px 8px !important;
        cursor: pointer !important;
        font-size: 0.8rem !important;
        transition: all 0.15s ease !important;
        color: var(--text-secondary) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    .action-btn:hover {{
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
        transform: scale(1.08) !important;
    }}

    /* Expander / Citations */
    .streamlit-expanderHeader {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        font-size: 0.85rem !important;
    }}

    .citation-card {{
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.82rem;
    }}

    .citation-title {{
        font-weight: 600;
        color: var(--accent);
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }}

    .citation-snippet {{
        color: var(--text-secondary);
        font-style: italic;
    }}

    /* Quick Prompt Cards */
    .prompt-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
    }}

    .prompt-card:hover {{
        border-color: var(--accent);
        background: var(--bg-secondary);
        transform: translateY(-2px);
    }}

    /* Scrollbars */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--bg-primary);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--border-color);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--accent);
    }}
    </style>
    """


def apply_theme(theme_key: str = "midnight"):
    """Inject active theme CSS into Streamlit document."""
    st.markdown(get_theme_css(theme_key), unsafe_allow_html=True)
