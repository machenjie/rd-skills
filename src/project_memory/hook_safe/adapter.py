"""Hook-safe adapter for Project Memory Governance.

The hook runtime calls this module instead of carrying a separate memory
projection implementation. Functions remain fail-open and return bounded facts
only; memory is an optional governance layer, not a source of repository truth.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from project_memory.privacy import (
    clean_paths,
    memory_task_fingerprint,
    repo_hash_for_path,
    sanitize_memory_event,
)
from project_memory.gates.fragile_file_gate import evaluate_fragile_file_gate
from project_memory.store.append_log import append_memory_event, iter_memory_events, memory_root_for_repo
from project_memory.store.projection import build_memory_projection, build_memory_summary


MAX_ITEMS = 50
TELEMETRY_DISABLED_VALUES = {"0", "off", "false", "no"}


def memory_policy_status() -> str:
    """Return enabled or disabled_by_policy from hook environment policy."""
    telemetry = os.environ.get("CHANGEFORGE_TELEMETRY", "").strip().casefold()
    memory = os.environ.get("CHANGEFORGE_MEMORY", "").strip().casefold()
    if telemetry in TELEMETRY_DISABLED_VALUES or memory in TELEMETRY_DISABLED_VALUES:
        return "disabled_by_policy"
    return "enabled"


def memory_enabled() -> bool:
    return memory_policy_status() == "enabled"


def sanitize_event(repo: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a hook memory event using the formal project_memory schema."""
    return sanitize_memory_event(event if isinstance(event, dict) else {}, repo=repo)


def write_event(repo: str | Path, event: dict[str, Any]) -> dict[str, Any] | None:
    """Append one bounded memory event when memory policy is enabled."""
    if not memory_enabled():
        return None
    return append_memory_event(event if isinstance(event, dict) else {}, repo=repo, fail_open=True)


def pre_edit_advice(
    repo: str | Path,
    changed_paths: Iterable[str],
    state: dict[str, Any] | None = None,
    assistant_text: str = "",
) -> dict[str, Any]:
    """Return bounded memory advice for structural pre-edit gates."""
    if not memory_enabled():
        return _empty_pre_edit("disabled_by_policy")
    state = state if isinstance(state, dict) else {}
    repo_path = Path(repo)
    paths = clean_paths(list(changed_paths), repo=repo_path)
    try:
        events = _read_events(repo_path)
        repo_hash = repo_hash_for_path(repo_path)
        owner = str(state.get("owner_skill") or "").strip()
        task = memory_task_fingerprint(paths, owner, "")
        summary = build_memory_summary(
            events,
            {
                "repo_hash": repo_hash,
                "paths": paths,
            },
        ).get("project_memory_summary", {})
        repeat = _repeat_failure(events, repo_hash=repo_hash, task=task, paths=paths, owner=owner)
        evidence = _pre_edit_evidence(state, assistant_text)
        gate = evaluate_fragile_file_gate(
            events,
            paths=paths,
            evidence=evidence,
            repo_root=repo_path,
        ).get("fragile_file_gate", {})
        fragile_paths = list(gate.get("matched_paths") or [])[:MAX_ITEMS]
        historical_paths = list(gate.get("historical_hint_paths") or [])[:MAX_ITEMS]
        if repeat.get("repeated") and evidence["failure_diagnosis_route"]:
            repeat = {**repeat, "allowed_to_continue": True}
        missing: list[str] = []
        if fragile_paths:
            missing.extend(str(item) for item in gate.get("missing") or [])
        return {
            "status": "available",
            "fragile_paths": fragile_paths,
            "current_fragile_paths": fragile_paths,
            "historical_fragile_paths": historical_paths,
            "warning_only_paths": list(gate.get("warning_only_paths") or [])[:MAX_ITEMS],
            "source_status_by_path": dict(gate.get("source_status_by_path") or {}),
            "evidence_role_by_path": dict(gate.get("evidence_role_by_path") or {}),
            "source_status": _overall_source_status((gate.get("source_status_by_path") or {}).values()),
            "repeat_failure": repeat,
            "missing": _unique(missing),
            "historical_missing": list(gate.get("missing") or [])[:MAX_ITEMS] if historical_paths else [],
            "warnings": _pre_edit_warnings(historical_paths),
            "residual_risk": list(gate.get("residual_risk") or [])[:MAX_ITEMS],
            "memory_summary_seen": bool(summary),
        }
    except Exception:
        result = _empty_pre_edit("unavailable_due_error")
        if paths:
            result["residual_risk"] = ["project_memory_unavailable"]
        return result


def closure_advice(repo: str | Path, state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return fail-open Project Memory closure facts for Stop telemetry."""
    state = state if isinstance(state, dict) else {}
    changed_paths = clean_paths(state.get("changed_paths") or [], repo=repo)
    if not memory_enabled():
        return {
            "available": False,
            "status": "disabled_by_policy",
            "projection_key": "",
            "included_events": [],
            "excluded_events": [],
            "source_status": "not_applicable",
            "source_statuses": [],
            "stale_context_gate": "not_applicable",
            "residual_risk": [],
        }
    try:
        repo_path = Path(repo)
        query = {
            "repo_hash": repo_hash_for_path(repo_path),
            "paths": changed_paths,
            "graph_freshness": _graph_freshness(state),
        }
        projection = build_memory_projection(
            _read_events(repo_path),
            query,
            repo_root=repo_path,
        ).get("project_memory_projection", {})
        included = projection.get("included_events") if isinstance(projection, dict) else []
        excluded = projection.get("excluded_events") if isinstance(projection, dict) else []
        source_statuses = _source_statuses(included)
        return {
            "available": True,
            "status": "available",
            "projection_key": str(projection.get("retrieval_key") or ""),
            "included_events": _included_event_ids(included),
            "excluded_events": _excluded_event_refs(excluded),
            "source_status": _overall_source_status(source_statuses),
            "source_statuses": source_statuses,
            "stale_context_gate": str(projection.get("stale_context_gate") or "pass"),
            "residual_risk": _unique(str(item) for item in projection.get("residual_risk", []) or [])[:MAX_ITEMS],
        }
    except Exception:
        return {
            "available": False,
            "status": "unavailable_due_error",
            "projection_key": "",
            "included_events": [],
            "excluded_events": [],
            "source_status": "unknown",
            "source_statuses": [],
            "stale_context_gate": "warn" if changed_paths else "pass",
            "residual_risk": ["project_memory_unavailable"] if changed_paths else [],
        }


def _read_events(repo: Path, *, max_events: int = 500) -> list[dict[str, Any]]:
    events = list(iter_memory_events(memory_root_for_repo(repo)))
    return list(reversed(events[-max_events:]))


def _fragile_paths(summary: dict[str, Any], paths: list[str]) -> list[str]:
    items = summary.get("fragile_files") if isinstance(summary, dict) else []
    fragile = {
        str(item.get("path") or "").strip()
        for item in items or []
        if isinstance(item, dict) and str(item.get("path") or "").strip()
    }
    return [path for path in paths if path in fragile][:MAX_ITEMS]


def _empty_pre_edit(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "fragile_paths": [],
        "current_fragile_paths": [],
        "historical_fragile_paths": [],
        "warning_only_paths": [],
        "source_status": "not_applicable" if status == "disabled_by_policy" else "unknown",
        "source_status_by_path": {},
        "evidence_role_by_path": {},
        "repeat_failure": {},
        "missing": [],
        "historical_missing": [],
        "warnings": [],
        "residual_risk": [],
    }


def _pre_edit_warnings(paths: list[str]) -> list[str]:
    if not paths:
        return []
    joined = ", ".join(paths[:MAX_ITEMS])
    return [
        "project memory fragile-file hit is historical only; reread current source and nearby tests before editing "
        + joined
    ]


def _source_statuses(events: object) -> list[str]:
    if not isinstance(events, list):
        return []
    return _unique(
        str(item.get("source_status") or "")
        for item in events
        if isinstance(item, dict)
    )[:MAX_ITEMS]


def _overall_source_status(values: Iterable[str]) -> str:
    statuses = [str(value).strip() for value in values if str(value).strip()]
    if not statuses:
        return "unknown"
    for status in ("stale", "deleted", "missing", "generated", "unknown"):
        if status in statuses:
            return status
    if all(status == "current" for status in statuses):
        return "current"
    if all(status == "not_applicable" for status in statuses):
        return "not_applicable"
    return statuses[0]


def _repeat_failure(
    events: list[dict[str, Any]],
    *,
    repo_hash: str,
    task: str,
    paths: list[str],
    owner: str,
) -> dict[str, Any]:
    exact = _matching_failures(
        events,
        repo_hash=repo_hash,
        task=task,
        paths=paths,
        owner=owner,
        require_task=True,
    )
    failures = exact if len(exact) >= 2 else _matching_failures(
        events,
        repo_hash=repo_hash,
        task=task,
        paths=paths,
        owner=owner,
        require_task=False,
    )
    failures.sort(key=lambda event: str(event.get("created_at", "")), reverse=True)
    repeated = len(failures) >= 2
    return {
        "repeated": repeated,
        "failure_count": min(len(failures), 2),
        "matched_paths": _unique(path for event in failures[:2] for path in _event_paths(event)),
        "required_next_gate": "failure-diagnosis",
        "allowed_to_continue": not repeated,
    }


def _matching_failures(
    events: list[dict[str, Any]],
    *,
    repo_hash: str,
    task: str,
    paths: list[str],
    owner: str,
    require_task: bool,
) -> list[dict[str, Any]]:
    path_set = set(paths)
    failures: list[dict[str, Any]] = []
    for event in events:
        if event.get("repo_hash") != repo_hash:
            continue
        if require_task and event.get("task_fingerprint") != task:
            continue
        if owner and event.get("owner_skill") != owner:
            continue
        if not _paths_overlap(path_set, set(_event_paths(event))):
            continue
        if event.get("outcome") not in {"failed", "blocked"}:
            continue
        failures.append(event)
    return failures


def _pre_edit_evidence(state: dict[str, Any], assistant_text: str) -> dict[str, bool]:
    lowered = assistant_text.casefold()
    return {
        "read_file_evidence": bool(
            state.get("read_evidence_seen")
            or state.get("read_paths")
            or "read_evidence" in lowered
        ),
        "owner_source_of_truth_check": bool(
            "source of truth" in lowered
            or "owner source" in lowered
            or state.get("repository_context_seen")
        ),
        "same_pattern_scan": bool(
            state.get("searched_patterns")
            or "same-pattern" in lowered
            or "same pattern" in lowered
        ),
        "validator_mapping": bool(
            state.get("validation_command_seen")
            or "validator mapping" in lowered
            or "validation broker" in lowered
        ),
        "nearby_test_evidence": bool(
            state.get("validation_command_seen")
            or "test_plan" in lowered
            or "nearby test" in lowered
        ),
        "memory_summary_evidence": bool(
            "project_memory_summary" in lowered
            or "memory summary" in lowered
            or "project memory summary" in lowered
        ),
        "implementation_preflight": bool(
            state.get("implementation_preflight_seen")
            or "changeforge_implementation_preflight" in lowered
        ),
        "failure_diagnosis_route": bool(
            state.get("repair_evidence_seen")
            or "failure-diagnosis" in lowered
            or "failure diagnosis" in lowered
            or "route repair" in lowered
            or "quality-test-gate" in lowered
            or "quality test gate" in lowered
        ),
    }


def _graph_freshness(state: dict[str, Any]) -> str:
    raw = state.get("graph_freshness") or state.get("repository_graph_freshness") or "current"
    text = str(raw).strip().casefold()
    if text == "fresh":
        return "current"
    return text if text in {"current", "stale", "unknown"} else "current"


def _event_paths(event: dict[str, Any]) -> list[str]:
    values = event.get("bounded_paths")
    if not isinstance(values, list):
        values = event.get("paths")
    return [str(item).strip() for item in values or [] if str(item).strip()][:MAX_ITEMS]


def _paths_overlap(left_paths: set[str], right_paths: set[str]) -> bool:
    if left_paths & right_paths:
        return True
    for left in left_paths:
        for right in right_paths:
            if left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                return True
    return False


def _included_event_ids(events: object) -> list[str]:
    if not isinstance(events, list):
        return []
    return _unique(
        str(item.get("event_id") or "")
        for item in events
        if isinstance(item, dict)
    )[:MAX_ITEMS]


def _excluded_event_refs(events: object) -> list[str]:
    if not isinstance(events, list):
        return []
    refs: list[str] = []
    for item in events:
        if not isinstance(item, dict):
            continue
        event_id = str(item.get("event_id") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if event_id and reason:
            refs.append(f"{event_id}:{reason}")
    return _unique(refs)[:MAX_ITEMS]


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
