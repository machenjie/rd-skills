"""Bounded process phase ledger for runtime-enforced ChangeForge workflow."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from .privacy import cap_list, normalize_relative_path, redact_sensitive_value, validate_bounded_fact


CORE_PHASES = ("pdd", "ddd", "sdd", "tdd")
WORKFLOW_PHASES = (
    "pdd",
    "ddd",
    "sdd",
    "tdd",
    "implementation",
    "validation",
    "review",
    "repair",
    "rereview",
    "closure",
)
PHASE_STATUSES = (
    "pending",
    "draft",
    "review_pending",
    "reviewed",
    "failed",
    "waived",
    "not_applicable",
)
REVIEW_VERDICTS = ("pass", "fail", "needs_user_choice", "insufficient_evidence")
BLOCKING_SEVERITIES = {"critical", "high"}
PASSING_REVIEW_SCORE = 4
MAX_BLOCKERS = 25
MAX_PHASE_TEXT = 300

_HASH_RE = re.compile(r"^sha256:[A-Fa-f0-9]{12,64}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_FORBIDDEN_KEYS = {
    "prompt",
    "raw_prompt",
    "raw_user_prompt",
    "raw_command",
    "command_output",
    "stdout",
    "stderr",
    "environment",
    "env",
    "secret",
    "token",
    "password",
    "credentials",
    "api_key",
}


def artifact_digest(artifact: object) -> str:
    """Return a stable digest for a phase artifact without retaining the artifact."""
    payload = json.dumps(artifact, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sanitize_phase_ledger(ledger: dict[str, Any] | None) -> dict[str, Any]:
    """Return a privacy-safe, schema-bounded process phase ledger."""
    source = ledger if isinstance(ledger, dict) else {}
    route_id = _safe_scalar(source.get("route_id")) or "active-runtime-route"
    current_phase = _enum(source.get("current_phase"), WORKFLOW_PHASES, default="pdd")
    required_phases = [
        phase for phase in cap_list(source.get("required_phases"), max_items=8) if phase in CORE_PHASES
    ] or list(CORE_PHASES)
    result: dict[str, Any] = {
        "schema_version": 1,
        "route_id": route_id,
        "current_phase": current_phase,
        "required_phases": required_phases,
        "phase_status": _sanitize_phase_status(source.get("phase_status"), required_phases),
        "phase_scores": _sanitize_phase_scores(source.get("phase_scores")),
        "artifact_digests": _sanitize_digest_map(source.get("artifact_digests")),
        "review_ids": _sanitize_id_map(source.get("review_ids")),
        "blockers": _sanitize_blockers(source.get("blockers")),
        "unresolved_blocking_choices": _safe_int(source.get("unresolved_blocking_choices")),
        "validation_signal_present": bool(source.get("validation_signal_present")),
        "updated_by_hook": _safe_scalar(source.get("updated_by_hook")) or "",
    }
    not_applicable_reasons = _sanitize_reason_map(source.get("not_applicable_reasons"))
    if not_applicable_reasons:
        result["not_applicable_reasons"] = not_applicable_reasons
    degraded_evidence = cap_list(source.get("degraded_evidence"), max_items=25)
    if degraded_evidence:
        result["degraded_evidence"] = degraded_evidence
    return result


def normalize_process_phase_ledger(
    ledger: dict[str, Any] | None = None,
    *,
    route_id: str = "active-runtime-route",
    current_phase: str = "pdd",
    required_phases: list[str] | None = None,
) -> dict[str, Any]:
    """Normalize a partial ledger or create an empty ledger."""
    base = {
        "schema_version": 1,
        "route_id": route_id,
        "current_phase": current_phase,
        "required_phases": required_phases or list(CORE_PHASES),
    }
    if isinstance(ledger, dict):
        base.update(ledger)
    return sanitize_phase_ledger(base)


def merge_process_phase_ledger(
    current: dict[str, Any] | None,
    update: dict[str, Any] | None,
    *,
    phase_review_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Merge a partial ledger update and recompute reviewed phase facts."""
    merged = normalize_process_phase_ledger(current)
    raw_update = update if isinstance(update, dict) else {}
    update_clean = sanitize_phase_ledger(raw_update)
    for key in (
        "route_id",
        "current_phase",
        "required_phases",
        "unresolved_blocking_choices",
        "validation_signal_present",
        "updated_by_hook",
    ):
        if key in raw_update and update_clean.get(key) not in ("", [], None):
            merged[key] = update_clean[key]
    for key in ("phase_status", "phase_scores", "artifact_digests", "review_ids"):
        if key in raw_update:
            merged[key] = {**dict(merged.get(key) or {}), **dict(update_clean.get(key) or {})}
    if "not_applicable_reasons" in raw_update and update_clean.get("not_applicable_reasons"):
        merged["not_applicable_reasons"] = {
            **dict(merged.get("not_applicable_reasons") or {}),
            **dict(update_clean.get("not_applicable_reasons") or {}),
        }
    if "blockers" in raw_update:
        blockers = _unique_blockers([*_list_dicts(merged.get("blockers")), *_list_dicts(update_clean.get("blockers"))])
        merged["blockers"] = blockers[:MAX_BLOCKERS]
    merged = sanitize_phase_ledger(merged)
    if phase_review_results:
        merged = _apply_phase_reviews(merged, phase_review_results)
    return sanitize_phase_ledger(merged)


def phase_transition_allowed(ledger: dict[str, Any], requested_next_phase: str) -> tuple[bool, list[str]]:
    """Return whether the requested phase transition satisfies the phase chain."""
    clean = normalize_process_phase_ledger(ledger)
    requested = str(requested_next_phase or "").strip()
    blockers: list[str] = []
    if requested not in WORKFLOW_PHASES:
        return False, [f"unknown requested phase {requested!r}"]
    if requested in {"implementation", "validation", "review", "repair", "rereview", "closure"}:
        blockers.extend(phase_blockers(clean))
    if requested == "ddd" and not _phase_complete(clean, "pdd"):
        blockers.append("PDD must be reviewed before DDD can be complete")
    if requested == "sdd" and not _phase_complete(clean, "ddd"):
        blockers.append("DDD must be reviewed before SDD can be complete")
    if requested == "tdd" and not _phase_complete(clean, "sdd"):
        blockers.append("SDD must be reviewed before TDD can be complete")
    return not blockers, blockers


def phase_ready_for_implementation(ledger: dict[str, Any]) -> bool:
    return not phase_blockers(ledger)


def phase_blockers(ledger: dict[str, Any]) -> list[str]:
    """Return implementation-blocking process phase gaps."""
    clean = normalize_process_phase_ledger(ledger)
    errors = validate_process_phase_ledger(clean)
    phase_status = dict(clean.get("phase_status") or {})
    required = [phase for phase in clean.get("required_phases", CORE_PHASES) if phase in CORE_PHASES]
    for phase in required:
        if not _phase_complete(clean, phase):
            errors.append(f"{phase.upper()} is not independently reviewed")
    if _phase_complete(clean, "sdd") and int(clean.get("unresolved_blocking_choices") or 0) > 0:
        errors.append("SDD has unresolved blocking material choices")
    if phase_status.get("sdd") == "reviewed" and int(clean.get("unresolved_blocking_choices") or 0) > 0:
        errors.append("SDD reviewed status is invalid while material choices remain unresolved")
    if phase_status.get("tdd") == "reviewed" and not clean.get("validation_signal_present"):
        errors.append("TDD reviewed status requires validation_signal_present=true")
    return _unique(errors)


def validate_process_phase_ledger(ledger: dict[str, Any]) -> list[str]:
    clean = sanitize_phase_ledger(ledger)
    errors: list[str] = []
    if clean.get("schema_version") != 1:
        errors.append("process_phase_ledger.schema_version must be 1")
    if not _safe_id(clean.get("route_id")):
        errors.append("process_phase_ledger.route_id must be a bounded identifier")
    current_phase = clean.get("current_phase")
    if current_phase not in WORKFLOW_PHASES:
        errors.append("process_phase_ledger.current_phase is invalid")
    required = clean.get("required_phases")
    if not isinstance(required, list) or not required:
        errors.append("process_phase_ledger.required_phases must be non-empty")
    status = clean.get("phase_status")
    if not isinstance(status, dict):
        errors.append("process_phase_ledger.phase_status must be an object")
        status = {}
    reasons = clean.get("not_applicable_reasons") if isinstance(clean.get("not_applicable_reasons"), dict) else {}
    for phase in CORE_PHASES:
        phase_status = status.get(phase)
        if phase_status not in PHASE_STATUSES:
            errors.append(f"phase_status.{phase} is invalid")
        if phase_status == "not_applicable" and not _safe_scalar(reasons.get(phase)):
            errors.append(f"phase_status.{phase}=not_applicable requires a specific reason")
        if phase_status == "reviewed":
            if phase not in dict(clean.get("artifact_digests") or {}):
                errors.append(f"{phase} reviewed status requires artifact digest")
            if phase not in dict(clean.get("review_ids") or {}):
                errors.append(f"{phase} reviewed status requires review_id")
    required_phases = [phase for phase in clean.get("required_phases", []) if phase in CORE_PHASES]
    if "ddd" in required_phases and status.get("ddd") == "reviewed" and not _phase_complete(clean, "pdd"):
        errors.append("PDD must be reviewed before DDD can be reviewed")
    if "sdd" in required_phases and status.get("sdd") == "reviewed" and not _phase_complete(clean, "ddd"):
        errors.append("DDD must be reviewed before SDD can be reviewed")
    if "tdd" in required_phases and status.get("tdd") == "reviewed" and not _phase_complete(clean, "sdd"):
        errors.append("SDD must be reviewed before TDD can be reviewed")
    if status.get("sdd") == "reviewed" and int(clean.get("unresolved_blocking_choices") or 0) > 0:
        errors.append("SDD reviewed requires unresolved_blocking_choices=0")
    if status.get("tdd") == "reviewed" and not clean.get("validation_signal_present"):
        errors.append("TDD reviewed requires validation_signal_present=true")
    for blocker in _list_dicts(clean.get("blockers")):
        if not blocker.get("phase") or not blocker.get("reason"):
            errors.append("process_phase_ledger.blockers entries require phase and reason")
    return _unique(errors)


def sanitize_phase_review_result(result: dict[str, Any] | None) -> dict[str, Any]:
    source = result if isinstance(result, dict) else {}
    phase = _enum(source.get("phase"), (*WORKFLOW_PHASES, "implementation", "closure"), default="")
    clean: dict[str, Any] = {
        "schema_version": 1,
        "review_id": _safe_scalar(source.get("review_id")) or "",
        "phase": phase,
        "reviewer_skill": _safe_scalar(source.get("reviewer_skill")) or "",
        "owner_skill": _safe_scalar(source.get("owner_skill")) or "",
        "reviewed_artifact_digest": _safe_digest(source.get("reviewed_artifact_digest")),
        "verdict": _enum(source.get("verdict"), REVIEW_VERDICTS, default="insufficient_evidence"),
        "score": _safe_int(source.get("score"), upper=5),
        "findings": _sanitize_review_findings(source.get("findings")),
        "approved_scope": _sanitize_approved_scope(source.get("approved_scope")),
        "not_reviewed": cap_list(source.get("not_reviewed"), max_items=25),
        "required_next_action": [
            item
            for item in cap_list(source.get("required_next_action"), max_items=8)
            if item in {"proceed", "repair", "ask_user", "run_validation"}
        ],
        "residual_risk": _sanitize_residual_risk(source.get("residual_risk")),
    }
    return clean


def validate_phase_review_result(
    review_result: dict[str, Any],
    *,
    artifact_digest: str | None = None,
) -> list[str]:
    clean = sanitize_phase_review_result(review_result)
    errors: list[str] = []
    if clean.get("schema_version") != 1:
        errors.append("phase_review_result.schema_version must be 1")
    for field in ("review_id", "phase", "reviewer_skill", "owner_skill", "reviewed_artifact_digest"):
        if not clean.get(field):
            errors.append(f"phase_review_result.{field} is required")
    if clean.get("reviewer_skill") and clean.get("owner_skill") and clean["reviewer_skill"] == clean["owner_skill"]:
        errors.append("phase_review_result reviewer_skill must differ from owner_skill")
    if clean.get("verdict") not in REVIEW_VERDICTS:
        errors.append("phase_review_result.verdict is invalid")
    if not isinstance(clean.get("score"), int) or not 0 <= int(clean.get("score") or 0) <= 5:
        errors.append("phase_review_result.score must be 0-5")
    if artifact_digest and clean.get("reviewed_artifact_digest") != artifact_digest:
        errors.append("phase_review_result reviewed_artifact_digest is stale")
    for finding in _list_dicts(clean.get("findings")):
        if not finding.get("finding_id"):
            errors.append("phase_review_result.findings entries require finding_id")
        if not finding.get("required_fix") and finding.get("blocks_next_stage"):
            errors.append(f"finding {finding.get('finding_id') or '?'} blocks next stage but has no required_fix")
    return _unique(errors)


def phase_review_passes(
    review_result: dict[str, Any],
    *,
    artifact_digest: str | None = None,
) -> bool:
    clean = sanitize_phase_review_result(review_result)
    if validate_phase_review_result(clean, artifact_digest=artifact_digest):
        return False
    if clean.get("verdict") != "pass" or int(clean.get("score") or 0) < PASSING_REVIEW_SCORE:
        return False
    if any(_finding_blocks(finding) for finding in _list_dicts(clean.get("findings"))):
        return False
    return True


def review_findings_blocking(review_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for result in review_results:
        clean = sanitize_phase_review_result(result)
        if clean.get("verdict") in {"fail", "needs_user_choice", "insufficient_evidence"}:
            findings.append(
                {
                    "finding_id": _safe_scalar(clean.get("review_id")) or f"{clean.get('phase')}-review",
                    "phase": clean.get("phase"),
                    "severity": "high",
                    "evidence": f"review verdict {clean.get('verdict')}",
                    "required_fix": "repair phase artifact or gather required evidence",
                    "blocks_next_stage": True,
                    "resolved": False,
                }
            )
        findings.extend(
            finding for finding in _list_dicts(clean.get("findings")) if _finding_blocks(finding)
        )
    return _unique_findings(findings)


def _apply_phase_reviews(
    ledger: dict[str, Any],
    phase_review_results: list[dict[str, Any]],
) -> dict[str, Any]:
    result = copy.deepcopy(ledger)
    status = dict(result.get("phase_status") or {})
    scores = dict(result.get("phase_scores") or {})
    review_ids = dict(result.get("review_ids") or {})
    digests = dict(result.get("artifact_digests") or {})
    blockers = _list_dicts(result.get("blockers"))
    latest_by_phase: dict[str, dict[str, Any]] = {}
    for review in phase_review_results:
        clean = sanitize_phase_review_result(review)
        phase = str(clean.get("phase") or "")
        if phase in CORE_PHASES:
            latest_by_phase[phase] = clean
    for phase, review in latest_by_phase.items():
        digest = str(digests.get(phase) or "")
        if phase_review_passes(review, artifact_digest=digest or None):
            status[phase] = "reviewed"
            scores[phase] = int(review.get("score") or 0)
            review_ids[phase] = review.get("review_id")
        else:
            status[phase] = "failed"
            scores[phase] = int(review.get("score") or 0)
            blockers.append(
                {
                    "phase": phase,
                    "reason": f"phase review {review.get('review_id') or 'unknown'} did not pass",
                }
            )
    result["phase_status"] = status
    result["phase_scores"] = scores
    result["review_ids"] = review_ids
    result["blockers"] = _unique_blockers(blockers)
    return result


def _sanitize_phase_status(value: object, required_phases: list[str]) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    status: dict[str, str] = {}
    for phase in CORE_PHASES:
        default = "pending" if phase in required_phases else "not_applicable"
        status[phase] = _enum(source.get(phase), PHASE_STATUSES, default=default)
    return status


def _sanitize_phase_scores(value: object) -> dict[str, int]:
    source = value if isinstance(value, dict) else {}
    return {phase: _safe_int(source.get(phase), upper=5) for phase in CORE_PHASES}


def _sanitize_digest_map(value: object) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    result: dict[str, str] = {}
    for phase in CORE_PHASES:
        digest = _safe_digest(source.get(phase))
        if digest:
            result[phase] = digest
    return result


def _sanitize_id_map(value: object) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    result: dict[str, str] = {}
    for phase in CORE_PHASES:
        text = _safe_scalar(source.get(phase))
        if text and _safe_id(text):
            result[phase] = text
    return result


def _sanitize_reason_map(value: object) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    result: dict[str, str] = {}
    for phase in CORE_PHASES:
        reason = _safe_scalar(source.get(phase))
        if reason:
            result[phase] = reason
    return result


def _sanitize_blockers(value: object) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for blocker in _list_dicts(value)[:MAX_BLOCKERS]:
        phase = _enum(blocker.get("phase"), (*WORKFLOW_PHASES, *CORE_PHASES), default="")
        reason = _safe_scalar(blocker.get("reason"))
        if phase and reason:
            result.append({"phase": phase, "reason": reason})
    return _unique_blockers(result)


def _sanitize_review_findings(value: object) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for finding in _list_dicts(value)[:MAX_BLOCKERS]:
        clean = {
            "finding_id": _safe_scalar(finding.get("finding_id")) or "",
            "severity": _enum(
                finding.get("severity"),
                ("critical", "high", "medium", "low"),
                default="medium",
            ),
            "evidence": _safe_scalar(finding.get("evidence")) or "",
            "required_fix": _safe_scalar(finding.get("required_fix")) or "",
            "blocks_next_stage": bool(finding.get("blocks_next_stage")),
        }
        if clean["finding_id"] or clean["evidence"]:
            findings.append(clean)
    return _unique_findings(findings)


def _sanitize_approved_scope(value: object) -> dict[str, list[str]]:
    source = value if isinstance(value, dict) else {}
    return {
        "files": cap_list(source.get("files"), max_items=50, item_sanitizer=normalize_relative_path),
        "behaviors": cap_list(source.get("behaviors"), max_items=25),
        "facts": cap_list(source.get("facts"), max_items=25),
    }


def _sanitize_residual_risk(value: object) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    for risk in _list_dicts(value)[:25]:
        clean = {
            "risk": _safe_scalar(risk.get("risk")) or "",
            "owner": _safe_scalar(risk.get("owner")) or "",
            "next_gate": _safe_scalar(risk.get("next_gate")) or "",
        }
        if any(clean.values()):
            risks.append(clean)
    return risks


def _phase_complete(ledger: dict[str, Any], phase: str) -> bool:
    status = dict(ledger.get("phase_status") or {})
    reasons = dict(ledger.get("not_applicable_reasons") or {})
    value = status.get(phase)
    if value in {"reviewed", "waived"}:
        return True
    if value == "not_applicable":
        return bool(_safe_scalar(reasons.get(phase)))
    return False


def _finding_blocks(finding: dict[str, Any]) -> bool:
    severity = str(finding.get("severity") or "").casefold()
    return bool(finding.get("blocks_next_stage")) or severity in BLOCKING_SEVERITIES


def _list_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_scalar(value: object) -> str:
    if _forbidden_key_value(value):
        return ""
    text = redact_sensitive_value(value)
    if not text or text == "[REDACTED]":
        return ""
    if "\n" in text or "\r" in text or "\x00" in text:
        return ""
    if len(text) > MAX_PHASE_TEXT:
        text = text[: MAX_PHASE_TEXT - 15] + "...truncated"
    return text


def _safe_digest(value: object) -> str:
    text = _safe_scalar(value)
    return text if text and _HASH_RE.match(text) else ""


def _safe_id(value: object) -> bool:
    text = str(value or "").strip()
    return bool(text and _SAFE_ID_RE.match(text) and validate_bounded_fact(text))


def _safe_int(value: object, *, upper: int = 999) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(number, upper))


def _enum(value: object, allowed: tuple[str, ...], *, default: str) -> str:
    text = str(value or "").strip()
    return text if text in allowed else default


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _safe_scalar(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _unique_blockers(values: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in values:
        phase = _safe_scalar(item.get("phase"))
        reason = _safe_scalar(item.get("reason"))
        key = (phase, reason)
        if phase and reason and key not in seen:
            seen.add(key)
            result.append({"phase": phase, "reason": reason})
    return result


def _unique_findings(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in values:
        finding_id = _safe_scalar(item.get("finding_id")) or artifact_digest(item)[:24]
        if finding_id in seen:
            continue
        seen.add(finding_id)
        clean = dict(item)
        clean["finding_id"] = finding_id
        result.append(clean)
    return result


def _forbidden_key_value(value: object) -> bool:
    if isinstance(value, dict):
        return True
    text = str(value or "").casefold()
    return any(key in text for key in _FORBIDDEN_KEYS)


__all__ = [
    "CORE_PHASES",
    "WORKFLOW_PHASES",
    "PHASE_STATUSES",
    "REVIEW_VERDICTS",
    "artifact_digest",
    "merge_process_phase_ledger",
    "normalize_process_phase_ledger",
    "phase_blockers",
    "phase_ready_for_implementation",
    "phase_review_passes",
    "phase_transition_allowed",
    "review_findings_blocking",
    "sanitize_phase_ledger",
    "sanitize_phase_review_result",
    "validate_phase_review_result",
    "validate_process_phase_ledger",
]
