"""Reduce bounded execution observations into public advisory gaps."""

from __future__ import annotations

from dataclasses import dataclass

from .closure_evidence_summary import (
    ac_proven_by_lines,
    classify_user_requested_gate,
    find_internal_unawareness_violations,
    validate_repair_rereview_text,
    validate_task_review_text,
)
from .plan_execution_observer import PlanExecutionObservation


@dataclass(frozen=True)
class EngineeringQualityReport:
    """Natural-language advisory report for ordinary handoff use."""

    status: str
    observed_gaps: tuple[str, ...]
    recommended_next_actions: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_public_dict(self) -> dict[str, object]:
        return {
            "engineering_quality_report": {
                "status": self.status,
                "observed_gaps": list(self.observed_gaps),
                "recommended_next_actions": list(self.recommended_next_actions),
            }
        }

    def to_public_text(self) -> str:
        lines = ["engineering_quality_report:", f"  status: {self.status}"]
        lines.append("  observed_gaps:")
        if self.observed_gaps:
            lines.extend(f"    - {gap}" for gap in self.observed_gaps)
        else:
            lines.append("    - none_detected")
        lines.append("  recommended_next_actions:")
        if self.recommended_next_actions:
            lines.extend(f"    - {action}" for action in self.recommended_next_actions)
        else:
            lines.append("    - no_next_action")
        return "\n".join(lines)


def reduce_execution_evidence(observation: PlanExecutionObservation) -> EngineeringQualityReport:
    """Summarize execution risks without exposing internal runtime state."""

    gaps: list[str] = []
    actions: list[str] = []

    changed = set(observation.changed_files)
    planned = set(observation.planned_files)
    extra_files = sorted(changed - planned) if planned else []
    if changed and not planned:
        gaps.append("Plan-execution consistency could not be checked because accepted plan files were not visible.")
        actions.append("Include accepted plan files in the visible plan handoff or disclose plan drift status.")
    if extra_files:
        gaps.append(f"Changed files are outside the accepted plan: {', '.join(extra_files[:8])}.")
        actions.append("Explain the plan variance, review the added files, and map validation to them.")

    if changed and not observation.validation_commands:
        gaps.append("Changed files are visible, but no validation command is visible after implementation.")
        actions.append("Run the affected validation command or disclose not-run status with residual risk.")
    elif changed and observation.validation_fresh_after_last_edit is not True:
        gaps.append("Validation evidence is missing or not fresh after the final material edit.")
        actions.append("Re-run the affected validation command after the final edit.")

    review = validate_task_review_text(observation.review_text)
    if changed and observation.review_text and not review.passed:
        gaps.append("Review evidence is incomplete: " + ", ".join(review.missing) + ".")
        actions.append("Review spec compliance, code quality, reviewed scope, findings, next action, and residual risk.")
    elif changed and not observation.review_text:
        gaps.append("Review evidence is missing for the changed task.")
        actions.append("Request or perform independent task review before final closure.")

    repair = "\n".join(part for part in (observation.review_text, observation.repair_text, observation.rereview_text) if part)
    repair_result = validate_repair_rereview_text(repair)
    if not repair_result.passed:
        gaps.append("Repair is visible, but matching re-review evidence is missing.")
        actions.append("Run targeted re-review for the repaired finding before closure.")

    gate = classify_user_requested_gate(observation.user_gate_text)
    if gate.is_user_requested and not ac_proven_by_lines(observation.final_handoff):
        gaps.append("User-requested verification gate lacks AC -> PROVEN BY evidence.")
        actions.append("Report each acceptance criterion with the command, result, or artifact that proves it.")

    violations = find_internal_unawareness_violations(observation.final_handoff)
    if violations:
        gaps.append("Handoff mentions rd-skills internal control artifacts: " + ", ".join(violations[:5]) + ".")
        actions.append("Rewrite the handoff as ordinary engineering evidence and residual risk.")

    return EngineeringQualityReport(
        status="pass" if not gaps else "advisory_risk",
        observed_gaps=tuple(dict.fromkeys(gaps)),
        recommended_next_actions=tuple(dict.fromkeys(actions)),
    )
