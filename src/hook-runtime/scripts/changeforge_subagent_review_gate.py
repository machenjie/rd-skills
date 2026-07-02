#!/usr/bin/env python3
"""Bound subagent phase reviews to capsule/result contracts."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from changeforge_adapter_capabilities import adapter_capabilities_for
from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    is_subagent_start,
    is_subagent_stop,
    load_state,
    merge_state,
    read_event,
    repo_root,
    session_id_from_event,
    write_telemetry_event,
)
from changeforge_hook_policy import gate_mode, run_gate_with_policy, should_emit_context
from changeforge_runtime_adapters import adapter_for

try:
    from runtime_governance.process_phase import (
        phase_review_passes,
        review_findings_blocking,
        sanitize_phase_review_result,
    )
    from runtime_governance.review_capsule import sanitize_review_capsule
except ModuleNotFoundError:
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from runtime_governance.process_phase import (  # type: ignore[no-redef]
        phase_review_passes,
        review_findings_blocking,
        sanitize_phase_review_result,
    )
    from runtime_governance.review_capsule import sanitize_review_capsule  # type: ignore[no-redef]


GATE_NAME = "subagent_review"
PHASES = {"pdd", "ddd", "sdd", "tdd", "implementation", "closure"}
JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def main() -> int:
    return run_gate_with_policy(GATE_NAME, _main, fail_closed=_fail_closed)


def _fail_closed(exc: Exception) -> None:
    runtime = detect_runtime({})
    adapter_for(runtime).emit_permission_decision(
        "block",
        f"ChangeForge Subagent Review Gate failed closed: {exc}",
    )


def _main() -> int:
    event = read_event()
    if not event:
        return 0
    mode = gate_mode(GATE_NAME)
    if mode == "off":
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    if is_subagent_start(event):
        return _handle_subagent_start(event, runtime, repo, state, mode)
    if is_subagent_stop(event):
        return _handle_subagent_stop(event, runtime, repo, state, mode)
    return 0


def _handle_subagent_start(event: dict, runtime: str, repo: Path, state: dict, mode: str) -> int:
    review_type = _review_type(event, state)
    capsule = build_review_capsule(event, state, review_type=review_type)
    degraded = _adapter_degraded(runtime)
    merge_state(
        repo,
        runtime,
        review_capsules=[capsule],
        phase_review_seen=False,
        process_phase_blocked=bool(degraded),
        process_phase_blocked_reason="; ".join(degraded)[:300],
        prompt_signals=["subagent_review_capsule"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="subagent_review_gate",
        event_name=event_name(event) or "SubagentStart",
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        review_capsules=[capsule],
        process_phase_blocked=bool(degraded),
        process_phase_blocked_reason="; ".join(degraded)[:300],
        hook_findings={"degraded": degraded},
    )
    if mode not in {"monitor", "off"} and should_emit_context(GATE_NAME):
        adapter_for(runtime).emit_context(event_name(event) or "SubagentStart", render_capsule_message(capsule, degraded))
    return 0


def _handle_subagent_stop(event: dict, runtime: str, repo: Path, state: dict, mode: str) -> int:
    result = extract_phase_review_result(event)
    if not result:
        result = insufficient_evidence_result(_review_type(event, state))
    result = sanitize_phase_review_result(result)
    findings = review_findings_blocking([result])
    reviewed = phase_review_passes(result, artifact_digest=result.get("reviewed_artifact_digest") or None)
    phase = str(result.get("phase") or "")
    reviewed_flags = {
        "pdd_reviewed": reviewed if phase == "pdd" else None,
        "ddd_reviewed": reviewed if phase == "ddd" else None,
        "sdd_reviewed": reviewed if phase == "sdd" else None,
        "tdd_reviewed": reviewed if phase == "tdd" else None,
    }
    degraded = _adapter_degraded(runtime)
    blocked = bool(findings or degraded)
    reason = "; ".join([str(item.get("evidence") or item.get("finding_id")) for item in findings] + degraded)[:300]
    merge_state(
        repo,
        runtime,
        phase_review_results=[result],
        phase_review_findings=findings,
        phase_review_seen=True,
        process_phase_blocked=blocked,
        process_phase_blocked_reason=reason,
        phase_repair_required=bool(findings),
        prompt_signals=["subagent_phase_review_result"],
        **reviewed_flags,
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="subagent_review_gate",
        event_name=event_name(event) or "SubagentStop",
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        phase_review_results=[result],
        phase_review_findings=findings,
        phase_review_seen=True,
        process_phase_blocked=blocked,
        process_phase_blocked_reason=reason,
        phase_repair_required=bool(findings),
        pdd_reviewed=bool(reviewed_flags["pdd_reviewed"]),
        ddd_reviewed=bool(reviewed_flags["ddd_reviewed"]),
        sdd_reviewed=bool(reviewed_flags["sdd_reviewed"]),
        tdd_reviewed=bool(reviewed_flags["tdd_reviewed"]),
        hook_findings={"findings": findings, "degraded": degraded},
    )
    return 0


def build_review_capsule(event: dict, state: dict, *, review_type: str) -> dict[str, Any]:
    """Return a bounded review capsule derived from state, never raw prompts."""
    digest = _digest_for(review_type)
    paths = [str(path) for path in (state.get("read_paths") or state.get("changed_paths") or [])[:20]]
    read_files = [
        {
            "path": path[:300],
            "digest": _digest_for(path),
            "excerpt_summary": "bounded source path observed by parent context",
        }
        for path in paths
    ]
    capsule = {
        "schema_version": 1,
        "capsule_id": str(event.get("capsule_id") or f"{review_type}-capsule-1")[:120],
        "review_type": review_type,
        "user_request_summary": "bounded parent-supplied engineering request summary",
        "accepted_constraints": [
            "review only the artifact digest and bounded source evidence",
            "return phase_review_result only",
        ],
        "source_evidence": {
            "read_files": read_files,
            "searched_patterns": [str(item)[:300] for item in (state.get("searched_patterns") or [])[:20]],
        },
        "artifact_under_review": {
            "phase": review_type,
            "artifact_digest": str(event.get("artifact_digest") or digest),
            "artifact_summary": str(event.get("artifact_summary") or f"bounded {review_type} artifact summary")[:600],
        },
        "allowed_context": [
            "user_request_summary",
            "accepted_constraints",
            "source_evidence",
            "artifact_under_review",
        ],
        "forbidden_inputs": [
            "raw prompt",
            "raw secrets",
            "full command output",
            "implementer self-approval",
            "unverified completion claims",
        ],
    }
    return sanitize_review_capsule(capsule)


def extract_phase_review_result(event: dict) -> dict[str, Any]:
    """Extract a structured phase_review_result from bounded hook event fields."""
    direct = event.get("phase_review_result")
    if isinstance(direct, dict):
        return direct
    for key in ("response", "result", "last_assistant_message", "lastAssistantMessage"):
        value = event.get(key)
        if not isinstance(value, str):
            continue
        parsed = _json_from_text(value)
        if isinstance(parsed, dict):
            if isinstance(parsed.get("phase_review_result"), dict):
                return parsed["phase_review_result"]
            if "review_id" in parsed and "verdict" in parsed:
                return parsed
    return {}


def insufficient_evidence_result(phase: str) -> dict[str, Any]:
    digest = _digest_for(f"{phase}:insufficient")
    return {
        "schema_version": 1,
        "review_id": f"{phase}-review-insufficient-evidence",
        "phase": phase if phase in PHASES else "implementation",
        "reviewer_skill": "phase-review-capsule",
        "owner_skill": "development-process-orchestrator",
        "reviewed_artifact_digest": digest,
        "verdict": "insufficient_evidence",
        "score": 0,
        "findings": [
            {
                "finding_id": f"{phase}-review-missing",
                "severity": "high",
                "evidence": "subagent did not return phase_review_result",
                "required_fix": "rerun independent review and return phase_review_result",
                "blocks_next_stage": True,
            }
        ],
        "approved_scope": {"files": [], "behaviors": [], "facts": []},
        "not_reviewed": ["phase artifact was not independently reviewed"],
        "required_next_action": ["repair"],
        "residual_risk": [
            {
                "risk": "missing independent review evidence",
                "owner": "development-process-orchestrator",
                "next_gate": "subagent_review_gate",
            }
        ],
    }


def render_capsule_message(capsule: dict[str, Any], degraded: list[str]) -> str:
    lines = ["ChangeForge Subagent Review Gate: review capsule required"]
    lines.append(f"- review_type: {capsule.get('review_type')}")
    lines.append("- return only phase_review_result; do not return raw reasoning or transcript")
    for item in degraded:
        lines.append(f"- degraded enforcement: {item}")
    return "\n".join(lines)


def _review_type(event: dict, state: dict) -> str:
    for value in (event.get("review_type"), event.get("phase"), state.get("process_current_phase")):
        text = str(value or "").strip().casefold()
        if text in PHASES:
            return text
    return "implementation"


def _adapter_degraded(runtime: str) -> list[str]:
    capabilities = adapter_capabilities_for(runtime)
    if capabilities.supports_subagent_stop:
        return []
    return [f"{runtime} lacks SubagentStop support; require parent-context review result or CI validation"]


def _json_from_text(text: str) -> Any:
    stripped = text.strip()
    candidates = [stripped]
    match = JSON_OBJECT_RE.search(stripped)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _digest_for(value: str) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
