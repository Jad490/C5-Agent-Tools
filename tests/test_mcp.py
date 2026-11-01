import json
import sqlite3

import pytest
from fastmcp import Client

from campus_mcp.agent import EXPECTED_TOOLS, make_mcp_client
from campus_mcp.server import create_server
from campus_mcp.service import DEFAULT_CATALOG, LibraryService


@pytest.fixture
def server(tmp_path):
    return create_server(LibraryService(DEFAULT_CATALOG, tmp_path / "mcp.sqlite3"))


async def test_exactly_three_documented_typed_tools(server):
    async with Client(server) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == EXPECTED_TOOLS
        for tool in tools:
            assert tool.description and len(tool.description) > 80
            assert tool.input_schema["properties"]
            assert tool.output_schema
        data_tool = next(t for t in tools if t.name == "search_catalog")
        assert data_tool.annotations.read_only_hint is True
        assert await client.list_resources() == []


async def test_success_results_are_structured(server):
    async with Client(server) as client:
        search = await client.call_tool("search_catalog", {"query": "agents", "limit": 2})
        assert search.structured_content["total_matches"] == 2
        assert search.structured_content["matches"][0]["book_id"] == "B001"
        action = await client.call_tool("save_book", {"book_id": "B001", "list_name": "course"})
        assert action.structured_content["status"] == "saved"
        workflow = await client.call_tool(
            "build_reading_list",
            {
                "query": "agents",
                "list_name": "course",
                "limit": 2,
            },
        )
        assert workflow.structured_content["newly_saved"] == 1
        assert workflow.structured_content["already_saved"] == 1


@pytest.mark.parametrize(
    "name,arguments,code",
    [
        ("search_catalog", {"query": "   "}, "INVALID_QUERY"),
        ("search_catalog", {"query": "agents", "limit": 0}, "validation"),
        ("save_book", {"book_id": "B999", "list_name": "course"}, "BOOK_NOT_FOUND"),
        ("save_book", {"book_id": "B001", "list_name": "../escape"}, "validation"),
        ("build_reading_list", {"query": "unobtainium", "list_name": "course"}, "NO_MATCHES"),
    ],
)
async def test_expected_errors_are_mcp_errors(server, name, arguments, code):
    async with Client(server) as client:
        result = await client.call_tool(name, arguments, raise_on_error=False)
        assert result.is_error is True
        text = " ".join(block.text for block in result.content if block.type == "text")
        assert code.casefold() in text.casefold()


async def test_agents_sdk_stdio_client_round_trip(tmp_path):
    database = tmp_path / "stdio.sqlite3"
    async with make_mcp_client(database) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools} == EXPECTED_TOOLS
        data = await client.call_tool("search_catalog", {"query": "agents", "limit": 2})
        assert not data.is_error and not database.exists()
        assert json.loads(data.content[0].text)["total_matches"] == 2
        action = await client.call_tool("save_book", {"book_id": "B001", "list_name": "stdio"})
        assert not action.is_error
        workflow = await client.call_tool(
            "build_reading_list",
            {
                "query": "databases",
                "list_name": "stdio",
                "limit": 2,
            },
        )
        assert not workflow.is_error
        failure = await client.call_tool("save_book", {"book_id": "B999", "list_name": "stdio"})
        assert failure.is_error and "BOOK_NOT_FOUND" in failure.content[0].text
    # Read after the server has exited: the action was persisted, not only held in memory.
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM reading_list").fetchone()[0] == 3
