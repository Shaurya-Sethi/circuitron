"""Network utilities for Circuitron.

Pure helpers suitable for headless environments. No UI side-effects here.
"""

from __future__ import annotations

import socket
import httpx
import asyncio


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
    """Return ``True`` if an outbound connection to the default URL succeeds.

    This function intentionally performs no UI/printing to support headless use.
    Callers should decide how to surface connectivity errors.
    """
    return is_connected()

__all__ = ["check_internet_connection", "is_connected", "is_connected_async"]
def _suppress_unused() -> None:  # pragma: no cover - compatibility shim
    # Retain old export for backwards compatibility without encouraging use
    _ = httpx


async def is_connected_async(url: str = "https://api.openai.com", timeout: float = 10.0) -> bool:
    """Asynchronously check whether ``url`` is reachable.

    Mirrors :func:`is_connected` using httpx.AsyncClient to avoid blocking
    the event loop during connectivity checks.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            await client.head(url)
        return True
    except (httpx.RequestError, socket.gaierror, TimeoutError, OSError):
        return False

