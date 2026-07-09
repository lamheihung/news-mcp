"""Tests for the pcwatch scraper browser helpers."""

from datetime import date, datetime

import pytest

from scrapers.pcwatch.browser import (
    SearchResult,
    _parse_buddhist_date,
    _parse_publish_date,
    is_headed,
)


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
