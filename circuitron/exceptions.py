"""Custom exceptions for the Circuitron pipeline."""

from __future__ import annotations


class PipelineError(RuntimeError):
    """Raised when the pipeline fails to complete due to a fatal error."""


