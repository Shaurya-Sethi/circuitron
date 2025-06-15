from __future__ import annotations

import logging

import structlog


def get_logger() -> structlog.BoundLogger:
    """Return application logger."""
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
    return structlog.get_logger()
