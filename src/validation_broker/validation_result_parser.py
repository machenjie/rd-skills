"""Parse bounded validation result facts from closure text or event summaries."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

from .command_registry import command_coverage, command_kind, is_validation_looking, registry_commands


NEGATIVE_EVIDENCE_PHRASES = (
    "not run",
    "not verified",
    "not tested",
    "unable to run",
    "could not run",
    "did not run",
    "skipped validation",
    "tests not run",
    "validation not run",
    "未验证",
    "没有验证",
    "未运行",
    "没有运行",
    "无法运行",
    "未测试",
)
PASS_RE = re.compile(
    r"\b("
    r"pass(?:ed|ing)?|success(?:ful)?|ok|exit\s*(?:code)?\s*0|return\s*(?:code)?\s*0|"
    r"validated|green|通过|成功"
    r")\b",
    re.IGNORECASE,
)
FAIL_RE = re.compile(
    r"\b("
    r"fail(?:ed|ing|ures?)?|error(?:s)?|exit\s*(?:code)?\s*[1-9]\d*|"
    r"return\s*(?:code)?\s*[1-9]\d*|red|失败|错误"
    r")\b",
    re.IGNORECASE,
)
EXIT_CODE_RE = re.compile(r"\b(?:exit|return)\s*(?:code)?\s*[:=]?\s*(-?\d+)\b", re.IGNORECASE)
GENERIC_VALIDATION_COMMAND_RE = re.compile(
    r"((?:python3?\s+-m\s+unittest[^\n,;.]*)|"
    r"(?:python3?\s+scripts/(?:validate|eval|build)[^\n,;.]*)|"
    r"(?:pytest[^\n,;.]*)|"
    r"(?:go\s+test[^\n,;.]*)|"
    r"(?:cargo\s+test[^\n,;.]*)|"
    r"(?:(?:npm|yarn|pnpm)\s+test[^\n,;.]*))",
    re.IGNORECASE,
)


def parse_validation_result(
    text: str = "",
    *,
    command: str = "",
    exit_code: int | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    finished_index: int | None = None,
    changed_paths: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
) -> dict[str, object]:
    """Return a ValidationResult-shaped dictionary from bounded evidence."""
    body = text or ""
    detected_command = (command or _find_command(body)).strip()
    validation_looking = bool(detected_command and is_validation_looking(detected_command))
    parsed_exit = exit_code if exit_code is not None else _parse_exit_code(body)
    negative_reason = _negative_reason(body)
    outcome = _outcome(body, parsed_exit, negative_reason, validation_looking)
    coverage = command_coverage(detected_command) if detected_command else command_coverage("")
    evidence_strength = _evidence_strength(
        outcome=outcome,
        validation_looking=validation_looking,
        negative_reason=negative_reason,
    )

    return {
        "schema_version": 1,
        "command": detected_command,
        "command_kind": command_kind(detected_command) if detected_command else "unknown",
        "validation_looking": validation_looking,
        "started_at": started_at or "",
        "finished_at": finished_at or _now_if_outcome(outcome),
        "finished_index": finished_index,
        "outcome": outcome,
        "exit_code": parsed_exit,
        "covered_paths": _covered_paths(coverage),
        "covered_risk_surfaces": list(coverage.get("covered_risk_surfaces", [])),
        "material_edit_cutoff": "",
        "fresh_after_last_edit": "unknown",
        "coverage_aligned": _coverage_aligned(coverage, changed_paths, risk_surfaces),
        "evidence_strength": evidence_strength,
        "negative_evidence_reason": negative_reason,
    }


def _find_command(text: str) -> str:
    for spec in sorted(registry_commands(), key=lambda item: len(item.command), reverse=True):
        if spec.command.casefold() in text.casefold():
            return spec.command
    match = GENERIC_VALIDATION_COMMAND_RE.search(text)
    return " ".join(match.group(1).split()) if match else ""


def _parse_exit_code(text: str) -> int | None:
    match = EXIT_CODE_RE.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _negative_reason(text: str) -> str:
    lowered = text.casefold()
    if any(phrase.casefold() in lowered for phrase in NEGATIVE_EVIDENCE_PHRASES):
        if "unable" in lowered or "could not" in lowered or "无法运行" in lowered:
            return "unable_to_run"
        return "not_run"
    return ""


def _outcome(
    text: str,
    exit_code: int | None,
    negative_reason: str,
    validation_looking: bool,
) -> str:
    if negative_reason:
        return "not_run"
    if exit_code is not None:
        return "pass" if exit_code == 0 else "fail"
    if FAIL_RE.search(text):
        return "fail"
    if PASS_RE.search(text) and validation_looking:
        return "pass"
    if validation_looking:
        return "unknown"
    return "not_run"


def _evidence_strength(
    *,
    outcome: str,
    validation_looking: bool,
    negative_reason: str,
) -> str:
    if negative_reason or outcome in {"fail", "not_run"}:
        return "negative"
    if validation_looking and outcome == "pass":
        return "strong"
    return "weak"


def _covered_paths(coverage: dict[str, object]) -> list[str]:
    return [str(item) for item in coverage.get("covered_path_patterns", []) or []]


def _coverage_aligned(
    coverage: dict[str, object],
    changed_paths: Iterable[str],
    risk_surfaces: Iterable[str],
) -> bool | str:
    paths = [str(path).strip() for path in changed_paths if str(path).strip()]
    surfaces = {str(surface).strip() for surface in risk_surfaces if str(surface).strip()}
    if not paths and not surfaces:
        return "unknown"
    category = str(coverage.get("category", ""))
    covered_surfaces = {str(surface) for surface in coverage.get("covered_risk_surfaces", [])}
    if category == "unknown":
        return False
    if surfaces and not (surfaces & covered_surfaces):
        return False
    return True


def _now_if_outcome(outcome: str) -> str:
    if outcome in {"pass", "fail", "not_run"}:
        return datetime.now(timezone.utc).isoformat()
    return ""
