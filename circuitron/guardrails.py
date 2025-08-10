"""Custom guardrails for Circuitron."""

from __future__ import annotations

from typing import Any

import asyncio
from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail
import httpx
import openai

from .ui.app import TerminalUI

from .network import is_connected
from .exceptions import PipelineError
from .config import settings


class PCBQueryOutput(BaseModel):
    """Output schema for :func:`pcb_query_guardrail`."""

    is_relevant: bool
    reasoning: str


# Cheap model used to triage queries before running expensive agents
_QUERY_MODEL = "gpt-5-nano"

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
    try:
        coro = Runner.run(pcb_query_agent, input_data, context=ctx.context)
        result = await asyncio.wait_for(coro, timeout=settings.network_timeout)
    except asyncio.TimeoutError:
        if not is_connected(timeout=5.0):
            raise PipelineError(
                "Internet connection lost. Please check your connection and try again."
            )
        raise PipelineError(
            "Network operation timed out. Consider increasing CIRCUITRON_NETWORK_TIMEOUT."
        )
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        TerminalUI().display_error(f"Network error: {exc}")
        if not is_connected(timeout=5.0):
            raise PipelineError(
                "Internet connection lost. Please check your connection and try again."
            ) from exc
        raise PipelineError("Network connection issue") from exc

    output = result.final_output_as(PCBQueryOutput)
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_relevant,
    )


__all__ = ["pcb_query_guardrail"]
