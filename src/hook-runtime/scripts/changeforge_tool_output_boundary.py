#!/usr/bin/env python3
"""Bounded tool-output boundary records for ChangeForge hooks."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SMALL_OUTPUT_BYTES = 16_000
SMALL_OUTPUT_LINES = 200
MAX_SUMMARY_ITEMS = 8
MAX_TEXT = 240
MAX_RECORD_KEYS = 40

OUTPUT_SIZE_CLASSES = {"none", "small", "large", "unknown", "unsupported"}
LLM_CONTEXT_POLICIES = {
    "inline_bounded",
    "artifact_reference_only",
    "rerun_with_redirect",
    "unsupported_runtime",
}
ARTIFACT_PATH_SOURCES = {
    "explicit_tool_result",
    "user_created",
    "not_available",
}

FORBIDDEN_RECORD_KEY_TOKENS = (
    "stdout",
    "stderr",
    "command_output",
    "full_output",
    "raw_output",
    "full_diff",
    "file_contents",
    "raw_prompt",
    "prompt",
    "environment",
    "env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "password",
    "api_key",
    "apikey",
    "token",
)
OUTPUT_TEXT_KEYS = {
    "stdout",
    "stderr",
    "command_output",
    "commandOutput",
    "output",
    "outputs",
    "raw_output",
    "rawOutput",
    "full_output",
    "fullOutput",
    "result",
    "tool_result",
    "toolResult",
    "tool_response",
    "toolResponse",
    "response",
    "observation",
    "text",
    "content",
}
INPUT_CONTAINER_KEYS = {
    "tool_input",
    "toolInput",
    "input",
    "arguments",
    "parameters",
    "params",
}
SIZE_KEYS = {
    "output_bytes",
    "outputBytes",
    "outputByteLength",
    "bytes",
    "byte_length",
    "byteLength",
    "stdout_bytes",
    "stdoutBytes",
    "stderr_bytes",
    "stderrBytes",
}
LINE_KEYS = {
    "output_lines",
    "outputLines",
    "lines",
    "line_count",
    "lineCount",
    "stdout_lines",
    "stdoutLines",
    "stderr_lines",
    "stderrLines",
}
ARTIFACT_PATH_KEYS = {
    "artifact_path",
    "artifactPath",
    "artifact",
    "output_path",
    "outputPath",
    "report_path",
    "reportPath",
    "log_path",
    "logPath",
    "path",
    "file_path",
    "filePath",
}
DIGEST_KEYS = {"digest", "sha256", "output_digest", "outputDigest"}
TOOL_RESULT_EVENT_NAMES = {
    "posttooluse",
    "posttoolusefailure",
    "posttoolbatch",
    "taskcompleted",
}

SECRET_VALUE_RE = re.compile(
    r"(sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+|"
    r"(?i:OPENAI_API_KEY|CODEX_API_KEY|api[_-]?key|access[_-]?token|bearer\s+[A-Za-z0-9._/-]{8,}|token=|password=)"
    r"\s*[:=]?\s*[A-Za-z0-9_./+=-]{8,})"
)
ABSOLUTE_PATH_RE = re.compile(
    r"^(/Users/|/home/|/private/var/|/var/folders/|/tmp/|[A-Za-z]:[\\/])"
)
DIGEST_RE = re.compile(r"^(?:sha256:)?[A-Fa-f0-9]{16,64}$")


def tool_output_boundary_from_event(event: dict, *, state: dict | None = None) -> dict:
    """Return one privacy-safe bounded record for a tool-result-like event."""
    if not isinstance(event, dict):
        event = {}
    size_class = output_size_class(event)
    artifact = _artifact_path_fact(event)
    policy = artifact_reference_policy(event, size_class)
    digest = safe_output_digest(event)
    record = {
        "schema_version": SCHEMA_VERSION,
        "tool_name": _clean_text(_tool_name(event), limit=120),
        "event_name": _clean_text(_event_name(event), limit=120),
        "output_size_class": size_class,
        "output_bytes": _output_bytes(event),
        "output_lines": _output_lines(event),
        "artifact_path": artifact["path"],
        "artifact_path_source": artifact["source"],
        "digest": digest or None,
        "bounded_summary": _bounded_summary(event, size_class, artifact, policy, state),
        "truncation_advice": _truncation_advice(size_class, policy),
        "llm_context_policy": policy["llm_context_policy"],
        "privacy_status": "fail" if _secret_like_output_seen(event) else "pass",
        "unsupported_reason": policy.get("unsupported_reason"),
    }
    return sanitize_output_observation(record)


def output_size_class(event: dict) -> str:
    """Classify observable output volume without storing the output."""
    if not isinstance(event, dict):
        return "unsupported"
    texts = _output_texts(event)
    byte_count = _output_bytes(event)
    line_count = _output_lines(event)
    has_size_metadata = byte_count is not None or line_count is not None
    has_output_metadata = bool(texts) or has_size_metadata or _artifact_path_fact(event)["path"]
    if not has_output_metadata:
        if _tool_result_like_event(event):
            return "unsupported"
        return "unknown"
    if (byte_count == 0 or byte_count is None) and (line_count == 0 or line_count is None):
        if texts and any(text for text in texts):
            pass
        elif byte_count == 0 or line_count == 0:
            return "none"
    inferred_bytes = byte_count if byte_count is not None else sum(len(text.encode("utf-8", "ignore")) for text in texts)
    inferred_lines = line_count if line_count is not None else sum(_line_count(text) for text in texts)
    if inferred_bytes <= 0 and inferred_lines <= 0:
        return "none"
    if inferred_bytes > SMALL_OUTPUT_BYTES or inferred_lines > SMALL_OUTPUT_LINES:
        return "large"
    return "small"


def safe_output_digest(event: dict) -> str:
    """Return a digest of observable output facts without retaining raw output."""
    if not isinstance(event, dict):
        return ""
    explicit = _explicit_digest(event)
    if explicit:
        return explicit
    texts = _output_texts(event)
    artifact = _artifact_path_fact(event)
    bytes_value = _output_bytes(event)
    lines_value = _output_lines(event)
    if not texts and not artifact["path"] and bytes_value is None and lines_value is None:
        return ""
    digest = hashlib.sha256()
    for text in texts:
        digest.update(text.encode("utf-8", "ignore"))
        digest.update(b"\0")
    metadata = {
        "artifact_path": artifact["path"],
        "artifact_path_source": artifact["source"],
        "output_bytes": bytes_value,
        "output_lines": lines_value,
    }
    digest.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))
    return f"sha256:{digest.hexdigest()[:24]}"


def artifact_reference_policy(event: dict, output_size: str) -> dict:
    """Return the LLM context policy for the output observation."""
    artifact = _artifact_path_fact(event)
    output_size = output_size if output_size in OUTPUT_SIZE_CLASSES else "unknown"
    if output_size == "unsupported":
        return {
            "llm_context_policy": "unsupported_runtime",
            "artifact_required": True,
            "unsupported_reason": "output metadata not available from runtime event",
        }
    if output_size == "large":
        if artifact["path"] and artifact["path"] != "<local-artifact-path-redacted>":
            return {
                "llm_context_policy": "artifact_reference_only",
                "artifact_required": False,
                "unsupported_reason": None,
            }
        return {
            "llm_context_policy": "rerun_with_redirect",
            "artifact_required": True,
            "unsupported_reason": None,
        }
    if output_size == "unknown":
        return {
            "llm_context_policy": "unsupported_runtime",
            "artifact_required": True,
            "unsupported_reason": "output size metadata unknown",
        }
    return {
        "llm_context_policy": "inline_bounded",
        "artifact_required": False,
        "unsupported_reason": None,
    }


def sanitize_output_observation(record: dict) -> dict:
    """Return an allowlisted boundary record with sensitive keys removed."""
    if not isinstance(record, dict):
        record = {}
    had_forbidden = _contains_forbidden_key(record)
    privacy_failed = had_forbidden or _secret_like_value_seen(record)
    artifact_path = _sanitize_artifact_path(record.get("artifact_path"), record)
    output_size = str(record.get("output_size_class") or "unknown").strip()
    if output_size not in OUTPUT_SIZE_CLASSES:
        output_size = "unknown"
    policy = str(record.get("llm_context_policy") or "unsupported_runtime").strip()
    if policy not in LLM_CONTEXT_POLICIES:
        policy = "unsupported_runtime"
    path_source = str(record.get("artifact_path_source") or "not_available").strip()
    if path_source not in ARTIFACT_PATH_SOURCES:
        path_source = "not_available"
    clean = {
        "schema_version": _safe_int(record.get("schema_version")) or SCHEMA_VERSION,
        "tool_name": _clean_text(record.get("tool_name"), limit=120),
        "event_name": _clean_text(record.get("event_name"), limit=120),
        "output_size_class": output_size,
        "output_bytes": _nullable_int(record.get("output_bytes")),
        "output_lines": _nullable_int(record.get("output_lines")),
        "artifact_path": artifact_path,
        "artifact_path_source": path_source if artifact_path else "not_available",
        "digest": _clean_digest(record.get("digest")),
        "bounded_summary": _clean_list(record.get("bounded_summary"), max_items=MAX_SUMMARY_ITEMS),
        "truncation_advice": _clean_text(record.get("truncation_advice"), limit=MAX_TEXT),
        "llm_context_policy": policy,
        "privacy_status": "fail" if privacy_failed or record.get("privacy_status") == "fail" else "pass",
        "unsupported_reason": _clean_text(record.get("unsupported_reason"), limit=MAX_TEXT) or None,
    }
    if clean["artifact_path"] is None:
        clean["artifact_path_source"] = "not_available"
    if clean["privacy_status"] == "fail":
        clean["bounded_summary"] = _clean_list(
            [*clean["bounded_summary"], "privacy_status=fail; raw output excluded"],
            max_items=MAX_SUMMARY_ITEMS,
        )
    return clean


def sanitize_artifact_reference(value: Any, event: dict | None = None) -> str:
    """Return a repo-relative or cache-scoped artifact reference, or redaction."""
    return _sanitize_artifact_path(value, event or {}) or ""


def _bounded_summary(
    event: dict,
    size_class: str,
    artifact: dict[str, str | None],
    policy: dict[str, Any],
    state: dict | None,
) -> list[str]:
    summary = [
        f"tool={_tool_name(event) or 'unknown'}",
        f"event={_event_name(event) or 'unknown'}",
        f"output_size_class={size_class}",
    ]
    bytes_value = _output_bytes(event)
    lines_value = _output_lines(event)
    if bytes_value is not None:
        summary.append(f"output_bytes={bytes_value}")
    if lines_value is not None:
        summary.append(f"output_lines={lines_value}")
    if artifact["path"]:
        summary.append(f"artifact_path={artifact['path']}")
    summary.append(f"llm_context_policy={policy['llm_context_policy']}")
    if policy.get("unsupported_reason"):
        summary.append(f"unsupported_reason={policy['unsupported_reason']}")
    if isinstance(state, dict) and state.get("turn_stage"):
        summary.append(f"turn_stage={state.get('turn_stage')}")
    return _clean_list(summary, max_items=MAX_SUMMARY_ITEMS)


def _truncation_advice(size_class: str, policy: dict[str, Any]) -> str:
    if policy.get("llm_context_policy") == "unsupported_runtime":
        return (
            "Runtime did not expose bounded output metadata; do not claim a closure pass from this event. "
            "If full evidence is needed, rerun with explicit redirection or inspect bounded slices."
        )
    if size_class == "large":
        return (
            "Output appears large; do not paste full output. Use an explicit artifact path, redirected log, "
            "or bounded slices, and cite validation status separately."
        )
    if size_class == "small":
        return "Small output may be summarized inline only after secret and raw-output exclusion."
    if size_class == "none":
        return "No output observed; do not infer validation success without an explicit outcome."
    return "Output size is unknown; use bounded slices or explicit artifact references before relying on it."


def _output_texts(event: dict) -> list[str]:
    texts: list[str] = []

    def visit(value: Any, key: str = "", *, in_output: bool = False) -> None:
        if len(texts) >= 20:
            return
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                child_name = str(child_key)
                if child_name in INPUT_CONTAINER_KEYS:
                    continue
                child_output = in_output or child_name in OUTPUT_TEXT_KEYS
                visit(child_value, child_name, in_output=child_output)
            return
        if isinstance(value, list):
            for item in value:
                visit(item, key, in_output=in_output)
            return
        if isinstance(value, str) and in_output:
            texts.append(value)

    visit(event)
    return texts


def _output_bytes(event: dict) -> int | None:
    explicit = _first_int_for_keys(event, SIZE_KEYS)
    if explicit is not None:
        return explicit
    texts = _output_texts(event)
    if texts:
        return sum(len(text.encode("utf-8", "ignore")) for text in texts)
    return None


def _output_lines(event: dict) -> int | None:
    explicit = _first_int_for_keys(event, LINE_KEYS)
    if explicit is not None:
        return explicit
    texts = _output_texts(event)
    if texts:
        return sum(_line_count(text) for text in texts)
    return None


def _first_int_for_keys(value: Any, names: set[str]) -> int | None:
    found: int | None = None

    def visit(child: Any, key: str = "") -> None:
        nonlocal found
        if found is not None:
            return
        if isinstance(child, dict):
            for child_key, child_value in child.items():
                visit(child_value, str(child_key))
            return
        if key in names:
            found = _nullable_int(child)

    visit(value)
    return found


def _artifact_path_fact(event: dict) -> dict[str, str | None]:
    raw = _first_text_for_keys(event, ARTIFACT_PATH_KEYS)
    if not raw:
        return {"path": None, "source": "not_available"}
    path = _sanitize_artifact_path(raw, event)
    return {"path": path, "source": "explicit_tool_result" if path else "not_available"}


def _explicit_digest(event: dict) -> str:
    raw = _first_text_for_keys(event, DIGEST_KEYS)
    return _clean_digest(raw)


def _first_text_for_keys(value: Any, names: set[str]) -> str:
    found = ""

    def visit(child: Any, key: str = "") -> None:
        nonlocal found
        if found:
            return
        if isinstance(child, dict):
            for child_key, child_value in child.items():
                if str(child_key) in INPUT_CONTAINER_KEYS:
                    continue
                visit(child_value, str(child_key))
            return
        if isinstance(child, str) and key in names:
            found = child

    visit(value)
    return found.strip()


def _sanitize_artifact_path(value: Any, event: dict) -> str | None:
    text = str(value or "").strip().strip("'\"")
    if not text or "\n" in text or "\0" in text:
        return None
    text = SECRET_VALUE_RE.sub("<redacted-secret>", text).replace("\\", "/")
    if "://" in text:
        return None
    if text.startswith("./"):
        text = text[2:]
    if _is_repo_relative_path(text):
        return text[:MAX_TEXT]
    if not ABSOLUTE_PATH_RE.search(text):
        return None
    repo_relative = _repo_relative_path(text, event)
    if repo_relative:
        return repo_relative[:MAX_TEXT]
    cache_relative = _cache_scoped_path(text)
    if cache_relative:
        return cache_relative[:MAX_TEXT]
    return "<local-artifact-path-redacted>"


def _repo_relative_path(text: str, event: dict) -> str:
    cwd = ""
    if isinstance(event, dict):
        cwd = str(
            event.get("cwd")
            or event.get("project_dir")
            or event.get("projectDir")
            or event.get("workspace")
            or event.get("workspaceRoot")
            or ""
        ).strip()
    if not cwd:
        return ""
    try:
        path = Path(text).expanduser().resolve()
        root = Path(cwd).expanduser().resolve()
        relative = path.relative_to(root)
    except Exception:
        return ""
    return str(relative).replace("\\", "/")


def _cache_scoped_path(text: str) -> str:
    normalized = text.replace("\\", "/")
    for marker in ("/.cache/changeforge/", "/Library/Caches/changeforge/"):
        if marker in normalized:
            return "${CACHE}/changeforge/" + normalized.split(marker, 1)[1].lstrip("/")
    cache_home = os.environ.get("XDG_CACHE_HOME", "").strip()
    if cache_home:
        try:
            relative = Path(normalized).resolve().relative_to(Path(cache_home).expanduser().resolve())
        except Exception:
            return ""
        rel_text = str(relative).replace("\\", "/")
        if rel_text.startswith("changeforge/"):
            return "${CACHE}/" + rel_text
    return ""


def _is_repo_relative_path(path: str) -> bool:
    if not path or path.startswith(("/", "~")):
        return False
    if re.match(r"^[A-Za-z]:/", path):
        return False
    if path.startswith("../") or "/../" in path or path == "..":
        return False
    if path.startswith("{") or path.startswith("["):
        return False
    return True


def _secret_like_output_seen(event: dict) -> bool:
    return any(SECRET_VALUE_RE.search(text) for text in _output_texts(event))


def _secret_like_value_seen(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_secret_like_value_seen(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_secret_like_value_seen(item) for item in value)
    return bool(SECRET_VALUE_RE.search(str(value or "")))


def _contains_forbidden_key(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key, child in value.items():
        name = str(key).casefold()
        if any(token in name for token in FORBIDDEN_RECORD_KEY_TOKENS):
            return True
        if isinstance(child, dict) and _contains_forbidden_key(child):
            return True
        if isinstance(child, list) and any(_contains_forbidden_key(item) for item in child):
            return True
    return False


def _tool_result_like_event(event: dict) -> bool:
    return _compact(_event_name(event)) in TOOL_RESULT_EVENT_NAMES


def _tool_name(event: dict) -> str:
    for key in ("tool_name", "toolName", "name"):
        value = event.get(key)
        if isinstance(value, str):
            return value.strip()
    tool = event.get("tool")
    if isinstance(tool, dict):
        value = tool.get("name")
        if isinstance(value, str):
            return value.strip()
    if isinstance(tool, str):
        return tool.strip()
    return ""


def _event_name(event: dict) -> str:
    for key in ("hook_event_name", "hookEventName", "event_name", "eventName"):
        value = event.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def _clean_text(value: Any, *, limit: int = MAX_TEXT) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = SECRET_VALUE_RE.sub("<redacted-secret>", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    return text[:limit]


def _clean_list(value: Any, *, max_items: int) -> list[str]:
    values = value if isinstance(value, (list, tuple, set)) else [value]
    out: list[str] = []
    for raw in values:
        text = _clean_text(raw)
        if not text or text in out:
            continue
        out.append(text)
        if len(out) >= max_items:
            break
    return out


def _clean_digest(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if DIGEST_RE.match(text):
        return text if text.startswith("sha256:") else f"sha256:{text}"
    return ""


def _nullable_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, number)


def _safe_int(value: Any) -> int:
    return _nullable_int(value) or 0


def _line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


__all__ = [
    "artifact_reference_policy",
    "output_size_class",
    "safe_output_digest",
    "sanitize_artifact_reference",
    "sanitize_output_observation",
    "tool_output_boundary_from_event",
]
