#!/usr/bin/env python3
"""Remind agents to close ChangeForge handoff evidence before stopping."""

from __future__ import annotations

import re

from changeforge_common import (
    clear_state,
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_stop_reminder,
    event_name,
    extract_manifest_fields,
    hook_mode,
    is_stop,
    load_state,
    read_event,
    repo_root,
    session_id_from_event,
    write_telemetry_event,
)


CLOSURE_KEYWORDS = {
    "skills": ["skill", "ChangeForge", "router", "路由", "技能"],
    "files": ["file", "changed", "修改", "文件"],
    "validation": ["test", "verify", "validation", "验证", "测试"],
    "risk": ["risk", "residual", "风险", "未验证"],
    "next": ["next", "下一步", "后续"],
}

# Success-implying completion language. Presence detection only: the gate never
# judges whether a claim is true, it only notices a completion claim so the
# closure can be checked for matching validation evidence.
COMPLETION_LANGUAGE = [
    "done",
    "completed",
    "complete",
    "fixed",
    "resolved",
    "ready for review",
    "all tests pass",
    "should pass",
    "should work",
    "works now",
    "everything works",
    "完成",
    "修复完毕",
    "已修复",
]

NEGATIVE_VALIDATION_PHRASES = [
    "not verified",
    "not run",
    "not tested",
    "unable to run",
    "unable to verify",
    "could not run",
    "cannot run",
    "did not run",
    "validation not run",
    "tests not run",
    "tests are unavailable",
    "test runner is not installed",
    "未验证",
    "没有运行",
    "无法运行",
    "未运行",
]
VALIDATION_COMMAND_RE = re.compile(
    r"\b("
    r"pytest|unittest|go\s+test|cargo\s+test|npm\s+test|pnpm\s+test|"
    r"yarn\s+test|python3?\s+-m\s+unittest|scripts/validate[\w./-]*|"
    r"validate[-_\w./]*|eval-routing|eval-agent-behavior|"
    r"eval-pressure-behavior|run-codegen-benchmarks|validate-installation|"
    r"build\.py"
    r")\b",
    re.IGNORECASE,
)
VALIDATION_OUTCOME_RE = re.compile(
    r"\b("
    r"exit\s*(code)?\s*0|return\s*code\s*0|0\s+errors?|0\s+failures?|"
    r"\d+\s+passed|passed|passes|succeeded|success|green|validated|"
    r"通过|成功|退出码\s*0"
    r")\b",
    re.IGNORECASE,
)
VALIDATION_ARTIFACT_RE = re.compile(
    r"\b("
    r"output|artifact|report|log|junit|coverage|snapshot|build artifact"
    r")\b",
    re.IGNORECASE,
)

# Conditional keyword groups checked only when the matching structure gate fired
# this turn. They keep the closure reminder targeted instead of always demanding
# every kind of evidence.
CONDITIONAL_KEYWORDS = {
    "naming": ["naming", "命名", "filename", "文件名"],
    "reuse": ["reuse", "复用", "placement", "放置", "归属", "extension", "扩展"],
    "extension_safety": [
        "compatibility",
        "兼容",
        "behavior preserved",
        "旧行为",
        "行为保持",
        "extension",
        "扩展",
    ],
    "refactor": ["refactor", "重构", "class", "object", "inheritance", "reflection", "invariant"],
    "comments": [
        "comment",
        "doc comment",
        "注释",
        "文档注释",
        "godoc",
        "jsdoc",
        "javadoc",
        "docstring",
        "rustdoc",
        "test scenario",
        "regression",
        "edge case",
    ],
    "clarity": [
        "clarity",
        "main flow",
        "readability",
        "maintainability",
        "signature",
        "side effect",
        "cleanup",
        "deprecation",
        "feature flag",
        "change locality",
    ],
}
CONDITIONAL_GROUP_BY_STATE = {
    "file_naming_findings": "naming",
    "reuse_findings": "reuse",
    "extension_reuse_findings": "extension_safety",
    "advanced_refactor_findings": "refactor",
    "comment_findings": "comments",
    "structure_quality_findings": "clarity",
}


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    if runtime == "unknown":
        return 0
    mode = hook_mode()
    if mode == "off":
        return 0
    if not is_stop(event):
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        state = load_state(repo)
        debug_log(
            repo,
            f"stop gate runtime={runtime} event={event_name(event)} has_surface={_has_closure_surface(state)} validation_command_seen={state.get('validation_command_seen')}",
        )
        if not _has_closure_surface(state):
            return 0
        final_text = _final_text(event)
        manifest = extract_manifest_fields(final_text)
        signals = _closure_signals(final_text, state, manifest)
        write_telemetry_event(
            repo,
            runtime=runtime,
            hook_name="stop_closure_gate",
            event_name=event_name(event),
            mode=mode,
            session_id=session_id_from_event(event),
            cwd=cwd_from_event(event),
            changed_paths=state.get("changed_paths", []),
            hook_findings=_stop_findings(state),
            suggested_skills=state.get("suggested_skills", []),
            suggested_capabilities=state.get("suggested_capabilities", []),
            suggested_gates=state.get("suggested_gates", []),
            suggested_domain_extensions=state.get("suggested_domain_extensions", []),
            risk_surfaces=state.get("risk_surfaces", []),
            route_manifest_detected=signals["route_manifest"],
            required_references_detected=signals["references"],
            validation_evidence_detected=signals["validation"],
            residual_risk_detected=signals["risk"],
            completion_language_detected=signals["completion_language"],
            stage_manifest_detected=bool(manifest.get("stage_present")),
            manifest_current_stage=manifest.get("current_stage", ""),
            manifest_selected_skills=manifest.get("selected_skills", []),
            manifest_selected_capabilities=manifest.get("selected_capabilities", []),
            manifest_selected_domain_extensions=manifest.get("selected_domain_extensions", []),
            manifest_required_references=manifest.get("required_references", []),
            manifest_required_quality_gates=manifest.get("required_quality_gates", []),
            manifest_skipped_quality_gates=manifest.get("skipped_quality_gates", []),
        )
        if mode == "monitor":
            clear_state(repo, runtime)
            return 0
        missing = _missing_keyword_groups(final_text, state, manifest) if final_text else []
        stop_hook_active = bool(event.get("stop_hook_active") or event.get("stopHookActive"))
        should_block = mode == "block" and bool(missing) and not stop_hook_active
        message = _closure_message(state, final_text, manifest)
        if should_block:
            emit_stop_reminder(runtime, message, continue_turn=True)
        else:
            clear_state(repo, runtime)
            emit_stop_reminder(runtime, message, continue_turn=False)
        return 0
    except Exception as exc:
        emit_stop_reminder(
            runtime,
            f"ChangeForge Hook Runtime warning: closure gate failed open: {exc}",
            continue_turn=False,
        )
        return 0




def _has_closure_surface(state: dict) -> bool:
    return bool(
        state.get("changed_paths")
        or state.get("risk_surfaces")
        or state.get("structure_findings")
        or state.get("file_naming_findings")
        or state.get("reuse_findings")
        or state.get("extension_reuse_findings")
        or state.get("advanced_refactor_findings")
        or state.get("comment_findings")
        or state.get("structure_quality_findings")
    )


def _closure_signals(final_text: str, state: dict, manifest: dict) -> dict[str, bool]:
    """Completeness flags for telemetry. This is presence detection only.

    The Stop gate does not judge semantic correctness; it records whether the
    final handoff text contains each kind of closure evidence so offline review
    can spot missing route manifests, validation, references, or residual risk.
    The parsed manifest sharpens route and reference detection beyond a bare
    keyword scan.
    """
    lowered = final_text.casefold()

    def has(group: str) -> bool:
        return any(keyword.casefold() in lowered for keyword in CLOSURE_KEYWORDS[group])

    return {
        "route_manifest": bool(manifest.get("route_present")),
        "validation": _has_validation_evidence(final_text, state),
        "risk": has("risk"),
        "references": bool(manifest.get("required_references")) or "reference" in lowered,
        "skills": has("skills"),
        "completion_language": any(
            phrase.casefold() in lowered for phrase in COMPLETION_LANGUAGE
        ),
    }


def _stop_findings(state: dict) -> dict[str, list[str]]:
    return {
        key: list(state.get(key, []))
        for key in (
            "structure_findings",
            "file_naming_findings",
            "reuse_findings",
            "extension_reuse_findings",
            "advanced_refactor_findings",
            "comment_findings",
            "structure_quality_findings",
        )
    }


def _closure_message(state: dict, final_text: str, manifest: dict | None = None) -> str:
    missing = _missing_keyword_groups(final_text, state, manifest) if final_text else []
    route_present = bool(manifest and manifest.get("route_present"))
    details: list[str] = []
    if state.get("structure_findings"):
        details.append("- structure gate fired")
    if state.get("file_naming_findings"):
        details.append("- file naming gate fired")
    if state.get("reuse_findings"):
        details.append("- reuse gate fired")
    if state.get("extension_reuse_findings"):
        details.append("- extension reuse gate fired")
    if state.get("advanced_refactor_findings"):
        details.append("- advanced refactor gate fired")
    if state.get("comment_findings"):
        details.append("- comment quality gate fired")
    if state.get("structure_quality_findings"):
        details.append("- structure quality gate fired")
    if state.get("risk_surfaces"):
        details.append(f"- risk surfaces: {', '.join(state['risk_surfaces'])}")
    if state.get("changed_paths"):
        details.append(f"- changed paths: {', '.join(state['changed_paths'])}")
    if state.get("validation_command_seen") or state.get("validation_seen"):
        details.append("- validation command was observed")
    if state.get("suggested_domain_extensions"):
        details.append(
            f"- suggested domain extensions: {', '.join(state['suggested_domain_extensions'])}"
        )
    if missing:
        details.append(f"- missing closure signals: {', '.join(missing)}")
    detail_text = "\n".join(details)
    if detail_text:
        detail_text = f"\nObserved this turn:\n{detail_text}\n"
    evidence_text = _structure_evidence_block(state)

    headline = "ChangeForge Closure Gate reminder."
    if not route_present:
        headline += (
            " MISSING: this handoff has no complete changeforge_route manifest."
            " Real changes were observed but the route was not emitted in"
            " machine-readable form with selected_skills, selected_capabilities,"
            " required_references, and required_quality_gates."
            " Emit the changeforge_route manifest (and changeforge_stage_route for"
            " non-trivial engineering work) so the route is reviewable, not only"
            " described in prose."
        )
    if _unverified_completion(final_text, state):
        headline += (
            " MISSING: this handoff uses completion language but shows no validation"
            " evidence. State the fresh command and outcome that back the claim, or"
            " replace the claim with a not-verified disclosure (status, why not run,"
            " residual risk, exact command)."
        )

    return f"""{headline}
{detail_text}
This turn changed files or triggered risk surfaces. Before final handoff, include:
- the changeforge_route manifest: selected skills, selected capabilities, required references, and required quality gates
- for non-trivial engineering work, the changeforge_stage_route manifest: current stage, launched and explicitly skipped capabilities, and next-stage handoff
- required references: the router self-use references plus the selected capability references
- changed files
- structure/reuse/placement rationale if structure gate fired
- validation commands and results
- residual risks and unverified items
- next actions{evidence_text}"""


def _structure_evidence_block(state: dict) -> str:
    blocks: list[str] = []
    if state.get("file_naming_findings"):
        blocks.append(
            "- file naming convention evidence:\n"
            "  - same-directory files inspected\n"
            "  - parent-module naming pattern\n"
            "  - selected filename rationale\n"
            "  - rejected filename alternatives"
        )
    if state.get("reuse_findings"):
        blocks.append(
            "- reuse ladder record:\n"
            "  - direct reuse\n"
            "  - extension reuse\n"
            "  - composition/wrapper\n"
            "  - extraction\n"
            "  - new code justification"
        )
    if state.get("extension_reuse_findings"):
        blocks.append(
            "- extension safety record:\n"
            "  - old behavior preserved\n"
            "  - compatibility risk\n"
            "  - old behavior tests\n"
            "  - new behavior tests"
        )
    if state.get("advanced_refactor_findings"):
        blocks.append(
            "- advanced refactor decision:\n"
            "  - object/function/module choice\n"
            "  - class/interface/inheritance/reflection justification\n"
            "  - state/invariant/lifecycle/collaborator rationale\n"
            "  - public behavior tests"
        )
    if state.get("comment_findings"):
        blocks.append(
            "- comment quality evidence:\n"
            "  - exported/public doc comments added\n"
            "  - class/function/method comments added where required\n"
            "  - non-trivial test comments added\n"
            "  - critical internal logic comments added\n"
            "  - redundant comments avoided or removed"
        )
    if state.get("structure_quality_findings"):
        blocks.append(
            "- code clarity evidence:\n"
            "  - main flow assessment\n"
            "  - nested branch and signature trap review\n"
            "  - side-effect boundary review\n"
            "  - cleanup/deprecation owner and expiry\n"
            "  - change locality or deletion-path review"
        )
    if not blocks:
        return ""
    return "\n\nProvide stronger structure evidence:\n" + "\n".join(blocks)


def _final_text(event: dict) -> str:
    for key in (
        "final_response",
        "finalResponse",
        "assistant_response",
        "assistantResponse",
        "response",
        "message",
        "output",
        "last_assistant_message",
        "lastAssistantMessage",
    ):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def _missing_keyword_groups(
    text: str,
    state: dict,
    manifest: dict | None = None,
) -> list[str]:
    lowered = text.casefold()
    missing: list[str] = []
    parsed_manifest = manifest if manifest is not None else extract_manifest_fields(text)
    if not parsed_manifest.get("route_present"):
        missing.append("route_manifest")
    for group, keywords in CLOSURE_KEYWORDS.items():
        if group == "validation":
            if not _has_validation_evidence(text, state):
                missing.append(group)
            continue
        if not any(keyword.casefold() in lowered for keyword in keywords):
            missing.append(group)
    for state_key, group in CONDITIONAL_GROUP_BY_STATE.items():
        if not state.get(state_key):
            continue
        keywords = CONDITIONAL_KEYWORDS[group]
        if not any(keyword.casefold() in lowered for keyword in keywords) and group not in missing:
            missing.append(group)
    if _unverified_completion(text, state) and "completion_evidence" not in missing:
        missing.append("completion_evidence")
    return missing


def _unverified_completion(text: str, state: dict) -> bool:
    """Presence check: completion language with no validation evidence.

    This never judges whether the claim is true. It notices a completion claim
    in the final handoff and pairs it with the absence of any validation signal,
    so the closure reminder can ask for evidence or a not-verified disclosure.
    The Stop gate stays presence-only and fails open.
    """
    if not text:
        return False
    lowered = text.casefold()
    has_completion = any(phrase.casefold() in lowered for phrase in COMPLETION_LANGUAGE)
    if not has_completion:
        return False
    return not _has_validation_evidence(text, state)


def _has_validation_evidence(text: str, state: dict) -> bool:
    """Return true only for strong validation evidence in the closure text.

    A command-like string in hook state means a validation command was observed,
    not that it succeeded. The final handoff still needs an outcome, exit code,
    output, or artifact signal. Negative validation disclosures explicitly block
    this from being counted as evidence.
    """
    if not text:
        return False
    lowered = text.casefold()
    if _has_negative_validation_phrase(lowered):
        return False
    command_seen = bool(state.get("validation_command_seen") or state.get("validation_seen"))
    command_in_text = bool(VALIDATION_COMMAND_RE.search(text))
    outcome_in_text = bool(VALIDATION_OUTCOME_RE.search(text))
    artifact_in_text = bool(VALIDATION_ARTIFACT_RE.search(text))
    if outcome_in_text and (command_seen or command_in_text or artifact_in_text):
        return True
    if command_in_text and artifact_in_text:
        return True
    return False


def _has_negative_validation_phrase(lowered_text: str) -> bool:
    return any(phrase.casefold() in lowered_text for phrase in NEGATIVE_VALIDATION_PHRASES)


if __name__ == "__main__":
    raise SystemExit(main())
