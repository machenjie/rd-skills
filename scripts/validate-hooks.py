#!/usr/bin/env python3
"""Validate ChangeForge hook runtime source and templates."""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import sys
from pathlib import Path
from typing import Any

from validation_utils import fail_many, load_yaml_file, relpath


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
HOOK_RUNTIME_ROOT = ROOT / "src" / "hook-runtime"
HOOK_SCRIPTS_DIR = HOOK_RUNTIME_ROOT / "scripts"
HOOK_SCHEMAS_DIR = HOOK_RUNTIME_ROOT / "schemas"
CODEX_TEMPLATE = HOOK_RUNTIME_ROOT / "templates" / "codex" / "hooks.json"
CODEX_USER_TEMPLATE = HOOK_RUNTIME_ROOT / "templates" / "codex-user" / "hooks.json"
CLAUDE_TEMPLATE = (
    HOOK_RUNTIME_ROOT
    / "templates"
    / "claude"
    / "settings.changeforge-hooks.fragment.json"
)
CLAUDE_USER_TEMPLATE = (
    HOOK_RUNTIME_ROOT
    / "templates"
    / "claude-user"
    / "settings.changeforge-hooks.fragment.json"
)
# Codex and Claude each ship a project template and a user-scope template. The
# user templates are identical in shape but resolve their command path from the
# agent home (CODEX_HOME/CLAUDE_CONFIG_DIR) instead of the project git root.
CODEX_TEMPLATES = (CODEX_TEMPLATE, CODEX_USER_TEMPLATE)
CLAUDE_TEMPLATES = (CLAUDE_TEMPLATE, CLAUDE_USER_TEMPLATE)
# VS Code Copilot uses the flat (matcher-less) hook config format. Project
# commands resolve from the git root; user commands resolve from $HOME/.copilot.
COPILOT_TEMPLATE = HOOK_RUNTIME_ROOT / "templates" / "copilot" / "changeforge-hooks.json"
COPILOT_USER_TEMPLATE = (
    HOOK_RUNTIME_ROOT / "templates" / "copilot-user" / "changeforge-hooks.json"
)
COPILOT_TEMPLATES = (COPILOT_TEMPLATE, COPILOT_USER_TEMPLATE)
HOOK_TEMPLATE_DIST_DIRS = {
    CODEX_TEMPLATE: DIST_DIR / "codex" / "project" / ".codex" / "hooks",
    CODEX_USER_TEMPLATE: DIST_DIR / "codex" / "user" / ".codex" / "hooks",
    CLAUDE_TEMPLATE: DIST_DIR / "claude" / "project" / ".claude" / "hooks",
    CLAUDE_USER_TEMPLATE: DIST_DIR / "claude" / "user" / ".claude" / "hooks",
    COPILOT_TEMPLATE: DIST_DIR / "copilot" / "project" / ".github" / "hooks" / "changeforge",
    COPILOT_USER_TEMPLATE: DIST_DIR / "copilot" / "user" / ".copilot" / "hooks" / "changeforge",
}
HOOKS_DOC = ROOT / "docs" / "HOOKS.md"
RICH_EVENT_SCRIPTS = {
    "SessionStart": (
        "changeforge_session_bootstrap",
        "changeforge_professional_injector",
        "changeforge_compaction_snapshot",
        "changeforge_compaction_reinject",
    ),
    "UserPromptSubmit": (
        "changeforge_user_prompt_route_reminder",
        "changeforge_professional_injector",
        "changeforge_sdd_material_choice_gate",
        "changeforge_review_gate",
    ),
    "PreToolUse": (
        "changeforge_professional_injector",
        "changeforge_sdd_material_choice_gate",
        "changeforge_pre_edit_structure_gate",
        "changeforge_pre_tool_risk_preview",
        "changeforge_permission_policy_gate",
    ),
    "PermissionRequest": ("changeforge_permission_policy_gate",),
    "PostToolUse": (
        "changeforge_professional_injector",
        "changeforge_read_context_gate",
        "changeforge_tool_output_boundary_gate",
        "changeforge_review_gate",
        "changeforge_post_edit_structure_gate",
        "changeforge_risk_surface_gate",
    ),
    "SubagentStart": (
        "changeforge_session_bootstrap",
        "changeforge_professional_injector",
        "changeforge_subagent_skill_contract",
    ),
    "SubagentStop": ("changeforge_subagent_stop_reminder",),
    "Stop": ("changeforge_sdd_material_choice_gate", "changeforge_stop_closure_gate"),
}
# Copilot event -> the hook script(s) each event must invoke.
COPILOT_EVENT_SCRIPTS = {
    "SessionStart": (
        "changeforge_session_bootstrap",
        "changeforge_professional_injector",
        "changeforge_compaction_snapshot",
        "changeforge_compaction_reinject",
    ),
    "PostToolUse": (
        "changeforge_professional_injector",
        "changeforge_read_context_gate",
        "changeforge_tool_output_boundary_gate",
        "changeforge_review_gate",
        "changeforge_post_edit_structure_gate",
        "changeforge_risk_surface_gate",
    ),
    "SubagentStart": (
        "changeforge_session_bootstrap",
        "changeforge_professional_injector",
        "changeforge_subagent_skill_contract",
    ),
    "Stop": ("changeforge_stop_closure_gate",),
}
BOOTSTRAP_TEMPLATE = (
    HOOK_RUNTIME_ROOT / "templates" / "bootstrap" / "changeforge-route-preflight.md"
)
PROFESSIONAL_BOOTSTRAP_TEMPLATE = (
    HOOK_RUNTIME_ROOT / "templates" / "bootstrap" / "changeforge-professional-contract.md"
)
COPILOT_SKILL_SUMMARY = HOOK_SCRIPTS_DIR / "changeforge_copilot_skill_summary.md"
PROFESSIONAL_CONTRACT = HOOK_SCRIPTS_DIR / "changeforge_professional_contract.md"
COPILOT_PROFESSIONAL_CONTRACT = (
    HOOK_SCRIPTS_DIR / "changeforge_copilot_professional_contract.md"
)
REQUIRED_HOOK_SCRIPTS = (
    "changeforge_common.py",
    "changeforge_adapter_capabilities.py",
    "changeforge_runtime_adapters.py",
    "changeforge_hook_policy.py",
    "changeforge_state_reducer.py",
    "changeforge_compaction_contract.py",
    "changeforge_normalized_event.py",
    "changeforge_lifecycle_state.py",
    "changeforge_evidence_ledger.py",
    "changeforge_gate_result.py",
    "changeforge_closure_contract.py",
    "changeforge_executor_adapter_core.py",
    "changeforge_action_classifier.py",
    "changeforge_context_control_policy.py",
    "changeforge_tool_output_boundary.py",
    "changeforge_branch_route_summary.py",
    "changeforge_runtime_route_resolver.py",
    "changeforge_skill_index.py",
    "changeforge_session_bootstrap.py",
    "changeforge_user_prompt_route_reminder.py",
    "changeforge_sdd_material_choice_gate.py",
    "changeforge_pre_edit_structure_gate.py",
    "changeforge_pre_tool_risk_preview.py",
    "changeforge_professional_injector.py",
    "changeforge_read_context_gate.py",
    "changeforge_tool_output_boundary_gate.py",
    "changeforge_review_gate.py",
    "changeforge_permission_policy_gate.py",
    "changeforge_compaction_snapshot.py",
    "changeforge_compaction_reinject.py",
    "changeforge_subagent_skill_contract.py",
    "changeforge_post_edit_structure_gate.py",
    "changeforge_risk_surface_gate.py",
    "changeforge_subagent_stop_reminder.py",
    "changeforge_stop_closure_gate.py",
)
NETWORK_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|urllib|urllib3|socket)\b",
    re.MULTILINE,
)
USER_ABSOLUTE_PATH_RE = re.compile(
    r"(/home/[^ \"]+|/Users/[^ \"]+|/mnt/[a-zA-Z]/Users/[^ \"]+|[A-Za-z]:\\\\Users\\\\)"
)
PROJECT_SOURCE_WRITE_RE = re.compile(
    r"(repo\s*/|cwd\s*/|project\s*/|source\s*/).*(write_text|write_bytes|open\()"
)
GIT_MUTATION_RE = re.compile(
    r"git\s+(commit|checkout|reset|push|rebase|cherry-pick|clean|stash)\b"
)
HOOK_SCRIPT_REFERENCE_RE = re.compile(r"\b(changeforge_[A-Za-z0-9_]+\.py)\b")
STATE_FINDING_FIELDS = (
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
    "post_edit_structure_findings",
)
ADAPTER_SNAPSHOT_SCRIPTS = (
    "changeforge_pre_edit_structure_gate.py",
    "changeforge_sdd_material_choice_gate.py",
    "changeforge_post_edit_structure_gate.py",
    "changeforge_permission_policy_gate.py",
    "changeforge_tool_output_boundary_gate.py",
    "changeforge_risk_surface_gate.py",
    "changeforge_read_context_gate.py",
    "changeforge_review_gate.py",
    "changeforge_compaction_snapshot.py",
    "changeforge_stop_closure_gate.py",
)
SESSION_COMPACTION_ORDER = (
    "changeforge_compaction_snapshot",
    "changeforge_session_bootstrap",
    "changeforge_compaction_reinject",
    "changeforge_professional_injector",
)
READ_MATCHER_TOKENS = (
    "Fetch",
    "fetch_pr_patch",
    "get_pr_diff",
    "mcp__filesystem__read_file",
    "mcp__filesystem__list_directory",
    "mcp__github__get_file_contents",
    "mcp__github__pull_request_read",
    "mcp__github__search_code",
    "mcpfilesystemreadfile",
    "mcpfilesystemlistdirectory",
    "mcpgithubgetfilecontents",
    "mcpgithubpullrequestread",
    "mcpgithubsearchcode",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", help="Optional JSON validation report output path.")
    parser.add_argument("--out", help="Optional Markdown validation report output path.")
    args = parser.parse_args(argv)

    errors: list[str] = []

    _validate_required_files(errors)
    _validate_python_files(errors)
    _validate_adapter_capabilities(errors)
    _validate_docs_capability_matrix(errors)
    _validate_schema_files(errors)
    _validate_bootstrap_fragment(errors)
    codex = _load_json(CODEX_TEMPLATE, errors)
    codex_user = _load_json(CODEX_USER_TEMPLATE, errors)
    claude = _load_json(CLAUDE_TEMPLATE, errors)
    claude_user = _load_json(CLAUDE_USER_TEMPLATE, errors)
    copilot = _load_json(COPILOT_TEMPLATE, errors)
    copilot_user = _load_json(COPILOT_USER_TEMPLATE, errors)
    if isinstance(codex, dict):
        _validate_template(codex, CODEX_TEMPLATE, timeout_limit=10, errors=errors)
    if isinstance(codex_user, dict):
        _validate_template(codex_user, CODEX_USER_TEMPLATE, timeout_limit=10, errors=errors)
    if isinstance(claude, dict):
        _validate_template(claude, CLAUDE_TEMPLATE, timeout_limit=10, errors=errors)
    if isinstance(claude_user, dict):
        _validate_template(claude_user, CLAUDE_USER_TEMPLATE, timeout_limit=10, errors=errors)
    if isinstance(copilot, dict):
        _validate_copilot_template(copilot, COPILOT_TEMPLATE, errors=errors)
    if isinstance(copilot_user, dict):
        _validate_copilot_template(copilot_user, COPILOT_USER_TEMPLATE, errors=errors)
    for template_path, template_data in (
        (CODEX_TEMPLATE, codex),
        (CODEX_USER_TEMPLATE, codex_user),
        (CLAUDE_TEMPLATE, claude),
        (CLAUDE_USER_TEMPLATE, claude_user),
        (COPILOT_TEMPLATE, copilot),
        (COPILOT_USER_TEMPLATE, copilot_user),
    ):
        if isinstance(template_data, dict):
            _validate_template_script_references(template_data, template_path, errors)
    _validate_hook_behavior(errors)
    _validate_runtime_route_resolver(errors)

    capabilities = None
    if not errors:
        capabilities = _load_adapter_capabilities(errors)
    report = _validation_report(errors)
    _write_validation_report(report, json_out=args.json_out, markdown_out=args.out)
    if errors:
        return fail_many("validate-hooks", errors)
    if capabilities is not None:
        print(capabilities.format_coverage_matrix())
    print("validate-hooks: validated hook runtime scripts and templates.")
    return 0


def _validation_report(errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_by": "scripts/validate-hooks.py",
        "status": "fail" if errors else "pass",
        "errors": errors,
        "summary": {
            "hook_runtime_root": "src/hook-runtime",
            "required_hook_scripts": len(REQUIRED_HOOK_SCRIPTS),
            "codex_templates": len(CODEX_TEMPLATES),
            "claude_templates": len(CLAUDE_TEMPLATES),
            "copilot_templates": len(COPILOT_TEMPLATES),
            "required_hook_scripts_present": HOOK_SCRIPTS_DIR.is_dir()
            and all((HOOK_SCRIPTS_DIR / file_name).is_file() for file_name in REQUIRED_HOOK_SCRIPTS),
            "error_count": len(errors),
        },
    }


def _write_validation_report(
    report: dict[str, Any],
    *,
    json_out: str | None,
    markdown_out: str | None,
) -> None:
    if json_out:
        path = Path(json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if markdown_out:
        path = Path(markdown_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render_validation_report("Hook Validation", report), encoding="utf-8")


def _render_validation_report(title: str, report: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated by: `{report['generated_by']}`",
        f"- Error count: `{len(report['errors'])}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Errors", ""])
    if report["errors"]:
        lines.extend(f"- {error}" for error in report["errors"])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def _validate_required_files(errors: list[str]) -> None:
    if not HOOK_SCRIPTS_DIR.is_dir():
        errors.append("missing hook script directory: src/hook-runtime/scripts")
        return
    for file_name in REQUIRED_HOOK_SCRIPTS:
        path = HOOK_SCRIPTS_DIR / file_name
        if not path.is_file():
            errors.append(f"missing hook script: {relpath(ROOT, path)}")
    if not COPILOT_SKILL_SUMMARY.is_file():
        errors.append(f"missing Copilot hook support file: {relpath(ROOT, COPILOT_SKILL_SUMMARY)}")
    if not PROFESSIONAL_CONTRACT.is_file():
        errors.append(f"missing hook support file: {relpath(ROOT, PROFESSIONAL_CONTRACT)}")
    if not COPILOT_PROFESSIONAL_CONTRACT.is_file():
        errors.append(
            f"missing Copilot hook support file: {relpath(ROOT, COPILOT_PROFESSIONAL_CONTRACT)}"
        )
    for path in (
        CODEX_TEMPLATE,
        CODEX_USER_TEMPLATE,
        CLAUDE_TEMPLATE,
        CLAUDE_USER_TEMPLATE,
        COPILOT_TEMPLATE,
        COPILOT_USER_TEMPLATE,
    ):
        if not path.is_file():
            errors.append(f"missing hook template: {relpath(ROOT, path)}")


def _load_adapter_capabilities(errors: list[str]) -> Any:
    sys.path.insert(0, str(HOOK_SCRIPTS_DIR))
    try:
        import changeforge_adapter_capabilities as capabilities
    except Exception as exc:
        errors.append(f"adapter capabilities import failed: {exc}")
        return None
    finally:
        try:
            sys.path.remove(str(HOOK_SCRIPTS_DIR))
        except ValueError:
            pass
    return capabilities


def _validate_adapter_capabilities(errors: list[str]) -> None:
    capabilities = _load_adapter_capabilities(errors)
    if capabilities is None:
        return
    if not hasattr(capabilities, "runtime_adapter_for"):
        errors.append("adapter capabilities: runtime_adapter_for factory is required")
        return
    canonical_events = tuple(capabilities.CANONICAL_EVENTS)
    expected_visibility = {"none", "partial", "full"}
    for runtime in (
        "codex",
        "claude",
        "copilot",
        "generic",
        "cline",
        "roo",
        "openhands",
        "gemini-cli",
        "goose",
    ):
        adapter = capabilities.adapter_capabilities_for(runtime)
        if adapter.runtime != runtime:
            errors.append(f"adapter capabilities: {runtime} returned {adapter.runtime}")
        data = adapter.to_dict()
        for field in (
            "supports_session_start",
            "supports_user_prompt_submit",
            "supports_pre_tool_use",
            "supports_post_tool_use",
            "supports_stop",
            "supports_subagent_start",
            "supports_subagent_stop",
            "supports_permission_decision",
            "supports_blocking",
            "supports_context_injection",
            "supports_tool_result_inspection",
            "supports_pre_tool_block",
            "supports_post_tool_success",
            "supports_post_tool_failure",
            "supports_tool_batch",
            "supports_file_changed_event",
            "supports_config_changed_event",
            "supports_worktree_lifecycle",
            "supports_pre_compact",
            "supports_post_compact",
            "supports_session_end",
            "supports_task_lifecycle",
            "supports_checkpoint_or_rollback",
            "supports_plan_act_mode",
            "supports_codebase_index",
            "supports_mode_or_role_switch",
        ):
            if not isinstance(data.get(field), bool):
                errors.append(f"adapter capabilities: {runtime}.{field} must be boolean")
        for field in (
            "command_output_visibility",
            "changed_path_visibility",
            "validation_output_visibility",
            "read_path_visibility",
            "command_kind_visibility",
            "command_risk_visibility",
            "permission_decision_visibility",
            "rollback_checkpoint_visibility",
        ):
            if data.get(field) not in expected_visibility:
                errors.append(
                    f"adapter capabilities: {runtime}.{field} must be one of {sorted(expected_visibility)}"
                )
        visibility = data.get("visibility")
        if not isinstance(visibility, dict):
            errors.append(f"adapter capabilities: {runtime}.visibility must be a dict")
        else:
            for field in capabilities.VISIBILITY_FIELDS:
                if visibility.get(field) not in expected_visibility:
                    errors.append(
                        f"adapter capabilities: {runtime}.visibility.{field} must be one of {sorted(expected_visibility)}"
                    )
        if data.get("default_failure_mode") != "fail_open":
            errors.append(f"adapter capabilities: {runtime} must default to fail_open")
        if not data.get("fail_open_policy"):
            errors.append(f"adapter capabilities: {runtime}.fail_open_policy is required")
        if not isinstance(data.get("unsupported_events"), list):
            errors.append(f"adapter capabilities: {runtime}.unsupported_events must be a list")
        for field in (
            "supported_events",
            "observable_payload_fields",
            "advisory_context_events",
            "supported_checks",
            "unsupported_checks",
            "degraded_checks",
            "fail_closed_allowed_checks",
            "notes",
        ):
            if not isinstance(data.get(field), list):
                errors.append(f"adapter capabilities: {runtime}.{field} must be a list")
        if not isinstance(data.get("default_gate_modes"), dict):
            errors.append(f"adapter capabilities: {runtime}.default_gate_modes must be a dict")
        if not data.get("degradation_policy"):
            errors.append(f"adapter capabilities: {runtime}.degradation_policy is required")
        supported_events = set(data.get("supported_events") or [])
        unsupported_events = set(data.get("unsupported_events") or [])
        translator = capabilities.runtime_adapter_for(runtime)
        if translator.capabilities.runtime != adapter.runtime:
            errors.append(
                f"adapter factory: {runtime} returned {translator.capabilities.runtime}"
            )
        if runtime in {"codex", "claude", "copilot", "cline", "roo", "openhands"}:
            expected_class = f"{runtime.title()}Adapter"
            if runtime == "openhands":
                expected_class = "OpenHandsAdapter"
            if translator.__class__.__name__ != expected_class:
                errors.append(
                    f"adapter factory: {runtime} must return {expected_class}, got {translator.__class__.__name__}"
                )
        for event in canonical_events[:-1]:
            if event not in supported_events and event not in unsupported_events:
                errors.append(
                    f"adapter capabilities: {runtime} must explicitly mark {event} unsupported"
                )
        if runtime == "generic" and data.get("command_output_visibility") != "none":
            errors.append("adapter capabilities: generic command output visibility must be none")
        if runtime in {"gemini-cli", "goose"}:
            if not data.get("placeholder"):
                errors.append(f"adapter capabilities: {runtime} must be a placeholder")
            if data.get("supported_events"):
                errors.append(f"adapter capabilities: {runtime} must not claim supported events")
            missing = [event for event in canonical_events[:-1] if event not in unsupported_events]
            if missing:
                errors.append(
                    f"adapter capabilities: {runtime} placeholder must mark all events unsupported: {missing}"
                )
        if runtime in {"cline", "roo"}:
            if data.get("placeholder"):
                errors.append(f"adapter capabilities: {runtime} must be a staged adapter, not a placeholder")
            if data.get("supported_events"):
                errors.append(f"adapter capabilities: {runtime} must not claim hook lifecycle events")
            if data.get("stop_block_supported"):
                errors.append(f"adapter capabilities: {runtime} must not claim stop blocking")
            if not data.get("supports_mode_or_role_switch"):
                errors.append(f"adapter capabilities: {runtime} must expose mode or role switch support")
            if data.get("fail_closed_allowed_checks"):
                errors.append(f"adapter capabilities: {runtime} must not allow fail_closed checks")
        if runtime == "cline" and not data.get("supports_plan_act_mode"):
            errors.append("adapter capabilities: cline must expose Plan/Act mode support")
        if runtime == "openhands":
            if data.get("placeholder"):
                errors.append("adapter capabilities: openhands must be a backend-protocol adapter")
            for event in ("PostToolUse", "PostToolUseFailure", "FileChanged", "TaskCreated", "TaskCompleted"):
                if event not in supported_events:
                    errors.append(f"adapter capabilities: OpenHands must support {event}")
            for event in ("PreToolUse", "PermissionRequest", "SubagentStart", "SubagentStop"):
                if event not in unsupported_events:
                    errors.append(f"adapter capabilities: OpenHands must mark {event} unsupported")
            if data.get("command_output_visibility") == "full":
                errors.append("adapter capabilities: OpenHands must not claim full command output visibility")
    copilot = capabilities.adapter_capabilities_for("copilot")
    for event in ("UserPromptSubmit", "PreToolUse", "SubagentStop"):
        if event not in copilot.unsupported_events:
            errors.append(f"adapter capabilities: Copilot must mark {event} unsupported")
        if copilot.supports_event(event):
            errors.append(f"adapter capabilities: Copilot must not support {event}")
    for check in ("pre_tool_advisory_context", "user_prompt_advisory_context", "subagent_stop_context"):
        if check not in copilot.unsupported_checks:
            errors.append(f"adapter capabilities: Copilot must mark {check} unsupported")
    claude = capabilities.adapter_capabilities_for("claude")
    for event in (
        "PostToolUseFailure",
        "StopFailure",
        "SessionEnd",
        "TaskCreated",
        "TaskCompleted",
        "FileChanged",
        "ConfigChanged",
        "PreCompact",
        "PostCompact",
    ):
        if not claude.supports_event(event):
            errors.append(f"adapter capabilities: Claude must support {event}")


def _validate_docs_capability_matrix(errors: list[str]) -> None:
    capabilities = _load_adapter_capabilities(errors)
    if capabilities is None:
        return
    if not HOOKS_DOC.is_file():
        errors.append(f"missing hooks documentation: {relpath(ROOT, HOOKS_DOC)}")
        return
    actual = capabilities.docs_capability_matrix_from_text(HOOKS_DOC.read_text(encoding="utf-8"))
    expected = capabilities.format_docs_capability_matrix().strip()
    if not actual:
        errors.append(
            f"{relpath(ROOT, HOOKS_DOC)}: missing adapter capability matrix markers"
        )
    elif actual != expected:
        errors.append(
            f"{relpath(ROOT, HOOKS_DOC)}: adapter capability matrix is stale; regenerate from runtime_governance.adapters.base.format_docs_capability_matrix()"
        )


def _copilot_unsupported_advisory_events(errors: list[str]) -> tuple[str, ...]:
    capabilities = _load_adapter_capabilities(errors)
    if capabilities is None:
        return ()
    return tuple(capabilities.unsupported_events_for("copilot"))


def _validate_schema_files(errors: list[str]) -> None:
    if not HOOK_SCHEMAS_DIR.is_dir():
        errors.append("missing hook schema directory: src/hook-runtime/schemas")
        return
    for path in sorted(HOOK_SCHEMAS_DIR.glob("*.json")):
        _load_json(path, errors)


def _validate_python_files(errors: list[str]) -> None:
    if not HOOK_SCRIPTS_DIR.is_dir():
        return
    for path in sorted(HOOK_SCRIPTS_DIR.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{relpath(ROOT, path)}: py_compile failed: {exc.msg}")
        text = path.read_text(encoding="utf-8")
        if NETWORK_IMPORT_RE.search(text):
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not make network requests")
        if "requests." in text or "httpx." in text or "urllib." in text:
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not make network requests")
        if "shutil.rmtree" in text or ".unlink(" in text or ".rename(" in text:
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not modify project source")
        if PROJECT_SOURCE_WRITE_RE.search(text):
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not write project source")
        if GIT_MUTATION_RE.search(text):
            errors.append(
                f"{relpath(ROOT, path)}: hook scripts must not run mutating git commands"
            )

    stop_script = HOOK_SCRIPTS_DIR / "changeforge_stop_closure_gate.py"
    if stop_script.is_file():
        text = stop_script.read_text(encoding="utf-8")
        if "emit_warning(" in text:
            errors.append("changeforge_stop_closure_gate.py: Stop hook must not use emit_warning")
        if "emit_stop_reminder(" not in text:
            errors.append("changeforge_stop_closure_gate.py: Stop hook must use emit_stop_reminder")
        if "transcript_path" not in text or "transcriptPath" not in text:
            errors.append(
                "changeforge_stop_closure_gate.py: Stop hook must read Copilot transcript paths"
            )

    bootstrap_script = HOOK_SCRIPTS_DIR / "changeforge_session_bootstrap.py"
    if bootstrap_script.is_file():
        bootstrap_text = bootstrap_script.read_text(encoding="utf-8")
        if "is_session_start(" not in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must gate on is_session_start"
            )
        if "emit_session_context(" not in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must use emit_session_context"
            )
        if "emit_stop_reminder(" in bootstrap_text or "emit_block(" in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must not block or emit a stop reminder"
            )
        if '"decision"' in bootstrap_text or "'decision'" in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must not emit a block decision"
            )
        if "changeforge_copilot_skill_summary.md" not in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: Copilot bootstrap must load the skill summary"
            )

    # The context-injecting and reminder hooks are advisory only. They add
    # developer context or a systemMessage and must never deny a tool call or
    # force continuation through a block decision.
    advisory_scripts = (
        "changeforge_user_prompt_route_reminder.py",
        "changeforge_pre_tool_risk_preview.py",
        "changeforge_subagent_stop_reminder.py",
    )
    for script_name in advisory_scripts:
        advisory_path = HOOK_SCRIPTS_DIR / script_name
        if not advisory_path.is_file():
            continue
        advisory_text = advisory_path.read_text(encoding="utf-8")
        if "emit_block(" in advisory_text or "emit_stop_reminder(" in advisory_text:
            errors.append(f"{script_name}: advisory hook must not block or emit a stop reminder")
        if '"decision"' in advisory_text or "permissionDecision" in advisory_text:
            errors.append(f"{script_name}: advisory hook must not emit a block or deny decision")

    structure_script = HOOK_SCRIPTS_DIR / "changeforge_post_edit_structure_gate.py"
    if structure_script.is_file():
        structure_text = structure_script.read_text(encoding="utf-8")
        for field in STATE_FINDING_FIELDS:
            if field not in structure_text:
                errors.append(
                    f"changeforge_post_edit_structure_gate.py: structure gate must populate {field}"
                )
        if "post_edit_confirmed_preflight_gap" not in structure_text:
            errors.append(
                "changeforge_post_edit_structure_gate.py: must record post-edit preflight gaps"
            )
        if "post_edit_structure_findings" not in structure_text:
            errors.append(
                "changeforge_post_edit_structure_gate.py: must record post_edit_structure_findings"
            )

    for script_name in ADAPTER_SNAPSHOT_SCRIPTS:
        path = HOOK_SCRIPTS_DIR / script_name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "snapshot_from_event_state" not in text:
            errors.append(f"{script_name}: must use shared adapter snapshot creation")
        if script_name != "changeforge_stop_closure_gate.py" and "state_update_from_snapshot" not in text:
            errors.append(f"{script_name}: must persist bounded adapter snapshot state")

    pre_edit_script = HOOK_SCRIPTS_DIR / "changeforge_pre_edit_structure_gate.py"
    if pre_edit_script.is_file():
        pre_edit_text = pre_edit_script.read_text(encoding="utf-8")
        for token in (
            "implementation_preflight_required",
            "pre_edit_missing_read_evidence",
            "pre_edit_missing_reuse_decision",
            "pre_edit_missing_placement_decision",
            "pre_edit_missing_test_plan",
            "extract_implementation_preflight_fields",
            "should_block",
        ):
            if token not in pre_edit_text:
                errors.append(f"changeforge_pre_edit_structure_gate.py: missing {token}")
        forbidden_tokens = ("requests.", "httpx.", "urllib.", "subprocess.run")
        for token in forbidden_tokens:
            if token in pre_edit_text:
                errors.append(
                    f"changeforge_pre_edit_structure_gate.py: forbidden operation token {token!r}"
                )
        if "prompt_signals" in pre_edit_text or "prompt_text" in pre_edit_text:
            errors.append("changeforge_pre_edit_structure_gate.py: must not write raw prompt state")

    common_script = HOOK_SCRIPTS_DIR / "changeforge_common.py"
    if common_script.is_file():
        common_text = common_script.read_text(encoding="utf-8")
        if "reduce_state_update" not in common_text:
            errors.append("changeforge_common.py: merge_state must use changeforge_state_reducer")
        if "extract_implementation_preflight_fields" not in common_text:
            errors.append("changeforge_common.py: must parse implementation preflight manifests")
        if "hookSpecificOutput" not in common_text or "additionalContext" not in common_text:
            errors.append(
                "changeforge_common.py: Codex and Claude warnings must use hookSpecificOutput.additionalContext"
            )
        if '"additionalContext": text' not in common_text:
            errors.append(
                "changeforge_common.py: Copilot context hooks must emit top-level additionalContext"
            )
        if '"decision": "block"' not in common_text or '"reason": text' not in common_text:
            errors.append(
                "changeforge_common.py: Copilot Stop blocks must emit top-level decision/reason"
            )
        if "CHANGEFORGE_AGENT" not in common_text:
            errors.append("changeforge_common.py: detect_runtime must support CHANGEFORGE_AGENT override")
        if "def is_session_start(" not in common_text:
            errors.append("changeforge_common.py: must define is_session_start for the bootstrap")
        if "def emit_session_context(" not in common_text:
            errors.append("changeforge_common.py: must define emit_session_context for the bootstrap")
        for field in STATE_FINDING_FIELDS:
            if field not in common_text:
                errors.append(
                    f"changeforge_common.py: hook state must track {field}"
                )
        for field in (
            "runtime_adapter",
            "normalized_events",
            "deleted_paths",
            "generated_paths",
            "external_file_changes",
            "config_changes",
            "validation_results",
            "repair_events",
            "rereview_events",
            "command_risks",
            "rollback_points",
            "context_control_records",
            "tool_output_boundaries",
            "artifact_references",
            "context_budget_findings",
            "skipped_references",
        ):
            if f'"{field}"' not in common_text:
                errors.append(f"changeforge_common.py: hook state must track {field}")


def _validate_bootstrap_fragment(errors: list[str]) -> None:
    if not BOOTSTRAP_TEMPLATE.is_file():
        errors.append(f"missing bootstrap fragment: {relpath(ROOT, BOOTSTRAP_TEMPLATE)}")
        return
    text = BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
    if USER_ABSOLUTE_PATH_RE.search(text):
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must not contain a user absolute path"
        )
    if "change-forge-router" not in text:
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must point to change-forge-router"
        )
    if "implementation-structure-design" not in text:
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must reference implementation-structure-design"
        )
    if "agent-execution-discipline" not in text:
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must reference agent-execution-discipline"
        )
    if not PROFESSIONAL_BOOTSTRAP_TEMPLATE.is_file():
        errors.append(
            f"missing professional bootstrap fragment: {relpath(ROOT, PROFESSIONAL_BOOTSTRAP_TEMPLATE)}"
        )
    else:
        professional = PROFESSIONAL_BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
        if USER_ABSOLUTE_PATH_RE.search(professional):
            errors.append(
                f"{relpath(ROOT, PROFESSIONAL_BOOTSTRAP_TEMPLATE)}: professional bootstrap must not contain a user absolute path"
            )
        for required in ("owner skill", "reviewer skill", "prompt-free", "validation evidence"):
            if required not in professional:
                errors.append(
                    f"{relpath(ROOT, PROFESSIONAL_BOOTSTRAP_TEMPLATE)}: professional bootstrap must reference {required}"
                )
    for support_path in (PROFESSIONAL_CONTRACT, COPILOT_PROFESSIONAL_CONTRACT):
        if not support_path.is_file():
            continue
        support = support_path.read_text(encoding="utf-8")
        if USER_ABSOLUTE_PATH_RE.search(support):
            errors.append(
                f"{relpath(ROOT, support_path)}: support file must not contain a user absolute path"
            )
        for required in ("prompt", "validation evidence", "residual risk"):
            if required not in support:
                errors.append(
                    f"{relpath(ROOT, support_path)}: support file must reference {required}"
                )
    if COPILOT_SKILL_SUMMARY.is_file():
        summary = COPILOT_SKILL_SUMMARY.read_text(encoding="utf-8")
        if USER_ABSOLUTE_PATH_RE.search(summary):
            errors.append(
                f"{relpath(ROOT, COPILOT_SKILL_SUMMARY)}: support file must not contain a user absolute path"
            )
        for required in ("change-forge-router", "quality-test-gate", "security-privacy-gate"):
            if required not in summary:
                errors.append(
                    f"{relpath(ROOT, COPILOT_SKILL_SUMMARY)}: support file must reference {required}"
                )


def _load_json(path: Path, errors: list[str]) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{relpath(ROOT, path)}: invalid JSON: {exc}")
        return None


def _validate_template(
    data: dict[str, Any],
    path: Path,
    *,
    timeout_limit: int,
    errors: list[str],
) -> None:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        errors.append(f"{relpath(ROOT, path)}: hooks must be a JSON object")
        return
    capabilities_module = _load_adapter_capabilities(errors)
    if capabilities_module is not None and (path in CODEX_TEMPLATES or path in CLAUDE_TEMPLATES):
        runtime = "codex" if path in CODEX_TEMPLATES else "claude"
        capabilities = capabilities_module.adapter_capabilities_for(runtime)
        for event in hooks:
            if not capabilities.supports_event(event):
                errors.append(
                    f"{relpath(ROOT, path)}: {runtime} template wires unsupported event {event}"
                )
    for required_event in ("PostToolUse", "Stop"):
        if required_event not in hooks:
            errors.append(f"{relpath(ROOT, path)}: missing {required_event} hook")

    # Both templates wire the route-preflight bootstrap as a SessionStart hook.
    # Codex now exposes SessionStart (including the post-compaction compact
    # source), so it no longer relies only on the install-time fragment.
    session_start = hooks.get("SessionStart")
    if not isinstance(session_start, list) or not session_start:
        errors.append(
            f"{relpath(ROOT, path)}: template must wire a SessionStart bootstrap hook"
        )
    elif not any(
        "changeforge_session_bootstrap" in command
        for command, _context in _commands({"SessionStart": session_start})
    ):
        errors.append(
            f"{relpath(ROOT, path)}: SessionStart must invoke changeforge_session_bootstrap"
        )
    else:
        _validate_event_script_order(
            hooks,
            "SessionStart",
            SESSION_COMPACTION_ORDER,
            path,
            errors,
        )

    # Codex and Claude expose the lifecycle events the runtime uses to reinforce
    # routing and closure discipline. Require each one to invoke its dedicated
    # hook script.
    if path in CODEX_TEMPLATES or path in CLAUDE_TEMPLATES:
        agent_name = "Codex" if path in CODEX_TEMPLATES else "Claude"
        for event, scripts in RICH_EVENT_SCRIPTS.items():
            if event == "Stop":
                continue
            for script in scripts:
                if not _event_invokes(hooks, event, script):
                    errors.append(
                        f"{relpath(ROOT, path)}: {agent_name} {event} must invoke {script}"
                    )
        _validate_event_script_order(
            hooks,
            "PreToolUse",
            RICH_EVENT_SCRIPTS["PreToolUse"],
            path,
            errors,
        )
        if path in CLAUDE_TEMPLATES and not _event_invokes(
            hooks, "PostToolBatch", "changeforge_read_context_gate"
        ):
            errors.append(
                f"{relpath(ROOT, path)}: Claude PostToolBatch must invoke changeforge_read_context_gate"
            )

    matchers = _post_tool_matchers(hooks)
    if not any("edit" in matcher.casefold() for matcher in matchers):
        errors.append(
            f"{relpath(ROOT, path)}: PostToolUse must include an Edit/Write/MultiEdit matcher"
        )
    if not any("bash" in matcher.casefold() for matcher in matchers):
        errors.append(f"{relpath(ROOT, path)}: PostToolUse must include a Bash matcher")
    if path in CODEX_TEMPLATES and not any(
        "apply_patch" in matcher.casefold() for matcher in matchers
    ):
        errors.append(
            f"{relpath(ROOT, path)}: Codex PostToolUse must include an apply_patch matcher"
        )
    for token in READ_MATCHER_TOKENS:
        if not any(token.casefold() in matcher.casefold() for matcher in matchers):
            errors.append(
                f"{relpath(ROOT, path)}: PostToolUse matcher must include {token}"
            )

    for command, context in _commands(hooks):
        lowered = command.casefold()
        if "src/" in lowered or "src\\" in lowered:
            errors.append(f"{relpath(ROOT, path)}:{context}: hook command must not reference src/")
        if USER_ABSOLUTE_PATH_RE.search(command):
            errors.append(
                f"{relpath(ROOT, path)}:{context}: hook command must not contain a user absolute path"
            )
        if path in CODEX_TEMPLATES and "CHANGEFORGE_AGENT=codex" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Codex hook command must set CHANGEFORGE_AGENT=codex"
            )
        if path in CLAUDE_TEMPLATES and "CHANGEFORGE_AGENT=claude" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Claude hook command must set CHANGEFORGE_AGENT=claude"
            )
        if path in CODEX_TEMPLATES and "/usr/bin/env python3" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Codex hook command should use /usr/bin/env python3"
            )
        if path in CLAUDE_TEMPLATES and "/usr/bin/env python3" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Claude hook command should use /usr/bin/env python3"
            )

    for timeout, context in _timeouts(hooks):
        if timeout > timeout_limit:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: timeout {timeout} exceeds {timeout_limit} seconds"
            )


def _validate_copilot_template(
    data: dict[str, Any],
    path: Path,
    *,
    errors: list[str],
) -> None:
    """Validate a VS Code Copilot flat hook template.

    Copilot uses the matcher-less format: each event maps directly to a list of
    command entries. Every supported event must invoke its dedicated script, and
    every command must set CHANGEFORGE_AGENT=copilot, use python3, avoid src/ and
    user absolute paths, and stay within the 10-second timeout budget.
    """
    if data.get("version") != 1:
        errors.append(f"{relpath(ROOT, path)}: Copilot hook template must set version to 1")

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        errors.append(f"{relpath(ROOT, path)}: hooks must be a JSON object")
        return

    for event in _copilot_unsupported_advisory_events(errors):
        if event in hooks:
            errors.append(
                f"{relpath(ROOT, path)}: Copilot must not wire unsupported advisory {event}"
            )

    for event, scripts in COPILOT_EVENT_SCRIPTS.items():
        entries = hooks.get(event)
        if not isinstance(entries, list) or not entries:
            errors.append(f"{relpath(ROOT, path)}: missing {event} hook")
            continue
        rendered = json.dumps(entries)
        for script in scripts:
            if script not in rendered:
                errors.append(f"{relpath(ROOT, path)}: {event} must invoke {script}")
    _validate_event_script_order(
        hooks,
        "SessionStart",
        SESSION_COMPACTION_ORDER,
        path,
        errors,
    )

    for command, context in _commands(hooks):
        lowered = command.casefold()
        if "src/" in lowered or "src\\" in lowered:
            errors.append(f"{relpath(ROOT, path)}:{context}: hook command must not reference src/")
        if USER_ABSOLUTE_PATH_RE.search(command):
            errors.append(
                f"{relpath(ROOT, path)}:{context}: hook command must not contain a user absolute path"
            )
        if "CHANGEFORGE_AGENT=copilot" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Copilot hook command must set CHANGEFORGE_AGENT=copilot"
            )
        if "/usr/bin/env python3" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Copilot hook command should use /usr/bin/env python3"
            )
        if "CHANGEFORGE_HOOK_MODE=block" in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Copilot hooks must not force CHANGEFORGE_HOOK_MODE=block"
            )

    for entry, context in _command_entries(hooks):
        if "timeout" in entry:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Copilot hook command must use timeoutSec, not timeout"
            )
        timeout = entry.get("timeoutSec")
        if not isinstance(timeout, int):
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Copilot hook command must set timeoutSec"
            )
        elif timeout > 10:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: timeout {timeout} exceeds 10 seconds"
            )


def _post_tool_matchers(hooks: dict[str, Any]) -> list[str]:
    matchers: list[str] = []
    post = hooks.get("PostToolUse")
    if isinstance(post, list):
        for entry in post:
            if isinstance(entry, dict):
                matcher = entry.get("matcher")
                if isinstance(matcher, str):
                    matchers.append(matcher)
    return matchers


def _commands(value: Any, context: str = "hooks") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, dict):
        command = value.get("command")
        if isinstance(command, str):
            result.append((command, context))
        for key, child in value.items():
            result.extend(_commands(child, f"{context}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_commands(child, f"{context}[{index}]"))
    return result


def _command_entries(value: Any, context: str = "hooks") -> list[tuple[dict[str, Any], str]]:
    result: list[tuple[dict[str, Any], str]] = []
    if isinstance(value, dict):
        if isinstance(value.get("command"), str):
            result.append((value, context))
        for key, child in value.items():
            result.extend(_command_entries(child, f"{context}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_command_entries(child, f"{context}[{index}]"))
    return result


def _validate_template_script_references(
    data: dict[str, Any],
    path: Path,
    errors: list[str],
) -> None:
    dist_hooks_dir = HOOK_TEMPLATE_DIST_DIRS.get(path)
    if dist_hooks_dir is None:
        return
    dist_available = DIST_DIR.is_dir()
    for script_name in _referenced_hook_scripts(data):
        source_script = HOOK_SCRIPTS_DIR / script_name
        if not source_script.is_file():
            errors.append(
                f"{relpath(ROOT, path)}: references missing source hook script {script_name}"
            )
        if not dist_available:
            continue
        dist_script = dist_hooks_dir / script_name
        if not dist_script.is_file():
            errors.append(
                f"{relpath(ROOT, path)}: references {script_name} but "
                f"{relpath(ROOT, dist_script)} is missing"
            )


def _referenced_hook_scripts(data: dict[str, Any]) -> list[str]:
    scripts: set[str] = set()
    for command, _context in _commands(data.get("hooks", {})):
        scripts.update(match.group(1) for match in HOOK_SCRIPT_REFERENCE_RE.finditer(command))
    return sorted(scripts)


def _event_invokes(hooks: dict[str, Any], event: str, script: str) -> bool:
    """True when an event group exists and at least one command invokes script."""
    groups = hooks.get(event)
    if not isinstance(groups, list) or not groups:
        return False
    return any(
        script in command for command, _context in _commands({event: groups})
    )


def _validate_event_script_order(
    hooks: dict[str, Any],
    event: str,
    ordered_scripts: tuple[str, ...],
    path: Path,
    errors: list[str],
) -> None:
    groups = hooks.get(event)
    if not isinstance(groups, list) or not groups:
        return
    rendered_commands = [command for command, _context in _commands({event: groups})]
    positions: list[int] = []
    for script in ordered_scripts:
        matching = [index for index, command in enumerate(rendered_commands) if script in command]
        if not matching:
            errors.append(f"{relpath(ROOT, path)}: {event} must invoke {script}")
            return
        positions.append(matching[0])
    if positions != sorted(positions):
        errors.append(
            f"{relpath(ROOT, path)}: {event} must order scripts as {', '.join(ordered_scripts)}"
        )


def _validate_hook_behavior(errors: list[str]) -> None:
    sys.path.insert(0, str(HOOK_SCRIPTS_DIR))
    try:
        from changeforge_action_classifier import classify_event, is_read_tool, is_review_diff_tool
        from changeforge_pre_edit_structure_gate import evaluate_pre_edit
    except Exception as exc:
        errors.append(f"hook behavior import failed: {exc}")
        return
    finally:
        try:
            sys.path.remove(str(HOOK_SCRIPTS_DIR))
        except ValueError:
            pass

    question = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "请解释一下这个概念"}
    )
    if question.get("stage") != "question" or question.get("surfaces") or question.get("should_inject"):
        errors.append("classifier: pure questions must be stage=question, surfaces=[], should_inject=False")

    for prompt in (
        "解释 hook runtime 是什么",
        "capability 和 skill 的区别是什么",
        "how to install hooks",
        "release gate 是干嘛的",
        "what is code review?",
        "解释 code review 是什么",
        "什么是 test gate？",
        "fix 是什么意思？",
        "read-before-plan 是什么？",
        "review gate 是干嘛的？",
    ):
        domain_question = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        if (
            domain_question.get("stage") != "question"
            or domain_question.get("surfaces")
            or domain_question.get("should_inject")
            or any(
                signal in domain_question.get("prompt_signals", [])
                for signal in ("review_intent", "repair_intent", "repair_followup")
            )
        ):
            errors.append(
                f"classifier: domain keyword question must not inject: {prompt!r}"
            )

    review = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "请仔细审查最新提交"}
    )
    if review.get("stage") != "review" or "review_intent" not in review.get("prompt_signals", []):
        errors.append("classifier: Chinese review intent must classify as review")

    for prompt in ("检查这次修改", "检查最新改动", "检查上面的修复"):
        artifact_review = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        if (
            artifact_review.get("stage") != "review"
            or not artifact_review.get("should_inject")
            or "review_intent" not in artifact_review.get("prompt_signals", [])
        ):
            errors.append(
                f"classifier: Chinese artifact review intent must classify as review: {prompt!r}"
            )

    for prompt, expected_stage in (
        ("review latest commit", "review"),
        ("请审查最新提交", "review"),
        ("test this repo", "test"),
        ("验证一下这个修复", "test"),
    ):
        action_request = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        if action_request.get("stage") != expected_stage or not action_request.get("should_inject"):
            errors.append(
                f"classifier: explicit execution request {prompt!r} must classify as {expected_stage}"
            )

    deployment_review = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "review deployment change"}
    )
    if deployment_review.get("stage") != "review" or "infrastructure-deployment" not in deployment_review.get("surfaces", []):
        errors.append("classifier: review deployment change must be review stage with infrastructure-deployment surface")

    chinese_release_review = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "审查发布流程"}
    )
    if (
        chinese_release_review.get("stage") != "review"
        or "infrastructure-deployment" not in chinese_release_review.get("surfaces", [])
    ):
        errors.append("classifier: Chinese release review must be review stage with infrastructure-deployment surface")

    for prompt, expected_stage in (
        ("阅读这个文件", "read"),
        ("分析这个仓库", "read"),
        ("修改这个问题", "edit"),
        ("实现这个功能", "edit"),
        ("优化 hook", "edit"),
        ("重构目录", "refactor"),
        ("测试一下", "test"),
        ("验证一下", "test"),
    ):
        classified = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        if classified.get("stage") != expected_stage or not classified.get("should_inject"):
            errors.append(
                f"classifier: Chinese intent {prompt!r} must classify as {expected_stage}"
            )

    repair = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "修复已经提交，请审查"}
    )
    if repair.get("stage") != "repair" or "repair_followup" not in repair.get("prompt_signals", []):
        errors.append("classifier: Chinese repair follow-up must classify as repair")

    if not is_read_tool({"hook_event_name": "PostToolUse", "tool_name": "mcpfilesystemreadfile"}):
        errors.append("read gate: READ_TOOLS must cover mcpfilesystemreadfile")
    if not is_review_diff_tool({"hook_event_name": "PostToolUse", "tool_name": "get_pr_diff"}):
        errors.append("read gate: review diff detection must cover get_pr_diff")

    edit_without_read = evaluate_pre_edit(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "patch": "*** Begin Patch\n*** Add File: src/services/order_service.py\n+class OrderService:\n+    pass\n*** End Patch\n"
            },
        },
        {},
    )
    if "read_evidence" not in edit_without_read.get("missing", []):
        errors.append("pre-edit gate: edit without read evidence must miss read_evidence")
    if "placement_decision" not in edit_without_read.get("missing", []):
        errors.append("pre-edit gate: new file must miss placement_decision")
    if "reuse_decision" not in edit_without_read.get("missing", []):
        errors.append("pre-edit gate: helper/service path must miss reuse_decision")
    if "object_boundary" not in edit_without_read.get("missing", []):
        errors.append("pre-edit gate: class patch must miss object_boundary")

    helper_edit = evaluate_pre_edit(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "src/common/utils/token_helper.py",
                "content": "def token_helper(value):\n    return value\n",
            },
        },
        {"read_evidence_seen": True},
    )
    if "reuse_decision" not in helper_edit.get("missing", []):
        errors.append("pre-edit gate: new helper path must miss reuse_decision")

    for event in (
        {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": "a.py"}},
        {"hook_event_name": "UserPromptSubmit", "prompt": "review this file"},
        {"hook_event_name": "UserPromptSubmit", "prompt": "what is code review?"},
    ):
        result = evaluate_pre_edit(event, {}, ROOT)
        if result.get("required"):
            errors.append("pre-edit gate: read/review/question events must not require preflight")

    injector_text = (HOOK_SCRIPTS_DIR / "changeforge_professional_injector.py").read_text(
        encoding="utf-8"
    )
    if "stage_route_present=True" in injector_text or "stage_route_present = True" in injector_text:
        errors.append("professional injector must not set stage_route_present=True")

    common_text = (HOOK_SCRIPTS_DIR / "changeforge_common.py").read_text(encoding="utf-8")
    state_schema = (HOOK_SCHEMAS_DIR / "hook-state.v1.schema.json").read_text(encoding="utf-8")
    telemetry_schema = (HOOK_SCHEMAS_DIR / "telemetry-event.v1.schema.json").read_text(
        encoding="utf-8"
    )
    state_schema_payload = json.loads(state_schema)
    telemetry_schema_payload = json.loads(telemetry_schema)
    raw_prompt_fields = {"prompt", "prompt_text", "raw_prompt"}
    if raw_prompt_fields & set(state_schema_payload.get("properties", {})):
        errors.append("hook state schema must not store raw prompt fields")
    if raw_prompt_fields & set(telemetry_schema_payload.get("properties", {})):
        errors.append("telemetry schema must not store raw prompt fields")
    if '"prompt_signals"' not in common_text:
        errors.append("hook state must store compact prompt_signals instead of prompt text")
    for field in (
        "implementation_preflights",
        "implementation_preflight_seen",
        "implementation_preflight_complete",
        "implementation_preflight_required",
        "edit_without_preflight_seen",
        "post_edit_confirmed_preflight_gap",
        "runtime_adapter",
        "normalized_events",
        "deleted_paths",
        "generated_paths",
        "external_file_changes",
        "config_changes",
        "validation_results",
        "repair_events",
        "rereview_events",
        "command_risks",
        "rollback_points",
        "post_edit_structure_findings",
        "context_control_records",
        "context_budget_findings",
        "skipped_references",
        "choice_ids",
        "choice_triggers",
        "choice_status",
        "material_choice_surfaces",
        "blocked_tool_category",
        "bounded_paths",
        "choice_gate_seen",
        "choice_gate_blocked",
        "choice_resolution_evidence_seen",
    ):
        if f'"{field}"' not in state_schema:
            errors.append(f"hook state schema must include {field}")
        if f'"{field}"' not in common_text:
            errors.append(f"hook state defaults must include {field}")
    for field in (
        "implementation_preflight_required",
        "implementation_preflight_seen",
        "implementation_preflight_complete",
        "implementation_preflight_blocked",
        "edit_without_preflight_seen",
        "post_edit_confirmed_preflight_gap",
        "normalized_events",
        "deleted_paths",
        "generated_paths",
        "external_file_changes",
        "config_changes",
        "validation_results",
        "command_risk",
        "permission_decision",
        "post_edit_structure_findings",
        "context_control_records",
        "context_budget_findings",
        "skipped_references",
        "choice_ids",
        "choice_triggers",
        "choice_status",
        "material_choice_surfaces",
        "blocked_tool_category",
        "bounded_paths",
        "choice_gate_seen",
        "choice_gate_blocked",
        "choice_resolution_evidence_seen",
    ):
        if f'"{field}"' not in telemetry_schema:
            errors.append(f"telemetry schema must include {field}")
        if f'"{field}"' not in common_text:
            errors.append(f"telemetry writer must include {field}")
    if '"pre_edit_structure_gate"' not in telemetry_schema:
        errors.append("telemetry schema must include pre_edit_structure_gate hook name")
    if '"sdd_material_choice_gate"' not in telemetry_schema:
        errors.append("telemetry schema must include sdd_material_choice_gate hook name")


def _validate_runtime_route_resolver(errors: list[str]) -> None:
    resolver_path = HOOK_SCRIPTS_DIR / "changeforge_runtime_route_resolver.py"
    skill_index_path = HOOK_SCRIPTS_DIR / "changeforge_skill_index.py"
    injector_path = HOOK_SCRIPTS_DIR / "changeforge_professional_injector.py"
    classifier_path = HOOK_SCRIPTS_DIR / "changeforge_action_classifier.py"
    pre_edit_path = HOOK_SCRIPTS_DIR / "changeforge_pre_edit_structure_gate.py"
    post_edit_path = HOOK_SCRIPTS_DIR / "changeforge_post_edit_structure_gate.py"
    common_path = HOOK_SCRIPTS_DIR / "changeforge_common.py"
    policy_path = HOOK_SCRIPTS_DIR / "changeforge_context_control_policy.py"
    if not resolver_path.is_file():
        errors.append("missing runtime route resolver")
        return

    resolver_text = resolver_path.read_text(encoding="utf-8")
    skill_index_text = skill_index_path.read_text(encoding="utf-8") if skill_index_path.is_file() else ""
    injector_text = injector_path.read_text(encoding="utf-8") if injector_path.is_file() else ""
    classifier_text = classifier_path.read_text(encoding="utf-8") if classifier_path.is_file() else ""
    common_text = common_path.read_text(encoding="utf-8") if common_path.is_file() else ""
    policy_text = policy_path.read_text(encoding="utf-8") if policy_path.is_file() else ""

    if "SKILL_INDEX" in skill_index_text:
        errors.append("changeforge_skill_index.py: must not keep a static SKILL_INDEX")
    for forbidden in (
        '"edit": ("backend-change-builder"',
        "'edit': ('backend-change-builder'",
        '"repair": ("backend-change-builder"',
        "'repair': ('backend-change-builder'",
    ):
        if forbidden in skill_index_text:
            errors.append("changeforge_skill_index.py: edit/repair must not default to backend-change-builder")
    if "changeforge_runtime_route_resolver" not in skill_index_text:
        errors.append("changeforge_skill_index.py: must delegate to runtime route resolver")
    if "classification=classification" not in injector_text:
        errors.append("changeforge_professional_injector.py: must pass classification to resolver")
    if "reset_state_for_new_prompt" not in injector_text:
        errors.append("changeforge_professional_injector.py: must reset per-turn state on UserPromptSubmit")
    if "suggested_skills=context.get(\"selected_skills\"" not in injector_text:
        errors.append("changeforge_professional_injector.py: must persist resolver-selected skills")
    if "detect_product_surfaces" not in classifier_text or "detect_language_surfaces" not in classifier_text:
        errors.append("changeforge_action_classifier.py: must use runtime resolver surface detectors")
    if "def reset_state_for_new_prompt" not in common_text or "FOLLOW_UP_PROMPT_RE" not in common_text:
        errors.append("changeforge_common.py: must support prompt-turn state isolation")
    if not policy_path.is_file():
        errors.append("missing context control policy module")
    if any(
        token in policy_text
        for token in ("requests.", "httpx.", "urllib.", "socket.", "subprocess.", "open(", "read_text(", "write_text(")
    ):
        errors.append("changeforge_context_control_policy.py: must stay pure and avoid IO/network/process operations")
    if "context_control_records" not in common_text or "skipped_references" not in common_text:
        errors.append("changeforge_common.py: must track bounded context control state")
    for stage in (
        "requirement-intake",
        "architecture-design",
        "implementation-planning",
        "coding",
        "debugging-diagnosis",
        "bug-fix",
        "code-review",
        "refactoring",
        "testing",
        "release-delivery",
        "documentation-handoff",
        "skill-authoring",
    ):
        if stage not in resolver_text:
            errors.append(f"changeforge_runtime_route_resolver.py: missing canonical stage {stage}")
    for token in ("requests.", "httpx.", "urllib.", "socket.", "subprocess.", "write_text(", "write_bytes(", "git commit", "git push"):
        if token in resolver_text:
            errors.append(f"changeforge_runtime_route_resolver.py: forbidden runtime operation token {token!r}")
    for path in (pre_edit_path, post_edit_path):
        if path.is_file() and "CODE_FILE_EXTENSIONS" not in path.read_text(encoding="utf-8"):
            errors.append(f"{path.name}: must use shared CODE_FILE_EXTENSIONS")

    sys.path.insert(0, str(HOOK_SCRIPTS_DIR))
    try:
        from changeforge_action_classifier import classify_event
        from changeforge_runtime_route_resolver import (
            CAPABILITY_IDS,
            LANGUAGE_FILE_EXTENSIONS,
            build_active_skill_context,
            context_lines,
        )
        from changeforge_context_control_policy import context_budget_limits
    except Exception as exc:
        errors.append(f"runtime resolver import failed: {exc}")
        return
    finally:
        try:
            sys.path.remove(str(HOOK_SCRIPTS_DIR))
        except ValueError:
            pass

    try:
        stage_model = load_yaml_file(ROOT / "src" / "registry" / "stage-model.yaml")
    except Exception as exc:
        errors.append(f"stage model load failed for hook validation: {exc}")
        stage_model = {}
    if isinstance(stage_model, dict):
        for entry in stage_model.get("language_surfaces", []) or []:
            if not isinstance(entry, dict):
                continue
            language = entry.get("language")
            extensions = tuple(entry.get("file_extensions") or ())
            if isinstance(language, str) and tuple(LANGUAGE_FILE_EXTENSIONS.get(language, ())) != extensions:
                errors.append(
                    f"runtime resolver: language extensions for {language} do not match stage model"
                )

    frontend = classify_event(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"patch": "*** Begin Patch\n*** Update File: src/components/UserCard.tsx\n*** End Patch\n"},
        }
    )
    frontend_context = build_active_skill_context(
        runtime="codex",
        stage=frontend["stage"],
        surfaces=frontend["surfaces"],
        event_name="PreToolUse",
        classification=frontend,
    )
    if frontend_context.get("owner_skill") != "frontend-change-builder":
        errors.append("runtime resolver: .tsx edit must route to frontend-change-builder")
    if "backend-change-builder" in frontend_context.get("selected_skills", []):
        errors.append("runtime resolver: frontend edit must not select backend-change-builder")
    if "context_control" not in frontend_context:
        errors.append("runtime resolver: active context must include context_control")
    if len("\n".join(context_lines(frontend_context))) > 6000:
        errors.append("runtime resolver: context_lines must remain under MAX_HOOK_OUTPUT_CHARS")
    control = frontend_context.get("context_control") if isinstance(frontend_context.get("context_control"), dict) else {}
    limit = context_budget_limits(str(control.get("budget_mode") or "minimal"))["max_required_references"]
    if len(frontend_context.get("required_references", [])) > limit:
        errors.append("runtime resolver: required references exceed context budget")
    if any(key in str(control) for key in ("raw_prompt", "raw_command_output", "full_diff", "file_contents")):
        errors.append("runtime resolver: context_control must not emit raw prompt/output/diff/content fields")

    unknown = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": "what is this?"})
    if unknown.get("should_inject"):
        errors.append("runtime resolver: pure question must not inject")
    no_surface_context = build_active_skill_context(
        runtime="codex",
        stage="edit",
        surfaces=[],
        event_name="UserPromptSubmit",
        classification={"stage": "edit", "product_surfaces": [], "language_surfaces": []},
    )
    if no_surface_context.get("owner_skill") != "change-forge-router":
        errors.append("runtime resolver: no-surface edit must fall back to change-forge-router")
    if "backend-change-builder" in no_surface_context.get("selected_skills", []):
        errors.append("runtime resolver: no-surface edit must not select backend-change-builder")

    docs_context = build_active_skill_context(
        runtime="codex",
        stage="edit",
        surfaces=["documentation-only"],
        event_name="UserPromptSubmit",
        classification={
            "stage": "edit",
            "product_surfaces": ["documentation-only"],
            "language_surfaces": [],
            "risk_surfaces": ["documentation"],
        },
    )
    if docs_context.get("owner_skill") != "change-documentation-gate":
        errors.append("runtime resolver: docs-only edit must route to change-documentation-gate")
    if "quality-test-gate" in docs_context.get("selected_skills", []):
        errors.append("runtime resolver: docs-only edit must not select quality-test-gate")
    if "test gate" in docs_context.get("required_quality_gates", []):
        errors.append("runtime resolver: docs-only edit must not require test gate")

    read_context = build_active_skill_context(
        runtime="codex",
        stage="read",
        surfaces=[],
        event_name="PostToolUse",
        classification={
            "stage": "read",
            "product_surfaces": [],
            "language_surfaces": [],
            "risk_surfaces": [],
        },
    )
    if "quality-test-gate" in read_context.get("selected_skills", []):
        errors.append("runtime resolver: read-only route must not select quality-test-gate")
    if "test gate" in read_context.get("required_quality_gates", []):
        errors.append("runtime resolver: read-only route must not require test gate")

    coding_state = {
        "read_evidence_seen": True,
        "implementation_preflight_required": True,
        "implementation_preflight_complete": True,
        "implementation_preflights": ["paths=src/services/order_service.py; fields=test_plan,risk"],
        "pre_edit_missing_test_plan": False,
        "validation_command_seen": False,
        "validation_seen": False,
    }
    coding_context = build_active_skill_context(
        runtime="codex",
        stage="edit",
        surfaces=["backend-product"],
        event_name="PreToolUse",
        state=coding_state,
        classification={
            "stage": "edit",
            "product_surfaces": ["backend-product"],
            "language_surfaces": ["python"],
            "risk_surfaces": [],
        },
    )
    if coding_context.get("current_stage") != "coding":
        errors.append("runtime resolver: edit with completed preflight test plan must enter coding")

    multi_surface_context = build_active_skill_context(
        runtime="codex",
        stage="edit",
        surfaces=["backend-product", "api-contract"],
        event_name="PreToolUse",
        state=coding_state,
        classification={
            "stage": "edit",
            "product_surfaces": ["backend-product", "api-contract"],
            "language_surfaces": ["python"],
            "risk_surfaces": ["data-api"],
        },
    )
    if multi_surface_context.get("product_surfaces") != ["backend-product", "api-contract"]:
        errors.append("runtime resolver: multi-surface route must preserve all product surfaces")
    if multi_surface_context.get("primary_product_surface") != "backend-product":
        errors.append("runtime resolver: multi-surface route must record primary product surface")
    if "api-contract-design" not in multi_surface_context.get("selected_capabilities", []):
        errors.append("runtime resolver: secondary product surface capability must be selected")
    if multi_surface_context.get("product_surface") != multi_surface_context.get("primary_product_surface"):
        errors.append("runtime resolver: legacy product_surface must match primary_product_surface")

    registered_capabilities = set(CAPABILITY_IDS)
    illegal_skipped = []
    for context in (frontend_context, docs_context, read_context, multi_surface_context):
        for entry in context.get("skipped_capabilities", []):
            if not isinstance(entry, dict):
                illegal_skipped.append(str(entry))
                continue
            capability = entry.get("capability")
            if capability not in registered_capabilities:
                illegal_skipped.append(str(capability))
    if illegal_skipped:
        errors.append(
            "runtime resolver: skipped_capabilities must contain only registered "
            f"foundation capabilities, found {illegal_skipped}"
        )

    web3_sdk_context = build_active_skill_context(
        runtime="codex",
        stage="edit",
        surfaces=["web3", "sdk-library"],
        event_name="PreToolUse",
        state=coding_state,
        classification={
            "stage": "edit",
            "product_surfaces": ["web3", "sdk-library"],
            "language_surfaces": ["typescript"],
            "risk_surfaces": ["security"],
            "domain_extensions": ["web3-product-extension"],
        },
    )
    if web3_sdk_context.get("owner_skill") != "data-api-contract-changer":
        errors.append("runtime resolver: Web3 SDK coding owner must come from product surface")
    if "web3-product-extension" not in web3_sdk_context.get("selected_domain_extensions", []):
        errors.append("runtime resolver: Web3 SDK route must preserve web3 domain extension")

    context_risk = build_active_skill_context(
        runtime="codex",
        stage="edit",
        surfaces=["skill-authoring"],
        event_name="UserPromptSubmit",
        classification={
            "stage": "skill_authoring",
            "product_surfaces": ["skill-authoring"],
            "language_surfaces": [],
            "risk_surfaces": [],
            "conditional_capabilities": ["context-control-plane"],
        },
    )
    risk_control = context_risk.get("context_control", {})
    if risk_control.get("budget_mode") not in {"single-stage", "staged-plan"}:
        errors.append("runtime resolver: skill-authoring context risk must use bounded non-minimal budget")
    if "context-control-plane" not in context_risk.get("selected_capabilities", []):
        errors.append("runtime resolver: skill-authoring context risk must select context-control-plane")


def _timeouts(value: Any, context: str = "hooks") -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    if isinstance(value, dict):
        timeout = value.get("timeout")
        if isinstance(timeout, int):
            result.append((timeout, context))
        for key, child in value.items():
            result.extend(_timeouts(child, f"{context}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_timeouts(child, f"{context}[{index}]"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
