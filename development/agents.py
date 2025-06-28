"""
Agent definitions and configurations for the Circuitron system.
Contains all specialized agents used in the PCB design pipeline.
"""

from agents import Agent, handoff
from agents.model_settings import ModelSettings
from .prompts import PLAN_PROMPT, PLAN_EDIT_PROMPT, PARTFINDER_PROMPT
from .models import PlanOutput, PlanEditorOutput, PartFinderOutput
from .tools import execute_calculation, search_kicad_libraries


def create_planning_agent() -> Agent:
    """Create and configure the Planning Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-Planner",
        instructions=PLAN_PROMPT,
        model="o4-mini",
        output_type=PlanOutput,
        tools=[execute_calculation],
        model_settings=model_settings
    )


def create_plan_edit_agent() -> Agent:
    """Create and configure the Plan Edit Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-PlanEditor",
        instructions=PLAN_EDIT_PROMPT,
        model="o4-mini",
        output_type=PlanEditorOutput,
        tools=[execute_calculation],
        model_settings=model_settings,
    )


def create_partfinder_agent() -> Agent:
    """Create and configure the PartFinder Agent."""
    model_settings = ModelSettings(tool_choice="required")

    return Agent(
        name="Circuitron-PartFinder",
        instructions=PARTFINDER_PROMPT,
        model="o4-mini",
        output_type=PartFinderOutput,
        tools=[search_kicad_libraries],
        model_settings=model_settings,
    )

# Create agent instances
planner = create_planning_agent()
plan_editor = create_plan_edit_agent()
part_finder = create_partfinder_agent()

# Configure handoffs between agents
planner.handoffs = [plan_editor]
plan_editor.handoffs = [handoff(planner), handoff(part_finder)]
