"""Abstract base class for scraper plugins."""

from abc import ABC, abstractmethod

from src.models import Article, Company, DateRange, Source


class BaseScraper(ABC):
    """Base class for source-specific scraper plugins."""

    @abstractmethod
    async def fetch_articles(
        self, source: Source, company: Company, date_range: DateRange
    ) -> list[Article]:
        """Fetch articles for a company from this source within date_range."""

    @abstractmethod
    async def is_complete(self, source: Source, company: Company, date_range: DateRange) -> bool:
        """Return True if cached articles fully cover the requested date_range."""
