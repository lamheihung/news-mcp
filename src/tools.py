"""MCP tool implementations.

See architecture/001-architecture-design.md and architecture/002-architecture-design.md
for the tool contract.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from fastmcp import FastMCP

from src.config import load_config
from src.models import Article, Company, DateRange, Source
from src.resolver import resolve_company as _resolve_company
from src.scraper_base import BaseScraper
from src.scraper_loader import ScraperLoadError, get_scraper_class, load_scraper
from src.storage import list_cached_articles
from src.watchlist import load_watchlist, save_watchlist, upsert_company

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.yaml")
WATCHLIST_PATH = Path("data/watchlist.yaml")

_configured_sources: list[Source] = []


def init_tools(config_path: Path = CONFIG_PATH) -> None:
    """Load configuration and prepare tool handlers.

    Args:
        config_path: Path to the YAML configuration file.
    """
    global _configured_sources
    _configured_sources = load_config(config_path)
    logger.info("Tools initialized with %d source(s)", len(_configured_sources))


def list_sources() -> list[Source]:
    """Return all configured news/information sources."""
    logger.debug("list_sources called")
    return _configured_sources


def resolve_company(identifier: str) -> Company:
    """Normalize a company identifier to its canonical Bloomberg ticker.

    Args:
        identifier: Any common company name or ticker.

    Returns:
        A validated Company model.
    """
    logger.debug("resolve_company called with identifier: %s", identifier)
    return _resolve_company(identifier)


async def research_company(
    bloomberg_ticker: str,
    question: str,
    start_date: str | None = None,
    end_date: str | None = None,
    sources: list[str] | None = None,
) -> list[Article]:
    """Research a company across configured sources.

    Args:
        bloomberg_ticker: Canonical Bloomberg ticker for the company.
        question: Analyst's research question (used for future relevance scoring).
        start_date: Optional ISO date string (YYYY-MM-DD). Defaults to 6 months ago.
        end_date: Optional ISO date string (YYYY-MM-DD). Defaults to today.
        sources: Optional source ID filter. Defaults to all configured sources.

    Returns:
        A list of Article objects merged from cache and scrapers, deduplicated
        by URL and sorted by published_at descending.
    """
    logger.debug(
        "research_company called: ticker=%s, sources=%s",
        bloomberg_ticker,
        sources,
    )
    date_range = _build_date_range(start_date, end_date)
    company = _ensure_company_in_watchlist(bloomberg_ticker)

    selected_sources = _filter_sources(sources)

    articles_by_url: dict[str, Article] = {}
    for source in selected_sources:
        source_articles = await _fetch_source_articles(source, company, date_range)
        for article in source_articles:
            articles_by_url[article.url] = article

    results = sorted(
        articles_by_url.values(),
        key=lambda article: article.published_at,
        reverse=True,
    )

    logger.info(
        "research_company returning %d article(s) for %s",
        len(results),
        bloomberg_ticker,
    )
    return results


def register_tools(mcp: FastMCP) -> None:
    """Register all tool handlers on a FastMCP app.

    Args:
        mcp: The FastMCP application instance.
    """
    mcp.add_tool(list_sources)
    mcp.add_tool(resolve_company)
    mcp.add_tool(research_company)
    logger.info("Registered MCP tools with FastMCP app")


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


def _ensure_company_in_watchlist(bloomberg_ticker: str) -> Company:
    """Return a Company model, upserting it into the automatic watchlist."""
    entries = load_watchlist(WATCHLIST_PATH)
    for entry in entries:
        if entry.bloomberg_ticker == bloomberg_ticker:
            return Company(
                bloomberg_ticker=entry.bloomberg_ticker,
                name=entry.name,
                aliases=list(entry.aliases),
            )

    company = Company(
        bloomberg_ticker=bloomberg_ticker,
        name=bloomberg_ticker,
        aliases=[],
    )
    entries = upsert_company(entries, company)
    save_watchlist(entries, WATCHLIST_PATH)
    return company


def _filter_sources(sources: list[str] | None) -> list[Source]:
    """Return configured sources filtered by the optional source ID list."""
    if sources is None:
        return list(_configured_sources)

    source_set = set(sources)
    selected = [source for source in _configured_sources if source.id in source_set]
    unknown = source_set - {source.id for source in _configured_sources}
    if unknown:
        logger.warning("Requested unknown source IDs: %s", sorted(unknown))
    return selected


async def _fetch_source_articles(
    source: Source, company: Company, date_range: DateRange
) -> list[Article]:
    """Return articles for a single source, using cache or scraper as needed."""
    scraper = _load_source_scraper(source)
    if scraper is None:
        if source.id == "example":
            return _build_mock_articles(company.bloomberg_ticker, source.id, date_range)
        logger.warning("No scraper available for source %s; skipping", source.id)
        return []

    try:
        complete = await scraper.is_complete(source, company, date_range)
    except Exception as exc:
        logger.warning("is_complete failed for %s: %s", source.id, exc)
        complete = False

    if complete:
        logger.debug("Cache covers requested range for %s", source.id)
        return list_cached_articles(company.bloomberg_ticker, source.id, date_range)

    try:
        return await scraper.fetch_articles(source, company, date_range)
    except Exception as exc:
        logger.warning("Scraper %s failed: %s; falling back to cache", source.id, exc)
        return list_cached_articles(company.bloomberg_ticker, source.id, date_range)


def _load_source_scraper(source: Source) -> BaseScraper | None:
    """Load and instantiate a source's scraper, or None if unavailable."""
    try:
        module = load_scraper(source.scraper_module)
        cls = get_scraper_class(module)
        return cls()
    except ScraperLoadError as exc:
        logger.debug("Could not load scraper for %s: %s", source.id, exc)
        return None


def _build_mock_articles(ticker: str, source_id: str, date_range: DateRange) -> list[Article]:
    """Return mock articles for the example source fallback."""
    now = datetime.now()
    candidates = [
        Article(
            id="article-001",
            bloomberg_ticker=ticker,
            source_id=source_id,
            url="https://example.com/article-001",
            title=f"Mock article 1 for {ticker}",
            content="This is mock content for foundation testing.",
            published_at=now - timedelta(days=5),
            fetched_at=now,
            stored_path=Path(f"data/{ticker}/{source_id}/article-001.md"),
        ),
        Article(
            id="article-002",
            bloomberg_ticker=ticker,
            source_id=source_id,
            url="https://example.com/article-002",
            title=f"Mock article 2 for {ticker}",
            content="Another mock article for testing source filtering.",
            published_at=now - timedelta(days=35),
            fetched_at=now,
            stored_path=Path(f"data/{ticker}/{source_id}/article-002.md"),
        ),
        Article(
            id="article-003",
            bloomberg_ticker=ticker,
            source_id=source_id,
            url="https://example.com/article-003",
            title=f"Mock article 3 for {ticker}",
            content="Older mock article outside the default six-month window.",
            published_at=now - timedelta(days=220),
            fetched_at=now,
            stored_path=Path(f"data/{ticker}/{source_id}/article-003.md"),
        ),
    ]
    return [
        article
        for article in candidates
        if date_range.start <= article.published_at.date() <= date_range.end
    ]
