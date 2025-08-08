"""Utility functions for Circuitron."""

from __future__ import annotations

from typing import Callable, List, TYPE_CHECKING
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import os
import tempfile
import re
from agents.items import ReasoningItem
from agents.result import RunResult
from .models import (
    PlanOutput,
    UserFeedback,
    PlanEditorOutput,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
)
from .correction_context import CorrectionContext
from .progress import ProgressSink, NullProgressSink

if TYPE_CHECKING:
    from .ui.app import TerminalUI


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Return a cleaned version of ``text`` limited to ``max_length`` characters."""

    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
    cleaned = cleaned.replace("```", "'''")
    return cleaned.strip()[:max_length]


def convert_windows_path_for_docker(windows_path: str) -> str:
    """Return ``windows_path`` converted for Docker volume mounts.

    On Windows hosts, Docker expects Unix-style paths like ``/mnt/c/...``
    when mounting volumes into Linux containers. Paths that already look
    like Unix paths are returned unchanged.

    Args:
        windows_path: Original path using Windows notation.

    Returns:
        Unix-style path compatible with Docker volume mounts.

    Raises:
        ValueError: If ``windows_path`` does not contain a drive letter.

    Example:
        >>> convert_windows_path_for_docker('C:\\Temp')
        '/mnt/c/Temp'
    """

    if windows_path.startswith("/"):
        return windows_path

    match = re.match(r"^(?P<drive>[A-Za-z]):[\\/]*(?P<rest>.*)$", windows_path)
    if not match:
        raise ValueError(f"Invalid Windows path: {windows_path!r}")

    drive = match.group("drive").lower()
    rest = match.group("rest").replace("\\", "/")
    return f"/mnt/{drive}/{rest}"


def extract_reasoning_summary(run_result: RunResult) -> str:
    """Return the reasoning summary from a run result.

    Example:
        >>> summary = extract_reasoning_summary(result)
    """
    texts = []
    for item in run_result.new_items:
        if isinstance(item, ReasoningItem):
            # raw_item.summary is List[ResponseSummaryText]
            for chunk in item.raw_item.summary:
                if getattr(chunk, "type", None) == "summary_text":
                    texts.append(chunk.text)
    return "\n\n".join(texts).strip() or "(no summary returned)"


def print_section(
    title: str, items: List[str], bullet: str = "•", numbered: bool = False, console: Console | None = None
) -> None:
    """Display a section of text within a styled panel."""
    if not items:
        return

    console = console or Console()
    body_lines = []
    for i, item in enumerate(items):
        prefix = f"{i + 1}." if numbered else bullet
        body_lines.append(f"{prefix} {item}")
    content = "\n".join(body_lines)
    console.print(Panel(Markdown(content), title=title, expand=False))


def pretty_print_plan(plan: PlanOutput, console: Console | None = None) -> None:
    """Pretty print a structured plan output."""
    console = console or Console()
    # Section 0: Design Rationale (if provided)
    print_section("Design Rationale", plan.design_rationale, console=console)

    # Section 1: Schematic Overview
    print_section("Schematic Overview", plan.functional_blocks, console=console)

    # Section 2: Design Equations & Calculations
    if plan.design_equations:
        print_section(
            "Design Equations & Calculations", plan.design_equations, console=console
        )

        # Show calculation results if available
        if plan.calculation_results:
            print_section(
                "Calculated Values", plan.calculation_results, console=console
            )
    else:
        console.print("\nNo calculations required for this design.")

    # Section 3: Implementation Actions
    print_section(
        "Implementation Steps",
        plan.implementation_actions,
        numbered=True,
        console=console,
    )

    # Section 4: Component Search Queries
    print_section("Components to Search", plan.component_search_queries, console=console)

    # Section 5: SKiDL Notes
    print_section(
        "Implementation Notes (SKiDL)", plan.implementation_notes, console=console
    )

    # Section 6: Limitations / Open Questions
    print_section(
        "Design Limitations / Open Questions",
        plan.design_limitations,
        console=console,
    )


def collect_user_feedback(
    plan: PlanOutput,
    input_func: Callable[[str], str] | None = None,
    console: Console | None = None,
) -> UserFeedback:
    """
    Interactively collect user feedback on the design plan.
    This function prompts the user to answer open questions and request edits.
    """
    console = console or Console()
    console.print(Panel("PLAN REVIEW & FEEDBACK", border_style="cyan"))

    feedback = UserFeedback()
    input_func = input_func or input

    # Handle open questions if they exist
    if plan.design_limitations:
        console.print(
            Panel(
                f"The planner has identified {len(plan.design_limitations)} open questions that need your input:",
                border_style="cyan",
            )
        )

        for i, question in enumerate(plan.design_limitations, 1):
            console.print(Panel(f"{i}. {question}", border_style="cyan"))
            answer = sanitize_text(input_func("Answer: ").strip())
            if answer:
                feedback.open_question_answers.append(f"Q{i}: {question}\nA: {answer}")

    # Collect general edits and modifications
    console.print(Panel("OPTIONAL EDITS & MODIFICATIONS", border_style="cyan"))
    console.print(
        "Do you have any specific changes, clarifications, or modifications to request?"
    )
    console.print("(Press Enter on empty line to finish)")

    edit_counter = 1
    while True:
        edit = sanitize_text(input_func(f"Edit #{edit_counter}: ").strip())
        if not edit:
            break
        feedback.requested_edits.append(edit)
        edit_counter += 1

    # Collect additional requirements
    console.print(Panel("ADDITIONAL REQUIREMENTS", border_style="cyan"))
    console.print(
        "Are there any new requirements or constraints not captured in the original design?"
    )
    console.print("(Press Enter on empty line to finish)")

    req_counter = 1
    while True:
        req = sanitize_text(input_func(f"Additional requirement #{req_counter}: ").strip())
        if not req:
            break
        feedback.additional_requirements.append(req)
        req_counter += 1

    return feedback


def format_plan_edit_input(
    original_prompt: str, plan: PlanOutput, feedback: UserFeedback
) -> str:
    """
    Format the input for the PlanEdit Agent, combining all context.
    """
    input_parts = [
        "PLAN EDITING REQUEST",
        "=" * 50,
        "",
        "ORIGINAL USER PROMPT:",
        f'"""{original_prompt}"""',
        "",
        "GENERATED DESIGN PLAN:",
        "=" * 30,
    ]

    # Add each section of the plan
    if plan.design_rationale:
        input_parts.extend(
            ["Design Rationale:", *[f"• {item}" for item in plan.design_rationale], ""]
        )

    if plan.functional_blocks:
        input_parts.extend(
            [
                "Functional Blocks:",
                *[f"• {item}" for item in plan.functional_blocks],
                "",
            ]
        )

    if plan.design_equations:
        input_parts.extend(
            ["Design Equations:", *[f"• {item}" for item in plan.design_equations], ""]
        )

    if plan.calculation_results:
        input_parts.extend(
            [
                "Calculation Results:",
                *[f"• {item}" for item in plan.calculation_results],
                "",
            ]
        )

    if plan.implementation_actions:
        input_parts.extend(
            [
                "Implementation Actions:",
                *[
                    f"{i + 1}. {item}"
                    for i, item in enumerate(plan.implementation_actions)
                ],
                "",
            ]
        )

    if plan.component_search_queries:
        input_parts.extend(
            [
                "Component Search Queries:",
                *[f"• {item}" for item in plan.component_search_queries],
                "",
            ]
        )

    if plan.implementation_notes:
        input_parts.extend(
            [
                "Implementation Notes:",
                *[f"• {item}" for item in plan.implementation_notes],
                "",
            ]
        )

    if plan.design_limitations:
        input_parts.extend(
            [
                "Design Limitations / Open Questions:",
                *[f"• {item}" for item in plan.design_limitations],
                "",
            ]
        )

    # Add user feedback
    input_parts.extend(["USER FEEDBACK:", "=" * 30, ""])

    if feedback.open_question_answers:
        input_parts.extend(
            ["Answers to Open Questions:", *feedback.open_question_answers, ""]
        )

    if feedback.requested_edits:
        input_parts.extend(
            [
                "Requested Edits:",
                *[f"• {edit}" for edit in feedback.requested_edits],
                "",
            ]
        )

    if feedback.additional_requirements:
        input_parts.extend(
            [
                "Additional Requirements:",
                *[f"• {req}" for req in feedback.additional_requirements],
                "",
            ]
        )

    input_parts.extend(
        [
            "INSTRUCTIONS:",
            "Incorporate all feedback into a revised plan using the PlanOutput structure.",
            "Recompute affected calculations as needed and provide a concise bullet list of changes.",
        ]
    )

    return "\n".join(input_parts)


def format_part_selection_input(plan: PlanOutput, found: PartFinderOutput) -> str:
    """Format input for the Part Selection agent."""
    parts = [
        "PART SELECTION CONTEXT",
        "=" * 40,
        "",
    ]

    if plan.functional_blocks:
        parts.extend(
            ["Functional Blocks:", *[f"• {b}" for b in plan.functional_blocks], ""]
        )

    if plan.component_search_queries:
        parts.extend(
            [
                "Original Search Queries:",
                *[f"• {q}" for q in plan.component_search_queries],
                "",
            ]
        )

    from .config import settings
    import json

    found_dict = found.model_dump(exclude_none=True)
    if not settings.footprint_search_enabled:
        found_dict.pop("found_footprints", None)
    found_json = json.dumps(found_dict)
    parts.extend(["PART SEARCH RESULTS JSON:", found_json, ""])
    parts.append("Select the best components and extract pin details.")
    return "\n".join(parts)


def format_documentation_input(plan: PlanOutput, selection: PartSelectionOutput) -> str:
    """Format input for the Documentation agent."""
    parts = [
        "DOCUMENTATION CONTEXT",
        "=" * 40,
        "",
    ]
    if plan.functional_blocks:
        parts.extend(
            ["Functional Blocks:", *[f"• {b}" for b in plan.functional_blocks], ""]
        )
    if plan.implementation_actions:
        parts.extend(
            [
                "Implementation Actions:",
                *[f"{i + 1}. {a}" for i, a in enumerate(plan.implementation_actions)],
                "",
            ]
        )
    if selection.selections:
        parts.append("Selected Components:")
        for part in selection.selections:
            parts.append(f"- {part.name} ({part.library})")
            for pin in part.pin_details:
                parts.append(f"  pin {pin.number}: {pin.name} / {pin.function}")
        parts.append("")
    parts.append("Gather SKiDL documentation for these components and connections.")
    return "\n".join(parts)


def pretty_print_edited_plan(edited_output: PlanEditorOutput) -> None:
    """Pretty print an edited plan output with change summary."""
    print("\n" + "=" * 60)
    print("PLAN SUCCESSFULLY UPDATED")
    print("=" * 60)

    print(f"\nAction: {edited_output.decision.action}")
    print(f"Reasoning: {edited_output.decision.reasoning}")

    if edited_output.changes_summary:
        print("\n" + "=" * 40)
        print("SUMMARY OF CHANGES")
        print("=" * 40)
        for i, change in enumerate(edited_output.changes_summary, 1):
            print(f"{i}. {change}")

    print("\n" + "=" * 40)
    print("UPDATED DESIGN PLAN")
    print("=" * 40)
    if edited_output.updated_plan:
        pretty_print_plan(edited_output.updated_plan)


def pretty_print_found_parts(found: PartFinderOutput) -> None:
    """Display the components and footprints found by the PartFinder agent.

    Args:
        found: The :class:`PartFinderOutput` from the agent.

    Example:
        >>> pretty_print_found_parts(PartFinderOutput())
    """

    import json

    print("\n=== FOUND COMPONENTS AND FOOTPRINTS JSON ===\n")
    print(json.dumps(found.model_dump()))


def pretty_print_selected_parts(selection: PartSelectionOutput) -> None:
    """Display parts selected by the PartSelector agent."""
    if not selection.selections:
        print("\nNo parts selected.")
        return

    from .config import settings

    print("\n=== SELECTED COMPONENTS ===")
    for part in selection.selections:
        headline = f"\n{part.name} ({part.library})"
        if settings.footprint_search_enabled and part.footprint:
            headline += f" -> {part.footprint}"
        print(headline)
        if part.selection_reason:
            print(f"Reason: {part.selection_reason}")
        if part.pin_details:
            print("Pins:")
            for pin in part.pin_details:
                print(f"  {pin.number}: {pin.name} / {pin.function}")


def pretty_print_documentation(docs: DocumentationOutput) -> None:
    """Display documentation queries and findings."""
    print("\n=== DOCUMENTATION QUERIES ===")
    for q in docs.research_queries:
        print(f" • {q}")
    print("\n=== DOCUMENTATION FINDINGS ===")
    for item in docs.documentation_findings:
        print(f" • {item}")
    print(f"\nImplementation Readiness: {docs.implementation_readiness}")


def format_plan_summary(plan: PlanOutput | None) -> str:
    """Return a concise summary of the design plan.

    Args:
        plan: The :class:`PlanOutput` with design details or ``None``.

    Returns:
        Summary text describing design rationale, functional blocks and notes.
    """

    if plan is None:
        return ""

    lines: list[str] = []
    if plan.design_rationale:
        lines.append("Design Rationale:")
        lines.extend(f"- {item}" for item in plan.design_rationale)
    if plan.functional_blocks:
        lines.append("Functional Blocks:")
        lines.extend(f"- {blk}" for blk in plan.functional_blocks)
    if plan.implementation_actions:
        lines.append("Implementation Steps:")
        lines.extend(f"- {step}" for step in plan.implementation_actions)
    if plan.implementation_notes:
        lines.append("Implementation Notes:")
        lines.extend(f"- {note}" for note in plan.implementation_notes)
    if plan.design_equations:
        lines.append("Design Equations:")
        lines.extend(f"- {eq}" for eq in plan.design_equations)
    return "\n".join(lines)


def format_selection_summary(selection: PartSelectionOutput | None) -> str:
    """Return a summary of selected components.

    Args:
        selection: The :class:`PartSelectionOutput` with chosen parts.

    Returns:
        Text describing component choices and pin mappings.
    """

    if selection is None:
        return ""

    from .config import settings

    lines: list[str] = []
    for part in selection.selections:
        headline = f"- {part.name} ({part.library})"
        if settings.footprint_search_enabled and part.footprint:
            headline += f" -> {part.footprint}"
        lines.append(headline)
        for pin in part.pin_details:
            lines.append(f"  pin {pin.number}: {pin.name} / {pin.function}")
    if selection.summary:
        lines.append("Selection Rationale:")
        lines.extend(f"- {s}" for s in selection.summary)
    return "\n".join(lines)


def format_docs_summary(docs: DocumentationOutput | None) -> str:
    """Return a concise summary of documentation research.

    Args:
        docs: The :class:`DocumentationOutput` or ``None``.

    Returns:
        Short text with research queries and readiness notes.
    """

    if docs is None:
        return ""

    lines: list[str] = []
    if docs.research_queries:
        lines.append("Research Queries:")
        lines.extend(f"- {q}" for q in docs.research_queries)
    if docs.documentation_findings:
        lines.append("Key Guidance:")
        for finding in docs.documentation_findings[:5]:
            lines.append(f"- {finding}")
    lines.append(f"Implementation Readiness: {docs.implementation_readiness}")
    return "\n".join(lines)


def format_code_generation_input(
    plan: PlanOutput, selection: PartSelectionOutput, docs: DocumentationOutput
) -> str:
    """Format input for the Code Generation agent."""
    parts = [
        "CODE GENERATION CONTEXT",
        "=" * 40,
        "",
    ]
    if plan.functional_blocks:
        parts.extend(
            ["Functional Blocks:", *[f"• {b}" for b in plan.functional_blocks], ""]
        )
    if plan.implementation_actions:
        parts.extend(
            [
                "Implementation Actions:",
                *[f"{i + 1}. {a}" for i, a in enumerate(plan.implementation_actions)],
                "",
            ]
        )
    from .config import settings

    if selection.selections:
        parts.append("Selected Components:")
        for part in selection.selections:
            line = f"- {part.name} ({part.library})"
            if settings.footprint_search_enabled and part.footprint:
                line += f" -> {part.footprint}"
            parts.append(line)
            for pin in part.pin_details:
                parts.append(f"  pin {pin.number}: {pin.name} / {pin.function}")
        parts.append("")
    if docs.documentation_findings:
        parts.append("Relevant Documentation Snippets:")
        parts.extend([f"• {d}" for d in docs.documentation_findings])
        parts.append("")
    parts.append("Generate complete SKiDL code implementing the design plan.")
    return "\n".join(parts)


def format_code_validation_input(
    script_content: str, selection: PartSelectionOutput, docs: DocumentationOutput
) -> str:
    """Format input for the Code Validation agent."""

    parts = [
        "CODE VALIDATION CONTEXT",
        "=" * 40,
        "Script Content:",
        script_content,
        "",
    ]
    from .config import settings

    if selection.selections:
        parts.append("Selected Components:")
        for part in selection.selections:
            line = f"- {part.name} ({part.library})"
            if settings.footprint_search_enabled and part.footprint:
                line += f" -> {part.footprint}"
            parts.append(line)
            for pin in part.pin_details:
                parts.append(f"  pin {pin.number}: {pin.name}")
        parts.append("")
    if docs.documentation_findings:
        parts.append("Relevant Documentation Snippets:")
        parts.extend([f"• {d}" for d in docs.documentation_findings])
        parts.append("")
    parts.append("Validate the script and report any issues.")
    return "\n".join(parts)


def pretty_print_generated_code(
    code_output: CodeGenerationOutput, ui: "TerminalUI" | None = None
) -> None:
    """Display generated SKiDL code using the given UI if available."""

    if ui is not None:
        ui.display_code(code_output.complete_skidl_code)
        return

    print("\n=== GENERATED SKiDL CODE ===\n")
    print(code_output.complete_skidl_code)


def validate_code_generation_results(
    code_output: CodeGenerationOutput, sink: ProgressSink | None = None
) -> bool:
    """Basic validation of the generated code output.

    Reports issues via the provided ProgressSink (no direct printing).
    """
    sink = sink or NullProgressSink()
    required_phrases = ["from skidl import"]
    for phrase in required_phrases:
        if phrase not in code_output.complete_skidl_code:
            sink.display_warning(
                f"Expected phrase '{phrase}' not found in code"
            )
            return False
    return True


def write_temp_skidl_script(code: str) -> str:
    """Write SKiDL code to a temporary script and return its path."""

    fd, path = tempfile.mkstemp(prefix="skidl_", suffix=".py")
    # Explicitly use UTF-8 so that Unicode characters in prompts or generated
    # code do not cause cross-platform encoding issues.
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(code)
    return path


def keep_skidl_script(output_dir: str | None, script_content: str) -> None:
    """Write the SKiDL script to ``output_dir`` creating the directory.

    Args:
        output_dir (str | None): Directory to save the script. Abort if ``None``.
        script_content (str): The SKiDL code to write.

    Returns:
        None

    Example:
        >>> keep_skidl_script("/tmp/skidl", "from skidl import *\nERC()")
    """
    if output_dir is None:
        return  # No output directory specified, skip saving

    os.makedirs(output_dir, exist_ok=True)
    script_path = os.path.join(output_dir, "circuitron_skidl_script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)


def prepare_erc_only_script(full_script: str) -> str:
    """Return a modified script that only performs ``ERC()``.

    All ``generate_*`` function calls are commented out so that the script can
    be executed safely during validation or correction phases.

    Args:
        full_script: The complete SKiDL script as generated.

    Returns:
        The script with ``generate_*`` calls commented out.
    """

    new_lines: list[str] = []
    for line in full_script.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            new_lines.append(line)
            continue
        if re.search(r"\bgenerate_\w+\s*\(", stripped):
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def prepare_runtime_check_script(full_script: str) -> str:
    """Return a modified script that stops before ERC() for runtime checking."""

    new_lines: list[str] = []
    for line in full_script.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            new_lines.append(line)
            continue
        if re.search(r"\b(generate_\w+|ERC)\s*\(", stripped):
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def prepare_output_dir(output_dir: str | None = None) -> str:
    """Ensure ``output_dir`` exists and is empty.

    When ``output_dir`` is ``None`` a new directory called 'circuitron_output' 
    is created in the current working directory.

    Args:
        output_dir: Optional target directory path.

    Returns:
        The absolute path to the prepared directory.
    """

    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "circuitron_output")
    
    path = output_dir
    os.makedirs(path, exist_ok=True)
    
    # Clear any existing files in the directory
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except OSError:
            pass
    return os.path.abspath(path)


def pretty_print_validation(result: CodeValidationOutput) -> None:
    """Display validation summary and issues."""

    print("\n=== CODE VALIDATION SUMMARY ===")
    print(result.summary)
    if result.issues:
        print("\nIssues:")
        for issue in result.issues:
            line = f"line {issue.line}: " if issue.line else ""
            print(f" - {line}{issue.category}: {issue.message}")


def format_code_correction_input(
    script_content: str,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    erc_result: dict[str, object] | None = None,
    context: CorrectionContext | None = None,
) -> str:
    """Format input for the Code Correction agent.

    Args:
        script_content: The SKiDL script to fix.
        validation: Validation output describing issues.
        plan: The original design plan.
        selection: Component selections with pin mappings.
        docs: Documentation research results.
        erc_result: Optional ERC output from KiCad.

    Returns:
        A formatted string providing full context for code correction.
    """

    parts = [
        "CODE CORRECTION CONTEXT",
        "=" * 40,
        "Script Content:",
        script_content,
        "",
        f"Validation Summary: {validation.summary}",
    ]
    if validation.issues:
        parts.append("Issues:")
        for issue in validation.issues:
            line = f"line {issue.line}: " if issue.line else ""
            parts.append(f"- {line}{issue.category}: {issue.message}")
        parts.append("")
    if erc_result is not None:
        parts.append("ERC Result:")
        parts.append(str(erc_result))
        parts.append("")
    parts.append("")

    plan_text = format_plan_summary(plan)
    if plan_text:
        parts.append("DESIGN CONTEXT:")
        parts.append(plan_text)
        parts.append("")

    selection_text = format_selection_summary(selection)
    if selection_text:
        parts.append("COMPONENT CONTEXT:")
        parts.append(selection_text)
        parts.append("")

    docs_text = format_docs_summary(docs)
    if docs_text:
        parts.append("DOCUMENTATION CONTEXT:")
        parts.append(docs_text)
        parts.append("")

    if context is not None:
        parts.append("PREVIOUS CONTEXT:")
        parts.append(context.get_context_for_next_attempt())
        parts.append("")

    parts.append(
        "Apply iterative corrections until validation passes and ERC shows zero errors."
    )
    return "\n".join(parts)


def format_code_correction_validation_input(
    script_content: str,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext | None = None,
) -> str:
    """Format input for validation-only code correction."""

    text = format_code_correction_input(
        script_content,
        validation,
        plan,
        selection,
        docs,
        None,
        context,
    )
    return text + "\nFocus only on fixing validation issues. Ignore ERC results."



def format_erc_handling_input(
    script_content: str,
    validation: CodeValidationOutput,
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    erc_result: dict[str, object] | None,
    context: CorrectionContext | None = None,
) -> str:
    """Format input for the ERC Handling agent."""

    parts = [
        "ERC HANDLING CONTEXT",
        "=" * 40,
        "The code has passed validation; fix only electrical rules issues.",
        "",
        "Script Content:",
        script_content,
        "",
        f"Validation Summary: {validation.summary}",
    ]
    if erc_result is not None:
        parts.extend(["Latest ERC Result:", str(erc_result), ""])

    plan_text = format_plan_summary(plan)
    if plan_text:
        parts.append("DESIGN CONTEXT:")
        parts.append(plan_text)
        parts.append("")

    selection_text = format_selection_summary(selection)
    if selection_text:
        parts.append("COMPONENT CONTEXT:")
        parts.append(selection_text)
        parts.append("")

    docs_text = format_docs_summary(docs)
    if docs_text:
        parts.append("DOCUMENTATION CONTEXT:")
        parts.append(docs_text)
        parts.append("")

    if context is not None:
        parts.append("ERC HISTORY:")
        parts.append(context.get_erc_summary_for_agent())
        parts.append("")

    parts.append("Use electrical design knowledge to resolve remaining ERC violations.")
    return "\n".join(parts)


def format_runtime_correction_input(
    code: str,
    runtime_result: dict[str, object],
    plan: PlanOutput,
    selection: PartSelectionOutput,
    docs: DocumentationOutput,
    context: CorrectionContext | None = None,
) -> str:
    """Format input for the Runtime Error Correction agent."""

    parts = [
        "RUNTIME ERROR CONTEXT",
        "=" * 40,
        "Script Content:",
        code,
        "",
        "Runtime Result:",
        str(runtime_result),
        "",
    ]

    plan_text = format_plan_summary(plan)
    if plan_text:
        parts.append("DESIGN CONTEXT:")
        parts.append(plan_text)
        parts.append("")

    selection_text = format_selection_summary(selection)
    if selection_text:
        parts.append("COMPONENT CONTEXT:")
        parts.append(selection_text)
        parts.append("")

    docs_text = format_docs_summary(docs)
    if docs_text:
        parts.append("DOCUMENTATION CONTEXT:")
        parts.append(docs_text)
        parts.append("")

    if context is not None:
        parts.append("RUNTIME HISTORY:")
        parts.append(context.get_runtime_context_for_agent())
        parts.append("")

    parts.append("Fix the runtime errors so the script executes to the ERC stage.")
    return "\n".join(parts)
