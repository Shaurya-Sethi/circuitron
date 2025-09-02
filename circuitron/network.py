"""Network and service availability utilities for Circuitron.

This module provides internet reachability checks and MCP server availability
checks. The MCP server is a required service that exposes documentation and
validation tools via SSE and must be running before the pipeline or setup
flows execute.
"""

from __future__ import annotations

import os
import socket
import subprocess
from typing import Any

import httpx

from .config import settings


def is_connected(url: str = "https://api.openai.com", timeout: float = 10.0) -> bool:
    """Return ``True`` if ``url`` is reachable within ``timeout`` seconds.

    Args:
        url: Endpoint to send a ``HEAD`` request to.
        timeout: Seconds to wait for the response.

    Returns:
        ``True`` when the endpoint responds without error, otherwise ``False``.

    Example:
        >>> is_connected()
        True
    """
    try:
        httpx.head(url, timeout=timeout)
        return True
    except (httpx.RequestError, socket.gaierror, TimeoutError, OSError):
        return False


def _display_error(message: str, ui: Any | None = None) -> None:
    """Best-effort error display without creating import cycles.

    Uses the provided UI if available; otherwise attempts a lazy import of
    TerminalUI. Falls back to printing to stderr if UI components are
    unavailable at import time.
    """
    if ui is not None and hasattr(ui, "display_error"):
        try:
            ui.display_error(message)
            return
        except Exception:
            pass
    try:
        from .ui.app import TerminalUI  # local import to avoid circular import

        TerminalUI().display_error(message)
    except Exception:
        # Last resort: plain print
        try:
            import sys

            print(message, file=sys.stderr)
        except Exception:
            pass


def check_internet_connection() -> bool:
    """Check for internet connectivity and print a message when absent.

    Returns:
        ``True`` if :func:`is_connected` succeeds, otherwise ``False``.

    Example:
        >>> check_internet_connection()
        True
    """
    if not is_connected():
        _display_error(
            "No internet connection detected. Please connect and try again."
        )
        return False
    return True

def is_mcp_server_available(url: str | None = None, *, timeout: float | None = None) -> bool:
    """Return True if the MCP server responds on /health or /sse.

    Tries a quick health probe first, then attempts to open a short-lived SSE
    stream to verify the endpoint is reachable.

    Args:
        url: Base MCP server URL (defaults to settings.mcp_url).
        timeout: Overall timeout in seconds for each attempt. Uses a small
                 default derived from settings.network_timeout when omitted.

    Returns:
        True if the server responds without connection errors, else False.
    """
    base = (url or settings.mcp_url).rstrip("/")
    to = float(timeout if timeout is not None else max(1.0, min(5.0, float(settings.network_timeout))))

    # Try health endpoint first (best-effort)
    try:
        resp = httpx.get(f"{base}/health", timeout=to)
        if resp.status_code < 500:
            return True
    except Exception:
        pass

    # Fallback to opening an SSE stream and immediately close after headers
    try:
        with httpx.Client(timeout=httpx.Timeout(connect=to, read=1.0, write=1.0, pool=to)) as client:
            headers = {"Accept": "text/event-stream"}
            with client.stream("GET", f"{base}/sse", headers=headers) as r:  # type: ignore[no-redef]
                # If the connection was established and headers received, consider it available.
                return r.status_code < 500
    except Exception:
        return False


def detect_running_mcp_docker_container() -> bool:
    """Best-effort detection of a running Circuitron MCP docker container.

    This looks for known image/name identifiers in `docker ps` output. It is
    intentionally conservative and returns False on any error.
    """
    try:
        proc = subprocess.run(
            ["docker", "ps", "--format", "{{.Image}}||{{.Names}}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in proc.stdout.splitlines():
            low = line.strip().lower()
            if not low:
                continue
            # Accept either an image reference or a container name containing 'circuitron-mcp'
            if "circuitron-mcp" in low:
                return True
        return False
    except Exception:
        return False


def verify_mcp_server(ui: Any | None = None) -> bool:
    """Ensure the MCP server is running; display a friendly hint if not.

    Returns True when the server is reachable. When not available, prints a
    short instruction to start the server and returns False.
    """
    # Allow opt-out via env in special environments/tests
    if os.getenv("CIRCUITRON_SKIP_MCP_CHECK") in {"1", "true", "yes"}:
        return True

    if is_mcp_server_available():
        return True

    # Differentiate between "container present but booting" and "not running"
    container_seen = detect_running_mcp_docker_container()
    msg_lines: list[str] = []
    if not container_seen:
        msg_lines.append("Circuitron MCP server is not running.")
    else:
        msg_lines.append("Circuitron MCP server container detected but not responding yet.")
        msg_lines.append("It may still be starting up; please wait a few seconds and retry.")

    msg_lines.append(
        "Start it (or ensure it's up) with:\n  docker run --env-file mcp.env -p 8051:8051 ghcr.io/shaurya-sethi/circuitron-mcp:latest"
    )
    message = "\n".join(msg_lines)
    _display_error(message, ui=ui)
    return False


__all__ = [
    "check_internet_connection",
    "is_connected",
    "is_mcp_server_available",
    "detect_running_mcp_docker_container",
    "verify_mcp_server",
    "httpx",
]
