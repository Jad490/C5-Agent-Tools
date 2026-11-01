"""Typed wire contracts. Catalog locations are illustrative, not live library holdings."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Book(Contract):
    book_id: str = Field(pattern=r"^B\d{3}$")
    title: str = Field(min_length=1)
    authors: list[str] = Field(min_length=1)
    topics: list[str] = Field(min_length=1)
    shelf: str = Field(min_length=1)


class SearchResult(Contract):
    query: str
    matches: list[Book]
    total_matches: int
    source: Literal["bundled_demo_catalog"] = "bundled_demo_catalog"


class SaveResult(Contract):
    list_name: str
    book_id: str
    title: str
    status: Literal["saved", "already_saved"]


class WorkflowResult(Contract):
    query: str
    list_name: str
    selected: list[Book]
    saves: list[SaveResult]
    newly_saved: int
    already_saved: int
    steps: list[str]
