"""
Agent definitions and configurations for the Circuitron system.
Contains all specialized agents used in the PCB design pipeline.
"""

from agents import Agent, RunContextWrapper, handoff
from agents.model_settings import ModelSettings
import logging

from .config import settings
from .prompts import PLAN_PROMPT, PLAN_EDIT_PROMPT, PARTFINDER_PROMPT
from .models import PlanOutput, PlanEditorOutput, PartFinderOutput
from .tools import execute_calculation, search_kicad_libraries


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
        tools=[search_kicad_libraries],
        model_settings=model_settings,
        handoff_description="Search KiCad libraries for required parts",
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

# Configure handoffs between agents
planner.handoffs = [handoff(plan_editor, on_handoff=_log_handoff_to("PlanEditor"))]
plan_editor.handoffs = [
    handoff(planner, on_handoff=_log_handoff_to("Planner")),
    handoff(part_finder, on_handoff=_log_handoff_to("PartFinder")),
]
