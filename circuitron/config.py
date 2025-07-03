"""Environment setup and global configuration for Circuitron."""

from __future__ import annotations

import logfire
from dotenv import load_dotenv

from .settings import Settings

settings: Settings


def setup_environment() -> None:
    """Initialize environment variables and configure logging/tracing."""
    load_dotenv()
    logfire.configure()
    logfire.instrument_openai_agents()

    global settings
    settings = Settings()
