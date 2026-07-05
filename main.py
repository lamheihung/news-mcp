# FastMCP server entry point
# See architecture/001-architecture-design.md

from fastmcp import FastMCP

mcp = FastMCP("InvestmentResearch")

if __name__ == "__main__":
    mcp.run(transport="stdio")
