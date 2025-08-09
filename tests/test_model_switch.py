from types import SimpleNamespace

import importlib
import pytest


def test_settings_set_all_models() -> None:
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.set_all_models("gpt-5-mini")
    assert cfg.settings.planning_model == "gpt-5-mini"
    assert cfg.settings.plan_edit_model == "gpt-5-mini"
    assert cfg.settings.part_finder_model == "gpt-5-mini"
    assert cfg.settings.part_selection_model == "gpt-5-mini"
    assert cfg.settings.documentation_model == "gpt-5-mini"
    assert cfg.settings.code_generation_model == "gpt-5-mini"
    assert cfg.settings.code_validation_model == "gpt-5-mini"
    assert cfg.settings.code_correction_model == "gpt-5-mini"
    assert cfg.settings.erc_handling_model == "gpt-5-mini"
    assert cfg.settings.runtime_correction_model == "gpt-5-mini"


def test_ui_model_command_updates_settings_and_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    import circuitron.config as cfg

    # Fresh environment and reset models to default
    cfg.setup_environment()
    cfg.settings.set_all_models("o4-mini")

    # Build a TerminalUI with a fake console and patched input behavior
    from circuitron.ui.app import TerminalUI

    printed: list[str] = []

    class FakeConsole:
        def print(self, msg: str, *args, **kwargs) -> None:  # noqa: D401 - test helper
            printed.append(str(msg))

    ui = TerminalUI(console=FakeConsole())

    # First user enters /model, then selects gpt-5-mini, then provides the real prompt
    inputs = iter(["/model", "gpt-5-mini", "design a board"])
    # Accept kwargs so production code can pass completer=...
    monkeypatch.setattr(ui.input_box, "ask", lambda _msg, **_kw: next(inputs))

    result = ui.prompt_user("Enter prompt:")
    assert result == "design a board"

    # Settings should reflect the new model everywhere
    for name in (
        "planning_model",
        "plan_edit_model",
        "part_finder_model",
        "part_selection_model",
        "documentation_model",
        "code_generation_model",
        "code_validation_model",
        "code_correction_model",
        "erc_handling_model",
        "runtime_correction_model",
    ):
        assert getattr(cfg.settings, name) == "gpt-5-mini"

    # Confirmation message printed
    assert any("Active model set to gpt-5-mini" in m for m in printed)

    # Subsequent agent creation should use the updated model
    import sys
    sys.modules.pop("circuitron.agents", None)
    mod = importlib.import_module("circuitron.agents")
    assert mod.get_code_generation_agent().model == "gpt-5-mini"

