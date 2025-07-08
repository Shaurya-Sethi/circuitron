"""Tracking utilities for code correction attempts.

This module defines the :class:`CorrectionContext` used by the pipeline to
keep track of validation and ERC correction history. The context object is
passed to the correction agents so they can reason about what has already
been tried and which issues remain unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from .models import CodeValidationOutput


@dataclass
class CorrectionContext:
    """Track correction attempts across validation and ERC phases."""

    validation_attempts: int = 0
    erc_attempts: int = 0
    validation_issues_history: List[Dict[str, Any]] = field(default_factory=list)
    erc_issues_history: List[Dict[str, Any]] = field(default_factory=list)
    resolved_issues: List[str] = field(default_factory=list)
    failed_strategies: List[str] = field(default_factory=list)
    current_phase: Literal["validation", "erc"] = "validation"
    max_attempts: int = 3

    def add_validation_attempt(
        self, validation: CodeValidationOutput, corrections: List[str]
    ) -> None:
        """Record a validation attempt and its issues."""

        self.validation_attempts += 1
        issues = [issue.model_dump() for issue in validation.issues]
        self.validation_issues_history.append(
            {
                "attempt": self.validation_attempts,
                "issues": issues,
                "corrections": corrections,
            }
        )
        if validation.status == "pass":
            self.mark_issue_resolved("validation")

    def add_erc_attempt(self, erc_result: Dict[str, Any], corrections: List[str]) -> None:
        """Record an ERC attempt and its results."""

        self.current_phase = "erc"
        self.erc_attempts += 1
        self.erc_issues_history.append(
            {
                "attempt": self.erc_attempts,
                "erc_result": erc_result,
                "corrections": corrections,
            }
        )
        if erc_result.get("erc_passed", False):
            self.mark_issue_resolved("erc")

    def get_context_for_next_attempt(self) -> str:
        """Return formatted context for the next correction attempt."""

        lines: List[str] = []
        lines.append(f"Current phase: {self.current_phase}")
        lines.append(f"Validation attempts: {self.validation_attempts}")
        lines.append(f"ERC attempts: {self.erc_attempts}")
        if self.resolved_issues:
            lines.append("Resolved issues:")
            lines.extend(f"- {issue}" for issue in self.resolved_issues)
        if self.failed_strategies:
            lines.append("Previously failed strategies:")
            lines.extend(f"- {s}" for s in self.failed_strategies)
        if self.current_phase == "validation" and self.validation_issues_history:
            last = self.validation_issues_history[-1]
            lines.append("Latest validation issues:")
            for issue in last["issues"]:
                line = f"line {issue.get('line')}: " if issue.get("line") else ""
                lines.append(
                    f"- {line}{issue.get('category')}: {issue.get('message')}"
                )
        if self.current_phase == "erc" and self.erc_issues_history:
            last_erc = self.erc_issues_history[-1]
            lines.append("Latest ERC result:")
            lines.append(str(last_erc.get("erc_result")))
        return "\n".join(lines)

    def should_continue_attempts(self) -> bool:
        """Decide whether further attempts should be made."""

        if self.current_phase == "validation":
            if self.validation_attempts >= self.max_attempts:
                return False
            if len(self.validation_issues_history) >= 2:
                prev = self.validation_issues_history[-2]["issues"]
                last = self.validation_issues_history[-1]["issues"]
                if prev == last:
                    return False
            return True
        if self.erc_attempts >= self.max_attempts:
            return False
        if len(self.erc_issues_history) >= 2:
            prev = self.erc_issues_history[-2]["erc_result"]
            last = self.erc_issues_history[-1]["erc_result"]
            if prev == last:
                return False
        return True

    def mark_issue_resolved(self, issue: str) -> None:
        """Mark an issue as resolved."""

        if issue not in self.resolved_issues:
            self.resolved_issues.append(issue)

    def track_failed_strategy(self, strategy: str) -> None:
        """Record a failed correction strategy."""

        if strategy not in self.failed_strategies:
            self.failed_strategies.append(strategy)
