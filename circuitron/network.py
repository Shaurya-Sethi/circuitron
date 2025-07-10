"""Network utilities for Circuitron."""

from __future__ import annotations

import httpx


def is_connected(url: str = "https://api.openai.com", timeout: float = 3.0) -> bool:
    """Return ``True`` if ``url`` is reachable within ``timeout`` seconds."""
    try:
        httpx.head(url, timeout=timeout)
        return True
    except httpx.HTTPError:
        return False


def check_internet_connection() -> bool:
    """Check for internet connectivity and print a message when absent."""
    if not is_connected():
        print("No internet connection detected. Please connect and try again.")
        return False
    return True

__all__ = ["check_internet_connection", "is_connected"]
