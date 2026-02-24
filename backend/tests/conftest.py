import sys
import os

# Add backend/ to sys.path so tests can import backend modules directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock

from vector_store import SearchResults


# ---------------------------------------------------------------------------
# Plain helper functions (importable by test files)
# ---------------------------------------------------------------------------

def make_search_results(docs=None, metas=None, error=None):
    """Build a SearchResults instance for various test scenarios.

    Args:
        docs:  list of document strings (default empty)
        metas: list of metadata dicts aligned with docs (default empty)
        error: if provided, returns an error SearchResults with no documents
    """
    if error:
        return SearchResults(documents=[], metadata=[], distances=[], error=error)
    docs = docs or []
    metas = metas or []
    return SearchResults(
        documents=docs,
        metadata=metas,
        distances=[0.5] * len(docs),
        error=None,
    )


def mock_anthropic_response(stop_reason, content_blocks):
    """Build a mock object that looks like anthropic.types.Message.

    Args:
        stop_reason:    e.g. "end_turn" or "tool_use"
        content_blocks: list of mock content block objects
    """
    mock_response = MagicMock()
    mock_response.stop_reason = stop_reason
    mock_response.content = content_blocks
    return mock_response


# ---------------------------------------------------------------------------
# Shared pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_vector_store():
    """MagicMock of VectorStore for use in search tool tests."""
    return MagicMock()


@pytest.fixture
def mock_rag_system():
    """Pre-configured MagicMock representing a RAGSystem instance.

    Suitable as a drop-in replacement for app.rag_system in API tests.
    Defaults cover the happy path; individual tests can override return values.
    """
    mock = MagicMock()
    mock.query.return_value = ("Test answer", ["Course A - Lesson 1"])
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }
    mock.session_manager = MagicMock()
    mock.session_manager.create_session.return_value = "test-session-id"
    mock.add_course_folder.return_value = (0, 0)
    return mock
