#!/usr/bin/env python3
"""Bounded branch and route-repair summaries for ChangeForge hook state."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = 1
MAX_ITEMS = 10
MAX_TEXT = 240
MAX_PATHS = 20
TRIGGERS = {
    "repeated_same_path_retry",
    "repair_after_review",
    "route_repair",
    "branch_switch",
    "compaction_recovery",
}
FORBIDDEN_KEY_TOKENS = (
    "prompt",
    "raw_prompt",
    "assistant_message",
    "raw_assistant",
    "raw_output",
    "full_output",
    "command_output",
    "stdout",
    "stderr",
    "full_diff",
    "file_contents",
    "environment",
    "env",
    "secret",
    "password",
    "api_key",
    "apikey",
    "token",
)
SAFE_KEY_EXCEPTIONS = {"prompt_signal", "prompt_signals"}
ABSOLUTE_PATH_RE = re.compile(
    r"(/Users/[^\s\"'<>]+|/home/[^\s\"'<>]+|/private/var/[^\s\"'<>]+|"
    r"/var/folders/[^\s\"'<>]+|/tmp/[^\s\"'<>]+|[A-Za-z]:\\Users\\[^\s\"'<>]+)"
)
SECRET_RE = re.compile(
    r"(sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+|"
    r"(?i:api[_-]?key|access[_-]?token|bearer[_-]?token|password|secret)"
    r"\s*[:=]\s*[A-Za-z0-9_./+=-]{8,})"
)


def build_route_repair_summary(state: dict, *, event: dict | None = None) -> dict:
    """Build a bounded route-repair summary from hook state.

    The summary is intentionally lossy: it preserves route, validation, file,
    and reusable finding facts without raw prompts, raw tool output, full diffs,
    or file contents.
    """
    state = state if isinstance(state, dict) else {}
    event = event if isinstance(event, dict) else {}
    source_findings = _privacy_findings([state, event])
    forbidden_retries = _forbidden_retries(state, event)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "summary_id": "",
        "trigger": _trigger(state, event),
        "abandoned_or_repaired_route": {
            "owner_skill": _clean_text(
                state.get("owner_skill")
                or _active_context(state).get("owner_skill")
                or event.get("owner_skill")
            ),
            "reviewer_skill": _clean_text(
                state.get("reviewer_skill")
                or _active_context(state).get("reviewer_skill")
                or event.get("reviewer_skill")
            ),
            "hypothesis": _first_signal(
                state,
                ("route hypothesis", "hypothesis", "abandoned route", "failed route"),
            ),
            "files_touched": _path_list(
                [
                    *(_as_list(state.get("changed_paths"))),
                    *(_as_list(state.get("deleted_paths"))),
                    *(_as_list(state.get("generated_paths"))),
                ],
            ),
            "validation_result": _first_text_item(
                state.get("validation_results"),
                default="not_recorded",
            ),
            "failure_reason": _failure_reason(state, forbidden_retries),
        },
        "reusable_findings": _clean_list(
            [
                *(_as_list(state.get("review_findings"))),
                *(_as_list(state.get("repair_findings"))),
                *(_as_list(state.get("reuse_findings"))),
            ],
            max_items=MAX_ITEMS,
        ),
        "forbidden_retries": forbidden_retries,
        "new_route": {
            "owner_skill": _clean_text(
                event.get("new_owner_skill")
                or _active_context(state).get("new_owner_skill")
                or state.get("owner_skill")
            ),
            "selected_capabilities": _clean_list(
                _active_context(state).get("selected_capabilities")
                or state.get("suggested_capabilities"),
                max_items=MAX_ITEMS,
            ),
            "validation_plan": _clean_list(
                _active_context(state).get("tdd_validation_plan")
                or state.get("validation_results"),
                max_items=MAX_ITEMS,
            ),
        },
        "residual_risk": _clean_list(
            [
                *(_as_list(state.get("closure_risk_surfaces"))),
                *(_as_list(_active_context(state).get("residual_risk"))),
            ],
            max_items=MAX_ITEMS,
        ),
        "source_privacy_findings": source_findings,
        "source_privacy_status": "fail" if source_findings else "pass",
        "retained_summary_privacy_findings": [],
        "retained_summary_privacy_status": "pass",
        "privacy_redaction_status": "pass",
        "privacy_status": "pass",
    }
    summary = sanitize_route_repair_summary(summary)
    summary["summary_id"] = _summary_id(summary)
    return summary


def route_repair_summary_required(state: dict) -> bool:
    """Return true when state indicates a route-repair branch must be summarized."""
    state = state if isinstance(state, dict) else {}
    if _as_list(state.get("route_repair_forbidden_retries")):
        return True
    signals = _joined(
        [
            state.get("repair_events"),
            state.get("repair_findings"),
            state.get("review_findings"),
            state.get("prompt_signals"),
            state.get("closure_risk_surfaces"),
        ]
    )
    required_markers = (
        "route repair",
        "route_repair",
        "branch switch",
        "branch_switch",
        "abandoned route",
        "failed route",
        "repeated same-path",
        "same-path retry",
        "same path retry",
        "forbidden retry",
    )
    return any(marker in signals for marker in required_markers)


def sanitize_route_repair_summary(summary: dict) -> dict:
    """Return a bounded allowlisted route-repair summary."""
    source = summary if isinstance(summary, dict) else {}
    route = source.get("abandoned_or_repaired_route")
    route = route if isinstance(route, dict) else {}
    new_route = source.get("new_route")
    new_route = new_route if isinstance(new_route, dict) else {}
    source_findings = _clean_list(source.get("source_privacy_findings"), max_items=MAX_ITEMS)
    for finding in _privacy_findings([source]):
        if finding not in source_findings:
            source_findings.append(finding)
    if not source_findings and str(source.get("source_privacy_status") or "").strip() == "fail":
        source_findings = ["legacy_source_privacy_fail"]
    clean = {
        "schema_version": SCHEMA_VERSION,
        "summary_id": _clean_text(source.get("summary_id"), limit=80),
        "trigger": _clean_trigger(source.get("trigger")),
        "abandoned_or_repaired_route": {
            "owner_skill": _clean_text(route.get("owner_skill")),
            "reviewer_skill": _clean_text(route.get("reviewer_skill")),
            "hypothesis": _clean_text(route.get("hypothesis")),
            "files_touched": _path_list(route.get("files_touched")),
            "validation_result": _clean_text(route.get("validation_result")) or "not_recorded",
            "failure_reason": _clean_text(route.get("failure_reason")) or "not_recorded",
        },
        "reusable_findings": _clean_list(source.get("reusable_findings"), max_items=MAX_ITEMS),
        "forbidden_retries": _clean_list(source.get("forbidden_retries"), max_items=MAX_ITEMS),
        "new_route": {
            "owner_skill": _clean_text(new_route.get("owner_skill")),
            "selected_capabilities": _clean_list(new_route.get("selected_capabilities"), max_items=MAX_ITEMS),
            "validation_plan": _clean_list(new_route.get("validation_plan"), max_items=MAX_ITEMS),
        },
        "residual_risk": _clean_list(source.get("residual_risk"), max_items=MAX_ITEMS),
        "source_privacy_findings": source_findings,
        "source_privacy_status": "fail" if source_findings else "pass",
        "retained_summary_privacy_findings": [],
        "retained_summary_privacy_status": "pass",
        "privacy_redaction_status": "pass",
        "privacy_status": "pass",
    }
    retained_findings = _privacy_findings([_summary_core(clean)])
    clean["retained_summary_privacy_findings"] = retained_findings
    clean["retained_summary_privacy_status"] = "fail" if retained_findings else "pass"
    clean["privacy_redaction_status"] = "pass" if not retained_findings else "fail"
    clean["privacy_status"] = clean["retained_summary_privacy_status"]
    if not clean["summary_id"]:
        clean["summary_id"] = _summary_id(clean)
    return clean


def _trigger(state: dict, event: dict) -> str:
    text = _joined(
        [
            state.get("route_repair_forbidden_retries"),
            state.get("repair_events"),
            state.get("review_findings"),
            state.get("prompt_signals"),
            event.get("trigger"),
            event.get("reason"),
            event.get("source"),
        ]
    )
    if "same-path" in text or "same path" in text or "forbidden retry" in text:
        return "repeated_same_path_retry"
    if ("repair" in text and "review" in text) or state.get("repair_evidence_seen"):
        return "repair_after_review"
    if "branch" in text and "switch" in text:
        return "branch_switch"
    if "compact" in text:
        return "compaction_recovery"
    return "route_repair"


def _clean_trigger(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in TRIGGERS else "route_repair"


def _forbidden_retries(state: dict, event: dict) -> list[str]:
    values = [
        *(_as_list(state.get("route_repair_forbidden_retries"))),
        *(_as_list(event.get("route_repair_forbidden_retries"))),
    ]
    if values:
        return _clean_list(values, max_items=MAX_ITEMS)
    text = _joined([state.get("repair_events"), state.get("prompt_signals"), event.get("reason")])
    if "same-path" in text or "same path" in text:
        return ["same-path retry requires route repair summary before another attempt"]
    return []


def _failure_reason(state: dict, forbidden_retries: list[str]) -> str:
    if forbidden_retries:
        return forbidden_retries[0]
    for source in (state.get("repair_findings"), state.get("review_findings"), state.get("validation_results")):
        text = _first_text_item(source)
        if text:
            return text
    return "not_recorded"


def _first_signal(state: dict, markers: tuple[str, ...]) -> str:
    for value in _as_list(state.get("repair_events")) + _as_list(state.get("prompt_signals")):
        text = _clean_text(value)
        lowered = text.casefold()
        if any(marker in lowered for marker in markers):
            return text
    return ""


def _first_text_item(value: Any, *, default: str = "") -> str:
    items = _clean_list(value, max_items=1)
    return items[0] if items else default


def _active_context(state: dict) -> dict:
    context = state.get("active_skill_context")
    return context if isinstance(context, dict) else {}


def _clean_list(value: Any, *, max_items: int) -> list[str]:
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


def _clean_mapping(value: dict) -> dict:
    cleaned: dict[str, str] = {}
    for key, raw in value.items():
        name = _clean_text(key, limit=80)
        if not name or _forbidden_key(name):
            continue
        text = _clean_text(raw)
        if text:
            cleaned[name] = text
        if len(cleaned) >= MAX_ITEMS:
            break
    return cleaned


def _path_list(value: Any) -> list[str]:
    paths: list[str] = []
    for raw in _as_list(value):
        text = _clean_text(raw, limit=300).replace("\\", "/").lstrip("./")
        if not text:
            continue
        if "<local-path>" in text:
            text = "<local-path>"
        if text and text not in paths:
            paths.append(text[:MAX_TEXT])
        if len(paths) >= MAX_PATHS:
            break
    return paths


def _clean_text(value: Any, *, limit: int = MAX_TEXT) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = SECRET_RE.sub("<redacted-secret>", text)
    text = ABSOLUTE_PATH_RE.sub("<local-path>", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    return text[:limit]


def _privacy_failed(values: list[Any]) -> bool:
    return bool(_privacy_findings(values))


def _privacy_findings(values: list[Any]) -> list[str]:
    findings: list[str] = []
    for value in values:
        if _contains_forbidden_key(value):
            findings.append("forbidden_raw_field")
        try:
            text = json.dumps(value, sort_keys=True, ensure_ascii=False)
        except TypeError:
            text = str(value)
        if SECRET_RE.search(text):
            findings.append("secret_like_value")
        if ABSOLUTE_PATH_RE.search(text):
            findings.append("absolute_path")
    deduped: list[str] = []
    for finding in findings:
        if finding not in deduped:
            deduped.append(finding)
    return deduped[:MAX_ITEMS]


def _summary_core(summary: dict) -> dict:
    return {
        "schema_version": summary.get("schema_version"),
        "summary_id": summary.get("summary_id"),
        "trigger": summary.get("trigger"),
        "abandoned_or_repaired_route": summary.get("abandoned_or_repaired_route"),
        "reusable_findings": summary.get("reusable_findings"),
        "forbidden_retries": summary.get("forbidden_retries"),
        "new_route": summary.get("new_route"),
        "residual_risk": summary.get("residual_risk"),
    }


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if _forbidden_key(str(key)):
                return True
            if _contains_forbidden_key(child):
                return True
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _forbidden_key(value: str) -> bool:
    lowered = value.casefold()
    if lowered in SAFE_KEY_EXCEPTIONS:
        return False
    return any(token in lowered for token in FORBIDDEN_KEY_TOKENS)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _joined(values: list[Any]) -> str:
    texts: list[str] = []
    for value in values:
        for item in _as_list(value):
            texts.append(str(item).casefold())
    return " ".join(texts)


def _summary_id(summary: dict) -> str:
    payload = json.dumps(
        {
            "trigger": summary.get("trigger"),
            "route": summary.get("abandoned_or_repaired_route"),
            "forbidden_retries": summary.get("forbidden_retries"),
            "new_route": summary.get("new_route"),
        },
        sort_keys=True,
    )
    return "route-repair-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


__all__ = [
    "build_route_repair_summary",
    "route_repair_summary_required",
    "sanitize_route_repair_summary",
]
