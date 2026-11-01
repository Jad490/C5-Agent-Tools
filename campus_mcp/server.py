"""Exactly three MCP tools. Run with: python -m campus_mcp.server"""

import logging
import os
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from campus_mcp.models import SaveResult, SearchResult, WorkflowResult
from campus_mcp.service import DEFAULT_CATALOG, DEFAULT_DB, LibraryService, ToolkitError

Query = Annotated[
    str, Field(min_length=1, max_length=120, description="All search words must match")
]
Limit = Annotated[int, Field(ge=1, le=10, description="Maximum number of books, from 1 to 10")]
ListName = Annotated[
    str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,39}$", description="Local reading-list name")
]
BookID = Annotated[str, Field(pattern=r"^B\d{3}$", description="Exact catalog ID, e.g. B001")]


def create_server(service: LibraryService | None = None) -> FastMCP:
    service = service or LibraryService(
        Path(os.getenv("CAMPUS_CATALOG_PATH", str(DEFAULT_CATALOG))),
        Path(os.getenv("CAMPUS_DB_PATH", str(DEFAULT_DB))),
    )
    mcp = FastMCP("Campus Reading Toolkit")

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def search_catalog(query: Query, limit: Limit = 5) -> SearchResult:
        """DATA: Look up books in the bundled demo campus catalog without writing anything.

        Match every whitespace-separated query word, case-insensitively, across IDs,
        titles, authors and topics. Return matches in ascending book-ID order, the
        pre-limit total, and source label. An empty match list is a valid result.
        Invalid input or an unreadable catalog returns an MCP tool error.
        """
        try:
            return service.search_catalog(query, limit)
        except ToolkitError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    def save_book(book_id: BookID, list_name: ListName) -> SaveResult:
        """ACTION: Save one known catalog book to a local SQLite reading list.

        This writes persistent state. Only use when the user asks to save a book.
        Return the book ID, title, list name and saved/already_saved status.
        Repeating the same pair never duplicates it. Unknown IDs, invalid names,
        an unavailable catalog or unavailable storage return an MCP tool error.
        """
        try:
            return service.save_book(book_id, list_name)
        except ToolkitError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    def build_reading_list(query: Query, list_name: ListName, limit: Limit = 3) -> WorkflowResult:
        """ORCHESTRATION: Build a saved reading list for a topic from the demo catalog.

        Only use when the user asks to find books AND save the results. Call the
        search_catalog implementation, then save_book for each selected book.
        Return selected books, save outcomes, counts and ordered workflow steps.
        No matches returns NO_MATCHES with no writes. Later save failures report
        completed IDs; retries are safe. Catalog ordering determines the selection.
        """
        try:
            return service.build_reading_list(query, list_name, limit)
        except ToolkitError as exc:
            raise ToolError(str(exc)) from exc

    # No additional tools or resources: lookup is deliberately a callable Data tool.
    return mcp


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[MCP SERVER] %(message)s")
    create_server().run(transport="stdio", show_banner=False)
