"""Sanitization helpers for Project Memory Governance."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from project_memory import MEMORY_SCHEMA_VERSION


MAX_ITEMS = 50
MAX_VALUE_LEN = 300
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
OUTCOMES = {"success", "failed", "partial", "blocked", "unknown"}
CONFIDENCES = {"low", "medium", "high"}
PROMOTION_STATUSES = {"raw", "candidate", "approved", "rejected"}
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
    created_at = clean_scalar(source.get("created_at"), default=now_utc())
    event_type = clean_enum(source.get("type"), MEMORY_TYPES, "implementation_attempt")
    outcome = clean_enum(source.get("outcome"), OUTCOMES, "unknown")
    confidence = clean_enum(source.get("confidence"), CONFIDENCES, "medium")
    promotion_status = clean_enum(source.get("promotion_status"), PROMOTION_STATUSES, "raw")
    paths = clean_paths(source.get("paths"), repo=repo)
    symbols = clean_list(source.get("symbols"))
    owner_skill = clean_scalar(source.get("owner_skill"), default="")
    task_fingerprint = clean_scalar(source.get("task_fingerprint"), default="")
    if not task_fingerprint:
        task_fingerprint = memory_task_fingerprint(paths, owner_skill, source.get("type"))
    event_id = clean_scalar(source.get("event_id"), default="")
    if not event_id:
        event_id = f"mem-{uuid.uuid4().hex[:24]}"
    return {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "event_id": event_id,
        "repo_hash": repo_hash,
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
        "created_at": created_at,
    }


def sanitize_memory_query(raw: dict[str, Any], *, repo: str | Path | None = None) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    repo_hash = clean_scalar(source.get("repo_hash"), default="")
    if not repo_hash and repo is not None:
        repo_hash = repo_hash_for_path(repo)
    return {
        "repo_hash": repo_hash,
        "task_fingerprint": clean_scalar(source.get("task_fingerprint"), default=""),
        "paths": clean_paths(source.get("paths"), repo=repo),
        "symbols": clean_list(source.get("symbols")),
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
