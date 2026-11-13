import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import (
    create_engine,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    desc,
    select,
    func,
    text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from src.config import DEFAULT_SQLITE_URL


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user")  # 'admin' or 'user'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), index=True, default="guest")
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    provider: Mapped[str] = mapped_column(String(64), default="google")
    model: Mapped[str] = mapped_column(String(128), default="gemini-2.5-flash")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), index=True, default="guest")
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON serialized citations
    thought_process: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # CoT / Agent reasoning
    feedback: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # like, dislike
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def normalize_db_url(url: Optional[str]) -> str:
    """Normalize database URL for SQLAlchemy compatibility."""
    if not url or url.strip() == "":
        return DEFAULT_SQLITE_URL
    
    clean_url = url.strip()
    if clean_url.startswith("postgres://"):
        clean_url = clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+"):
        clean_url = clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
    return clean_url


class DatabaseManager:
    """Database manager supporting local SQLite, online PostgreSQL, RBAC, and Admin Audit."""

    def __init__(self, db_url: Optional[str] = None):
        self.raw_url = db_url or os.getenv("DATABASE_URL")
        self.db_url = normalize_db_url(self.raw_url)
        self.is_sqlite = self.db_url.startswith("sqlite")
        
        engine_kwargs: Dict[str, Any] = {"echo": False}
        if self.is_sqlite:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
            
        self.engine = create_engine(self.db_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()

    def init_db(self):
        """Create tables if they do not exist, and safely migrate new columns."""
        try:
            Base.metadata.create_all(bind=self.engine)
            if self.is_sqlite:
                with self.engine.connect() as conn:
                    # Chat Messages columns check
                    res_msg = conn.execute(text("PRAGMA table_info(chat_messages)")).fetchall()
                    msg_cols = [r[1] for r in res_msg]
                    if "thought_process" not in msg_cols:
                        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN thought_process TEXT"))
                    if "feedback" not in msg_cols:
                        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN feedback VARCHAR(16)"))
                    if "username" not in msg_cols:
                        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN username VARCHAR(64) DEFAULT 'guest'"))
                    
                    # Chat Sessions columns check
                    res_sess = conn.execute(text("PRAGMA table_info(chat_sessions)")).fetchall()
                    sess_cols = [r[1] for r in res_sess]
                    if "username" not in sess_cols:
                        conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN username VARCHAR(64) DEFAULT 'guest'"))
                    conn.commit()
        except Exception as e:
            if not self.is_sqlite:
                print(f"[Warning] Failed to connect to remote DB ({e}). Falling back to local SQLite.")
                self.db_url = DEFAULT_SQLITE_URL
                self.is_sqlite = True
                self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                Base.metadata.create_all(bind=self.engine)

    def test_connection(self) -> Tuple[bool, str]:
        """Test the active database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            if self.is_sqlite:
                return True, "🟢 Local SQLite active (./data/chat_history.db)"
            else:
                masked_url = self.db_url.split("@")[-1] if "@" in self.db_url else "Remote Host"
                return True, f"🟢 Connected to Online Cloud Database ({masked_url})"
        except Exception as e:
            return False, f"🔴 Database Connection Failed: {str(e)}"

    # ==================== User Management & RBAC ====================

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by username."""
        with self.SessionLocal() as db:
            stmt = select(User).where(User.username == username)
            u = db.scalar(stmt)
            if not u:
                return None
            return {
                "id": u.id,
                "username": u.username,
                "password_hash": u.password_hash,
                "salt": u.salt,
                "role": u.role,
                "created_at": u.created_at,
            }

    def create_user(self, username: str, password_hash: str, salt: str, role: str = "user") -> int:
        """Register a new user."""
        with self.SessionLocal() as db:
            u = User(username=username, password_hash=password_hash, salt=salt, role=role)
            db.add(u)
            db.commit()
            db.refresh(u)
            return u.id

    def list_users(self) -> List[Dict[str, Any]]:
        """List all registered users."""
        with self.SessionLocal() as db:
            stmt = select(User).order_by(User.created_at)
            users = db.scalars(stmt).all()
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "created_at": u.created_at,
                }
                for u in users
            ]

    # ==================== Session Management ====================

    def create_session(
        self,
        title: str = "New Chat",
        provider: str = "google",
        model: str = "gemini-2.5-flash",
        username: str = "guest",
    ) -> str:
        """Create a new chat session linked to a user."""
        session_id = str(uuid.uuid4())
        with self.SessionLocal() as db:
            session_obj = ChatSession(
                session_id=session_id,
                username=username,
                title=title,
                provider=provider,
                model=model,
            )
            db.add(session_obj)
            db.commit()
        return session_id

    def list_sessions(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """List chat sessions. If username provided (and not admin), filter by username."""
        with self.SessionLocal() as db:
            stmt = select(ChatSession)
            if username and username != "admin":
                stmt = stmt.where(ChatSession.username == username)
            stmt = stmt.order_by(desc(ChatSession.updated_at))
            sessions = db.scalars(stmt).all()
            return [
                {
                    "session_id": s.session_id,
                    "username": s.username,
                    "title": s.title,
                    "provider": s.provider,
                    "model": s.model,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                }
                for s in sessions
            ]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a specific session."""
        with self.SessionLocal() as db:
            stmt = select(ChatSession).where(ChatSession.session_id == session_id)
            s = db.scalar(stmt)
            if not s:
                return None
            return {
                "session_id": s.session_id,
                "username": s.username,
                "title": s.title,
                "provider": s.provider,
                "model": s.model,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }

    def update_session_title(self, session_id: str, title: str):
        """Update session title."""
        with self.SessionLocal() as db:
            stmt = select(ChatSession).where(ChatSession.session_id == session_id)
            s = db.scalar(stmt)
            if s:
                s.title = title
                s.updated_at = datetime.now(timezone.utc)
                db.commit()

    def delete_session(self, session_id: str):
        """Delete session and all its messages."""
        with self.SessionLocal() as db:
            stmt_msgs = select(ChatMessage).where(ChatMessage.session_id == session_id)
            msgs = db.scalars(stmt_msgs).all()
            for m in msgs:
                db.delete(m)
            stmt_sess = select(ChatSession).where(ChatSession.session_id == session_id)
            sess = db.scalar(stmt_sess)
            if sess:
                db.delete(sess)
            db.commit()

    # ==================== Message Management ====================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        username: str = "guest",
        sources: Optional[List[Dict[str, Any]]] = None,
        thought_process: Optional[str] = None,
        feedback: Optional[str] = None,
        latency_ms: float = 0.0,
        tokens: int = 0,
    ) -> int:
        """Add a message to a session."""
        sources_json = json.dumps(sources) if sources else None
        with self.SessionLocal() as db:
            msg = ChatMessage(
                session_id=session_id,
                username=username,
                role=role,
                content=content,
                sources=sources_json,
                thought_process=thought_process,
                feedback=feedback,
                latency_ms=latency_ms,
                tokens=tokens,
            )
            db.add(msg)
            stmt = select(ChatSession).where(ChatSession.session_id == session_id)
            sess = db.scalar(stmt)
            if sess:
                sess.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(msg)
            return msg.id

    def update_message_feedback(self, message_id: int, feedback: Optional[str]):
        """Record user feedback (like/dislike) for a message."""
        with self.SessionLocal() as db:
            stmt = select(ChatMessage).where(ChatMessage.id == message_id)
            msg = db.scalar(stmt)
            if msg:
                msg.feedback = feedback
                db.commit()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a session in chronological order."""
        with self.SessionLocal() as db:
            stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
            records = db.scalars(stmt).all()
            results = []
            for r in records:
                parsed_sources = None
                if r.sources:
                    try:
                        parsed_sources = json.loads(r.sources)
                    except Exception:
                        parsed_sources = None
                results.append(
                    {
                        "id": r.id,
                        "session_id": r.session_id,
                        "username": r.username,
                        "role": r.role,
                        "content": r.content,
                        "sources": parsed_sources,
                        "thought_process": r.thought_process,
                        "feedback": r.feedback,
                        "latency_ms": r.latency_ms,
                        "tokens": r.tokens,
                        "created_at": r.created_at,
                    }
                )
            return results

    # ==================== Admin Search History & Analytics ====================

    def get_admin_search_history(
        self,
        filter_user: Optional[str] = None,
        search_keyword: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve complete history of user queries and searches across all sessions for Admin audit.
        """
        with self.SessionLocal() as db:
            stmt = select(ChatMessage).where(ChatMessage.role == "user")
            if filter_user and filter_user != "All Users":
                stmt = stmt.where(ChatMessage.username == filter_user)
            if search_keyword and search_keyword.strip():
                stmt = stmt.where(ChatMessage.content.ilike(f"%{search_keyword.strip()}%"))
            stmt = stmt.order_by(desc(ChatMessage.created_at)).limit(limit)
            user_msgs = db.scalars(stmt).all()

            results = []
            for u in user_msgs:
                # Find matching assistant message for this query
                stmt_reply = (
                    select(ChatMessage)
                    .where(
                        ChatMessage.session_id == u.session_id,
                        ChatMessage.role == "assistant",
                        ChatMessage.created_at >= u.created_at,
                    )
                    .order_by(ChatMessage.created_at)
                    .limit(1)
                )
                reply = db.scalar(stmt_reply)

                results.append({
                    "id": u.id,
                    "session_id": u.session_id,
                    "username": u.username or "guest",
                    "query": u.content,
                    "timestamp": u.created_at,
                    "reply_preview": (reply.content[:120] + "...") if reply else "No reply recorded",
                    "latency_ms": reply.latency_ms if reply else 0.0,
                    "tokens": reply.tokens if reply else 0,
                    "feedback": reply.feedback if reply else None,
                    "has_citations": bool(reply.sources) if (reply and reply.sources) else False,
                })
            return results

    def get_system_analytics(self) -> Dict[str, Any]:
        """Aggregate system KPIs for Admin dashboard."""
        with self.SessionLocal() as db:
            total_searches = db.scalar(select(func.count(ChatMessage.id)).where(ChatMessage.role == "user")) or 0
            total_users = db.scalar(select(func.count(User.id))) or 0
            total_sessions = db.scalar(select(func.count(ChatSession.id))) or 0
            avg_latency = db.scalar(
                select(func.avg(ChatMessage.latency_ms)).where(ChatMessage.role == "assistant", ChatMessage.latency_ms > 0)
            ) or 0.0
            total_likes = db.scalar(
                select(func.count(ChatMessage.id)).where(ChatMessage.feedback == "like")
            ) or 0

            return {
                "total_searches": total_searches,
                "total_users": total_users,
                "total_sessions": total_sessions,
                "avg_latency": round(float(avg_latency), 1),
                "total_likes": total_likes,
            }

    # ==================== Document Records ====================

    def add_document_record(self, filename: str, file_type: str, chunk_count: int) -> str:
        """Record an indexed document in the database."""
        doc_id = str(uuid.uuid4())
        with self.SessionLocal() as db:
            doc = DocumentRecord(
                doc_id=doc_id,
                filename=filename,
                file_type=file_type,
                chunk_count=chunk_count,
            )
            db.add(doc)
            db.commit()
        return doc_id

    def list_document_records(self) -> List[Dict[str, Any]]:
        """List all indexed documents."""
        with self.SessionLocal() as db:
            stmt = select(DocumentRecord).order_by(desc(DocumentRecord.uploaded_at))
            docs = db.scalars(stmt).all()
            return [
                {
                    "doc_id": d.doc_id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "chunk_count": d.chunk_count,
                    "uploaded_at": d.uploaded_at,
                }
                for d in docs
            ]

    def clear_documents(self):
        """Clear all document index records."""
        with self.SessionLocal() as db:
            stmt = select(DocumentRecord)
            docs = db.scalars(stmt).all()
            for d in docs:
                db.delete(d)
            db.commit()


_db_instance: Optional[DatabaseManager] = None


def get_db(db_url: Optional[str] = None) -> DatabaseManager:
    """Get or initialize singleton DatabaseManager instance."""
    global _db_instance
    if _db_instance is None or (db_url and normalize_db_url(db_url) != _db_instance.db_url):
        _db_instance = DatabaseManager(db_url)
    return _db_instance
