import pytest

from circuitron.models import (
    PlanOutput,
    PlanEditDecision,
    PlanEditorOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    ValidationIssue,
    APIValidationResult,
    KnowledgeGraphValidationReport,
    CodeValidationOutput,
)


def test_plan_editor_output_edit() -> None:
    plan = PlanOutput()
    decision = PlanEditDecision(reasoning="ok")
    result = PlanEditorOutput(decision=decision, updated_plan=plan)
    assert result.updated_plan is plan


def test_plan_editor_output_edit_missing_plan() -> None:
    decision = PlanEditDecision(reasoning="bad")
    with pytest.raises(ValueError):
        PlanEditorOutput(decision=decision)


def test_documentation_output() -> None:
    out = DocumentationOutput(
        research_queries=["q"],
        documentation_findings=["f"],
        implementation_readiness="ready",
    )
    assert out.implementation_readiness == "ready"


def test_code_generation_output() -> None:
    out = CodeGenerationOutput(
        complete_skidl_code="from skidl import *\n",
        imports=["from skidl import *"],
    )
    assert "skidl" in out.complete_skidl_code


def test_code_validation_output() -> None:
    issue = ValidationIssue(line=1, category="syntax", message="bad")
    api_result = APIValidationResult(
        api_name="generate_netlist",
        api_type="function",
        target_class=None,
        line_number=1,
        is_valid=True,
        fix_suggestion=None,
    )
    report = KnowledgeGraphValidationReport(
        total_apis_checked=1,
        valid_apis=1,
        invalid_apis=0,
        confidence_score=1.0,
        validation_details=[api_result],
        skidl_insights=[],
    )
    out = CodeValidationOutput(
        status="pass",
        summary="ok",
        issues=[issue],
        kg_validation_report=report,
    )
    assert out.status == "pass"
    assert out.issues[0].category == "syntax"
