import os, json, httpx, sseclient, asyncio
from dotenv import load_dotenv

load_dotenv()
MCP_URL = os.getenv("MCP_URL")

async def _stream(tool: str, params: dict):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", MCP_URL,
                                 json={"tool": tool, "params": params}) as r:
            async for line in r.aiter_lines():
                if line.strip():
                    yield json.loads(line)

async def perform_rag_query(params: dict):
    return [c async for c in _stream("perform_rag_query", params)]

async def search_code_examples(params: dict):
    return [c async for c in _stream("search_code_examples", params)]
