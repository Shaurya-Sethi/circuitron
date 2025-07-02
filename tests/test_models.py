import pytest

from circuitron.models import (
    PlanOutput,
    PlanEditDecision,
    PlanEditorOutput,
    DocumentationOutput,
)


def test_plan_editor_output_edit():
    plan = PlanOutput()
    decision = PlanEditDecision(action="edit_plan", reasoning="ok")
    result = PlanEditorOutput(decision=decision, updated_plan=plan)
    assert result.updated_plan is plan


def test_plan_editor_output_edit_missing_plan():
    decision = PlanEditDecision(action="edit_plan", reasoning="bad")
    with pytest.raises(ValueError):
        PlanEditorOutput(decision=decision)


def test_plan_editor_output_regenerate():
    decision = PlanEditDecision(action="regenerate_plan", reasoning="redo")
    result = PlanEditorOutput(decision=decision, reconstructed_prompt="new")
    assert result.reconstructed_prompt == "new"


def test_documentation_output():
    out = DocumentationOutput(
        research_queries=["q"],
        documentation_findings=["f"],
        implementation_readiness="ready",
    )
    assert out.implementation_readiness == "ready"
