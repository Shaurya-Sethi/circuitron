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

from circuitron.config import settings
from .mcp_manager import mcp_manager

from circuitron.debug import run_agent


from circuitron.agents import (
    planner,
    plan_editor,
    part_finder,
    part_selector,
    documentation,
    code_generator,
    code_validator,
    code_corrector,
    erc_handler,
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
    ERCHandlingOutput,
)
from circuitron.correction_context import CorrectionContext
from circuitron.utils import (
    pretty_print_plan,
    pretty_print_edited_plan,
    pretty_print_found_parts,
    extract_reasoning_summary,
    pretty_print_selected_parts,
    pretty_print_documentation,
    collect_user_feedback,
    sanitize_text,
    format_plan_edit_input,
    format_part_selection_input,
    format_documentation_input,
    format_code_generation_input,
    format_code_validation_input,
    format_code_correction_input,
    format_code_correction_validation_input,
    format_erc_handling_input,
    write_temp_skidl_script,
    prepare_erc_only_script,
    prepare_output_dir,
    pretty_print_validation,
    pretty_print_generated_code,
    validate_code_generation_results,
)

# ``run_erc_tool`` is the FunctionTool named "run_erc" used by agents.
from circuitron.tools import run_erc
from circuitron.tools import execute_final_script


class PipelineError(RuntimeError):
    """Raised when the pipeline fails to produce valid SKiDL code."""


__all__ = [
    "run_planner",
    "run_plan_editor",
    "run_part_finder",
    "run_part_selector",
    "run_documentation",
    "run_code_generation",
    "run_code_validation",
    "run_code_correction",
    "run_validation_correction",
    "run_erc_handling",
    "run_with_retry",
    "pipeline",
    "main",
    "parse_args",
    "CorrectionContext",
    "PipelineError",
    "run_erc",
    "settings",
]

async def run_planner(prompt: str) -> RunResult:
    """Run the planning agent and return the run result."""
    return await run_agent(planner, sanitize_text(prompt))


async def run_plan_editor(
    original_prompt: str, plan: PlanOutput, feedback: UserFeedback
) -> PlanEditorOutput:
    """Run the PlanEditor agent with formatted input."""
    input_msg = format_plan_edit_input(sanitize_text(original_prompt), plan, feedback)
    result = await run_agent(plan_editor, input_msg)
    return cast(PlanEditorOutput, result.final_output)


async def run_part_finder(plan: PlanOutput) -> PartFinderOutput:
    """Search KiCad libraries for components from the plan."""
    query_text = "\n".join(plan.component_search_queries)
    result = await run_agent(part_finder, sanitize_text(query_text))
    return cast(PartFinderOutput, result.final_output)


async def run_part_selector(
    plan: PlanOutput, part_output: PartFinderOutput
) -> PartSelectionOutput:
    """Select optimal parts using search results."""
    input_msg = format_part_selection_input(plan, part_output)
    result = await run_agent(part_selector, sanitize_text(input_msg))
    return cast(PartSelectionOutput, result.final_output)


async def run_documentation(
    plan: PlanOutput, selection: PartSelectionOutput
) -> DocumentationOutput:
    """Gather SKiDL documentation based on plan and selected parts."""
    input_msg = format_documentation_input(plan, selection)
    result = await run_agent(documentation, sanitize_text(input_msg))
    return cast(DocumentationOutput, result.final_output)


async def run_code_generation(
    plan: PlanOutput, selection: PartSelectionOutput, docs: DocumentationOutput
) -> CodeGenerationOutput:
    """Generate SKiDL code using plan, selected parts, and documentation."""
    input_msg = format_code_generation_input(plan, selection, docs)
    result = await run_agent(code_generator, sanitize_text(input_msg))
    code_output = cast(CodeGenerationOutput, result.final_output)
    pretty_print_generated_code(code_output)
    validate_code_generation_results(code_output)
    return code_output


async def run_code_validation(
    code_output: CodeGenerationOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    run_erc_flag: bool = True,
) -> tuple[CodeValidationOutput, dict[str, object] | None]:
    """Validate generated code and optionally run ERC.

    Args:
        code_output: Generated SKiDL code to validate.
        selection: Component selections used in the design.
        docs: Documentation context for the validator.
        run_erc_flag: When ``True`` run ERC after validation passes.

    Returns:
        Tuple containing the :class:`CodeValidationOutput` and optional ERC
        results.
    """

    script_path: str | None = None
    if run_erc_flag:
        erc_only_code = prepare_erc_only_script(code_output.complete_skidl_code)
        script_path = write_temp_skidl_script(erc_only_code)
    try:
        input_msg = format_code_validation_input(
            code_output.complete_skidl_code, selection, docs
        )
        result = await run_agent(code_validator, sanitize_text(input_msg))
        validation = cast(CodeValidationOutput, result.final_output)
        pretty_print_validation(validation)
        erc_result: dict[str, object] | None = None
        if run_erc_flag and validation.status == "pass" and script_path:
            erc_json = await run_erc(script_path)
            try:
                erc_result = json.loads(erc_json)
            except (json.JSONDecodeError, TypeError) as e:
                erc_result = {"success": False, "erc_passed": False, "stderr": f"JSON parsing error: {str(e)}", "stdout": erc_json}
            print("\n=== ERC RESULT ===")
            print(erc_result)
        return validation, erc_result
    finally:
        if script_path:
            try:
                os.remove(script_path)
            except OSError:
                pass


async def run_code_correction(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    erc_result: dict[str, object] | None = None,
) -> CodeGenerationOutput:
    """Run the Code Correction agent and return updated code."""
    input_msg = format_code_correction_input(
        code_output.complete_skidl_code,
        validation,
        plan,
        selection,
        docs,
        erc_result,
    )
    result = await run_agent(code_corrector, sanitize_text(input_msg))
    correction = cast(CodeCorrectionOutput, result.final_output)
    code_output.complete_skidl_code = correction.corrected_code
    return code_output


async def run_validation_correction(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext | None = None,
) -> CodeGenerationOutput:
    """Run code correction to address validation errors only.

    Args:
        code_output: Current code to fix.
        validation: Validation output describing errors.
        plan: The original design plan.
        selection: Chosen components for the design.
        docs: Documentation context.

    Returns:
        Updated :class:`CodeGenerationOutput` with attempted fixes applied.
    """

    input_msg = format_code_correction_validation_input(
        code_output.complete_skidl_code,
        validation,
        plan,
        selection,
        docs,
        context,
    )
    result = await run_agent(code_corrector, sanitize_text(input_msg))
    correction = cast(CodeCorrectionOutput, result.final_output)
    code_output.complete_skidl_code = correction.corrected_code
    return code_output



async def run_erc_handling(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    erc_result: dict[str, object] | None,
    context: CorrectionContext | None = None,
) -> tuple[CodeGenerationOutput, ERCHandlingOutput]:
    """Run the ERC Handling agent and return updated code and ERC info."""

    input_msg = format_erc_handling_input(
        code_output.complete_skidl_code,
        validation,
        plan,
        selection,
        docs,
        erc_result,
        context,
    )
    result = await run_agent(erc_handler, sanitize_text(input_msg))
    erc_out = cast(ERCHandlingOutput, result.final_output)
    code_output.complete_skidl_code = erc_out.final_code
    return code_output, erc_out


async def run_with_retry(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
) -> CodeGenerationOutput | None:
    """Run :func:`pipeline` with retry and error handling."""

    attempts = 0
    while True:
        try:
            return await pipeline(prompt, show_reasoning=show_reasoning)
        except Exception as exc:
            attempts += 1
            print(f"Error during pipeline execution: {exc}")
            if attempts > retries:
                print("Maximum retries exceeded. Shutting down gracefully.")
                return None
            print(f"Retrying ({attempts}/{retries})...")


async def pipeline(prompt: str, show_reasoning: bool = False) -> CodeGenerationOutput:
    """Execute planning, plan editing and part search flow.

    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.

    Returns:
        The :class:`CodeGenerationOutput` generated from the pipeline.

    Example:
        >>> asyncio.run(pipeline("buck converter"))
    """
    plan_result = await run_planner(prompt)
    plan = plan_result.final_output
    pretty_print_plan(plan)

    if settings.dev_mode and plan.calculation_codes:
        print("\n=== Debug: Calculation Codes ===")
        for i, code in enumerate(plan.calculation_codes, 1):
            print(f"\nCalculation #{i} code:\n{code}")

    if show_reasoning:
        print("\n=== Reasoning Summary ===\n")
        print(extract_reasoning_summary(plan_result))

    feedback = collect_user_feedback(plan)
    if not any(
        [
            feedback.open_question_answers,
            feedback.requested_edits,
            feedback.additional_requirements,
        ]
    ):
        part_output = await run_part_finder(plan)
        pretty_print_found_parts(part_output.found_components_json)
        selection = await run_part_selector(plan, part_output)
        pretty_print_selected_parts(selection)
        docs = await run_documentation(plan, selection)
        pretty_print_documentation(docs)
        code_out = await run_code_generation(plan, selection, docs)
        validation, _ = await run_code_validation(
            code_out, selection, docs, run_erc_flag=False
        )
        correction_context = CorrectionContext()
        correction_context.add_validation_attempt(validation, [])  # Empty list: validation doesn't need correction tracking
        validation_loop_count = 0
        while validation.status == "fail" and correction_context.should_continue_attempts():
            validation_loop_count += 1
            if validation_loop_count > 10:  # Safety net to prevent infinite loops
                raise PipelineError("Validation correction loop exceeded maximum iterations")
            code_out = await run_validation_correction(
                code_out, validation, plan, selection, docs, correction_context
            )
            validation, _ = await run_code_validation(
                code_out, selection, docs, run_erc_flag=False
            )
            correction_context.add_validation_attempt(validation, [])  # Empty list: validation doesn't need correction tracking

        erc_result: dict[str, object] | None = None
        if validation.status == "pass":
            _, erc_result = await run_code_validation(
                code_out, selection, docs, run_erc_flag=True
            )
            if erc_result is not None:
                correction_context.add_erc_attempt(erc_result, [])
            erc_loop_count = 0
            # Run ERC handler if there are errors OR warnings (errors block, warnings should be addressed)
            while (
                erc_result
                and (not erc_result.get("erc_passed", False) or _has_erc_warnings(erc_result))
                and correction_context.should_continue_attempts()
                and not correction_context.has_no_issues()  # Stop if no errors and no warnings
                and not correction_context.agent_approved_warnings()
            ):
                erc_loop_count += 1
                if erc_loop_count > 10:  # Safety net to prevent infinite loops
                    raise PipelineError("ERC correction loop exceeded maximum iterations")
                code_out, erc_out = await run_erc_handling(
                    code_out,
                    validation,
                    plan,
                    selection,
                    docs,
                    erc_result,
                    correction_context,
                )
                _, erc_result = await run_code_validation(
                    code_out, selection, docs, run_erc_flag=True
                )
                if erc_result is not None:
                    # Add special marker for warnings approval if agent approved them
                    if erc_out.erc_validation_status == "warnings_only" and erc_result.get("erc_passed", False):
                        corrections_with_approval = erc_out.corrections_applied + ["warnings approved by agent"]
                        correction_context.add_erc_attempt(erc_result, corrections_with_approval)
                    else:
                        correction_context.add_erc_attempt(erc_result, erc_out.corrections_applied)
                
                # If the ERC Handling agent explicitly approved remaining warnings
                # as acceptable, exit the loop to avoid further attempts.
                if correction_context.agent_approved_warnings():
                    print("\n=== ERC HANDLER DECISION ===")
                    print(f"Agent approved warnings as acceptable: {erc_out.resolution_strategy}")
                    if erc_out.remaining_warnings:
                        print("Remaining acceptable warnings:")
                        for warning in erc_out.remaining_warnings:
                            print(f"  - {warning}")
                    break

        if validation.status != "pass":
            if settings.dev_mode:
                pretty_print_generated_code(code_out)
            raise PipelineError("Validation failed after maximum correction attempts")

        # Final check - only fail if there are actual errors (not warnings)
        if erc_result and not erc_result.get("erc_passed", False):
            if settings.dev_mode:
                pretty_print_generated_code(code_out)
            raise PipelineError("ERC failed after maximum correction attempts - errors remain (warnings are acceptable)")

        out_dir = prepare_output_dir()
        files_json = await execute_final_script(code_out.complete_skidl_code, out_dir)
        print("\n=== GENERATED FILES ===")
        print(files_json)
        return code_out

    edit_result = await run_plan_editor(prompt, plan, feedback)
    pretty_print_edited_plan(edit_result)
    assert edit_result.updated_plan is not None
    final_plan = edit_result.updated_plan

    part_output = await run_part_finder(final_plan)
    pretty_print_found_parts(part_output.found_components_json)
    selection = await run_part_selector(final_plan, part_output)
    pretty_print_selected_parts(selection)
    docs = await run_documentation(final_plan, selection)
    pretty_print_documentation(docs)
    code_out = await run_code_generation(final_plan, selection, docs)
    validation, _ = await run_code_validation(
        code_out, selection, docs, run_erc_flag=False
    )

    correction_context = CorrectionContext()
    correction_context.add_validation_attempt(validation, [])  # Empty list: validation doesn't need correction tracking
    validation_loop_count = 0
    while validation.status == "fail" and correction_context.should_continue_attempts():
        validation_loop_count += 1
        if validation_loop_count > 10:  # Safety net to prevent infinite loops
            raise PipelineError("Validation correction loop exceeded maximum iterations")
        code_out = await run_validation_correction(
            code_out, validation, final_plan, selection, docs, correction_context
        )
        validation, _ = await run_code_validation(
            code_out, selection, docs, run_erc_flag=False
        )
        correction_context.add_validation_attempt(validation, [])  # Empty list: validation doesn't need correction tracking

    erc_result = None
    if validation.status == "pass":
        _, erc_result = await run_code_validation(
            code_out, selection, docs, run_erc_flag=True
        )
        if erc_result is not None:
            correction_context.add_erc_attempt(erc_result, [])
        erc_loop_count = 0
        # Run ERC handler if there are errors OR warnings (errors block, warnings should be addressed)
        while (
            erc_result
            and (not erc_result.get("erc_passed", False) or _has_erc_warnings(erc_result))
            and correction_context.should_continue_attempts()
            and not correction_context.has_no_issues()  # Stop if no errors and no warnings
            and not correction_context.agent_approved_warnings()
        ):
            erc_loop_count += 1
            if erc_loop_count > 10:  # Safety net to prevent infinite loops
                raise PipelineError("ERC correction loop exceeded maximum iterations")
            code_out, erc_out = await run_erc_handling(
                code_out,
                validation,
                final_plan,
                selection,
                docs,
                erc_result,
                correction_context,
            )
            _, erc_result = await run_code_validation(
                code_out, selection, docs, run_erc_flag=True
            )
            if erc_result is not None:
                # Add special marker for warnings approval if agent approved them
                if erc_out.erc_validation_status == "warnings_only" and erc_result.get("erc_passed", False):
                    corrections_with_approval = erc_out.corrections_applied + ["warnings approved by agent"]
                    correction_context.add_erc_attempt(erc_result, corrections_with_approval)
                else:
                    correction_context.add_erc_attempt(erc_result, erc_out.corrections_applied)
                
            # If the ERC Handling agent explicitly approved remaining warnings
            # as acceptable, exit the loop to avoid further attempts.
            if correction_context.agent_approved_warnings():
                print("\n=== ERC HANDLER DECISION ===")
                print(f"Agent approved warnings as acceptable: {erc_out.resolution_strategy}")
                if erc_out.remaining_warnings:
                    print("Remaining acceptable warnings:")
                    for warning in erc_out.remaining_warnings:
                        print(f"  - {warning}")
                break

    if validation.status != "pass":
        if settings.dev_mode:
            pretty_print_generated_code(code_out)
        raise PipelineError("Validation failed after maximum correction attempts")

    # Final check - only fail if there are actual errors (not warnings)
    if erc_result and not erc_result.get("erc_passed", False):
        if settings.dev_mode:
            pretty_print_generated_code(code_out)
        raise PipelineError("ERC failed after maximum correction attempts - errors remain (warnings are acceptable)")

    out_dir = prepare_output_dir()
    files_json = await execute_final_script(code_out.complete_skidl_code, out_dir)
    print("\n=== GENERATED FILES ===")
    print(files_json)
    return code_out


async def main() -> None:
    """CLI entry point for the Circuitron pipeline."""
    args = parse_args()
    from circuitron.config import setup_environment

    setup_environment(dev=args.dev)
    await mcp_manager.initialize()
    try:
        prompt = args.prompt or input("Prompt: ")
        await run_with_retry(
            prompt,
            show_reasoning=args.reasoning,
            retries=args.retries,
        )
    finally:
        await mcp_manager.cleanup()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Example:
        >>> args = parse_args(["prompt text", "-r", "--dev"])
    """
    parser = argparse.ArgumentParser(description="Run the Circuitron pipeline")
    parser.add_argument("prompt", nargs="?", help="Design prompt")
    parser.add_argument(
        "-r", "--reasoning", action="store_true", help="show reasoning summary"
    )
    parser.add_argument(
        "--dev", action="store_true", help="enable tracing with logfire"
    )
    parser.add_argument(
        "-n",
        "--retries",
        type=int,
        default=0,
        help="number of retries if the pipeline fails",
    )
    return parser.parse_args(argv)


def _has_erc_warnings(erc_result: dict[str, object]) -> bool:
    """Check if ERC result contains warnings."""
    import re
    stdout = str(erc_result.get("stdout", ""))
    warning_match = re.search(r'(\d+) warnings found during ERC', stdout)
    warning_count = int(warning_match.group(1)) if warning_match else 0
    return warning_count > 0


if __name__ == "__main__":
    asyncio.run(main())
