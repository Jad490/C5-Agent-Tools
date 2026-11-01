import sqlite3
from unittest.mock import Mock

import pytest

from campus_mcp.service import DEFAULT_CATALOG, LibraryService, ToolkitError


@pytest.fixture
def service(tmp_path):
    return LibraryService(DEFAULT_CATALOG, tmp_path / "lists.sqlite3")


def saved_ids(service):
    if not service.db_path.exists():
        return []
    with sqlite3.connect(service.db_path) as db:
        return db.execute("SELECT list_name, book_id FROM reading_list ORDER BY book_id").fetchall()


def test_data_search_is_read_only_and_deterministic(service):
    before = DEFAULT_CATALOG.read_bytes()
    result = service.search_catalog("  AGENTS  ", 1)
    assert result.query == "AGENTS"
    assert [b.book_id for b in result.matches] == ["B001"]
    assert result.total_matches == 2
    assert DEFAULT_CATALOG.read_bytes() == before
    assert not service.db_path.exists()


@pytest.mark.parametrize(
    "query,ids",
    [
        ("databases", ["B002", "B007"]),
        ("russell", ["B001"]),
        ("machine learning", ["B003", "B008"]),
        ("B006", ["B006"]),
        ("unobtainium", []),
    ],
)
def test_search_contract(service, query, ids):
    assert [b.book_id for b in service.search_catalog(query).matches] == ids


@pytest.mark.parametrize("query", ["", " \t ", "x" * 121])
def test_data_invalid_query(service, query):
    with pytest.raises(ToolkitError, match="INVALID_QUERY"):
        service.search_catalog(query)


@pytest.mark.parametrize("limit", [0, 11, True, 1.5])
def test_limit_bounds(service, limit):
    with pytest.raises(ToolkitError, match="INVALID_LIMIT"):
        service.search_catalog("agents", limit)


def test_action_persists_across_service_instances_and_is_idempotent(service):
    assert service.save_book("B001", "course").status == "saved"
    restarted = LibraryService(DEFAULT_CATALOG, service.db_path)
    assert restarted.save_book("B001", "course").status == "already_saved"
    assert saved_ids(service) == [("course", "B001")]
    assert restarted.save_book("B001", "other").status == "saved"


@pytest.mark.parametrize("name", ["", "Course", "../escape", "two words", "x" * 41])
def test_action_invalid_list_has_no_write(service, name):
    with pytest.raises(ToolkitError, match="INVALID_LIST_NAME"):
        service.save_book("B001", name)
    assert not service.db_path.exists()


@pytest.mark.parametrize("book_id,code", [("B999", "BOOK_NOT_FOUND"), ("1", "INVALID_BOOK_ID")])
def test_action_unknown_id_has_no_write(service, book_id, code):
    with pytest.raises(ToolkitError, match=code):
        service.save_book(book_id, "course")
    assert not service.db_path.exists()


def test_orchestration_calls_data_then_action_in_order(service, monkeypatch):
    calls = []
    search, save = service.search_catalog, service.save_book

    def lookup(query, limit):
        calls.append("data")
        return search(query, limit)

    def action(book_id, list_name):
        calls.append(book_id)
        return save(book_id, list_name)

    monkeypatch.setattr(service, "search_catalog", lookup)
    monkeypatch.setattr(service, "save_book", action)
    result = service.build_reading_list("agents", "course", 2)
    assert calls == ["data", "B001", "B003"]
    assert result.newly_saved == 2 and result.already_saved == 0
    assert len(result.steps) == 3
    assert saved_ids(service) == [("course", "B001"), ("course", "B003")]
    again = service.build_reading_list("agents", "course", 2)
    assert again.newly_saved == 0 and again.already_saved == 2


def test_workflow_no_matches_never_calls_action(service, monkeypatch):
    action = Mock()
    monkeypatch.setattr(service, "save_book", action)
    with pytest.raises(ToolkitError, match="NO_MATCHES"):
        service.build_reading_list("unobtainium", "course")
    action.assert_not_called()
    assert not service.db_path.exists()


def test_workflow_reports_partial_progress_and_retry_is_safe(service, monkeypatch):
    save = service.save_book

    def fail_second(book_id, list_name):
        if book_id == "B003":
            raise ToolkitError("STORAGE_UNAVAILABLE: simulated disk failure")
        return save(book_id, list_name)

    monkeypatch.setattr(service, "save_book", fail_second)
    with pytest.raises(ToolkitError, match=r'WORKFLOW_FAILED: completed IDs=\["B001"\]'):
        service.build_reading_list("agents", "course", 2)
    assert saved_ids(service) == [("course", "B001")]
    monkeypatch.setattr(service, "save_book", save)
    retried = service.build_reading_list("agents", "course", 2)
    assert retried.newly_saved == 1 and retried.already_saved == 1


def test_storage_error_is_clear(tmp_path):
    service = LibraryService(DEFAULT_CATALOG, tmp_path)  # directory cannot be a database file
    with pytest.raises(ToolkitError, match="STORAGE_UNAVAILABLE"):
        service.save_book("B001", "course")


@pytest.mark.parametrize("contents", [None, "not json", "{}", '[{"book_id":"B001"}]'])
def test_catalog_unavailable(tmp_path, contents):
    catalog = tmp_path / "broken.json"
    if contents is not None:
        catalog.write_text(contents)
    service = LibraryService(catalog, tmp_path / "lists.sqlite3")
    with pytest.raises(ToolkitError, match="CATALOG_UNAVAILABLE"):
        service.search_catalog("agents")
    with pytest.raises(ToolkitError, match="CATALOG_UNAVAILABLE"):
        service.save_book("B001", "course")
    assert not service.db_path.exists()
