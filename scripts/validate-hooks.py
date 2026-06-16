#!/usr/bin/env python3
"""Validate ChangeForge hook runtime source and templates."""

from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path
from typing import Any

from validation_utils import fail_many, relpath


ROOT = Path(__file__).resolve().parents[1]
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
        "changeforge_review_gate",
    ),
    "PreToolUse": (
        "changeforge_professional_injector",
        "changeforge_pre_tool_risk_preview",
        "changeforge_permission_policy_gate",
    ),
    "PermissionRequest": ("changeforge_permission_policy_gate",),
    "PostToolUse": (
        "changeforge_professional_injector",
        "changeforge_read_context_gate",
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
    "Stop": ("changeforge_stop_closure_gate",),
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
COPILOT_UNSUPPORTED_ADVISORY_EVENTS = ("UserPromptSubmit", "PreToolUse", "SubagentStop")
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
    "changeforge_runtime_adapters.py",
    "changeforge_action_classifier.py",
    "changeforge_skill_index.py",
    "changeforge_session_bootstrap.py",
    "changeforge_user_prompt_route_reminder.py",
    "changeforge_pre_tool_risk_preview.py",
    "changeforge_professional_injector.py",
    "changeforge_read_context_gate.py",
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
STATE_FINDING_FIELDS = (
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
)
SESSION_COMPACTION_ORDER = (
    "changeforge_compaction_snapshot",
    "changeforge_session_bootstrap",
    "changeforge_compaction_reinject",
    "changeforge_professional_injector",
)
READ_MATCHER_TOKENS = ("Fetch", "fetch_pr_patch", "get_pr_diff")


def main() -> int:
    errors: list[str] = []

    _validate_required_files(errors)
    _validate_python_files(errors)
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
    _validate_hook_behavior(errors)

    if errors:
        return fail_many("validate-hooks", errors)
    print("validate-hooks: validated hook runtime scripts and templates.")
    return 0


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

    common_script = HOOK_SCRIPTS_DIR / "changeforge_common.py"
    if common_script.is_file():
        common_text = common_script.read_text(encoding="utf-8")
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

    for event in COPILOT_UNSUPPORTED_ADVISORY_EVENTS:
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
        if ".Stop" in context:
            if "CHANGEFORGE_HOOK_MODE=block" not in command:
                errors.append(
                    f"{relpath(ROOT, path)}:{context}: Copilot Stop must set CHANGEFORGE_HOOK_MODE=block"
                )
        elif "CHANGEFORGE_HOOK_MODE=block" in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: only Copilot Stop may set CHANGEFORGE_HOOK_MODE=block"
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
            f"{relpath(ROOT, path)}: {event} must order compaction snapshot before bootstrap, reinject, and professional injection"
        )


def _validate_hook_behavior(errors: list[str]) -> None:
    sys.path.insert(0, str(HOOK_SCRIPTS_DIR))
    try:
        from changeforge_action_classifier import classify_event, is_read_tool, is_review_diff_tool
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

    review = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "请仔细审查最新提交"}
    )
    if review.get("stage") != "review" or "review_intent" not in review.get("prompt_signals", []):
        errors.append("classifier: Chinese review intent must classify as review")

    repair = classify_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "修复已经提交，请审查"}
    )
    if repair.get("stage") != "repair" or "repair_followup" not in repair.get("prompt_signals", []):
        errors.append("classifier: Chinese repair follow-up must classify as repair")

    if not is_read_tool({"hook_event_name": "PostToolUse", "tool_name": "mcpfilesystemreadfile"}):
        errors.append("read gate: READ_TOOLS must cover mcpfilesystemreadfile")
    if not is_review_diff_tool({"hook_event_name": "PostToolUse", "tool_name": "get_pr_diff"}):
        errors.append("read gate: review diff detection must cover get_pr_diff")

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
    if '"prompt"' in state_schema or '"prompt_text"' in state_schema:
        errors.append("hook state schema must not store raw prompt fields")
    if '"prompt"' in telemetry_schema or '"prompt_text"' in telemetry_schema:
        errors.append("telemetry schema must not store raw prompt fields")
    if '"prompt_signals"' not in common_text:
        errors.append("hook state must store compact prompt_signals instead of prompt text")


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
