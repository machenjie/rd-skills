#!/usr/bin/env python3
"""Warn when edits or commands touch ChangeForge risk surfaces."""

from __future__ import annotations

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
    hook_mode,
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
READ_ONLY_GIT_SUBCOMMANDS = {"grep"}
SHELL_WRAPPER_PROGRAMS = {"bash", "sh", "zsh"}
COMMAND_SEPARATORS = {"|", "|&", "&&", "||", ";"}
WRITE_REDIRECT_TOKENS = {">", ">>", "1>", "1>>", "2>", "2>>", "&>", "&>>"}
FIND_MUTATING_TOKENS = {"-delete", "-exec", "-execdir"}


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
    if not is_post_tool_use(event):
        return 0
    tool = compact_name(tool_name(event))
    if tool not in WATCHED_TOOLS:
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        paths = extract_changed_paths(event)
        command = extract_bash_command(event)
        path_findings = _risk_findings(paths, "")
        command_findings = _risk_findings([], command)
        findings = _merge_findings(path_findings + command_findings)
        closure_command_findings = (
            command_findings if _command_risk_is_closure_relevant(paths, command) else []
        )
        closure_findings = _merge_findings(path_findings + closure_command_findings)
        path_surfaces = [str(finding["name"]) for finding in path_findings]
        command_surfaces = [str(finding["name"]) for finding in command_findings]
        closure_surfaces = [str(finding["name"]) for finding in closure_findings]
        debug_log(
            repo,
            f"risk gate runtime={runtime} event={event_name(event)} tool={tool_name(event)} paths={paths} command={command!r} findings={findings} closure={closure_findings}",
        )
        state = merge_state(
            repo,
            runtime,
            changed_paths=paths,
            risk_surfaces=closure_surfaces,
            changed_path_risk_surfaces=path_surfaces,
            command_risk_surfaces=command_surfaces,
            closure_risk_surfaces=closure_surfaces,
            suggested_skills=_collect(closure_findings, "skills"),
            suggested_capabilities=_collect(closure_findings, "capabilities"),
            suggested_domain_extensions=_collect(closure_findings, "domain_extensions"),
            suggested_gates=_collect(closure_findings, "gates"),
            validation_command_seen=_looks_like_validation(command),
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
            changed_paths=paths,
            command_program=summarize_command_program(command),
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
            validation_evidence_detected=False,
        )
        if not closure_findings or mode == "monitor":
            return 0
        # First risk surface of the turn carries a route-preflight nudge so Codex,
        # which has no session-start hook, still gets an early routing reminder.
        # Subsequent risk warnings in the same turn omit it to avoid repetition.
        preflight_needed = bool(closure_findings) and not bool(
            state.get("route_preflight_emitted")
        )
        message = _warning_message(closure_findings, include_route_preflight=preflight_needed)
        if preflight_needed:
            state["route_preflight_emitted"] = True
            save_state(repo, state)
        if mode == "block":
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
    if command:
        evidence.append(command.strip())
    haystacks = [item.casefold().replace("\\", "/") for item in evidence]
    findings: list[dict[str, object]] = []
    for rule in RISK_RULES:
        matched = [
            item
            for item, lowered in zip(evidence, haystacks, strict=False)
            if any(pattern.casefold() in lowered for pattern in rule["patterns"])
        ]
        if matched:
            findings.append({**rule, "evidence": _unique(matched)})
    return findings


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
    if _looks_like_validation(command):
        return False
    return not _command_is_read_only(command)


def _command_is_read_only(command: str, *, depth: int = 0) -> bool:
    if depth > 3:
        return False
    tokens = _command_tokens(command)
    if not tokens or _has_write_redirection(tokens):
        return False
    inner_command = _shell_wrapper_inner_command(tokens)
    if inner_command is not None:
        return _command_is_read_only(inner_command, depth=depth + 1)
    segments = _command_segments(tokens)
    return bool(segments) and all(_segment_is_read_only(segment) for segment in segments)


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


def _command_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in COMMAND_SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _segment_is_read_only(tokens: list[str]) -> bool:
    program, index = _program_token(tokens)
    if not program:
        return False
    if program == "git":
        return _git_subcommand(tokens[index + 1 :]) in READ_ONLY_GIT_SUBCOMMANDS
    if program == "find" and any(token in FIND_MUTATING_TOKENS for token in tokens[index + 1 :]):
        return False
    return program in READ_ONLY_COMMAND_PROGRAMS


def _program_token(tokens: list[str]) -> tuple[str, int]:
    for index, token in enumerate(tokens):
        if "=" in token and token.split("=", 1)[0].isidentifier():
            continue
        return token.casefold(), index
    return "", -1


def _git_subcommand(tokens: list[str]) -> str:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "-C" and index + 1 < len(tokens):
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token.casefold()
    return ""


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
            "\nExpected ChangeForge domain extensions:\n"
            f"{chr(10).join(extension_lines)}\n"
        )
    preflight_text = ""
    if include_route_preflight:
        preflight_text = (
            "Route preflight (first risk surface this turn): run change-forge-router "
            "before continuing and emit a changeforge_route manifest naming "
            "selected_skills, selected_capabilities, required_references, and "
            "required_quality_gates. Restate it at handoff; a route described only in "
            "prose is not closure evidence.\n\n"
        )
    return f"""{preflight_text}ChangeForge Risk Surface Gate triggered.

Detected risk surfaces:
{chr(10).join(surface_lines)}
{extension_text}

Expected ChangeForge gates:
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
