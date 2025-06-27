"""Circuitron orchestration pipeline."""
from __future__ import annotations

import asyncio
import sys

from agents import Runner

from development.agents import planner, plan_editor
from agents.result import RunResult
from development.models import PlanOutput, UserFeedback, PlanEditorOutput
from development.utils import (
    pretty_print_plan,
    pretty_print_edited_plan,
    pretty_print_regeneration_prompt,
    extract_reasoning_summary,
    collect_user_feedback,
    format_plan_edit_input,
)


async def run_planner(prompt: str) -> RunResult:
    """Run the planning agent and return the run result."""
    return await Runner.run(planner, prompt)


async def run_plan_editor(
    original_prompt: str, plan: PlanOutput, feedback: UserFeedback
) -> PlanEditorOutput:
    """Run the PlanEditor agent with formatted input."""
    input_msg = format_plan_edit_input(original_prompt, plan, feedback)
    result = await Runner.run(plan_editor, input_msg)
    return result.final_output


async def pipeline(prompt: str, show_reasoning: bool = False, debug: bool = False) -> PlanOutput:
    """Execute planning and optional plan editing flow."""
    plan_result = await run_planner(prompt)
    plan = plan_result.final_output
    pretty_print_plan(plan)

    if debug and plan.calculation_codes:
        print("\n=== Debug: Calculation Codes ===")
        for i, code in enumerate(plan.calculation_codes, 1):
            print(f"\nCalculation #{i} code:\n{code}")

    if show_reasoning:
        print("\n=== Reasoning Summary ===\n")
        print(extract_reasoning_summary(plan_result))

    feedback = collect_user_feedback(plan)
    if not any([
        feedback.open_question_answers,
        feedback.requested_edits,
        feedback.additional_requirements,
    ]):
        return plan

    edit_result = await run_plan_editor(prompt, plan, feedback)

    if edit_result.decision.action == "edit_plan":
        pretty_print_edited_plan(edit_result)
        return edit_result.updated_plan  # type: ignore[return-value]

    pretty_print_regeneration_prompt(edit_result)
    assert edit_result.reconstructed_prompt is not None
    regen_result = await run_planner(edit_result.reconstructed_prompt)
    new_plan = regen_result.final_output
    pretty_print_plan(new_plan)
    return new_plan


async def main() -> None:
    """CLI entry point for the Circuitron pipeline."""
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("Prompt: ")
    show_reasoning = "--reasoning" in sys.argv or "-r" in sys.argv
    debug = "--debug" in sys.argv or "-d" in sys.argv
    await pipeline(prompt, show_reasoning=show_reasoning, debug=debug)


if __name__ == "__main__":
    asyncio.run(main())
