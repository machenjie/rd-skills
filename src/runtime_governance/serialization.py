"""JSON serialization helpers for runtime governance dataclasses."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, TypeVar


T = TypeVar("T")


def to_json_dict(value: Any) -> Any:
    """Convert dataclasses, enums, mappings, and lists to JSON-safe values."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return to_json_dict(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_json_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_dict(item) for item in value]
    return value


def json_dumps(value: Any) -> str:
    """Serialize a governance object with deterministic key ordering."""
    return json.dumps(to_json_dict(value), sort_keys=True, separators=(",", ":"))


def json_loads(text: str) -> dict[str, Any]:
    """Load a JSON object mapping."""
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("expected JSON object")
    return loaded


def coerce_enum(enum_type: type[T], value: object, default: T) -> T:
    """Coerce a stored string into an enum value with a deterministic default."""
    try:
        return enum_type(value)  # type: ignore[call-arg]
    except ValueError:
        return default
