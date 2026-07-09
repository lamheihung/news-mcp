"""Playwright browser helpers for pcwatch."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime

from playwright.async_api import Page

from src.models import Article
from src.storage import _title_hash, article_path


@dataclass
class SearchResult:
    """A single pcwatch search result."""

    url: str
    title: str
    snippet_date: date | None


_SALES_PATH = "/docs/news/todays_sales/"


def is_headed() -> bool:
    """Return True if the PCWATCH_HEADED environment variable is set."""
    return os.environ.get("PCWATCH_HEADED", "").lower() in {"1", "true", "yes"}


def _parse_buddhist_date(value: str) -> date | None:
    """Parse a date like 'BE2569/06/22' or '2026/06/22' into a Gregorian date."""
    match = re.search(r"(\d{4})/(\d{2})/(\d{2})", value)
    if not match:
        return None
    year, month, day = (int(part) for part in match.groups())
    if year > 2500:
        year -= 543
    return date(year, month, day)


def _parse_publish_date(value: str) -> datetime:
    """Parse a Japanese datetime like '2026年6月22日 06:06'."""
    match = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{2}):(\d{2})", value)
    if not match:
        raise ValueError(f"unpublishable date format: {value!r}")
    year, month, day, hour, minute = (int(part) for part in match.groups())
    return datetime(year, month, day, hour, minute)


def _search_url(term: str, page_number: int) -> str:
    encoded = term.replace(" ", "%20")
    base = "https://pc.watch.impress.co.jp/extra/pcw/search/"
    return (
        f"{base}?q={encoded}&gsc.sort=date"
        f"#gsc.tab=0&gsc.q={encoded}&gsc.page={page_number}&gsc.sort=date"
    )


async def search_results(page: Page, term: str, stop_before: date) -> list[SearchResult]:
    """Collect pcwatch search results for a term until results are older than stop_before."""
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    for page_number in range(1, 101):
        await page.goto(_search_url(term, page_number))
        await page.wait_for_selector(".gsc-webResult", timeout=10000)

        rows = await page.locator(".gsc-webResult").all()
        if not rows:
            break

        oldest_seen: date | None = None
        for row in rows:
            link_locator = row.locator(".gs-title a").first
            url = await link_locator.get_attribute("href")
            title = (await link_locator.text_content() or "").strip()
            snippet = (await row.locator(".gs-snippet").first.text_content() or "").strip()

            if url is None or _SALES_PATH in url:
                continue

            snippet_date = _parse_buddhist_date(snippet)
            if snippet_date is not None and (oldest_seen is None or snippet_date < oldest_seen):
                oldest_seen = snippet_date

            if url not in seen_urls:
                seen_urls.add(url)
                results.append(SearchResult(url=url, title=title, snippet_date=snippet_date))

        if oldest_seen is not None and oldest_seen < stop_before:
            break

        await page.wait_for_timeout(500)

    return results


async def _extract_content(page: Page) -> str:
    """Return clean article text from .main-contents, excluding related links/ads."""
    text: str = await page.evaluate(
        """() => {
            const container = document.querySelector('article .main-contents');
            if (!container) return '';
            const clone = container.cloneNode(true);
            const selectors = [
                '.related-links',
                '.relatedLinks',
                '.ad',
                '.ads',
                'iframe',
                'script',
                'style',
            ];
            clone.querySelectorAll(selectors.join(', ')).forEach(el => el.remove());
            return clone.textContent.replace(/\\s+/g, ' ').trim();
        }"""
    )
    return text


async def extract_article(page: Page, url: str, bloomberg_ticker: str, source_id: str) -> Article:
    """Open a pcwatch article page and extract an Article model."""
    await page.goto(url)
    await page.wait_for_selector("article h1", timeout=10000)

    title = (await page.locator("article h1").text_content() or "").strip()
    date_text = (
        await page.locator("article .article-info .publish-date").text_content() or ""
    ).strip()
    published_at = _parse_publish_date(date_text)
    content = await _extract_content(page)

    article_id = _title_hash(title)
    stored_path = article_path(bloomberg_ticker, source_id, title)
    return Article(
        id=article_id,
        bloomberg_ticker=bloomberg_ticker,
        source_id=source_id,
        url=url,
        title=title,
        content=content,
        published_at=published_at,
        fetched_at=datetime.now(),
        stored_path=stored_path,
    )
