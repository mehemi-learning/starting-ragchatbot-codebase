"""Unit tests for AIGenerator tool-call flow.

All tests patch anthropic.Anthropic so no real API calls are made.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch

from ai_generator import AIGenerator
from conftest import mock_anthropic_response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    """Patch anthropic.Anthropic and return the mock client instance."""
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        mock_client_instance = MagicMock()
        MockAnthropic.return_value = mock_client_instance
        yield mock_client_instance


@pytest.fixture
def generator(mock_client):
    """AIGenerator wired to the mock Anthropic client."""
    return AIGenerator(api_key="test-key", model="claude-test-model")


def _text_block(text="Answer."):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _tool_block(name="search_course_content", tool_id="tool_123", **input_kwargs):
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.id = tool_id
    block.input = input_kwargs or {"query": "test query"}
    return block


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAIGeneratorGenerateResponse:

    def test_returns_direct_text_when_no_tool_use(self, generator, mock_client):
        """Returns the text content directly when stop_reason is 'end_turn'."""
        response = mock_anthropic_response("end_turn", [_text_block("Here is my answer.")])
        mock_client.messages.create.return_value = response

        result = generator.generate_response(query="What is Python?")

        assert result == "Here is my answer."

    def test_calls_handle_tool_execution_on_tool_use(self, generator, mock_client):
        """Makes a second API call when stop_reason is 'tool_use'."""
        first_response = mock_anthropic_response(
            "tool_use", [_tool_block(query="Python basics")]
        )
        second_response = mock_anthropic_response("end_turn", [_text_block("Final answer.")])
        mock_client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Search results here"

        result = generator.generate_response(
            query="What is Python?",
            tools=[{"name": "search_course_content"}],
            tool_manager=tool_manager,
        )

        assert mock_client.messages.create.call_count == 2
        assert result == "Final answer."

    def test_handle_tool_execution_calls_tool_manager(self, generator, mock_client):
        """tool_manager.execute_tool() is called with the correct tool name and input."""
        first_response = mock_anthropic_response(
            "tool_use",
            [_tool_block(tool_id="t456", query="loops", course_name="Python 101")],
        )
        second_response = mock_anthropic_response(
            "end_turn", [_text_block("Loops are used for iteration.")]
        )
        mock_client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Content about loops"

        generator.generate_response(
            query="Tell me about loops",
            tools=[{"name": "search_course_content"}],
            tool_manager=tool_manager,
        )

        tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="loops",
            course_name="Python 101",
        )

    def test_handle_tool_execution_sends_tool_results_in_messages(
        self, generator, mock_client
    ):
        """Second API call includes a {'type': 'tool_result', ...} message content block."""
        first_response = mock_anthropic_response(
            "tool_use", [_tool_block(tool_id="t789", query="variables")]
        )
        second_response = mock_anthropic_response(
            "end_turn", [_text_block("Variables store data.")]
        )
        mock_client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Variables are ..."

        generator.generate_response(
            query="What are variables?",
            tools=[{"name": "search_course_content"}],
            tool_manager=tool_manager,
        )

        second_call = mock_client.messages.create.call_args_list[1]
        messages = second_call.kwargs.get("messages", [])

        # Collect all content items across all messages
        all_content = []
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                all_content.extend(content)

        tool_result_found = any(
            isinstance(item, dict) and item.get("type") == "tool_result"
            for item in all_content
        )
        assert tool_result_found, (
            "Expected a {'type': 'tool_result', ...} block in the second API call messages"
        )

    def test_system_prompt_includes_conversation_history(self, generator, mock_client):
        """When conversation_history is provided it appears in the system param."""
        response = mock_anthropic_response("end_turn", [_text_block("Response.")])
        mock_client.messages.create.return_value = response

        generator.generate_response(
            query="Tell me more",
            conversation_history="User: What is Python?\nAssistant: Python is a language.",
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        system_param = call_kwargs.get("system", "")
        assert "User: What is Python?" in system_param

    def test_tools_added_to_api_params_when_provided(self, generator, mock_client):
        """API call includes 'tools' and 'tool_choice' keys when tools are passed."""
        response = mock_anthropic_response("end_turn", [_text_block("Answer.")])
        mock_client.messages.create.return_value = response

        tools = [{"name": "search_course_content"}]
        generator.generate_response(query="Question?", tools=tools)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "tools" in call_kwargs
        assert "tool_choice" in call_kwargs

    def test_no_tools_in_second_call(self, generator, mock_client):
        """The follow-up API call after tool execution does NOT include a 'tools' key."""
        first_response = mock_anthropic_response(
            "tool_use", [_tool_block(tool_id="tabc", query="functions")]
        )
        second_response = mock_anthropic_response(
            "end_turn", [_text_block("Functions encapsulate code.")]
        )
        mock_client.messages.create.side_effect = [first_response, second_response]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "Function content"

        generator.generate_response(
            query="What are functions?",
            tools=[{"name": "search_course_content"}],
            tool_manager=tool_manager,
        )

        second_call_kwargs = mock_client.messages.create.call_args_list[1].kwargs
        assert "tools" not in second_call_kwargs
