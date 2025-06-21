import json
import os
from typing import AsyncGenerator, Dict

from dotenv import load_dotenv
import httpx

load_dotenv()
_mcp_url = os.getenv("MCP_URL")
if not _mcp_url:
    raise RuntimeError("MCP_URL environment variable not set")
MCP_URL: str = _mcp_url


async def _stream(tool: str, params: Dict) -> AsyncGenerator[Dict, None]:
    """Yield JSON dicts returned by the MCP server.

    Any malformed JSON or network issues are logged and skipped so callers never
    see exceptions from this helper.
    """
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                MCP_URL,
                json={"tool": tool, "params": params},
            ) as r:
                async for line in r.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except Exception as exc:
                        print(f"[mcp_client] invalid JSON from server: {line!r} ({exc})")
                        continue
                    if isinstance(payload, dict):
                        yield payload
                    else:
                        print(f"[mcp_client] non-dict payload skipped: {payload!r}")
    except httpx.HTTPError as exc:
        print(f"[mcp_client] HTTP error calling {tool}: {exc}")
    except Exception as exc:
        print(f"[mcp_client] unexpected error calling {tool}: {exc}")


async def perform_rag_query(params: Dict) -> list[Dict]:
    try:
        return [c async for c in _stream("perform_rag_query", params)]
    except Exception as exc:
        print(f"[mcp_client] perform_rag_query failed: {exc}")
        return []


async def search_code_examples(params: Dict) -> list[Dict]:
    try:
        return [c async for c in _stream("search_code_examples", params)]
    except Exception as exc:
        print(f"[mcp_client] search_code_examples failed: {exc}")
        return []
