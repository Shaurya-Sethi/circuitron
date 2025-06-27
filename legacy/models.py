"""Pydantic models for structured outputs in Circuitron pipeline."""
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanOutput(BaseModel):
    """Structured output from the planning agent."""
    schematic_overview: List[str] = Field(description="High-level functional blocks as bullet points")
    calculations: List[str] = Field(description="Design assumptions, equations, and derivations")
    actions: List[str] = Field(description="Imperative actions, one per item")
    draft_search_queries: List[str] = Field(description="SKiDL search queries for components")
    part_candidates: List[str] = Field(description="Optional hints for component lookup")
    implementation_notes: List[str] = Field(description="SKiDL-specific implementation guidance")
    limitations: List[str] = Field(description="Missing specs or open questions")


class PartSearchOutput(BaseModel):
    """Structured output from part search cleaning agent."""
    cleaned_queries: List[str] = Field(description="Cleaned SKiDL search terms")
    
    
class PartLookupResult(BaseModel):
    """Individual component lookup result."""
    part: str = Field(description="Library:Part identifier")
    description: str = Field(description="Component description")
    

class PartLookupOutput(BaseModel):
    """Structured output from part lookup process."""
    found_parts: List[PartLookupResult] = Field(description="Successfully found components")
    failed_queries: List[str] = Field(description="Queries that returned no results")


class DocumentationQuery(BaseModel):
    """Individual documentation question."""
    query: str = Field(description="Specific SKiDL API or pattern question")
    priority: str = Field(description="high/medium/low priority")


class DocumentationOutput(BaseModel):
    """Structured output from documentation seeker agent."""
    queries: List[DocumentationQuery] = Field(description="SKiDL questions to research")


class CodeOutput(BaseModel):
    """Structured output from code generation agent."""
    skidl_code: str = Field(description="Complete SKiDL Python script")
    parts_count: int = Field(description="Number of parts instantiated")
    power_rails: List[str] = Field(description="Power rail names used")
    assumptions: List[str] = Field(description="Design assumptions made")


class ApprovalRequest(BaseModel):
    """Base class for human approval requests."""
    stage: str = Field(description="Pipeline stage requesting approval")
    content: str = Field(description="Content to review")
    approve: bool = Field(description="Whether to approve and continue", default=False)


class PlanApproval(ApprovalRequest):
    """Plan approval with edit capability."""
    edited_plan: Optional[PlanOutput] = Field(description="User-edited plan if changes needed", default=None)


class PartsApproval(ApprovalRequest):
    """Parts approval with selection capability."""
    selected_parts: List[str] = Field(description="User-selected subset of parts", default_factory=list)


class CodeApproval(ApprovalRequest):
    """Code approval with edit capability."""
    edited_code: Optional[str] = Field(description="User-edited code if changes needed", default=None)
