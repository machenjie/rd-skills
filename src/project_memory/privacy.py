"""Sanitization helpers for Project Memory Governance."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from project_memory import MEMORY_SCHEMA_VERSION
from project_memory.source_evidence import FRESHNESS_VALUES, is_sha256, sha256_file


MAX_ITEMS = 50
MAX_VALUE_LEN = 300
MAX_SUMMARY_LEN = 240
MAX_PATH_LEN = 200
MEMORY_TYPES = {
    "route_decision",
    "context_pack",
    "implementation_attempt",
    "validation_result",
    "review_finding",
    "repair_attempt",
    "accepted_decision",
    "rejected_decision",
    "fragile_file",
    "validated_command",
    "hook_false_positive",
    "hook_false_negative",
    "repeat_failure",
}
MEMORY_KINDS = {
    "fragile_file",
    "repeat_failure",
    "validation_pattern",
    "review_finding_pattern",
    "module_convention",
    "generated_source_mapping",
    "route_correction",
    "false_positive_hook",
    "false_negative_hook",
}
KIND_BY_TYPE = {
    "route_decision": "route_correction",
    "context_pack": "generated_source_mapping",
    "implementation_attempt": "module_convention",
    "validation_result": "validation_pattern",
    "validated_command": "validation_pattern",
    "review_finding": "review_finding_pattern",
    "repair_attempt": "review_finding_pattern",
    "accepted_decision": "module_convention",
    "rejected_decision": "module_convention",
    "fragile_file": "fragile_file",
    "hook_false_positive": "false_positive_hook",
    "hook_false_negative": "false_negative_hook",
    "repeat_failure": "repeat_failure",
}
TYPE_BY_KIND = {
    "fragile_file": "fragile_file",
    "repeat_failure": "repeat_failure",
    "validation_pattern": "validation_result",
    "review_finding_pattern": "review_finding",
    "module_convention": "implementation_attempt",
    "generated_source_mapping": "context_pack",
    "route_correction": "route_decision",
    "false_positive_hook": "hook_false_positive",
    "false_negative_hook": "hook_false_negative",
}
OUTCOMES = {"success", "failed", "partial", "blocked", "unknown"}
CONFIDENCES = {"low", "medium", "high"}
PROMOTION_STATUSES = {"raw", "candidate", "approved", "rejected"}
PRIVACY_CLASSES = {"safe_bounded", "redacted", "rejected_sensitive"}
MEMORY_SOURCES = {"telemetry", "trajectory", "human", "validator"}
HASH_ALGORITHMS = {"sha256"}
FORBIDDEN_KEY_TOKENS = (
    "prompt",
    "raw_prompt",
    "stdout",
    "stderr",
    "environment",
    "env",
    "secret",
    "password",
    "api_key",
    "apikey",
    "token_value",
)
SECRET_VALUE_RE = re.compile(
    r"(secret|password|api[_-]?key|bearer\s+[a-z0-9._-]{12,}|token=)",
    re.IGNORECASE,
)


def repo_hash_for_path(repo: str | Path) -> str:
    """Return the path-free repository hash used by hook telemetry."""
    try:
        key = str(Path(repo).expanduser().resolve())
    except OSError:
        key = str(repo)
    return hash_text(key)


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_memory_event(raw: dict[str, Any], *, repo: str | Path | None = None) -> dict[str, Any]:
    """Return a bounded MemoryEvent, ignoring unsafe or unknown input fields."""
    source = raw if isinstance(raw, dict) else {}
    repo_hash = clean_scalar(source.get("repo_hash"), default="")
    if not repo_hash and repo is not None:
        repo_hash = repo_hash_for_path(repo)
    repo_hash = repo_hash or "unknown"
    timestamp = clean_scalar(source.get("timestamp") or source.get("created_at"), default=now_utc())
    raw_kind = clean_enum(source.get("kind"), MEMORY_KINDS, "")
    event_type = clean_enum(
        source.get("type"),
        MEMORY_TYPES,
        TYPE_BY_KIND.get(raw_kind, "implementation_attempt"),
    )
    kind = raw_kind or KIND_BY_TYPE.get(event_type, "module_convention")
    outcome = clean_enum(source.get("outcome"), OUTCOMES, "unknown")
    confidence = clean_enum(source.get("confidence"), CONFIDENCES, "medium")
    promotion_status = clean_enum(source.get("promotion_status"), PROMOTION_STATUSES, "raw")
    paths = clean_paths(source.get("bounded_paths") or source.get("paths"), repo=repo)
    symbols = clean_list(source.get("symbols"))
    owner_skill = clean_scalar(source.get("owner_skill"), default="")
    task_fingerprint = clean_scalar(source.get("task_fingerprint"), default="")
    if not task_fingerprint:
        task_fingerprint = memory_task_fingerprint(paths, owner_skill, source.get("kind") or source.get("type"))
    summary = clean_summary(source.get("summary"), default=_summary_from_event(kind, paths, outcome))
    sensitive_input = contains_forbidden_key(source) or contains_sensitive_value(source)
    privacy_default = "redacted" if sensitive_input else "safe_bounded"
    privacy_class = clean_enum(
        source.get("privacy_class"),
        PRIVACY_CLASSES,
        privacy_default,
    )
    event_id = clean_scalar(source.get("event_id"), default="")
    if not event_id:
        event_id = _deterministic_event_id(repo_hash, timestamp, kind, paths, summary, source)
    elif not event_id.startswith("mem_"):
        event_id = "mem_" + hash_text(event_id)
    retention_policy = clean_scalar(
        source.get("retention_policy"),
        default=_default_retention_policy(kind),
    )
    memory_source = clean_enum(source.get("source"), MEMORY_SOURCES, "telemetry")
    commit_sha = clean_scalar(source.get("commit_sha"), default="")
    source_evidence = sanitize_source_evidence(
        source.get("source_evidence"),
        repo=repo,
        fallback_path=paths[0] if paths else "",
        event_id=event_id,
        timestamp=timestamp,
    )
    event = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "event_id": event_id,
        "repo_hash": repo_hash,
        "commit_sha": commit_sha,
        "timestamp": timestamp,
        "kind": kind,
        "bounded_paths": paths,
        "summary": summary,
        "privacy_class": privacy_class,
        "retention_policy": retention_policy,
        "source": memory_source,
        "task_fingerprint": task_fingerprint,
        "type": event_type,
        "paths": paths,
        "symbols": symbols,
        "owner_skill": owner_skill,
        "reviewer_skill": clean_scalar(source.get("reviewer_skill"), default=""),
        "route_manifest_hash": clean_scalar(source.get("route_manifest_hash"), default=""),
        "outcome": outcome,
        "evidence_refs": clean_list(source.get("evidence_refs")),
        "confidence": confidence,
        "promotion_status": promotion_status,
        "created_at": timestamp,
    }
    if source_evidence:
        event["source_evidence"] = source_evidence
    return event


def sanitize_memory_query(raw: dict[str, Any], *, repo: str | Path | None = None) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    repo_hash = clean_scalar(source.get("repo_hash"), default="")
    if not repo_hash and repo is not None:
        repo_hash = repo_hash_for_path(repo)
    return {
        "repo_hash": repo_hash,
        "task": clean_scalar(source.get("task"), default=""),
        "task_fingerprint": clean_scalar(source.get("task_fingerprint"), default=""),
        "paths": clean_paths(source.get("bounded_paths") or source.get("paths"), repo=repo),
        "symbols": clean_list(source.get("symbols")),
        "stage": clean_scalar(source.get("stage"), default=""),
        "capabilities": clean_list(source.get("capabilities")),
        "graph_freshness": clean_enum(
            source.get("graph_freshness"),
            {"current", "stale", "unknown"},
            "unknown",
        ),
        "changed_files": clean_changed_files(source.get("changed_files"), repo=repo),
        "owner_skill": clean_scalar(source.get("owner_skill"), default=""),
        "reviewer_skill": clean_scalar(source.get("reviewer_skill"), default=""),
        "limit": clean_int(source.get("limit"), default=20, minimum=1, maximum=100),
    }


def memory_task_fingerprint(
    paths: Iterable[str],
    owner_skill: object = "",
    task_hint: object = "",
) -> str:
    """Build a prompt-free task fingerprint from bounded operational facts."""
    parts = [str(owner_skill or "").strip(), str(task_hint or "").strip()]
    parts.extend(sorted(str(path).strip() for path in paths if str(path).strip())[:10])
    key = "|".join(part for part in parts if part)
    return hash_text(key or "unknown-task")


def clean_enum(value: object, allowed: set[str], default: str) -> str:
    text = clean_scalar(value, default="")
    return text if text in allowed else default


def clean_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def clean_scalar(value: object, *, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    if not text or SECRET_VALUE_RE.search(text):
        return default
    return text[:MAX_VALUE_LEN]


def clean_summary(value: object, *, default: str = "") -> str:
    """Return a single bounded summary string with secret-like values removed."""
    text = clean_scalar(value, default=default)
    return text[:MAX_SUMMARY_LEN]


def clean_list(value: object) -> list[str]:
    values = value if isinstance(value, (list, tuple, set)) else []
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = clean_scalar(item, default="")
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if len(result) >= MAX_ITEMS:
            break
    return result


def clean_paths(value: object, *, repo: str | Path | None = None) -> list[str]:
    values = value if isinstance(value, (list, tuple, set)) else []
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        path = clean_path(item, repo=repo)
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(path)
        if len(result) >= MAX_ITEMS:
            break
    return result


def clean_changed_files(value: object, *, repo: str | Path | None = None) -> list[dict[str, str]]:
    """Return bounded changed-file freshness markers using relative paths only."""
    if not isinstance(value, (list, tuple)):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        path = clean_path(item.get("path"), repo=repo)
        changed_at = clean_scalar(item.get("changed_at") or item.get("mtime"), default="")
        if not path:
            continue
        result.append({"path": path, "changed_at": changed_at})
        if len(result) >= MAX_ITEMS:
            break
    return result


def sanitize_source_evidence(
    value: object,
    *,
    repo: str | Path | None = None,
    fallback_path: object = "",
    event_id: object = "",
    timestamp: object = "",
) -> dict[str, str]:
    """Return optional source evidence without storing raw source content."""
    source = value if isinstance(value, dict) else {}
    path = clean_path(source.get("repo_rel_path") or fallback_path, repo=repo)
    if not path:
        return {}
    source_hash = clean_scalar(source.get("source_hash"), default="").casefold()
    if repo is not None:
        current = Path(repo) / path
        try:
            if current.is_file():
                source_hash = sha256_file(current)
        except OSError:
            source_hash = ""
    if not is_sha256(source_hash):
        return {}
    observed_event = clean_scalar(source.get("observed_at_event_id"), default="")
    observed_timestamp = clean_scalar(source.get("observed_at_timestamp"), default="")
    return {
        "repo_rel_path": path,
        "source_hash": source_hash,
        "hash_algorithm": clean_enum(source.get("hash_algorithm"), HASH_ALGORITHMS, "sha256"),
        "observed_at_event_id": observed_event or clean_scalar(event_id, default=""),
        "observed_at_timestamp": observed_timestamp or clean_scalar(timestamp, default=""),
        "graph_freshness": clean_enum(
            source.get("graph_freshness"),
            FRESHNESS_VALUES,
            "unknown",
        ),
        "validation_freshness": clean_enum(
            source.get("validation_freshness"),
            FRESHNESS_VALUES,
            "unknown",
        ),
    }


def clean_path(value: object, *, repo: str | Path | None = None) -> str:
    text = clean_scalar(value, default="")
    if not text:
        return ""
    text = text.replace("\\", "/")
    if text.startswith("~") or "\x00" in text:
        return ""
    if Path(text).is_absolute():
        if repo is None:
            return ""
        try:
            relative = Path(text).resolve().relative_to(Path(repo).resolve())
        except (OSError, ValueError):
            return ""
        text = relative.as_posix()
    else:
        if text.startswith("../") or "/../" in text or text == "..":
            return ""
        text = text.lstrip("./")
    if text.startswith("../") or "/../" in text or text == "..":
        return ""
    return text[:MAX_PATH_LEN]


def contains_forbidden_key(data: Any) -> bool:
    """Return True when a mapping exposes raw prompt/env/secret style fields."""
    if isinstance(data, dict):
        for key, value in data.items():
            key_text = str(key).casefold()
            if any(token in key_text for token in FORBIDDEN_KEY_TOKENS):
                return True
            if contains_forbidden_key(value):
                return True
    elif isinstance(data, list):
        return any(contains_forbidden_key(item) for item in data)
    return False


def contains_sensitive_value(data: Any) -> bool:
    """Return True when nested data contains secret-looking scalar values."""
    if isinstance(data, dict):
        return any(contains_sensitive_value(value) for value in data.values())
    if isinstance(data, list):
        return any(contains_sensitive_value(item) for item in data)
    if isinstance(data, str):
        return bool(SECRET_VALUE_RE.search(data))
    return False


def _summary_from_event(kind: str, paths: list[str], outcome: str) -> str:
    path_text = ", ".join(paths[:3]) if paths else "no bounded path"
    return f"{kind} memory signal for {path_text}; outcome={outcome}"


def _default_retention_policy(kind: str) -> str:
    if kind in {"false_positive_hook", "false_negative_hook"}:
        return "retain_until_human_review"
    if kind in {"fragile_file", "repeat_failure"}:
        return "retain_90_days_or_until_superseded"
    return "retain_30_days_or_until_superseded"


def _deterministic_event_id(
    repo_hash: str,
    timestamp: str,
    kind: str,
    paths: list[str],
    summary: str,
    source: dict[str, Any],
) -> str:
    payload = {
        "repo_hash": repo_hash,
        "timestamp": timestamp,
        "kind": kind,
        "paths": sorted(paths),
        "summary": summary,
        "source": clean_scalar(source.get("source"), default=""),
        "evidence_refs": clean_list(source.get("evidence_refs")),
    }
    return "mem_" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]
