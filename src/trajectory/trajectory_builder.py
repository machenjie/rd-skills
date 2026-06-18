"""Build ordered ChangeForge execution trajectories from bounded evidence logs.

The builder reads telemetry and optional memory/evidence-ledger style events.
It never records full prompts, stdout/stderr, environment variables, or secrets.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1

VALID_STAGES = {
    "user_prompt",
    "route",
    "read",
    "plan",
    "edit",
    "test",
    "review",
    "repair",
    "re_review",
    "stop",
}

READ_ONLY_COMMANDS = {
    "cat",
    "sed",
    "rg",
    "grep",
    "find",
    "ls",
    "nl",
    "head",
    "tail",
    "wc",
    "git",
}

EDIT_TOOLS = {
    "apply_patch",
    "python_write",
    "write_file",
    "edit",
}

TEST_COMMANDS = {
    "python",
    "python3",
    "pytest",
    "unittest",
    "npm",
    "pnpm",
    "yarn",
    "go",
    "cargo",
    "mvn",
}


def default_telemetry_root() -> Path:
    """Return the default ChangeForge telemetry root."""
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")).expanduser()
    return cache_root / "changeforge" / "telemetry"


def default_memory_root() -> Path:
    """Return the default ChangeForge project-memory root."""
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")).expanduser()
    return cache_root / "changeforge" / "memory"


def load_telemetry_records(
    telemetry_root: str | Path | None,
    repo_hash: str,
    session_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load telemetry JSONL records for one repository hash.

    A missing telemetry root or session directory returns an empty list. Invalid
    JSON lines are skipped so one malformed record cannot hide other evidence.
    """
    root = Path(telemetry_root).expanduser() if telemetry_root else default_telemetry_root()
    sessions_dir = root / repo_hash / "sessions"
    if not sessions_dir.is_dir():
        return []

    records: list[dict[str, Any]] = []
    sequence = 0
    for path in sorted(sessions_dir.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            if session_id and not _session_matches(str(record.get("session_id", "")), session_id):
                continue
            record = dict(record)
            record["_source_file"] = path.name
            record["_source_sequence"] = sequence
            sequence += 1
            records.append(record)
    return sorted(records, key=_record_sort_key)


def load_memory_events(
    memory_root: str | Path | None,
    repo_hash: str,
    session_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load bounded project-memory events for one repository hash."""
    root = Path(memory_root).expanduser() if memory_root else default_memory_root()
    events_dir = root / repo_hash / "events"
    if not events_dir.is_dir():
        return []

    events: list[dict[str, Any]] = []
    sequence = 0
    for path in sorted(events_dir.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            event_session = str(event.get("session_id") or "")
            if session_id and event_session and not _session_matches(event_session, session_id):
                continue
            event = dict(event)
            event["_source_sequence"] = sequence
            sequence += 1
            events.append(event)
    return sorted(events, key=_record_sort_key)


def build_trajectory(
    records: Iterable[dict[str, Any]],
    *,
    repo_hash: str = "",
    session_id: str | None = None,
    memory_events: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Build a trajectory from telemetry records and optional memory events.

    Returns ``None`` when no records or memory events are provided. This lets
    command-line tools report ``no samples found`` with exit code 0.
    """
    telemetry_records = [dict(record) for record in records if isinstance(record, dict)]
    memory_records = [_memory_event_to_record(event) for event in (memory_events or []) if isinstance(event, dict)]
    combined = sorted(telemetry_records + memory_records, key=_record_sort_key)
    if not combined:
        return None

    session = session_id or _first_non_empty(record.get("session_id") for record in combined)
    repository_hash = repo_hash or _first_non_empty(record.get("repo_hash") for record in combined)
    started_at = _first_non_empty(record.get("timestamp_utc") or record.get("created_at") for record in combined)
    ended_at = _last_non_empty(record.get("timestamp_utc") or record.get("created_at") for record in combined)
    task_fingerprint = _first_non_empty(record.get("task_fingerprint") for record in combined)
    if not task_fingerprint:
        task_fingerprint = _fingerprint(repository_hash, session, combined)

    steps: list[dict[str, Any]] = []
    repair_seen = False
    cumulative = _CumulativeEvidence()
    for index, record in enumerate(combined, start=1):
        stage = _stage_for_record(record, repair_seen)
        evidence = _evidence_for_record(record, cumulative)
        paths = _paths_for_record(record)
        facts = _facts_for_record(record, paths)
        material_edit = _is_material_edit(record, stage, paths)
        facts["material_edit"] = material_edit
        facts["source"] = record.get("_source", "telemetry")
        step = {
            "index": index,
            "stage": stage,
            "event_type": _bounded_text(record.get("event_name") or record.get("event_type") or "", 120),
            "runtime": _runtime_for_record(record),
            "tool_name": _bounded_text(record.get("tool_name") or "", 120),
            "command_program": _bounded_text(record.get("command_program") or "", 120),
            "paths": paths,
            "facts": facts,
            "evidence": evidence,
            "risk_surfaces": _risk_surfaces_for_record(record),
            "outcome": _outcome_for_record(record),
        }
        steps.append(step)
        cumulative.observe(step)
        repair_seen = repair_seen or stage == "repair" or evidence.get("repair_seen", False)

    trajectory = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session,
        "repo_hash": repository_hash,
        "task_fingerprint": task_fingerprint,
        "started_at": started_at,
        "ended_at": ended_at,
        "ordered_events": _ordered_events(steps, session),
        "changed_paths": _changed_paths(steps),
        "read_paths": _read_paths(steps),
        "validation_timeline": _validation_timeline(steps),
        "review_repair_timeline": _review_repair_timeline(steps),
        "memory_hits": _memory_hits(steps),
        "adapter_degradations": _adapter_degradations(steps),
        "steps": steps,
        "issues": [],
    }
    return trajectory


class _CumulativeEvidence:
    def __init__(self) -> None:
        self.route_manifest_seen = False
        self.read_evidence_seen = False
        self.repository_context_seen = False
        self.implementation_preflight_seen = False
        self.validation_seen = False
        self.review_seen = False
        self.repair_seen = False
        self.residual_risk_seen = False
        self.memory_summary_seen = False
        self.nearby_test_seen = False

    def observe(self, step: dict[str, Any]) -> None:
        evidence = step.get("evidence", {})
        self.route_manifest_seen = self.route_manifest_seen or bool(evidence.get("route_manifest_seen"))
        self.read_evidence_seen = self.read_evidence_seen or bool(evidence.get("read_evidence_seen"))
        self.repository_context_seen = self.repository_context_seen or bool(evidence.get("repository_context_seen"))
        self.implementation_preflight_seen = self.implementation_preflight_seen or bool(
            evidence.get("implementation_preflight_seen")
        )
        self.validation_seen = self.validation_seen or bool(evidence.get("validation_seen"))
        self.review_seen = self.review_seen or bool(evidence.get("review_seen"))
        self.repair_seen = self.repair_seen or bool(evidence.get("repair_seen"))
        self.residual_risk_seen = self.residual_risk_seen or bool(evidence.get("residual_risk_seen"))
        self.memory_summary_seen = self.memory_summary_seen or bool(evidence.get("memory_summary_seen"))
        self.nearby_test_seen = self.nearby_test_seen or bool(evidence.get("nearby_test_seen"))


def _session_matches(record_session: str, requested: str) -> bool:
    return record_session == requested or record_session.startswith(f"{requested}:")


def _record_sort_key(record: dict[str, Any]) -> tuple[str, int]:
    timestamp = str(record.get("timestamp_utc") or record.get("created_at") or "")
    sequence = int(record.get("_source_sequence") or 0)
    return (timestamp, sequence)


def _stage_for_record(record: dict[str, Any], repair_seen: bool) -> str:
    raw_stage = _normalize_stage(record.get("turn_stage") or record.get("stage") or record.get("manifest_current_stage"))
    if raw_stage == "review" and repair_seen:
        return "re_review"
    if raw_stage:
        return raw_stage

    event = str(record.get("event_name") or record.get("event_type") or "")
    hook = str(record.get("hook_name") or "")
    command_program = str(record.get("command_program") or "")
    tool_name = str(record.get("tool_name") or "")

    if event == "Stop" or "stop" in hook:
        return "stop"
    if bool(record.get("repair_evidence_seen")):
        return "repair"
    if bool(record.get("review_evidence_seen")):
        return "re_review" if repair_seen else "review"
    if bool(record.get("validation_evidence_detected")) or _is_test_command(command_program):
        return "test"
    if _is_material_edit(record, "edit", _paths_for_record(record)):
        return "edit"
    if bool(record.get("implementation_preflight_seen")) or bool(record.get("implementation_preflight_required")):
        return "plan"
    if bool(record.get("read_evidence_seen")) or tool_name in {"cat", "sed", "rg", "find", "ls"}:
        return "read"
    if bool(record.get("route_manifest_detected")) or record.get("suggested_skills") or record.get("suggested_capabilities"):
        return "route"
    if event == "UserPromptSubmit":
        return "user_prompt"
    return "route" if "route" in hook else "read"


def _normalize_stage(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    mapping = {
        "routing": "route",
        "planning": "plan",
        "preflight": "plan",
        "implementation_preflight": "plan",
        "coding": "edit",
        "implementation": "edit",
        "test_validation": "test",
        "testing": "test",
        "validation": "test",
        "code_review": "review",
        "rereview": "re_review",
        "re_review": "re_review",
        "final_handoff": "stop",
        "documentation_handoff": "stop",
    }
    text = mapping.get(text, text)
    return text if text in VALID_STAGES else ""


def _evidence_for_record(record: dict[str, Any], cumulative: _CumulativeEvidence) -> dict[str, bool]:
    broker_ledger = _validation_broker_command_ledger(record)
    broker_ledger_outcomes = {
        str(item.get("outcome") or "").strip().lower()
        for item in broker_ledger
        if isinstance(item, dict)
    }
    route_seen = bool(record.get("route_manifest_detected") or record.get("route_manifest_seen"))
    read_seen = bool(record.get("read_evidence_seen")) or bool(record.get("read_paths"))
    repository_context_seen = bool(record.get("repository_context_seen"))
    implementation_preflight_seen = bool(
        record.get("implementation_preflight_complete") or record.get("implementation_preflight_seen")
    )
    validation_seen = bool(record.get("validation_evidence_detected") or record.get("validation_seen")) or bool(
        broker_ledger_outcomes & {"passed", "failed", "stale", "partial"}
    )
    validation_command_seen = bool(
        record.get("validation_command_detected") or record.get("validation_command_seen")
    ) or bool(broker_ledger)
    validation_outcome_seen = _outcome_for_record(record) in {"pass", "fail"} and (
        validation_seen or validation_command_seen or bool(record.get("validation_result_outcome"))
    )
    review_seen = bool(record.get("review_evidence_seen") or record.get("review_seen"))
    repair_seen = bool(record.get("repair_evidence_seen") or record.get("repair_seen"))
    residual_risk_seen = bool(record.get("residual_risk_detected") or record.get("residual_risk_seen"))
    memory_summary_seen = bool(
        record.get("memory_summary_seen")
        or record.get("type") == "memory_summary"
        or record.get("project_memory_projection_key")
        or record.get("project_memory_included_events")
    )
    nearby_test_seen = bool(record.get("nearby_test_evidence") or record.get("nearby_test_seen"))
    return {
        "route_manifest_seen": route_seen or cumulative.route_manifest_seen,
        "read_evidence_seen": read_seen or cumulative.read_evidence_seen,
        "repository_context_seen": repository_context_seen or cumulative.repository_context_seen,
        "implementation_preflight_seen": implementation_preflight_seen or cumulative.implementation_preflight_seen,
        "validation_seen": validation_seen or cumulative.validation_seen,
        "validation_command_seen": validation_command_seen,
        "validation_outcome_seen": validation_outcome_seen,
        "review_seen": review_seen or cumulative.review_seen,
        "repair_seen": repair_seen or cumulative.repair_seen,
        "residual_risk_seen": residual_risk_seen or cumulative.residual_risk_seen,
        "memory_summary_seen": memory_summary_seen or cumulative.memory_summary_seen,
        "nearby_test_seen": nearby_test_seen or cumulative.nearby_test_seen,
    }


def _facts_for_record(record: dict[str, Any], paths: list[str]) -> dict[str, Any]:
    route_lists = {
        "selected_skills": _string_list(record.get("manifest_selected_skills") or record.get("selected_skills")),
        "selected_capabilities": _string_list(
            record.get("manifest_selected_capabilities") or record.get("selected_capabilities")
        ),
        "required_references": _string_list(record.get("manifest_required_references") or record.get("required_references")),
        "required_quality_gates": _string_list(
            record.get("manifest_required_quality_gates") or record.get("required_quality_gates")
        ),
    }
    return {
        "changed_paths": _string_list(record.get("changed_paths")),
        "added_paths": _string_list(record.get("added_paths")),
        "read_paths": _string_list(record.get("read_paths")),
        "owner_skill": str(record.get("owner_skill") or ""),
        "reviewer_skill": str(record.get("reviewer_skill") or ""),
        "implementation_preflight_required": bool(record.get("implementation_preflight_required")),
        "implementation_preflight_complete": bool(record.get("implementation_preflight_complete")),
        "edit_without_preflight_seen": bool(record.get("edit_without_preflight_seen")),
        "post_edit_confirmed_preflight_gap": bool(record.get("post_edit_confirmed_preflight_gap")),
        "validation_command_detected": bool(record.get("validation_command_detected") or record.get("validation_command_seen")),
        "validation_evidence_detected": bool(record.get("validation_evidence_detected") or record.get("validation_seen")),
        "validation_result_outcome": str(record.get("validation_result_outcome") or record.get("outcome") or ""),
        "validation_freshness_seen": bool(record.get("validation_freshness_seen")),
        "validation_broker_closure_outcome": _validation_broker_closure_outcome(record),
        "validation_broker_negative_evidence": _validation_broker_negative_evidence(record),
        "validation_broker_selected_scope": _validation_broker_selected_scope(record),
        "validation_broker_command_ledger": _validation_broker_command_ledger(record),
        "adapter_name": str(record.get("adapter_name") or record.get("runtime") or ""),
        "adapter_supported_checks": _string_list(record.get("adapter_supported_checks")),
        "adapter_unsupported_checks": _string_list(record.get("adapter_unsupported_checks")),
        "adapter_degraded_capabilities": _string_list(
            record.get("adapter_degraded_capabilities")
        ),
        "closure_contract_verdict": str(record.get("closure_contract_verdict") or ""),
        "closure_contract_residual_risk": _string_list(
            record.get("closure_contract_residual_risk")
        ),
        "project_memory_available": record.get("project_memory_available"),
        "project_memory_projection_key": str(record.get("project_memory_projection_key") or ""),
        "project_memory_included_events": _string_list(record.get("project_memory_included_events")),
        "project_memory_excluded_events": _string_list(record.get("project_memory_excluded_events")),
        "project_memory_stale_context_gate": str(record.get("project_memory_stale_context_gate") or ""),
        "project_memory_residual_risk": _string_list(record.get("project_memory_residual_risk")),
        "route_manifest_detected": bool(record.get("route_manifest_detected")),
        "stage_manifest_detected": bool(record.get("stage_manifest_detected")),
        "memory_event_kind": str(record.get("kind") or ""),
        "memory_event_type": str(record.get("type") or ""),
        "hook_name": str(record.get("hook_name") or ""),
        "paths_count": len(paths),
        **route_lists,
    }


def _paths_for_record(record: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in ("bounded_paths", "paths", "changed_paths", "added_paths", "read_paths"):
        values.extend(_string_list(record.get(field)))
    return _unique(values)


def _risk_surfaces_for_record(record: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in (
        "risk_surfaces",
        "closure_risk_surfaces",
        "changed_path_risk_surfaces",
        "command_risk_surfaces",
    ):
        values.extend(_string_list(record.get(field)))
    kind = str(record.get("kind") or "")
    event_type = str(record.get("type") or "")
    if kind == "repeat_failure" or event_type == "repeat_failure":
        values.append("repeat-failure")
    if kind == "fragile_file" or event_type == "fragile_file":
        values.append("fragile-file")
    return _unique(values)


def _outcome_for_record(record: dict[str, Any]) -> str:
    broker_outcome = _validation_broker_closure_outcome(record)
    broker_ledger_outcomes = {
        str(item.get("outcome") or "").strip().lower()
        for item in _validation_broker_command_ledger(record)
        if isinstance(item, dict)
    }
    if broker_outcome == "blocked" or broker_ledger_outcomes & {"failed", "stale"}:
        return "fail"
    if broker_ledger_outcomes & {"passed"}:
        return "pass"
    value = str(record.get("validation_result_outcome") or record.get("outcome") or "").strip().lower()
    if value in {"pass", "passed", "success", "succeeded"}:
        return "pass"
    if value in {"fail", "failed", "failure", "blocked", "error"}:
        return "fail"
    if value in {"not_applicable", "n/a", "na"}:
        return "not_applicable"
    return "unknown"


def _ordered_events(steps: list[dict[str, Any]], session_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for step in steps:
        facts = _facts_from_step(step)
        index = int(step.get("index") or 0)
        events.append(
            {
                "event_id": f"{session_id or 'session'}-{index}",
                "order": index,
                "stage": str(step.get("stage") or ""),
                "action_type": _action_type(step),
                "bounded_paths": list(step.get("paths", []) or [])[:80],
                "owner_skill": str(facts.get("owner_skill") or ""),
                "reviewer_skill": str(facts.get("reviewer_skill") or ""),
                "command_kind": _command_kind(step),
                "validation_outcome": _validation_outcome(step),
            }
        )
    return events


def _changed_paths(steps: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for step in steps:
        facts = _facts_from_step(step)
        values.extend(_string_list(facts.get("changed_paths")))
        values.extend(_string_list(facts.get("added_paths")))
    return _unique(values)


def _read_paths(steps: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for step in steps:
        facts = _facts_from_step(step)
        values.extend(_string_list(facts.get("read_paths")))
    return _unique(values)


def _validation_timeline(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for step in steps:
        facts = _facts_from_step(step)
        ledger = facts.get("validation_broker_command_ledger")
        if isinstance(ledger, list) and ledger:
            for item in ledger:
                if not isinstance(item, dict):
                    continue
                timeline.append(
                    {
                        "order": int(step.get("index") or 0),
                        "stage": str(step.get("stage") or ""),
                        "command_kind": _bounded_text(item.get("command_kind") or _command_kind(step), 120),
                        "scope": _bounded_text(item.get("scope") or facts.get("validation_broker_selected_scope") or "", 80),
                        "validation_outcome": _bounded_text(item.get("outcome") or _validation_outcome(step), 80),
                        "freshness": _timeline_freshness(facts, item),
                        "covered_paths": _string_list(item.get("covered_paths"))[:80],
                        "covered_risk_surfaces": _string_list(item.get("covered_risk_surfaces"))[:80],
                        "negative_evidence": _string_list(facts.get("validation_broker_negative_evidence"))[:80],
                    }
                )
            continue
        if (
            step.get("stage") == "test"
            or facts.get("validation_command_detected")
            or facts.get("validation_evidence_detected")
        ):
            timeline.append(
                {
                    "order": int(step.get("index") or 0),
                    "stage": str(step.get("stage") or ""),
                    "command_kind": _command_kind(step),
                    "scope": _bounded_text(facts.get("validation_broker_selected_scope") or "", 80),
                    "validation_outcome": _validation_outcome(step),
                    "freshness": _timeline_freshness(facts, {}),
                    "covered_paths": list(step.get("paths", []) or [])[:80],
                    "covered_risk_surfaces": list(step.get("risk_surfaces", []) or [])[:80],
                    "negative_evidence": _string_list(facts.get("validation_broker_negative_evidence"))[:80],
                }
            )
    return timeline


def _review_repair_timeline(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for step in steps:
        if step.get("stage") not in {"review", "repair", "re_review"}:
            continue
        evidence = step.get("evidence") if isinstance(step.get("evidence"), dict) else {}
        facts = _facts_from_step(step)
        timeline.append(
            {
                "order": int(step.get("index") or 0),
                "stage": str(step.get("stage") or ""),
                "owner_skill": str(facts.get("owner_skill") or ""),
                "reviewer_skill": str(facts.get("reviewer_skill") or ""),
                "review_seen": bool(evidence.get("review_seen")),
                "repair_seen": bool(evidence.get("repair_seen")),
                "bounded_paths": list(step.get("paths", []) or [])[:80],
            }
        )
    return timeline


def _memory_hits(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for step in steps:
        facts = _facts_from_step(step)
        evidence = step.get("evidence") if isinstance(step.get("evidence"), dict) else {}
        if not (
            evidence.get("memory_summary_seen")
            or facts.get("project_memory_projection_key")
            or facts.get("project_memory_included_events")
            or facts.get("project_memory_excluded_events")
            or facts.get("memory_event_kind")
            or facts.get("memory_event_type")
        ):
            continue
        hits.append(
            {
                "order": int(step.get("index") or 0),
                "projection_key": str(facts.get("project_memory_projection_key") or ""),
                "included_events": _string_list(facts.get("project_memory_included_events"))[:80],
                "excluded_events": _string_list(facts.get("project_memory_excluded_events"))[:80],
                "stale_context_gate": str(facts.get("project_memory_stale_context_gate") or ""),
                "residual_risk": _string_list(facts.get("project_memory_residual_risk"))[:80],
                "event_kind": str(facts.get("memory_event_kind") or ""),
                "event_type": str(facts.get("memory_event_type") or ""),
                "bounded_paths": list(step.get("paths", []) or [])[:80],
            }
        )
    return hits


def _adapter_degradations(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    degradations: list[dict[str, Any]] = []
    for step in steps:
        facts = _facts_from_step(step)
        unsupported = _string_list(facts.get("adapter_unsupported_checks"))
        degraded = _string_list(facts.get("adapter_degraded_capabilities"))
        verdict = str(facts.get("closure_contract_verdict") or "")
        residual = _string_list(facts.get("closure_contract_residual_risk"))
        if not unsupported and not degraded and verdict not in {"degraded_ready", "needs_validation", "blocked"}:
            continue
        degradations.append(
            {
                "order": int(step.get("index") or 0),
                "adapter_name": str(facts.get("adapter_name") or ""),
                "unsupported_checks": unsupported[:80],
                "degraded_capabilities": degraded[:80],
                "closure_contract_verdict": verdict,
                "residual_risk": residual[:80],
            }
        )
    return degradations


def _action_type(step: dict[str, Any]) -> str:
    tool_name = str(step.get("tool_name") or "")
    command_program = str(step.get("command_program") or "")
    event_type = str(step.get("event_type") or "")
    if command_program:
        return "command"
    if tool_name:
        return tool_name[:120]
    return event_type[:120] or str(step.get("stage") or "")


def _command_kind(step: dict[str, Any]) -> str:
    command_program = str(step.get("command_program") or "")
    if command_program:
        return command_program[:120]
    tool_name = str(step.get("tool_name") or "")
    return tool_name[:120]


def _validation_outcome(step: dict[str, Any]) -> str:
    facts = _facts_from_step(step)
    value = str(facts.get("validation_result_outcome") or "").strip().lower()
    if value in {"pass", "passed", "success", "succeeded"}:
        return "passed"
    if value in {"fail", "failed", "failure", "blocked", "error"}:
        return "failed"
    ledger = facts.get("validation_broker_command_ledger")
    if isinstance(ledger, list):
        outcomes = {
            str(item.get("outcome") or "").strip().lower()
            for item in ledger
            if isinstance(item, dict)
        }
        if "failed" in outcomes:
            return "failed"
        if "stale" in outcomes:
            return "stale"
        if "passed" in outcomes:
            return "passed"
        if "partial" in outcomes:
            return "partial"
        if outcomes & {"not_run", "not_verified"}:
            return sorted(outcomes & {"not_run", "not_verified"})[0]
    outcome = str(step.get("outcome") or "").strip().lower()
    if outcome == "pass":
        return "passed"
    if outcome == "fail":
        return "failed"
    return "unknown"


def _timeline_freshness(facts: dict[str, Any], ledger_item: dict[str, Any]) -> str:
    negatives = {str(item).strip().lower() for item in _string_list(facts.get("validation_broker_negative_evidence"))}
    outcome = str(ledger_item.get("outcome") or "").strip().lower()
    if "stale_validation" in negatives or outcome == "stale":
        return "stale"
    freshness = facts.get("validation_freshness_seen")
    if freshness:
        return "fresh"
    return "unknown"


def _facts_from_step(step: dict[str, Any]) -> dict[str, Any]:
    facts = step.get("facts")
    return facts if isinstance(facts, dict) else {}


def _validation_broker_result(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("validation_broker_result")
    return value if isinstance(value, dict) else {}


def _validation_broker_command_ledger(record: dict[str, Any]) -> list[dict[str, Any]]:
    value = record.get("validation_broker_command_ledger")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    broker = _validation_broker_result(record)
    value = broker.get("command_ledger")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _validation_broker_negative_evidence(record: dict[str, Any]) -> list[str]:
    value = record.get("validation_broker_negative_evidence")
    if isinstance(value, list):
        return _string_list(value)
    broker = _validation_broker_result(record)
    return _string_list(broker.get("negative_evidence", []))


def _validation_broker_closure_outcome(record: dict[str, Any]) -> str:
    value = str(record.get("validation_broker_closure_outcome") or "").strip()
    if value:
        return value
    return str(_validation_broker_result(record).get("closure_outcome") or "").strip()


def _validation_broker_selected_scope(record: dict[str, Any]) -> str:
    value = str(record.get("validation_broker_selected_scope") or "").strip()
    if value:
        return value
    return str(_validation_broker_result(record).get("selected_scope") or "").strip()


def _is_material_edit(record: dict[str, Any], stage: str, paths: list[str]) -> bool:
    changed_paths = _string_list(record.get("changed_paths")) or _string_list(record.get("added_paths"))
    tool_name = str(record.get("tool_name") or "")
    command_program = str(record.get("command_program") or "")
    if changed_paths:
        return True
    if tool_name in EDIT_TOOLS:
        return True
    if stage not in {"edit", "repair"}:
        return False
    if command_program in READ_ONLY_COMMANDS:
        return False
    return bool(paths)


def _is_test_command(command_program: str) -> bool:
    return command_program in TEST_COMMANDS


def _runtime_for_record(record: dict[str, Any]) -> str:
    runtime = str(record.get("runtime") or "generic").strip().lower()
    return runtime if runtime in {"codex", "claude", "copilot", "generic"} else "generic"


def _memory_event_to_record(event: dict[str, Any]) -> dict[str, Any]:
    record = {
        "_source": "memory",
        "timestamp_utc": event.get("timestamp") or event.get("created_at", ""),
        "event_name": "MemoryEvent",
        "runtime": "generic",
        "session_id": event.get("session_id", ""),
        "repo_hash": event.get("repo_hash", ""),
        "task_fingerprint": event.get("task_fingerprint", ""),
        "kind": event.get("kind", ""),
        "type": event.get("type", ""),
        "bounded_paths": event.get("bounded_paths", []),
        "paths": event.get("bounded_paths") or event.get("paths", []),
        "outcome": event.get("outcome", ""),
        "owner_skill": event.get("owner_skill", ""),
        "reviewer_skill": event.get("reviewer_skill", ""),
    }
    event_type = str(event.get("type") or "")
    kind = str(event.get("kind") or "")
    if event_type == "validation_result" or kind == "validation_pattern":
        record["validation_evidence_detected"] = True
        record["validation_result_outcome"] = event.get("outcome", "")
    if event_type == "review_finding" or kind == "review_finding_pattern":
        record["review_evidence_seen"] = True
    if event_type == "implementation_attempt":
        record["changed_paths"] = event.get("paths", [])
    if event_type == "repeat_failure" or kind == "repeat_failure":
        record["outcome"] = "fail"
    if event_type == "fragile_file" or kind == "fragile_file":
        record["memory_summary_seen"] = True
    return record


def _first_non_empty(values: Iterable[Any]) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _last_non_empty(values: Iterable[Any]) -> str:
    result = ""
    for value in values:
        text = str(value or "").strip()
        if text:
            result = text
    return result


def _fingerprint(repo_hash: str, session_id: str, records: list[dict[str, Any]]) -> str:
    payload = {
        "repo_hash": repo_hash,
        "session_id": session_id,
        "started_at": _first_non_empty(record.get("timestamp_utc") or record.get("created_at") for record in records),
        "paths": sorted(_unique(path for record in records for path in _paths_for_record(record)))[:20],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _bounded_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit]


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
