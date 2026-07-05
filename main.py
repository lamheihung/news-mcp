# FastMCP server entry point
# See architecture/001-architecture-design.md

from pathlib import Path

from fastmcp import FastMCP

from src.tools import init_tools, register_tools


def create_app(config_path: Path = Path("config.yaml")) -> FastMCP:
    """Create and configure the FastMCP application.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        A FastMCP app with all tool handlers registered.
    """
    mcp = FastMCP("InvestmentResearch")
    init_tools(config_path)
    register_tools(mcp)
    return mcp


mcp = create_app()

if __name__ == "__main__":
    mcp.run(transport="stdio")
