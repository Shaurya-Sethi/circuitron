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

    planning_model: str = field(default="o4-mini")
    plan_edit_model: str = field(default="o4-mini")
    part_finder_model: str = field(default="o4-mini")
    part_selection_model: str = field(default="o4-mini") # Use a model that supports tool_choice="required"
    documentation_model: str = field(default="o4-mini")
    # Default to o4-mini so the system is consistent until user changes it at runtime
    code_generation_model: str = field(default="o4-mini") # Use a model that supports tool_choice="required"
    code_validation_model: str = field(default="o4-mini")
    code_correction_model: str = field(default="o4-mini") 
    erc_handling_model: str = field(default="o4-mini")
    runtime_correction_model: str = field(default="o4-mini")
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
    max_turns: int = field(
        default_factory=lambda: int(os.getenv("CIRCUITRON_MAX_TURNS", "50"))
    )
    network_timeout: float = field(
        default_factory=lambda: float(os.getenv("CIRCUITRON_NETWORK_TIMEOUT", "300"))
    )
    dev_mode: bool = False
    footprint_search_enabled: bool = True

    def set_all_models(self, model: str) -> None:
        """Set all agent model fields to the given ``model``.

        This enables runtime switching of the active model used by all agents.

        Args:
            model: The model name to apply (e.g., "o4-mini", "gpt-5-mini").

        Example:
            >>> from circuitron.config import settings
            >>> settings.set_all_models("gpt-5-mini")
        """
        self.planning_model = model
        self.plan_edit_model = model
        self.part_finder_model = model
        self.part_selection_model = model
        self.documentation_model = model
        self.code_generation_model = model
        self.code_validation_model = model
        self.code_correction_model = model
        self.erc_handling_model = model
        self.runtime_correction_model = model
