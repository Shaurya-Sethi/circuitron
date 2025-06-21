import asyncio
import contextlib
import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
import httpx
from httpx_sse import aconnect_sse, EventSource

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_port = os.getenv("PORT", "8051")
_base = os.getenv("MCP_URL") or f"http://localhost:{_port}"
_base = _base.rstrip("/")
if _base.endswith("/sse"):
    _base = _base[: -len("/sse")]

MCP_BASE: str = _base
SSE_URL: str = f"{MCP_BASE}/sse"

TRANSPORT = os.getenv("TRANSPORT", "sse").lower()


# ---------------------------------------------------------------------------
# Persistent SSE client implementation
# ---------------------------------------------------------------------------
class _SSEClient:
    """Handles a persistent SSE session with the Fast‑MCP server."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=None)
        self._es_cm = None  # context manager for SSE connection
        self._es: Optional[EventSource] = None
        self._recv_task: Optional[asyncio.Task] = None
        self._endpoint_ready = asyncio.Event()
        self._message_url: Optional[str] = None
        self._next_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    # ------------------------------
    async def connect(self) -> None:
        """Establish the SSE connection if not already connected."""

        async with self._lock:
            if self._es is not None:
                return
            self._es_cm = aconnect_sse(self._client, "GET", SSE_URL)
            self._es = await self._es_cm.__aenter__()
            # Start background listener
            self._recv_task = asyncio.create_task(self._listen())
        # Wait until the server provides the message endpoint
        await self._endpoint_ready.wait()
        if self._message_url is None:
            raise RuntimeError("MCP server did not provide a session endpoint")

        # ── automatic session initialization ──
        # fire a tools/list RPC so the server marks the session "ready"
        try:
            await self.call("tools/list", {})
        except Exception:
            # if it fails, we’ll let your real calls bubble up later
            pass

    # ------------------------------
    async def _listen(self) -> None:
        """Background task consuming SSE events from the server."""
        assert self._es is not None
        try:
            async for event in self._es.aiter_sse():
                if event.event == "endpoint":
                    # Initial message containing /messages/?session_id=...
                    self._message_url = str(httpx.URL(MCP_BASE).join(event.data))
                    self._endpoint_ready.set()
                elif event.event == "message":
                    self._handle_message(event.data)
                elif event.event == "error":
                    # Propagate server errors to all waiters
                    self._fail_all(RuntimeError(f"MCP error event: {event.data}"))
        except Exception as exc:  # Connection failure
            self._fail_all(RuntimeError(f"SSE connection error: {exc}"))
        finally:
            self._endpoint_ready.set()
            if self._es_cm:
                await self._es_cm.__aexit__(None, None, None)
            self._es = None
            self._es_cm = None

    # ------------------------------
    def _handle_message(self, data: str) -> None:
        try:
            payload = json.loads(data)
        except Exception:
            # Ignore malformed data but unblock waiters
            self._fail_all(RuntimeError("Invalid JSON from server"))
            return

        msg_id = payload.get("id")
        fut = self._pending.pop(msg_id, None)
        if fut is not None and not fut.done():
            fut.set_result(payload.get("result", payload))

    # ------------------------------
    def _fail_all(self, exc: Exception) -> None:
        for fut in list(self._pending.values()):
            if not fut.done():
                fut.set_exception(exc)
        self._pending.clear()

    # ------------------------------
    async def call(self, method: str, params: Optional[Dict]) -> List[Dict]:
        if TRANSPORT != "sse":
            raise RuntimeError("Only TRANSPORT=sse is supported in this client")

        await self.connect()

        self._next_id += 1
        msg_id = self._next_id
        payload = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params or {},
        }

        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = fut

        resp = await self._client.post(self._message_url, json=payload)
        if resp.status_code not in (200, 202):
            self._pending.pop(msg_id, None)
            raise RuntimeError(
                f"{resp.status_code} from {self._message_url}: {resp.text[:200]}"
            )

        # Wait for response via SSE
        result = await fut
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                result = {}
        content = result.get("results") or result.get("content")
        if isinstance(content, list):
            return content
        return []

    # ------------------------------
    async def close(self) -> None:
        if self._recv_task:
            self._recv_task.cancel()
            with contextlib.suppress(Exception):
                await self._recv_task
        if self._es_cm:
            await self._es_cm.__aexit__(None, None, None)
        await self._client.aclose()


_client = _SSEClient()


async def _call_tool(tool: str, params: Dict | None) -> List[Dict]:
    """
    Send an MCP JSON-RPC request using the universal "tools/call" method
    and return the streamed result.
    """
    # 1) Wrap your tool name + its params under the standard JSON-RPC envelope
    rpc_params = {
        "name":   tool,
        "params": params or {}
    }
    try:
        # 2) Always call via the JSON-RPC method "tools/call"
        return await _client.call("tools/call", rpc_params)
    except Exception as exc:
        print(f"[mcp_client] {tool} failed: {exc}")
        return []


async def perform_rag_query(params: Dict) -> List[Dict]:
    return await _call_tool("perform_rag_query", params)


async def search_code_examples(params: Dict) -> List[Dict]:
    return await _call_tool("search_code_examples", params)


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
# async def main():
#     results = await perform_rag_query({"query": "op-amp", "match_count": 3})
#     for item in results:
#         print(item["content"])
#
# asyncio.run(main())
