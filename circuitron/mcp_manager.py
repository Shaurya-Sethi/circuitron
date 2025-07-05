"""Manage lifecycle of MCP servers used in Circuitron."""

from __future__ import annotations
import asyncio
import logging

from agents.mcp import MCPServer

from .tools import create_mcp_server


class MCPManager:
    """Central manager for MCP server connections."""

    def __init__(self) -> None:
        self._server = create_mcp_server()

    async def _connect_server_with_timeout(self) -> None:
        """Attempt to connect to the MCP server with retries."""
        for attempt in range(3):
            try:
                await asyncio.wait_for(self._server.connect(), timeout=20.0)  # type: ignore[no-untyped-call]
                logging.info("Successfully connected to MCP server: %s", self._server.name)
                return
            except Exception as exc:  # pragma: no cover - network errors
                if attempt == 2:
                    logging.warning(
                        "Failed to connect MCP server %s: %s", self._server.name, exc
                    )
                else:
                    await asyncio.sleep(2**attempt)

    async def initialize(self) -> None:
        """Connect the managed MCP server."""
        await self._connect_server_with_timeout()

    async def cleanup(self) -> None:
        """Disconnect the managed MCP server."""
        try:
            await self._server.cleanup()  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover - cleanup errors
            logging.warning("Error cleaning MCP server %s: %s", self._server.name, exc)

    def get_doc_server(self) -> MCPServer:
        """Return the MCP server instance."""
        return self._server

    def get_validation_server(self) -> MCPServer:
        """Return the MCP server instance."""
        return self._server


# Global manager instance used across the application
mcp_manager = MCPManager()

__all__ = ["MCPManager", "mcp_manager"]
