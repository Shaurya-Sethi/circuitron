"""Environment setup and global configuration for Circuitron."""

from __future__ import annotations

import os
import sys
import logfire
from dotenv import load_dotenv

from .settings import Settings

settings: Settings


def setup_environment() -> None:
    """Initialize environment variables and configure logging/tracing.

    Exits the program if required variables are missing.
    """
    load_dotenv()

    required = ["OPENAI_API_KEY", "MCP_URL"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        msg = ", ".join(missing)
        sys.exit(f"Missing required environment variables: {msg}")
    logfire.configure()
    logfire.instrument_openai_agents()

    global settings
    settings = Settings()
