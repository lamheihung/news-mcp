# FastMCP server entry point
# See architecture/001-architecture-design.md

import logging
from pathlib import Path

from fastmcp import FastMCP

from src.tools import init_tools, register_tools

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure structured logging for the MCP server process."""
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def create_app(config_path: Path = Path("config.yaml")) -> FastMCP:
    """Create and configure the FastMCP application.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        A FastMCP app with all tool handlers registered.
    """
    mcp = FastMCP("InvestmentResearch")
    logger.info("Loading configuration from %s", config_path)
    init_tools(config_path)
    register_tools(mcp)
    logger.info("Registered MCP tools: list_sources, resolve_company, research_company")
    return mcp


_configure_logging()
mcp = create_app()

if __name__ == "__main__":
    logger.info("Starting InvestmentResearch MCP server over stdio")
    mcp.run(transport="stdio")
