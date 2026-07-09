"""Tests for the pcwatch scraper browser helpers and plugin."""

from datetime import date, datetime
from pathlib import Path

import pytest

from scrapers.pcwatch import PcwatchScraper
from scrapers.pcwatch.browser import (
    SearchResult,
    _parse_buddhist_date,
    _parse_publish_date,
    is_headed,
)
from src.models import Company, DateRange, Source


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
