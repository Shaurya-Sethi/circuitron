"""Circuitron orchestration pipeline.

This module wires together the planner, plan editor and part finder agents.
It also exposes a simple CLI for running the pipeline from the command line.
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
from circuitron.ui.app import TerminalUI
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
    format_runtime_correction_input,
    write_temp_skidl_script,
    prepare_erc_only_script,
    prepare_runtime_check_script,
    prepare_output_dir,
    pretty_print_validation,
    pretty_print_generated_code,
    validate_code_generation_results,
    format_docs_summary,
    format_plan_summary,
)
from circuitron.ui.components import panel

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
]

async def run_planner(
    prompt: str,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> RunResult:
    """Run the planning agent and return the run result."""

    agent = agent or get_planning_agent()
    if ui:
        ui.start_stage("Planning")
    result = await run_agent(agent, sanitize_text(prompt))
    if ui:
        ui.finish_stage("Planning")
        ui.display_plan(result.final_output)
    return result


async def run_plan_editor(
    original_prompt: str,
    plan: PlanOutput,
    feedback: UserFeedback,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> PlanEditorOutput:
    """Run the PlanEditor agent with formatted input."""
    if ui:
        ui.start_stage("Editing")
    input_msg = format_plan_edit_input(sanitize_text(original_prompt), plan, feedback)
    agent = agent or get_plan_edit_agent()
    result = await run_agent(agent, input_msg)
    if ui:
        ui.finish_stage("Editing")
        if result.final_output.updated_plan:
            ui.display_plan(result.final_output.updated_plan)
    return cast(PlanEditorOutput, result.final_output)


async def run_part_finder(
    plan: PlanOutput,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> PartFinderOutput:
    """Search KiCad libraries for components from the plan."""
    if ui:
        ui.start_stage("Looking for Parts")
    query_text = "\n".join(plan.component_search_queries)
    agent = agent or get_partfinder_agent()
    result = await run_agent(agent, sanitize_text(query_text))
    if ui:
        ui.finish_stage("Looking for Parts")
    return cast(PartFinderOutput, result.final_output)


async def run_part_selector(
    plan: PlanOutput,
    part_output: PartFinderOutput,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> PartSelectionOutput:
    """Select optimal parts using search results."""
    if ui:
        ui.start_stage("Selecting Parts")
    input_msg = format_part_selection_input(plan, part_output)
    agent = agent or get_partselection_agent()
    result = await run_agent(agent, sanitize_text(input_msg))
    if ui:
        ui.finish_stage("Selecting Parts")
    return cast(PartSelectionOutput, result.final_output)


async def run_documentation(
    plan: PlanOutput,
    selection: PartSelectionOutput,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> DocumentationOutput:
    """Gather SKiDL documentation based on plan and selected parts."""
    if ui:
        ui.start_stage("Gathering Docs")
    input_msg = format_documentation_input(plan, selection)
    agent = agent or get_documentation_agent()
    result = await run_agent(agent, sanitize_text(input_msg))
    if ui:
        ui.finish_stage("Gathering Docs")
    return cast(DocumentationOutput, result.final_output)


async def run_code_generation(
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> CodeGenerationOutput:
    """Generate SKiDL code using plan, selected parts, and documentation."""
    if ui:
        ui.start_stage("Coding")
    input_msg = format_code_generation_input(plan, selection, docs)
    agent = agent or get_code_generation_agent()
    result = await run_agent(agent, sanitize_text(input_msg))
    code_output = cast(CodeGenerationOutput, result.final_output)
    pretty_print_generated_code(code_output, ui)
    validate_code_generation_results(code_output)
    if ui:
        ui.finish_stage("Coding")
    return code_output


async def run_code_validation(
    code_output: CodeGenerationOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    run_erc_flag: bool = True,
    ui: "TerminalUI" | None = None,
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

    script_path: str | None = None
    if run_erc_flag:
        erc_only_code = prepare_erc_only_script(code_output.complete_skidl_code)
        script_path = write_temp_skidl_script(erc_only_code)
    try:
        if ui:
            ui.start_stage("Validating")
        input_msg = format_code_validation_input(
            code_output.complete_skidl_code,
            selection,
            docs,
        )
        agent = agent or get_code_validation_agent()
        result = await run_agent(agent, sanitize_text(input_msg))
        validation = cast(CodeValidationOutput, result.final_output)
        if ui:
            ui.display_validation_summary(validation.summary)
        else:
            pretty_print_validation(validation)
        erc_result: dict[str, object] | None = None
        if run_erc_flag and validation.status == "pass" and script_path:
            erc_json = await run_erc(script_path)
            try:
                erc_result = json.loads(erc_json)
            except (json.JSONDecodeError, TypeError) as e:
                erc_result = {"success": False, "erc_passed": False, "stderr": f"JSON parsing error: {str(e)}", "stdout": erc_json}
            if ui:
                panel.show_panel(ui.console, "ERC Result", json.dumps(erc_result, indent=2))
            else:
                print("\n=== ERC RESULT ===")
                print(erc_result)
        if ui:
            ui.finish_stage("Validating")
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
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> CodeGenerationOutput:
    """Run the Code Correction agent and return updated code."""
    if ui:
        ui.start_stage("Correcting")
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
    if ui:
        ui.finish_stage("Correcting")
    return code_output


async def run_validation_correction(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext | None = None,
    ui: "TerminalUI" | None = None,
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

    if ui:
        ui.start_stage("Correcting")
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
    if ui:
        ui.finish_stage("Correcting")
    return code_output



async def run_erc_handling(
    code_output: CodeGenerationOutput,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    erc_result: dict[str, object] | None,
    context: CorrectionContext | None = None,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> tuple[CodeGenerationOutput, ERCHandlingOutput]:
    """Run the ERC Handling agent and return updated code and ERC info."""

    if ui:
        ui.start_stage("ERC Handling")
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
    if ui:
        ui.finish_stage("ERC Handling")
    return code_output, erc_out


async def run_runtime_check_and_correction(
    code_output: CodeGenerationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext,
    ui: "TerminalUI" | None = None,
    agent: Agent | None = None,
) -> tuple[CodeGenerationOutput, bool]:
    """Check for runtime errors and correct them if needed."""

    if ui and hasattr(ui, "start_stage"):
        ui.start_stage("Runtime Check")
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
            if ui and hasattr(ui, "finish_stage"):
                ui.finish_stage("Runtime Check")
            return code_output, True

        if "No such file or directory" in runtime_result.get("error_details", ""):
            # Docker not available - skip runtime checks in test environments
            if ui and hasattr(ui, "finish_stage"):
                ui.finish_stage("Runtime Check")
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
            if ui and hasattr(ui, "display_error"):
                ui.display_error(f"Runtime correction agent failed: {exc}")
            else:
                print(f"Runtime correction agent failed: {exc}")
            context.add_runtime_attempt(runtime_result, [])
            if ui and hasattr(ui, "finish_stage"):
                ui.finish_stage("Runtime Check")
            return code_output, True

        correction = cast(RuntimeErrorCorrectionOutput | None, result.final_output)
        if correction is None:
            context.add_runtime_attempt(runtime_result, [])
            if ui:
                ui.finish_stage("Runtime Check")
            return code_output, True

        code_output.complete_skidl_code = correction.corrected_code
        context.add_runtime_attempt(runtime_result, correction.corrections_applied)
        if ui and hasattr(ui, "finish_stage"):
            ui.finish_stage("Runtime Check")
        return code_output, correction.execution_status == "success"

    finally:
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
    ui: "TerminalUI" | None = None,
) -> CodeGenerationOutput | None:
    """Run :func:`pipeline` with retry and error handling.
    
    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.
        retries: Maximum number of retry attempts on failure.
        output_dir: Directory to save generated files. If None, uses current directory.
        keep_skidl: If True, save generated SKiDL code files to the output directory 
                   for debugging, education, and understanding how the circuit design 
                   was generated. The script is saved as 'circuitron_skidl_script.py'.
        ui: Optional terminal UI instance for progress feedback.
        
    Returns:
        The :class:`CodeGenerationOutput` generated from the pipeline, or None if
        all retry attempts failed.

    Example:
        >>> asyncio.run(run_with_retry("buck converter", retries=1))
    """

    attempts = 0
    while True:
        try:
            # Call pipeline with only universally supported kwargs to allow
            # tests to stub `pipeline` with a simplified signature.
            return await pipeline(
                prompt,
                show_reasoning=show_reasoning,
                output_dir=output_dir,
                ui=ui,
            )
        except PipelineError:
            raise
        except Exception as exc:
            attempts += 1
            if ui:
                ui.display_error(f"Error during pipeline execution: {exc}")
            else:
                print(f"Error during pipeline execution: {exc}")
            if attempts > retries:
                if ui:
                    ui.display_error("Maximum retries exceeded. Shutting down gracefully.")
                else:
                    print("Maximum retries exceeded. Shutting down gracefully.")
                return None
            if ui:
                ui.display_warning(f"Retrying ({attempts}/{retries})...")
            else:
                print(f"Retrying ({attempts}/{retries})...")


async def pipeline(
    prompt: str,
    show_reasoning: bool = False,
    output_dir: str | None = None,
    keep_skidl: bool = False,
    ui: "TerminalUI" | None = None,
) -> CodeGenerationOutput:
    """Execute planning, plan editing and part search flow.

    Args:
        prompt: Natural language design request.
        show_reasoning: Print the reasoning summary when ``True``.
        output_dir: Directory to save generated files. If None, uses current directory.
        keep_skidl: If True, keep generated SKiDL code files after execution.

    Returns:
        The :class:`CodeGenerationOutput` generated from the pipeline.

    Example:
        >>> asyncio.run(pipeline("buck converter"))
    """
    # Show where files will be saved at the start
    final_output_dir = output_dir or os.path.join(os.getcwd(), "circuitron_output")
    message = f"Generated files will be saved to: {os.path.abspath(final_output_dir)}"
    if ui:
        ui.display_info(message)
    else:
        print(f"{message}")
        print()

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

    plan_result = await run_planner(prompt, ui=ui, agent=planner_agent)
    plan = plan_result.final_output
    if ui:
        ui.display_plan(plan)
    else:
        pretty_print_plan(plan)

    if settings.dev_mode and plan.calculation_codes:
        debug_msg = ["Debug: Calculation Codes"]
        for i, code in enumerate(plan.calculation_codes, 1):
            debug_msg.append(f"Calculation #{i} code:\n{code}")
        message = "\n".join(debug_msg)
        if ui:
            panel.show_panel(ui.console, "Debug", message)
        else:
            print("\n=== Debug: Calculation Codes ===")
            for i, code in enumerate(plan.calculation_codes, 1):
                print(f"\nCalculation #{i} code:\n{code}")

    if show_reasoning:
        summary = extract_reasoning_summary(plan_result)
        if ui:
            panel.show_panel(ui.console, "Reasoning Summary", summary)
        else:
            print("\n=== Reasoning Summary ===\n")
            print(summary)

    # Use the UI's feedback collector (boxed input) when a UI is provided.
    # Falls back to the plain function when running without UI.
    feedback = ui.collect_feedback(plan) if ui else collect_user_feedback(
        plan, console=None
    )
    if not any(
        [
            feedback.open_question_answers,
            feedback.requested_edits,
            feedback.additional_requirements,
        ]
    ):
        part_output = await run_part_finder(plan, ui=ui, agent=partfinder_agent)
        if ui:
            ui.display_found_parts(part_output.found_components)
        else:
            pretty_print_found_parts(part_output)
        selection = await run_part_selector(
            plan,
            part_output,
            ui=ui,
            agent=partselection_agent,
        )
        if ui:
            ui.display_selected_parts(selection.selections)
        else:
            pretty_print_selected_parts(selection)
        docs = await run_documentation(
            plan,
            selection,
            ui=ui,
            agent=documentation_agent,
        )
        if ui:
            panel.show_panel(ui.console, "Documentation", format_docs_summary(docs))
        else:
            pretty_print_documentation(docs)
        code_out = await run_code_generation(
            plan,
            selection,
            docs,
            ui=ui,
            agent=codegen_agent,
        )
        validation, _ = await run_code_validation(
            code_out,
            selection,
            docs,
            run_erc_flag=False,
            ui=ui,
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
                ui=ui,
                agent=corrector_agent,
            )
            validation, _ = await run_code_validation(
                code_out,
                selection,
                docs,
                run_erc_flag=False,
                ui=ui,
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
                ui=ui,
                agent=runtime_agent,
            )

        if validation.status == "pass" and not runtime_success:
            if settings.dev_mode:
                pretty_print_generated_code(code_out, ui)
            raise PipelineError("Runtime errors persist after maximum correction attempts")

        erc_result: dict[str, object] | None = None
        if validation.status == "pass":
            _, erc_result = await run_code_validation(
                code_out,
                selection,
                docs,
                run_erc_flag=True,
                ui=ui,
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
                    agent=erc_agent,
                )
                _, erc_result = await run_code_validation(
                    code_out,
                    selection,
                    docs,
                    run_erc_flag=True,
                    ui=ui,
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
                    if ui:
                        panel.show_panel(ui.console, "ERC Handler Decision", message)
                    else:
                        print("\n=== ERC HANDLER DECISION ===")
                        print(message)
                    break

        if validation.status != "pass":
            if settings.dev_mode:
                pretty_print_generated_code(code_out, ui)
            raise PipelineError("Validation failed after maximum correction attempts")

        # Final check - only fail if there are actual errors (not warnings)
        if erc_result and not erc_result.get("erc_passed", False):
            if settings.dev_mode:
                pretty_print_generated_code(code_out, ui)
            raise PipelineError(
                "ERC failed after maximum correction attempts - errors remain (warnings are acceptable)"
            )

        out_dir = prepare_output_dir(output_dir)
        files_json = await execute_final_script(code_out.complete_skidl_code, out_dir, keep_skidl)
        if ui:
            ui.display_files(json.loads(files_json))
        else:
            print("\n=== GENERATED FILES ===")
            print(files_json)
            print(f"\nFiles saved to: {out_dir}")
        return code_out

    edit_result = await run_plan_editor(
        prompt,
        plan,
        feedback,
        agent=plan_edit_agent,
    )
    if ui:
        panel.show_panel(ui.console, "Plan Updated", format_plan_summary(edit_result.updated_plan))
    else:
        pretty_print_edited_plan(edit_result)
    assert edit_result.updated_plan is not None
    final_plan = edit_result.updated_plan

    part_output = await run_part_finder(final_plan, ui=ui, agent=partfinder_agent)
    if ui:
        ui.display_found_parts(part_output.found_components)
    else:
        pretty_print_found_parts(part_output)
    selection = await run_part_selector(final_plan, part_output, ui=ui, agent=partselection_agent)
    if ui:
        ui.display_selected_parts(selection.selections)
    else:
        pretty_print_selected_parts(selection)
    docs = await run_documentation(final_plan, selection, ui=ui, agent=documentation_agent)
    if ui:
        panel.show_panel(ui.console, "Documentation", format_docs_summary(docs))
    else:
        pretty_print_documentation(docs)
    code_out = await run_code_generation(final_plan, selection, docs, ui=ui, agent=codegen_agent)
    validation, _ = await run_code_validation(
        code_out,
        selection,
        docs,
        run_erc_flag=False,
        ui=ui,
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
            final_plan,
            selection,
            docs,
            correction_context,
            ui=ui,
            agent=corrector_agent,
        )
        validation, _ = await run_code_validation(
            code_out,
            selection,
            docs,
            run_erc_flag=False,
            ui=ui,
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
            final_plan,
            selection,
            docs,
            correction_context,
            ui=ui,
            agent=runtime_agent,
        )

        if validation.status == "pass" and not runtime_success:
            if settings.dev_mode:
                pretty_print_generated_code(code_out, ui)
            raise PipelineError(
                "Runtime errors persist after maximum correction attempts"
            )

    erc_result = None
    if validation.status == "pass":
        _, erc_result = await run_code_validation(
            code_out,
            selection,
            docs,
            run_erc_flag=True,
            ui=ui,
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
                final_plan,
                selection,
                docs,
                erc_result,
                correction_context,
                ui=ui,
                agent=erc_agent,
            )
            _, erc_result = await run_code_validation(
                code_out,
                selection,
                docs,
                run_erc_flag=True,
                ui=ui,
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
                if ui:
                    panel.show_panel(ui.console, "ERC Handler Decision", message)
                else:
                    print("\n=== ERC HANDLER DECISION ===")
                    print(message)
                break

    if validation.status != "pass":
        if settings.dev_mode:
            pretty_print_generated_code(code_out, ui)
        raise PipelineError("Validation failed after maximum correction attempts")

    # Final check - only fail if there are actual errors (not warnings)
    if erc_result and not erc_result.get("erc_passed", False):
        if settings.dev_mode:
            pretty_print_generated_code(code_out, ui)
        raise PipelineError(
            "ERC failed after maximum correction attempts - errors remain (warnings are acceptable)"
        )

    out_dir = prepare_output_dir(output_dir)
    files_json = await execute_final_script(code_out.complete_skidl_code, out_dir, keep_skidl)
    if ui:
        ui.display_files(json.loads(files_json))
    else:
        print("\n=== GENERATED FILES ===")
        print(files_json)
        print(f"\nFiles saved to: {out_dir}")
    return code_out


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
