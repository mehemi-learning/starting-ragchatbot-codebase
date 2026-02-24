"""Integration tests for the FastAPI endpoints (/api/query, /api/courses).

app.py is imported inside a patch context so that:
  - RAGSystem() does not attempt to initialise ChromaDB
  - StaticFiles() does not fail when the frontend directory is absent
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Patch heavy dependencies BEFORE importing app
# ---------------------------------------------------------------------------

# Pre-load these modules so their sys.modules entries exist before patching.
import rag_system as _rag_module
import fastapi.staticfiles as _fs_module


class _FakeStaticFiles:
    """Minimal ASGI stub that satisfies app.mount() without touching the filesystem."""

    def __init__(self, *args, **kwargs):
        pass

    async def __call__(self, scope, receive, send):
        pass


# Module-level RAG mock used as the default for the duration of the process.
# Individual tests replace app.rag_system via the rag_mock fixture.
_module_rag = MagicMock()
_module_rag.query.return_value = ("module-level default", [])
_module_rag.get_course_analytics.return_value = {"total_courses": 0, "course_titles": []}
_module_rag.session_manager = MagicMock()
_module_rag.session_manager.create_session.return_value = "default-session"
_module_rag.add_course_folder.return_value = (0, 0)

with patch.object(_rag_module, "RAGSystem", MagicMock(return_value=_module_rag)), \
        patch.object(_fs_module, "StaticFiles", _FakeStaticFiles):
    import app as _app_module  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures (local to this file)
# ---------------------------------------------------------------------------

@pytest.fixture
def rag_mock(mock_rag_system):
    """Swap app.rag_system with a fresh per-test mock, then restore."""
    _app_module.rag_system = mock_rag_system
    yield mock_rag_system
    _app_module.rag_system = _module_rag


@pytest.fixture
def client(rag_mock):
    """TestClient wired to the patched FastAPI app."""
    return TestClient(_app_module.app)


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------

class TestQueryEndpoint:

    def test_returns_200_for_valid_request(self, client, rag_mock):
        rag_mock.query.return_value = ("An answer.", ["Course A - Lesson 1"])
        rag_mock.session_manager.create_session.return_value = "s1"

        resp = client.post("/api/query", json={"query": "What is Python?"})

        assert resp.status_code == 200

    def test_response_contains_required_fields(self, client, rag_mock):
        rag_mock.query.return_value = ("Answer.", ["Source"])
        rag_mock.session_manager.create_session.return_value = "s2"

        data = client.post("/api/query", json={"query": "Question?"}).json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

    def test_answer_matches_rag_output(self, client, rag_mock):
        rag_mock.query.return_value = ("Loops repeat code.", ["Python 101 - Lesson 3"])
        rag_mock.session_manager.create_session.return_value = "s3"

        data = client.post("/api/query", json={"query": "What are loops?"}).json()

        assert data["answer"] == "Loops repeat code."

    def test_sources_match_rag_output(self, client, rag_mock):
        rag_mock.query.return_value = ("Answer", ["Course X - Lesson 2", "Course Y - Lesson 5"])
        rag_mock.session_manager.create_session.return_value = "s4"

        data = client.post("/api/query", json={"query": "Question?"}).json()

        assert data["sources"] == ["Course X - Lesson 2", "Course Y - Lesson 5"]

    def test_provided_session_id_is_echoed_back(self, client, rag_mock):
        rag_mock.query.return_value = ("Answer", [])

        data = client.post(
            "/api/query",
            json={"query": "Question?", "session_id": "existing-session"},
        ).json()

        assert data["session_id"] == "existing-session"

    def test_auto_creates_session_when_omitted(self, client, rag_mock):
        rag_mock.query.return_value = ("Answer", [])
        rag_mock.session_manager.create_session.return_value = "auto-sess"

        data = client.post("/api/query", json={"query": "Question?"}).json()

        assert data["session_id"] == "auto-sess"

    def test_calls_rag_with_correct_query_and_session(self, client, rag_mock):
        rag_mock.query.return_value = ("Answer", [])
        rag_mock.session_manager.create_session.return_value = "s5"

        client.post(
            "/api/query",
            json={"query": "Tell me about Python", "session_id": "s5"},
        )

        rag_mock.query.assert_called_once_with("Tell me about Python", "s5")

    def test_missing_query_field_returns_422(self, client, rag_mock):
        resp = client.post("/api/query", json={})

        assert resp.status_code == 422

    def test_rag_exception_returns_500(self, client, rag_mock):
        rag_mock.query.side_effect = RuntimeError("DB exploded")
        rag_mock.session_manager.create_session.return_value = "s-err"

        resp = client.post("/api/query", json={"query": "Fail?"})

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------

class TestCoursesEndpoint:

    def test_returns_200(self, client, rag_mock):
        rag_mock.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Python 101"],
        }

        resp = client.get("/api/courses")

        assert resp.status_code == 200

    def test_response_contains_required_fields(self, client, rag_mock):
        rag_mock.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        data = client.get("/api/courses").json()

        assert "total_courses" in data
        assert "course_titles" in data

    def test_total_courses_matches_analytics(self, client, rag_mock):
        rag_mock.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["A", "B", "C"],
        }

        data = client.get("/api/courses").json()

        assert data["total_courses"] == 3

    def test_course_titles_match_analytics(self, client, rag_mock):
        rag_mock.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Python 101", "MCP Course"],
        }

        data = client.get("/api/courses").json()

        assert data["course_titles"] == ["Python 101", "MCP Course"]

    def test_empty_catalog(self, client, rag_mock):
        rag_mock.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        data = client.get("/api/courses").json()

        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_analytics_exception_returns_500(self, client, rag_mock):
        rag_mock.get_course_analytics.side_effect = RuntimeError("Store failed")

        resp = client.get("/api/courses")

        assert resp.status_code == 500
