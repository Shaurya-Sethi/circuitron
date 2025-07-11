"""Custom guardrails for Circuitron."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail
import httpx
import openai


class PCBQueryOutput(BaseModel):
    """Output schema for :func:`pcb_query_guardrail`."""

    is_relevant: bool
    reasoning: str


# Cheap model used to triage queries before running expensive agents
_QUERY_MODEL = "gpt-4.1-nano"

pcb_query_agent = Agent(
    name="PCB Query Check",
    instructions="Determine if the user's request is related to electrical or PCB design.",
    model=_QUERY_MODEL,
    output_type=PCBQueryOutput,
)


@input_guardrail
async def pcb_query_guardrail(ctx: Any, agent: Any, input_data: Any) -> GuardrailFunctionOutput:
    """Refuse processing if the user query is not PCB related."""
    try:
        result = await Runner.run(pcb_query_agent, input_data, context=ctx.context)
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        print(f"Network error: {exc}")
        raise RuntimeError("Network connection issue") from exc

    output = result.final_output_as(PCBQueryOutput)
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_relevant,
    )


__all__ = ["pcb_query_guardrail"]
