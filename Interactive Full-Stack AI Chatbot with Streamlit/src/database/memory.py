import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from src.database.db import DatabaseManager, get_db


class ConversationMemoryManager:
    """Manages conversation memory, persistence, and LangChain message history integration."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def load_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Load conversation messages from database."""
        return self.db.get_messages(session_id)

    def persist_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        latency_ms: float = 0.0,
        tokens: int = 0,
    ) -> int:
        """Persist a single message to database."""
        return self.db.add_message(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            latency_ms=latency_ms,
            tokens=tokens,
        )

    def to_langchain_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_turns: int = 15,
    ) -> List[BaseMessage]:
        """
        Convert stored messages to LangChain BaseMessage objects with optional system prompt
        and sliding window token/turn management.
        """
        lc_messages: List[BaseMessage] = []

        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))

        # Apply sliding window to keep latest turns
        trimmed = messages[-max_turns * 2 :] if max_turns and len(messages) > max_turns * 2 else messages

        for msg in trimmed:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        return lc_messages

    def generate_session_title(self, first_user_message: str) -> str:
        """Generate a clean, truncated title based on the first user query."""
        clean = " ".join(first_user_message.strip().split())
        if len(clean) > 42:
            return clean[:39] + "..."
        return clean or "New Conversation"

    def export_as_markdown(self, session_title: str, messages: List[Dict[str, Any]]) -> str:
        """Export session conversation as clean Markdown."""
        md_lines = [
            f"# {session_title}",
            f"*Exported from OmniStream AI on {messages[0].get('created_at') if messages else 'N/A'}*",
            "\n---\n",
        ]
        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            created = msg.get("created_at")
            md_lines.append(f"### {role}")
            md_lines.append(content)
            if msg.get("sources"):
                md_lines.append("\n**Sources Cited:**")
                for s in msg["sources"]:
                    md_lines.append(f"- *{s.get('source')}* (Page {s.get('page', 1)})")
            md_lines.append("\n---\n")
        return "\n".join(md_lines)

    def export_as_json(self, session_metadata: Dict[str, Any], messages: List[Dict[str, Any]]) -> str:
        """Export session as structured JSON."""
        export_data = {
            "session": session_metadata,
            "messages": messages,
        }
        return json.dumps(export_data, default=str, indent=2)
