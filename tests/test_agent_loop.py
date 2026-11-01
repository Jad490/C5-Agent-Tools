"""Exercise Runner -> MCP -> Runner with a test double, not live model inference."""

import json

import pytest
from agents import Agent, Model, ModelResponse, RunConfig, Runner
from agents.usage import Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

from campus_mcp.agent import EXPECTED_TOOLS, INSTRUCTIONS, make_mcp_client


class ToolCallingTestModel(Model):
    """Scripted test double; verifies the SDK's execution loop without an API key."""

    def __init__(self, name, arguments, expected_output):
        self.name = name
        self.arguments = arguments
        self.expected_output = expected_output
        self.turn = 0

    async def get_response(
        self, system_instructions, input, model_settings, tools, *args, **kwargs
    ):
        self.turn += 1
        assert {tool.name for tool in tools} == EXPECTED_TOOLS
        if self.turn == 1:
            output = [
                ResponseFunctionToolCall(
                    type="function_call",
                    call_id="test_call_1",
                    name=self.name,
                    arguments=json.dumps(self.arguments),
                )
            ]
        else:
            assert self.turn == 2
            # The real MCP reply must be returned to the model by Runner.
            replies = [item for item in input if item.get("type") == "function_call_output"]
            assert len(replies) == 1
            assert self.expected_output in str(replies[0]["output"])
            output = [
                ResponseOutputMessage(
                    id="test_message_1",
                    type="message",
                    role="assistant",
                    status="completed",
                    content=[
                        ResponseOutputText(
                            type="output_text", text="Test reply received.", annotations=[]
                        )
                    ],
                )
            ]
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError("This test model covers only non-streaming Runner.run.")
        yield  # pragma: no cover


@pytest.mark.parametrize(
    "name,arguments,expected,error",
    [
        ("search_catalog", {"query": "agents", "limit": 2}, "B003", False),
        ("save_book", {"book_id": "B001", "list_name": "loop"}, "saved", False),
        (
            "build_reading_list",
            {"query": "databases", "list_name": "loop", "limit": 2},
            "newly_saved",
            False,
        ),
        ("save_book", {"book_id": "B999", "list_name": "loop"}, "BOOK_NOT_FOUND", True),
    ],
)
async def test_sdk_executes_mcp_tool_and_returns_reply(tmp_path, name, arguments, expected, error):
    model = ToolCallingTestModel(name, arguments, expected)
    async with make_mcp_client(tmp_path / "loop.sqlite3") as server:
        agent = Agent(
            name="Test host", instructions=INSTRUCTIONS, model=model, mcp_servers=[server]
        )
        result = await Runner.run(
            agent, "Execute the scripted test request.", run_config=RunConfig(tracing_disabled=True)
        )
        assert result.final_output == "Test reply received."
        assert server.calls == [(name, error)]
        assert model.turn == 2
