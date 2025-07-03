"""Centralized configuration values for Circuitron.

Environment variables can override defaults.

Example:
    from circuitron.config import settings
    print(settings.planning_model)
"""

from dataclasses import dataclass, field
import os


@dataclass
class Settings:
    """Configuration settings loaded from environment variables."""

    planning_model: str = field(
        default_factory=lambda: os.getenv("PLANNING_MODEL", "o4-mini")
    )
    plan_edit_model: str = field(
        default_factory=lambda: os.getenv("PLAN_EDIT_MODEL", "o4-mini")
    )
    part_finder_model: str = field(
        default_factory=lambda: os.getenv("PART_FINDER_MODEL", "o4-mini")
    )
    part_selection_model: str = field(
        default_factory=lambda: os.getenv("PART_SELECTION_MODEL", "o4-mini")
    )
    documentation_model: str = field(
        default_factory=lambda: os.getenv("DOCUMENTATION_MODEL", "o4-mini")
    )
    code_generation_model: str = field(
        default_factory=lambda: os.getenv("CODE_GENERATION_MODEL", "o4-mini")
    )
    code_validation_model: str = field(
        default_factory=lambda: os.getenv("CODE_VALIDATION_MODEL", "o4-mini")
    )
    calculation_image: str = field(
        default_factory=lambda: os.getenv("CALC_IMAGE", "python:3.12-slim")
    )
    kicad_image: str = field(
        default_factory=lambda: os.getenv(
            "KICAD_IMAGE", "ghcr.io/shaurya-sethi/circuitron-kicad:latest"
        )
    )
    mcp_url: str = field(
        default_factory=lambda: os.getenv("MCP_URL", "http://localhost:8051")
    )
