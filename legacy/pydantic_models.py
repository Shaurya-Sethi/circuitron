"""Pydantic BaseModels for structured outputs in the Circuitron pipeline.

This module defines all the Pydantic BaseModels required for getting structured outputs
from each agent in the pipeline, following OpenAI Agents SDK patterns for structured outputs.

Note: Models are simplified to use primitive types only to avoid JSON schema $defs issues
with the OpenAI Agents SDK strict validation.
"""

from enum import Enum
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field, ConfigDict


# ========== Planning Agent Models ==========

class PlanOutput(BaseModel):
    """Complete output from the Planning Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Functional blocks as simple strings
    functional_blocks: List[str] = Field(default_factory=list, description="High-level functional blocks with name, description, inputs, and outputs as formatted strings")
    
    # Calculations as executable code strings
    calculation_codes: List[str] = Field(default_factory=list, description="All design calculations as executable Python code with descriptions")
    
    # Implementation actions as simple strings
    implementation_actions: List[str] = Field(default_factory=list, description="Ordered implementation steps with step numbers and dependencies")
    
    # Component search queries as simple strings
    component_search_queries: List[str] = Field(default_factory=list, description="SKiDL search queries for parts needed with component type and specifications")
    
    # Implementation notes as simple strings
    implementation_notes: List[str] = Field(default_factory=list, description="SKiDL-specific implementation guidance by category")
    
    # Limitations as simple strings
    design_limitations: List[str] = Field(default_factory=list, description="Missing specifications and open questions by category")

 
# ========== Part Search Agent Models ==========

class PartSearchOutput(BaseModel):
    """Complete output from the Part Search Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Search plans as formatted strings
    search_plans: List[str] = Field(default_factory=list, description="Search plans for each component with ranked queries and rationales")
    
    # Search results as formatted strings  
    search_results: List[str] = Field(default_factory=list, description="Found parts with name, library, description, footprint, and specifications")

 
# ========== Part Selection Agent Models ==========

class PartSelectionOutput(BaseModel):
    """Complete output from the Part Selection Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Selection criteria as formatted strings
    selection_criteria: List[str] = Field(default_factory=list, description="Electrical requirements, package preferences, and performance priorities")
    
    # Part evaluations as formatted strings
    part_evaluations: List[str] = Field(default_factory=list, description="Evaluation of all candidate parts with scores, pros, cons, and notes")
    
    # Selected parts as formatted strings
    selected_parts: List[str] = Field(default_factory=list, description="Final selected parts with rationale and alternatives")


# ========== Documentation Agent Models ==========

class PriorityLevel(str, Enum):
    """Priority levels for documentation queries."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentationOutput(BaseModel):
    """Complete output from the Documentation Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Research queries as formatted strings
    research_queries: List[str] = Field(default_factory=list, description="Prioritized research queries with priority levels and context")
    
    # Documentation findings as formatted strings
    documentation_findings: List[str] = Field(default_factory=list, description="Research findings with code examples, API references, and best practices")
    
    # Implementation readiness assessment
    implementation_readiness: str = Field(..., description="Assessment of readiness for code generation")


# ========== Code Generation Agent Models ==========

class CodeGenerationOutput(BaseModel):
    """Complete output from the Code Generation Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Complete SKiDL code
    complete_skidl_code: str = Field(..., description="Complete executable SKiDL code")
    
    # Code metadata as formatted strings
    imports: List[str] = Field(default_factory=list, description="Required import statements")
    power_rails: List[str] = Field(default_factory=list, description="Power rail configurations with names, voltages, and settings")
    components: List[str] = Field(default_factory=list, description="Component instantiations with names, parts, libraries, and parameters")
    connections: List[str] = Field(default_factory=list, description="All connections between components with from/to details and net names")
    validation_calls: List[str] = Field(default_factory=list, description="ERC and other validation calls")
    output_generation: List[str] = Field(default_factory=list, description="SVG and other output generation calls")
    
    # Implementation notes and assumptions
    implementation_notes: List[str] = Field(default_factory=list, description="Important notes about the implementation")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made during code generation")


# ========== Code Execution Agent Models ==========

class CodeExecutionOutput(BaseModel):
    """Complete output from the Code Execution Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Hallucination check results
    hallucination_check_passed: bool = Field(..., description="Whether the code passed hallucination checks")
    hallucination_issues: List[str] = Field(default_factory=list, description="List of hallucination issues found")
    hallucination_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the validation")
    
    # Execution results
    execution_success: bool = Field(..., description="Whether the code executed successfully")
    execution_output: str = Field(..., description="Output from code execution")
    execution_errors: List[str] = Field(default_factory=list, description="Any errors encountered during execution")
    execution_warnings: List[str] = Field(default_factory=list, description="Any warnings generated")
    files_generated: List[str] = Field(default_factory=list, description="List of files generated (e.g., SVG, netlist)")
    
    # Summary and next action
    verification_summary: str = Field(..., description="Summary of verification outcome")
    next_action: str = Field(..., description="Recommended next action (execute, correct, or flag)")


# ========== Code Correction Agent Models ==========

class CodeCorrectionOutput(BaseModel):
    """Complete output from the Code Correction Agent."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    # Issues and corrections as formatted strings
    issues_identified: List[str] = Field(default_factory=list, description="All issues identified with type, description, location, and severity")
    corrections_made: List[str] = Field(default_factory=list, description="All corrections applied with issue addressed, original code, corrected code, and rationale")
    documentation_references: List[str] = Field(default_factory=list, description="Documentation references used with source, section, and application")
    
    # Final corrected code
    corrected_code: str = Field(..., description="Complete corrected SKiDL code")
    validation_notes: str = Field(..., description="Notes about the validation and correction process")

 
# ========== Calculation Execution Models ==========

class CalculationRequest(BaseModel):
    """Request to execute a calculation."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    calculation_id: str = Field(..., description="Unique identifier for the calculation")
    description: str = Field(..., description="Description of what the calculation does")
    code: str = Field(..., description="Python code to execute")

 
class CalculationResult(BaseModel):
    """Result from executing a calculation."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    calculation_id: str = Field(..., description="Identifier of the executed calculation")
    success: bool = Field(..., description="Whether the calculation executed successfully")
    result_value: str = Field(..., description="Calculation result as a string representation")
    output: str = Field(..., description="Text output from the calculation")
    error: str = Field(default="", description="Error message if calculation failed")


# ========== Common Models ==========

class AgentResponse(BaseModel):
    """Base model for agent responses with metadata."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    agent_name: str = Field(..., description="Name of the agent providing the response")
    timestamp: str = Field(..., description="Timestamp of the response")
    success: bool = Field(..., description="Whether the agent operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")

 
class PipelineStatus(BaseModel):
    """Status of the overall pipeline execution."""
    model_config = ConfigDict(extra="forbid", strict=True)
    
    current_stage: str = Field(..., description="Current stage in the pipeline")
    completed_stages: List[str] = Field(default_factory=list, description="List of completed stages")
    pending_stages: List[str] = Field(default_factory=list, description="List of remaining stages")
    overall_progress: float = Field(..., ge=0.0, le=1.0, description="Overall progress as a percentage")
    status_message: str = Field(..., description="Current status description")
