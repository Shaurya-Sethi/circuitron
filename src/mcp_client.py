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
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            MCP_URL,
            json={"tool": tool, "params": params},
        ) as r:
            async for line in r.aiter_lines():
                if line.strip():
                    yield json.loads(line)


async def perform_rag_query(params: Dict) -> list[Dict]:
    return [c async for c in _stream("perform_rag_query", params)]


async def search_code_examples(params: Dict) -> list[Dict]:
    return [c async for c in _stream("search_code_examples", params)]
