#!/usr/bin/env python3
"""Shared helpers for ChangeForge telemetry review and promotion tooling.

These helpers are used by the offline review (``review-agent-telemetry.py``),
the agent-behavior eval (``eval-agent-behavior.py``), the promotion generator
(``promote-telemetry-suggestion.py``), and ``installers/doctor.py``. They only
read telemetry written by the hook runtime; they never call a model, never reach
the network, and never mutate skills, routing rules, or capabilities.

Telemetry lives in the user cache, not in project source:

    ${XDG_CACHE_HOME:-~/.cache}/changeforge/telemetry/<repo_hash>/
        sessions/    # append-only JSONL fact log written by hooks
        reports/     # generated review reports
        suggestions/ # generated, human-review-only suggestions
        promoted/    # audit trail of human-approved promotions
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from validation_utils import load_yaml_text


TELEMETRY_SCHEMA_VERSION = "1"
TELEMETRY_SUBDIRS = ("sessions", "reports", "suggestions", "promoted")
ROUTE_MANIFEST_KEY = "changeforge_route"
STAGE_MANIFEST_KEY = "changeforge_stage_route"
RUNTIME_PROMPT_FLOW_KEY = "runtime_prompt_flow"
_ROUTE_MANIFEST_FENCE_RE = re.compile(
    r"```[a-zA-Z0-9]*\s*\n(?P<block>.*?)```",
    re.DOTALL,
)


def default_cache_base() -> Path:
    """Resolve the ChangeForge cache root, honoring XDG_CACHE_HOME."""
    cache_root = os.environ.get("XDG_CACHE_HOME")
    return Path(cache_root).expanduser() if cache_root else Path.home() / ".cache"


def default_telemetry_root() -> Path:
    """Default telemetry root under the user cache."""
    return default_cache_base() / "changeforge" / "telemetry"


def resolve_telemetry_root(arg: Path | None) -> Path:
    return arg.expanduser() if arg is not None else default_telemetry_root()


def iter_repo_hashes(root: Path) -> list[str]:
    """Return repo-hash subdirectory names that contain a sessions directory."""
    if not root.is_dir():
        return []
    return sorted(
        child.name
        for child in root.iterdir()
        if child.is_dir() and (child / "sessions").is_dir()
    )


def iter_session_records(
    root: Path,
    repo_hash: str,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield telemetry records for one repo hash, optionally filtered by time."""
    sessions_dir = root / repo_hash / "sessions"
    if not sessions_dir.is_dir():
        return
    for path in sorted(sessions_dir.glob("*.jsonl")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            if not _within_window(record.get("timestamp_utc"), since, until):
                continue
            yield record


def parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO 8601 date or datetime into an aware UTC datetime."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for candidate in (text, f"{text}T00:00:00+00:00"):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def extract_route_manifest(text: str) -> dict[str, Any] | None:
    """Extract and parse the ``changeforge_route`` YAML block from agent output.

    Accepts either a fenced block whose body is ``changeforge_route:`` wrapping
    the manifest, or a fenced block that is already the manifest body. Returns
    the manifest mapping, or None when no parseable manifest is present.
    """
    return _extract_manifest(text, ROUTE_MANIFEST_KEY)


def extract_stage_manifest(text: str) -> dict[str, Any] | None:
    """Extract and parse the ``changeforge_stage_route`` YAML block from output.

    Mirrors :func:`extract_route_manifest`. Without PyYAML the repository loader
    flattens deeply nested mappings, so the stage manifest is most reliable in a
    flat, two-level form (scalars and lists of scalars); callers that read the
    skipped-capability and context-budget fields tolerate both shapes.
    """
    return _extract_manifest(text, STAGE_MANIFEST_KEY)


def _extract_manifest(text: str, key: str) -> dict[str, Any] | None:
    if not isinstance(text, str) or key not in text:
        return None
    for match in _ROUTE_MANIFEST_FENCE_RE.finditer(text):
        block = match.group("block")
        if key not in block:
            continue
        manifest = _load_manifest_block(block, key)
        if manifest is not None:
            return manifest
    # Fall back to parsing from the key onward when no fence is present.
    index = text.find(f"{key}:")
    if index != -1:
        return _load_manifest_block(text[index:], key)
    return None


def _load_manifest_block(block: str, key: str = ROUTE_MANIFEST_KEY) -> dict[str, Any] | None:
    try:
        loaded = load_yaml_text(block, Path(key))
    except Exception:
        return None
    if not isinstance(loaded, dict):
        return None
    inner = loaded.get(key, loaded)
    return inner if isinstance(inner, dict) else None


def manifest_string_list(manifest: dict[str, Any], *keys: str) -> list[str]:
    """Return the first present key as a clean list of strings."""
    for key in keys:
        value = manifest.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
    return []


def manifest_runtime_prompt_flow(manifest: dict[str, Any]) -> dict[str, Any] | None:
    """Return the nested runtime prompt-flow manifest, when present."""
    value = manifest.get(RUNTIME_PROMPT_FLOW_KEY)
    return value if isinstance(value, dict) else None


def runtime_flow_actions(flow: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return structured runtime-flow action entries."""
    if not isinstance(flow, dict):
        return []
    actions = flow.get("actions")
    if not isinstance(actions, list):
        return []
    return [entry for entry in actions if isinstance(entry, dict)]


def load_registry_names(registry_dir: Path) -> dict[str, set[str]]:
    """Load registry entry names for offline validation of generated artifacts.

    Returns skill, capability, extension, and quality-gate name sets so the
    behavior eval and promotion generators can reject names that are not part of
    the authored registries.
    """

    def names(file_name: str, key: str) -> set[str]:
        path = registry_dir / file_name
        if not path.is_file():
            return set()
        try:
            data = load_yaml_text(path.read_text(encoding="utf-8"), path)
        except Exception:
            return set()
        if not isinstance(data, dict):
            return set()
        result: set[str] = set()
        for entry in data.get(key, []) or []:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                result.add(entry["name"].strip())
        return result

    gates: set[str] = set()
    rules_path = registry_dir / "routing-rules.yaml"
    if rules_path.is_file():
        try:
            rules = load_yaml_text(rules_path.read_text(encoding="utf-8"), rules_path)
        except Exception:
            rules = {}
        if isinstance(rules, dict):
            gates = {
                str(gate).strip()
                for gate in rules.get("quality_gates", []) or []
                if str(gate).strip()
            }
    return {
        "skills": names("skills.yaml", "skills"),
        "capabilities": names("capabilities.yaml", "capabilities"),
        "extensions": names("domain-extensions.yaml", "domain_extensions"),
        "gates": gates,
    }


def _within_window(
    timestamp: Any,
    since: datetime | None,
    until: datetime | None,
) -> bool:
    if since is None and until is None:
        return True
    parsed = parse_iso_datetime(timestamp if isinstance(timestamp, str) else None)
    if parsed is None:
        # Keep undated records rather than silently dropping facts.
        return True
    if since is not None and parsed < since:
        return False
    if until is not None and parsed > until:
        return False
    return True


def read_report_summary(path: Path) -> dict[str, Any] | None:
    """Extract the machine-readable summary from a review report.

    Supports JSON and YAML reports (``summary`` key) and markdown reports (a
    fenced ``json`` block). Returns the summary mapping, or None when no
    parseable summary is present.
    """
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    suffix = path.suffix.casefold()
    if suffix == ".json":
        try:
            return _summary_from(json.loads(text))
        except json.JSONDecodeError:
            return None
    if suffix in {".yaml", ".yml"}:
        try:
            return _summary_from(load_yaml_text(text, path))
        except Exception:
            return None
    for match in _ROUTE_MANIFEST_FENCE_RE.finditer(text):
        try:
            summary = _summary_from(json.loads(match.group("block")))
        except json.JSONDecodeError:
            continue
        if summary is not None:
            return summary
    return None


def _summary_from(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    summary = data.get("summary")
    if isinstance(summary, dict):
        return summary
    if "sessions" in data or "records" in data:
        return data
    return None


def find_latest_report(root: Path, repo_hash: str | None = None) -> Path | None:
    """Return the most recent generated review report under a telemetry root."""
    repo_hashes = [repo_hash] if repo_hash else iter_repo_hashes(root)
    candidates: list[Path] = []
    for current in repo_hashes:
        reports_dir = root / current / "reports"
        if reports_dir.is_dir():
            candidates.extend(
                path
                for path in reports_dir.iterdir()
                if path.is_file() and path.suffix.casefold() in {".md", ".json", ".yaml", ".yml"}
            )
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def dump_yaml(data: Any) -> str:
    """Emit a deterministic YAML subset that the repository parser can re-read.

    Supports nested mappings, lists of scalars, and lists of single-level
    mappings. This is intentionally small; it exists because PyYAML is optional
    in the validation environment and generated files must round-trip through
    ``validation_utils.load_yaml_text``.
    """
    lines: list[str] = []
    _emit_mapping(data, 0, lines)
    return "\n".join(lines) + "\n"


def _emit_mapping(data: Any, indent: int, lines: list[str]) -> None:
    if not isinstance(data, dict):
        raise TypeError("dump_yaml expects a mapping at the top level")
    pad = " " * indent
    for key, value in data.items():
        if isinstance(value, dict) and value:
            lines.append(f"{pad}{key}:")
            _emit_mapping(value, indent + 2, lines)
        elif isinstance(value, dict):
            lines.append(f"{pad}{key}: {{}}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}:")
                _emit_list(value, indent + 2, lines)
        else:
            lines.append(f"{pad}{key}: {_scalar(value)}")


def _emit_list(items: Iterable[Any], indent: int, lines: list[str]) -> None:
    pad = " " * indent
    for item in items:
        if isinstance(item, dict) and item:
            first = True
            for key, value in item.items():
                if first:
                    lines.append(f"{pad}- {key}: {_scalar(value)}")
                    first = False
                else:
                    lines.append(f"{pad}  {key}: {_scalar(value)}")
        else:
            lines.append(f"{pad}- {_scalar(item)}")


def _scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "null"
    text = str(value)
    if _needs_quote(text):
        escaped = text.replace("\n", " ").replace('"', "'")
        return f'"{escaped}"'
    return text


def _needs_quote(text: str) -> bool:
    if text == "":
        return True
    if text.strip() != text:
        return True
    if any( char in text for char in (":", "#", "\n", '"')):
        return True
    return text[0] in {"-", "[", "]", "{", "}", "'", "&", "*", "!", "|", ">", "%", "@", "`"}
