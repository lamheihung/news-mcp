"""pcwatch scraper plugin."""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.async_api import async_playwright

from scrapers.pcwatch.browser import extract_article, is_headed, search_results
from src import embeddings
from src.models import Article, Company, DateRange, Source, WatchlistEntry
from src.scraper_base import BaseScraper
from src.storage import list_cached_articles, save_article
from src.watchlist import (
    get_exhausted_before,
    get_search_terms,
    load_watchlist,
    save_watchlist,
    set_exhausted_before,
    upsert_company,
)

WATCHLIST_PATH = Path("data/watchlist.yaml")

logger = logging.getLogger(__name__)


def _find_entry(watchlist: list[WatchlistEntry], ticker: str) -> WatchlistEntry | None:
    for entry in watchlist:
        if entry.bloomberg_ticker == ticker:
            return entry
    return None


class PcwatchScraper(BaseScraper):
    """Source-specific scraper for pc.watch.impress.co.jp."""

    async def fetch_articles(
        self, source: Source, company: Company, date_range: DateRange
    ) -> list[Article]:
        """Search pcwatch for the company and return articles within date_range."""
        watchlist = load_watchlist(WATCHLIST_PATH)
        terms = get_search_terms(watchlist, company.bloomberg_ticker, source.id)
        if not terms:
            terms = [company.name]

        cached_articles = list_cached_articles(company.bloomberg_ticker, source.id, date_range)
        cached_urls = {article.url for article in cached_articles}

        new_articles: list[Article] = []
        seen_urls: set[str] = set(cached_urls)

        # Ensure a watchlist entry exists before updating the exhaustion marker.
        if _find_entry(watchlist, company.bloomberg_ticker) is None:
            watchlist = upsert_company(
                watchlist,
                Company(
                    bloomberg_ticker=company.bloomberg_ticker,
                    name=company.name,
                    aliases=list(company.aliases),
                ),
            )

        logger.info(
            "pcwatch search terms for %s: %s",
            company.bloomberg_ticker,
            terms,
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=not is_headed())
            context = await browser.new_context()
            page = await context.new_page()

            try:
                for term in terms:
                    results = await search_results(page, term, date_range.start)
                    for result in results:
                        if result.url in seen_urls:
                            continue
                        seen_urls.add(result.url)

                        try:
                            article = await extract_article(
                                page,
                                result.url,
                                company.bloomberg_ticker,
                                source.id,
                            )
                        except Exception as exc:
                            logger.warning(
                                "Failed to extract article %s: %s", result.url, exc
                            )
                            continue

                        if date_range.start <= article.published_at.date() <= date_range.end:
                            if embeddings.is_available():
                                try:
                                    article.embedding = embeddings.embed(
                                        f"{article.title}\n\n{article.content}"
                                    )
                                except Exception as exc:
                                    logger.warning(
                                        "Failed to embed article %s: %s", article.url, exc
                                    )
                            save_article(article)
                            new_articles.append(article)
            finally:
                await browser.close()

        if new_articles:
            logger.info(
                "Saved %d new pcwatch articles for %s; marking exhausted_before=%s",
                len(new_articles),
                company.bloomberg_ticker,
                date_range.start,
            )
            watchlist = set_exhausted_before(
                watchlist,
                company.bloomberg_ticker,
                source.id,
                date_range.start,
            )
        else:
            logger.info(
                "No new pcwatch articles saved for %s; skipping exhaustion marker",
                company.bloomberg_ticker,
            )
        save_watchlist(watchlist, WATCHLIST_PATH)

        articles_by_url = {article.url: article for article in cached_articles}
        for article in new_articles:
            articles_by_url[article.url] = article

        return sorted(
            articles_by_url.values(),
            key=lambda article: article.published_at,
            reverse=True,
        )

    async def is_complete(self, source: Source, company: Company, date_range: DateRange) -> bool:
        """Return True when cached articles cover the requested date_range."""
        watchlist = load_watchlist(WATCHLIST_PATH)
        exhausted = get_exhausted_before(watchlist, company.bloomberg_ticker, source.id)
        if exhausted is None:
            return False
        return date_range.start >= exhausted
