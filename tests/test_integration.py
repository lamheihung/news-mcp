"""Integration smoke test for the InvestmentResearch MCP server.

Starts the server as a subprocess over stdio and exercises all three MCP tools
through the transport layer.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

ENV_PATH = Path(".env")


def _load_env_file(path: Path = ENV_PATH) -> None:
    """Load key=value pairs from a .env file into the environment."""
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


@pytest.fixture(scope="module", autouse=True)
def load_env() -> None:
    """Ensure .env is loaded before the integration test runs."""
    _load_env_file()


def test_server_smoke() -> None:
    """Run an end-to-end smoke test against the stdio MCP server."""

    async def run() -> None:
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "main.py"],
            env=os.environ.copy(),
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(
                read,
                write,
                read_timeout_seconds=timedelta(seconds=30),
            ) as session:
                await session.initialize()

                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert names == {
                    "list_sources",
                    "resolve_company",
                    "research_company",
                    "get_company_status",
                    "set_search_terms",
                    "reset_source_cache",
                    "get_research_diagnostics",
                }

                list_result = await session.call_tool("list_sources", {})
                assert list_result.isError is False
                assert list_result.structuredContent is not None
                sources = list_result.structuredContent["result"]
                ids = {source["id"] for source in sources}
                assert "example" in ids
                assert "pcwatch" in ids

                if os.environ.get("GEMINI_API_KEY"):
                    try:
                        resolve_result = await session.call_tool(
                            "resolve_company", {"identifier": "Apple"}
                        )
                    except (TimeoutError, McpError) as exc:
                        pytest.skip(f"Live resolver call unavailable or timed out: {exc}")
                    if resolve_result.isError:
                        error_text = ""
                        if resolve_result.content:
                            error_text = getattr(resolve_result.content[0], "text", "")
                        pytest.skip(f"Live resolver returned an error: {error_text}")
                    assert resolve_result.structuredContent is not None
                    company = resolve_result.structuredContent
                    assert company["bloomberg_ticker"]
                    assert "Apple" in company["aliases"]
                else:
                    pytest.skip("GEMINI_API_KEY not set; skipping live resolver call")

                research_result = await session.call_tool(
                    "research_company",
                    {
                        "bloomberg_ticker": "AAPL US Equity",
                        "question": "latest news",
                    },
                )
                assert research_result.isError is False
                assert research_result.structuredContent is not None
                articles = research_result.structuredContent["result"]
                assert len(articles) >= 1
                for article in articles:
                    assert article["bloomberg_ticker"] == "AAPL US Equity"
                    assert article["id"]
                    assert article["title"]
                    assert article["content"]
                    assert article["published_at"]

                # Optional pcwatch real scraping path. Skip when Playwright is not
                # installed or the browser cannot be launched.
                try:
                    import playwright  # noqa: F401
                except ImportError:
                    pass
                else:
                    try:
                        pcwatch_result = await session.call_tool(
                            "research_company",
                            {
                                "bloomberg_ticker": "000660 KS Equity",
                                "question": "latest news",
                                "sources": ["pcwatch"],
                                "start_date": (date.today() - timedelta(days=30)).isoformat(),
                                "end_date": date.today().isoformat(),
                            },
                        )
                    except (TimeoutError, McpError) as exc:
                        pytest.skip(f"pcwatch research unavailable: {exc}")

                    if pcwatch_result.isError:
                        error_text = ""
                        if pcwatch_result.content:
                            error_text = getattr(pcwatch_result.content[0], "text", "")
                        pytest.skip(f"pcwatch research returned an error: {error_text}")

                    assert pcwatch_result.structuredContent is not None
                    pcwatch_articles = pcwatch_result.structuredContent["result"]
                    assert isinstance(pcwatch_articles, list)
                    for article in pcwatch_articles:
                        assert article["bloomberg_ticker"] == "000660 KS Equity"
                        assert article["source_id"] == "pcwatch"
                        assert article["id"]
                        assert article["title"]
                        assert article["published_at"]

    asyncio.run(run())
