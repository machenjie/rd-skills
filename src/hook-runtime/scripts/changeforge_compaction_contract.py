#!/usr/bin/env python3
"""Bounded context snapshot contract for ChangeForge compaction hooks."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable

SCHEMA_VERSION = 1
MAX_ITEMS = 20
MAX_TEXT = 240
MAX_MAPPING_KEYS = 40
MAX_SNAPSHOTS = 5
OPERATIONAL_CONTEXT_FIELDS = ("changed_paths", "read_paths")

REQUIRED_CONTEXT_FIELDS = (
    "route_id",
    "selected_skills",
    "selected_capabilities",
    "required_quality_gates",
    "current_stage",
    "pdd_summary",
    "ddd_invariants",
    "sdd_decisions",
    "tdd_validation_plan",
    "changed_paths",
    "read_paths",
    "validation_results",
    "validation_freshness",
    "review_findings",
    "repair_events",
    "rereview_events",
    "residual_risk",
    "memory_references",
    "repo_graph_references",
    "active_skill_context",
    "last_material_edit_index",
    "last_validation_command_index",
)

SENSITIVE_KEY_TOKENS = (
    "raw_prompt",
    "prompt",
    "assistant_message",
    "raw_assistant",
    "raw_command",
    "command_output",
    "stdout",
    "stderr",
    "env",
    "environment",
    "secret",
    "password",
    "api_key",
    "apikey",
    "token",
    "full_diff",
    "file_contents",
    "content",
)
ABSOLUTE_PATH_RE = re.compile(
    r"(/Users/[^\s\"'<>]+|/home/[^\s\"'<>]+|/private/var/[^\s\"'<>]+|"
    r"/var/folders/[^\s\"'<>]+|/tmp/[^\s\"'<>]+|[A-Za-z]:\\Users\\[^\s\"'<>]+)"
)
SECRET_RE = re.compile(
    r"(sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+|"
    r"(?i:OPENAI_API_KEY|CODEX_API_KEY|api[_-]?key|access[_-]?token|bearer[_-]?token)"
    r"\s*[:=]\s*[A-Za-z0-9_./+=-]{8,})"
)


def compaction_event_phase(event: dict[str, Any]) -> str:
    """Classify vendor compaction event names into a stable phase label."""
    raw = " ".join(
        str(event.get(key) or "")
        for key in ("hook_event_name", "hookEventName", "event_name", "eventName", "source", "reason", "matcher")
    ).casefold()
    compacted = re.sub(r"[^a-z0-9]", "", raw)
    if "precompact" in compacted or "beforecompact" in compacted:
        return "pre_compact"
    if "postcompact" in compacted or "aftercompact" in compacted:
        return "post_compact"
    if "sessionstart" in compacted and "compact" in compacted:
        return "session_compact"
    return "compact"


def snapshot_from_state(
    state: dict[str, Any],
    event: dict[str, Any] | None = None,
    *,
    snapshot_kind: str | None = None,
) -> dict[str, Any]:
    """Build a machine-readable bounded snapshot from hook state."""
    event = event or {}
    active = state.get("active_skill_context") if isinstance(state.get("active_skill_context"), dict) else {}
    last_edit = _safe_int(state.get("last_material_edit_index"))
    last_validation = _safe_int(state.get("last_validation_command_index"))
    kind = snapshot_kind or compaction_event_phase(event)
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": _snapshot_id(state, event, kind),
        "snapshot_kind": kind,
        "event_name": _event_name(event),
        "route_id": _first_text(active, "route_id", "route", "route_key")
        or _first_text(state, "route_id", "owner_skill", "turn_id"),
        "selected_skills": _first_list(active, "selected_skills", fallback=state.get("suggested_skills")),
        "selected_capabilities": _first_list(
            active,
            "selected_capabilities",
            fallback=state.get("suggested_capabilities"),
            max_items=30,
        ),
        "required_quality_gates": _first_list(active, "required_quality_gates", fallback=state.get("suggested_gates")),
        "current_stage": _first_text(active, "current_stage", "stage") or str(state.get("turn_stage") or ""),
        "pdd_summary": _first_list(active, "pdd_summary", "acceptance_criteria", fallback=state.get("implementation_preflights")),
        "ddd_invariants": _first_list(active, "ddd_invariants", "invariants", fallback=state.get("risk_surfaces")),
        "sdd_decisions": _first_list(active, "sdd_decisions", "placement_decisions", fallback=state.get("structure_findings")),
        "tdd_validation_plan": _first_list(active, "tdd_validation_plan", "validation_plan", fallback=state.get("validation_results")),
        "changed_paths": _path_list(state.get("changed_paths")),
        "read_paths": _path_list(state.get("read_paths")),
        "validation_results": _clean_list(state.get("validation_results")),
        "validation_freshness": _validation_freshness(last_edit, last_validation, state),
        "review_findings": _clean_list(state.get("review_findings")),
        "repair_events": _clean_list(state.get("repair_events")),
        "rereview_events": _clean_list(state.get("rereview_events")),
        "residual_risk": _clean_list(state.get("closure_risk_surfaces") or active.get("residual_risk")),
        "memory_references": _clean_list(state.get("reference_loads") or active.get("memory_references"), max_items=10),
        "repo_graph_references": _clean_list(state.get("reuse_findings") or active.get("repo_graph_references"), max_items=10),
        "active_skill_context": _clean_mapping(active),
        "last_material_edit_index": last_edit,
        "last_validation_command_index": last_validation,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    snapshot = sanitize_compaction_snapshot(snapshot)
    missing = missing_required_fields(snapshot)
    snapshot["missing_required_fields"] = missing
    snapshot["privacy_redaction_status"] = "pass" if not privacy_findings(snapshot) else "fail"
    snapshot["redacted_required_fields"] = redacted_required_fields(snapshot)
    snapshot["context_usable_fields"] = context_usable_fields(snapshot)
    snapshot["context_unusable_fields"] = context_unusable_fields(snapshot)
    snapshot["context_usable_status"] = "pass" if not snapshot["context_unusable_fields"] else "fail"
    snapshot["context_retention_status"] = _context_retention_status(snapshot)
    warnings = [f"missing_required_field:{field}" for field in missing]
    warnings.extend(f"redacted_required_field:{field}" for field in snapshot["redacted_required_fields"])
    warnings.extend(f"context_unusable_field:{field}" for field in snapshot["context_unusable_fields"])
    snapshot["warnings"] = warnings[:20]
    return snapshot


def sanitize_compaction_snapshot(snapshot: Any) -> dict[str, Any]:
    """Return a bounded allowlisted snapshot with sensitive fields removed or redacted."""
    if isinstance(snapshot, str):
        try:
            parsed = json.loads(snapshot)
        except json.JSONDecodeError:
            return {}
        snapshot = parsed
    if not isinstance(snapshot, dict):
        snapshot = {}
    clean: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": _clean_text(snapshot.get("snapshot_id") or _hash_text(json.dumps(snapshot, sort_keys=True))),
        "snapshot_kind": _snapshot_kind(snapshot.get("snapshot_kind")),
        "event_name": _clean_text(snapshot.get("event_name"), limit=80),
        "route_id": _clean_text(snapshot.get("route_id"), limit=160),
        "selected_skills": _clean_list(snapshot.get("selected_skills")),
        "selected_capabilities": _clean_list(snapshot.get("selected_capabilities"), max_items=30),
        "required_quality_gates": _clean_list(snapshot.get("required_quality_gates")),
        "current_stage": _clean_text(snapshot.get("current_stage"), limit=120),
        "pdd_summary": _clean_list(snapshot.get("pdd_summary"), max_items=8),
        "ddd_invariants": _clean_list(snapshot.get("ddd_invariants"), max_items=10),
        "sdd_decisions": _clean_list(snapshot.get("sdd_decisions"), max_items=10),
        "tdd_validation_plan": _clean_list(snapshot.get("tdd_validation_plan"), max_items=10),
        "changed_paths": _path_list(snapshot.get("changed_paths")),
        "read_paths": _path_list(snapshot.get("read_paths")),
        "validation_results": _clean_list(snapshot.get("validation_results"), max_items=12),
        "validation_freshness": _clean_text(snapshot.get("validation_freshness"), limit=160),
        "review_findings": _clean_list(snapshot.get("review_findings"), max_items=12),
        "repair_events": _clean_list(snapshot.get("repair_events"), max_items=12),
        "rereview_events": _clean_list(snapshot.get("rereview_events"), max_items=12),
        "residual_risk": _clean_list(snapshot.get("residual_risk"), max_items=10),
        "memory_references": _clean_list(snapshot.get("memory_references"), max_items=10),
        "repo_graph_references": _clean_list(snapshot.get("repo_graph_references"), max_items=10),
        "active_skill_context": _clean_mapping(snapshot.get("active_skill_context")),
        "last_material_edit_index": _safe_int(snapshot.get("last_material_edit_index")),
        "last_validation_command_index": _safe_int(snapshot.get("last_validation_command_index")),
    }
    clean["missing_required_fields"] = missing_required_fields(clean)
    clean["privacy_redaction_status"] = "pass" if not privacy_findings(clean) else "fail"
    clean["redacted_required_fields"] = redacted_required_fields(clean)
    clean["context_usable_fields"] = context_usable_fields(clean)
    clean["context_unusable_fields"] = context_unusable_fields(clean)
    clean["context_usable_status"] = "pass" if not clean["context_unusable_fields"] else "fail"
    clean["context_retention_status"] = _context_retention_status(clean)
    raw_warnings = snapshot.get("warnings") if isinstance(snapshot.get("warnings"), list) else []
    clean["warnings"] = _clean_list(
        [
            *raw_warnings,
            *[f"missing_required_field:{field}" for field in clean["missing_required_fields"]],
            *[f"redacted_required_field:{field}" for field in clean["redacted_required_fields"]],
            *[f"context_unusable_field:{field}" for field in clean["context_unusable_fields"]],
        ]
    )
    return clean


def missing_required_fields(snapshot: dict[str, Any]) -> list[str]:
    """Return required fields that are absent or empty after sanitization."""
    missing: list[str] = []
    for field in REQUIRED_CONTEXT_FIELDS:
        value = snapshot.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field)
    return missing


def restored_required_fields(snapshot: dict[str, Any]) -> list[str]:
    """Return required fields that have usable bounded values."""
    missing = set(missing_required_fields(snapshot))
    unusable = set(context_unusable_fields(snapshot))
    return [field for field in REQUIRED_CONTEXT_FIELDS if field not in missing and field not in unusable]


def redacted_required_fields(snapshot: dict[str, Any]) -> list[str]:
    """Return required fields whose value is privacy-safe but operationally redacted."""
    redacted: list[str] = []
    for field in REQUIRED_CONTEXT_FIELDS:
        value = snapshot.get(field)
        if field in OPERATIONAL_CONTEXT_FIELDS and _has_local_path_redaction(value):
            redacted.append(field)
    return redacted


def context_usable_fields(snapshot: dict[str, Any]) -> list[str]:
    """Return required fields that can be used to continue work after compaction."""
    usable: list[str] = []
    missing = set(missing_required_fields(snapshot))
    for field in REQUIRED_CONTEXT_FIELDS:
        if field in missing:
            continue
        value = snapshot.get(field)
        if field in OPERATIONAL_CONTEXT_FIELDS and not _path_values_usable(value):
            continue
        usable.append(field)
    return usable


def context_unusable_fields(snapshot: dict[str, Any]) -> list[str]:
    """Return required fields that are present but not usable for continuation."""
    unusable: list[str] = []
    missing = set(missing_required_fields(snapshot))
    for field in REQUIRED_CONTEXT_FIELDS:
        if field in missing:
            continue
        value = snapshot.get(field)
        if field in OPERATIONAL_CONTEXT_FIELDS and not _path_values_usable(value):
            unusable.append(field)
    return unusable


def privacy_findings(value: Any) -> list[str]:
    """Detect forbidden raw prompt, secret, environment, path, or full-content remnants."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    findings: list[str] = []
    if SECRET_RE.search(text):
        findings.append("secret_or_api_key_pattern")
    if ABSOLUTE_PATH_RE.search(text):
        findings.append("absolute_local_path")
    lowered = text.casefold()
    for token in ("raw_prompt", "raw assistant", "raw_command_output", "full_diff_body", "full_file_contents"):
        if token in lowered:
            findings.append(token.replace(" ", "_"))
    return sorted(set(findings))


def latest_snapshot(values: Any) -> dict[str, Any]:
    """Return the latest valid snapshot from a list of dict or JSON snapshot values."""
    snapshots = [sanitize_compaction_snapshot(value) for value in _as_list(values)]
    snapshots = [snapshot for snapshot in snapshots if snapshot.get("snapshot_id")]
    if not snapshots:
        return {}
    snapshots.sort(key=snapshot_priority_key)
    return snapshots[-1]


def snapshot_priority_key(snapshot: dict[str, Any]) -> tuple[int, int, str]:
    """Sort latest active snapshots after less complete checkpoints."""
    last_edit = _safe_int(snapshot.get("last_material_edit_index"))
    last_validation = _safe_int(snapshot.get("last_validation_command_index"))
    completeness = len(restored_required_fields(snapshot))
    return (max(last_edit, last_validation), completeness, str(snapshot.get("snapshot_id") or ""))


def preserve_required_snapshots(existing: Any, incoming: Any = (), *, limit: int = MAX_SNAPSHOTS) -> list[Any]:
    """Preserve critical compact checkpoints instead of trimming by insertion time only."""
    raw_values = [*_as_list(existing), *_as_list(incoming)]
    legacy = [
        str(value).strip()[:MAX_TEXT]
        for value in raw_values
        if isinstance(value, str) and str(value).strip() and not str(value).lstrip().startswith("{")
    ]
    snapshots = [sanitize_compaction_snapshot(value) for value in raw_values]
    by_id: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        snapshot_id = str(snapshot.get("snapshot_id") or "")
        if not snapshot_id:
            continue
        current = by_id.get(snapshot_id)
        if current is None or snapshot_priority_key(snapshot) >= snapshot_priority_key(current):
            by_id[snapshot_id] = snapshot
    snapshots = list(by_id.values())
    if not snapshots:
        return _dedupe_text(legacy)[-limit:]

    kept: list[dict[str, Any]] = []

    def add(snapshot: dict[str, Any] | None) -> None:
        if not snapshot:
            return
        if any(item.get("snapshot_id") == snapshot.get("snapshot_id") for item in kept):
            return
        kept.append(snapshot)

    complete = [snapshot for snapshot in snapshots if not missing_required_fields(snapshot)]
    add(max(complete, key=snapshot_priority_key, default=None))
    add(max(snapshots, key=lambda snapshot: _safe_int(snapshot.get("last_material_edit_index")), default=None))
    add(max((snapshot for snapshot in snapshots if _snapshot_has_stale_validation(snapshot)), key=snapshot_priority_key, default=None))
    add(max((snapshot for snapshot in snapshots if _snapshot_has_unresolved_review(snapshot)), key=snapshot_priority_key, default=None))
    add(max((snapshot for snapshot in snapshots if _snapshot_has_repair_state(snapshot)), key=snapshot_priority_key, default=None))

    for snapshot in sorted(snapshots, key=snapshot_priority_key, reverse=True):
        add(snapshot)
        if len(kept) >= limit:
            break
    kept = kept[:limit]
    kept.sort(key=snapshot_priority_key)
    return [*kept, *_dedupe_text(legacy)[-limit:]]


def merge_active_context(existing: Any, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Fill missing active context fields from a snapshot without overwriting richer context."""
    base = _clean_mapping(existing)
    source = snapshot.get("active_skill_context") if isinstance(snapshot.get("active_skill_context"), dict) else {}
    source = _clean_mapping(source)
    for key, value in source.items():
        if isinstance(value, list):
            base[key] = _bounded_context_union(base.get(key), value)
            continue
        if key == "validation_freshness":
            base[key] = _merge_validation_freshness(base.get(key), value)
            continue
        if _has_value(base.get(key)):
            continue
        base[key] = value
    for snapshot_key, context_key in (
        ("route_id", "route_id"),
        ("selected_skills", "selected_skills"),
        ("selected_capabilities", "selected_capabilities"),
        ("required_quality_gates", "required_quality_gates"),
        ("current_stage", "current_stage"),
        ("pdd_summary", "pdd_summary"),
        ("ddd_invariants", "ddd_invariants"),
        ("sdd_decisions", "sdd_decisions"),
        ("tdd_validation_plan", "tdd_validation_plan"),
        ("changed_paths", "changed_paths"),
        ("read_paths", "read_paths"),
        ("validation_results", "validation_results"),
        ("validation_freshness", "validation_freshness"),
        ("review_findings", "review_findings"),
        ("repair_events", "repair_events"),
        ("rereview_events", "rereview_events"),
        ("residual_risk", "residual_risk"),
        ("memory_references", "memory_references"),
        ("repo_graph_references", "repo_graph_references"),
        ("last_material_edit_index", "last_material_edit_index"),
        ("last_validation_command_index", "last_validation_command_index"),
    ):
        value = snapshot.get(snapshot_key)
        if isinstance(value, list):
            base[context_key] = _bounded_context_union(base.get(context_key), value)
            continue
        if context_key == "validation_freshness":
            base[context_key] = _merge_validation_freshness(base.get(context_key), value)
            continue
        if not _has_value(base.get(context_key)) and _has_value(value):
            base[context_key] = snapshot[snapshot_key]
    return _clean_mapping(base)


def format_compaction_lines(snapshot: dict[str, Any], state: dict[str, Any] | None = None) -> list[str]:
    """Render prioritized bounded reinjection lines from a snapshot and current state."""
    state = state or {}
    missing = missing_required_fields(snapshot)
    lines = [
        "- P0 route_id: " + _display(snapshot.get("route_id")),
        "- P0 current_stage: " + _display(snapshot.get("current_stage")),
        "- P0 required_quality_gates: " + _display(snapshot.get("required_quality_gates")),
        "- P0 changed_paths: " + _display(snapshot.get("changed_paths")),
        "- P0 validation_freshness: " + _display(snapshot.get("validation_freshness")),
        "- P0 review_findings: " + _display(snapshot.get("review_findings")),
        "- P0 repair_events: " + _display(snapshot.get("repair_events")),
        "- P0 rereview_events: " + _display(snapshot.get("rereview_events")),
        "- P1 pdd_summary: " + _display(snapshot.get("pdd_summary")),
        "- P1 ddd_invariants: " + _display(snapshot.get("ddd_invariants")),
        "- P1 sdd_decisions: " + _display(snapshot.get("sdd_decisions")),
        "- P1 tdd_validation_plan: " + _display(snapshot.get("tdd_validation_plan")),
        "- P1 memory_references: " + _display(snapshot.get("memory_references")),
        "- P1 repo_graph_references: " + _display(snapshot.get("repo_graph_references")),
        "- P1 residual_risk: " + _display(snapshot.get("residual_risk")),
    ]
    adapter = state.get("runtime_adapter") if isinstance(state.get("runtime_adapter"), dict) else {}
    unsupported = adapter.get("unsupported_checks") if isinstance(adapter.get("unsupported_checks"), list) else []
    if unsupported:
        lines.append("- P2 unsupported_runtime_checks: " + _display(unsupported))
    if missing:
        lines.append("- warning missing_required_context_fields: " + ", ".join(missing))
    redacted = redacted_required_fields(snapshot)
    if redacted:
        lines.append("- warning redacted_required_context_fields: " + ", ".join(redacted))
    unusable = context_unusable_fields(snapshot)
    if unusable:
        lines.append("- warning context_unusable_fields: " + ", ".join(unusable))
    privacy = privacy_findings(snapshot)
    if privacy:
        lines.append("- warning compaction_privacy_findings: " + ", ".join(privacy))
    lines.append("- privacy_redaction_status: " + _display(snapshot.get("privacy_redaction_status")))
    lines.append("- context_usable_status: " + _display(snapshot.get("context_usable_status")))
    lines.append("- context_retention_status: " + _display(snapshot.get("context_retention_status")))
    return lines


def _snapshot_id(state: dict[str, Any], event: dict[str, Any], kind: str) -> str:
    source = json.dumps(
        {
            "kind": kind,
            "turn_id": state.get("turn_id"),
            "event_index": state.get("event_index"),
            "event": _event_name(event),
            "last_edit": state.get("last_material_edit_index"),
            "last_validation": state.get("last_validation_command_index"),
        },
        sort_keys=True,
    )
    return f"compact-{_hash_text(source)}"


def _event_name(event: dict[str, Any]) -> str:
    for key in ("hook_event_name", "hookEventName", "event_name", "eventName"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return _clean_text(value, limit=80)
    return ""


def _snapshot_kind(value: Any) -> str:
    text = str(value or "compact").strip()
    return text if text in {"pre_compact", "post_compact", "session_compact", "compact"} else "compact"


def _validation_freshness(last_edit: int, last_validation: int, state: dict[str, Any]) -> str:
    explicit = state.get("validation_freshness")
    if isinstance(explicit, str) and explicit.strip():
        return _clean_text(explicit, limit=160)
    if last_validation <= 0:
        return "not_validated"
    if last_edit > last_validation:
        return "stale_after_material_change"
    return "fresh_after_latest_material_change"


def _first_text(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return _clean_text(value)
    return ""


def _first_list(mapping: dict[str, Any], *keys: str, fallback: Any = None, max_items: int = MAX_ITEMS) -> list[str]:
    for key in keys:
        value = mapping.get(key)
        items = _clean_list(value, max_items=max_items)
        if items:
            return items
    return _clean_list(fallback, max_items=max_items)


def _clean_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for key, raw in value.items():
        name = str(key).strip()[:80]
        if not name or _sensitive_key(name):
            continue
        if isinstance(raw, dict):
            child = _clean_mapping(raw)
            if child:
                cleaned[name] = child
        elif isinstance(raw, (list, tuple, set)):
            items = _clean_list(raw)
            if items:
                cleaned[name] = items
        else:
            text = _clean_text(raw)
            if text:
                cleaned[name] = text
        if len(cleaned) >= MAX_MAPPING_KEYS:
            break
    return cleaned


def _clean_list(value: Any, *, max_items: int = MAX_ITEMS) -> list[str]:
    items: list[str] = []
    for raw in _as_list(value):
        if isinstance(raw, dict):
            text = _clean_text(json.dumps(_clean_mapping(raw), sort_keys=True))
        else:
            text = _clean_text(raw)
        if text and text not in items:
            items.append(text)
        if len(items) >= max_items:
            break
    return items


def _path_list(value: Any) -> list[str]:
    return [_clean_path(item) for item in _clean_list(value) if _clean_path(item)]


def _clean_path(value: Any) -> str:
    text = _clean_text(value, limit=200)
    if not text:
        return ""
    text = text.replace("\\", "/").lstrip("./")
    text = ABSOLUTE_PATH_RE.sub("<local-path>", text)
    if text.startswith("<local-path>"):
        return "<local-path>"
    return text[:200]


def _path_values_usable(value: Any) -> bool:
    paths = _path_list(value)
    if not paths:
        return False
    return all(_is_repo_relative_path(path) for path in paths)


def _is_repo_relative_path(path: str) -> bool:
    if not path or path == "<local-path>" or "<local-path>" in path:
        return False
    if path.startswith(("/", "~")):
        return False
    if re.match(r"^[A-Za-z]:/", path):
        return False
    if "://" in path or path.startswith("../"):
        return False
    return True


def _has_local_path_redaction(value: Any) -> bool:
    return any("<local-path>" in str(item) for item in _as_list(value))


def _clean_text(value: Any, *, limit: int = MAX_TEXT) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = SECRET_RE.sub("<redacted-secret>", text)
    text = ABSOLUTE_PATH_RE.sub("<local-path>", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    return text[:limit]


def _sensitive_key(key: str) -> bool:
    lowered = key.casefold()
    return any(token in lowered for token in SENSITIVE_KEY_TOKENS)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _safe_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _has_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def _context_retention_status(snapshot: dict[str, Any]) -> str:
    if missing_required_fields(snapshot):
        return "partial"
    redacted_operational = [
        field for field in redacted_required_fields(snapshot) if field in OPERATIONAL_CONTEXT_FIELDS
    ]
    if redacted_operational:
        return "partial"
    if snapshot.get("privacy_redaction_status") != "pass":
        return "fail"
    if snapshot.get("context_usable_status") != "pass":
        return "partial"
    return "pass"


def _bounded_context_union(existing: Any, incoming: Any) -> list[str]:
    values = _clean_list([*_as_list(existing), *_as_list(incoming)], max_items=MAX_ITEMS * 2)
    if not values:
        return []

    def score(item: str) -> tuple[int, int]:
        lowered = item.casefold()
        risky = any(term in lowered for term in ("critical", "p0", "security", "stale", "unresolved", "repair"))
        return (0 if risky else 1, values.index(item))

    return sorted(values, key=score)[:MAX_ITEMS]


def _merge_validation_freshness(existing: Any, incoming: Any) -> str:
    current = _clean_text(existing, limit=160)
    candidate = _clean_text(incoming, limit=160)
    if "stale" in current.casefold() and candidate and "rerun" not in candidate.casefold():
        return current
    if "stale" in candidate.casefold():
        return candidate
    return current or candidate


def _snapshot_has_stale_validation(snapshot: dict[str, Any]) -> bool:
    text = json.dumps(
        {
            "validation_freshness": snapshot.get("validation_freshness"),
            "validation_results": snapshot.get("validation_results"),
        },
        sort_keys=True,
    ).casefold()
    return "stale" in text


def _snapshot_has_unresolved_review(snapshot: dict[str, Any]) -> bool:
    for value in _clean_list(snapshot.get("review_findings"), max_items=MAX_ITEMS):
        lowered = value.casefold()
        if "unresolved" in lowered:
            return True
        if not any(term in lowered for term in ("resolved", "fixed", "closed", "rereview passed")):
            return True
    return False


def _snapshot_has_repair_state(snapshot: dict[str, Any]) -> bool:
    return bool(_clean_list(snapshot.get("repair_events")) or _clean_list(snapshot.get("rereview_events")))


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _display(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item)[:80] for item in value[:6]) or "not_collected"
    if isinstance(value, dict):
        return ", ".join(f"{key}={str(val)[:40]}" for key, val in list(value.items())[:6]) or "not_collected"
    return str(value or "not_collected")[:160]


__all__ = [
    "REQUIRED_CONTEXT_FIELDS",
    "context_unusable_fields",
    "context_usable_fields",
    "compaction_event_phase",
    "format_compaction_lines",
    "latest_snapshot",
    "merge_active_context",
    "missing_required_fields",
    "preserve_required_snapshots",
    "privacy_findings",
    "redacted_required_fields",
    "restored_required_fields",
    "sanitize_compaction_snapshot",
    "snapshot_from_state",
    "snapshot_priority_key",
]
