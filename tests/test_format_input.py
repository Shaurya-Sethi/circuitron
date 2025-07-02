from circuitron.models import PlanOutput, UserFeedback, SelectedPart, PinDetail, PartSelectionOutput
from circuitron.utils import format_plan_edit_input, format_documentation_input


def test_format_plan_edit_input_includes_sections():
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


def test_format_documentation_input_includes_parts():
    plan = PlanOutput(functional_blocks=["Block"], implementation_actions=["Do"])
    pin = PinDetail(number="1", name="VCC", function="POWER-IN")
    part = SelectedPart(name="U1", library="lib", pin_details=[pin])
    selection = PartSelectionOutput(selections=[part])
    text = format_documentation_input(plan, selection)
    assert "DOCUMENTATION CONTEXT" in text
    assert "U1 (lib)" in text
    assert "pin 1: VCC" in text
