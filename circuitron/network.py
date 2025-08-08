"""Network utilities for Circuitron.

Pure helpers suitable for headless environments. No UI side-effects here.
"""

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
    """Return ``True`` if an outbound connection to the default URL succeeds.

    This function intentionally performs no UI/printing to support headless use.
    Callers should decide how to surface connectivity errors.
    """
    return is_connected()

__all__ = ["check_internet_connection", "is_connected"]
