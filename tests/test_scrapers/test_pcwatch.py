"""Tests for the pcwatch scraper browser helpers and plugin."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import scrapers.pcwatch
from scrapers.pcwatch import PcwatchScraper
from scrapers.pcwatch.browser import (
    SearchResult,
    _parse_buddhist_date,
    _parse_publish_date,
    extract_article,
    is_headed,
    search_results,
)
from src.models import Article, Company, DateRange, Source
from src.watchlist import load_watchlist


class TestParseBuddhistDate:
    def test_parses_buddhist_era_date(self) -> None:
        assert _parse_buddhist_date("BE2569/06/22 ...") == date(2026, 6, 22)

    def test_parses_gregorian_date(self) -> None:
        assert _parse_buddhist_date("2026/06/22 ...") == date(2026, 6, 22)

    def test_returns_none_when_no_date(self) -> None:
        assert _parse_buddhist_date("No date in this snippet") is None


class TestParsePublishDate:
    def test_parses_japanese_datetime(self) -> None:
        assert _parse_publish_date("2026年6月22日 06:06") == datetime(2026, 6, 22, 6, 6)

    def test_parses_single_digit_month_day(self) -> None:
        assert _parse_publish_date("2026年1月5日 12:34") == datetime(2026, 1, 5, 12, 34)

    def test_rejects_invalid_format(self) -> None:
        with pytest.raises(ValueError):
            _parse_publish_date("not a date")


class TestIsHeaded:
    def test_default_is_headless(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PCWATCH_HEADED", raising=False)
        assert is_headed() is False

    @pytest.mark.parametrize("value", ["1", "true", "True", "yes"])
    def test_headed_when_env_set(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("PCWATCH_HEADED", value)
        assert is_headed() is True


class TestSearchResult:
    def test_dataclass_fields(self) -> None:
        result = SearchResult(
            url="https://example.com", title="Example", snippet_date=date(2026, 1, 1)
        )
        assert result.url == "https://example.com"
        assert result.title == "Example"
        assert result.snippet_date == date(2026, 1, 1)


class TestPcwatchScraper:
    @pytest.fixture
    def scraper(self) -> PcwatchScraper:
        return PcwatchScraper()

    @pytest.fixture
    def source(self) -> Source:
        return Source(
            id="pcwatch",
            name="PC Watch",
            base_url="https://pc.watch.impress.co.jp/",
            scraper_module="scrapers.pcwatch",
            description="Japanese PC/tech news site.",
        )

    @pytest.fixture
    def company(self) -> Company:
        return Company(
            bloomberg_ticker="000660 KS Equity",
            name="SK hynix",
            aliases=["SK Hynix"],
        )

    @pytest.mark.asyncio
    async def test_is_complete_returns_false_without_exhausted_marker(
        self, scraper: PcwatchScraper, source: Source, company: Company, tmp_path: Path
    ) -> None:
        monkeypatch = pytest.MonkeyPatch()
        watchlist_path = tmp_path / "watchlist.yaml"
        watchlist_path.write_text("companies: []\n", encoding="utf-8")
        monkeypatch.setattr("scrapers.pcwatch.WATCHLIST_PATH", watchlist_path)
        try:
            assert (
                await scraper.is_complete(
                    source, company, DateRange(start=date(2026, 1, 1), end=date(2026, 6, 30))
                )
                is False
            )
        finally:
            monkeypatch.undo()

    @pytest.mark.asyncio
    async def test_is_complete_returns_true_when_start_on_exhausted_marker(
        self, scraper: PcwatchScraper, source: Source, company: Company, tmp_path: Path
    ) -> None:
        monkeypatch = pytest.MonkeyPatch()
        watchlist_path = tmp_path / "watchlist.yaml"
        watchlist_path.write_text(
            "companies:\n"
            '  - bloomberg_ticker: "000660 KS Equity"\n'
            "    name: SK hynix\n"
            "    aliases: [SK Hynix]\n"
            "    search_terms: {}\n"
            "    exhausted_before:\n"
            "      pcwatch: 2026-01-01\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("scrapers.pcwatch.WATCHLIST_PATH", watchlist_path)
        try:
            assert (
                await scraper.is_complete(
                    source, company, DateRange(start=date(2026, 1, 1), end=date(2026, 6, 30))
                )
                is True
            )
        finally:
            monkeypatch.undo()

    @pytest.mark.asyncio
    async def test_is_complete_returns_false_when_start_before_exhausted_marker(
        self, scraper: PcwatchScraper, source: Source, company: Company, tmp_path: Path
    ) -> None:
        monkeypatch = pytest.MonkeyPatch()
        watchlist_path = tmp_path / "watchlist.yaml"
        watchlist_path.write_text(
            "companies:\n"
            '  - bloomberg_ticker: "000660 KS Equity"\n'
            "    name: SK hynix\n"
            "    aliases: [SK Hynix]\n"
            "    search_terms: {}\n"
            "    exhausted_before:\n"
            "      pcwatch: 2026-01-01\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("scrapers.pcwatch.WATCHLIST_PATH", watchlist_path)
        try:
            assert (
                await scraper.is_complete(
                    source, company, DateRange(start=date(2025, 6, 1), end=date(2026, 6, 30))
                )
                is False
            )
        finally:
            monkeypatch.undo()


class TestSearchResults:
    @pytest.fixture
    def page(self) -> MagicMock:
        return MagicMock()

    def _make_row(self, url: str, title: str, snippet: str) -> MagicMock:
        link_first = MagicMock()
        link_first.get_attribute = AsyncMock(return_value=url)
        link_first.text_content = AsyncMock(return_value=title)
        link_locator = MagicMock()
        link_locator.first = link_first

        snippet_first = MagicMock()
        snippet_first.text_content = AsyncMock(return_value=snippet)
        snippet_locator = MagicMock()
        snippet_locator.first = snippet_first

        row = MagicMock()
        row.locator = MagicMock(
            side_effect=lambda selector: {
                ".gs-title a": link_locator,
                ".gs-snippet": snippet_locator,
            }[selector]
        )
        return row

    @pytest.mark.asyncio
    async def test_collects_results_until_older_than_stop_before(self, page: MagicMock) -> None:
        stop_before = date(2026, 6, 1)
        row = self._make_row(
            "https://pc.watch.impress.co.jp/docs/article/1.html",
            "Article title",
            "2026/06/02 ...",
        )

        page.locator = MagicMock(
            return_value=MagicMock(
                all=AsyncMock(return_value=[row]),
                filter=MagicMock(return_value=MagicMock(all=AsyncMock(return_value=[]))),
            )
        )
        page.locator(".gsc-cursor-current-page").text_content = AsyncMock(return_value="1")
        page.wait_for_selector = AsyncMock(return_value=None)
        page.goto = AsyncMock(return_value=None)

        results = await search_results(page, "SK hynix", stop_before)

        assert len(results) == 1
        assert results[0].url == "https://pc.watch.impress.co.jp/docs/article/1.html"
        assert results[0].title == "Article title"
        page.goto.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_sales_urls(self, page: MagicMock) -> None:
        stop_before = date(2026, 6, 1)
        sales_row = self._make_row(
            "https://pc.watch.impress.co.jp/docs/news/todays_sales/1.html",
            "Sales title",
            "2026/06/02 ...",
        )

        page.locator = MagicMock(
            return_value=MagicMock(
                all=AsyncMock(return_value=[sales_row]),
                filter=MagicMock(return_value=MagicMock(all=AsyncMock(return_value=[]))),
            )
        )
        page.locator(".gsc-cursor-current-page").text_content = AsyncMock(return_value="1")
        page.wait_for_selector = AsyncMock(return_value=None)
        page.goto = AsyncMock(return_value=None)

        results = await search_results(page, "SK hynix", stop_before)

        assert results == []


class TestExtractArticle:
    @pytest.fixture
    def page(self) -> MagicMock:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_extracts_article_from_standard_markup(self, page: MagicMock) -> None:
        page.goto = AsyncMock(return_value=None)
        page.wait_for_selector = AsyncMock(return_value=None)
        page.locator = MagicMock(
            side_effect=lambda selector: {
                (
                    "article h1, article .title strong, article .article-title, h1, .title strong"
                ): MagicMock(
                    first=MagicMock(text_content=AsyncMock(return_value="Article title")),
                ),
                "head": MagicMock(
                    inner_html=AsyncMock(
                        return_value='<meta content="2026-06-22T06:06:00+09:00" />'
                    ),
                ),
            }[selector]
        )
        page.evaluate = AsyncMock(return_value="Article body content.")

        article = await extract_article(
            page,
            "https://pc.watch.impress.co.jp/docs/article/1.html",
            "000660 KS Equity",
            "pcwatch",
        )

        assert article.title == "Article title"
        assert article.content == "Article body content."
        expected_published = datetime(2026, 6, 22, 6, 6, tzinfo=timezone(timedelta(hours=9)))
        assert article.published_at == expected_published
        assert article.bloomberg_ticker == "000660 KS Equity"
        assert article.source_id == "pcwatch"


class TestPcwatchScraperFetchArticles:
    @pytest.fixture
    def scraper(self) -> PcwatchScraper:
        return PcwatchScraper()

    @pytest.fixture
    def source(self) -> Source:
        return Source(
            id="pcwatch",
            name="PC Watch",
            base_url="https://pc.watch.impress.co.jp/",
            scraper_module="scrapers.pcwatch",
            description="Japanese PC/tech news site.",
        )

    @pytest.fixture
    def company(self) -> Company:
        return Company(
            bloomberg_ticker="000660 KS Equity",
            name="SK hynix",
            aliases=["SK Hynix"],
        )

    @pytest.mark.asyncio
    async def test_uses_watchlist_search_terms(
        self,
        scraper: PcwatchScraper,
        source: Source,
        company: Company,
        tmp_path: Path,
    ) -> None:
        watchlist_path = tmp_path / "watchlist.yaml"
        watchlist_path.write_text(
            "companies:\n"
            '  - bloomberg_ticker: "000660 KS Equity"\n'
            "    name: SK hynix\n"
            "    aliases: [SK Hynix]\n"
            "    search_terms:\n"
            "      pcwatch:\n"
            "        - SK Hynix\n"
            "        - SK hynix\n"
            "    exhausted_before: {}\n",
            encoding="utf-8",
        )

        with patch.object(scrapers.pcwatch, "WATCHLIST_PATH", watchlist_path):
            search_mock = AsyncMock(return_value=[])
            extract_mock = AsyncMock()
            with patch("scrapers.pcwatch.search_results", new=search_mock) as mock_search:
                with patch("scrapers.pcwatch.extract_article", new=extract_mock):
                    with patch("scrapers.pcwatch.async_playwright") as mock_playwright:
                        browser = MagicMock()
                        context = MagicMock()
                        page = MagicMock()
                        browser.new_context = AsyncMock(return_value=context)
                        context.new_page = AsyncMock(return_value=page)
                        browser.launch = AsyncMock(return_value=browser)
                        browser.close = AsyncMock()
                        playwright_obj = MagicMock(
                            chromium=MagicMock(launch=AsyncMock(return_value=browser)),
                        )
                        mock_playwright.return_value.__aenter__ = AsyncMock(
                            return_value=playwright_obj
                        )
                        mock_playwright.return_value.__aexit__ = AsyncMock(return_value=False)

                        await scraper.fetch_articles(
                            source,
                            company,
                            DateRange(start=date(2026, 1, 1), end=date(2026, 6, 30)),
                        )

        assert mock_search.await_count == 2

    @pytest.mark.asyncio
    async def test_saves_new_articles_and_updates_exhausted_marker(
        self,
        scraper: PcwatchScraper,
        source: Source,
        company: Company,
        tmp_path: Path,
    ) -> None:
        watchlist_path = tmp_path / "watchlist.yaml"
        watchlist_path.write_text("companies: []\n", encoding="utf-8")

        now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
        result = SearchResult(
            url="https://pc.watch.impress.co.jp/docs/article/1.html",
            title="New article",
            snippet_date=date(2026, 6, 15),
        )
        article = Article(
            id="hash",
            bloomberg_ticker="000660 KS Equity",
            source_id="pcwatch",
            url=result.url,
            title="New article",
            content="Content",
            published_at=now,
            fetched_at=now,
            stored_path=tmp_path / "article.md",
        )

        with patch.object(scrapers.pcwatch, "WATCHLIST_PATH", watchlist_path):
            search_mock = AsyncMock(return_value=[result])
            extract_mock = AsyncMock(return_value=article)
            with patch("scrapers.pcwatch.search_results", new=search_mock):
                with patch("scrapers.pcwatch.extract_article", new=extract_mock) as mock_extract:
                    with patch("scrapers.pcwatch.save_article") as mock_save:
                        with patch(
                            "scrapers.pcwatch.list_cached_articles", return_value=[]
                        ) as mock_cached:
                            with patch("scrapers.pcwatch.async_playwright") as mock_playwright:
                                browser = MagicMock()
                                context = MagicMock()
                                page = MagicMock()
                                browser.new_context = AsyncMock(return_value=context)
                                context.new_page = AsyncMock(return_value=page)
                                browser.launch = AsyncMock(return_value=browser)
                                browser.close = AsyncMock()
                                playwright_obj = MagicMock(
                                    chromium=MagicMock(launch=AsyncMock(return_value=browser)),
                                )
                                mock_playwright.return_value.__aenter__ = AsyncMock(
                                    return_value=playwright_obj
                                )
                                mock_playwright.return_value.__aexit__ = AsyncMock(
                                    return_value=False
                                )

                                articles = await scraper.fetch_articles(
                                    source,
                                    company,
                                    DateRange(start=date(2026, 1, 1), end=date(2026, 6, 30)),
                                )

        assert len(articles) == 1
        assert articles[0].url == result.url
        mock_extract.assert_awaited_once()
        mock_save.assert_called_once_with(article)
        mock_cached.assert_called_once()

        watchlist = load_watchlist(watchlist_path)
        assert watchlist[0].exhausted_before["pcwatch"] == date(2026, 1, 1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_pcwatch_search_and_extract() -> None:
    pytest.importorskip("playwright")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception as exc:
            pytest.skip(f"Browser unavailable: {exc}")

        context = await browser.new_context()
        page = await context.new_page()
        try:
            results = await search_results(page, "SK hynix", date(2025, 1, 1))
            assert isinstance(results, list)
            for result in results:
                assert result.url
                assert result.title
                assert "/docs/news/todays_sales/" not in result.url
        finally:
            await browser.close()
