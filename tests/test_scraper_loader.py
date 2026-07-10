"""Tests for the scraper loader and base class."""

from __future__ import annotations

import types
from datetime import date

import pytest

from src.models import Article, Company, DateRange, Source
from src.scraper_base import BaseScraper
from src.scraper_loader import (
    ScraperLoadError,
    get_scraper_class,
    load_scraper,
)


class TestLoadScraper:
    def test_load_existing_module_returns_module(self) -> None:
        module = load_scraper("scrapers.pcwatch")
        assert isinstance(module, types.ModuleType)
        assert module.__name__ == "scrapers.pcwatch"

    def test_load_missing_module_raises_scraper_load_error(self) -> None:
        with pytest.raises(ScraperLoadError, match="scraper module not found"):
            load_scraper("scrapers.does_not_exist")


class TestGetScraperClass:
    def test_get_scraper_class_by_convention(self) -> None:
        module = load_scraper("scrapers.pcwatch")
        cls = get_scraper_class(module)
        assert cls.__name__ == "PcwatchScraper"
        assert issubclass(cls, BaseScraper)

    def test_get_scraper_class_with_explicit_name(self) -> None:
        module = load_scraper("scrapers.pcwatch")
        cls = get_scraper_class(module, "PcwatchScraper")
        assert cls.__name__ == "PcwatchScraper"

    def test_get_missing_scraper_class_raises_error(self) -> None:
        module = load_scraper("scrapers.pcwatch")
        with pytest.raises(ScraperLoadError, match="scraper class not found"):
            get_scraper_class(module, "MissingScraper")

    def test_get_non_class_attribute_raises_error(self) -> None:
        module = types.ModuleType("fake_module")
        module.SomeScraper = "not a class"  # type: ignore[attr-defined]
        with pytest.raises(ScraperLoadError, match="is not a BaseScraper subclass"):
            get_scraper_class(module, "SomeScraper")

    def test_get_non_subclass_class_raises_error(self) -> None:
        module = types.ModuleType("fake_module")

        class NotAScraper:
            pass

        module.NotAScraper = NotAScraper  # type: ignore[attr-defined]
        with pytest.raises(ScraperLoadError, match="is not a BaseScraper subclass"):
            get_scraper_class(module, "NotAScraper")


class TestBaseScraper:
    def test_base_scraper_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            BaseScraper()  # type: ignore[abstract]

    def test_subclass_missing_fetch_articles_cannot_be_instantiated(self) -> None:
        class IncompleteScraper(BaseScraper):
            async def is_complete(
                self, source: Source, company: Company, date_range: DateRange
            ) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteScraper()  # type: ignore[abstract]

    def test_subclass_missing_is_complete_cannot_be_instantiated(self) -> None:
        class IncompleteScraper(BaseScraper):
            async def fetch_articles(
                self, source: Source, company: Company, date_range: DateRange
            ) -> list[Article]:
                return []

        with pytest.raises(TypeError):
            IncompleteScraper()  # type: ignore[abstract]


class TestConcreteScraper:
    @pytest.fixture
    def scraper_class(self) -> type[BaseScraper]:
        class MinimalScraper(BaseScraper):
            async def fetch_articles(
                self, source: Source, company: Company, date_range: DateRange
            ) -> list[Article]:
                return []

            async def is_complete(
                self, source: Source, company: Company, date_range: DateRange
            ) -> bool:
                return True

        return MinimalScraper

    def test_can_instantiate_complete_subclass(self, scraper_class: type[BaseScraper]) -> None:
        scraper = scraper_class()
        assert isinstance(scraper, BaseScraper)

    @pytest.mark.asyncio
    async def test_fetch_articles_returns_expected_value(
        self, scraper_class: type[BaseScraper]
    ) -> None:
        scraper = scraper_class()
        source = Source(
            id="test",
            name="Test Source",
            base_url="https://example.com",
            scraper_module="scrapers.test",
            description="A test source.",
        )
        company = Company(
            bloomberg_ticker="TEST US Equity",
            name="Test Co",
            aliases=["Test"],
        )
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 6, 30))
        articles = await scraper.fetch_articles(source, company, date_range)
        assert articles == []

    @pytest.mark.asyncio
    async def test_is_complete_returns_expected_value(
        self, scraper_class: type[BaseScraper]
    ) -> None:
        scraper = scraper_class()
        source = Source(
            id="test",
            name="Test Source",
            base_url="https://example.com",
            scraper_module="scrapers.test",
            description="A test source.",
        )
        company = Company(
            bloomberg_ticker="TEST US Equity",
            name="Test Co",
            aliases=["Test"],
        )
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 6, 30))
        assert await scraper.is_complete(source, company, date_range) is True


class TestScraperLoadError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(ScraperLoadError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(ScraperLoadError):
            raise ScraperLoadError("test error")


def test_default_class_name_derivation() -> None:
    """The default class name follows the convention: last_segment -> CapitalizedScraper."""
    module = load_scraper("scrapers.pcwatch")
    cls = get_scraper_class(module)
    assert cls.__name__ == "PcwatchScraper"
