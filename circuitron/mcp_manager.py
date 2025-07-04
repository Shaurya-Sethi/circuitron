"""Manage lifecycle of MCP servers used in Circuitron."""

from __future__ import annotations
import asyncio
import logging

from agents.mcp import MCPServer

from .tools import create_mcp_documentation_server, create_mcp_validation_server


class MCPManager:
    """Central manager for MCP server connections."""

    def __init__(self) -> None:
        self._doc_server = create_mcp_documentation_server()
        self._validation_server = create_mcp_validation_server()
        self._servers: list[MCPServer] = [self._doc_server, self._validation_server]

    async def _connect_server_with_timeout(self, server: MCPServer) -> None:
        """Attempt to connect to an MCP server with retries."""
        for attempt in range(3):
            try:
                await asyncio.wait_for(server.connect(), timeout=20.0)  # type: ignore[no-untyped-call]
                logging.info("Successfully connected to MCP server: %s", server.name)
                return
            except Exception as exc:  # pragma: no cover - network errors
                if attempt == 2:
                    logging.warning(
                        "Failed to connect MCP server %s: %s", server.name, exc
                    )
                else:
                    await asyncio.sleep(2**attempt)

    async def initialize(self) -> None:
        """Connect all managed servers."""
        for server in self._servers:
            await self._connect_server_with_timeout(server)

    async def cleanup(self) -> None:
        """Disconnect all managed servers."""
        for server in self._servers:
            try:
                await server.cleanup()  # type: ignore[no-untyped-call]
            except Exception as exc:  # pragma: no cover - cleanup errors
                logging.warning("Error cleaning MCP server %s: %s", server.name, exc)

    def get_doc_server(self) -> MCPServer:
        """Return the documentation server instance."""
        return self._doc_server

    def get_validation_server(self) -> MCPServer:
        """Return the validation server instance."""
        return self._validation_server


# Global manager instance used across the application
mcp_manager = MCPManager()

__all__ = ["MCPManager", "mcp_manager"]
