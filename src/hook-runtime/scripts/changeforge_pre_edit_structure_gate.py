#!/usr/bin/env python3
"""PreToolUse implementation-structure gate for structural edits."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_changed_paths,
    extract_implementation_preflight_fields,
    is_pre_tool_use,
    load_state,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    session_id_from_event,
    tool_name,
    write_telemetry_event,
)
from changeforge_hook_policy import gate_mode, should_block, should_emit_context
from changeforge_runtime_adapters import adapter_for


EDIT_TOOLS = {"applypatch", "apply_patch", "edit", "write", "multiedit"}
HELPER_PATH_TOKENS = {
    "helper",
    "helpers",
    "common",
    "utils",
    "shared",
    "service",
    "services",
    "repository",
    "repositories",
    "repo",
    "adapter",
    "adapters",
    "client",
    "clients",
    "manager",
    "managers",
}
OBJECT_BOUNDARY_TOKENS = {"service", "repository", "repo", "adapter", "client", "manager"}
CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
    ".tsx",
}
CLASS_OR_OBJECT_RE = re.compile(
    r"^\+.*\b(class|interface|struct|trait|abstract|extends|implements|inheritance|reflection)\b",
    re.IGNORECASE | re.MULTILINE,
)
PUBLIC_API_RE = re.compile(
    r"^\+.*\b(export|public|pub|interface|class|def|func|function)\b",
    re.IGNORECASE | re.MULTILINE,
)
EXISTING_EXTENSION_RE = re.compile(
    r"^\+.*\b(case|elif|else if|switch|if|strategy|adapter|extends|implements|fallback|compat)\b",
    re.IGNORECASE | re.MULTILINE,
)


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    mode = gate_mode("pre_edit_structure")
    if mode == "off":
        return 0
    if not _is_pre_edit_event(event):
        return 0
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    result = evaluate_pre_edit(event, state, repo)
    if not result["required"]:
        return 0
    missing = result["missing"]
    manifest = result["manifest"]
    merge_state(
        repo,
        runtime,
        changed_paths=result["changed_paths"],
        implementation_preflights=result["preflight_summaries"],
        pre_edit_structure_findings=result["findings"],
        implementation_preflight_required=True,
        implementation_preflight_seen=bool(manifest.get("present")),
        implementation_preflight_blocked=bool(result["block"]),
        pre_edit_missing_read_evidence="read_evidence" in missing,
        pre_edit_missing_reuse_decision="reuse_decision" in missing,
        pre_edit_missing_placement_decision="placement_decision" in missing,
        pre_edit_missing_test_plan="test_plan" in missing,
        suggested_capabilities=["implementation-structure-design", "test-strategy"],
        suggested_gates=["quality-test-gate"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="pre_edit_structure_gate",
        event_name=event_name(event) or "PreToolUse",
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        changed_paths=result["changed_paths"],
        added_paths=result["added_paths"],
        hook_findings={"missing": missing, "findings": result["findings"]},
        suggested_capabilities=["implementation-structure-design", "test-strategy"],
        suggested_gates=["quality-test-gate"],
        read_evidence_seen=bool(result["has_read_evidence"]),
    )
    if not missing or mode == "monitor":
        return 0
    message = render_message(result)
    adapter = adapter_for(runtime)
    if result["block"]:
        adapter.emit_permission_decision("block", message)
    elif should_emit_context("pre_edit_structure"):
        adapter.emit_context(event_name(event) or "PreToolUse", message)
    return 0


def evaluate_pre_edit(event: dict, state: dict | None = None, repo: Path | None = None) -> dict:
    """Evaluate a PreToolUse edit event without emitting output."""
    state = state if isinstance(state, dict) else {}
    patch_text = extract_patch_text(event)
    changed_paths = [normalize_path(path) for path in extract_changed_paths(event)]
    added_paths = extract_added_paths(event, repo=repo)
    helper_paths = detect_new_helper_like_paths([*changed_paths, *added_paths])
    assistant_text = _assistant_text_from_event(event)
    manifest = extract_implementation_preflight_fields(assistant_text)
    has_read_evidence = _has_read_evidence(state, manifest)
    structural = _is_structural_edit(changed_paths, added_paths, helper_paths, patch_text)
    required = _is_pre_edit_event(event) and structural
    missing: list[str] = []
    findings: list[str] = []
    if not required:
        return _result(
            required=False,
            missing=[],
            findings=[],
            manifest=manifest,
            changed_paths=changed_paths,
            added_paths=added_paths,
            helper_paths=helper_paths,
            has_read_evidence=has_read_evidence,
            block=False,
        )
    if not has_read_evidence:
        missing.append("read_evidence")
        findings.append("no read evidence before edit")
    if not manifest.get("present"):
        missing.append("implementation_preflight")
        findings.append("no changeforge_implementation_preflight manifest")
    if added_paths and not manifest.get("placement_decision"):
        missing.append("placement_decision")
        findings.append("new file lacks placement decision")
    if helper_paths and not manifest.get("reuse_decision"):
        missing.append("reuse_decision")
        findings.append("helper/common/service-like path lacks reuse ladder")
    if _needs_object_boundary(patch_text, helper_paths) and not manifest.get("object_boundary"):
        missing.append("object_boundary")
        findings.append("object or public boundary lacks rationale")
    if structural and not manifest.get("test_plan"):
        missing.append("test_plan")
        findings.append("structural edit lacks test plan")
    if structural and not manifest.get("risk"):
        missing.append("risk")
        findings.append("structural edit lacks rollback or residual-risk note")
    high_confidence = (
        "read_evidence" in missing
        and "implementation_preflight" in missing
        and bool(added_paths or helper_paths)
    )
    block = should_block(
        "pre_edit_structure", confidence="high" if high_confidence else "medium"
    )
    return _result(
        required=True,
        missing=_unique(missing),
        findings=_unique(findings),
        manifest=manifest,
        changed_paths=changed_paths,
        added_paths=added_paths,
        helper_paths=helper_paths,
        has_read_evidence=has_read_evidence,
        block=block,
    )


def render_message(result: dict) -> str:
    missing_lines = "\n".join(f"  - {item}" for item in result["missing"])
    target_paths = ", ".join(result["changed_paths"][:6]) or "(unknown)"
    return (
        "ChangeForge Pre-Edit Implementation Structure Gate\n"
        "- stage: edit\n"
        f"- target paths: {target_paths}\n"
        "- missing:\n"
        f"{missing_lines}\n"
        "- required manifest:\n"
        "  changeforge_implementation_preflight:\n"
        "    read_evidence: target/sibling/caller/tests/config docs\n"
        "    placement_decision: target file, owner module, rejected locations\n"
        "    reuse_decision: direct reuse, extension reuse, new-code justification\n"
        "    object_boundary: artifact type, owner, invariant, API compatibility\n"
        "    test_plan: nearby tests and validation commands\n"
        "    risk: residual risk and rollback/revert path\n"
        "- action: read more / emit preflight / then edit"
    )


def extract_patch_text(event: dict) -> str:
    parts: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if not isinstance(value, str):
            return
        if "*** Begin Patch" in value or "diff --git" in value:
            parts.append(value)
        elif "\n" in value and any(line.startswith(("+", "-")) for line in value.splitlines()):
            parts.append(value)

    visit(event.get("tool_input") or event.get("toolInput") or event)
    return "\n".join(parts)


def extract_added_paths(event: dict, repo: Path | None = None) -> list[str]:
    patch_text = extract_patch_text(event)
    added: list[str] = []
    for line in patch_text.splitlines():
        match = re.match(r"^\*\*\* Add File:\s+(.+?)\s*$", line.strip())
        if match:
            added.append(normalize_path(match.group(1)))
            continue
        match = re.match(r"^diff --git a/(.+?) b/(.+?)\s*$", line.strip())
        if match and f"--- /dev/null" in patch_text:
            added.append(normalize_path(match.group(2)))
    tool = compact_name(tool_name(event))
    if tool == "write":
        for path in extract_changed_paths(event):
            normalized = normalize_path(path)
            if repo is None or not (repo / normalized).exists():
                added.append(normalized)
    return _unique(added)


def detect_new_helper_like_paths(paths: list[str]) -> list[str]:
    matches: list[str] = []
    for path in paths:
        tokens = _path_tokens(path)
        if tokens & HELPER_PATH_TOKENS:
            matches.append(path)
    return _unique(matches)


def detect_public_api_patch(patch_text: str) -> bool:
    return bool(PUBLIC_API_RE.search(patch_text or ""))


def detect_class_or_object_patch(patch_text: str) -> bool:
    return bool(CLASS_OR_OBJECT_RE.search(patch_text or ""))


def detect_existing_logic_extension(patch_text: str) -> bool:
    return bool(EXISTING_EXTENSION_RE.search(patch_text or ""))


def _is_pre_edit_event(event: dict) -> bool:
    if not is_pre_tool_use(event):
        return False
    return compact_name(tool_name(event)) in EDIT_TOOLS


def _has_read_evidence(state: dict, manifest: dict) -> bool:
    return bool(
        state.get("read_evidence_seen")
        or state.get("read_paths")
        or state.get("searched_patterns")
        or manifest.get("read_evidence")
    )


def _is_structural_edit(
    changed_paths: list[str], added_paths: list[str], helper_paths: list[str], patch_text: str
) -> bool:
    if added_paths or helper_paths:
        return True
    if any(Path(path).suffix in CODE_EXTENSIONS for path in changed_paths):
        return True
    return any(
        (
            detect_public_api_patch(patch_text),
            detect_class_or_object_patch(patch_text),
            detect_existing_logic_extension(patch_text),
        )
    )


def _needs_object_boundary(patch_text: str, helper_paths: list[str]) -> bool:
    if detect_class_or_object_patch(patch_text) or detect_public_api_patch(patch_text):
        return True
    for path in helper_paths:
        if _path_tokens(path) & OBJECT_BOUNDARY_TOKENS:
            return True
    return False


def _assistant_text_from_event(event: dict) -> str:
    texts: list[str] = []
    for key in (
        "message",
        "assistant_message",
        "assistantMessage",
        "last_assistant_message",
        "lastAssistantMessage",
        "response",
        "finalResponse",
    ):
        value = event.get(key)
        if isinstance(value, str):
            texts.append(value)
    transcript = event.get("transcript_path") or event.get("transcriptPath")
    if isinstance(transcript, str) and transcript.strip():
        tail = _transcript_tail(transcript)
        if tail:
            texts.append(tail)
    return "\n".join(texts)


def _transcript_tail(path: str) -> str:
    try:
        lines = Path(path).expanduser().read_text(encoding="utf-8").splitlines()
    except Exception:
        return ""
    for line in reversed(lines[-80:]):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(payload, dict) and payload.get("role") == "assistant":
            content = payload.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and isinstance(item.get("text"), str)
                ]
                return "\n".join(parts)
    return ""


def _path_tokens(path: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", normalize_path(path).casefold())
        if token
    }


def _result(
    *,
    required: bool,
    missing: list[str],
    findings: list[str],
    manifest: dict,
    changed_paths: list[str],
    added_paths: list[str],
    helper_paths: list[str],
    has_read_evidence: bool,
    block: bool,
) -> dict:
    fields = []
    if manifest.get("present"):
        fields = [
            key
            for key in (
                "read_evidence",
                "placement_decision",
                "reuse_decision",
                "object_boundary",
                "test_plan",
                "risk",
            )
            if manifest.get(key)
        ]
    return {
        "required": required,
        "missing": missing,
        "findings": findings,
        "manifest": manifest,
        "changed_paths": _unique(changed_paths),
        "added_paths": _unique(added_paths),
        "helper_paths": _unique(helper_paths),
        "has_read_evidence": has_read_evidence,
        "block": block,
        "preflight_summaries": [
            f"paths={','.join(_unique(changed_paths)[:5])}; fields={','.join(fields)}"
        ]
        if manifest.get("present")
        else [],
    }


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
