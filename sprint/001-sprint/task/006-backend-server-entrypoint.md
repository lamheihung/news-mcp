# Task 006: Backend - Server Entrypoint

## Description
Complete the FastMCP server entry point by registering the tool handlers and starting the stdio transport.

## Requirements
- Import the tool handlers from `src.tools` into `main.py`.
- Register `list_sources`, `resolve_company`, and `research_company` with the FastMCP app instance.
- Start the server with `mcp.run(transport="stdio")`.
- Keep the entry point minimal and free of tool implementation logic.
- Ensure the server starts without import errors when `config.yaml` is valid.

## Dependencies
- Blocks: [008]
- Blocked by: [002, 003, 005]
- Parallelizable with: [007]

## Success Criteria (5 points)
1. `main.py` imports `src.tools` and registers all three tool handlers with the `mcp` app.
2. `uv run main.py` starts the stdio server without crashing.
3. The server initializes within two seconds of launch.
4. Removing or corrupting `config.yaml` causes startup to fail with a readable error.
5. `main.py` contains no tool implementation logic beyond registration and startup.

## Status
[006-backend-server-entrypoint-status.md](../status/006-backend-server-entrypoint-status.md)
