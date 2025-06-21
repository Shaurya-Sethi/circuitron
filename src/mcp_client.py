import json
import os
from typing import Dict, List

from dotenv import load_dotenv
import httpx

load_dotenv()
_mcp_url = os.getenv("MCP_URL")
if not _mcp_url:
    raise RuntimeError("MCP_URL environment variable not set")
MCP_URL: str = _mcp_url


async def _call_tool(tool: str, params: Dict | None) -> List[Dict]:
    """Call a tool on the MCP server via JSON-RPC."""

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": params or {}},
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(MCP_URL, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        print(f"[mcp_client] HTTP request failed for {MCP_URL}: {exc}")
        return []

    if response.status_code != 200:
        txt = response.text[:200]
        print(f"[mcp_client] {response.status_code} from {MCP_URL}: {txt}")
        return []

    try:
        data = response.json()
    except Exception as exc:
        print(f"[mcp_client] invalid JSON from {MCP_URL}: {exc}")
        return []

    result = data.get("result", data) if isinstance(data, dict) else {}
    content = result.get("content") or result.get("results")
    if isinstance(content, list):
        return content

    print(f"[mcp_client] unexpected payload from {MCP_URL}: {data!r}")
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
