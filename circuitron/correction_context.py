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
    erc_issue_types: Dict[str, int] = field(default_factory=dict)
    resolved_issues: List[str] = field(default_factory=list)
    failed_strategies: List[str] = field(default_factory=list)
    successful_strategies: List[str] = field(default_factory=list)
    current_phase: Literal["validation", "erc"] = "validation"
    max_attempts: int = 3

    def _parse_erc_messages(
        self, erc_result: Dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Extract warning and error lines from ERC output."""

        warnings: list[str] = []
        errors: list[str] = []
        stdout = str(erc_result.get("stdout", ""))
        for line in stdout.splitlines():
            uline = line.upper()
            if "WARNING" in uline:
                warnings.append(line.strip())
                self.erc_issue_types["WARNING"] = (
                    self.erc_issue_types.get("WARNING", 0) + 1
                )
            if "ERROR" in uline:
                errors.append(line.strip())
                self.erc_issue_types["ERROR"] = self.erc_issue_types.get("ERROR", 0) + 1
        return warnings, errors

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

    def add_erc_attempt(
        self, erc_result: Dict[str, Any], corrections: List[str]
    ) -> None:
        """Record an ERC attempt and its results."""

        self.current_phase = "erc"
        self.erc_attempts += 1
        warnings, errors = self._parse_erc_messages(erc_result)
        self.erc_issues_history.append(
            {
                "attempt": self.erc_attempts,
                "erc_result": erc_result,
                "warnings": warnings,
                "errors": errors,
                "corrections": corrections,
            }
        )
        if not warnings and not errors and corrections:
            self.successful_strategies.extend(corrections)
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
                lines.append(f"- {line}{issue.get('category')}: {issue.get('message')}")
        if self.current_phase == "erc" and self.erc_issues_history:
            last_erc = self.erc_issues_history[-1]
            lines.append("Latest ERC issues:")
            issues = last_erc.get("errors", []) + last_erc.get("warnings", [])
            if issues:
                lines.extend(f"- {m}" for m in issues)
            else:
                lines.append(str(last_erc.get("erc_result")))
            if last_erc.get("corrections"):
                lines.append("Corrections applied:")
                lines.extend(f"- {c}" for c in last_erc["corrections"])
            if len(self.erc_issues_history) > 1:
                lines.append("Previous ERC attempts summary:")
                lines.append(self.get_erc_summary_for_agent())
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

    def get_erc_summary_for_agent(self, limit: int = 3) -> str:
        """Return a concise summary of previous ERC attempts."""

        if not self.erc_issues_history:
            return "No previous ERC attempts."

        lines: list[str] = []
        for entry in self.erc_issues_history[-limit:]:
            lines.append(f"Attempt {entry['attempt']}:")
            for msg in entry.get("errors", []):
                lines.append(f"- ERROR: {msg}")
            for msg in entry.get("warnings", []):
                lines.append(f"- WARNING: {msg}")
            for corr in entry.get("corrections", []):
                lines.append(f"  correction: {corr}")
        if self.erc_issue_types:
            lines.append("Common issue counts:")
            for name, count in sorted(self.erc_issue_types.items()):
                lines.append(f"- {name}: {count}")
        if self.successful_strategies:
            lines.append("Successful strategies:")
            lines.extend(f"- {s}" for s in self.successful_strategies)
        return "\n".join(lines)
