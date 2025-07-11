"""Environment setup and global configuration for Circuitron."""

from __future__ import annotations

import os
import sys
import importlib
from pathlib import Path
from dotenv import load_dotenv
import urllib.request

from .settings import Settings
from .onboarding import run_onboarding

ENV_FILE = Path(os.getenv("CIRCUITRON_ENV_FILE", str(Path.home() / ".circuitron" / ".env")))

settings = Settings()

ENV_DIR = ENV_FILE.parent


def _load_env() -> None:
    """Load environment variables from the Circuitron configuration file."""
    if not ENV_FILE.exists() and os.getenv("CIRCUITRON_AUTO_ONBOARD", "1") != "0":
        run_onboarding()
    load_dotenv(ENV_FILE)



def _check_mcp_health(url: str) -> None:
    """Warn if the MCP server is unreachable."""
    if os.getenv("MCP_HEALTHCHECK") not in {"1", "true", "yes"}:
        return
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=5):
            pass
        with urllib.request.urlopen(f"{url}/sse", timeout=5):
            pass
    except Exception as exc:  # pragma: no cover - network errors
        print(f"Warning: MCP server {url} unreachable: {exc}")


def setup_environment(dev: bool = False) -> Settings:
    """Initialize environment variables and optionally configure tracing.

    Exits the program if required variables are missing.

    Args:
        dev: Enable logfire tracing when ``True``. Requires ``logfire`` to be installed.
    """
    _load_env()

    required = [
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "MCP_URL",
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        msg = ", ".join(missing)
        sys.exit(f"Missing required environment variables: {msg}")
    _check_mcp_health(os.getenv("MCP_URL", settings.mcp_url))
    if dev:
        try:
            logfire = importlib.import_module("logfire")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "logfire is required for --dev mode. Install with 'pip install circuitron[dev]'"
            ) from exc

        logfire.configure()
        logfire.instrument_openai_agents()

    new_settings = Settings()
    settings.__dict__.update(vars(new_settings))
    settings.dev_mode = dev
    return settings

__all__ = ["settings", "setup_environment", "ENV_FILE"]
