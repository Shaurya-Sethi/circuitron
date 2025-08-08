"""Circuitron orchestration pipeline.

Headless-ready orchestration that reports progress via a ProgressSink and
never blocks on interactive prompts. The CLI remains in ``cli.py``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from typing import cast
from collections.abc import Mapping

from circuitron.config import settings
from .mcp_manager import mcp_manager

from circuitron.debug import run_agent
from typing import Callable

from .progress import ProgressSink, NullProgressSink
from .network import check_internet_connection


from circuitron.agents import (
    get_planning_agent,
    get_plan_edit_agent,
    get_partfinder_agent,
    get_partselection_agent,
    get_documentation_agent,
    get_code_generation_agent,
    get_code_validation_agent,
    get_code_correction_agent,
    get_runtime_error_correction_agent,
    get_erc_handling_agent,
)
from agents import Agent
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
    RuntimeErrorCorrectionOutput,
)
from circuitron.correction_context import CorrectionContext
from circuitron.utils import (
    pretty_print_plan,
    pretty_print_edited_plan,
    pretty_print_found_parts,
    extract_reasoning_summary,
    pretty_print_selected_parts,
    pretty_print_documentation,
    sanitize_text,
    format_plan_edit_input,
    format_part_selection_input,
    format_documentation_input,
    format_code_generation_input,
    format_code_validation_input,
    format_code_correction_input,
    format_code_correction_validation_input,
    format_erc_handling_input,
    format_runtime_correction_input,
    write_temp_skidl_script,
    prepare_erc_only_script,
    prepare_runtime_check_script,
    prepare_output_dir,
    validate_code_generation_results,
    format_docs_summary,
    format_plan_summary,
)

# ``run_erc_tool`` is the FunctionTool named "run_erc" used by agents.
from circuitron.tools import run_erc
from circuitron.tools import execute_final_script
from circuitron.tools import run_runtime_check
from .exceptions import PipelineError


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
    "run_runtime_check_and_correction",
    "run_erc_handling",
    "run_with_retry",
    "pipeline",
    "main",
    "parse_args",
    "CorrectionContext",
    "PipelineError",
    "run_erc",
    "RuntimeErrorCorrectionOutput",
    "PlanOutput",
    "PlanEditorOutput",
    "PartFinderOutput",
    "PartSelectionOutput",
    "DocumentationOutput",
    "CodeGenerationOutput",
    "CodeValidationOutput",
    "CodeCorrectionOutput",
    "ERCHandlingOutput",
    "settings",
    "check_internet_connection",
]

async def run_planner(
    prompt: str,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> RunResult:
    """Run the planning agent and return the run result."""

    agent = agent or get_planning_agent()
    sink = sink or NullProgressSink()
    sink.start_stage("Planning")
    try:
        result = await run_agent(agent, sanitize_text(prompt))
        return result
    finally:
        # Ensure spinner/state resets even on exceptions
        sink.finish_stage("Planning")


async def run_plan_editor(
    original_prompt: str,
    plan: PlanOutput,
    feedback: UserFeedback,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> PlanEditorOutput:
    """Run the PlanEditor agent with formatted input."""
    sink = sink or NullProgressSink()
    sink.start_stage("Editing")
    try:
        input_msg = format_plan_edit_input(sanitize_text(original_prompt), plan, feedback)
        agent = agent or get_plan_edit_agent()
        result = await run_agent(agent, input_msg)
        if result.final_output.updated_plan:
            sink.display_plan(result.final_output.updated_plan)
        return cast(PlanEditorOutput, result.final_output)
    finally:
        sink.finish_stage("Editing")


async def run_part_finder(
    plan: PlanOutput,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> PartFinderOutput:
    """Search KiCad libraries for components from the plan."""
    sink = sink or NullProgressSink()
    sink.start_stage("Looking for Parts")
    try:
        query_text = "\n".join(plan.component_search_queries)
        agent = agent or get_partfinder_agent()
        result = await run_agent(agent, sanitize_text(query_text))
        return cast(PartFinderOutput, result.final_output)
    finally:
        sink.finish_stage("Looking for Parts")


async def run_part_selector(
    plan: PlanOutput,
    part_output: PartFinderOutput,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> PartSelectionOutput:
    """Select optimal parts using search results."""
    sink = sink or NullProgressSink()
    sink.start_stage("Selecting Parts")
    try:
        input_msg = format_part_selection_input(plan, part_output)
        agent = agent or get_partselection_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        return cast(PartSelectionOutput, result.final_output)
    finally:
        sink.finish_stage("Selecting Parts")


async def run_documentation(
    plan: PlanOutput,
    selection: PartSelectionOutput,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> DocumentationOutput:
    """Gather SKiDL documentation based on plan and selected parts."""
    sink = sink or NullProgressSink()
    sink.start_stage("Gathering Docs")
    try:
        input_msg = format_documentation_input(plan, selection)
        agent = agent or get_documentation_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        return cast(DocumentationOutput, result.final_output)
    finally:
        sink.finish_stage("Gathering Docs")


async def run_code_generation(
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> CodeGenerationOutput:
    """Generate SKiDL code using plan, selected parts, and documentation."""
    sink = sink or NullProgressSink()
    sink.start_stage("Coding")
    try:
        input_msg = format_code_generation_input(plan, selection, docs)
        agent = agent or get_code_generation_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        code_output = cast(CodeGenerationOutput, result.final_output)
        sink.display_code(code_output.complete_skidl_code)
        # Act on validation result; surface an explicit warning if basic checks fail
        is_basic_valid = validate_code_generation_results(code_output, sink)
        if not is_basic_valid:
            sink.display_warning(
                "Basic code checks failed; proceeding to full validation and correction."
            )
        return code_output
    finally:
        sink.finish_stage("Coding")


async def run_code_validation(
    code_output: CodeGenerationOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    run_erc_flag: bool = True,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
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

    sink = sink or NullProgressSink()
    script_path: str | None = None
    if run_erc_flag:
        erc_only_code = prepare_erc_only_script(code_output.complete_skidl_code)
        script_path = write_temp_skidl_script(erc_only_code)
    try:
        sink.start_stage("Validating")
        input_msg = format_code_validation_input(
            code_output.complete_skidl_code,
            selection,
            docs,
        )
        agent = agent or get_code_validation_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        validation = cast(CodeValidationOutput, result.final_output)
        sink.display_validation_summary(validation.summary)
        erc_result: dict[str, object] | None = None
        if run_erc_flag and validation.status == "pass" and script_path:
            erc_json = await run_erc(script_path)
            try:
                erc_result = json.loads(erc_json)
            except (json.JSONDecodeError, TypeError) as e:
                erc_result = {
                    "success": False,
                    "erc_passed": False,
                    "stderr": f"JSON parsing error: {str(e)}",
                    "stdout": erc_json,
                }
            sink.display_info(json.dumps(erc_result, indent=2))
        return validation, erc_result
    finally:
        # Always end the stage and clean up temp files
        sink.finish_stage("Validating")
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
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> CodeGenerationOutput:
    """Run the Code Correction agent and return updated code."""
    sink = sink or NullProgressSink()
    sink.start_stage("Correcting")
    try:
        input_msg = format_code_correction_input(
            code_output.complete_skidl_code,
            validation,
            plan,
            selection,
            docs,
            erc_result,
        )
        agent = agent or get_code_correction_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        correction = cast(CodeCorrectionOutput, result.final_output)
        code_output.complete_skidl_code = correction.corrected_code
        return code_output
    finally:
        sink.finish_stage("Correcting")


async def run_validation_correction(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext | None = None,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
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

    sink = sink or NullProgressSink()
    sink.start_stage("Correcting")
    try:
        input_msg = format_code_correction_validation_input(
            code_output.complete_skidl_code,
            validation,
            plan,
            selection,
            docs,
            context,
        )
        agent = agent or get_code_correction_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        correction = cast(CodeCorrectionOutput, result.final_output)
        code_output.complete_skidl_code = correction.corrected_code
        return code_output
    finally:
        sink.finish_stage("Correcting")



async def run_erc_handling(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    erc_result: dict[str, object] | None,
    context: CorrectionContext | None = None,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> tuple[CodeGenerationOutput, ERCHandlingOutput]:
    """Run the ERC Handling agent and return updated code and ERC info."""

    sink = sink or NullProgressSink()
    sink.start_stage("ERC Handling")
    try:
        input_msg = format_erc_handling_input(
            code_output.complete_skidl_code,
            validation,
            plan,
            selection,
            docs,
            erc_result,
            context,
        )
        agent = agent or get_erc_handling_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        erc_out = cast(ERCHandlingOutput, result.final_output)
        code_output.complete_skidl_code = erc_out.final_code
        return code_output, erc_out
    finally:
        sink.finish_stage("ERC Handling")


async def run_runtime_check_and_correction(
    code_output: CodeGenerationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext,
    sink: ProgressSink | None = None,
    agent: Agent | None = None,
) -> tuple[CodeGenerationOutput, bool]:
    """Check for runtime errors and correct them if needed."""

    sink = sink or NullProgressSink()
    sink.start_stage("Runtime Check")
    runtime_check_script = prepare_runtime_check_script(code_output.complete_skidl_code)
    script_path = write_temp_skidl_script(runtime_check_script)

    try:
        try:
            runtime_result_json = await run_runtime_check(script_path)
            runtime_result = json.loads(runtime_result_json)
        except Exception as exc:  # pragma: no cover - unexpected errors
            runtime_result = {
                "success": False,
                "error_details": str(exc),
                "stdout": "",
                "stderr": "",
            }

        if runtime_result.get("success", False):
            return code_output, True

        if "No such file or directory" in runtime_result.get("error_details", ""):
            # Docker not available - skip runtime checks in test environments
            return code_output, True

        input_msg = format_runtime_correction_input(
            code_output.complete_skidl_code,
            runtime_result,
            plan,
            selection,
            docs,
            context,
        )
        try:
            agent = agent or get_runtime_error_correction_agent()
            result = await run_agent(
                agent, sanitize_text(input_msg)
            )
        except Exception as exc:  # pragma: no cover - unexpected errors
            sink.display_error(f"Runtime correction agent failed: {exc}")
            context.add_runtime_attempt(runtime_result, [])
            return code_output, True

        correction = cast(RuntimeErrorCorrectionOutput | None, result.final_output)
        if correction is None:
            context.add_runtime_attempt(runtime_result, [])
            return code_output, True

        code_output.complete_skidl_code = correction.corrected_code
        context.add_runtime_attempt(runtime_result, correction.corrections_applied)
        return code_output, correction.execution_status == "success"

    finally:
        # Always end the stage and clean up temp files
        sink.finish_stage("Runtime Check")
        try:
            os.remove(script_path)
        except OSError:
            pass


async def run_with_retry(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
    output_dir: str | None = None,
    keep_skidl: bool = False,
    sink: ProgressSink | None = None,
    feedback_provider: Callable[[PlanOutput], UserFeedback] | None = None,
) -> CodeGenerationOutput | None:
    """Run :func:`pipeline` with retry and error handling.

    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.
        retries: Maximum number of retry attempts on failure.
        output_dir: Directory to save generated files. If None, uses current directory.
        keep_skidl: If True, save generated SKiDL code files to the output directory
            for debugging and education.
        sink: Progress sink for reporting progress/messages.
        feedback_provider: Optional callback to provide plan edits headlessly.

    Returns:
        The :class:`CodeGenerationOutput` generated from the pipeline, or ``None`` if
        all retry attempts failed.

    Example:
        >>> asyncio.run(run_with_retry("buck converter", retries=1))
    """

    import inspect
    attempts = 0
    while True:
        try:
            kwargs = {
                "show_reasoning": show_reasoning,
                "output_dir": output_dir,
                "sink": sink,
                "keep_skidl": keep_skidl,
                "feedback_provider": feedback_provider,
            }
            # Forward only the kwargs that the current pipeline callable accepts
            sig_params = set(inspect.signature(pipeline).parameters.keys())
            supported = {k: v for k, v in kwargs.items() if k in sig_params}
            return await pipeline(prompt, **supported)
        except PipelineError:
            raise
        except Exception as exc:
            attempts += 1
            (sink or NullProgressSink()).display_error(
                f"Error during pipeline execution: {exc}"
            )
            if attempts > retries:
                (sink or NullProgressSink()).display_error(
                    "Maximum retries exceeded. Shutting down gracefully."
                )
                return None
            (sink or NullProgressSink()).display_warning(
                f"Retrying ({attempts}/{retries})..."
            )


async def pipeline(
    prompt: str,
    show_reasoning: bool = False,
    output_dir: str | None = None,
    keep_skidl: bool = False,
    sink: ProgressSink | None = None,
    feedback_provider: Callable[[PlanOutput], UserFeedback] | None = None,
) -> CodeGenerationOutput:
    """Execute planning, plan editing and part search flow.

    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.
        output_dir: Directory to save generated files. If None, uses current directory.
    keep_skidl: If True, keep generated SKiDL code files after execution.
    sink: Progress sink for reporting progress/messages.
    feedback_provider: Optional callback to provide plan edits headlessly.

    Returns:
        The :class:`CodeGenerationOutput` generated from the pipeline.

    Example:
        >>> asyncio.run(pipeline("buck converter"))
    """
    # Show where files will be saved at the start
    sink = sink or NullProgressSink()
    final_output_dir = output_dir or os.path.join(os.getcwd(), "circuitron_output")
    message = f"Generated files will be saved to: {os.path.abspath(final_output_dir)}"
    sink.display_info(message)

    planner_agent = get_planning_agent()
    plan_edit_agent = get_plan_edit_agent()
    partfinder_agent = get_partfinder_agent()
    partselection_agent = get_partselection_agent()
    documentation_agent = get_documentation_agent()
    codegen_agent = get_code_generation_agent()
    validator_agent = get_code_validation_agent()
    corrector_agent = get_code_correction_agent()
    runtime_agent = get_runtime_error_correction_agent()
    erc_agent = get_erc_handling_agent()

    plan_result = await run_planner(prompt, sink=sink, agent=planner_agent)
    plan = plan_result.final_output
    # Display once at the pipeline level (remove duplicate display in run_planner)
    sink.display_plan(plan)

    if settings.dev_mode and plan.calculation_codes:
        debug_msg = ["Debug: Calculation Codes"]
        for i, code in enumerate(plan.calculation_codes, 1):
            debug_msg.append(f"Calculation #{i} code:\n{code}")
        message = "\n".join(debug_msg)
        sink.display_info(message)

    if show_reasoning:
        summary = extract_reasoning_summary(plan_result)
        sink.display_info(summary)

    # Headless by default: skip blocking prompts unless a feedback_provider is supplied
    feedback = feedback_provider(plan) if feedback_provider else UserFeedback()
    if not any(
        [
            feedback.open_question_answers,
            feedback.requested_edits,
            feedback.additional_requirements,
        ]
    ):
        part_output = await run_part_finder(plan, sink=sink, agent=partfinder_agent)
        sink.display_found_parts(part_output.found_components)
        selection = await run_part_selector(
            plan,
            part_output,
            sink=sink,
            agent=partselection_agent,
        )
        sink.display_selected_parts(selection.selections)
        docs = await run_documentation(
            plan,
            selection,
            sink=sink,
            agent=documentation_agent,
        )
        sink.display_info(format_docs_summary(docs))
        code_out = await run_code_generation(
            plan,
            selection,
            docs,
            sink=sink,
            agent=codegen_agent,
        )
        validation, _ = await run_code_validation(
            code_out,
            selection,
            docs,
            run_erc_flag=False,
            sink=sink,
            agent=validator_agent,
        )
        correction_context = CorrectionContext()
        correction_context.add_validation_attempt(validation, [])  # Empty list: validation doesn't need correction tracking
        validation_loop_count = 0
        while validation.status == "fail" and correction_context.should_continue_attempts():
            validation_loop_count += 1
            if validation_loop_count > 10:  # Safety net to prevent infinite loops
                raise PipelineError("Validation correction loop exceeded maximum iterations")
            code_out = await run_validation_correction(
                code_out,
                validation,
                plan,
                selection,
                docs,
                correction_context,
                sink=sink,
                agent=corrector_agent,
            )
            validation, _ = await run_code_validation(
                code_out,
                selection,
                docs,
                run_erc_flag=False,
                sink=sink,
                agent=validator_agent,
            )
            correction_context.add_validation_attempt(validation, [])  # Empty list: validation doesn't need correction tracking

        runtime_success = False
        runtime_loop_count = 0
        while validation.status == "pass" and not runtime_success and correction_context.should_continue_runtime_attempts():
            runtime_loop_count += 1
            if runtime_loop_count > 5:
                raise PipelineError("Runtime error correction loop exceeded maximum iterations")
            code_out, runtime_success = await run_runtime_check_and_correction(
                code_out,
                plan,
                selection,
                docs,
                correction_context,
                sink=sink,
                agent=runtime_agent,
            )

        if validation.status == "pass" and not runtime_success:
            if settings.dev_mode:
                from .utils import pretty_print_generated_code
                pretty_print_generated_code(code_out)
            raise PipelineError("Runtime errors persist after maximum correction attempts")

        erc_result: dict[str, object] | None = None
        if validation.status == "pass":
            _, erc_result = await run_code_validation(
                code_out,
                selection,
                docs,
                run_erc_flag=True,
                sink=sink,
                agent=validator_agent,
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
                    sink=sink,
                    agent=erc_agent,
                )
                _, erc_result = await run_code_validation(
                    code_out,
                    selection,
                    docs,
                    run_erc_flag=True,
                    sink=sink,
                    agent=validator_agent,
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
                    decision = f"Agent approved warnings as acceptable: {erc_out.resolution_strategy}"
                    details = "\n".join(f"  - {w}" for w in erc_out.remaining_warnings) if erc_out.remaining_warnings else ""
                    message = f"{decision}\n{details}" if details else decision
                    sink.display_info(message)
                    break

        if validation.status != "pass":
            if settings.dev_mode:
                from .utils import pretty_print_generated_code
                pretty_print_generated_code(code_out)
            raise PipelineError("Validation failed after maximum correction attempts")

        # Final check - only fail if there are actual errors (not warnings)
        if erc_result and not erc_result.get("erc_passed", False):
            if settings.dev_mode:
                from .utils import pretty_print_generated_code
                pretty_print_generated_code(code_out)
            raise PipelineError(
                "ERC failed after maximum correction attempts - errors remain (warnings are acceptable)"
            )

    out_dir = prepare_output_dir(output_dir)
    files_json = await execute_final_script(code_out.complete_skidl_code, out_dir, keep_skidl)
    sink.display_files(json.loads(files_json))
    sink.display_info(f"Files saved to: {out_dir}")
    return code_out

def collect_user_feedback(plan: PlanOutput) -> UserFeedback:
    """Backward-compatible shim used by legacy tests.

    Headless default collects no feedback. Interactive paths should supply a
    feedback_provider or use TerminalUI.collect_feedback instead.
    """
    return UserFeedback()


async def main() -> None:
    """CLI entry point for the Circuitron pipeline."""
    args = parse_args()
    from circuitron.config import setup_environment, settings

    setup_environment(dev=args.dev)
    if args.no_footprint_search:
        settings.footprint_search_enabled = False
    if not check_internet_connection():
        return
    await mcp_manager.initialize()
    try:
        prompt = args.prompt or input("What would you like me to design? ")
        try:
            await run_with_retry(
                prompt,
                show_reasoning=args.reasoning,
                retries=args.retries,
                output_dir=args.output_dir,
            )
        except PipelineError as exc:
            print(f"Fatal error: {exc}")
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
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="directory to save generated files (default: ./circuitron_output)",
    )
    parser.add_argument(
        "--no-footprint-search",
        action="store_true",
        help="disable the agent's footprint search functionality",
    )
    parser.add_argument(
        "--keep-skidl",
        action="store_true",
        help="keep generated SKiDL code files after execution",
    )
    return parser.parse_args(argv)




def _has_erc_warnings(erc_result: Mapping[str, object]) -> bool:
    """Return ``True`` if the ERC output reports any warnings."""
    stdout = str(erc_result.get("stdout", ""))
    warning_match = re.search(r"(\d+) warning[s]? found during ERC", stdout)
    warning_count = int(warning_match.group(1)) if warning_match else 0
    return warning_count > 0


if __name__ == "__main__":
    asyncio.run(main())
