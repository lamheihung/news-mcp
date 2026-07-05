"""Tests for Pydantic data models in src/models.py."""

from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models import Article, Company, DateRange, Source


def test_company_creation() -> None:
    company = Company(bloomberg_ticker="AAPL US", name="Apple Inc.", aliases=["AAPL"])
    assert company.bloomberg_ticker == "AAPL US"
    assert company.name == "Apple Inc."
    assert company.aliases == ["AAPL"]


def test_company_missing_field_raises() -> None:
    with pytest.raises(ValidationError):
        Company(bloomberg_ticker="AAPL US", name="Apple Inc.")  # type: ignore[call-arg]


def test_source_creation() -> None:
    source = Source(
        id="reuters",
        name="Reuters",
        base_url="https://www.reuters.com",
        scraper_module="scrapers.reuters",
        description="Financial news",
    )
    assert source.id == "reuters"
    assert source.name == "Reuters"


def test_source_missing_field_raises() -> None:
    with pytest.raises(ValidationError):
        Source(  # type: ignore[call-arg]
            id="reuters",
            name="Reuters",
            base_url="https://www.reuters.com",
        )


def test_article_creation_and_serialization() -> None:
    article = Article(
        id="abc123",
        bloomberg_ticker="AAPL US",
        source_id="reuters",
        url="https://www.reuters.com/article",
        title="Apple Earnings",
        content="Apple reported strong earnings.",
        published_at=datetime(2024, 6, 1, 12, 0, 0),
        fetched_at=datetime(2024, 6, 1, 13, 0, 0),
        stored_path=Path("data/AAPL US/reuters/abc123.md"),
    )
    data = article.model_dump()
    expected_fields = {
        "id",
        "bloomberg_ticker",
        "source_id",
        "url",
        "title",
        "content",
        "published_at",
        "fetched_at",
        "stored_path",
    }
    assert set(data.keys()) == expected_fields
    assert data["bloomberg_ticker"] == "AAPL US"


def test_article_missing_field_raises() -> None:
    with pytest.raises(ValidationError):
        Article(  # type: ignore[call-arg]
            id="abc123",
            bloomberg_ticker="AAPL US",
            source_id="reuters",
            url="https://www.reuters.com/article",
            title="Apple Earnings",
            content="Apple reported strong earnings.",
            published_at=datetime(2024, 6, 1, 12, 0, 0),
            fetched_at=datetime(2024, 6, 1, 13, 0, 0),
        )


def test_daterange_valid() -> None:
    dr = DateRange(start=date(2024, 1, 1), end=date(2024, 12, 31))
    assert dr.start == date(2024, 1, 1)
    assert dr.end == date(2024, 12, 31)


def test_daterange_equal_start_end_ok() -> None:
    dr = DateRange(start=date(2024, 1, 1), end=date(2024, 1, 1))
    assert dr.start == dr.end


def test_daterange_end_before_start_raises() -> None:
    with pytest.raises(ValidationError):
        DateRange(start=date(2024, 6, 1), end=date(2024, 1, 1))
