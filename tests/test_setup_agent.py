from types import SimpleNamespace
from unittest.mock import patch

from circuitron.setup_agent import create_setup_agent


def test_setup_agent_uses_dedicated_mcp_server() -> None:
    sentinel = SimpleNamespace(connect=lambda: None, cleanup=lambda: None, name="x")
    with patch("circuitron.setup_agent.create_mcp_server", return_value=sentinel):
        agent, server = create_setup_agent()
    assert server is sentinel
    assert agent.mcp_servers and agent.mcp_servers[0] is sentinel


def test_setup_agent_tool_choice_auto_for_o4mini() -> None:
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.documentation_model = "o4-mini"
    agent, _ = create_setup_agent()
    assert agent.model_settings.tool_choice == "auto"

