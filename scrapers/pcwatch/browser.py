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
    page.set_default_navigation_timeout(60000)
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    await page.goto(_search_url(term, 1), wait_until="domcontentloaded")

    for _ in range(100):
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

        next_pages = page.locator(".gsc-cursor-page").filter(has_text=re.compile(r"^\d+$"))
        current = await page.locator(".gsc-cursor-current-page").text_content()
        next_page = None
        for btn in await next_pages.all():
            text = await btn.text_content()
            if text and int(text) > int(current or 0):
                next_page = btn
                break
        if next_page is None:
            break
        await next_page.click()
        await page.wait_for_timeout(500)

    return results


async def _extract_content(page: Page) -> str:
    """Return article text from .main-contents or legacy .news."""
    text: str = await page.evaluate(
        """() => {
            const container =
                document.querySelector('article .main-contents') ||
                document.querySelector('article .news');
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


_ISO_DATE_RE = re.compile(r'content="(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})"')


def _parse_iso_date(value: str) -> datetime:
    """Parse an ISO-8601 datetime string."""
    return datetime.fromisoformat(value)


async def _extract_publish_date(page: Page, url: str) -> datetime:
    """Return the article publish date from meta tags or the page text fallback."""
    head = await page.locator("head").inner_html()
    match = _ISO_DATE_RE.search(head)
    if match:
        return _parse_iso_date(match.group(1))
    raise ValueError(f"Could not determine publish date for {url}")


async def _extract_title(page: Page) -> str:
    """Return the article title from the standard or legacy markup."""
    title_locator = page.locator("article h1, article .title strong").first
    title_text = (await title_locator.text_content() or "").strip()
    return title_text


async def extract_article(page: Page, url: str, bloomberg_ticker: str, source_id: str) -> Article:
    """Open a pcwatch article page and extract an Article model."""
    page.set_default_navigation_timeout(60000)
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_selector("article", timeout=10000)

    title = await _extract_title(page)
    published_at = await _extract_publish_date(page, url)
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
