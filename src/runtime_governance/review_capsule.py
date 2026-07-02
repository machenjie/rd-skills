"""Bounded review capsule normalization and validation."""

from __future__ import annotations

from typing import Any


REVIEW_TYPES = {"pdd", "ddd", "sdd", "tdd", "implementation", "closure"}
REQUIRED_ALLOWED_CONTEXT = {
    "user_request_summary",
    "accepted_constraints",
    "source_evidence",
    "artifact_under_review",
}
REQUIRED_FORBIDDEN_INPUTS = {
    "raw prompt",
    "raw secrets",
    "full command output",
    "implementer self-approval",
    "unverified completion claims",
}
FORBIDDEN_KEY_TOKENS = {
    "raw_prompt",
    "prompt_text",
    "secret",
    "token",
    "password",
    "credential",
    "env",
    "stdout",
    "stderr",
    "transcript",
}
MAX_TEXT = 600
MAX_LIST = 40


def sanitize_review_capsule(capsule: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(capsule, dict):
        return {}
    clean: dict[str, Any] = {}
    for key, value in capsule.items():
        if _forbidden_key(key):
            continue
        if key in {"schema_version", "capsule_id", "review_type", "user_request_summary"}:
            clean[key] = _safe_scalar(value)
        elif key in {"accepted_constraints", "allowed_context", "forbidden_inputs"}:
            clean[key] = _safe_list(value)
        elif key == "source_evidence":
            clean[key] = _clean_source_evidence(value)
        elif key == "artifact_under_review":
            clean[key] = _clean_artifact_under_review(value)
    if "schema_version" not in clean:
        clean["schema_version"] = 1
    return clean


def validate_review_capsule(capsule: dict[str, Any] | None) -> list[str]:
    clean = sanitize_review_capsule(capsule)
    errors: list[str] = []
    if clean.get("schema_version") != 1:
        errors.append("review capsule schema_version must be 1")
    if not clean.get("capsule_id"):
        errors.append("review capsule requires capsule_id")
    if clean.get("review_type") not in REVIEW_TYPES:
        errors.append("review capsule review_type is invalid")
    if not clean.get("user_request_summary"):
        errors.append("review capsule requires bounded user_request_summary")
    allowed = set(clean.get("allowed_context") or [])
    if not REQUIRED_ALLOWED_CONTEXT.issubset(allowed):
        errors.append("review capsule allowed_context must include every bounded context section")
    forbidden = set(clean.get("forbidden_inputs") or [])
    if not REQUIRED_FORBIDDEN_INPUTS.issubset(forbidden):
        errors.append("review capsule forbidden_inputs must reject raw prompt, secrets, output, self-approval, and unverified claims")
    source = clean.get("source_evidence")
    if not isinstance(source, dict):
        errors.append("review capsule requires source_evidence")
    else:
        for record in source.get("read_files") or []:
            if not isinstance(record, dict):
                errors.append("review capsule read_files entries must be objects")
                continue
            if not record.get("path") or not record.get("digest") or not record.get("excerpt_summary"):
                errors.append("review capsule read_files entries require path, digest, and excerpt_summary")
    artifact = clean.get("artifact_under_review")
    if not isinstance(artifact, dict):
        errors.append("review capsule requires artifact_under_review")
    else:
        if artifact.get("phase") not in REVIEW_TYPES:
            errors.append("review capsule artifact_under_review phase is invalid")
        if not str(artifact.get("artifact_digest") or "").startswith("sha256:"):
            errors.append("review capsule artifact_under_review requires sha256 digest")
        if not artifact.get("artifact_summary"):
            errors.append("review capsule artifact_under_review requires artifact_summary")
    if capsule and any(_forbidden_key(str(key)) for key in capsule):
        errors.append("review capsule contained forbidden raw or secret-like keys")
    return errors


def _clean_source_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    read_files = []
    for record in value.get("read_files") or []:
        if not isinstance(record, dict):
            continue
        clean_record: dict[str, Any] = {}
        for key in ("path", "digest", "excerpt_summary"):
            if key in record:
                clean_record[key] = _safe_scalar(record.get(key))
        if clean_record:
            read_files.append(clean_record)
        if len(read_files) >= MAX_LIST:
            break
    return {
        "read_files": read_files,
        "searched_patterns": _safe_list(value.get("searched_patterns") or []),
    }


def _clean_artifact_under_review(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: _safe_scalar(value.get(key))
        for key in ("phase", "artifact_digest", "artifact_summary")
        if key in value
    }


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    clean: list[str] = []
    for item in value:
        scalar = _safe_scalar(item)
        if scalar:
            clean.append(str(scalar))
        if len(clean) >= MAX_LIST:
            break
    return clean


def _safe_scalar(value: Any) -> str | int:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        return ""
    text = str(value or "").strip()
    return text[:MAX_TEXT]


def _forbidden_key(key: str) -> bool:
    normalized = key.casefold().replace("-", "_")
    return any(token in normalized for token in FORBIDDEN_KEY_TOKENS)
