"""Progress reporting interfaces for headless-friendly execution.

Defines a minimal ProgressSink protocol that decouples the core pipeline
from any specific UI. A NullProgressSink is provided for headless runs.
"""

from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from .models import PlanOutput, SelectedPart, PartSearchResult


@runtime_checkable
class ProgressSink(Protocol):
    """Protocol for reporting progress, messages, and artifacts.

    Implementations may render to a terminal, publish events, or no-op.
    """

    # Stages
    def start_stage(self, name: str) -> None: ...
    def finish_stage(self, name: str) -> None: ...

    # Artifacts and summaries
    def display_plan(self, plan: PlanOutput) -> None: ...
    def display_found_parts(self, found: Iterable[PartSearchResult]) -> None: ...
    def display_selected_parts(self, parts: Iterable[SelectedPart]) -> None: ...
    def display_validation_summary(self, summary: str) -> None: ...
    def display_files(self, files: Iterable[str]) -> None: ...
    def display_code(self, code: str, language: str = "python") -> None: ...

    # Messages
    def display_info(self, message: str) -> None: ...
    def display_warning(self, message: str) -> None: ...
    def display_error(self, message: str) -> None: ...


class NullProgressSink:
    """No-op sink for headless or silent operation."""

    def start_stage(self, name: str) -> None:  # pragma: no cover - trivial no-op
        pass

    def finish_stage(self, name: str) -> None:  # pragma: no cover - trivial no-op
        pass

    def display_plan(self, plan: PlanOutput) -> None:  # pragma: no cover
        pass

    def display_found_parts(self, found: Iterable[PartSearchResult]) -> None:  # pragma: no cover
        pass

    def display_selected_parts(self, parts: Iterable[SelectedPart]) -> None:  # pragma: no cover
        pass

    def display_validation_summary(self, summary: str) -> None:  # pragma: no cover
        pass

    def display_files(self, files: Iterable[str]) -> None:  # pragma: no cover
        pass

    def display_code(self, code: str, language: str = "python") -> None:  # pragma: no cover
        pass

    def display_info(self, message: str) -> None:  # pragma: no cover
        pass

    def display_warning(self, message: str) -> None:  # pragma: no cover
        pass

    def display_error(self, message: str) -> None:  # pragma: no cover
        pass


__all__ = ["ProgressSink", "NullProgressSink"]
