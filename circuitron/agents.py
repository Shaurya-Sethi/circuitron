"""
Agent definitions and configurations for the Circuitron system.
Contains all specialized agents used in the PCB design pipeline.
"""

from agents import Agent, RunContextWrapper, handoff
from agents.model_settings import ModelSettings
import logging

from .config import settings
from .prompts import (
    PLAN_PROMPT,
    PLAN_EDIT_PROMPT,
    PARTFINDER_PROMPT,
    PART_SELECTION_PROMPT,
)
from .models import (
    PlanOutput,
    PlanEditorOutput,
    PartFinderOutput,
    PartSelectionOutput,
)
from .tools import (
    execute_calculation,
    search_kicad_libraries,
    search_kicad_footprints,
    extract_pin_details,
)


def create_planning_agent() -> Agent:
    """Create and configure the Planning Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-Planner",
        instructions=PLAN_PROMPT,
        model=settings.planning_model,
        output_type=PlanOutput,
        tools=[execute_calculation],
        model_settings=model_settings,
        handoff_description="Generate initial design plan",
    )


def create_plan_edit_agent() -> Agent:
    """Create and configure the Plan Edit Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-PlanEditor",
        instructions=PLAN_EDIT_PROMPT,
        model=settings.plan_edit_model,
        output_type=PlanEditorOutput,
        tools=[execute_calculation],
        model_settings=model_settings,
        handoff_description="Review user feedback and adjust the plan",
    )


def create_partfinder_agent() -> Agent:
    """Create and configure the PartFinder Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-PartFinder",
        instructions=PARTFINDER_PROMPT,
        model=settings.part_finder_model,
        output_type=PartFinderOutput,
        tools=[search_kicad_libraries, search_kicad_footprints],
        model_settings=model_settings,
        handoff_description="Search KiCad libraries for required parts",
    )


def create_partselection_agent() -> Agent:
    """Create and configure the Part Selection Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-PartSelector",
        instructions=PART_SELECTION_PROMPT,
        model=settings.part_selection_model,
        output_type=PartSelectionOutput,
        tools=[extract_pin_details],
        model_settings=model_settings,
        handoff_description="Select optimal components and extract pin info",
    )


def _log_handoff_to(target: str):
    """Return a callback that logs when a handoff occurs."""

    def _callback(ctx: RunContextWrapper[None]) -> None:
        logging.info("Handoff to %s", target)

    return _callback

# Create agent instances
planner = create_planning_agent()
plan_editor = create_plan_edit_agent()
part_finder = create_partfinder_agent()
part_selector = create_partselection_agent()

# Configure handoffs between agents
planner.handoffs = [handoff(plan_editor, on_handoff=_log_handoff_to("PlanEditor"))]
plan_editor.handoffs = [
    handoff(planner, on_handoff=_log_handoff_to("Planner")),
    handoff(part_finder, on_handoff=_log_handoff_to("PartFinder")),
]
part_finder.handoffs = [handoff(part_selector, on_handoff=_log_handoff_to("PartSelector"))]
