"""Circuitron agent implementation using OpenAI Agents SDK."""
import asyncio
import json
import os
from typing import Any, Dict

from agents import Agent, Runner, RunResult, ModelSettings
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agents.exceptions import MaxTurnsExceeded, ModelBehaviorError, AgentsException
from .prompts import PLAN_PROMPT, DOC_QA_PROMPT, SYSTEM_PROMPT, USER_TEMPLATE
from .part_lookup import extract_queries, lookup_parts
from .skidl_exec import run_skidl_script
from .utils_llm import AGENT_PLAN, OPENAI_API_KEY
from .utils_text import trim_to_tokens

# Configuration
MODEL_CODE = os.getenv("MODEL_CODE", "gpt-4o")
MODEL_TEMP = float(os.getenv("MODEL_TEMP", "0.15"))
MAX_TURNS = int(os.getenv("MAX_TOOL_CALLS", "5"))  # Renamed for clarity


# ---------------------------------------------------------------------------
# MCP Server Setup
# ---------------------------------------------------------------------------

async def create_mcp_server():
    """Create and initialize the MCP server connection using official SDK."""
    port = os.getenv("PORT", "8051")
    base_url = os.getenv("MCP_URL") or f"http://localhost:{port}"
    base_url = base_url.rstrip("/")
    if base_url.endswith("/sse"):
        base_url = base_url[: -len("/sse")]
    
    # Use the official OpenAI Agents SDK MCP integration with proper params
    params = MCPServerStreamableHttpParams(
        url=f"{base_url}/mcp",
        headers={},
        timeout=30.0,
        sse_read_timeout=30.0,
        terminate_on_close=True
    )
    server = MCPServerStreamableHttp(params=params)
    return server


# ---------------------------------------------------------------------------
# Agent Creation (will be initialized with MCP server)
# ---------------------------------------------------------------------------

_mcp_server = None
CODE_AGENT = None

async def get_code_agent():
    """Get or create the code generation agent with MCP server."""
    global _mcp_server, CODE_AGENT
    
    if CODE_AGENT is None:
        # Initialize MCP server
        _mcp_server = await create_mcp_server()
        
        # Create the code generation agent with MCP server
        CODE_AGENT = Agent(
            name="Code Generation Agent",
            instructions=SYSTEM_PROMPT,
            model=MODEL_CODE,
            model_settings=ModelSettings(temperature=MODEL_TEMP),
            mcp_servers=[_mcp_server]  # Official MCP integration
        )
    
    return CODE_AGENT


# ---------------------------------------------------------------------------
# Legacy function support (for backward compatibility during transition)
# ---------------------------------------------------------------------------

async def retrieve_docs_legacy(query: str, match_count: int = 3) -> str:
    """Legacy function that uses MCP client directly (for backward compatibility)."""
    from .mcp_client import perform_rag_query, search_code_examples
    
    try:
        docs = await perform_rag_query({"query": query, "match_count": match_count})
    except Exception as exc:
        print(f"[agent] retrieve_docs doc query failed: {exc}")
        docs = []
    
    try:
        codes = await search_code_examples({"query": query, "match_count": match_count})
    except Exception as exc:
        print(f"[agent] retrieve_docs code query failed: {exc}")
        codes = []

    ctx_lines = []
    for c in docs + codes:
        if isinstance(c, dict) and "content" in c:
            ctx_lines.append(c["content"])
        else:
            print(f"[agent] skipping invalid RAG result: {c!r}")
    return trim_to_tokens("\n".join(ctx_lines))


# ---------------------------------------------------------------------------
# Pipeline Functions
# ---------------------------------------------------------------------------

async def pipeline(user_req: str):
    """Main pipeline for Circuitron PCB design generation."""
    
    # Get the agent with MCP server integration
    code_agent = await get_code_agent()
    
    # A ▸ PLAN
    plan_result = await Runner.run(AGENT_PLAN, PLAN_PROMPT.replace("REQUIREMENTS", user_req))
    plan = plan_result.final_output
    display = plan.split("</think>", 1)[-1] if "</think>" in plan else plan
    print("\n--- PLAN ---\n", display)
    
    if input("\nApprove plan? [y/N] ").lower() != "y":
        print("Aborted.")
        return

    # B ▸ QUERIES → PARTS
    queries = extract_queries(plan)
    print(f"\n--- QUERIES ---\n{queries}")
    
    parts_list = []
    for q in queries.splitlines():
        q = q.strip()
        if q:
            print(f"[part_lookup] searching for: {q}")
            found = lookup_parts(q)
            parts_list.extend(found)

    # Legacy support: use the custom MCP client for context gathering
    context_for_code = ""
    for q in queries.splitlines():
        q = q.strip()
        if q:
            try:
                # Use legacy function during transition
                resp = await retrieve_docs_legacy(q, 3)
                context_for_code += f"\n{resp}"
            except Exception as exc:
                print(f"[agent] skipping docs for '{q}': {exc}")

    # C ▸ CODE GENERATION
    user_prompt = USER_TEMPLATE.format(
        requirements=user_req,
        plan=plan,
        parts=json.dumps(parts_list, indent=2),
        context=context_for_code.strip(),
    )

    print("\n--- GENERATING CODE ---")
    try:
        # Use the agent with MCP server integration
        # The agent can now access MCP tools directly through the SDK
        code_result = await Runner.run(
            code_agent,
            user_prompt,
            max_turns=MAX_TURNS
        )
        
        code = code_result.final_output
        print("\n--- GENERATED CODE ---")
        print(code)
        
        # D ▸ TEST
        success, output = run_skidl_script(code)
        if success:
            print("\n--- SKIDL EXECUTION: SUCCESS ---")
            print(output)
        else:
            print("\n--- SKIDL EXECUTION: FAILED ---")
            print(output)
            
    except (MaxTurnsExceeded, ModelBehaviorError, AgentsException) as exc:
        print(f"\n--- AGENT ERROR ---\n{exc}")
    except Exception as exc:
        print(f"\n--- UNEXPECTED ERROR ---\n{exc}")


def cli():
    """Command-line interface for Circuitron."""
    req = input("Enter design request: ")
    asyncio.run(pipeline(req))


if __name__ == "__main__":
    cli()
