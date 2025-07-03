"""Environment setup and global configuration for Circuitron."""

from __future__ import annotations

import os
import sys
import logfire
from dotenv import load_dotenv

from .settings import Settings

settings = Settings()


def setup_environment() -> Settings:
    """Initialize environment variables and configure logging/tracing.

    Exits the program if required variables are missing.
    """
    load_dotenv()

    required = [
        "OPENAI_API_KEY",
        "PLANNING_MODEL",
        "PLAN_EDIT_MODEL",
        "PART_FINDER_MODEL",
        "MCP_URL",
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        msg = ", ".join(missing)
        sys.exit(f"Missing required environment variables: {msg}")
    logfire.configure()
    logfire.instrument_openai_agents()

    new_settings = Settings()
    settings.__dict__.update(vars(new_settings))
    return settings
