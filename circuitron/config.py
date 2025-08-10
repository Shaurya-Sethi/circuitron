"""Environment setup and global configuration for Circuitron."""

from __future__ import annotations

import os
import sys
import importlib
from dotenv import load_dotenv
import urllib.request

from .settings import Settings

settings = Settings()


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


def setup_environment(dev: bool = False, use_dotenv: bool = False) -> Settings:
    """Initialize environment variables and configure tracing.

    Exits the program if required variables are missing.

    Args:
        dev: Deprecated behavior toggle for verbose output. Tracing is now
             enabled regardless of this flag; ``dev`` only increases verbosity
             and enables additional debug panels.
    """
    # Only load .env when explicitly requested; keep tests strict by default
    if use_dotenv:
        load_dotenv()

    required = [
        "OPENAI_API_KEY",
        "MCP_URL",
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        msg = ", ".join(missing)
        sys.exit(f"Missing required environment variables: {msg}")
    _check_mcp_health(os.getenv("MCP_URL", settings.mcp_url))
    # Always configure logfire tracing (required dependency)
    try:
        logfire = importlib.import_module("logfire")
        # Default configuration; environment variables can refine it
        logfire.configure()
        # Instrument OpenAI Agents SDK traces
        logfire.instrument_openai_agents()
        # Attach our token usage span processor if possible (no user-visible change)
        try:
            from .telemetry import attach_span_processor_if_possible

            attach_span_processor_if_possible()
        except Exception:
            # Never break setup if telemetry attachment fails
            pass
    except ModuleNotFoundError as exc:  # pragma: no cover - installation issue
        raise RuntimeError(
            "logfire is now a required dependency. Install with 'pip install circuitron'."
        ) from exc

    new_settings = Settings()
    settings.__dict__.update(vars(new_settings))
    # dev flag now controls verbosity & extra panels only
    settings.dev_mode = dev
    return settings
