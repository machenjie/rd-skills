"""Append-only Project Memory event log."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from project_memory.privacy import repo_hash_for_path, sanitize_memory_event


MEMORY_SUBDIRS = ("events", "projections", "suggestions", "promoted")


def default_cache_base() -> Path:
    cache = os.environ.get("XDG_CACHE_HOME")
    return Path(cache).expanduser() if cache else Path.home() / ".cache"


def default_memory_root() -> Path:
    return default_cache_base() / "changeforge" / "memory"


def memory_root_for_repo(repo: str | Path, *, cache_base: Path | None = None) -> Path:
    base = cache_base if cache_base is not None else default_cache_base()
    return base / "changeforge" / "memory" / repo_hash_for_path(repo)


def memory_root_for_repo_hash(repo_hash: str, *, cache_base: Path | None = None) -> Path:
    base = cache_base if cache_base is not None else default_cache_base()
    return base / "changeforge" / "memory" / repo_hash


def ensure_memory_root(root: Path) -> None:
    for subdir in MEMORY_SUBDIRS:
        (root / subdir).mkdir(parents=True, exist_ok=True)


def append_memory_event(
    event: dict[str, Any],
    *,
    repo: str | Path | None = None,
    root: Path | None = None,
    fail_open: bool = True,
) -> dict[str, Any] | None:
    """Append one sanitized event as JSONL.

    Writes are best-effort by default, matching hook telemetry's fail-open
    behavior. Passing ``fail_open=False`` lets tests and validators surface IO
    errors explicitly.
    """
    try:
        sanitized = sanitize_memory_event(event, repo=repo)
        target_root = root
        if target_root is None:
            if repo is not None:
                target_root = memory_root_for_repo(repo)
            else:
                target_root = memory_root_for_repo_hash(sanitized["repo_hash"])
        ensure_memory_root(target_root)
        target = target_root / "events" / f"{_date_from_created_at(sanitized['created_at'])}.jsonl"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sanitized, sort_keys=True) + "\n")
        return sanitized
    except Exception:
        if fail_open:
            return None
        raise


def iter_memory_events(root: Path, *, since: str | None = None, until: str | None = None) -> Iterator[dict[str, Any]]:
    events_dir = root / "events"
    if not events_dir.is_dir():
        return
    since_dt = parse_iso_datetime(since)
    until_dt = parse_iso_datetime(until)
    for path in sorted(events_dir.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            created = parse_iso_datetime(event.get("created_at"))
            if since_dt is not None and created is not None and created < since_dt:
                continue
            if until_dt is not None and created is not None and created > until_dt:
                continue
            yield event


def iter_repo_hashes(memory_root: Path | None = None) -> list[str]:
    root = memory_root if memory_root is not None else default_memory_root()
    if not root.is_dir():
        return []
    return sorted(
        child.name
        for child in root.iterdir()
        if child.is_dir() and (child / "events").is_dir()
    )


def parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _date_from_created_at(value: str) -> str:
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d")

