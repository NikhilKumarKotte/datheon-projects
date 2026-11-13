import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Application metadata
APP_TITLE = os.getenv("APP_NAME", "OmniStream AI")
APP_TAGLINE = os.getenv("APP_DESCRIPTION", "Interactive Full-Stack AI Chatbot with Streaming & Conversation Memory")

# Theme Configurations
THEMES = {
    "midnight": {
        "name": "Midnight Slate (Dark)",
        "icon": "🌌",
        "bg_primary": "#0f172a",
        "bg_secondary": "#1e293b",
        "bg_card": "#1e293b",
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "accent": "#6366f1",
        "accent_hover": "#4f46e5",
        "user_msg_bg": "#312e81",
        "assistant_msg_bg": "#1e293b",
        "border": "#334155",
        "code_bg": "#0b0f19",
    },
    "nordic": {
        "name": "Nordic Frost (Light)",
        "icon": "❄️",
        "bg_primary": "#f8fafc",
        "bg_secondary": "#ffffff",
        "bg_card": "#ffffff",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "user_msg_bg": "#e0e7ff",
        "assistant_msg_bg": "#f1f5f9",
        "border": "#e2e8f0",
        "code_bg": "#f1f5f9",
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon (Dark)",
        "icon": "⚡",
        "bg_primary": "#0d0221",
        "bg_secondary": "#19053b",
        "bg_card": "#1d0845",
        "text_primary": "#00f0ff",
        "text_secondary": "#ff007f",
        "accent": "#ff007f",
        "accent_hover": "#d6006b",
        "user_msg_bg": "#2b0a4e",
        "assistant_msg_bg": "#16072b",
        "border": "#00f0ff44",
        "code_bg": "#080114",
    },
    "emerald": {
        "name": "Emerald Obsidian (Dark)",
        "icon": "🌲",
        "bg_primary": "#06140f",
        "bg_secondary": "#0c241b",
        "bg_card": "#0f2c21",
        "text_primary": "#ecfdf5",
        "text_secondary": "#6ee7b7",
        "accent": "#10b981",
        "accent_hover": "#059669",
        "user_msg_bg": "#064e3b",
        "assistant_msg_bg": "#0a261c",
        "border": "#047857",
        "code_bg": "#030a08",
    },
    "sunset": {
        "name": "Sunset Amber (Warm Dark)",
        "icon": "🌅",
        "bg_primary": "#1c1018",
        "bg_secondary": "#2c1722",
        "bg_card": "#381c2c",
        "text_primary": "#fff1f2",
        "text_secondary": "#fbcfe8",
        "accent": "#f43f5e",
        "accent_hover": "#e11d48",
        "user_msg_bg": "#4c1d34",
        "assistant_msg_bg": "#2a1523",
        "border": "#881337",
        "code_bg": "#12080f",
    },
}

# LLM Providers and Model Options
SUPPORTED_PROVIDERS = {
    "google": {
        "name": "Google Gemini",
        "icon": "✨",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"],
        "api_key_env": "GOOGLE_API_KEY",
        "default_model": "gemini-2.5-flash",
    },
    "openai": {
        "name": "OpenAI",
        "icon": "🧠",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "groq": {
        "name": "Groq (Ultra-Fast)",
        "icon": "⚡",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "icon": "🦙",
        "models": ["llama3.2", "mistral", "deepseek-r1", "phi3"],
        "api_key_env": None,
        "default_model": "llama3.2",
    },
    "demo": {
        "name": "Interactive Demo Mode (No Key Needed)",
        "icon": "🧪",
        "models": ["interactive-demo-agent"],
        "api_key_env": None,
        "default_model": "interactive-demo-agent",
    },
}

# Persona System Prompts
SYSTEM_PERSONAS = {
    "General Assistant": (
        "You are OmniStream AI, a production-grade, helpful, accurate, and articulate AI assistant. "
        "You provide well-structured, concise, and insightful answers with markdown formatting."
    ),
    "Senior Software Engineer": (
        "You are an expert Senior Principal Software Engineer. Provide optimal, modern, clean, and bug-free code "
        "following SOLID design patterns. Include brief explanations, time/space complexity analysis, and edge cases."
    ),
    "Academic Researcher": (
        "You are a rigorous Academic Researcher and Scientist. Provide deep, evidence-based reasoning, "
        "structured literature-style breakdowns, and cite relevant methodology wherever applicable."
    ),
    "Executive Business Strategist": (
        "You are an Executive Business Advisor and Strategist. Provide crisp, high-impact bulleted analyses, "
        "actionable recommendations, ROI considerations, and executive summaries."
    ),
    "Creative & Storytelling Copilot": (
        "You are a versatile Creative Writer and Narrative Designer. Craft compelling, imaginative, "
        "and engaging content tailored to the audience's tone and requirements."
    ),
}

# Default Database Settings
DEFAULT_SQLITE_URL = f"sqlite:///{DATA_DIR / 'chat_history.db'}"
