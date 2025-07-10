"""Developer-facing debugging utilities."""

from __future__ import annotations

from typing import Any

import httpx
import openai
from agents.exceptions import InputGuardrailTripwireTriggered

from agents import Runner
from agents.items import MessageOutputItem, ToolCallOutputItem
from agents.result import RunResult

from .config import settings


def display_run_items(result: RunResult) -> None:
    """Print all new items from an agent run.

    Args:
        result: The :class:`RunResult` from ``Runner.run``.
    """
    for item in result.new_items:
        agent_name = getattr(item.agent, "name", "agent")
        if isinstance(item, MessageOutputItem):
            parts = []
            for part in item.raw_item.content:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
            text = "".join(parts)
            print(f"[{agent_name}] MESSAGE: {text}")
        elif isinstance(item, ToolCallOutputItem):
            print(f"[{agent_name}] TOOL OUTPUT: {item.output}")
        else:
            print(f"[{agent_name}] {item.type}")


async def run_agent(agent: Any, input_data: Any) -> RunResult:
    """Run an agent and display outputs when in dev mode.

    Args:
        agent: The agent to execute.
        input_data: The input to pass to the agent.

    Returns:
        The :class:`RunResult` from the agent run.
    """
    try:
        result = await Runner.run(agent, input_data, max_turns=settings.max_turns)
    except InputGuardrailTripwireTriggered:
        message = "Sorry, I can only assist with PCB design questions."
        print(message)
        raise RuntimeError(message)
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        print(f"Network error: {exc}")
        raise RuntimeError("Network connection issue") from exc

    if settings.dev_mode:
        display_run_items(result)
    return result
