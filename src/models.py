"""Pydantic data models for the Investment Research MCP Server.

See architecture/001-architecture-design.md for the canonical definitions.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, model_validator


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
