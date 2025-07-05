import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from circuitron.mcp_manager import MCPManager


def test_manager_connects_and_cleans_up() -> None:
    server = SimpleNamespace(connect=AsyncMock(), cleanup=AsyncMock(), name="srv")

    with patch(
        "circuitron.mcp_manager.create_mcp_server",
        return_value=server,
    ):
        manager = MCPManager()
        asyncio.run(manager.initialize())
        server.connect.assert_awaited_once()
        asyncio.run(manager.cleanup())
        server.cleanup.assert_awaited_once()
