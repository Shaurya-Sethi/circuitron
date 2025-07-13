from circuitron.models import (
    PlanOutput,
    UserFeedback,
    SelectedPart,
    PinDetail,
    PartSelectionOutput,
    DocumentationOutput,
    CodeValidationOutput,
)
from circuitron.correction_context import CorrectionContext
from circuitron.utils import (
    format_plan_edit_input,
    format_documentation_input,
    format_code_generation_input,
    format_code_validation_input,
    format_erc_handling_input,
)


def test_format_plan_edit_input_includes_sections() -> None:
    plan = PlanOutput(
        design_rationale=["Reason"],
        functional_blocks=["Block"],
        implementation_actions=["Do"],
        component_search_queries=["resistor"],
        implementation_notes=["note"],
        design_limitations=["open"],
    )
    feedback = UserFeedback(
        open_question_answers=["A"],
        requested_edits=["edit"],
    )
    text = format_plan_edit_input("prompt", plan, feedback)
    assert "PLAN EDITING REQUEST" in text
    assert "Functional Blocks:" in text
    assert "Requested Edits:" in text
    assert "Answers to Open Questions:" in text


def test_format_documentation_input_includes_parts() -> None:
    plan = PlanOutput(functional_blocks=["Block"], implementation_actions=["Do"])
    pin = PinDetail(number="1", name="VCC", function="POWER-IN")
    part = SelectedPart(name="U1", library="lib", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    text = format_documentation_input(plan, selection)
    assert "DOCUMENTATION CONTEXT" in text
    assert "U1 (lib)" in text
    assert "pin 1: VCC" in text


def test_format_code_generation_input_includes_docs() -> None:
    plan = PlanOutput(functional_blocks=["Block"], implementation_actions=["Do"])
    pin = PinDetail(number="1", name="VCC", function="POWER-IN")
    part = SelectedPart(name="U1", library="lib", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    docs = DocumentationOutput(
        research_queries=[],
        documentation_findings=["example"],
        implementation_readiness="ok",
    )
    text = format_code_generation_input(plan, selection, docs)
    assert "CODE GENERATION CONTEXT" in text
    assert "example" in text


def test_format_inputs_omit_footprints_when_disabled() -> None:
    import circuitron.config as cfg

    cfg.setup_environment()
    cfg.settings.footprint_search_enabled = False

    plan = PlanOutput()
    pin = PinDetail(number="1", name="VCC", function="POWER-IN")
    part = SelectedPart(name="U1", library="lib", footprint="SOIC", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    docs = DocumentationOutput(
        research_queries=[],
        documentation_findings=["doc"],
        implementation_readiness="ok",
    )
    gen_text = format_code_generation_input(plan, selection, docs)
    val_text = format_code_validation_input("print()", selection, docs)

    assert "SOIC" not in gen_text
    assert "SOIC" not in val_text


def test_format_erc_handling_input_provides_history() -> None:
    ctx = CorrectionContext()
    ctx.add_erc_attempt({"erc_passed": False, "stdout": "ERC ERROR: fail"}, ["c1"])
    pin = PinDetail(number="1", name="VCC", function="POWER-IN")
    part = SelectedPart(name="U1", library="lib", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    docs = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    val = CodeValidationOutput(status="pass", summary="ok")
    text = format_erc_handling_input(
        "code",
        val,
        PlanOutput(),
        selection,
        docs,
        {"erc_passed": False},
        ctx,
    )
    assert "ERC HANDLING CONTEXT" in text
    assert "Attempt 1" in text
