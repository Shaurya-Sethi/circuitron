import importlib


def test_agent_models_from_env(monkeypatch):
    import sys
    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg
    cfg.setup_environment()
    cfg.settings.planning_model = "x-model"
    cfg.settings.plan_edit_model = "y-model"
    cfg.settings.part_finder_model = "z-model"
    mod = importlib.import_module("circuitron.agents")
    assert mod.planner.model == "x-model"
    assert mod.plan_editor.model == "y-model"
    assert mod.part_finder.model == "z-model"


def test_partfinder_includes_footprint_tool():
    import sys
    sys.modules.pop("circuitron.agents", None)
    import circuitron.config as cfg
    cfg.setup_environment()
    mod = importlib.import_module("circuitron.agents")
    tool_names = [tool.name for tool in mod.part_finder.tools]
    assert "search_kicad_footprints" in tool_names

