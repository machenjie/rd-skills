#!/usr/bin/env python3
"""Warn when edits or commands touch ChangeForge risk surfaces."""

from __future__ import annotations

import re
import shlex

from changeforge_common import (
    compact_name,
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_block,
    emit_warning,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    is_post_tool_use,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    save_state,
    session_id_from_event,
    summarize_command_program,
    tool_name,
    write_telemetry_event,
)
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)
from changeforge_hook_policy import gate_mode


# Compacted (lowercase, alphanumeric-only) watched tool names across runtimes:
# Codex/Claude edit + bash tools, plus VS Code Copilot edit tools and the
# VS Code terminal tools (runTerminalCommand, runInTerminal / run_in_terminal).
WATCHED_TOOLS = {
    "edit",
    "write",
    "multiedit",
    "applypatch",
    "bash",
    "editfiles",
    "createfile",
    "replacestringinfile",
    "inserteditintofile",
    "multireplacestringinfile",
    "runterminalcommand",
    "runinterminal",
}
RISK_RULES = [
    {
        "name": "security",
        "patterns": ["auth", "authorization", "permission", "rbac", "jwt", "oauth", "secret", "token"],
        "skills": ["security-privacy-gate"],
        "capabilities": ["authentication-authorization", "secret-configuration-security"],
        "gates": ["security gate"],
    },
    {
        "name": "data-api",
        "patterns": ["migration", "schema", "sql", "dto", "contract", "repository", "dao"],
        "skills": ["data-api-contract-changer", "quality-test-gate"],
        "capabilities": ["data-model-design", "data-migration-design", "contract-testing"],
        "gates": ["API/data gate", "test gate"],
    },
    {
        "name": "cache",
        "patterns": ["redis", "cache", "memcached", "ttl", "eviction"],
        "skills": ["data-middleware-change-builder", "reliability-observability-gate"],
        "capabilities": ["cache-design"],
        "gates": ["reliability gate"],
    },
    {
        "name": "queue",
        "patterns": ["kafka", "topic", "consumer", "producer", "dlq", "offset"],
        "skills": ["data-middleware-change-builder"],
        "capabilities": ["message-queue-design"],
        "gates": ["reliability gate"],
    },
    {
        "name": "kubernetes",
        "patterns": [
            "kubectl",
            "k8s",
            "kubernetes",
            "deployment",
            "statefulset",
            "ingress",
            "gateway",
            "hpa",
            "rbac",
            "serviceaccount",
        ],
        "skills": ["delivery-release-gate", "reliability-observability-gate"],
        "capabilities": ["kubernetes-gateway"],
        "gates": ["delivery gate", "reliability gate"],
    },
    {
        "name": "helm",
        "patterns": ["helm", "chart.yaml", "values.yaml", "templates/"],
        "skills": ["delivery-release-gate"],
        "capabilities": ["kubernetes-gateway", "ci-cd", "secret-configuration-security"],
        "gates": ["delivery gate", "security gate"],
    },
    {
        "name": "spark-bigdata",
        "patterns": ["spark", "pyspark", "flink", "warehouse", "partition", "etl", "backfill"],
        "skills": ["data-middleware-change-builder", "quality-test-gate"],
        "capabilities": [],
        "domain_extensions": ["bigdata-product-extension"],
        "gates": ["test gate", "reliability gate"],
    },
    {
        "name": "ai-rag",
        "patterns": ["llm", "rag", "embedding", "vector database", "prompt injection", "agent tool"],
        "skills": ["security-privacy-gate", "quality-test-gate"],
        "capabilities": ["threat-modeling", "test-strategy"],
        "domain_extensions": ["ai-product-extension"],
        "gates": ["security gate", "test gate"],
    },
    {
        "name": "web3",
        "patterns": ["web3", "wallet", "smart contract", "blockchain", "on-chain", "eip-712", "reorg", "solidity"],
        "skills": ["security-privacy-gate", "quality-test-gate"],
        "capabilities": ["authentication-security", "threat-modeling"],
        "domain_extensions": ["web3-product-extension"],
        "gates": ["security gate", "test gate"],
    },
    {
        "name": "payment-trading",
        "patterns": ["payment", "billing", "subscription", "invoice", "trading", "ledger", "settlement", "refund", "chargeback"],
        "skills": ["security-privacy-gate", "data-api-contract-changer", "quality-test-gate"],
        "capabilities": ["idempotency-retry-design", "transaction-consistency"],
        "domain_extensions": ["payment-trading-extension"],
        "gates": ["security gate", "API/data gate", "test gate"],
    },
    {
        "name": "mobile",
        "patterns": ["android", "/ios/", "ios app", "mobile app", "push notification", "deep link", "app store"],
        "skills": ["quality-test-gate"],
        "capabilities": ["test-strategy"],
        "domain_extensions": ["mobile-product-extension"],
        "gates": ["test gate"],
    },
    {
        "name": "iot-embedded",
        "patterns": ["firmware", "embedded", "sensor", "actuator", "ota update", "field device"],
        "skills": ["reliability-observability-gate", "quality-test-gate"],
        "capabilities": ["concurrency-control", "language-performance-safety"],
        "domain_extensions": ["iot-embedded-extension"],
        "gates": ["reliability gate", "test gate"],
    },
    {
        "name": "low-level-systems",
        "patterns": [".cpp", ".hpp", ".cxx", "kernel", "driver", "syscall", "ffi", "c abi", "undefined behavior", "sanitizer"],
        "skills": ["reliability-observability-gate", "quality-test-gate"],
        "capabilities": ["language-performance-safety", "concurrency-control"],
        "domain_extensions": ["low-level-systems-extension"],
        "gates": ["reliability gate", "test gate"],
    },
]
VALIDATION_MARKERS = (
    " test",
    "pytest",
    "unittest",
    "go test",
    "cargo test",
    "npm test",
    "pnpm test",
    "validate-",
    "validate_",
    "scripts/validate",
    "eval-routing",
    "eval-skill-professionalism",
    "eval-professional-benchmarks",
    "eval-agent-behavior",
    "eval-professional-agent-samples",
    "eval-pressure-behavior",
    "run-codegen-benchmarks",
    "validate-installation",
)
READ_ONLY_COMMAND_PROGRAMS = {
    "awk",
    "bat",
    "cat",
    "cd",
    "fd",
    "find",
    "grep",
    "head",
    "jq",
    "less",
    "ls",
    "nl",
    "pwd",
    "rg",
    "ripgrep",
    "sed",
    "stat",
    "tail",
    "tree",
    "wc",
}
READ_ONLY_GIT_SUBCOMMANDS = {
    "branch",
    "cat-file",
    "diff",
    "grep",
    "log",
    "ls-files",
    "rev-parse",
    "show",
    "status",
}
NEUTRAL_STATUS_PROGRAMS = {"true", ":"}
KUBECTL_READ_ONLY_SUBCOMMANDS = {"get", "describe", "top", "version"}
KUBECTL_MUTATING_SUBCOMMANDS = {
    "apply",
    "delete",
    "edit",
    "patch",
    "scale",
    "cp",
    "port-forward",
}
KUBECTL_OPTIONS_WITH_VALUES = {
    "--as",
    "--as-group",
    "--cache-dir",
    "--certificate-authority",
    "--client-certificate",
    "--client-key",
    "--cluster",
    "--context",
    "--kubeconfig",
    "--namespace",
    "--password",
    "--profile",
    "--server",
    "--token",
    "--user",
    "--username",
    "-n",
}
SSH_OPTIONS_WITH_VALUES = {
    "-b",
    "-c",
    "-D",
    "-E",
    "-e",
    "-F",
    "-I",
    "-i",
    "-J",
    "-L",
    "-l",
    "-m",
    "-O",
    "-o",
    "-p",
    "-Q",
    "-R",
    "-S",
    "-W",
    "-w",
}
MUTATING_GIT_BRANCH_OPTIONS = {
    "-c",
    "-C",
    "-d",
    "-D",
    "-m",
    "-M",
    "--copy",
    "--delete",
    "--edit-description",
    "--move",
    "--no-track",
    "--set-upstream-to",
    "--track",
    "--unset-upstream",
}
SHELL_WRAPPER_PROGRAMS = {"bash", "sh", "zsh"}
COMMAND_SEPARATORS = {"|", "|&", "&&", "||", ";"}
WRITE_REDIRECT_TOKENS = {">", ">>", "1>", "1>>", "2>", "2>>", "&>", "&>>"}
FIND_MUTATING_TOKENS = {"-delete", "-exec", "-execdir"}
HIGH_RISK_TOOL_PERMISSION_PROGRAMS = {
    "az",
    "aws",
    "chmod",
    "chown",
    "gcloud",
    "helm",
    "kubectl",
    "mysql",
    "psql",
    "rm",
    "sudo",
    "terraform",
    "tofu",
}
HIGH_RISK_GIT_SUBCOMMANDS = {
    "checkout",
    "clean",
    "push",
    "reset",
    "restore",
}
HIGH_RISK_COMMAND_MARKER_RE = re.compile(
    r"(^|[/_\-\s])"
    r"(?:migrate|migration|backfill|deploy|apply|destroy|publish|delete|credential|secret|token)"
    r"($|[/_\-\s.])"
)
ENV_FILE_RE = re.compile(r"(^|[\s/])\.env(?:\s|$)")
ENV_METADATA_RE = re.compile(
    r"(?:\btest\s+-f\s+\.env\b|\[\s+-f\s+\.env\s*\])"
)
ENV_KEY_NAME_ONLY_RE = re.compile(
    r"(?:cut\s+-d=?['\"]?=['\"]?\s+-f\s*1\s+\.env|"
    r"awk\s+-f=?['\"]?=['\"]?.*print\s+\$1.*\.env|"
    r"sed\s+.*s/=\.\*/.*\.env)"
)


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    if runtime == "unknown":
        return 0
    mode = gate_mode("risk_surface")
    if mode == "off":
        return 0
    if not is_post_tool_use(event):
        return 0
    tool = compact_name(tool_name(event))
    if tool not in WATCHED_TOOLS:
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        paths = extract_changed_paths(event)
        command = extract_bash_command(event)
        command_risk = _command_risk_class(command, paths)
        command_fact = _command_evidence_fact(command, command_risk)
        validation_results = _validation_results(command, event)
        path_findings = _risk_findings(paths, "")
        special_findings = _special_command_findings(command, command_risk)
        advisory_findings = [
            finding for finding in special_findings if finding.get("advisory")
        ]
        required_special_findings = [
            finding for finding in special_findings if not finding.get("advisory")
        ]
        command_findings = (
            []
            if command_risk in {"production_readonly_diagnostic", "secret_metadata_read"}
            else _risk_findings([], command)
        )
        tool_permission_findings = _tool_permission_findings(tool, command, paths)
        findings = _merge_findings(
            path_findings
            + command_findings
            + required_special_findings
            + tool_permission_findings
            + advisory_findings
        )
        closure_command_findings = (
            command_findings + required_special_findings
            if _command_risk_is_closure_relevant(paths, command)
            else []
        )
        closure_findings = _merge_findings(
            path_findings + closure_command_findings + tool_permission_findings
        )
        display_findings = _merge_findings(closure_findings + advisory_findings)
        path_surfaces = [str(finding["name"]) for finding in path_findings]
        command_surfaces = [
            str(finding["name"])
            for finding in [
                *command_findings,
                *required_special_findings,
                *tool_permission_findings,
                *advisory_findings,
            ]
        ]
        closure_surfaces = [str(finding["name"]) for finding in closure_findings]
        debug_log(
            repo,
            f"risk gate runtime={runtime} event={event_name(event)} tool={tool_name(event)} paths={paths} command_fact={command_fact!r} findings={findings} closure={closure_findings}",
        )
        snapshot = snapshot_from_event_state(
            event,
            {},
            classification={
                "stage": "test" if _looks_like_validation(command) else "edit",
                "paths": paths,
                "tool": tool_name(event),
                "command_program": summarize_command_program(command),
                "risk_surfaces": closure_surfaces,
            },
            gate_name="risk_surface",
            gate_mode=mode,
            gate_facts={"command_risk": command_risk, "risk_surfaces": closure_surfaces},
        )
        snapshot_update = state_update_from_snapshot(snapshot)
        snapshot_update["changed_paths"] = paths
        snapshot_update["command_risks"] = [f"{command_risk}:{command_fact}"]
        snapshot_update["validation_results"] = validation_results
        snapshot_update["validation_command_seen"] = _looks_like_validation(command) or None
        state = merge_state(
            repo,
            runtime,
            **snapshot_update,
            risk_surfaces=closure_surfaces,
            changed_path_risk_surfaces=path_surfaces,
            command_risk_surfaces=command_surfaces,
            closure_risk_surfaces=closure_surfaces,
            suggested_skills=_collect(closure_findings, "skills"),
            suggested_capabilities=_collect(closure_findings, "capabilities"),
            suggested_domain_extensions=_collect(closure_findings, "domain_extensions"),
            suggested_gates=_collect(closure_findings, "gates"),
            tool_permission_sandbox_seen=bool(tool_permission_findings),
        )
        write_telemetry_event(
            repo,
            runtime=runtime,
            hook_name="risk_surface_gate",
            event_name=event_name(event),
            mode=mode,
            session_id=session_id_from_event(event),
            cwd=cwd_from_event(event),
            tool_name=tool_name(event),
            normalized_events=snapshot_update["normalized_events"],
            changed_paths=paths,
            command_program=summarize_command_program(command),
            command_risk=command_risk,
            hook_findings={
                "risk_surfaces": closure_surfaces,
                "changed_path_risk_surfaces": path_surfaces,
                "command_risk_surfaces": command_surfaces,
                "closure_risk_surfaces": closure_surfaces,
            },
            suggested_skills=_collect(closure_findings, "skills"),
            suggested_capabilities=_collect(closure_findings, "capabilities"),
            suggested_domain_extensions=_collect(closure_findings, "domain_extensions"),
            suggested_gates=_collect(closure_findings, "gates"),
            risk_surfaces=closure_surfaces,
            changed_path_risk_surfaces=path_surfaces,
            command_risk_surfaces=command_surfaces,
            closure_risk_surfaces=closure_surfaces,
            validation_command_detected=_looks_like_validation(command),
            validation_results=validation_results,
            validation_evidence_detected=False,
            tool_permission_sandbox_seen=bool(tool_permission_findings),
        )
        if not display_findings or mode == "monitor":
            return 0
        # First risk surface of the turn carries a route-preflight nudge so Codex,
        # which has no session-start hook, still gets an early routing reminder.
        # Subsequent risk warnings in the same turn omit it to avoid repetition.
        preflight_needed = bool(closure_findings) and not bool(
            state.get("route_preflight_emitted")
        )
        message = _warning_message(display_findings, include_route_preflight=preflight_needed)
        if preflight_needed:
            state["route_preflight_emitted"] = True
            save_state(repo, state)
        if mode == "block" and closure_findings:
            emit_block(runtime, event_name(event), message)
            return 0
        emit_warning(runtime, event_name(event), message)
        return 0
    except Exception as exc:
        emit_warning(
            runtime,
            event_name(event),
            f"ChangeForge Hook Runtime warning: risk surface gate failed open: {exc}",
        )
        return 0


def _risk_findings(paths: list[str], command: str) -> list[dict[str, object]]:
    evidence = [normalize_path(path) for path in paths]
    raw = list(evidence)
    if command:
        raw.append(command.strip())
        evidence.append(_command_evidence_fact(command))
    haystacks = [item.casefold().replace("\\", "/") for item in raw]
    findings: list[dict[str, object]] = []
    for rule in RISK_RULES:
        matched = [
            item
            for item, lowered in zip(evidence, haystacks)
            if any(pattern.casefold() in lowered for pattern in rule["patterns"])
        ]
        if matched:
            findings.append({**rule, "evidence": _unique(matched)})
    return findings


def _special_command_findings(command: str, risk_class: str) -> list[dict[str, object]]:
    """Return precise command findings without reusing raw command text."""
    if not command:
        return []
    evidence = [_command_evidence_fact(command, risk_class)]
    if risk_class == "production_readonly_diagnostic":
        return [
            {
                "name": "production-readonly-diagnostic",
                "skills": [
                    "reliability-observability-gate",
                    "security-privacy-gate",
                    "agent-execution-discipline",
                ],
                "capabilities": ["failure-diagnosis", "agent-tool-permission-sandbox"],
                "gates": ["reliability gate", "security gate"],
                "evidence": evidence,
                "advisory": True,
            }
        ]
    if risk_class == "secret_sensitive_output":
        return [
            {
                "name": "secret-sensitive-output",
                "skills": ["security-privacy-gate", "agent-execution-discipline"],
                "capabilities": [
                    "secret-configuration-security",
                    "agent-tool-permission-sandbox",
                ],
                "gates": ["security gate"],
                "evidence": evidence,
            }
        ]
    if risk_class == "external_write_release":
        return [
            {
                "name": "external-write-release",
                "skills": [
                    "delivery-release-gate",
                    "reliability-observability-gate",
                    "security-privacy-gate",
                    "agent-execution-discipline",
                ],
                "capabilities": ["kubernetes-gateway", "agent-tool-permission-sandbox"],
                "gates": ["delivery gate", "reliability gate", "security gate"],
                "evidence": evidence,
            }
        ]
    return []


def _command_evidence_fact(command: str, risk_class: str = "") -> str:
    classification = _special_command_classification(command)
    if classification:
        evidence = str(classification.get("evidence") or "").strip()
        if evidence:
            return evidence
    program = summarize_command_program(command) or "unknown"
    return f"{risk_class}:{program}" if risk_class else program


def _special_command_classification(command: str, *, depth: int = 0) -> dict[str, object]:
    if depth > 4:
        return {}
    tokens = _command_tokens(command)
    if not tokens:
        return {}
    inner_command = _shell_wrapper_inner_command(tokens)
    if inner_command is not None:
        return _special_command_classification(inner_command, depth=depth + 1)
    ssh_inner = _ssh_inner_command(tokens)
    if ssh_inner is not None:
        inner = _special_command_classification(ssh_inner, depth=depth + 1)
        if inner:
            return _remote_classification(inner)
        if _command_is_read_only(ssh_inner, depth=depth + 1):
            return {
                "risk_class": "safe",
                "read_only": True,
                "closure_relevant": False,
                "high_tool_permission": False,
                "evidence": "ssh:readonly",
            }
        return {}
    if _has_write_redirection(tokens) and _kubectl_logs_seen(tokens):
        return {
            "risk_class": "secret_sensitive_output",
            "read_only": False,
            "closure_relevant": True,
            "high_tool_permission": True,
            "evidence": "kubectl:logs:raw-capture",
        }
    if _env_metadata_command(command, tokens):
        return {
            "risk_class": "secret_metadata_read",
            "read_only": True,
            "closure_relevant": False,
            "high_tool_permission": False,
            "evidence": "env_file:metadata",
        }
    if _env_secret_value_command(command, tokens):
        return {
            "risk_class": "secret_sensitive_output",
            "read_only": False,
            "closure_relevant": True,
            "high_tool_permission": True,
            "evidence": "env_file:value_read",
        }
    segments = _command_segments(tokens)
    segment_classes = [
        _kubectl_segment_classification(segment)
        for _separator, segment in segments
        if segment and _program_token(segment)[0] == "kubectl"
    ]
    segment_classes = [item for item in segment_classes if item]
    if not segment_classes:
        return {}
    if any(item.get("risk_class") == "external_write_release" for item in segment_classes):
        return _first_classification(segment_classes, "external_write_release")
    if any(item.get("risk_class") == "secret_sensitive_output" for item in segment_classes):
        return _first_classification(segment_classes, "secret_sensitive_output")
    if any(item.get("risk_class") == "production_readonly_diagnostic" for item in segment_classes):
        return _first_classification(segment_classes, "production_readonly_diagnostic")
    if all(item.get("read_only") for item in segment_classes):
        return {
            "risk_class": "safe",
            "read_only": True,
            "closure_relevant": False,
            "high_tool_permission": False,
            "evidence": "kubectl:readonly",
        }
    return {}


def _first_classification(items: list[dict[str, object]], risk_class: str) -> dict[str, object]:
    for item in items:
        if item.get("risk_class") == risk_class:
            return item
    return {}


def _remote_classification(classification: dict[str, object]) -> dict[str, object]:
    result = dict(classification)
    evidence = str(result.get("evidence") or "").strip()
    result["evidence"] = f"ssh:{evidence}" if evidence else "ssh:command"
    return result


def _env_metadata_command(command: str, tokens: list[str]) -> bool:
    lowered = command.casefold()
    if ".env" not in lowered:
        return False
    if _has_write_redirection(tokens):
        return False
    if _env_value_program_seen(tokens):
        return False
    if ENV_METADATA_RE.search(lowered) and (
        "env_file=present" in lowered or "env_file=missing" in lowered
    ):
        return True
    return bool(ENV_KEY_NAME_ONLY_RE.search(lowered))


def _env_secret_value_command(command: str, tokens: list[str]) -> bool:
    lowered = command.casefold()
    if _env_value_program_seen(tokens):
        return True
    if ".env" not in lowered:
        return False
    if _has_write_redirection(tokens):
        return True
    if _env_metadata_command(command, tokens):
        return False
    value_readers = {"awk", "cat", "grep", "rg", "ripgrep", "sed"}
    for _separator, segment in _command_segments(tokens):
        program, _index = _program_token(segment)
        if program in value_readers:
            return True
    return False


def _env_value_program_seen(tokens: list[str]) -> bool:
    for _separator, segment in _command_segments(tokens):
        program, _index = _program_token(segment)
        if program in {"env", "printenv"}:
            return True
    return False


def _kubectl_logs_seen(tokens: list[str]) -> bool:
    for _separator, segment in _command_segments(tokens):
        program, index = _program_token(segment)
        if program != "kubectl":
            continue
        subcommand, _args = _kubectl_subcommand_and_args(segment[index + 1 :])
        if subcommand == "logs":
            return True
    return False


def _ssh_inner_command(tokens: list[str]) -> str | None:
    program, index = _program_token(tokens)
    if program != "ssh":
        return None
    position = index + 1
    while position < len(tokens):
        token = tokens[position]
        if token == "--":
            position += 1
            break
        if token.startswith("-"):
            option = token.split("=", 1)[0]
            position += 1
            if "=" not in token and option in SSH_OPTIONS_WITH_VALUES and position < len(tokens):
                position += 1
            continue
        position += 1
        break
    if position >= len(tokens):
        return None
    return " ".join(tokens[position:])


def _kubectl_segment_classification(tokens: list[str]) -> dict[str, object]:
    program, index = _program_token(tokens)
    if program != "kubectl":
        return {}
    subcommand, args = _kubectl_subcommand_and_args(tokens[index + 1 :])
    if not subcommand:
        return {}
    evidence = f"kubectl:{subcommand}"
    if subcommand in KUBECTL_MUTATING_SUBCOMMANDS:
        return _kubectl_classification(
            "external_write_release",
            read_only=False,
            high=True,
            evidence=f"{evidence}:external_write",
        )
    if subcommand == "rollout" and _kubectl_rollout_is_mutating(args):
        return _kubectl_classification(
            "external_write_release",
            read_only=False,
            high=True,
            evidence="kubectl:rollout:external_write",
        )
    if subcommand == "exec":
        return _kubectl_exec_classification(args)
    if subcommand == "logs":
        if _kubectl_logs_is_bounded(args):
            return _kubectl_classification(
                "production_readonly_diagnostic",
                read_only=True,
                high=False,
                closure_relevant=False,
                evidence="kubectl:logs:bounded",
            )
        return _kubectl_classification(
            "secret_sensitive_output",
            read_only=False,
            high=True,
            evidence="kubectl:logs:unbounded",
        )
    if subcommand == "config":
        if _kubectl_config_current_context(args):
            return _kubectl_classification(
                "safe",
                read_only=True,
                high=False,
                closure_relevant=False,
                evidence="kubectl:config:current-context",
            )
        if _kubectl_config_raw(args):
            return _kubectl_classification(
                "secret_sensitive_output",
                read_only=False,
                high=True,
                evidence="kubectl:config:raw",
            )
    if subcommand in {"get", "describe"} and _kubectl_resource_is_secret(args):
        return _kubectl_classification(
            "secret_sensitive_output",
            read_only=False,
            high=True,
            evidence=f"kubectl:{subcommand}:secret",
        )
    if subcommand in KUBECTL_READ_ONLY_SUBCOMMANDS:
        return _kubectl_classification(
            "safe",
            read_only=True,
            high=False,
            closure_relevant=False,
            evidence=evidence,
        )
    return {}


def _kubectl_classification(
    risk_class: str,
    *,
    read_only: bool,
    high: bool,
    evidence: str,
    closure_relevant: bool = True,
) -> dict[str, object]:
    return {
        "risk_class": risk_class,
        "read_only": read_only,
        "closure_relevant": closure_relevant,
        "high_tool_permission": high,
        "evidence": evidence,
    }


def _kubectl_subcommand_and_args(tokens: list[str]) -> tuple[str, list[str]]:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            continue
        if token.startswith("-"):
            option = token.split("=", 1)[0]
            index += 1
            if "=" not in token and option in KUBECTL_OPTIONS_WITH_VALUES and index < len(tokens):
                index += 1
            continue
        return token.casefold(), tokens[index + 1 :]
    return "", []


def _kubectl_resource_is_secret(args: list[str]) -> bool:
    for token in args:
        lowered = token.casefold()
        if lowered == "--":
            break
        if lowered.startswith("-"):
            continue
        if lowered in {"secret", "secrets"}:
            return True
        if lowered.startswith(("secret/", "secrets/")):
            return True
    return False


def _kubectl_logs_is_bounded(args: list[str]) -> bool:
    has_since = False
    has_tail = False
    index = 0
    while index < len(args):
        token = args[index]
        lowered = token.casefold()
        if lowered.startswith("--since=") or lowered.startswith("--since-time="):
            has_since = True
        elif lowered in {"--since", "--since-time"} and index + 1 < len(args):
            has_since = True
            index += 1
        elif lowered.startswith("--tail="):
            has_tail = _tail_bound_is_finite(lowered.split("=", 1)[1])
        elif lowered == "--tail" and index + 1 < len(args):
            has_tail = _tail_bound_is_finite(args[index + 1])
            index += 1
        index += 1
    return has_since and has_tail


def _tail_bound_is_finite(value: str) -> bool:
    text = str(value or "").strip()
    if not text or text in {"-1", "all"}:
        return False
    return text.isdigit() and int(text) > 0


def _kubectl_config_current_context(args: list[str]) -> bool:
    return _first_non_option(args) == "current-context"


def _kubectl_config_raw(args: list[str]) -> bool:
    return _first_non_option(args) == "view" and any(arg == "--raw" for arg in args)


def _kubectl_rollout_is_mutating(args: list[str]) -> bool:
    return _first_non_option(args) == "restart"


def _first_non_option(args: list[str]) -> str:
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--":
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token.casefold()
    return ""


def _kubectl_exec_classification(args: list[str]) -> dict[str, object]:
    if "--" not in args:
        return _kubectl_classification(
            "external_write_release",
            read_only=False,
            high=True,
            evidence="kubectl:exec:unbounded",
        )
    inner = args[args.index("--") + 1 :]
    if not inner:
        return _kubectl_classification(
            "external_write_release",
            read_only=False,
            high=True,
            evidence="kubectl:exec:unbounded",
        )
    inner_command = " ".join(inner)
    if _command_is_read_only(inner_command, depth=1):
        return _kubectl_classification(
            "production_readonly_diagnostic",
            read_only=True,
            high=False,
            closure_relevant=False,
            evidence="kubectl:exec:readonly",
        )
    return _kubectl_classification(
        "external_write_release",
        read_only=False,
        high=True,
        evidence="kubectl:exec:external_write",
    )


def _tool_permission_findings(tool: str, command: str, paths: list[str]) -> list[dict[str, object]]:
    """Return command permission findings without storing full command arguments."""
    if not command or not _command_risk_is_closure_relevant(paths, command):
        return []
    command_risk = _command_risk_class(command, paths)
    high_risk = _command_has_high_tool_permission_risk(command)
    finding = {
        "name": "tool-permission-sandbox",
        "skills": ["security-privacy-gate", "agent-execution-discipline"],
        "capabilities": ["agent-tool-permission-sandbox"],
        "gates": ["security gate"],
        "evidence": _unique([summarize_command_program(command)]),
        "risk_class": "high" if high_risk else "local-write",
    }
    if high_risk and command_risk != "secret_sensitive_output":
        finding["skills"] = [
            "security-privacy-gate",
            "delivery-release-gate",
            "reliability-observability-gate",
            "agent-execution-discipline",
        ]
        finding["gates"] = ["security gate", "delivery gate", "reliability gate"]
    return [finding]


def _command_has_high_tool_permission_risk(command: str, *, depth: int = 0) -> bool:
    if depth > 3:
        return True
    tokens = _command_tokens(command)
    if not tokens:
        return False
    classification = _special_command_classification(command, depth=depth)
    if classification:
        return bool(classification.get("high_tool_permission"))
    inner_command = _shell_wrapper_inner_command(tokens)
    if inner_command is not None:
        return _command_has_high_tool_permission_risk(inner_command, depth=depth + 1)

    program, index = _program_token(tokens)
    if program in HIGH_RISK_TOOL_PERMISSION_PROGRAMS:
        return True
    if program == "git":
        return _git_subcommand(tokens[index + 1 :]) in HIGH_RISK_GIT_SUBCOMMANDS

    lowered = command.casefold().replace("\\", "/")
    return bool(HIGH_RISK_COMMAND_MARKER_RE.search(lowered))


def _merge_findings(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for finding in findings:
        name = str(finding.get("name", "")).strip()
        if not name:
            continue
        target = merged.setdefault(name, {**finding, "evidence": []})
        evidence = finding.get("evidence", [])
        if isinstance(evidence, list):
            target["evidence"] = _unique(
                [str(item) for item in target.get("evidence", [])]
                + [str(item) for item in evidence]
            )
    return list(merged.values())


def _command_risk_is_closure_relevant(paths: list[str], command: str) -> bool:
    if paths or not command:
        return True
    classification = _special_command_classification(command)
    if classification:
        return bool(classification.get("closure_relevant"))
    if _looks_like_validation(command):
        return False
    return not _command_is_read_only(command)


def _command_is_read_only(command: str, *, depth: int = 0) -> bool:
    if depth > 3:
        return False
    tokens = _command_tokens(command)
    if not tokens or _has_write_redirection(tokens):
        return False
    classification = _special_command_classification(command, depth=depth)
    if classification:
        return bool(classification.get("read_only"))
    inner_command = _shell_wrapper_inner_command(tokens)
    if inner_command is not None:
        return _command_is_read_only(inner_command, depth=depth + 1)
    segments = _command_segments(tokens)
    if not segments:
        return False
    for index, (separator, segment) in enumerate(segments):
        if _segment_is_neutral_status(segment):
            if separator == "||" and index == len(segments) - 1:
                continue
            return False
        if not _segment_is_read_only(segment):
            return False
    return True


def _command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.strip().split()


def _has_write_redirection(tokens: list[str]) -> bool:
    return any(
        token in WRITE_REDIRECT_TOKENS
        or token.startswith((">", ">>", "1>", "1>>", "2>", "2>>", "&>", "&>>"))
        for token in tokens
    )


def _shell_wrapper_inner_command(tokens: list[str]) -> str | None:
    program, index = _program_token(tokens)
    if program not in SHELL_WRAPPER_PROGRAMS:
        return None
    for offset, token in enumerate(tokens[index + 1 :], start=index + 1):
        if token == "-c" and offset + 1 < len(tokens):
            return tokens[offset + 1]
        if token.startswith("-") and "c" in token[1:] and offset + 1 < len(tokens):
            return tokens[offset + 1]
    return None


def _command_segments(tokens: list[str]) -> list[tuple[str | None, list[str]]]:
    segments: list[tuple[str | None, list[str]]] = []
    current: list[str] = []
    current_separator: str | None = None
    for token in tokens:
        if token in COMMAND_SEPARATORS:
            if current:
                segments.append((current_separator, current))
                current = []
            current_separator = token
            continue
        current.append(token)
    if current:
        segments.append((current_separator, current))
    return segments


def _segment_is_neutral_status(tokens: list[str]) -> bool:
    program, _ = _program_token(tokens)
    return program in NEUTRAL_STATUS_PROGRAMS


def _segment_is_read_only(tokens: list[str]) -> bool:
    program, index = _program_token(tokens)
    if not program:
        return False
    if program == "git":
        return _git_command_is_read_only(tokens[index + 1 :])
    if program == "kubectl":
        classification = _kubectl_segment_classification(tokens)
        return bool(classification.get("read_only"))
    if program == "find" and any(token in FIND_MUTATING_TOKENS for token in tokens[index + 1 :]):
        return False
    return program in READ_ONLY_COMMAND_PROGRAMS


def _program_token(tokens: list[str]) -> tuple[str, int]:
    for index, token in enumerate(tokens):
        if "=" in token and token.split("=", 1)[0].isidentifier():
            continue
        return token.casefold(), index
    return "", -1


def _git_command_is_read_only(tokens: list[str]) -> bool:
    subcommand, args = _git_subcommand_and_args(tokens)
    if subcommand not in READ_ONLY_GIT_SUBCOMMANDS:
        return False
    if subcommand == "branch":
        return _git_branch_is_read_only(args)
    return True


def _git_branch_is_read_only(args: list[str]) -> bool:
    if not args:
        return True
    if any(arg in MUTATING_GIT_BRANCH_OPTIONS for arg in args):
        return False
    return all(arg.startswith("-") for arg in args)


def _git_subcommand(tokens: list[str]) -> str:
    return _git_subcommand_and_args(tokens)[0]


def _git_subcommand_and_args(tokens: list[str]) -> tuple[str, list[str]]:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "-C" and index + 1 < len(tokens):
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token.casefold(), tokens[index + 1 :]
    return "", []


def _collect(findings: list[dict[str, object]], key: str) -> list[str]:
    values: list[str] = []
    for finding in findings:
        items = finding.get(key, [])
        if isinstance(items, list):
            values.extend(str(item) for item in items)
    return _unique(values)


def _looks_like_validation(command: str) -> bool:
    lowered = f" {command.casefold()} "
    return any(marker in lowered for marker in VALIDATION_MARKERS)


def _command_risk_class(command: str, paths: list[str]) -> str:
    if paths and not command:
        return "mutation"
    if not command:
        return "unknown"
    classification = _special_command_classification(command)
    if classification:
        return str(classification.get("risk_class") or "safe")
    if _looks_like_validation(command) or _command_is_read_only(command):
        return "safe"
    tokens = _command_tokens(command)
    program, index = _program_token(tokens)
    subcommand = _git_subcommand(tokens[index + 1 :]) if program == "git" else ""
    lowered = command.casefold()
    if any(token in lowered for token in ("alembic", "prisma migrate", "db:migrate")):
        return "migration"
    if any(token in lowered for token in ("kubectl", "helm", "terraform", "docker compose")):
        return "external_write_release"
    if _command_has_high_tool_permission_risk(command) and (
        program in {"rm", "sudo"} or subcommand in {"reset", "clean", "push", "restore"}
    ):
        return "destructive"
    if any(token in lowered for token in ("npm install", "pnpm add", "yarn add", "pip install")):
        return "dependency"
    if program in {"curl", "wget", "ssh", "scp", "rsync"}:
        return "network"
    return "mutation"


def _validation_results(command: str, event: dict) -> list[str]:
    if not _looks_like_validation(command):
        return []
    return [
        "{outcome}:unknown:{program}".format(
            outcome=_observable_command_outcome(event),
            program=summarize_command_program(command) or "unknown",
        )
    ]


def _observable_command_outcome(event: dict) -> str:
    for key in ("exit_code", "exitCode", "status", "returncode", "return_code"):
        value = event.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return "pass" if value == 0 else "fail"
        if isinstance(value, str) and value.strip().isdigit():
            return "pass" if int(value.strip()) == 0 else "fail"
    outcome = str(event.get("outcome") or event.get("result") or "").strip().casefold()
    if outcome in {"success", "succeeded", "pass", "passed"}:
        return "pass"
    if outcome in {"failure", "failed", "fail", "error"}:
        return "fail"
    return "unknown"


def _warning_message(
    findings: list[dict[str, object]],
    *,
    include_route_preflight: bool = False,
) -> str:
    surface_lines = []
    for finding in findings:
        evidence = finding.get("evidence", [])
        details = ", ".join(str(item) for item in evidence) if isinstance(evidence, list) else ""
        surface_lines.append(f"- {finding['name']}: {details}")
    gate_lines = [f"- {gate}" for gate in _collect(findings, "gates")]
    extension_lines = [f"- {extension}" for extension in _collect(findings, "domain_extensions")]
    extension_text = ""
    if extension_lines:
        extension_text = (
            "\nRelevant domain expertise:\n"
            f"{chr(10).join(extension_lines)}\n"
        )
    preflight_text = ""
    if include_route_preflight:
        preflight_text = (
            "Engineering expert note:\n"
            "This change touches a high-risk surface. Before continuing, be explicit about:\n"
            "- task type and risk level\n"
            "- relevant owner skill or professional concerns\n"
            "- source files and tests that need to be read\n"
            "- validation plan and residual risk\n\n"
        )
    return f"""{preflight_text}Design risk note.

Detected risk surfaces:
{chr(10).join(surface_lines)}
{extension_text}

Relevant validation focus:
{chr(10).join(gate_lines)}

Before completion, provide:
- validation evidence
- rollback note
- residual risk"""


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
