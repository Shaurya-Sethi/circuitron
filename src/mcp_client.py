import json
import os
from typing import Dict, List

from dotenv import load_dotenv
import httpx
from httpx_sse import aconnect_sse

load_dotenv()

_port = os.getenv("PORT", "8051")
_base = os.getenv("MCP_URL")
if _base is None:
    _base = f"http://localhost:{_port}"
_base = _base.rstrip("/")
if _base.endswith("/sse"):
    _base = _base[: -len("/sse")]

MCP_BASE: str = _base
SSE_URL: str = f"{MCP_BASE}/sse"

TRANSPORT = os.getenv("TRANSPORT", "sse").lower()


async def _call_tool(tool: str, params: Dict | None) -> List[Dict]:
    """Call a Fast-MCP tool using the SSE transport."""

    if TRANSPORT != "sse":
        raise RuntimeError("Only TRANSPORT=sse is supported in this client")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": tool,
        "params": params or {},
    }

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with aconnect_sse(client, "GET", SSE_URL) as es:
                endpoint = None
                async for event in es.aiter_sse():
                    if event.event == "endpoint":
                        endpoint = httpx.URL(MCP_BASE).join(event.data)
                        break

                if endpoint is None:
                    print("[mcp_client] no endpoint from MCP server")
                    return []

                response = await client.post(str(endpoint), json=payload)
                if response.status_code not in (200, 202):
                    txt = response.text[:200]
                    print(
                        f"[mcp_client] {response.status_code} from {endpoint}: {txt}"
                    )
                    return []

                async for event in es.aiter_sse():
                    if event.event == "message":
                        try:
                            data = json.loads(event.data)
                        except Exception as exc:  # invalid JSON
                            print(f"[mcp_client] invalid JSON from SSE: {exc}")
                            return []

                        result = data.get("result", data)
                        content = result.get("content") or result.get("results")
                        if isinstance(content, list):
                            return content
                        print(
                            f"[mcp_client] unexpected payload from {endpoint}: {data!r}"
                        )
                        return []
        except httpx.HTTPError as exc:
            print(f"[mcp_client] HTTP request failed for {SSE_URL}: {exc}")
            return []

    return []


async def perform_rag_query(params: Dict) -> list[Dict]:
    try:
        return await _call_tool("perform_rag_query", params)
    except Exception as exc:
        print(f"[mcp_client] perform_rag_query failed: {exc}")
        return []


async def search_code_examples(params: Dict) -> list[Dict]:
    try:
        return await _call_tool("search_code_examples", params)
    except Exception as exc:
        print(f"[mcp_client] search_code_examples failed: {exc}")
        return []
