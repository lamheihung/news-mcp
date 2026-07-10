"""Tests for src/tools.py."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Generator
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP

import src.resolver
import src.tools as tools_module
from src.models import Article, Company, DateRange, Source
from src.scraper_base import BaseScraper
from src.tools import (
    init_tools,
    list_sources,
    register_tools,
    research_company,
    resolve_company,
)
from src.watchlist import load_watchlist


def _mock_gemini_client(payload: dict[str, Any]) -> Any:
    """Return a mock Gemini client that responds with the given JSON payload."""
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps(payload)
    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


@pytest.fixture(autouse=True)
def reset_configured_sources(tmp_path: Path) -> Generator[None]:
    """Reset the configured sources before each test."""
    tools_module._configured_sources = []
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text("companies: []\n", encoding="utf-8")
    patcher = patch.object(tools_module, "WATCHLIST_PATH", watchlist_path)
    patcher.start()
    yield
    patcher.stop()


def _write_config(path: Path, sources: list[Source]) -> None:
    """Write a config.yaml with the given sources."""
    lines = ["sources:"]
    for source in sources:
        lines.extend(
            [
                f"  - id: {source.id}",
                f"    name: {source.name}",
                f"    base_url: {source.base_url}",
                f"    scraper_module: {source.scraper_module}",
                f"    description: {source.description}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_init_tools_loads_sources(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
sources:
  - id: reuters
    name: Reuters
    base_url: https://www.reuters.com
    scraper_module: scrapers.reuters
    description: Financial news
""",
        encoding="utf-8",
    )

    init_tools(config_path)
    sources = list_sources()

    assert len(sources) == 1
    assert isinstance(sources[0], Source)
    assert sources[0].id == "reuters"


def test_list_sources_before_init() -> None:
    assert list_sources() == []


def test_resolve_company_tool(tmp_path: Path) -> None:
    expected = Company(
        bloomberg_ticker="MSFT US Equity",
        name="Microsoft Corp.",
        aliases=["Microsoft", "MSFT"],
    )

    with patch("src.tools._resolve_company", return_value=expected) as mock_resolver:
        result = resolve_company("Microsoft")

    assert result == expected
    mock_resolver.assert_called_once_with("Microsoft")


@pytest.mark.asyncio
async def test_research_company_default_date_range(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="example",
                name="Example Source",
                base_url="https://example.com",
                scraper_module="scrapers.example",
                description="An example source.",
            )
        ],
    )
    init_tools(config_path)

    articles = await research_company("AAPL US Equity", "What is Apple up to?")

    assert len(articles) == 2
    for article in articles:
        assert isinstance(article, Article)
        assert article.bloomberg_ticker == "AAPL US Equity"
        published = article.published_at.date()
        assert published >= date.today() - timedelta(days=180)
        assert published <= date.today()


@pytest.mark.asyncio
async def test_research_company_source_filter(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="example",
                name="Example Source",
                base_url="https://example.com",
                scraper_module="scrapers.example",
                description="An example source.",
            ),
            Source(
                id="pcwatch",
                name="PC Watch",
                base_url="https://pc.watch.impress.co.jp/",
                scraper_module="scrapers.pcwatch",
                description="Japanese PC/tech news site.",
            ),
        ],
    )
    init_tools(config_path)

    mock_article = Article(
        id="pcwatch-001",
        bloomberg_ticker="AAPL US Equity",
        source_id="pcwatch",
        url="https://pc.watch.impress.co.jp/docs/article/1.html",
        title="PC Watch article",
        content="PC Watch content",
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        stored_path=Path("data/AAPL US Equity/pcwatch/pcwatch-001.md"),
    )

    def _make_scraper(source: Source) -> MagicMock | None:
        if source.id == "example":
            return None
        pcwatch_scraper = MagicMock()
        pcwatch_scraper.is_complete = AsyncMock(return_value=True)
        pcwatch_scraper.fetch_articles = AsyncMock(return_value=[mock_article])
        return pcwatch_scraper

    with patch("src.tools._load_source_scraper", side_effect=_make_scraper) as mock_load_scraper:
        articles = await research_company(
            "AAPL US Equity",
            "News please",
            sources=["example"],
        )

    assert len(articles) == 2
    assert all(article.source_id == "example" for article in articles)
    mock_load_scraper.assert_called_once()


@pytest.mark.asyncio
async def test_research_company_custom_date_range(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="example",
                name="Example Source",
                base_url="https://example.com",
                scraper_module="scrapers.example",
                description="An example source.",
            )
        ],
    )
    init_tools(config_path)

    start = (datetime.now() - timedelta(days=250)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    articles = await research_company(
        "AAPL US Equity",
        "News please",
        start_date=start,
        end_date=end,
    )

    assert len(articles) == 3


def test_register_tools() -> None:
    mcp = FastMCP("Test")
    register_tools(mcp)

    async def check() -> None:
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}
        assert names == {"list_sources", "resolve_company", "research_company"}

    asyncio.run(check())


def test_list_sources_tool_schema_and_serialization(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
sources:
  - id: example
    name: Example Source
    base_url: https://example.com
    scraper_module: scrapers.example
    description: An example source.
""",
        encoding="utf-8",
    )
    init_tools(config_path)

    mcp = FastMCP("Test")
    register_tools(mcp)

    async def check() -> None:
        tool = await mcp.get_tool("list_sources")
        assert tool is not None
        assert tool.name == "list_sources"
        assert tool.parameters is not None
        assert tool.parameters.get("type") == "object"
        assert "identifier" not in tool.parameters.get("properties", {})

        result = await mcp.call_tool("list_sources", {})
        assert result.is_error is False
        assert result.structured_content is not None
        sources = result.structured_content["result"]
        assert len(sources) == 1
        assert sources[0]["id"] == "example"

    asyncio.run(check())


def test_resolve_company_tool_schema_and_serialization() -> None:
    expected = Company(
        bloomberg_ticker="MSFT US Equity",
        name="Microsoft Corp.",
        aliases=["Microsoft", "MSFT"],
    )

    mcp = FastMCP("Test")
    register_tools(mcp)

    async def check() -> None:
        tool = await mcp.get_tool("resolve_company")
        assert tool is not None
        assert tool.name == "resolve_company"
        assert tool.parameters is not None
        properties = tool.parameters.get("properties", {})
        assert "identifier" in properties
        assert properties["identifier"]["type"] == "string"
        assert "identifier" in tool.parameters.get("required", [])

        assert tool.output_schema is not None
        output_properties = tool.output_schema.get("properties", {})
        assert "bloomberg_ticker" in output_properties
        assert "name" in output_properties
        assert "aliases" in output_properties

        with patch.object(tools_module, "_resolve_company", return_value=expected) as mock_resolver:
            result = await mcp.call_tool("resolve_company", {"identifier": "Microsoft"})

        assert result.is_error is False
        assert result.structured_content is not None
        company = result.structured_content
        assert company["bloomberg_ticker"] == "MSFT US Equity"
        assert company["name"] == "Microsoft Corp."
        assert "Microsoft" in company["aliases"]
        mock_resolver.assert_called_once_with("Microsoft")

    asyncio.run(check())


def test_research_company_tool_schema_and_serialization(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
sources:
  - id: example
    name: Example Source
    base_url: https://example.com
    scraper_module: scrapers.example
    description: An example source.
""",
        encoding="utf-8",
    )
    init_tools(config_path)

    mcp = FastMCP("Test")
    register_tools(mcp)

    async def check() -> None:
        tool = await mcp.get_tool("research_company")
        assert tool is not None
        assert tool.name == "research_company"
        assert tool.parameters is not None
        properties = tool.parameters.get("properties", {})
        assert "bloomberg_ticker" in properties
        assert "question" in properties
        assert "start_date" in properties
        assert "end_date" in properties
        assert "sources" in properties
        required = tool.parameters.get("required", [])
        assert "bloomberg_ticker" in required
        assert "question" in required
        assert "start_date" not in required

        result = await mcp.call_tool(
            "research_company",
            {
                "bloomberg_ticker": "AAPL US Equity",
                "question": "What is Apple up to?",
            },
        )
        assert result.is_error is False
        assert result.structured_content is not None
        articles = result.structured_content["result"]
        assert len(articles) == 2
        for article in articles:
            assert "id" in article
            assert "bloomberg_ticker" in article
            assert "published_at" in article
            assert "stored_path" in article

    asyncio.run(check())


@pytest.mark.asyncio
async def test_research_company_upserts_watchlist(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="example",
                name="Example Source",
                base_url="https://example.com",
                scraper_module="scrapers.example",
                description="An example source.",
            )
        ],
    )
    init_tools(config_path)

    await research_company("TICKER US Equity", "question")

    watchlist = load_watchlist(tools_module.WATCHLIST_PATH)
    assert len(watchlist) == 1
    assert watchlist[0].bloomberg_ticker == "TICKER US Equity"


@pytest.mark.asyncio
async def test_research_company_loads_scraper_and_merges_results(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="pcwatch",
                name="PC Watch",
                base_url="https://pc.watch.impress.co.jp/",
                scraper_module="scrapers.pcwatch",
                description="Japanese PC/tech news site.",
            )
        ],
    )
    init_tools(config_path)

    now = datetime.now()
    fetched = Article(
        id="fetched-001",
        bloomberg_ticker="AAPL US Equity",
        source_id="pcwatch",
        url="https://pc.watch.impress.co.jp/docs/article/1.html",
        title="Fetched article",
        content="Fetched content",
        published_at=now - timedelta(days=10),
        fetched_at=now,
        stored_path=Path("data/AAPL US Equity/pcwatch/fetched-001.md"),
    )

    with patch("src.tools._load_source_scraper") as mock_load_scraper:
        scraper = MagicMock()
        scraper.is_complete = AsyncMock(return_value=False)
        scraper.fetch_articles = AsyncMock(return_value=[fetched])
        mock_load_scraper.return_value = scraper

        articles = await research_company("AAPL US Equity", "question")

    assert len(articles) == 1
    assert articles[0].url == fetched.url
    scraper.is_complete.assert_awaited_once()
    scraper.fetch_articles.assert_awaited_once()


@pytest.mark.asyncio
async def test_research_company_skips_fetch_when_complete(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="pcwatch",
                name="PC Watch",
                base_url="https://pc.watch.impress.co.jp/",
                scraper_module="scrapers.pcwatch",
                description="Japanese PC/tech news site.",
            )
        ],
    )
    init_tools(config_path)

    with patch("src.tools._load_source_scraper") as mock_load_scraper:
        scraper = MagicMock()
        scraper.is_complete = AsyncMock(return_value=True)
        scraper.fetch_articles = AsyncMock(return_value=[])
        mock_load_scraper.return_value = scraper

        with patch("src.tools.list_cached_articles", return_value=[]) as mock_list_cached:
            articles = await research_company("AAPL US Equity", "question")

    assert articles == []
    scraper.is_complete.assert_awaited_once()
    scraper.fetch_articles.assert_not_awaited()
    mock_list_cached.assert_called_once()


def test_resolve_company_upserts_watchlist(tmp_path: Path) -> None:
    """Calling the resolve_company tool persists the resolved company."""
    resolver_watchlist_path = tmp_path / "resolver-watchlist.yaml"
    mock_client = _mock_gemini_client(
        {
            "bloomberg_ticker": "AAPL US Equity",
            "name": "Apple Inc.",
            "aliases": ["Apple", "AAPL"],
        }
    )

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with patch.object(src.resolver, "WATCHLIST_PATH", resolver_watchlist_path):
                company = resolve_company("Apple")

    assert company.bloomberg_ticker == "AAPL US Equity"
    entries = load_watchlist(resolver_watchlist_path)
    assert len(entries) == 1
    assert entries[0].bloomberg_ticker == "AAPL US Equity"
    assert entries[0].name == "Apple Inc."


@pytest.mark.asyncio
async def test_research_company_merges_results_from_mock_scraper_class(tmp_path: Path) -> None:
    """A concrete BaseScraper subclass can be loaded and its results merged."""

    class MockScraper(BaseScraper):
        async def fetch_articles(
            self, source: Source, company: Company, date_range: DateRange
        ) -> list[Article]:
            return [
                Article(
                    id="mock-001",
                    bloomberg_ticker=company.bloomberg_ticker,
                    source_id=source.id,
                    url="https://example.com/mock-001",
                    title="Mock article",
                    content="Mock content",
                    published_at=datetime(2026, 6, 15, 12, 0),
                    fetched_at=datetime.now(),
                    stored_path=Path("data/mock.md"),
                )
            ]

        async def is_complete(
            self, source: Source, company: Company, date_range: DateRange
        ) -> bool:
            return False

    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        [
            Source(
                id="mock",
                name="Mock Source",
                base_url="https://example.com",
                scraper_module="tests.test_tools_mock_scraper",
                description="A mock source.",
            )
        ],
    )
    init_tools(config_path)

    with patch("src.tools.load_scraper") as mock_load:
        fake_module = MagicMock()
        fake_module.__name__ = "mock"
        fake_module.MockScraper = MockScraper
        mock_load.return_value = fake_module

        articles = await research_company("TICKER US Equity", "question")

    assert len(articles) == 1
    assert articles[0].source_id == "mock"
    assert articles[0].url == "https://example.com/mock-001"
    mock_load.assert_called_once_with("tests.test_tools_mock_scraper")
