"""Tests for main.py server entry point."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from main import create_app


def test_create_app_loads_config_and_registers_tools(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
sources:
  - id: example
    name: Example Source
    base_url: https://example.com
    scraper_module: scrapers.example
    description: An example source for testing.
""",
        encoding="utf-8",
    )

    mcp = create_app(config_path)

    async def check() -> None:
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}
        assert names == {
            "list_sources",
            "resolve_company",
            "research_company",
            "get_company_status",
            "set_search_terms",
            "reset_source_cache",
            "get_research_diagnostics",
        }

    asyncio.run(check())


def test_create_app_fails_on_missing_config(tmp_path: Path) -> None:
    missing_config = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        create_app(missing_config)


def test_create_app_initializes_quickly(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("sources: []\n", encoding="utf-8")

    start = time.perf_counter()
    mcp = create_app(config_path)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
    assert mcp.name == "InvestmentResearch"
