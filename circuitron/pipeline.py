"""Circuitron orchestration pipeline.

This module wires together the planner, plan editor and part finder agents.
It also exposes a simple CLI for running the pipeline from the command line.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import cast

from agents import Runner

from circuitron.agents import (
    planner,
    plan_editor,
    part_finder,
    part_selector,
    documentation,
    code_generator,
    code_validator,
    code_corrector,
)
from agents.result import RunResult
from circuitron.models import (
    PlanOutput,
    UserFeedback,
    PlanEditorOutput,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
    CodeCorrectionOutput,
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
    format_code_generation_input,
    format_code_validation_input,
    format_code_correction_input,
    write_temp_skidl_script,
    pretty_print_validation,
    pretty_print_generated_code,
    validate_code_generation_results,
)
from circuitron.tools import run_erc


async def run_planner(prompt: str) -> RunResult:
    """Run the planning agent and return the run result."""
    return await Runner.run(planner, prompt)


async def run_plan_editor(
    original_prompt: str, plan: PlanOutput, feedback: UserFeedback
) -> PlanEditorOutput:
    """Run the PlanEditor agent with formatted input."""
    input_msg = format_plan_edit_input(original_prompt, plan, feedback)
    result = await Runner.run(plan_editor, input_msg)
    return cast(PlanEditorOutput, result.final_output)


async def run_part_finder(plan: PlanOutput) -> PartFinderOutput:
    """Search KiCad libraries for components from the plan."""
    query_text = "\n".join(plan.component_search_queries)
    result = await Runner.run(part_finder, query_text)
    return cast(PartFinderOutput, result.final_output)


async def run_part_selector(
    plan: PlanOutput, part_output: PartFinderOutput
) -> PartSelectionOutput:
    """Select optimal parts using search results."""
    input_msg = format_part_selection_input(plan, part_output)
    result = await Runner.run(part_selector, input_msg)
    return cast(PartSelectionOutput, result.final_output)


async def run_documentation(
    plan: PlanOutput, selection: PartSelectionOutput
) -> DocumentationOutput:
    """Gather SKiDL documentation based on plan and selected parts."""
    input_msg = format_documentation_input(plan, selection)
    result = await Runner.run(documentation, input_msg)
    return cast(DocumentationOutput, result.final_output)


async def run_code_generation(
    plan: PlanOutput, selection: PartSelectionOutput, docs: DocumentationOutput
) -> CodeGenerationOutput:
    """Generate SKiDL code using plan, selected parts, and documentation."""
    input_msg = format_code_generation_input(plan, selection, docs)
    result = await Runner.run(code_generator, input_msg)
    code_output = cast(CodeGenerationOutput, result.final_output)
    pretty_print_generated_code(code_output)
    validate_code_generation_results(code_output)
    return code_output


async def run_code_validation(
    code_output: CodeGenerationOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
) -> tuple[CodeValidationOutput, dict[str, object] | None]:
    """Validate generated code and optionally run ERC."""

    script_path = write_temp_skidl_script(code_output.complete_skidl_code)
    try:
        input_msg = format_code_validation_input(script_path, selection, docs)
        result = await Runner.run(code_validator, input_msg)
        validation = cast(CodeValidationOutput, result.final_output)
        pretty_print_validation(validation)
        erc_result: dict[str, object] | None = None
        if validation.status == "pass":
            erc_json = await run_erc(script_path)  # type: ignore[operator]
            try:
                erc_result = json.loads(erc_json)
            except Exception:
                erc_result = {"success": False, "stderr": erc_json}
            print("\n=== ERC RESULT ===")
            print(erc_result)
        return validation, erc_result
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass


async def run_code_correction(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    erc_result: dict[str, object] | None = None,
) -> CodeGenerationOutput:
    """Run the Code Correction agent and return updated code."""

    script_path = write_temp_skidl_script(code_output.complete_skidl_code)
    try:
        input_msg = format_code_correction_input(script_path, validation, erc_result)
        result = await Runner.run(code_corrector, input_msg)
        correction = cast(CodeCorrectionOutput, result.final_output)
        code_output.complete_skidl_code = correction.corrected_code
        return code_output
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass


def validate_edit_result(edit_result: PlanEditorOutput) -> None:
    """Ensure ``PlanEditorOutput`` contains required fields.

    Args:
        edit_result: Output returned from the PlanEditor agent.

    Raises:
        ValueError: If required fields are missing based on the decision action.
    """
    action = edit_result.decision.action
    if action == "edit_plan" and edit_result.updated_plan is None:
        raise ValueError(
            "PlanEditor output missing updated_plan for action 'edit_plan'",
        )
    if action == "regenerate_plan" and edit_result.reconstructed_prompt is None:
        raise ValueError(
            "PlanEditor output missing reconstructed_prompt for action 'regenerate_plan'",
        )


async def pipeline(
    prompt: str, show_reasoning: bool = False, debug: bool = False
) -> CodeGenerationOutput:
    """Execute planning, plan editing and part search flow.

    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.
        debug: Print calculation code when ``True``.

    Returns:
        The :class:`CodeGenerationOutput` generated from the pipeline.

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
        code_out = await run_code_generation(plan, selection, docs)
        validation, erc_result = await run_code_validation(code_out, selection, docs)
        attempts = 0
        while validation.status == "fail" or (erc_result and not erc_result.get("erc_passed", False)):
            code_out = await run_code_correction(code_out, validation, erc_result)
            validation, erc_result = await run_code_validation(code_out, selection, docs)
            attempts += 1
            if attempts >= 3:
                break
        return code_out

    edit_result = await run_plan_editor(prompt, plan, feedback)
    validate_edit_result(edit_result)

    if edit_result.decision.action == "edit_plan":
        pretty_print_edited_plan(edit_result)
        final_plan = cast(PlanOutput, edit_result.updated_plan)
        part_output = await run_part_finder(final_plan)
        pretty_print_found_parts(part_output.found_components_json)
        selection = await run_part_selector(final_plan, part_output)
        pretty_print_selected_parts(selection)
        docs = await run_documentation(final_plan, selection)
        pretty_print_documentation(docs)
        code_out = await run_code_generation(final_plan, selection, docs)
        validation, erc_result = await run_code_validation(code_out, selection, docs)
        attempts = 0
        while validation.status == "fail" or (erc_result and not erc_result.get("erc_passed", False)):
            code_out = await run_code_correction(code_out, validation, erc_result)
            validation, erc_result = await run_code_validation(code_out, selection, docs)
            attempts += 1
            if attempts >= 3:
                break
        return code_out

    pretty_print_regeneration_prompt(edit_result)
    regen_prompt = cast(str, edit_result.reconstructed_prompt)
    regen_result = await run_planner(regen_prompt)
    new_plan = regen_result.final_output
    pretty_print_plan(new_plan)
    part_output = await run_part_finder(new_plan)
    pretty_print_found_parts(part_output.found_components_json)
    selection = await run_part_selector(new_plan, part_output)
    pretty_print_selected_parts(selection)
    docs = await run_documentation(new_plan, selection)
    pretty_print_documentation(docs)
    code_out = await run_code_generation(new_plan, selection, docs)
    validation, erc_result = await run_code_validation(code_out, selection, docs)
    attempts = 0
    while validation.status == "fail" or (erc_result and not erc_result.get("erc_passed", False)):
        code_out = await run_code_correction(code_out, validation, erc_result)
        validation, erc_result = await run_code_validation(code_out, selection, docs)
        attempts += 1
        if attempts >= 3:
            break
    return code_out


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
