import pytest

from circuitron.models import (
    PlanOutput,
    PlanEditDecision,
    PlanEditorOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    ValidationIssue,
    HallucinationReport,
    ValidationSummary,
    AnalysisMetadata,
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
    summary = ValidationSummary(
        total_validations=1,
        valid_count=1,
        invalid_count=0,
        uncertain_count=0,
        not_found_count=0,
        hallucination_rate=0.0,
    )
    meta = AnalysisMetadata(
        total_imports=1,
        total_classes=0,
        total_methods=0,
        total_attributes=0,
        total_functions=0,
    )
    report = HallucinationReport(
        success=True,
        script_path="x.py",
        overall_confidence=0.9,
        validation_summary=summary,
        hallucinations_detected=False,
        recommendations=[],
        analysis_metadata=meta,
        libraries_analyzed=[],
    )
    out = CodeValidationOutput(
        status="pass",
        summary="ok",
        issues=[issue],
        hallucination_report=report,
    )
    assert out.status == "pass"
    assert out.issues[0].category == "syntax"
