"""Network utilities for Circuitron."""

from __future__ import annotations

import socket
import httpx


def is_connected(url: str = "https://api.openai.com", timeout: float = 3.0) -> bool:
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


async def async_health_check(url: str, timeout: float = 10.0) -> bool:
    """Asynchronously check server health via a HEAD request."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.head(url)
            return response.status_code < 400
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError, socket.gaierror, TimeoutError, OSError):
        return False


def classify_connection_error(exc: Exception) -> str:
    """Return a short classification string for connection-related errors."""
    if isinstance(exc, httpx.ConnectError):
        return "connection_refused"
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.RequestError):
        return "request_error"
    return exc.__class__.__name__


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

__all__ = [
    "check_internet_connection",
    "is_connected",
    "async_health_check",
    "classify_connection_error",
]
