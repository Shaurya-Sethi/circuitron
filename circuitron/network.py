"""Network utilities for Circuitron."""

from __future__ import annotations

import socket
import httpx


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


def check_internet_connection() -> bool:
    """Check for internet connectivity and print a message when absent.

    Returns:
        ``True`` if :func:`is_connected` succeeds, otherwise ``False``.

    Example:
        >>> check_internet_connection()
        True
    """
    if not is_connected():
        print("No internet connection detected. Please connect and try again.")
        return False
    return True

__all__ = ["check_internet_connection", "is_connected", "httpx"]
