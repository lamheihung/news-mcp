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
from src.models import (
    Article,
    Company,
    CompanyStatus,
    DateRange,
    ResearchDiagnostics,
    Source,
    SourceStatus,
    WatchlistEntry,
    published_at_sort_key,
)
from src.resolver import resolve_company as _resolve_company
from src.scraper_base import BaseScraper
from src.scraper_loader import ScraperLoadError, get_scraper_class, load_scraper
from src.storage import ARTICLE_STORE_PATH, list_cached_articles
from src.watchlist import (
    clear_exhausted_before,
    get_exhausted_before,
    get_search_terms,
    load_watchlist,
    save_watchlist,
    upsert_company,
)
from src.watchlist import (
    set_search_terms as _set_search_terms,
)

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
        key=published_at_sort_key,
        reverse=True,
    )

    logger.info(
        "research_company returning %d article(s) for %s",
        len(results),
        bloomberg_ticker,
    )
    return results


async def get_company_status(bloomberg_tickers: list[str]) -> list[CompanyStatus]:
    """Return watchlist metadata and per-source cache status for each ticker.

    Args:
        bloomberg_tickers: List of canonical Bloomberg tickers to look up.

    Returns:
        A list of ``CompanyStatus`` objects, one per requested ticker.

    Raises:
        ValueError: If a requested ticker is not in the watchlist.
    """
    logger.info("get_company_status called for tickers: %s", bloomberg_tickers)
    entries = load_watchlist(WATCHLIST_PATH)
    results: list[CompanyStatus] = []

    for ticker in bloomberg_tickers:
        entry = _find_watchlist_entry(entries, ticker)
        if entry is None:
            raise ValueError(f"company {ticker} not found in watchlist")
        results.append(_build_company_status(entry))

    return results


async def set_search_terms(
    bloomberg_ticker: str,
    source_id: str,
    terms: list[str],
) -> CompanyStatus:
    """Update source-specific search terms for a company and clear exhaustion.

    Args:
        bloomberg_ticker: Canonical Bloomberg ticker for the company.
        source_id: Source identifier whose terms will be replaced.
        terms: New search terms for the source.

    Returns:
        The updated ``CompanyStatus`` for the company.

    Raises:
        ValueError: If the company is not in the watchlist or the source is unknown.
    """
    logger.info(
        "set_search_terms called: ticker=%s, source=%s, terms=%s",
        bloomberg_ticker,
        source_id,
        terms,
    )
    _validate_source_id(source_id)

    entries = load_watchlist(WATCHLIST_PATH)
    entries = _set_search_terms(entries, bloomberg_ticker, source_id, terms)
    save_watchlist(entries, WATCHLIST_PATH)

    entry = _find_watchlist_entry(entries, bloomberg_ticker)
    assert entry is not None
    return _build_company_status(entry)


async def reset_source_cache(
    bloomberg_ticker: str,
    source_id: str,
    delete_cached_articles: bool = False,
) -> CompanyStatus:
    """Clear the exhaustion marker for a company/source and optionally delete cache.

    Args:
        bloomberg_ticker: Canonical Bloomberg ticker for the company.
        source_id: Source identifier to reset.
        delete_cached_articles: If True, remove cached ``.md`` files for the source.

    Returns:
        The updated ``CompanyStatus`` for the company.

    Raises:
        ValueError: If the company is not in the watchlist or the source is unknown.
    """
    logger.info(
        "reset_source_cache called: ticker=%s, source=%s, delete=%s",
        bloomberg_ticker,
        source_id,
        delete_cached_articles,
    )
    _validate_source_id(source_id)

    entries = load_watchlist(WATCHLIST_PATH)
    entries = clear_exhausted_before(entries, bloomberg_ticker, source_id)

    if delete_cached_articles:
        _delete_cached_articles(bloomberg_ticker, source_id)
        logger.info(
            "Deleted cached articles for %s/%s",
            bloomberg_ticker,
            source_id,
        )

    save_watchlist(entries, WATCHLIST_PATH)

    entry = _find_watchlist_entry(entries, bloomberg_ticker)
    assert entry is not None
    return _build_company_status(entry)


async def get_research_diagnostics(
    bloomberg_ticker: str,
    source_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[ResearchDiagnostics]:
    """Report what ``research_company`` would do without scraping.

    Args:
        bloomberg_ticker: Canonical Bloomberg ticker for the company.
        source_id: Optional source ID filter. If omitted, all sources are diagnosed.
        start_date: Optional ISO date string (YYYY-MM-DD). Defaults to 6 months ago.
        end_date: Optional ISO date string (YYYY-MM-DD). Defaults to today.

    Returns:
        A list of ``ResearchDiagnostics`` objects, one per source.
    """
    logger.info(
        "get_research_diagnostics called: ticker=%s, source=%s",
        bloomberg_ticker,
        source_id,
    )
    entries = load_watchlist(WATCHLIST_PATH)
    entry = _find_watchlist_entry(entries, bloomberg_ticker)
    if entry is None:
        raise ValueError(f"company {bloomberg_ticker} not found in watchlist")

    date_range = _build_date_range(start_date, end_date)
    company = Company(
        bloomberg_ticker=entry.bloomberg_ticker,
        name=entry.name,
        aliases=list(entry.aliases),
    )

    sources = _filter_sources([source_id] if source_id else None)
    diagnostics: list[ResearchDiagnostics] = []

    for source in sources:
        planned_action, is_complete, reason = await _determine_planned_action(
            entries, source, company, date_range
        )
        diagnostics.append(
            ResearchDiagnostics(
                bloomberg_ticker=bloomberg_ticker,
                source_id=source.id,
                date_range=date_range,
                search_terms=list(get_search_terms(entries, bloomberg_ticker, source.id)),
                exhausted_before=get_exhausted_before(entries, bloomberg_ticker, source.id),
                is_complete=is_complete,
                cached_article_count=_count_cached_articles(bloomberg_ticker, source.id),
                planned_action=planned_action,
                reason=reason,
            )
        )

    return diagnostics


def register_tools(mcp: FastMCP) -> None:
    """Register all tool handlers on a FastMCP app.

    Args:
        mcp: The FastMCP application instance.
    """
    mcp.add_tool(list_sources)
    mcp.add_tool(resolve_company)
    mcp.add_tool(research_company)
    mcp.add_tool(get_company_status)
    mcp.add_tool(set_search_terms)
    mcp.add_tool(reset_source_cache)
    mcp.add_tool(get_research_diagnostics)
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


def _find_watchlist_entry(entries: list[WatchlistEntry], ticker: str) -> WatchlistEntry | None:
    for entry in entries:
        if entry.bloomberg_ticker == ticker:
            return entry
    return None


def _validate_source_id(source_id: str) -> None:
    if source_id not in {source.id for source in _configured_sources}:
        raise ValueError(f"unknown source_id: {source_id}")


def _count_cached_articles(ticker: str, source_id: str) -> int:
    directory = ARTICLE_STORE_PATH / ticker / source_id
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.md")))


def _delete_cached_articles(ticker: str, source_id: str) -> None:
    directory = ARTICLE_STORE_PATH / ticker / source_id
    if not directory.exists():
        return
    for path in directory.glob("*.md"):
        path.unlink()


def _build_company_status(entry: WatchlistEntry) -> CompanyStatus:
    sources: dict[str, SourceStatus] = {}
    for source in _configured_sources:
        sources[source.id] = SourceStatus(
            source_id=source.id,
            search_terms=list(get_search_terms([entry], entry.bloomberg_ticker, source.id)),
            exhausted_before=get_exhausted_before([entry], entry.bloomberg_ticker, source.id),
            cached_article_count=_count_cached_articles(entry.bloomberg_ticker, source.id),
        )
    return CompanyStatus(
        bloomberg_ticker=entry.bloomberg_ticker,
        name=entry.name,
        aliases=list(entry.aliases),
        sources=sources,
    )


async def _determine_planned_action(
    entries: list[WatchlistEntry],
    source: Source,
    company: Company,
    date_range: DateRange,
) -> tuple[str, bool, str]:
    if source.id == "example":
        return "mock", False, "source is example"

    scraper = _load_source_scraper(source)
    if scraper is None:
        return "skip_no_scraper", False, f"no loadable scraper for {source.id}"

    try:
        is_complete = await scraper.is_complete(source, company, date_range)
    except Exception as exc:
        return "scrape", False, f"is_complete failed: {exc}"

    if is_complete:
        exhausted = get_exhausted_before(entries, company.bloomberg_ticker, source.id)
        return (
            "return_cached",
            True,
            f"date_range.start ({date_range.start}) >= exhausted_before ({exhausted})",
        )

    return "scrape", False, "cache does not cover requested range"
