"""Pydantic data models for the Investment Research MCP Server.

See architecture/001-architecture-design.md and architecture/002-architecture-design.md
for the canonical definitions.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import BaseModel, model_validator


def published_at_sort_key(article: Article) -> datetime:
    """Return a timezone-aware UTC datetime for sorting articles by publish date.

    Handles articles whose `published_at` may be offset-naive or offset-aware.
    """
    dt = article.published_at
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class Company(BaseModel):
    """A company normalized to its canonical Bloomberg ticker."""

    bloomberg_ticker: str
    name: str
    aliases: list[str]


class Source(BaseModel):
    """A developer-curated news/information source."""

    id: str
    name: str
    base_url: str
    scraper_module: str
    description: str


class Article(BaseModel):
    """A scraped article saved locally and returned inline to the LLM."""

    id: str
    bloomberg_ticker: str
    source_id: str
    url: str
    title: str
    content: str
    published_at: datetime
    fetched_at: datetime
    stored_path: Path


class DateRange(BaseModel):
    """An inclusive date range used to bound article queries."""

    start: date
    end: date

    @model_validator(mode="after")
    def check_end_after_start(self) -> DateRange:
        if self.end < self.start:
            raise ValueError("end date must be on or after start date")
        return self


class WatchlistEntry(BaseModel):
    """An automatically tracked company with per-source search terms."""

    bloomberg_ticker: str
    name: str
    aliases: list[str]
    search_terms: dict[str, list[str]]
    exhausted_before: dict[str, date] = {}
