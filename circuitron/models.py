"""
Pydantic models for structured outputs in the Circuitron pipeline.
Defines all BaseModels required for getting structured outputs from agents.
"""

from typing import List, Literal
from enum import Enum
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
    """Decision output from the PlanEditor agent."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["edit_plan"] = Field(
        default="edit_plan",
        description='Action type. Always "edit_plan".'
    )
    reasoning: str = Field(
        description="Explanation of the updates applied to the plan.",
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

    @model_validator(mode="after")
    def validate_fields(self) -> "PlanEditorOutput":
        if self.updated_plan is None:
            raise ValueError("updated_plan must be provided")
        return self


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
    found_components_json: str = Field(description="JSON mapping search query to list of found components. Only include queries that returned useful results.")

    def get_total_components(self) -> int:
        """Get total number of components found across all searches."""
        import json
        try:
            data = json.loads(self.found_components_json)
            return sum(len(components) for components in data.values() if components)
        except Exception:
            return 0
    
    def get_successful_searches(self) -> int:
        """Get number of searches that returned results."""
        import json
        try:
            data = json.loads(self.found_components_json)
            return sum(1 for components in data.values() if components)
        except Exception:
            return 0


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


class PriorityLevel(str, Enum):
    """Priority levels for documentation queries."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentationOutput(BaseModel):
    """Complete output from the Documentation Agent."""

    model_config = ConfigDict(extra="forbid", strict=True)
    research_queries: List[str] = Field(
        default_factory=list,
        description="Prioritized research queries with context",
    )
    documentation_findings: List[str] = Field(
        default_factory=list,
        description="Research findings with code examples and references",
    )
    implementation_readiness: str = Field(
        ...,
        description="Assessment of readiness for code generation",
    )


class CodeGenerationOutput(BaseModel):
    """Complete output from the Code Generation Agent."""

    model_config = ConfigDict(extra="forbid", strict=True)

    # Complete SKiDL code
    complete_skidl_code: str = Field(
        ..., description="Complete executable SKiDL code"
    )

    # Code metadata as formatted strings
    imports: List[str] = Field(
        default_factory=list, description="Required import statements"
    )
    power_rails: List[str] = Field(
        default_factory=list,
        description="Power rail configurations with names and settings",
    )
    components: List[str] = Field(
        default_factory=list,
        description="Component instantiations with part and footprint details",
    )
    connections: List[str] = Field(
        default_factory=list,
        description="Connections between components with net names",
    )
    validation_calls: List[str] = Field(
        default_factory=list, description="ERC and other validation calls"
    )
    output_generation: List[str] = Field(
        default_factory=list, description="Output generation calls"
    )

    # Implementation notes and assumptions
    implementation_notes: List[str] = Field(
        default_factory=list, description="Important implementation notes"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="Assumptions made during generation"
    )

class ValidationIssue(BaseModel):
    """Issue detected during code validation."""

    line: int | None = Field(
        default=None, description="Line number where the issue was found"
    )
    category: str = Field(
        ..., description="Type of issue such as syntax, mismatch, or warning"
    )
    message: str = Field(..., description="Human readable description of the issue")


class ValidationSummary(BaseModel):
    """Summary counts from hallucination checking."""

    total_validations: int
    valid_count: int
    invalid_count: int
    uncertain_count: int
    not_found_count: int
    hallucination_rate: float


class AnalysisMetadata(BaseModel):
    """Metadata about script analysis."""

    total_imports: int
    total_classes: int
    total_methods: int
    total_attributes: int
    total_functions: int


class HallucinationReport(BaseModel):
    """Result from ``check_ai_script_hallucinations``."""

    success: bool
    script_path: str
    overall_confidence: float | int
    validation_summary: ValidationSummary
    hallucinations_detected: bool
    recommendations: List[str] = Field(default_factory=list)
    analysis_metadata: AnalysisMetadata
    libraries_analyzed: List[str] = Field(default_factory=list)


class CodeValidationOutput(BaseModel):
    """Output from the Code Validation agent."""

    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["pass", "fail"]
    summary: str = Field(..., description="Overall validation summary")
    issues: List[ValidationIssue] = Field(default_factory=list)
    hallucination_report: HallucinationReport | None = None


class CodeCorrectionOutput(BaseModel):
    """Complete output from the Code Correction Agent."""

    model_config = ConfigDict(extra="forbid", strict=True)

    issues_identified: List[str] = Field(
        default_factory=list,
        description="All issues identified with type, description, and location",
    )
    corrections_made: List[str] = Field(
        default_factory=list,
        description="Corrections applied with rationale",
    )
    documentation_references: List[str] = Field(
        default_factory=list,
        description="Documentation references used",
    )
    corrected_code: str = Field(..., description="Complete corrected SKiDL code")
    validation_notes: str = Field(
        ..., description="Notes about the validation and correction process"
    )
