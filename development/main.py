"""
Main entry point for the Circuitron development system.
Orchestrates the agent pipeline and handles command-line interface.
"""

import sys
import asyncio
from agents import Runner
from .config import setup_environment
from .agents import planner, plan_editor, part_finder
from .utils import (
    pretty_print_plan,
    pretty_print_edited_plan,
    pretty_print_regeneration_prompt,
    collect_user_feedback,
    format_plan_edit_input,
)
from .models import UserFeedback, PlanEditorOutput, PartFinderOutput


async def run_circuitron(prompt: str):
    """Execute the full Circuitron pipeline."""
    plan_result = await Runner.run(planner, prompt)
    plan = plan_result.final_output
    pretty_print_plan(plan)

    feedback = collect_user_feedback(plan)
    if any([
        feedback.open_question_answers,
        feedback.requested_edits,
        feedback.additional_requirements,
    ]):
        edit_input = format_plan_edit_input(prompt, plan, feedback)
        edit_result = await Runner.run(plan_editor, edit_input)
        edit_output = edit_result.final_output_as(PlanEditorOutput)
        if edit_output.decision.action == "regenerate_plan":
            assert edit_output.reconstructed_prompt is not None
            pretty_print_regeneration_prompt(edit_output)
            regen_result = await Runner.run(planner, edit_output.reconstructed_prompt)
            plan = regen_result.final_output
        else:
            pretty_print_edited_plan(edit_output)
            plan = edit_output.updated_plan or plan

    if plan.component_search_queries:
        search_input = "\n".join(plan.component_search_queries)
        part_result = await Runner.run(part_finder, search_input)
        return part_result.final_output_as(PartFinderOutput)

    return None


def main():
    """Main entry point for the Circuitron system."""
    # Parse command line arguments
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("Prompt: ")
    _ = "--reasoning" in sys.argv or "-r" in sys.argv
    _ = "--debug" in sys.argv or "-d" in sys.argv
    
    # Execute pipeline
    part_output = asyncio.run(run_circuitron(prompt))
    if part_output:
        print("\nFOUND COMPONENTS JSON:\n")
        print(part_output.found_components_json)


if __name__ == "__main__":
    main()
