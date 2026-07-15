"""Tests for Pydantic data models in src/models.py."""

from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models import (
    Article,
    Company,
    CompanyStatus,
    DateRange,
    ResearchDiagnostics,
    Source,
    SourceStatus,
)


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
        "relevance_score",
        "embedding",
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


def test_article_relevance_score_optional() -> None:
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
        relevance_score=0.87,
    )
    assert article.relevance_score == 0.87


def test_article_relevance_score_defaults_to_none() -> None:
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
    assert article.relevance_score is None


def test_article_relevance_score_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        Article(
            id="abc123",
            bloomberg_ticker="AAPL US",
            source_id="reuters",
            url="https://www.reuters.com/article",
            title="Apple Earnings",
            content="Apple reported strong earnings.",
            published_at=datetime(2024, 6, 1, 12, 0, 0),
            fetched_at=datetime(2024, 6, 1, 13, 0, 0),
            stored_path=Path("data/AAPL US/reuters/abc123.md"),
            relevance_score=1.5,
        )


def test_source_status_creation() -> None:
    status = SourceStatus(
        source_id="pcwatch",
        search_terms=["SK Hynix"],
        exhausted_before=date(2024, 7, 11),
        cached_article_count=21,
    )
    assert status.source_id == "pcwatch"
    assert status.cached_article_count == 21


def test_source_status_exhausted_before_optional() -> None:
    status = SourceStatus(
        source_id="example",
        search_terms=[],
        cached_article_count=3,
    )
    assert status.exhausted_before is None


def test_company_status_creation_and_json_dump() -> None:
    company_status = CompanyStatus(
        bloomberg_ticker="000660 KS Equity",
        name="SK Hynix Inc.",
        aliases=["SK Hynix", "SK Hynix Inc.", "Hynix", "000660"],
        sources={
            "pcwatch": SourceStatus(
                source_id="pcwatch",
                search_terms=["SK Hynix"],
                exhausted_before=date(2024, 7, 11),
                cached_article_count=21,
            ),
            "example": SourceStatus(
                source_id="example",
                search_terms=[],
                cached_article_count=3,
            ),
        },
    )
    data = company_status.model_dump(mode="json")
    assert data["bloomberg_ticker"] == "000660 KS Equity"
    assert data["sources"]["pcwatch"]["search_terms"] == ["SK Hynix"]
    assert data["sources"]["pcwatch"]["exhausted_before"] == "2024-07-11"
    assert data["sources"]["example"]["exhausted_before"] is None


def test_research_diagnostics_creation_and_json_dump() -> None:
    diagnostics = ResearchDiagnostics(
        bloomberg_ticker="000660 KS Equity",
        source_id="pcwatch",
        date_range=DateRange(start=date(2025, 7, 14), end=date(2026, 7, 14)),
        search_terms=["SK Hynix"],
        exhausted_before=date(2024, 7, 11),
        is_complete=True,
        cached_article_count=0,
        planned_action="return_cached",
        reason="date_range.start (2025-07-14) >= exhausted_before (2024-07-11)",
    )
    data = diagnostics.model_dump(mode="json")
    assert data["bloomberg_ticker"] == "000660 KS Equity"
    assert data["date_range"] == {"start": "2025-07-14", "end": "2026-07-14"}
    assert data["planned_action"] == "return_cached"
    assert data["is_complete"] is True
