import os
import time
from typing import Optional, Any, Iterator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessageChunk
from src.config import SUPPORTED_PROVIDERS


class DemoChatModel:
    """Simulated streaming chat model for testing and demonstration without API keys."""

    def __init__(self, model_name: str = "interactive-demo-agent"):
        self.model_name = model_name

    def stream(self, messages: list[BaseMessage], **kwargs) -> Iterator[AIMessageChunk]:
        """Yield realistic simulated token streaming response."""
        last_message = messages[-1].content if messages else "Hello"
        
        # Check if RAG context was injected
        has_rag = any("RELEVANT DOCUMENT CONTEXT" in str(m.content) for m in messages)
        
        response_intro = (
            f"👋 **[Demo Mode Active]**\n\n"
            f"I have received your prompt: *\"{last_message[:100]}...\"*\n\n"
        )
        
        if has_rag:
            response_body = (
                "### 📑 Knowledge Base Analysis (RAG Augmented)\n"
                "I analyzed your indexed documents and correlated them with your query. "
                "Here are the key takeaways:\n\n"
                "- **Primary Finding**: The contextual excerpts address the specific scope of your question.\n"
                "- **Confidence Level**: High matching relevance score based on semantic vector distance.\n"
                "- **Citation Reference**: Check the expandable source cards below for specific document pages.\n\n"
            )
        else:
            response_body = (
                "### 💡 Architectural Overview & Capabilities\n"
                "OmniStream AI is operating in full streaming mode with the following components active:\n\n"
                "1. **Streamlit Dynamic Chat**: Low-latency reactive token streaming with `st.chat_message`.\n"
                "2. **State & Conversation Memory**: Session synchronization with multi-turn sliding window.\n"
                "3. **Online Database Layer**: Live SQLAlchemy persistence supporting local SQLite or cloud PostgreSQL/Supabase.\n"
                "4. **Changeable UI Themes**: Instant theme transitions via custom CSS tokens.\n\n"
                "```python\n"
                "# Example: Streaming generator pattern in LangChain\n"
                "for chunk in model.stream(messages):\n"
                "    yield chunk.content\n"
                "```\n\n"
            )

        full_text = (
            response_intro
            + response_body
            + "👉 *To connect to a live model (Gemini, OpenAI, Groq), provide an API key in the sidebar.*"
        )

        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            time.sleep(0.02)  # Simulate streaming latency
            yield AIMessageChunk(content=chunk)


def is_provider_configured(provider: str, api_key: Optional[str] = None) -> bool:
    """Check if an API key is available for the given provider."""
    if provider in ["demo", "ollama"]:
        return True
    if api_key and api_key.strip():
        return True
    env_var = SUPPORTED_PROVIDERS.get(provider, {}).get("api_key_env")
    if env_var and os.getenv(env_var, "").strip():
        return True
    return False


def get_chat_model(
    provider: str,
    model_name: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: Optional[str] = None,
) -> Any:
    """
    Factory creating a LangChain chat model or Demo simulator.
    """
    # Demo Mode
    if provider == "demo":
        return DemoChatModel(model_name=model_name)

    # Google Gemini
    if provider == "google":
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Google API Key is required. Enter it in the sidebar or set GOOGLE_API_KEY in .env.")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=key,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    # OpenAI
    elif provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API Key is required. Enter it in the sidebar or set OPENAI_API_KEY in .env.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Groq
    elif provider == "groq":
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("Groq API Key is required. Enter it in the sidebar or set GROQ_API_KEY in .env.")
        from langchain_groq import ChatGroq

        return ChatGroq(
            model_name=model_name,
            groq_api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Ollama
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=model_name,
            temperature=temperature,
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")
