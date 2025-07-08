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
    assert mod.planner.model == "x-model"
    assert mod.plan_editor.model == "y-model"
    assert mod.part_finder.model == "z-model"
    assert mod.part_selector.model == "s-model"
    assert mod.documentation.model == "d-model"
    assert mod.code_generator.model == "c-model"


def test_partfinder_includes_footprint_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    tool_names = [tool.name for tool in mod.part_finder.tools]
    assert "search_kicad_footprints" in tool_names


def test_partselector_includes_pin_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    tool_names = [tool.name for tool in mod.part_selector.tools]
    assert "extract_pin_details" in tool_names


def test_documentation_agent_has_mcp_server() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    assert any(
        server.__class__.__name__ == "MCPServerSse"
        for server in mod.documentation.mcp_servers
    )


def test_code_generation_agent_has_mcp_server() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    assert any(
        server.__class__.__name__ == "MCPServerSse"
        for server in mod.code_generator.mcp_servers
    )


def test_code_corrector_configuration() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    assert mod.code_corrector.model == cfg.settings.code_validation_model
    tool_names = [t.name for t in mod.code_corrector.tools]
    assert "run_erc" in tool_names


def test_agents_include_kg_guide_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    validator_tools = [t.name for t in mod.code_validator.tools]
    corrector_tools = [t.name for t in mod.code_corrector.tools]
    assert "get_kg_usage_guide" in validator_tools
    assert "get_kg_usage_guide" in corrector_tools


def test_corrector_includes_erc_info_tool() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    corrector_tools = [t.name for t in mod.code_corrector.tools]
    assert "get_erc_info" in corrector_tools


def test_tool_choice_auto_for_o4mini() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    assert mod.documentation.model_settings.tool_choice == "auto"
    assert mod.code_validator.model_settings.tool_choice == "auto"
    assert mod.code_corrector.model_settings.tool_choice == "auto"


def test_tool_choice_required_for_full_model() -> None:
    import sys

    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.documentation_model = "gpt-4o"
    cfg.settings.code_validation_model = "gpt-4o"
    cfg.settings.code_generation_model = "gpt-4o"
    mod = importlib.import_module("circuitron.agents")
    assert mod.documentation.model_settings.tool_choice == "required"
    assert mod.code_validator.model_settings.tool_choice == "required"
    assert mod.code_corrector.model_settings.tool_choice == "required"
