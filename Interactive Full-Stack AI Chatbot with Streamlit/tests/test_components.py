import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db import DatabaseManager
from src.database.memory import ConversationMemoryManager
from src.rag.document_loader import DocumentChunk
from src.rag.vector_store import RAGManager
from src.llm.providers import get_chat_model
from src.llm.chains import stream_chat_response
from src.agent.tools import python_calc, web_search
from src.agent.orchestrator import run_agentic_loop
from src.auth.auth_manager import authenticate, register_user, ensure_default_accounts


class TestOmniStreamComponents(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for testing
        self.db = DatabaseManager("sqlite:///:memory:")
        self.mem = ConversationMemoryManager(self.db)
        self.rag = RAGManager()

    def test_database_crud_and_feedback(self):
        # 1. Create session
        session_id = self.db.create_session(title="Unit Test Chat", provider="demo", model="interactive-demo-agent", username="tester")
        self.assertIsNotNone(session_id)
        
        # 2. List sessions
        sessions = self.db.list_sessions(username="tester")
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "Unit Test Chat")

        # 3. Add message with thought process
        msg_id = self.db.add_message(
            session_id=session_id,
            role="assistant",
            content="Hello World",
            username="tester",
            thought_process="Thinking: User greeted.",
        )
        self.assertGreater(msg_id, 0)

        # 4. Retrieve messages and verify thought process
        messages = self.db.get_messages(session_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "Hello World")
        self.assertEqual(messages[0]["thought_process"], "Thinking: User greeted.")
        self.assertIsNone(messages[0]["feedback"])

        # 5. Update feedback
        self.db.update_message_feedback(msg_id, "like")
        messages = self.db.get_messages(session_id)
        self.assertEqual(messages[0]["feedback"], "like")

        # 6. Update session title
        self.db.update_session_title(session_id, "Updated Chat Title")
        sess_meta = self.db.get_session(session_id)
        self.assertEqual(sess_meta["title"], "Updated Chat Title")

        # 7. Delete session
        self.db.delete_session(session_id)
        self.assertEqual(len(self.db.list_sessions(username="tester")), 0)
        self.assertEqual(len(self.db.get_messages(session_id)), 0)

    def test_auth_and_admin_search_audit(self):
        # 1. Test auto-seeding of default admin and user
        ensure_default_accounts(self.db)
        admin_auth = authenticate("admin", "admin123", self.db)
        self.assertIsNotNone(admin_auth)
        self.assertEqual(admin_auth["role"], "admin")

        user_auth = authenticate("user", "user123", self.db)
        self.assertIsNotNone(user_auth)
        self.assertEqual(user_auth["role"], "user")

        # 2. Test registration
        ok, msg = register_user("newuser", "securepass", "user", self.db)
        self.assertTrue(ok)
        new_auth = authenticate("newuser", "securepass", self.db)
        self.assertIsNotNone(new_auth)

        # 3. Add searches under newuser
        sess_id = self.db.create_session("Audit Test", username="newuser")
        self.db.add_message(sess_id, "user", "What is quantum computing?", username="newuser")
        self.db.add_message(sess_id, "assistant", "Quantum computing uses qubits.", username="newuser", latency_ms=120.0, tokens=80)

        # 4. Admin search audit logs
        history = self.db.get_admin_search_history(filter_user="newuser")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["query"], "What is quantum computing?")
        self.assertEqual(history[0]["username"], "newuser")

        # 5. System analytics
        analytics = self.db.get_system_analytics()
        self.assertGreaterEqual(analytics["total_searches"], 1)
        self.assertGreaterEqual(analytics["total_users"], 3)

    def test_rag_vector_search(self):
        chunks = [
            DocumentChunk(
                chunk_id="chunk1",
                page_content="Streamlit is an open-source Python framework used to build interactive web apps for machine learning and data science.",
                source="streamlit_guide.pdf",
                page_number=1,
            ),
            DocumentChunk(
                chunk_id="chunk2",
                page_content="LangChain is a framework for developing applications powered by large language models, providing chains and memory.",
                source="langchain_guide.pdf",
                page_number=2,
            ),
            DocumentChunk(
                chunk_id="chunk3",
                page_content="PostgreSQL and SQLite are relational databases that can store chat message history and session state.",
                source="database_guide.pdf",
                page_number=1,
            ),
        ]
        self.rag.add_chunks(chunks)
        self.assertTrue(self.rag.has_documents())
        self.assertEqual(len(self.rag.get_indexed_files()), 3)

        # Search for Streamlit
        results = self.rag.search("How do I build web apps with Streamlit?", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["source"], "streamlit_guide.pdf")

    def test_demo_streaming_chain(self):
        model = get_chat_model("demo", "interactive-demo-agent")
        token_iter, sources, meta = stream_chat_response(
            model=model,
            messages=[],
            user_query="How does full stack streaming work?",
            rag_manager=None,
            system_prompt="You are a helpful assistant.",
        )
        tokens = list(token_iter)
        self.assertGreater(len(tokens), 0)
        full_text = "".join(tokens)
        self.assertIn("Demo Mode Active", full_text)
        self.assertGreater(meta.get("token_count", 0), 0)

    def test_agent_tools_and_loop(self):
        # 1. Test Python Calculator Tool
        calc_res = python_calc("25 * 4 + 50")
        self.assertEqual(calc_res, "150")
        sqrt_res = python_calc("sqrt(144)")
        self.assertEqual(sqrt_res, "12.0")

        # 2. Test Agentic Loop Orchestrator
        model = get_chat_model("demo", "interactive-demo-agent")
        token_iter, thought_trace, sources, meta = run_agentic_loop(
            model=model,
            messages=[],
            user_query="Calculate 50 * 20",
            rag_manager=None,
            agent_mode=True,
        )
        tokens = list(token_iter)
        self.assertGreater(len(tokens), 0)
        self.assertIn("Python Calculator", thought_trace)
        self.assertIn("1000", thought_trace)
        self.assertIn("Python Math Engine", meta.get("tools_used", []))

    def test_export_tools(self):
        session_id = self.db.create_session("Export Test")
        self.db.add_message(session_id, "user", "What is AI?")
        self.db.add_message(session_id, "assistant", "AI is Artificial Intelligence.")
        msgs = self.db.get_messages(session_id)
        sess = self.db.get_session(session_id)

        md = self.mem.export_as_markdown("Export Test", msgs)
        self.assertIn("# Export Test", md)
        self.assertIn("What is AI?", md)

        js = self.mem.export_as_json(sess, msgs)
        self.assertIn('"title": "Export Test"', js)


if __name__ == "__main__":
    unittest.main()
