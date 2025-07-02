"""Circuitron orchestration pipeline.

This module wires together the planner, plan editor and part finder agents.
It also exposes a simple CLI for running the pipeline from the command line.
"""
from __future__ import annotations

import argparse
import asyncio

from agents import Runner

from circuitron.agents import (
    planner,
    plan_editor,
    part_finder,
    part_selector,
    documentation,
)
from agents.result import RunResult
from circuitron.models import (
    PlanOutput,
    UserFeedback,
    PlanEditorOutput,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
)
from circuitron.utils import (
    pretty_print_plan,
    pretty_print_edited_plan,
    pretty_print_regeneration_prompt,
    pretty_print_found_parts,
    extract_reasoning_summary,
    pretty_print_selected_parts,
    pretty_print_documentation,
    collect_user_feedback,
    format_plan_edit_input,
    format_part_selection_input,
    format_documentation_input,
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


async def run_part_finder(plan: PlanOutput) -> PartFinderOutput:
    """Search KiCad libraries for components from the plan."""
    query_text = "\n".join(plan.component_search_queries)
    result = await Runner.run(part_finder, query_text)
    return result.final_output


async def run_part_selector(
    plan: PlanOutput, part_output: PartFinderOutput
) -> PartSelectionOutput:
    """Select optimal parts using search results."""
    input_msg = format_part_selection_input(plan, part_output)
    result = await Runner.run(part_selector, input_msg)
    return result.final_output


async def run_documentation(
    plan: PlanOutput, selection: PartSelectionOutput
) -> DocumentationOutput:
    """Gather SKiDL documentation based on plan and selected parts."""
    input_msg = format_documentation_input(plan, selection)
    result = await Runner.run(documentation, input_msg)
    return result.final_output


async def pipeline(
    prompt: str, show_reasoning: bool = False, debug: bool = False
) -> DocumentationOutput:
    """Execute planning, plan editing and part search flow.

    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.
        debug: Print calculation code when ``True``.

    Returns:
        The :class:`DocumentationOutput` gathered for code generation.

    Example:
        >>> asyncio.run(pipeline("buck converter"))
    """
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
        part_output = await run_part_finder(plan)
        pretty_print_found_parts(part_output.found_components_json)
        selection = await run_part_selector(plan, part_output)
        pretty_print_selected_parts(selection)
        docs = await run_documentation(plan, selection)
        pretty_print_documentation(docs)
        return docs

    edit_result = await run_plan_editor(prompt, plan, feedback)

    if edit_result.decision.action == "edit_plan":
        pretty_print_edited_plan(edit_result)
        assert edit_result.updated_plan is not None
        final_plan = edit_result.updated_plan
        part_output = await run_part_finder(final_plan)
        pretty_print_found_parts(part_output.found_components_json)
        selection = await run_part_selector(final_plan, part_output)
        pretty_print_selected_parts(selection)
        docs = await run_documentation(final_plan, selection)
        pretty_print_documentation(docs)
        return docs

    pretty_print_regeneration_prompt(edit_result)
    assert edit_result.reconstructed_prompt is not None
    regen_result = await run_planner(edit_result.reconstructed_prompt)
    new_plan = regen_result.final_output
    pretty_print_plan(new_plan)
    part_output = await run_part_finder(new_plan)
    pretty_print_found_parts(part_output.found_components_json)
    selection = await run_part_selector(new_plan, part_output)
    pretty_print_selected_parts(selection)
    docs = await run_documentation(new_plan, selection)
    pretty_print_documentation(docs)
    return docs


async def main() -> None:
    """CLI entry point for the Circuitron pipeline."""
    args = parse_args()
    prompt = args.prompt or input("Prompt: ")
    await pipeline(prompt, show_reasoning=args.reasoning, debug=args.debug)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Example:
        >>> args = parse_args(["prompt text", "-r"])
    """
    parser = argparse.ArgumentParser(description="Run the Circuitron pipeline")
    parser.add_argument("prompt", nargs="?", help="Design prompt")
    parser.add_argument("-r", "--reasoning", action="store_true", help="show reasoning summary")
    parser.add_argument("-d", "--debug", action="store_true", help="show debug info")
    return parser.parse_args(argv)


if __name__ == "__main__":
    asyncio.run(main())
