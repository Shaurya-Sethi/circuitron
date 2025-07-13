import os
from types import SimpleNamespace
from pathlib import Path
from typing import Any, cast
import pytest

from agents.items import ReasoningItem
from agents.agent import Agent
from agents.result import RunResult
from openai.types.responses.response_reasoning_item import (
    ResponseReasoningItem,
    Summary,
)

from circuitron.models import (
    CodeGenerationOutput,
    PlanOutput,
    CodeValidationOutput,
    DocumentationOutput,
    PartSelectionOutput,
    PartFinderOutput,
    PartSearchResult,
    FoundFootprint,
    PinDetail,
    SelectedPart,
    ValidationIssue,
)
from circuitron.utils import (
    extract_reasoning_summary,
    format_code_validation_input,
    format_code_correction_input,
    pretty_print_plan,
    pretty_print_edited_plan,
    pretty_print_found_parts,
    pretty_print_selected_parts,
    pretty_print_documentation,
    pretty_print_generated_code,
    format_part_selection_input,
    collect_user_feedback,
    pretty_print_validation,
    write_temp_skidl_script,
    convert_windows_path_for_docker,
)


def test_extract_reasoning_summary() -> None:
    summary = Summary(text="explain", type="summary_text")
    rr = ResponseReasoningItem(id="1", summary=[summary], type="reasoning")
    item = ReasoningItem(agent=cast(Agent[Any], SimpleNamespace()), raw_item=rr)
    result = extract_reasoning_summary(
        cast(RunResult, SimpleNamespace(new_items=[item]))
    )
    assert "explain" in result


def test_write_temp_skidl_script(tmp_path: Path) -> None:
    path = write_temp_skidl_script("print('hi')")
    assert os.path.exists(path)
    with open(path) as fh:
        content = fh.read()
    assert "print('hi')" in content
    os.remove(path)


def test_write_temp_skidl_script_unicode(tmp_path: Path) -> None:
    code = "print('\u03a9')"
    path = write_temp_skidl_script(code)
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert "\u03a9" in content
    os.remove(path)


def test_format_code_validation_and_correction_input() -> None:
    pin = PinDetail(number="1", name="VCC", function="pwr")
    part = SelectedPart(name="U1", library="lib", footprint="fp", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    docs = cast(
        DocumentationOutput,
        SimpleNamespace(
            research_queries=[],
            documentation_findings=["doc"],
            implementation_readiness="ok",
        ),
    )
    val = CodeValidationOutput(
        status="fail",
        summary="bad",
        issues=[ValidationIssue(category="err", message="m", line=1)],
    )
    text = format_code_validation_input("print('hi')", selection, docs)
    assert "print('hi')" in text and "U1" in text and "doc" in text
    corr = format_code_correction_input(
        "print('hi')",
        val,
        PlanOutput(),
        selection,
        docs,
        {"erc_passed": False},
    )
    assert "Validation Summary: bad" in corr
    assert "erc_passed" in corr


def test_format_part_selection_input_includes_footprints() -> None:
    plan = PlanOutput(component_search_queries=["R"])
    part_output = PartFinderOutput(
        found_components=[PartSearchResult(query="R")],
        found_footprints=[FoundFootprint(name="0603", library="Resistor_SMD")],
    )
    text = format_part_selection_input(plan, part_output)
    assert "found_footprints" in text


def test_pretty_print_helpers(capsys: pytest.CaptureFixture[str]) -> None:
    from circuitron.models import (
        PlanEditDecision,
        PlanEditorOutput,
        PlanOutput,
        DocumentationOutput,
    )

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
    edit = PlanEditorOutput(decision=PlanEditDecision(reasoning="r"), updated_plan=plan)
    pretty_print_edited_plan(edit)
    pretty_print_found_parts(PartFinderOutput())
    selected = PartSelectionOutput(
        selections=[
            SelectedPart(name="U1", library="lib", footprint="fp", pin_details=[])
        ]
    )
    pretty_print_selected_parts(selected)
    docs = DocumentationOutput(
        research_queries=["q"],
        documentation_findings=["doc"],
        implementation_readiness="ok",
    )
    pretty_print_documentation(docs)
    val = CodeValidationOutput(status="pass", summary="ok")
    pretty_print_generated_code(
        CodeGenerationOutput(complete_skidl_code="from skidl import *"), ui=None
    )
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


def test_get_kg_usage_guide() -> None:
    from circuitron.tools import get_kg_usage_guide
    from agents.tool_context import ToolContext
    import json
    import asyncio
    from typing import Any, Coroutine, cast

    ctx = ToolContext(context=None, tool_call_id="kg1")
    args = json.dumps({"task_type": "method"})
    guide = asyncio.run(
        cast(Coroutine[Any, Any, str], get_kg_usage_guide.on_invoke_tool(ctx, args))
    )
    assert "method" in guide and "query_knowledge_graph" in guide


def test_get_kg_usage_guide_new_categories() -> None:
    """Verify workflow, schema, and advanced guides are returned."""
    from circuitron.tools import get_kg_usage_guide
    from agents.tool_context import ToolContext
    import json
    import asyncio
    from typing import Any, Coroutine, cast

    ctx = ToolContext(context=None, tool_call_id="kg2")
    categories = {
        "workflow": "ESSENTIAL KNOWLEDGE GRAPH WORKFLOW",
        "schema": "KNOWLEDGE GRAPH SCHEMA",
        "advanced": "ADVANCED KNOWLEDGE GRAPH PATTERNS",
    }
    for name, marker in categories.items():
        args = json.dumps({"task_type": name})
        guide = asyncio.run(
            cast(Coroutine[Any, Any, str], get_kg_usage_guide.on_invoke_tool(ctx, args))
        )
        assert marker in guide
        if name != "schema":
            assert "query_knowledge_graph" in guide




def test_sanitize_text_multiline() -> None:
    from circuitron.utils import sanitize_text

    text = "hello\nworld\t!\rtest"
    cleaned = sanitize_text(text)
    assert cleaned == text


def test_sanitize_text_removes_nonprintable() -> None:
    from circuitron.utils import sanitize_text

    text = "bad\x00text"
    cleaned = sanitize_text(text)
    assert "\x00" not in cleaned


def test_prepare_erc_only_script() -> None:
    from circuitron.utils import prepare_erc_only_script

    script = "from skidl import *\ngenerate_netlist()\nERC()\n"
    result = prepare_erc_only_script(script)
    assert "# generate_netlist()" in result
    lines = [line.strip() for line in result.splitlines() if not line.strip().startswith("#")]
    assert "generate_netlist()" not in lines
    assert "ERC()" in lines


def test_convert_windows_path_for_docker() -> None:
    path = convert_windows_path_for_docker("C:\\Users\\bob")
    assert path == "/mnt/c/Users/bob"
    assert convert_windows_path_for_docker("/mnt/c/Users") == "/mnt/c/Users"
    with pytest.raises(ValueError):
        convert_windows_path_for_docker("not/a/windows/path")
