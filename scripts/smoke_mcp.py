"""Real stdio round trips through the Agents SDK MCP client; no LLM or API key."""

import asyncio
import sqlite3
import tempfile
from pathlib import Path

from campus_mcp.agent import EXPECTED_TOOLS, make_mcp_client


async def main() -> None:
    print("OFFLINE MCP CHECK — real server/client, no model inference")
    with tempfile.TemporaryDirectory(prefix="campus-mcp-") as directory:
        database = Path(directory) / "reading_lists.sqlite3"
        async with make_mcp_client(database) as client:
            names = {tool.name for tool in await client.list_tools()}
            assert names == EXPECTED_TOOLS, names
            print(f"Discovered: {sorted(names)}")
            for name, arguments, error in [
                ("search_catalog", {"query": "agents", "limit": 2}, False),
                ("save_book", {"book_id": "B001", "list_name": "smoke"}, False),
                (
                    "build_reading_list",
                    {"query": "databases", "list_name": "smoke", "limit": 2},
                    False,
                ),
                ("save_book", {"book_id": "B999", "list_name": "smoke"}, True),
                ("build_reading_list", {"query": "unobtainium", "list_name": "smoke"}, True),
            ]:
                result = await client.call_tool(name, arguments)
                assert bool(result.is_error) == error, result
            with sqlite3.connect(database) as db:
                rows = db.execute("SELECT book_id FROM reading_list ORDER BY book_id").fetchall()
            assert rows == [("B001",), ("B002",), ("B007",)], rows
        print(
            "\nPASS: exactly three tools; data, action, workflow, persistence and errors verified."
        )


if __name__ == "__main__":
    asyncio.run(main())
