"""Refactored agent pipeline using handoffs and structured outputs."""
import asyncio
import json
import os
from typing import Any, Dict, Optional

from agents import Agent, Runner, ModelSettings, handoff, RunContextWrapper
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agents.exceptions import MaxTurnsExceeded, ModelBehaviorError, AgentsException
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from pydantic import BaseModel

from .models import (
    PlanOutput, PartSearchOutput, PartLookupOutput, DocumentationOutput, 
    CodeOutput, PlanApproval, PartsApproval, CodeApproval
)
from .part_lookup import lookup_parts
from .skidl_exec import run_skidl_script

# Configuration
MODEL_PLAN = os.getenv("MODEL_PLAN", "gpt-4o-mini")
MODEL_PART = os.getenv("MODEL_PART", "gpt-4o-mini") 
MODEL_DOC = os.getenv("MODEL_DOC", "gpt-4o-mini")
MODEL_CODE = os.getenv("MODEL_CODE", "gpt-4o")
MODEL_TEMP = float(os.getenv("MODEL_TEMP", "0.15"))
MAX_TURNS = int(os.getenv("MAX_TOOL_CALLS", "5"))


class CircuitronContext(BaseModel):
    """Context passed between agents in the pipeline."""
    user_request: str
    current_stage: str
    plan: Optional[PlanOutput] = None
    cleaned_queries: Optional[PartSearchOutput] = None
    found_parts: Optional[PartLookupOutput] = None
    documentation: Optional[DocumentationOutput] = None
    final_code: Optional[CodeOutput] = None


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
# Agent Definitions with Structured Outputs
# ---------------------------------------------------------------------------

# Import structured prompts
from .prompts_structured import (
    PLAN_PROMPT_STRUCTURED, PART_SEARCH_PROMPT_STRUCTURED, 
    DOC_AGENT_PROMPT_STRUCTURED, CODE_AGENT_PROMPT_STRUCTURED
)

# 1. Planning Agent
planning_agent = Agent[CircuitronContext](
    name="Planning Agent",
    instructions=prompt_with_handoff_instructions(PLAN_PROMPT_STRUCTURED),
    model=MODEL_PLAN,
    model_settings=ModelSettings(temperature=MODEL_TEMP),
    output_type=PlanOutput
)

# 2. Part Search Agent  
part_search_agent = Agent[CircuitronContext](
    name="Part Search Agent",
    instructions=prompt_with_handoff_instructions(PART_SEARCH_PROMPT_STRUCTURED),
    model=MODEL_PART,
    model_settings=ModelSettings(temperature=MODEL_TEMP),
    output_type=PartSearchOutput
)

# 3. Documentation Agent
documentation_agent = Agent[CircuitronContext](
    name="Documentation Agent", 
    instructions=prompt_with_handoff_instructions(DOC_AGENT_PROMPT_STRUCTURED),
    model=MODEL_DOC,
    model_settings=ModelSettings(temperature=MODEL_TEMP),
    output_type=DocumentationOutput
)

# 4. Code Generation Agent (with MCP)
async def create_code_agent(mcp_server):
    return Agent[CircuitronContext](
        name="Code Generation Agent",
        instructions=prompt_with_handoff_instructions(CODE_AGENT_PROMPT_STRUCTURED),
        model=MODEL_CODE,
        model_settings=ModelSettings(temperature=MODEL_TEMP),
        output_type=CodeOutput,
        mcp_servers=[mcp_server]
    )


# ---------------------------------------------------------------------------
# Handoff Configuration with Context Passing
# ---------------------------------------------------------------------------

async def on_plan_handoff(ctx: RunContextWrapper[CircuitronContext], plan_data: PlanOutput):
    """Process plan output and update context."""
    ctx.context.plan = plan_data
    ctx.context.current_stage = "part_search"
    print(f"\n--- PLAN COMPLETE ---")
    print(f"Functional blocks: {len(plan_data.schematic_overview)}")
    print(f"Search queries: {len(plan_data.draft_search_queries)}")
    
    # Human approval point
    approval = await get_plan_approval(plan_data)
    if not approval.approve:
        raise Exception("Plan not approved by user")
    
    if approval.edited_plan:
        ctx.context.plan = approval.edited_plan
        print("Using edited plan from user")


async def on_part_search_handoff(ctx: RunContextWrapper[CircuitronContext], search_data: PartSearchOutput):
    """Process part search and perform actual lookup."""
    ctx.context.cleaned_queries = search_data
    ctx.context.current_stage = "part_lookup"
    
    print(f"\n--- PART SEARCH COMPLETE ---")
    print(f"Cleaned queries: {search_data.cleaned_queries}")
    
    # Perform actual part lookup
    found_parts = []
    failed_queries = []
    
    for query in search_data.cleaned_queries:
        try:
            parts = lookup_parts(query)
            if parts:
                found_parts.extend([{"part": p["part"], "description": p["desc"]} for p in parts])
            else:
                failed_queries.append(query)
        except Exception as e:
            print(f"Failed to lookup {query}: {e}")
            failed_queries.append(query)
    
    lookup_result = PartLookupOutput(found_parts=found_parts, failed_queries=failed_queries)
    ctx.context.found_parts = lookup_result
    
    # Human approval point for parts
    approval = await get_parts_approval(lookup_result)
    if not approval.approve:
        raise Exception("Parts not approved by user")


async def on_doc_handoff(ctx: RunContextWrapper[CircuitronContext], doc_data: DocumentationOutput):
    """Process documentation requirements."""
    ctx.context.documentation = doc_data
    ctx.context.current_stage = "code_generation"
    print(f"\n--- DOCUMENTATION ANALYSIS COMPLETE ---")
    print(f"Research queries identified: {len(doc_data.queries)}")


# Configure handoffs with callbacks and context
part_search_handoff = handoff(
    agent=part_search_agent,
    on_handoff=on_plan_handoff,
    input_type=PlanOutput,
)

documentation_handoff = handoff(
    agent=documentation_agent,
    on_handoff=on_part_search_handoff,
    input_type=PartSearchOutput,
)

async def create_code_handoff(code_agent):
    return handoff(
        agent=code_agent,
        on_handoff=on_doc_handoff,
        input_type=DocumentationOutput,
    )

# ---------------------------------------------------------------------------
# Human Approval Functions
# ---------------------------------------------------------------------------

async def get_plan_approval(plan: PlanOutput) -> PlanApproval:
    """Get human approval for the plan."""
    print("\n" + "="*50)
    print("PLAN REVIEW")
    print("="*50)
    
    print("\nFunctional Blocks:")
    for block in plan.schematic_overview:
        print(f"  • {block}")
        
    print("\nCalculations:")
    for calc in plan.calculations:
        print(f"  {calc}")
        
    print("\nActions:")
    for i, action in enumerate(plan.actions, 1):
        print(f"  {i}. {action}")
        
    print("\nSearch Queries:")
    for query in plan.draft_search_queries:
        print(f"  • {query}")
    
    if plan.limitations:
        print("\nLimitations:")
        for limit in plan.limitations:
            print(f"  • {limit}")
    
    response = input("\nApprove this plan? [y/N/e=edit]: ").lower()
    
    if response == 'y':
        return PlanApproval(stage="planning", content="approved", approve=True)
    elif response == 'e':
        print("Plan editing not implemented in this demo")
        return PlanApproval(stage="planning", content="needs_edit", approve=False)
    else:
        return PlanApproval(stage="planning", content="rejected", approve=False)


async def get_parts_approval(parts: PartLookupOutput) -> PartsApproval:
    """Get human approval for found parts."""
    print("\n" + "="*50)
    print("PARTS REVIEW")
    print("="*50)
    
    print("\nFound Components:")
    for i, part in enumerate(parts.found_parts, 1):
        print(f"  {i}. {part.part} - {part.description}")
    
    if parts.failed_queries:
        print("\nFailed Queries:")
        for query in parts.failed_queries:
            print(f"  • {query}")
    
    response = input("\nApprove these parts? [y/N]: ").lower()
    
    if response == 'y':
        return PartsApproval(stage="parts", content="approved", approve=True)
    else:
        return PartsApproval(stage="parts", content="rejected", approve=False)


async def get_code_approval(code: CodeOutput) -> CodeApproval:
    """Get human approval for generated code."""
    print("\n" + "="*50)
    print("CODE REVIEW")
    print("="*50)
    
    print(f"\nGenerated SKiDL Code ({code.parts_count} parts):")
    print("-" * 40)
    print(code.skidl_code)
    print("-" * 40)
    
    print(f"\nPower Rails: {', '.join(code.power_rails)}")
    print("\nAssumptions:")
    for assumption in code.assumptions:
        print(f"  • {assumption}")
    
    response = input("\nApprove this code? [y/N]: ").lower()
    
    if response == 'y':
        return CodeApproval(stage="code", content="approved", approve=True)
    else:
        return CodeApproval(stage="code", content="rejected", approve=False)


# ---------------------------------------------------------------------------
# Main Pipeline Function
# ---------------------------------------------------------------------------

async def agent_pipeline(user_request: str):
    """Main agent pipeline using handoffs and structured outputs."""
    
    # Initialize context
    context = CircuitronContext(
        user_request=user_request,
        current_stage="planning"
    )
    
    # Create MCP server and code agent
    mcp_server = await create_mcp_server()
    code_agent = await create_code_agent(mcp_server)
    
    # Configure the handoff chain
    planning_agent.handoffs = [part_search_handoff]
    part_search_agent.handoffs = [documentation_handoff]
    documentation_agent.handoffs = [await create_code_handoff(code_agent)]
    
    try:
        print(f"\n--- STARTING CIRCUITRON PIPELINE ---")
        print(f"Request: {user_request}")
        
        # Start the pipeline with the planning agent
        result = await Runner.run(
            starting_agent=planning_agent,
            input=user_request,
            context=context,
            max_turns=MAX_TURNS
        )
        
        # Extract final code
        if isinstance(result.final_output, CodeOutput):
            code_output = result.final_output
            context.final_code = code_output
            
            # Final approval
            approval = await get_code_approval(code_output)
            if approval.approve:
                # Test the code
                print("\n--- TESTING SKIDL CODE ---")
                success, output = run_skidl_script(code_output.skidl_code)
                if success:
                    print("✅ SKiDL execution SUCCESS")
                    print(output)
                else:
                    print("❌ SKiDL execution FAILED")
                    print(output)
            else:
                print("Code not approved by user")
        else:
            print(f"Unexpected final output type: {type(result.final_output)}")
            
    except (MaxTurnsExceeded, ModelBehaviorError, AgentsException) as exc:
        print(f"\n--- AGENT ERROR ---\n{exc}")
    except Exception as exc:
        print(f"\n--- UNEXPECTED ERROR ---\n{exc}")


def cli():
    """Command-line interface for refactored Circuitron."""
    req = input("Enter design request: ")
    asyncio.run(agent_pipeline(req))


if __name__ == "__main__":
    cli()
