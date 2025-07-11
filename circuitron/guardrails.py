"""Custom guardrails for Circuitron."""

from __future__ import annotations

from typing import Any

import asyncio
from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail
import httpx
import openai

from .network import is_connected, classify_connection_error
from .exceptions import PipelineError
from .config import settings


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
    """Refuse processing if the user query is not PCB related.

    Args:
        ctx: The :class:`~agents.RunContextWrapper` supplied to the guardrail.
        agent: The :class:`~agents.Agent` about to run.
        input_data: The user's request or message payload.

    Returns:
        A :class:`GuardrailFunctionOutput` describing whether the query is
        relevant. ``tripwire_triggered`` is ``True`` when the query is
        unrelated to PCB design.

    Example:
        >>> await pcb_query_guardrail(ctx, agent, "Design a buck converter")
        GuardrailFunctionOutput(...)
    """
    if not is_connected():
        raise PipelineError(
            "Internet connection lost. Please check your connection and try again."
        )

    try:
        coro = Runner.run(pcb_query_agent, input_data, context=ctx.context)
        result = await asyncio.wait_for(coro, timeout=settings.network_timeout)
    except asyncio.TimeoutError as exc:
        raise PipelineError(
            f"Operation timeout: {classify_connection_error(exc)}"
        )
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        print(f"Network error: {exc}")
        if not is_connected():
            raise PipelineError(
                "Internet connection lost. Please check your connection and try again."
            ) from exc
        raise PipelineError(
            f"Network connection issue: {classify_connection_error(exc)}"
        ) from exc

    output = result.final_output_as(PCBQueryOutput)
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_relevant,
    )


__all__ = ["pcb_query_guardrail"]
