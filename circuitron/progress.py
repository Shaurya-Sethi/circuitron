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
    def start_stage(self, name: str) -> None:
        """Mark the beginning of a named stage.

        Args:
            name: Human-friendly stage name (e.g., "Planning").
        """
        ...

    def finish_stage(self, name: str) -> None:
        """Mark the completion of a named stage.

        Implementations should stop any progress indicators started by
        start_stage and reset transient UI state.

        Args:
            name: The stage name previously passed to start_stage.
        """
        ...

    # Artifacts and summaries
    def display_plan(self, plan: PlanOutput) -> None:
        """Render a concise summary of the generated plan."""
        ...

    def display_found_parts(self, found: Iterable[PartSearchResult]) -> None:
        """Show components/footprints found by the search stage."""
        ...

    def display_selected_parts(self, parts: Iterable[SelectedPart]) -> None:
        """Show final part selections and important pin details."""
        ...

    def display_validation_summary(self, summary: str) -> None:
        """Display validator output or a short status summary."""
        ...

    def display_files(self, files: Iterable[str]) -> None:
        """List generated file paths or links to artifacts."""
        ...

    def display_code(self, code: str, language: str = "python") -> None:
        """Show code in a viewer or stream it to logs."""
        ...

    # Messages
    def display_info(self, message: str) -> None:
        """Show an informational message to the user/log."""
        ...

    def display_warning(self, message: str) -> None:
        """Show a non-fatal warning that may need attention."""
        ...

    def display_error(self, message: str) -> None:
        """Show an error message indicating a failure or blocker."""
        ...


class NullProgressSink:
    """No-op sink for headless or silent operation."""

    def start_stage(self, name: str) -> None:  # pragma: no cover - trivial no-op
        ...

    def finish_stage(self, name: str) -> None:  # pragma: no cover - trivial no-op
        ...

    def display_plan(self, plan: PlanOutput) -> None:  # pragma: no cover
        ...

    def display_found_parts(self, found: Iterable[PartSearchResult]) -> None:  # pragma: no cover
        ...

    def display_selected_parts(self, parts: Iterable[SelectedPart]) -> None:  # pragma: no cover
        ...

    def display_validation_summary(self, summary: str) -> None:  # pragma: no cover
        ...

    def display_files(self, files: Iterable[str]) -> None:  # pragma: no cover
        ...

    def display_code(self, code: str, language: str = "python") -> None:  # pragma: no cover
        ...

    def display_info(self, message: str) -> None:  # pragma: no cover
        ...

    def display_warning(self, message: str) -> None:  # pragma: no cover
        ...

    def display_error(self, message: str) -> None:  # pragma: no cover
        ...


__all__ = ["ProgressSink", "NullProgressSink"]
