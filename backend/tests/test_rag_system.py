"""Unit tests for RAGSystem.query().

AIGenerator, VectorStore, SessionManager, ToolManager and CourseSearchTool
are all patched so no real I/O occurs.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch

from rag_system import RAGSystem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rag(request):
    """Build a RAGSystem with all external dependencies mocked.

    Yields (system, ai_mock, session_mock, tool_manager_mock).
    """
    patches = [
        patch("rag_system.DocumentProcessor"),
        patch("rag_system.VectorStore"),
        patch("rag_system.AIGenerator"),
        patch("rag_system.SessionManager"),
        patch("rag_system.ToolManager"),
        patch("rag_system.CourseSearchTool"),
    ]
    mocks = [p.start() for p in patches]

    MockDocProc, MockVS, MockAI, MockSession, MockToolManager, MockSearchTool = mocks

    cfg = MagicMock()
    cfg.ANTHROPIC_API_KEY = "test-key"
    cfg.ANTHROPIC_MODEL = "claude-test"
    cfg.CHUNK_SIZE = 800
    cfg.CHUNK_OVERLAP = 100
    cfg.CHROMA_PATH = "./test_chroma"
    cfg.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    cfg.MAX_RESULTS = 5
    cfg.MAX_HISTORY = 2

    system = RAGSystem(cfg)

    ai_instance = MockAI.return_value
    session_instance = MockSession.return_value
    tool_manager_instance = MockToolManager.return_value

    # Sensible defaults
    ai_instance.generate_response.return_value = "AI response text"
    session_instance.get_conversation_history.return_value = None
    tool_manager_instance.get_last_sources.return_value = []
    tool_manager_instance.get_tool_definitions.return_value = [
        {"name": "search_course_content"}
    ]

    yield system, ai_instance, session_instance, tool_manager_instance

    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRAGSystemQuery:

    def test_query_returns_response_and_sources(self, rag):
        """query() returns a (response_text, sources_list) tuple."""
        system, ai, session, tm = rag
        ai.generate_response.return_value = "Hello world"
        tm.get_last_sources.return_value = ["Python 101 - Lesson 1"]

        response, sources = system.query("What is Python?")

        assert response == "Hello world"
        assert sources == ["Python 101 - Lesson 1"]

    def test_query_wraps_query_in_course_materials_prompt(self, rag):
        """generate_response is called with a prompt that starts with the expected prefix."""
        system, ai, session, tm = rag

        system.query("How do loops work?")

        call_kwargs = ai.generate_response.call_args.kwargs
        prompt = call_kwargs.get("query", "")
        assert prompt.startswith("Answer this question about course materials:")
        assert "How do loops work?" in prompt

    def test_query_passes_conversation_history(self, rag):
        """generate_response is called with the conversation_history from the session."""
        system, ai, session, tm = rag
        session.get_conversation_history.return_value = (
            "User: Hi\nAssistant: Hello"
        )

        system.query("Tell me more", session_id="session_1")

        call_kwargs = ai.generate_response.call_args.kwargs
        assert call_kwargs.get("conversation_history") == "User: Hi\nAssistant: Hello"

    def test_query_calls_tool_manager_with_tools(self, rag):
        """generate_response receives both tools= and tool_manager= arguments."""
        system, ai, session, tm = rag

        system.query("What is FastAPI?")

        call_kwargs = ai.generate_response.call_args.kwargs
        assert "tools" in call_kwargs
        assert "tool_manager" in call_kwargs
        assert call_kwargs["tool_manager"] is system.tool_manager

    def test_query_resets_sources_after_retrieval(self, rag):
        """tool_manager.reset_sources() is called after sources are retrieved."""
        system, ai, session, tm = rag
        tm.get_last_sources.return_value = ["Some Course - Lesson 2"]

        system.query("A question")

        tm.reset_sources.assert_called_once()

    def test_query_updates_session_history(self, rag):
        """session_manager.add_exchange() is called with the query and response."""
        system, ai, session, tm = rag
        ai.generate_response.return_value = "Nice answer"

        system.query("What is RAG?", session_id="session_42")

        session.add_exchange.assert_called_once_with(
            "session_42", "What is RAG?", "Nice answer"
        )

    def test_query_without_session_id_still_returns(self, rag):
        """Calling query() without session_id does not crash and returns (text, [])."""
        system, ai, session, tm = rag
        ai.generate_response.return_value = "No session answer"
        tm.get_last_sources.return_value = []

        response, sources = system.query("General question")

        assert response == "No session answer"
        assert sources == []
        # add_exchange should NOT have been called (no session_id)
        session.add_exchange.assert_not_called()
