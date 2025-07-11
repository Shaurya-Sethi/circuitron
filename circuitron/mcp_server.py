"""Utilities to manage the MCP server Docker container."""

from __future__ import annotations

import atexit
import logging
import os
import subprocess
import time
import urllib.request
from typing import Any

CONTAINER_NAME = "circuitron-mcp"
IMAGE = "ghcr.io/shaurya-sethi/circuitron-mcp:latest"


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def _health_check(url: str) -> bool:
    """Check if the MCP server is reachable via its SSE endpoint."""
    try:
        with urllib.request.urlopen(f"{url}/sse", timeout=5):
            pass
        return True
    except Exception:
        return False


def is_running(url: str) -> bool:
    return _health_check(url)


def _container_status() -> str | None:
    proc = _run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name={CONTAINER_NAME}",
            "--format",
            "{{.Status}}",
        ],
    )
    if proc.returncode != 0:
        logging.warning("docker ps failed: %s", proc.stderr.strip())
        return None
    return proc.stdout.strip() or None


def _remove_container() -> None:
    _run(["docker", "rm", "-f", CONTAINER_NAME])


def start() -> bool:
    """Start the MCP Docker container if it is not running."""
    url = os.getenv("MCP_URL", "http://localhost:8051")
    if is_running(url):
        return True

    status = _container_status()
    if status:
        if status.lower().startswith("up"):
            if is_running(url):
                return True
        _remove_container()

    env_vars = {
        k: os.getenv(k, v)
        for k, v in {
            "OPENAI_API_KEY": "",
            "SUPABASE_URL": "",
            "SUPABASE_SERVICE_KEY": "",
            "NEO4J_URI": "",
            "NEO4J_USER": "",
            "NEO4J_PASSWORD": "",
            "HOST": "0.0.0.0",
            "PORT": "8051",
            "TRANSPORT": "sse",
            "MODEL_CHOICE": "gpt-4.1-nano",
            "USE_CONTEXTUAL_EMBEDDINGS": "true",
            "USE_HYBRID_SEARCH": "true",
            "USE_AGENTIC_RAG": "true",
            "USE_RERANKING": "true",
            "USE_KNOWLEDGE_GRAPH": "true",
            "LLM_MAX_CONCURRENCY": "2",
            "LLM_REQUEST_DELAY": "0.5",
        }.items()
    }

    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        CONTAINER_NAME,
        "-p",
        "8051:8051",
    ]
    for k, v in env_vars.items():
        if v:
            cmd.extend(["-e", f"{k}={v}"])
    cmd.append(IMAGE)

    proc = _run(cmd)
    if proc.returncode != 0:
        logging.error("Failed to start MCP container: %s", proc.stderr.strip())
        return False

    max_attempts = int(os.getenv("MCP_START_MAX_ATTEMPTS", "20"))
    for _ in range(max_attempts):
        time.sleep(1)
        if is_running(url):
            atexit.register(stop)
            return True
    logging.error("MCP server failed to start after %s seconds", max_attempts)
    return False


def stop() -> None:
    """Stop the MCP Docker container."""
    _remove_container()


def ensure_running() -> bool:
    """Ensure the MCP server is available."""
    url = os.getenv("MCP_URL", "http://localhost:8051")
    if is_running(url):
        return True
    return start()


__all__ = ["ensure_running", "start", "stop", "is_running"]
