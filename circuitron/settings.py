"""Centralized configuration values for Circuitron.

Environment variables can override defaults.

Example:
    from circuitron.config import settings
    print(settings.planning_model)
"""

from dataclasses import dataclass, field
import os
from typing import Final


@dataclass
class ConnectionSettings:
    """Centralized timeouts and retry configuration."""

    container_start_timeout: int = int(os.getenv("CONTAINER_START_TIMEOUT", "30"))
    container_health_check_timeout: int = int(
        os.getenv("CONTAINER_HEALTH_TIMEOUT", "10")
    )
    container_max_startup_attempts: int = int(
        os.getenv("CONTAINER_MAX_ATTEMPTS", "3")
    )

    mcp_startup_timeout: int = int(os.getenv("MCP_STARTUP_TIMEOUT", "60"))
    mcp_health_check_timeout: int = int(os.getenv("MCP_HEALTH_TIMEOUT", "15"))
    mcp_connection_timeout: int = int(os.getenv("MCP_CONNECTION_TIMEOUT", "20"))
    mcp_max_connection_attempts: int = int(
        os.getenv("MCP_MAX_CONNECTION_ATTEMPTS", "5")
    )

    network_operation_timeout: int = int(
        os.getenv("NETWORK_OPERATION_TIMEOUT", "120")
    )
    api_request_timeout: int = int(os.getenv("API_REQUEST_TIMEOUT", "30"))

    initial_retry_delay: float = float(os.getenv("INITIAL_RETRY_DELAY", "1"))
    max_retry_delay: float = float(os.getenv("MAX_RETRY_DELAY", "10"))
    retry_exponential_base: float = float(os.getenv("RETRY_EXPONENTIAL_BASE", "2"))

    def get_progressive_timeout(self, attempt: int, base_timeout: int) -> int:
        """Return progressively increased timeout for retry attempts."""
        return min(
            int(base_timeout * (self.retry_exponential_base**attempt)),
            base_timeout * 3,
        )


CONNECTION_SETTINGS: Final = ConnectionSettings()

__all__ = ["Settings", "ConnectionSettings", "CONNECTION_SETTINGS"]


@dataclass
class Settings:
    """Configuration settings loaded from environment variables."""

    planning_model: str = field(default="o4-mini")
    plan_edit_model: str = field(default="o4-mini")
    part_finder_model: str = field(default="o4-mini")
    part_selection_model: str = field(default="o4-mini")  
    documentation_model: str = field(default="o4-mini")
    code_generation_model: str = field(default="gpt-4.1")
    code_validation_model: str = field(default="o4-mini")
    code_correction_model: str = field(default="o4-mini")  # Use a model that supports tool_choice="required"
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
        default_factory=lambda: float(os.getenv("CIRCUITRON_NETWORK_TIMEOUT", "60"))
    )
    dev_mode: bool = False
