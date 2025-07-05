"""Prototype implementation for Circuitron."""

import asyncio
import subprocess
import sys
import textwrap
from typing import List

import logfire
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

from agents import Agent, Runner, function_tool
from agents.model_settings import ModelSettings, Reasoning  # type: ignore[attr-defined]
from agents.result import RunResult
from circuitron.utils import extract_reasoning_summary, pretty_print_plan

load_dotenv()
logfire.configure()
logfire.instrument_openai_agents()

# ---------- Planning Agent Prompt ----------
PLAN_PROMPT = """You are Circuitron-Planner, an expert PCB designer.

Analyze the user's requirements and create a comprehensive design solution.
Before everything, provide a concise **Design Rationale** that explains your overarching goals, trade-offs, and key performance targets in plain English.

Your analysis should include:
0. **Design Rationale**  
   - One to three bullet points summarizing “why” you’ve chosen this architecture, key constraints, and performance targets.
1. **Schematic Overview**: Break down the design into high-level functional blocks
   - For each block, include a one-line purpose (e.g., “Power Supply Decoupling – to filter RF noise and stabilize the LM324 rails”).
2. **Calculations**: Document all design assumptions, equations, and derivations if any.
   - **Design Equations**: Present electrical equations and derivations in standard engineering notation (e.g., "V_out = V_in × (R2/(R1+R2))", "P_dissipated = I² × R", "f_cutoff = 1/(2πRC)") with clear variable definitions and units.
   - **Executable Code**: For each equation that requires numerical computation, also provide clear, executable Python code using only standard math libraries (e.g., `v_out = v_in * (r2/(r1+r2)); print(f"V_out = {v_out:.2f}V")`).
   - When a result is needed, **write code to perform the calculation** and request that it be executed using the provided calculation tool - `execute_calculation` to obtain accurate values.
   - Once the tool responds, **take its result value** and add it to your final `calculation_results` list, *in the same order* as your `calculation_codes`, and **provide a short explanation for each result**.
3. **Actions**: List specific implementation steps in order
4. **Component Search**: Identify and list all components needed for the design.
5. **Implementation Notes**: Provide SKiDL-specific guidance for later stages
6. **Limitations**: Note any missing specifications or open questions

For component search queries, use SKiDL keyword style:
- Generic part types with specifications
- No numeric values for passives, keep model names for ICs  
- Examples: "opamp lm324 quad", "capacitor ceramic", "mosfet n-channel"

Focus on creating a complete, actionable plan that later agents can execute. **When calculations are required, always write them as code, not as internal reasoning or estimates.**
"""

# =================================================================================

# Pydantic BaseModels for structured outputs in the Circuitron pipeline.
# This module defines all the BaseModels required for getting structured outputs
# from each agent in the pipeline, following OpenAI Agents SDK patterns.


class PlanOutput(BaseModel):
    """Complete output from the Planning Agent."""
    model_config = ConfigDict(extra="forbid")
    design_rationale: List[str] = Field(
        default_factory=list, 
        description="High-level bullet points explaining the overarching goals, trade-offs, and key performance targets for the chosen architecture."
    )
    functional_blocks: List[str] = Field(
        default_factory=list, 
        description="High-level functional blocks of the design, each with a one-line purpose explaining its role in the circuit."
    )
    design_equations: List[str] = Field(
        default_factory=list,
        description="Electrical equations, derivations, and design assumptions explained in engineering notation (e.g., 'V_out = V_in * (R2/(R1+R2))', 'I_max = V_supply / R_load', etc.) with clear variable definitions and units."
    )
    calculation_codes: List[str] = Field(
        default_factory=list, 
        description="Executable Python code snippets for all design calculations, using only standard math libraries."
    )
    calculation_results: List[str] = Field(
        default_factory=list,
        description="The numeric outputs from each calculation, in the same order as calculation_codes, along with an explanation of the result - not just the number."
    )
    implementation_actions: List[str] = Field(
        default_factory=list, 
        description="Specific implementation steps listed in chronological order for executing the design."
    )
    component_search_queries: List[str] = Field(
        default_factory=list, 
        description="SKiDL-style component search queries for all parts needed in the design (generic types with specifications, no numeric values for passives)."
    )
    implementation_notes: List[str] = Field(
        default_factory=list, 
        description="SKiDL-specific guidance and best practices for later implementation stages."
    )
    design_limitations: List[str] = Field(
        default_factory=list, 
        description="Missing specifications, open questions, and design constraints that need to be addressed."
    )
    

class CalcResult(BaseModel):
    calculation_id: str
    success: bool
    stdout: str = ""
    stderr: str = ""

# ========== Calculation Tool ==========

@function_tool
async def execute_calculation(
    calculation_id: str,
    description: str,
    code: str,
) -> CalcResult:
    """
    Execute pure-Python maths code *generated by the LLM* in an isolated Docker container.

    Args:
        calculation_id: Correlates this request to its tool response.
        description: What this calculation is intended to compute.
        code: Python source (generated by the LLM) that prints the final value.
    Returns:
        CalcResult with stdout, stderr, and success flag.
    """
    safe_code = textwrap.dedent(code)
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "128m",
        "--pids-limit", "64",
        "python:3.12-slim",
        "python", "-c", safe_code,
    ]
    try:
        proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=15)
        return CalcResult(
            calculation_id=calculation_id,
            success=proc.returncode == 0,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except Exception as e:
        return CalcResult(
            calculation_id=calculation_id,
            success=False,
            stderr=str(e),
        )


# ---------- Planning Agent -------------



model_settings = ModelSettings(
    tool_choice="required",
    reasoning=Reasoning(effort="medium", summary="detailed"),
)

planner = Agent(
    name="Circuitron-Planner",
    instructions=PLAN_PROMPT,
    model="o4-mini",
    output_type=PlanOutput,
    tools=[execute_calculation],
    model_settings=model_settings    # <-- Pass model_settings to Agent
)

# ---------- Main execution block ----------

async def run_circuitron(prompt: str) -> RunResult:
    from circuitron.config import settings
    return await Runner.run(planner, prompt, max_turns=settings.max_turns)

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("Prompt: ")
    show_reasoning = "--reasoning" in sys.argv or "-r" in sys.argv
    
    result = asyncio.run(run_circuitron(prompt))

    # Always print the structured plan
    pretty_print_plan(result.final_output)

    if result.final_output.calculation_codes:
        print("\n=== Calculation Codes ===")
        for i, code in enumerate(result.final_output.calculation_codes, 1):
            print(f"\nCalculation #{i} code:")
            print(code)

    # Optionally show reasoning summary
    if show_reasoning:
        print("\n=== Reasoning Summary ===\n")
        print(extract_reasoning_summary(result))
