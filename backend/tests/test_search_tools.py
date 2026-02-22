"""Unit tests for CourseSearchTool.execute()"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock

from search_tools import CourseSearchTool
from conftest import make_search_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool(mock_store):
    """Return a fresh CourseSearchTool wired to mock_store."""
    return CourseSearchTool(mock_store)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCourseSearchToolExecute:

    def test_returns_formatted_text_on_success(self, mock_vector_store):
        """execute() returns text with [CourseTitle - Lesson N] headers when results exist."""
        results = make_search_results(
            docs=["Content A", "Content B"],
            metas=[
                {"course_title": "Python 101", "lesson_number": 1},
                {"course_title": "Python 101", "lesson_number": 2},
            ],
        )
        mock_vector_store.search.return_value = results
        tool = _make_tool(mock_vector_store)

        output = tool.execute(query="what is python")

        assert "[Python 101 - Lesson 1]" in output
        assert "[Python 101 - Lesson 2]" in output

    def test_stores_sources_after_search(self, mock_vector_store):
        """last_sources is populated with 'CourseName - Lesson N' after a successful search."""
        results = make_search_results(
            docs=["Content"],
            metas=[{"course_title": "MCP Course", "lesson_number": 3}],
        )
        mock_vector_store.search.return_value = results
        tool = _make_tool(mock_vector_store)

        tool.execute(query="what is mcp")

        assert tool.last_sources == ["MCP Course - Lesson 3"]

    def test_returns_error_string_on_store_error(self, mock_vector_store):
        """execute() returns the error message string when store returns an error."""
        results = make_search_results(error="DB down")
        mock_vector_store.search.return_value = results
        tool = _make_tool(mock_vector_store)

        output = tool.execute(query="anything")

        assert output == "DB down"

    def test_returns_no_results_message_when_empty(self, mock_vector_store):
        """execute() returns a 'No relevant content found' message for empty results."""
        mock_vector_store.search.return_value = make_search_results()
        tool = _make_tool(mock_vector_store)

        output = tool.execute(query="unknown topic")

        assert "No relevant content found" in output

    def test_no_results_message_includes_course_filter(self, mock_vector_store):
        """Empty-results message mentions the course_name filter."""
        mock_vector_store.search.return_value = make_search_results()
        tool = _make_tool(mock_vector_store)

        output = tool.execute(query="something", course_name="Python")

        assert "in course 'Python'" in output

    def test_no_results_message_includes_lesson_filter(self, mock_vector_store):
        """Empty-results message mentions the lesson_number filter."""
        mock_vector_store.search.return_value = make_search_results()
        tool = _make_tool(mock_vector_store)

        output = tool.execute(query="something", lesson_number=3)

        assert "in lesson 3" in output

    def test_passes_query_to_vector_store(self, mock_vector_store):
        """execute() passes the query string to store.search()."""
        mock_vector_store.search.return_value = make_search_results()
        tool = _make_tool(mock_vector_store)

        tool.execute(query="deep learning")

        mock_vector_store.search.assert_called_once()
        call_kwargs = mock_vector_store.search.call_args
        # Accept both positional and keyword call styles
        passed_query = (
            call_kwargs.kwargs.get("query")
            if call_kwargs.kwargs.get("query") is not None
            else call_kwargs.args[0]
        )
        assert passed_query == "deep learning"

    def test_passes_course_name_to_vector_store(self, mock_vector_store):
        """execute() passes course_name keyword to store.search()."""
        mock_vector_store.search.return_value = make_search_results()
        tool = _make_tool(mock_vector_store)

        tool.execute(query="something", course_name="MCP")

        call_kwargs = mock_vector_store.search.call_args
        assert call_kwargs.kwargs.get("course_name") == "MCP"

    def test_passes_lesson_number_to_vector_store(self, mock_vector_store):
        """execute() passes lesson_number keyword to store.search()."""
        mock_vector_store.search.return_value = make_search_results()
        tool = _make_tool(mock_vector_store)

        tool.execute(query="something", lesson_number=2)

        call_kwargs = mock_vector_store.search.call_args
        assert call_kwargs.kwargs.get("lesson_number") == 2

    def test_result_without_lesson_number_omits_lesson_in_header(self, mock_vector_store):
        """When metadata has no lesson_number key, header is [CourseTitle] only."""
        results = make_search_results(
            docs=["Content"],
            metas=[{"course_title": "Data Science"}],  # no lesson_number
        )
        mock_vector_store.search.return_value = results
        tool = _make_tool(mock_vector_store)

        output = tool.execute(query="numpy")

        assert "[Data Science]" in output
        assert "Lesson" not in output
