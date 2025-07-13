import importlib
import pytest


def test_agent_models_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.planning_model = "x-model"
    cfg.settings.plan_edit_model = "y-model"
    cfg.settings.part_finder_model = "z-model"
    cfg.settings.part_selection_model = "s-model"
    cfg.settings.documentation_model = "d-model"
    cfg.settings.code_generation_model = "c-model"
    mod = importlib.import_module("circuitron.agents")
    assert mod.get_planning_agent().model == "x-model"
    assert mod.get_plan_edit_agent().model == "y-model"
    assert mod.get_partfinder_agent().model == "z-model"
    assert mod.get_partselection_agent().model == "s-model"
    assert mod.get_documentation_agent().model == "d-model"
    assert mod.get_code_generation_agent().model == "c-model"


def test_partfinder_includes_footprint_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    tool_names = [tool.name for tool in mod.get_partfinder_agent().tools]
    assert "search_kicad_footprints" in tool_names


def test_partfinder_disables_footprint_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.footprint_search_enabled = False
    mod = importlib.import_module("circuitron.agents")
    agent = mod.get_partfinder_agent()
    tool_names = [tool.name for tool in agent.tools]
    assert "search_kicad_footprints" not in tool_names
    from circuitron import prompts
    assert agent.instructions == prompts.PARTFINDER_PROMPT_NO_FOOTPRINT


def test_partselector_includes_pin_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    tool_names = [tool.name for tool in mod.get_partselection_agent().tools]
    assert "extract_pin_details" in tool_names


def test_documentation_agent_has_mcp_server() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    agent = mod.get_documentation_agent()
    assert any(
        server.__class__.__name__ == "MCPServerSse"
        for server in agent.mcp_servers
    )


def test_code_generation_agent_has_mcp_server() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    agent = mod.get_code_generation_agent()
    assert any(
        server.__class__.__name__ == "MCPServerSse"
        for server in agent.mcp_servers
    )


def test_code_corrector_configuration() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    agent = mod.get_code_correction_agent()
    assert agent.model == cfg.settings.code_correction_model
    tool_names = [t.name for t in agent.tools]
    assert "get_kg_usage_guide" in tool_names


def test_agents_include_kg_guide_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    validator_tools = [t.name for t in mod.get_code_validation_agent().tools]
    corrector_tools = [t.name for t in mod.get_code_correction_agent().tools]
    assert "get_kg_usage_guide" in validator_tools
    assert "get_kg_usage_guide" in corrector_tools


def test_erc_handler_configuration() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    handler_tools = [t.name for t in mod.get_erc_handling_agent().tools]
    assert "run_erc" in handler_tools


def test_tool_choice_auto_for_o4mini() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.code_correction_model = "o4-mini"
    mod = importlib.import_module("circuitron.agents")
    assert mod.get_documentation_agent().model_settings.tool_choice == "auto"
    assert mod.get_code_validation_agent().model_settings.tool_choice == "auto"
    assert mod.get_code_correction_agent().model_settings.tool_choice == "auto"


def test_tool_choice_required_for_full_model() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.documentation_model = "gpt-4o"
    cfg.settings.code_validation_model = "gpt-4o"
    cfg.settings.code_generation_model = "gpt-4o"
    cfg.settings.code_correction_model = "gpt-4o"
    mod = importlib.import_module("circuitron.agents")
    assert mod.get_documentation_agent().model_settings.tool_choice == "required"
    assert mod.get_code_validation_agent().model_settings.tool_choice == "required"
    assert mod.get_code_correction_agent().model_settings.tool_choice == "required"


def test_planner_has_pcb_guardrail() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    guard_names = [g.guardrail_function.__name__ for g in mod.get_planning_agent().input_guardrails]
    assert "pcb_query_guardrail" in guard_names
