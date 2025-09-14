"""Setup runner to initialize Circuitron knowledge bases via MCP tools.

This module provides an isolated, one-time setup flow that crawls SKiDL docs
into Supabase and parses the SKiDL repository into Neo4j using MCP tools.
"""

from __future__ import annotations

import asyncio
import time
from typing import Tuple

from .network import check_internet_connection
from .ui.components import panel
from .ui.app import TerminalUI
from .setup_agent import get_setup_agent
from .debug import run_agent
from .models import SetupOutput


async def _connect_server(server: object, timeout: float) -> None:
    """Connect an MCP server with a timeout."""

    await asyncio.wait_for(server.connect(), timeout=timeout)  # type: ignore[attr-defined]


async def _cleanup_server(server: object) -> None:
    """Cleanup server; log/ignore any errors."""

    try:
        await server.cleanup()  # type: ignore[attr-defined]
    except Exception:
        pass


async def run_setup(
    docs_url: str,
    repo_url: str,
    *,
    ui: TerminalUI | None = None,
    timeout: float | None = None,
) -> SetupOutput:
    """Run the Setup Agent to populate Supabase and Neo4j.

    Args:
        docs_url: Base URL for SKiDL documentation (crawled into Supabase).
        repo_url: Git repository URL for the SKiDL source (parsed into Neo4j).
        ui: Optional TerminalUI for progress display.
        timeout: Optional network timeout override in seconds.

    Returns:
        SetupOutput summarizing the setup outcome.
    """

    if not check_internet_connection():
        raise RuntimeError("No internet connection; cannot perform setup.")

    agent, server = get_setup_agent()
    # Use the current settings timeout if none provided
    from .config import settings

    to = float(timeout) if timeout is not None else float(settings.network_timeout)
    started = time.perf_counter()

    # Minimal, explicit input for the agent to consume
    input_text = (
        "SETUP REQUEST\n"
        f"docs_url: {docs_url}\n"
        f"repo_url: {repo_url}\n"
        "Please perform idempotent initialization as instructed."
    )

    if ui:
        ui.start_stage("Setup")
    await _connect_server(server, to)
    try:
        result = await run_agent(agent, input_text)
        out = result.final_output
        if not isinstance(out, SetupOutput):
            raise RuntimeError("Setup agent did not return SetupOutput")
        # Augment elapsed time if agent omitted it
        if not out.elapsed_seconds:
            out.elapsed_seconds = time.perf_counter() - started
        if ui:
            summary_lines = [
                f"Docs: {out.docs_url} — {out.supabase_status}",
                f"Repo: {out.repo_url} — {out.neo4j_status}",
            ]
            if out.warnings:
                summary_lines.append("Warnings:\n- " + "\n- ".join(out.warnings))
            if out.errors:
                summary_lines.append("Errors:\n- " + "\n- ".join(out.errors))
            panel.show_panel(ui.console, "Setup Summary", "\n".join(summary_lines))
        return out
    finally:
        await _cleanup_server(server)
        if ui:
            ui.finish_stage("Setup")


__all__ = ["run_setup"]

