"""MCP tool implementations.

See architecture/001-architecture-design.md for the tool contract.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from fastmcp import FastMCP

from src.config import load_config
from src.models import Article, Company, DateRange, Source
from src.resolver import resolve_company as _resolve_company

CONFIG_PATH = Path("config.yaml")

_configured_sources: list[Source] = []


def init_tools(config_path: Path = CONFIG_PATH) -> None:
    """Load configuration and prepare tool handlers.

    Args:
        config_path: Path to the YAML configuration file.
    """
    global _configured_sources
    _configured_sources = load_config(config_path)


def list_sources() -> list[Source]:
    """Return all configured news/information sources."""
    return _configured_sources


def resolve_company(identifier: str) -> Company:
    """Normalize a company identifier to its canonical Bloomberg ticker.

    Args:
        identifier: Any common company name or ticker.

    Returns:
        A validated Company model.
    """
    return _resolve_company(identifier)


def research_company(
    bloomberg_ticker: str,
    question: str,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
) -> list[Article]:
    """Return sample articles for a company (foundation phase mock data).

    Args:
        bloomberg_ticker: Canonical Bloomberg ticker for the company.
        question: Analyst's research question (used for future relevance scoring).
        start_date: Optional ISO date string (YYYY-MM-DD). Defaults to 6 months ago.
        end_date: Optional ISO date string (YYYY-MM-DD). Defaults to today.
        sources: Optional source ID filter. Defaults to all mock sources.

    Returns:
        A list of mock Article objects filtered by date range and source IDs.
    """
    date_range = _build_date_range(start_date, end_date)
    articles = _build_mock_articles(bloomberg_ticker)

    filtered = [
        article
        for article in articles
        if date_range.start <= article.published_at.date() <= date_range.end
    ]

    if sources is not None:
        source_set = set(sources)
        filtered = [article for article in filtered if article.source_id in source_set]

    return filtered


def register_tools(mcp: FastMCP) -> None:
    """Register all tool handlers on a FastMCP app.

    Args:
        mcp: The FastMCP application instance.
    """
    mcp.add_tool(list_sources)
    mcp.add_tool(resolve_company)
    mcp.add_tool(research_company)


def _build_date_range(start_date: str | None, end_date: str | None) -> DateRange:
    today = date.today()
    default_start = today - timedelta(days=180)
    parsed_start = _parse_date(start_date, default_start)
    parsed_end = _parse_date(end_date, today)
    return DateRange(start=parsed_start, end=parsed_end)


def _parse_date(date_str: str | None, default: date) -> date:
    if date_str is None:
        return default
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _build_mock_articles(ticker: str) -> list[Article]:
    now = datetime.now()
    return [
        Article(
            id="article-001",
            bloomberg_ticker=ticker,
            source_id="example",
            url="https://example.com/article-001",
            title=f"Mock article 1 for {ticker}",
            content="This is mock content for foundation testing.",
            published_at=now - timedelta(days=5),
            fetched_at=now,
            stored_path=Path(f"data/{ticker}/example/article-001.md"),
        ),
        Article(
            id="article-002",
            bloomberg_ticker=ticker,
            source_id="reuters",
            url="https://reuters.com/article-002",
            title=f"Mock article 2 for {ticker}",
            content="Another mock article for testing source filtering.",
            published_at=now - timedelta(days=35),
            fetched_at=now,
            stored_path=Path(f"data/{ticker}/reuters/article-002.md"),
        ),
        Article(
            id="article-003",
            bloomberg_ticker=ticker,
            source_id="example",
            url="https://example.com/article-003",
            title=f"Mock article 3 for {ticker}",
            content="Older mock article outside the default six-month window.",
            published_at=now - timedelta(days=220),
            fetched_at=now,
            stored_path=Path(f"data/{ticker}/example/article-003.md"),
        ),
    ]
