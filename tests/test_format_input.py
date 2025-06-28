from circuitron.models import PlanOutput, UserFeedback
from circuitron.utils import format_plan_edit_input


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
