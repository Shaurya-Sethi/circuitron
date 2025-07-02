"""Centralized configuration values for Circuitron.

Environment variables can override defaults.

Example:
    from circuitron.config import settings
    print(settings.planning_model)
"""

from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Configuration settings loaded from environment variables."""

    planning_model: str = os.getenv("PLANNING_MODEL", "o4-mini")
    plan_edit_model: str = os.getenv("PLAN_EDIT_MODEL", "o4-mini")
    part_finder_model: str = os.getenv("PART_FINDER_MODEL", "o4-mini")
    part_selection_model: str = os.getenv("PART_SELECTION_MODEL", "o4-mini")
    documentation_model: str = os.getenv("DOCUMENTATION_MODEL", "o4-mini")
    calculation_image: str = os.getenv("CALC_IMAGE", "python:3.12-slim")
    kicad_image: str = os.getenv(
        "KICAD_IMAGE", "ghcr.io/circuitron/kicad-skidl:latest"
    )
    mcp_url: str = os.getenv("MCP_URL", "http://localhost:8051")
