#!/usr/bin/env python3
"""Warn when edits or commands touch ChangeForge risk surfaces."""

from __future__ import annotations

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
    session_id_from_event,
    summarize_command_program,
    tool_name,
    write_telemetry_event,
)


WATCHED_TOOLS = {"edit", "write", "multiedit", "applypatch", "bash"}
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
    "run-codegen-benchmarks",
    "validate-installation",
)


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
        findings = _risk_findings(paths, command)
        debug_log(
            repo,
            f"risk gate runtime={runtime} event={event_name(event)} tool={tool_name(event)} paths={paths} command={command!r} findings={findings}",
        )
        merge_state(
            repo,
            runtime,
            changed_paths=paths,
            risk_surfaces=[finding["name"] for finding in findings],
            suggested_skills=_collect(findings, "skills"),
            suggested_capabilities=_collect(findings, "capabilities"),
            suggested_domain_extensions=_collect(findings, "domain_extensions"),
            suggested_gates=_collect(findings, "gates"),
            validation_seen=_looks_like_validation(command),
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
                "risk_surfaces": [str(finding["name"]) for finding in findings],
            },
            suggested_skills=_collect(findings, "skills"),
            suggested_capabilities=_collect(findings, "capabilities"),
            suggested_domain_extensions=_collect(findings, "domain_extensions"),
            suggested_gates=_collect(findings, "gates"),
            risk_surfaces=[str(finding["name"]) for finding in findings],
            validation_evidence_detected=_looks_like_validation(command),
        )
        if not findings or mode == "monitor":
            return 0
        message = _warning_message(findings)
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


def _warning_message(findings: list[dict[str, object]]) -> str:
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
    return f"""ChangeForge Risk Surface Gate triggered.

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
