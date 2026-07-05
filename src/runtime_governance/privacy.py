"""Privacy and bounded-fact helpers for runtime governance records."""

from __future__ import annotations

import hashlib
import re
import shlex
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, TypeVar


MAX_FACT_LENGTH = 300
MAX_LIST_ITEMS = 50
HASH_PREFIX = "sha256:"
REDACTED = "[REDACTED]"

_SECRET_KEY_RE = re.compile(
    r"(?i)\b("
    r"api[_-]?key|secret|token|password|passwd|pwd|credential|credentials|"
    r"authorization|auth[_-]?token|bearer|private[_-]?key|access[_-]?key|"
    r"session[_-]?key|client[_-]?secret"
    r")\b"
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)("
    r"sk-[A-Za-z0-9_-]{8,}|"
    r"gh[pousr]_[A-Za-z0-9_]{12,}|"
    r"xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r")"
)
_ENV_ASSIGN_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=")
_KEY_VALUE_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)(?:=|:)")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_SAFE_COMMAND_RE = re.compile(r"^[A-Za-z0-9_.+-]+$")
_SENSITIVE_KEY_PARTS = {
    "api",
    "apikey",
    "api_key",
    "secret",
    "token",
    "password",
    "passwd",
    "pwd",
    "credential",
    "credentials",
    "authorization",
    "bearer",
    "private",
    "access",
    "session",
}

T = TypeVar("T")


def normalize_relative_path(path: object, *, base: str | Path | None = None) -> str:
    """Return a repository-relative path or a stable hash for unsafe paths.

    Absolute paths are converted to ``base``-relative paths only when they are
    inside ``base``. Otherwise the path is hashed so the absolute working
    directory is never retained.
    """
    text = _clean_text(path)
    if not text or _looks_sensitive(text):
        return ""
    text = text.replace("\\", "/")
    if text.startswith("a/") or text.startswith("b/"):
        text = text[2:]

    if _is_absolute_path(text):
        relative = _relative_to_base(text, base)
        if relative:
            return _cap_path(relative)
        return _hash_text(text)

    parts: list[str] = []
    for part in PurePosixPath(text).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            return _hash_text(text)
        parts.append(part)
    normalized = "/".join(parts).lstrip("/")
    if not normalized:
        return ""
    return _cap_path(normalized)


def sanitize_command_kind(command: object) -> str | None:
    """Return only the leading program/command kind from a command string."""
    text = _clean_text(command)
    if not text:
        return None
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        tokens = text.split()
    for token in tokens:
        if not token:
            continue
        match = _ENV_ASSIGN_RE.match(token)
        if match:
            continue
        program = Path(token.replace("\\", "/")).name
        program = program.strip()
        if not program or _looks_sensitive(program):
            return None
        if not _SAFE_COMMAND_RE.match(program):
            return _hash_text(program)
        return _cap_scalar(program, limit=80)
    return None


def cap_list(
    values: Iterable[object] | object,
    *,
    max_items: int = MAX_LIST_ITEMS,
    max_length: int = MAX_FACT_LENGTH,
    item_sanitizer: Callable[[object], str | None] | None = None,
) -> list[str]:
    """Return a deterministic, de-duplicated, bounded list of string facts."""
    if values is None:
        return []
    iterable: Iterable[object]
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        iterable = (values,)
    else:
        iterable = values

    result: list[str] = []
    seen: set[str] = set()
    sanitizer = item_sanitizer or _default_list_item
    for value in iterable:
        item = sanitizer(value)
        if item is None:
            continue
        item = _cap_scalar(str(item), limit=max_length).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
        if len(result) >= max_items:
            break
    return result


def redact_sensitive_value(value: object) -> str:
    """Return a bounded scalar with secret-like content redacted."""
    text = _clean_text(value)
    if not text:
        return ""
    if _looks_sensitive(text):
        return REDACTED
    return _cap_scalar(text)


def validate_bounded_fact(value: object) -> bool:
    """Return whether a value is safe to persist as a bounded fact."""
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return False
    text = _clean_text(value)
    if not text or len(text) > MAX_FACT_LENGTH:
        return False
    if "\x00" in text or "\n" in text or "\r" in text:
        return False
    if _looks_sensitive(text):
        return False
    if _is_absolute_path(text):
        return False
    return True


def _default_list_item(value: object) -> str | None:
    text = redact_sensitive_value(value)
    if not text or text == REDACTED:
        return None
    return text


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value).strip().strip("\"'")


def _looks_sensitive(text: str) -> bool:
    if _SECRET_VALUE_RE.search(text):
        return True
    match = _KEY_VALUE_RE.match(text)
    if match and _sensitive_key(match.group(1)):
        return True
    return bool(_SECRET_KEY_RE.search(text) and "=" in text)


def _sensitive_key(key: str) -> bool:
    normalized = key.casefold()
    if _SECRET_KEY_RE.search(normalized):
        return True
    parts = {part for part in re.split(r"[^a-z0-9]+|_", normalized) if part}
    return bool(parts & _SENSITIVE_KEY_PARTS)


def _is_absolute_path(text: str) -> bool:
    if text.startswith("/") or text.startswith("~/") or _WINDOWS_ABSOLUTE_RE.match(text):
        return True
    return False


def _relative_to_base(text: str, base: str | Path | None) -> str:
    if base is None:
        return ""
    try:
        path = Path(text).expanduser().resolve(strict=False)
        root = Path(base).expanduser().resolve(strict=False)
        return path.relative_to(root).as_posix()
    except (OSError, ValueError):
        return ""


def _cap_path(path: str) -> str:
    if len(path) <= MAX_FACT_LENGTH:
        return path
    return _hash_text(path)


def _cap_scalar(text: str, *, limit: int = MAX_FACT_LENGTH) -> str:
    if len(text) <= limit:
        return text
    if limit <= 20:
        return text[:limit]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{text[: limit - 18]}...{digest}"


def _hash_text(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
    return f"{HASH_PREFIX}{digest}"
