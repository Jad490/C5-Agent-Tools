"""Single-purpose implementations shared by MCP endpoints and the workflow."""

import json
import logging
import re
import sqlite3
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from campus_mcp.models import Book, SaveResult, SearchResult, WorkflowResult

log = logging.getLogger("campus.server")
DEFAULT_CATALOG = Path(__file__).parent / "data" / "catalog.json"
DEFAULT_DB = Path(__file__).resolve().parents[1] / "runtime" / "reading_lists.sqlite3"


class ToolkitError(ValueError):
    """An expected failure with a stable, model-readable code prefix."""


def validate_query(query: str) -> str:
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 120:
        raise ToolkitError("INVALID_QUERY: use 1–120 non-whitespace characters.")
    return query.strip()


def validate_limit(limit: int) -> int:
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ToolkitError("INVALID_LIMIT: limit must be an integer from 1 to 10.")
    return limit


def validate_list_name(list_name: str) -> str:
    if not isinstance(list_name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", list_name):
        raise ToolkitError("INVALID_LIST_NAME: use 1–40 lowercase letters, digits, _ or -.")
    return list_name


class LibraryService:
    def __init__(self, catalog_path: Path = DEFAULT_CATALOG, db_path: Path = DEFAULT_DB):
        self.catalog_path = Path(catalog_path)
        self.db_path = Path(db_path)

    def _catalog(self) -> list[Book]:
        try:
            books = TypeAdapter(list[Book]).validate_json(self.catalog_path.read_text("utf-8"))
            if len({b.book_id for b in books}) != len(books):
                raise ValueError("duplicate book IDs")
            return books
        except (OSError, ValidationError, ValueError) as exc:
            raise ToolkitError("CATALOG_UNAVAILABLE: demo catalog is missing or invalid.") from exc

    def search_catalog(self, query: str, limit: int = 5) -> SearchResult:
        """Read the catalog only; never create directories or write the database."""
        query, limit = validate_query(query), validate_limit(limit)
        tokens = query.casefold().split()
        matches = []
        for book in self._catalog():
            haystack = " ".join([book.book_id, book.title, *book.authors, *book.topics]).casefold()
            if all(token in haystack for token in tokens):
                matches.append(book)
        matches.sort(key=lambda book: book.book_id)
        log.info("DATA search_catalog query=%r matches=%d", query, len(matches))
        return SearchResult(query=query, matches=matches[:limit], total_matches=len(matches))

    def save_book(self, book_id: str, list_name: str) -> SaveResult:
        """Persist one known ID; a UNIQUE key makes retries idempotent."""
        list_name = validate_list_name(list_name)
        if not isinstance(book_id, str) or not re.fullmatch(r"B\d{3}", book_id):
            raise ToolkitError("INVALID_BOOK_ID: expected B followed by exactly three digits.")
        book = next((book for book in self._catalog() if book.book_id == book_id), None)
        if book is None:
            raise ToolkitError(f"BOOK_NOT_FOUND: {book_id} is not in the demo catalog.")
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path, timeout=5) as db:
                db.execute("""CREATE TABLE IF NOT EXISTS reading_list (
                    list_name TEXT NOT NULL, book_id TEXT NOT NULL, title TEXT NOT NULL,
                    PRIMARY KEY (list_name, book_id))""")
                cursor = db.execute(
                    "INSERT OR IGNORE INTO reading_list VALUES (?, ?, ?)",
                    (list_name, book_id, book.title),
                )
                status = "saved" if cursor.rowcount == 1 else "already_saved"
        except (OSError, sqlite3.Error) as exc:
            raise ToolkitError(
                "STORAGE_UNAVAILABLE: could not persist the reading-list entry."
            ) from exc
        log.info("ACTION save_book book_id=%s list_name=%s status=%s", book_id, list_name, status)
        return SaveResult(list_name=list_name, book_id=book_id, title=book.title, status=status)

    def build_reading_list(self, query: str, list_name: str, limit: int = 3) -> WorkflowResult:
        """Coordinate the Data implementation followed by the Action implementation."""
        list_name = validate_list_name(list_name)
        log.info("ORCHESTRATION build_reading_list start")
        found = self.search_catalog(query, limit)
        if not found.matches:
            raise ToolkitError(
                "NO_MATCHES: no matching books; nothing was saved. Try another topic."
            )
        saves: list[SaveResult] = []
        steps = [f"search_catalog: {len(found.matches)} selected of {found.total_matches} matches"]
        for book in found.matches:
            try:
                saved = self.save_book(book.book_id, list_name)
            except ToolkitError as exc:
                # A workflow spans separate single-book transactions. Never hide a partial write.
                completed = json.dumps([item.book_id for item in saves])
                raise ToolkitError(
                    f"WORKFLOW_FAILED: completed IDs={completed}; stopped at {book.book_id}; "
                    f"{exc} Retry the same request safely after fixing the cause."
                ) from exc
            saves.append(saved)
            steps.append(f"save_book: {book.book_id} -> {saved.status}")
        log.info("ORCHESTRATION build_reading_list complete saves=%d", len(saves))
        return WorkflowResult(
            query=found.query,
            list_name=list_name,
            selected=found.matches,
            saves=saves,
            newly_saved=sum(item.status == "saved" for item in saves),
            already_saved=sum(item.status == "already_saved" for item in saves),
            steps=steps,
        )
