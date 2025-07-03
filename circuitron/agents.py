"""
Agent definitions and configurations for the Circuitron system.
Contains all specialized agents used in the PCB design pipeline.
"""

from agents import Agent, RunContextWrapper, handoff
from agents.tool import Tool
from typing import Callable
from agents.model_settings import ModelSettings
import logging

from .config import settings
from .prompts import (
    PLAN_PROMPT,
    PLAN_EDIT_PROMPT,
    PARTFINDER_PROMPT,
    PART_SELECTION_PROMPT,
    DOC_AGENT_PROMPT,
    CODE_GENERATION_PROMPT,
    CODE_VALIDATION_PROMPT,
    CODE_CORRECTION_PROMPT,
)
from .models import (
    PlanOutput,
    PlanEditorOutput,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
    CodeCorrectionOutput,
)
from .tools import (
    execute_calculation,
    search_kicad_libraries,
    search_kicad_footprints,
    extract_pin_details,
    create_mcp_documentation_tools,
    create_mcp_validation_tools,
    run_erc_tool,
)


def create_planning_agent() -> Agent:
    """Create and configure the Planning Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = [execute_calculation]

    return Agent(
        name="Circuitron-Planner",
        instructions=PLAN_PROMPT,
        model=settings.planning_model,
        output_type=PlanOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Generate initial design plan",
    )


def create_plan_edit_agent() -> Agent:
    """Create and configure the Plan Edit Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = [execute_calculation]

    return Agent(
        name="Circuitron-PlanEditor",
        instructions=PLAN_EDIT_PROMPT,
        model=settings.plan_edit_model,
        output_type=PlanEditorOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Review user feedback and adjust the plan",
    )


def create_partfinder_agent() -> Agent:
    """Create and configure the PartFinder Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = [search_kicad_libraries, search_kicad_footprints]

    return Agent(
        name="Circuitron-PartFinder",
        instructions=PARTFINDER_PROMPT,
        model=settings.part_finder_model,
        output_type=PartFinderOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Search KiCad libraries for required parts",
    )


def create_partselection_agent() -> Agent:
    """Create and configure the Part Selection Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = [extract_pin_details]

    return Agent(
        name="Circuitron-PartSelector",
        instructions=PART_SELECTION_PROMPT,
        model=settings.part_selection_model,
        output_type=PartSelectionOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Select optimal components and extract pin info",
    )


def create_documentation_agent() -> Agent:
    """Create and configure the Documentation Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = create_mcp_documentation_tools()

    return Agent(
        name="Circuitron-DocSeeker",
        instructions=DOC_AGENT_PROMPT,
        model=settings.documentation_model,
        output_type=DocumentationOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Gather SKiDL documentation",
    )


def create_code_generation_agent() -> Agent:
    """Create and configure the Code Generation Agent."""
    model_settings = ModelSettings(tool_choice="auto")

    tools: list[Tool] = create_mcp_documentation_tools()

    return Agent(
        name="Circuitron-Coder",
        instructions=CODE_GENERATION_PROMPT,
        model=settings.code_generation_model,
        output_type=CodeGenerationOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Generate production-ready SKiDL code",
    )


def create_code_validation_agent() -> Agent:
    """Create and configure the Code Validation Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = create_mcp_validation_tools()

    return Agent(
        name="Circuitron-Validator",
        instructions=CODE_VALIDATION_PROMPT,
        model=settings.code_validation_model,
        output_type=CodeValidationOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Validate SKiDL code",
    )


def create_code_correction_agent() -> Agent:
    """Create and configure the Code Correction Agent."""
    model_settings = ModelSettings(tool_choice="required")

    tools: list[Tool] = [
        *create_mcp_documentation_tools(),
        *create_mcp_validation_tools(),
        run_erc_tool,
    ]

    return Agent(
        name="Circuitron-Corrector",
        instructions=CODE_CORRECTION_PROMPT,
        model=settings.code_validation_model,
        output_type=CodeCorrectionOutput,
        tools=tools,
        model_settings=model_settings,
        handoff_description="Iteratively fix SKiDL code",
    )


def _log_handoff_to(target: str) -> Callable[[RunContextWrapper[None]], None]:
    """Return a callback that logs when a handoff occurs."""

    def _callback(ctx: RunContextWrapper[None]) -> None:
        logging.info("Handoff to %s", target)

    return _callback

# Create agent instances
planner = create_planning_agent()
plan_editor = create_plan_edit_agent()
part_finder = create_partfinder_agent()
part_selector = create_partselection_agent()
documentation = create_documentation_agent()
code_generator = create_code_generation_agent()
code_validator = create_code_validation_agent()
code_corrector = create_code_correction_agent()

# Configure handoffs between agents
planner.handoffs = [handoff(plan_editor, on_handoff=_log_handoff_to("PlanEditor"))]
plan_editor.handoffs = [
    handoff(planner, on_handoff=_log_handoff_to("Planner")),
    handoff(part_finder, on_handoff=_log_handoff_to("PartFinder")),
]
part_finder.handoffs = [handoff(part_selector, on_handoff=_log_handoff_to("PartSelector"))]
part_selector.handoffs = [handoff(documentation, on_handoff=_log_handoff_to("Documentation"))]
documentation.handoffs = [handoff(code_generator, on_handoff=_log_handoff_to("CodeGeneration"))]
code_generator.handoffs = [handoff(code_validator, on_handoff=_log_handoff_to("CodeValidation"))]
code_validator.handoffs = [handoff(code_corrector, on_handoff=_log_handoff_to("CodeCorrection"))]
