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
    """Initialize environment variables and optionally configure tracing.

    Exits the program if required variables are missing.

    Args:
        dev: Enable logfire tracing when ``True``. Requires ``logfire`` to be installed.
        use_dotenv: When ``True``, load variables from a .env file. Defaults to False
            so tests and strict environments aren't masked by .env contents.
    """
    # Load .env file only when explicitly requested so tests can assert missing envs
    if use_dotenv:
        load_dotenv(override=False)

    required = [
        "OPENAI_API_KEY",
        "MCP_URL",
    ]
    # Re-read from process env each call; treat empty strings as missing
    missing = [var for var in required if not os.environ.get(var)]
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
