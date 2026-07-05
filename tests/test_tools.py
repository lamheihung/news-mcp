"""Tests for src/tools.py."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from fastmcp import FastMCP

import src.tools as tools_module
from src.models import Article, Company, Source
from src.tools import (
    init_tools,
    list_sources,
    register_tools,
    research_company,
    resolve_company,
)


@pytest.fixture(autouse=True)
def reset_configured_sources() -> None:
    """Reset the configured sources before each test."""
    tools_module._configured_sources = []


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


def test_resolve_company_tool() -> None:
    expected = Company(
        bloomberg_ticker="MSFT US Equity",
        name="Microsoft Corp.",
        aliases=["Microsoft", "MSFT"],
    )

    with patch("src.tools._resolve_company", return_value=expected) as mock_resolver:
        result = resolve_company("Microsoft")

    assert result == expected
    mock_resolver.assert_called_once_with("Microsoft")


def test_research_company_default_date_range() -> None:
    articles = research_company("AAPL US Equity", "What is Apple up to?")

    assert len(articles) == 2
    for article in articles:
        assert isinstance(article, Article)
        assert article.bloomberg_ticker == "AAPL US Equity"
        published = article.published_at.date()
        assert published >= date.today() - timedelta(days=180)
        assert published <= date.today()


def test_research_company_source_filter() -> None:
    articles = research_company(
        "AAPL US Equity",
        "News please",
        sources=["example"],
    )

    assert len(articles) == 1
    assert articles[0].source_id == "example"


def test_research_company_custom_date_range() -> None:
    start = (datetime.now() - timedelta(days=250)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    articles = research_company(
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
