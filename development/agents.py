"""
Agent definitions and configurations for the Circuitron system.
Contains all specialized agents used in the PCB design pipeline.
"""

from agents import Agent
from agents.model_settings import ModelSettings
from .prompts import PLAN_PROMPT, PLAN_EDIT_PROMPT
from .models import PlanOutput, EditedPlanOutput, RegeneratedPlanPrompt
from .tools import execute_calculation


def create_planning_agent() -> Agent:
    """Create and configure the Planning Agent."""
    model_settings = ModelSettings(
        tool_choice="required",
        reasoning={
            "effort": "medium",  # default
            "summary": "detailed"  
        }
    )

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
    model_settings = ModelSettings(
        tool_choice="required",
        reasoning={
            "effort": "medium",
            "summary": "detailed"  
        }
    )

    return Agent(
        name="Circuitron-PlanEditor",
        instructions=PLAN_EDIT_PROMPT,
        model="o4-mini",
        # Note: We'll need to handle dynamic output types based on the decision
        # This will be handled in the orchestration logic
        tools=[execute_calculation],
        model_settings=model_settings
    )


# Create agent instances
planner = create_planning_agent()
plan_editor = create_plan_edit_agent()
