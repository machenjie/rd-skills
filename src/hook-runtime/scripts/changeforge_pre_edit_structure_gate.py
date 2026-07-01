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
    extract_repository_context_fields,
    extract_senior_programming_judgment_fields,
    is_pre_tool_use,
    load_state,
    memory_pre_edit_advice,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    session_id_from_event,
    tool_name,
    write_telemetry_event,
)
from changeforge_hook_policy import gate_mode, run_gate_with_policy, should_block, should_emit_context
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_runtime_route_resolver import CODE_FILE_EXTENSIONS


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
CODE_EXTENSIONS = CODE_FILE_EXTENSIONS
EDIT_CONTENT_KEYS = {"content", "new_string", "replacement", "text", "file_content"}
MAX_TRANSCRIPT_BYTES = 1_000_000
CLASS_OR_OBJECT_PATCH_RE = re.compile(
    r"^\+.*\b(class|interface|struct|trait|abstract|extends|implements|inheritance|reflection)\b",
    re.IGNORECASE | re.MULTILINE,
)
CLASS_OR_OBJECT_CONTENT_RE = re.compile(
    r"^\s*.*\b(class|interface|struct|trait|abstract|extends|implements|inheritance|reflection)\b",
    re.IGNORECASE | re.MULTILINE,
)
PUBLIC_API_PATCH_RE = re.compile(
    r"^\+.*\b(export|public|pub|interface|class|def|func|function)\b",
    re.IGNORECASE | re.MULTILINE,
)
PUBLIC_API_CONTENT_RE = re.compile(
    r"^\s*.*\b(export|public|pub|interface|class|def|func|function)\b",
    re.IGNORECASE | re.MULTILINE,
)
EXISTING_EXTENSION_PATCH_RE = re.compile(
    r"^\+.*\b(case|elif|else if|switch|if|strategy|adapter|extends|implements|fallback|compat)\b",
    re.IGNORECASE | re.MULTILINE,
)
EXISTING_EXTENSION_CONTENT_RE = re.compile(
    r"^\s*.*\b(case|elif|else if|switch|if|strategy|adapter|extends|implements|fallback|compat)\b",
    re.IGNORECASE | re.MULTILINE,
)


def main() -> int:
    return run_gate_with_policy(
        "pre_edit_structure",
        _main,
        fail_closed=_fail_closed,
    )


def _fail_closed(exc: Exception) -> None:
    runtime = detect_runtime({})
    adapter_for(runtime).emit_permission_decision(
        "block",
        f"ChangeForge Pre-Edit gate failed closed: {exc}",
    )


def _main() -> int:
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
    snapshot = snapshot_from_event_state(
        event,
        state,
        classification={
            "stage": "edit",
            "paths": result["changed_paths"],
            "tool": tool_name(event),
        },
        read_evidence={
            "paths": state.get("read_paths", []),
            "patterns": state.get("searched_patterns", []),
        },
        gate_name="pre_edit_structure",
        gate_mode=mode,
        gate_facts={"missing": missing, "findings": result["findings"]},
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    snapshot_update["changed_paths"] = result["changed_paths"]
    merge_state(
        repo,
        runtime,
        **snapshot_update,
        implementation_preflights=result["preflight_summaries"],
        senior_programming_judgments=result["senior_judgment_summaries"],
        pre_edit_structure_findings=result["findings"],
        implementation_preflight_required=True,
        implementation_preflight_seen=bool(manifest.get("present")),
        implementation_preflight_complete=bool(result["preflight_complete"]),
        implementation_preflight_blocked=bool(result["block"]),
        senior_programming_judgment_required=True,
        senior_programming_judgment_seen=bool(result["senior_judgment"].get("present")),
        senior_programming_judgment_complete=bool(result["senior_judgment_complete"]),
        senior_programming_judgment_blocked=bool(result["block"]),
        repository_context_seen=bool(result["repository_context"].get("complete")),
        pre_edit_missing_read_evidence="read_evidence" in missing,
        pre_edit_missing_reuse_decision="reuse_decision" in missing,
        pre_edit_missing_placement_decision="placement_decision" in missing,
        pre_edit_missing_test_plan="test_plan" in missing,
        pre_edit_missing_senior_programming_judgment="senior_programming_judgment" in missing,
        suggested_capabilities=[
            "implementation-structure-design",
            "senior-programming-judgment-core",
            "test-strategy",
        ],
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
        normalized_events=snapshot_update["normalized_events"],
        changed_paths=result["changed_paths"],
        deleted_paths=snapshot_update["deleted_paths"],
        generated_paths=snapshot_update["generated_paths"],
        external_file_changes=snapshot_update["external_file_changes"],
        config_changes=snapshot_update["config_changes"],
        added_paths=result["added_paths"],
        hook_findings={"missing": missing, "findings": result["findings"]},
        suggested_capabilities=[
            "implementation-structure-design",
            "senior-programming-judgment-core",
            "test-strategy",
        ],
        suggested_gates=["quality-test-gate"],
        read_evidence_seen=bool(result["has_read_evidence"]),
        repository_context_seen=bool(result["repository_context"].get("complete")),
        implementation_preflight_required=True,
        implementation_preflight_seen=bool(manifest.get("present")),
        implementation_preflight_complete=bool(result["preflight_complete"]),
        implementation_preflight_blocked=bool(result["block"]),
        senior_programming_judgment_required=True,
        senior_programming_judgment_seen=bool(result["senior_judgment"].get("present")),
        senior_programming_judgment_complete=bool(result["senior_judgment_complete"]),
        senior_programming_judgment_blocked=bool(result["block"]),
        edit_without_preflight_seen="implementation_preflight" in missing,
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
    content_text = extract_edit_content_text(event)
    raw_changed_paths = [normalize_path(path) for path in extract_changed_paths(event)]
    snapshot = snapshot_from_event_state(
        event,
        state,
        classification={
            "stage": "edit",
            "paths": raw_changed_paths,
            "tool": tool_name(event),
        },
        read_evidence={
            "paths": state.get("read_paths", []),
            "patterns": state.get("searched_patterns", []),
        },
        gate_name="pre_edit_structure",
    )
    changed_paths = snapshot.normalized_event.changed_paths or raw_changed_paths
    added_paths = extract_added_paths(event, repo=repo)
    helper_paths = detect_new_helper_like_paths([*changed_paths, *added_paths])
    assistant_text = _assistant_text_from_event(event)
    manifest = extract_implementation_preflight_fields(assistant_text)
    senior_judgment = extract_senior_programming_judgment_fields(assistant_text)
    repository_context = extract_repository_context_fields(assistant_text)
    has_read_evidence = _has_read_evidence(state, manifest)
    structural = _is_structural_edit(changed_paths, added_paths, helper_paths, patch_text, content_text)
    required = _is_pre_edit_event(event) and structural
    missing: list[str] = []
    findings: list[str] = []
    if not required:
        return _result(
            required=False,
            missing=[],
            findings=[],
            manifest=manifest,
            senior_judgment=senior_judgment,
            repository_context=repository_context,
            changed_paths=changed_paths,
            added_paths=added_paths,
            helper_paths=helper_paths,
            has_read_evidence=has_read_evidence,
            block=False,
        )
    if not has_read_evidence:
        missing.append("read_evidence")
        findings.append("no read evidence before edit")
    if not repository_context.get("complete") and not manifest.get("read_evidence"):
        missing.append("repository_context")
        findings.append("no structured repository_context or preflight read evidence before edit")
    if not manifest.get("present"):
        missing.append("implementation_preflight")
        findings.append("no changeforge_implementation_preflight manifest")
    if added_paths and not manifest.get("placement_decision"):
        missing.append("placement_decision")
        findings.append("new file lacks placement decision")
    if helper_paths and not manifest.get("reuse_decision"):
        missing.append("reuse_decision")
        findings.append("helper/common/service-like path lacks reuse ladder")
    if _needs_object_boundary(patch_text, content_text, helper_paths) and not manifest.get(
        "object_boundary"
    ):
        missing.append("object_boundary")
        findings.append("object or public boundary lacks rationale")
    if structural and not manifest.get("test_plan"):
        missing.append("test_plan")
        findings.append("structural edit lacks test plan")
    if structural and not manifest.get("risk"):
        missing.append("risk")
        findings.append("structural edit lacks rollback or residual-risk note")
    if not senior_judgment.get("complete"):
        missing.append("senior_programming_judgment")
        if not senior_judgment.get("present"):
            findings.append("no senior_programming_judgment manifest")
        else:
            missing_sections = ",".join(senior_judgment.get("missing", [])[:6])
            findings.append(f"senior_programming_judgment missing sections: {missing_sections}")
    memory_advice = (
        memory_pre_edit_advice(repo, changed_paths, state, assistant_text)
        if repo is not None
        else {"fragile_paths": [], "repeat_failure": {}, "missing": []}
    )
    if memory_advice.get("fragile_paths"):
        findings.append(
            "fragile file memory gate requires read/test/memory/preflight evidence"
        )
        for item in memory_advice.get("missing", []):
            if item not in missing:
                missing.append(item)
    if memory_advice.get("historical_fragile_paths"):
        for warning in memory_advice.get("warnings", []):
            if warning:
                findings.append(str(warning))
    repeat_failure = memory_advice.get("repeat_failure") or {}
    if repeat_failure.get("repeated"):
        if repeat_failure.get("allowed_to_continue", True):
            findings.append("repeat failure memory gate satisfied by diagnosis or repair route")
        else:
            findings.append(
                "repeat failure memory gate requires failure diagnosis or repair route"
            )
            if "failure_diagnosis_route" not in missing:
                missing.append("failure_diagnosis_route")
    preflight_complete = bool(manifest.get("present")) and not missing
    code_edit_without_read_preflight = (
        compact_name(tool_name(event)) in EDIT_TOOLS
        and any(Path(path).suffix in CODE_EXTENSIONS for path in changed_paths)
        and "read_evidence" in missing
        and "implementation_preflight" in missing
    )
    high_confidence = (
        (
            "read_evidence" in missing
            and "implementation_preflight" in missing
            and bool(added_paths or helper_paths or code_edit_without_read_preflight)
        )
        or "failure_diagnosis_route" in missing
    )
    block = should_block(
        "pre_edit_structure", confidence="high" if high_confidence else "medium"
    )
    return _result(
        required=True,
        missing=_unique(missing),
        findings=_unique(findings),
        manifest=manifest,
        senior_judgment=senior_judgment,
        repository_context=repository_context,
        changed_paths=changed_paths,
        added_paths=added_paths,
        helper_paths=helper_paths,
        has_read_evidence=has_read_evidence,
        block=block,
        preflight_complete=preflight_complete,
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
        "  senior_programming_judgment:\n"
        "    purpose, facts, objects, states, behaviors, rules, invariants,\n"
        "    boundaries, failure_contract, side_effects, reuse_and_placement,\n"
        "    minimality_decision, validation_map, observability_map,\n"
        "    residual_risk, or an allowed skip_reason for trivial/no-semantic work\n"
        "  repository_context:\n"
        "    source_of_truth/context_pack, reuse candidates, validation candidates,\n"
        "    graph_freshness, and residual_risk\n"
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


def extract_edit_content_text(event: dict) -> str:
    parts: list[str] = []
    roots = [
        event.get("tool_input"),
        event.get("toolInput"),
        event.get("input"),
        event.get("arguments"),
        event.get("parameters"),
        event.get("params"),
    ]
    roots = [root for root in roots if isinstance(root, dict)]
    if not roots:
        roots = [event]

    def visit(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
            return
        if isinstance(value, list):
            for child in value:
                visit(child, key)
            return
        if not isinstance(value, str):
            return
        normalized_key = str(key or "").strip()
        if normalized_key not in EDIT_CONTENT_KEYS:
            return
        if "*** Begin Patch" in value or "diff --git" in value:
            return
        text = value.strip()
        if text:
            parts.append(text)

    for root in roots:
        visit(root)
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


def detect_public_api_patch(*texts: str) -> bool:
    return _detect_edit_text(PUBLIC_API_PATCH_RE, PUBLIC_API_CONTENT_RE, *texts)


def detect_class_or_object_patch(*texts: str) -> bool:
    return _detect_edit_text(CLASS_OR_OBJECT_PATCH_RE, CLASS_OR_OBJECT_CONTENT_RE, *texts)


def detect_existing_logic_extension(*texts: str) -> bool:
    return _detect_edit_text(EXISTING_EXTENSION_PATCH_RE, EXISTING_EXTENSION_CONTENT_RE, *texts)


def _detect_edit_text(patch_pattern: re.Pattern, content_pattern: re.Pattern, *texts: str) -> bool:
    for text in texts:
        value = text or ""
        if not value:
            continue
        if "*** Begin Patch" in value or "diff --git" in value:
            if patch_pattern.search(value):
                return True
            continue
        if content_pattern.search(value):
            return True
    return False


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
    changed_paths: list[str],
    added_paths: list[str],
    helper_paths: list[str],
    patch_text: str,
    content_text: str,
) -> bool:
    if added_paths or helper_paths:
        return True
    if any(_is_structural_path(path) for path in changed_paths):
        return True
    return any(
        (
            detect_public_api_patch(patch_text, content_text),
            detect_class_or_object_patch(patch_text, content_text),
            detect_existing_logic_extension(patch_text, content_text),
        )
    )


def _is_structural_path(path: str) -> bool:
    normalized = normalize_path(path).casefold()
    suffix = Path(normalized).suffix
    if suffix in CODE_EXTENSIONS:
        return True
    registry_source_prefix = "src/" + "registry/"
    if normalized.startswith((registry_source_prefix, "registry/", "src/hook-runtime/")):
        return True
    if "/adapter/" in normalized or "/adapters/" in normalized:
        return True
    if normalized.startswith(("dist/", "generated/")) or "/generated/" in normalized:
        return True
    if normalized.startswith("tests/") or "/test/" in normalized or "/tests/" in normalized:
        return True
    return Path(normalized).name in {
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
        "pyproject.toml",
        "requirements.txt",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
    }


def _needs_object_boundary(patch_text: str, content_text: str, helper_paths: list[str]) -> bool:
    if detect_class_or_object_patch(patch_text, content_text) or detect_public_api_patch(
        patch_text, content_text
    ):
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
        transcript_path = Path(path).expanduser()
        with transcript_path.open("rb") as file:
            try:
                file.seek(0, 2)
                size = file.tell()
                file.seek(max(size - MAX_TRANSCRIPT_BYTES, 0))
            except OSError:
                pass
            lines = file.read().decode("utf-8", errors="replace").splitlines()
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
    senior_judgment: dict,
    changed_paths: list[str],
    added_paths: list[str],
    helper_paths: list[str],
    has_read_evidence: bool,
    block: bool,
    preflight_complete: bool = False,
    repository_context: dict | None = None,
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
    senior_fields = []
    if senior_judgment.get("present"):
        senior_fields = list(senior_judgment.get("sections", []))
        if senior_judgment.get("allowed_skip"):
            senior_fields.append("allowed_skip")
    return {
        "required": required,
        "missing": missing,
        "findings": findings,
        "manifest": manifest,
        "senior_judgment": senior_judgment,
        "repository_context": repository_context if isinstance(repository_context, dict) else {},
        "changed_paths": _unique(changed_paths),
        "added_paths": _unique(added_paths),
        "helper_paths": _unique(helper_paths),
        "has_read_evidence": has_read_evidence,
        "block": block,
        "preflight_complete": bool(preflight_complete),
        "senior_judgment_complete": bool(senior_judgment.get("complete")),
        "preflight_summaries": [
            f"paths={','.join(_unique(changed_paths)[:5])}; fields={','.join(fields)}"
        ]
        if manifest.get("present")
        else [],
        "senior_judgment_summaries": [
            f"paths={','.join(_unique(changed_paths)[:5])}; fields={','.join(senior_fields)}"
        ]
        if senior_judgment.get("present")
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
