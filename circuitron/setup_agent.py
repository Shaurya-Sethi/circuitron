"""Setup Agent definition for knowledge base initialization.

Creates an isolated agent that connects to its own MCP server instance and
invokes MCP tools to populate Supabase (docs) and Neo4j (knowledge graph).
"""

from __future__ import annotations

from agents import Agent
from agents.model_settings import ModelSettings

from .config import settings
from .prompts import SETUP_AGENT_PROMPT
from .models import SetupOutput
from .tools import create_mcp_server


def _tool_choice_for_mcp(model: str) -> str:
    """Return appropriate tool_choice for MCP tools based on the model.

    Mirrors the behavior used elsewhere: allow 'auto' for o4-mini, otherwise
    require explicit tool usage for determinism.
    """

    return "auto" if model == "o4-mini" else "required"


def create_setup_agent() -> tuple[Agent, object]:
    """Create and configure the Setup Agent and its dedicated MCP server.

    Returns:
        (agent, server): The configured Agent and a fresh MCP server instance.

    Notes:
        The caller is responsible for connecting and cleaning up the server.
    """

    model_settings = ModelSettings(tool_choice=_tool_choice_for_mcp(settings.documentation_model))

    # Use a dedicated MCP server for the setup flow to keep it isolated
    server = create_mcp_server()
    agent = Agent(
        name="Circuitron-Setup",
        instructions=SETUP_AGENT_PROMPT,
        model=settings.documentation_model,
        output_type=SetupOutput,
        mcp_servers=[server],
        model_settings=model_settings,
    )
    return agent, server


def get_setup_agent() -> tuple[Agent, object]:
    """Return a new Setup Agent and its MCP server instance."""

    return create_setup_agent()


__all__ = ["create_setup_agent", "get_setup_agent"]

