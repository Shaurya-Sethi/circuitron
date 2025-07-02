import os
from pathlib import Path
from types import SimpleNamespace

from typing import Any, cast

import pytest

from agents.result import RunResult

from agents.items import ReasoningItem
from openai.types.responses.response_reasoning_item import (
    ResponseReasoningItem,
    Summary,
)

from circuitron.models import (
    CodeGenerationOutput,
    PlanOutput,
    AnalysisMetadata,
    CodeValidationOutput,
    HallucinationReport,
    PartSelectionOutput,
    PinDetail,
    SelectedPart,
    ValidationIssue,
    ValidationSummary,
    DocumentationOutput,
)
from circuitron.utils import (
    extract_reasoning_summary,
    format_code_validation_input,
    format_code_correction_input,
    pretty_print_plan,
    parse_hallucination_report,
    pretty_print_edited_plan,
    pretty_print_regeneration_prompt,
    pretty_print_found_parts,
    pretty_print_selected_parts,
    pretty_print_documentation,
    pretty_print_generated_code,
    collect_user_feedback,
    pretty_print_validation,
    write_temp_skidl_script,
)



def test_extract_reasoning_summary() -> None:
    summary = Summary(text="explain", type="summary_text")
    rr = ResponseReasoningItem(id="1", summary=[summary], type="reasoning")
    item = ReasoningItem(agent=cast(Any, SimpleNamespace()), raw_item=rr)
    result = extract_reasoning_summary(cast(RunResult, SimpleNamespace(new_items=[item])))
    assert "explain" in result



def test_write_temp_skidl_script(tmp_path: Path) -> None:
    path = write_temp_skidl_script("print('hi')")
    assert os.path.exists(path)
    with open(path) as fh:
        content = fh.read()
    assert "print('hi')" in content
    os.remove(path)


def test_parse_hallucination_report_roundtrip() -> None:
    summary = ValidationSummary(
        total_validations=1,
        valid_count=1,
        invalid_count=0,
        uncertain_count=0,
        not_found_count=0,
        hallucination_rate=0.0,
    )
    meta = AnalysisMetadata(
        total_imports=0,
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
        libraries_analyzed=["lib"],
    )
    text = report.model_dump_json()
    parsed = parse_hallucination_report(text)
    assert parsed.script_path == "x.py"
    assert parsed.validation_summary.valid_count == 1


def test_format_code_validation_and_correction_input() -> None:
    pin = PinDetail(number="1", name="VCC", function="pwr")
    part = SelectedPart(name="U1", library="lib", footprint="fp", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    docs = cast(DocumentationOutput, SimpleNamespace(documentation_findings=["doc"]))
    val = CodeValidationOutput(status="fail", summary="bad", issues=[ValidationIssue(category="err", message="m", line=1)])
    text = format_code_validation_input("/tmp/s.py", selection, docs)
    assert "s.py" in text and "U1" in text and "doc" in text
    corr = format_code_correction_input("/tmp/s.py", val, {"erc_passed": False})
    assert "Validation Summary: bad" in corr
    assert "erc_passed" in corr


def test_pretty_print_helpers(capsys: pytest.CaptureFixture[str]) -> None:
    from circuitron.models import PlanEditDecision, PlanEditorOutput, PlanOutput, DocumentationOutput
    plan = PlanOutput(
        design_rationale=["why"],
        functional_blocks=["block"],
        design_equations=[],
        implementation_actions=["do"],
        component_search_queries=["R"],
        implementation_notes=["note"],
        design_limitations=["lim"],
    )
    pretty_print_plan(plan)
    cap = capsys.readouterr().out
    assert "Design Rationale" in cap
    # edited plan
    edit = PlanEditorOutput(decision=PlanEditDecision(action="edit_plan", reasoning="r"), updated_plan=plan)
    pretty_print_edited_plan(edit)
    regen = PlanEditorOutput(decision=PlanEditDecision(action="regenerate_plan", reasoning="r"), reconstructed_prompt="new")
    pretty_print_regeneration_prompt(regen)
    pretty_print_found_parts("[]")
    selected = PartSelectionOutput(selections=[SelectedPart(name="U1", library="lib", footprint="fp", pin_details=[])])
    pretty_print_selected_parts(selected)
    docs = DocumentationOutput(research_queries=["q"], documentation_findings=["doc"], implementation_readiness="ok")
    pretty_print_documentation(docs)
    val = CodeValidationOutput(status="pass", summary="ok")
    pretty_print_generated_code(CodeGenerationOutput(complete_skidl_code="from skidl import *"))
    pretty_print_validation(val)
    out = capsys.readouterr().out
    assert "SELECTED COMPONENTS" in out

def test_collect_user_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = PlanOutput(design_limitations=["q"], component_search_queries=[])
    answers = iter(["ans", "edit1", "", "req1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    fb = collect_user_feedback(plan)
    assert fb.open_question_answers[0].startswith("Q1:")
    assert fb.requested_edits == ["edit1"]
    assert fb.additional_requirements == ["req1"]
