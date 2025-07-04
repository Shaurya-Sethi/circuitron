import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from circuitron.mcp_manager import MCPManager


def test_manager_connects_and_cleans_up() -> None:
    doc_server = SimpleNamespace(connect=AsyncMock(), cleanup=AsyncMock(), name="doc")
    val_server = SimpleNamespace(connect=AsyncMock(), cleanup=AsyncMock(), name="val")

    with (
        patch(
            "circuitron.mcp_manager.create_mcp_documentation_server",
            return_value=doc_server,
        ),
        patch(
            "circuitron.mcp_manager.create_mcp_validation_server",
            return_value=val_server,
        ),
    ):
        manager = MCPManager()
        asyncio.run(manager.initialize())
        doc_server.connect.assert_awaited_once()
        val_server.connect.assert_awaited_once()
        asyncio.run(manager.cleanup())
        doc_server.cleanup.assert_awaited_once()
        val_server.cleanup.assert_awaited_once()
