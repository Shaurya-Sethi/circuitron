import importlib
import os


def test_agent_models_from_env(monkeypatch):
    import sys
    sys.modules.pop("development.agents", None)
    import development.config as cfg
    cfg.settings.planning_model = "x-model"
    cfg.settings.plan_edit_model = "y-model"
    cfg.settings.part_finder_model = "z-model"
    mod = importlib.import_module("development.agents")
    assert mod.planner.model == "x-model"
    assert mod.plan_editor.model == "y-model"
    assert mod.part_finder.model == "z-model"

