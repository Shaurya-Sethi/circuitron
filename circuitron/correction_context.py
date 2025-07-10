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
        """Extract warning and error lines from ERC output.
        
        SKiDL ERC output format:
        - "X warnings found during ERC."
        - "X errors found during ERC."
        - Individual warning/error messages with "WARNING:" or "ERROR:" prefixes
        """

        warnings: list[str] = []
        errors: list[str] = []
        stdout = str(erc_result.get("stdout", ""))
        
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # Skip summary lines, focus on actual messages
            if "warnings found during ERC" in line.lower():
                continue
            if "errors found during ERC" in line.lower():
                continue
                
            # Capture actual warning/error messages that start with the prefix
            if line.startswith("WARNING:"):
                warnings.append(line)
                self.erc_issue_types["WARNING"] = (
                    self.erc_issue_types.get("WARNING", 0) + 1
                )
            elif line.startswith("ERROR:"):
                errors.append(line)
                self.erc_issue_types["ERROR"] = self.erc_issue_types.get("ERROR", 0) + 1
                
        return warnings, errors

    def add_validation_attempt(
        self, validation: CodeValidationOutput, corrections: List[str]
    ) -> None:
        """Record a validation attempt and its issues."""

        self.current_phase = "validation"
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
        # Mark strategies as successful if errors are reduced or warnings are reduced
        if corrections:
            # Previous attempt comparison
            if len(self.erc_issues_history) > 1:
                prev_entry = self.erc_issues_history[-2]
                prev_errors = len(prev_entry.get("errors", []))
                prev_warnings = len(prev_entry.get("warnings", []))
                current_errors = len(errors)
                current_warnings = len(warnings)
                
                # Strategy is successful if errors decreased or warnings decreased
                if current_errors < prev_errors or current_warnings < prev_warnings:
                    self.successful_strategies.extend(corrections)
            elif not errors:  # First attempt and no errors
                self.successful_strategies.extend(corrections)
        
        # Special handling for warnings-only status
        if not errors and warnings:
            # Check if agent explicitly approved warnings (this will be set by pipeline)
            if any("warnings approved" in str(c).lower() for c in corrections):
                self.mark_issue_resolved("erc_warnings")
                
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
                prev_issues = self.validation_issues_history[-2]["issues"]
                last_issues = self.validation_issues_history[-1]["issues"]
                # Compare issue contents, not object references
                if self._issues_are_identical(prev_issues, last_issues):
                    return False
            return True
        if self.erc_attempts >= self.max_attempts:
            return False
        if len(self.erc_issues_history) >= 2:
            prev_result = self.erc_issues_history[-2]["erc_result"]
            last_result = self.erc_issues_history[-1]["erc_result"]
            # Compare ERC result contents, not object references
            if self._erc_results_are_identical(prev_result, last_result):
                return False
        return True

    def _issues_are_identical(self, issues1: List[Dict[str, Any]], issues2: List[Dict[str, Any]]) -> bool:
        """Compare two lists of validation issues for equality."""
        if len(issues1) != len(issues2):
            return False
        for i1, i2 in zip(issues1, issues2):
            if (i1.get("line") != i2.get("line") or 
                i1.get("category") != i2.get("category") or 
                i1.get("message") != i2.get("message")):
                return False
        return True

    def _erc_results_are_identical(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> bool:
        """Compare two ERC results for equality."""
        # Compare key fields that indicate if the same errors/warnings persist
        # Now we care about both errors and warnings since we try to fix warnings
        stdout1 = result1.get("stdout", "")
        stdout2 = result2.get("stdout", "")
        
        # Extract error and warning counts from stdout for comparison
        import re
        error_pattern = r'(\d+) errors found during ERC'
        warning_pattern = r'(\d+) warnings found during ERC'
        
        error1 = re.search(error_pattern, stdout1)
        error2 = re.search(error_pattern, stdout2)
        warning1 = re.search(warning_pattern, stdout1)
        warning2 = re.search(warning_pattern, stdout2)
        
        error_count1 = int(error1.group(1)) if error1 else 0
        error_count2 = int(error2.group(1)) if error2 else 0
        warning_count1 = int(warning1.group(1)) if warning1 else 0
        warning_count2 = int(warning2.group(1)) if warning2 else 0
        
        # Compare success status, ERC pass status, error counts, and warning counts
        # Now we compare warning counts too since we try to address warnings
        return (result1.get("success") == result2.get("success") and
                result1.get("erc_passed") == result2.get("erc_passed") and
                error_count1 == error_count2 and
                warning_count1 == warning_count2 and
                result1.get("stderr") == result2.get("stderr"))

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

    def has_no_issues(self) -> bool:
        """Check if the latest ERC attempt has no errors or warnings."""
        if not self.erc_issues_history:
            return False
        
        last_erc = self.erc_issues_history[-1]
        errors = last_erc.get("errors", [])
        warnings = last_erc.get("warnings", [])
        
        return len(errors) == 0 and len(warnings) == 0

    def agent_approved_warnings(self) -> bool:
        """Check if the latest ERC attempt has agent-approved warnings."""
        if not self.erc_issues_history:
            return False
        
        last_erc = self.erc_issues_history[-1]
        corrections = last_erc.get("corrections", [])
        
        # Check if any correction indicates warnings are acceptable
        for correction in corrections:
            if any(phrase in correction.lower() for phrase in [
                "warnings are acceptable",
                "warnings can be ignored", 
                "warnings are intentional",
                "suppress warnings",
                "do_erc = false",
                "warnings only"
            ]):
                return True
        return False
