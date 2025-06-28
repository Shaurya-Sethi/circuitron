"""
Pydantic models for structured outputs in the Circuitron pipeline.
Defines all BaseModels required for getting structured outputs from agents.
"""

from typing import List
from pydantic import BaseModel, Field, ConfigDict, model_validator


class PlanOutput(BaseModel):
    """Complete output from the Planning Agent."""
    model_config = ConfigDict(extra="forbid")
    design_rationale: List[str] = Field(
        default_factory=list, 
        description="High-level bullet points explaining the overarching goals, trade-offs, and key performance targets for the chosen architecture."
    )
    functional_blocks: List[str] = Field(
        default_factory=list, 
        description="High-level functional blocks of the design, each with a one-line purpose explaining its role in the circuit."
    )
    design_equations: List[str] = Field(
        default_factory=list,
        description="Electrical equations, derivations, and design assumptions explained in engineering notation (e.g., 'V_out = V_in * (R2/(R1+R2))', 'I_max = V_supply / R_load', etc.) with clear variable definitions and units."
    )
    calculation_codes: List[str] = Field(
        default_factory=list, 
        description="Executable Python code snippets for all design calculations, using only standard math libraries."
    )
    calculation_results: List[str] = Field(
        default_factory=list,
        description="The numeric outputs from each calculation, in the same order as calculation_codes, along with an explanation of the result - not just the number."
    )
    implementation_actions: List[str] = Field(
        default_factory=list, 
        description="Specific implementation steps listed in chronological order for executing the design."
    )
    component_search_queries: List[str] = Field(
        default_factory=list, 
        description="SKiDL-style component search queries for all parts needed in the design (generic types with specifications, no numeric values for passives)."
    )
    implementation_notes: List[str] = Field(
        default_factory=list, 
        description="SKiDL-specific guidance and best practices for later implementation stages."
    )
    design_limitations: List[str] = Field(
        default_factory=list, 
        description="Missing specifications, open questions, and design constraints that need to be addressed."
    )


class CalcResult(BaseModel):
    """Result from executing a calculation in an isolated environment."""
    calculation_id: str
    success: bool
    stdout: str = ""
    stderr: str = ""


class UserFeedback(BaseModel):
    """User feedback structure for plan editing."""
    model_config = ConfigDict(extra="forbid")
    
    open_question_answers: List[str] = Field(
        default_factory=list,
        description="User's answers to the open questions from design_limitations, in the same order as presented."
    )
    requested_edits: List[str] = Field(
        default_factory=list,
        description="Specific changes, clarifications, or modifications requested by the user."
    )
    additional_requirements: List[str] = Field(
        default_factory=list,
        description="New requirements or constraints not captured in the original prompt."
    )


class PlanEditDecision(BaseModel):
    """Decision output from the PlanEdit Agent."""
    model_config = ConfigDict(extra="forbid")
    
    action: str = Field(
        description="Either 'edit_plan' or 'regenerate_plan' based on the scope of required changes."
    )
    reasoning: str = Field(
        description="Clear explanation of why this action was chosen and what changes are needed."
    )
    

class PlanEditorOutput(BaseModel):
    """Unified output from the PlanEditor agent."""

    model_config = ConfigDict(extra="forbid")

    decision: PlanEditDecision
    updated_plan: PlanOutput | None = Field(
        default=None,
        description="The updated design plan with user feedback applied if action is 'edit_plan'.",
    )
    changes_summary: List[str] = Field(
        default_factory=list,
        description="Summary of modifications made to the original plan.",
    )
    reconstructed_prompt: str | None = Field(
        default=None,
        description="New prompt for the Planner when action is 'regenerate_plan'.",
    )
    regeneration_guidance: List[str] = Field(
        default_factory=list,
        description="Guidance for the Planner when regenerating a plan.",
    )

    @model_validator(mode="after")  # type: ignore[misc,arg-type]
    def validate_fields(cls, model: "PlanEditorOutput") -> "PlanEditorOutput":
        action = model.decision.action
        if action == "edit_plan" and model.updated_plan is None:
            raise ValueError("updated_plan must be provided when action is 'edit_plan'")
        if action == "regenerate_plan" and model.reconstructed_prompt is None:
            raise ValueError(
                "reconstructed_prompt must be provided when action is 'regenerate_plan'"
            )
        return model


# ========== Part Search Agent Models ==========

class PartSearchOutput(BaseModel):
    """Complete output from the Part Search Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Search plans as formatted strings
    search_plans: List[str] = Field(default_factory=list, description="Search plans for each component with ranked queries and rationales")
    
    # Search results as formatted strings  
    search_results: List[str] = Field(default_factory=list, description="Found parts with name, library, description, footprint, and specifications")



class FoundPart(BaseModel):
    """Structure for a component found in KiCad libraries."""
    name: str
    library: str
    footprint: str | None = None
    description: str | None = None


class FoundFootprint(BaseModel):
    """Structure for a footprint found in KiCad libraries."""

    name: str
    library: str
    description: str | None = None
    package_type: str | None = None


class PartFinderOutput(BaseModel):
    """Output from the PartFinder agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    found_components_json: str = Field(description="JSON mapping search query to list of found components")


class PinDetail(BaseModel):
    """Detailed pin information for a selected component."""

    number: str | None = None
    name: str | None = None
    function: str | None = None


class SelectedPart(BaseModel):
    """A part chosen for the design with footprint and pin info."""

    name: str
    library: str
    footprint: str | None = None
    selection_reason: str | None = None
    pin_details: List[PinDetail] = Field(default_factory=list)


class PartSelectionOutput(BaseModel):
    """Output from the Part Selection agent."""

    model_config = ConfigDict(extra="forbid", strict=True)
    selections: List[SelectedPart] = Field(default_factory=list, description="Chosen parts with rationale and pin info")
    summary: List[str] = Field(default_factory=list, description="Overall selection rationale")

