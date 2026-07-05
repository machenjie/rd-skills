"""Validate visible Markdown implementation plans for maintainer and CI use."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .task_contract_model import (
    InternalTaskGraph,
    InternalTaskNode,
    PlanContractFinding,
    PlanQualityReport,
)
from .visible_plan_parser import parse_plan_handoff, parse_visible_plan


VALID_PLAN_MODES = {"auto", "full", "minimal"}


PLACEHOLDER_PATTERNS = (
    (re.compile(r"\bTBD\b", re.IGNORECASE), "TBD"),
    (re.compile(r"\bTODO\b", re.IGNORECASE), "TODO"),
    (re.compile(r"\bgeneric placeholder\b", re.IGNORECASE), "generic placeholder"),
    (re.compile(r"\bsimilar to above\b", re.IGNORECASE), "similar to above"),
    (re.compile(r"\bwrite tests\b", re.IGNORECASE), "write tests"),
    (re.compile(r"\bhandle edge cases\b", re.IGNORECASE), "handle edge cases"),
    (re.compile(r"\badd proper error handling\b", re.IGNORECASE), "add proper error handling"),
    (re.compile(r"\bvalidate it works\b", re.IGNORECASE), "validate it works"),
    (re.compile(r"\brefactor as needed\b", re.IGNORECASE), "refactor as needed"),
    (re.compile(r"\bupdate docs if necessary\b", re.IGNORECASE), "update docs if necessary"),
)

RISK_DOMAIN_PATTERNS = {
    "migration": re.compile(r"\b(migration|migrate|schema|backfill|data model|database)\b", re.I),
    "api": re.compile(r"\b(api|contract|endpoint|request|response|dto|status code|error code)\b", re.I),
    "auth": re.compile(r"\b(auth|authorization|permission|tenant|role|access)\b", re.I),
    "deploy": re.compile(r"\b(deploy|deployment|release|rollout|feature flag|config)\b", re.I),
}

DECISION_RISK_RE = re.compile(
    r"\b(public contract|data model|schema|security|authorization|permission|migration|rollback|release)\b",
    re.IGNORECASE,
)

ROLLBACK_RISK_DOMAINS = {"migration", "deploy"}
MINIMAL_TASK_HANDOFF_SECTIONS = {
    "files",
    "files_to_inspect",
    "files_to_change",
    "verify",
    "residual_risk",
}


def validate_visible_plan(plan: str | InternalTaskGraph, mode: str = "auto") -> PlanQualityReport:
    """Return human-readable gaps for a visible Markdown implementation plan."""

    if mode not in VALID_PLAN_MODES:
        raise ValueError(f"unknown visible plan validation mode: {mode}")
    graph = parse_visible_plan(plan) if isinstance(plan, str) else plan
    selected_mode = _select_mode(plan, graph, mode)
    findings: list[PlanContractFinding] = []

    if selected_mode == "minimal" and not graph.tasks and isinstance(plan, str):
        handoff = parse_plan_handoff(plan)
        findings.extend(_validate_minimal_handoff(handoff))
        findings.extend(_validate_placeholders(handoff))
        return PlanQualityReport(
            status="pass" if not findings else "fail",
            findings=tuple(findings),
            task_count=1,
        )

    if not graph.tasks:
        findings.append(
            PlanContractFinding(
                code="missing_tasks",
                message="No task sections were found. Use headings like '## Task 1: <title>'.",
            )
        )

    for task in graph.tasks:
        if selected_mode == "minimal":
            findings.extend(_validate_minimal_handoff(task))
            findings.extend(_validate_placeholders(task))
        else:
            findings.extend(_validate_task(task))

    return PlanQualityReport(
        status="pass" if not findings else "fail",
        findings=tuple(findings),
        task_count=len(graph.tasks),
    )


def _select_mode(plan: str | InternalTaskGraph, graph: InternalTaskGraph, requested: str) -> str:
    if requested != "auto":
        return requested
    if graph.tasks:
        if _looks_like_minimal_task_handoff(graph):
            return "minimal"
        return "full"
    if not isinstance(plan, str):
        return "full"
    handoff = parse_plan_handoff(plan)
    if _looks_like_plan_handoff(plan, handoff):
        return "minimal"
    return "full"


def _looks_like_plan_handoff(plan: str, handoff: InternalTaskNode) -> bool:
    text = str(plan or "").casefold()
    if "plan handoff" in text and (handoff.declared_files or handoff.verify or handoff.residual_risk):
        return True
    return bool(handoff.declared_files and handoff.verify and handoff.residual_risk)


def _looks_like_minimal_task_handoff(graph: InternalTaskGraph) -> bool:
    return bool(graph.tasks) and all(_is_minimal_task_handoff_shape(task) for task in graph.tasks)


def _is_minimal_task_handoff_shape(task: InternalTaskNode) -> bool:
    if not (task.declared_files and task.verify and task.residual_risk):
        return False
    if task.acceptance_criteria or task.review_scope or task.stop_conditions:
        return False
    return set(task.raw_sections).issubset(MINIMAL_TASK_HANDOFF_SECTIONS)


def _validate_task(task: InternalTaskNode) -> Iterable[PlanContractFinding]:
    findings: list[PlanContractFinding] = []
    missing_checks = (
        ("missing_goal", not task.goal, "has no Goal section."),
        ("missing_files", not task.declared_files, "has no Files section."),
        (
            "missing_acceptance_criteria",
            not task.acceptance_criteria,
            "has no Acceptance Criteria section.",
        ),
        ("missing_verify", not task.verify, "has no observable Verify command or check."),
        ("missing_expected", not task.expected_output, "has no Expected output section."),
        ("missing_review", not task.review_scope, "has no Review scope section."),
        ("missing_stop_conditions", not task.stop_conditions, "has no Stop Conditions section."),
    )
    for code, missing, message in missing_checks:
        if missing:
            findings.append(_finding(task, code, message))

    findings.extend(_validate_placeholders(task))

    domains = _risk_domains(task.all_text)
    if len(domains) >= 2:
        findings.append(
            _finding(
                task,
                "multi_risk_task",
                "combines multiple high-risk domains "
                f"({', '.join(sorted(domains))}); split it into separate reviewable tasks.",
            )
        )

    if DECISION_RISK_RE.search(task.all_text) and not task.stop_conditions:
        findings.append(
            _finding(
                task,
                "missing_risk_stop_condition",
                "touches a contract, data, security, migration, release, or rollback decision but has no stop condition.",
            )
        )

    if domains.intersection(ROLLBACK_RISK_DOMAINS) and not task.rollback_note:
        findings.append(
            _finding(
                task,
                "missing_rollback_note",
                "touches migration or release risk but has no rollback or revert note.",
            )
        )

    return findings


def _validate_minimal_handoff(task: InternalTaskNode) -> Iterable[PlanContractFinding]:
    findings: list[PlanContractFinding] = []
    missing_checks = (
        ("missing_files", not task.declared_files, "has no Files section."),
        ("missing_verify", not task.verify, "has no observable Verify command or check."),
        ("missing_residual_risk", not task.residual_risk, "has no Residual Risk section."),
    )
    for code, missing, message in missing_checks:
        if missing:
            findings.append(_finding(task, code, message))
    return findings


def _validate_placeholders(task: InternalTaskNode) -> list[PlanContractFinding]:
    findings: list[PlanContractFinding] = []
    for phrase in _placeholder_phrases(task.all_text):
        findings.append(
            _finding(
                task,
                "placeholder_text",
                f"contains placeholder text '{phrase}'; replace it with exact files, behavior, and validation.",
            )
        )
    return findings


def _placeholder_phrases(text: str) -> list[str]:
    phrases: list[str] = []
    for pattern, phrase in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            phrases.append(phrase)
    return phrases


def _risk_domains(text: str) -> set[str]:
    return {
        domain
        for domain, pattern in RISK_DOMAIN_PATTERNS.items()
        if pattern.search(text)
    }


def _finding(task: InternalTaskNode, code: str, message: str) -> PlanContractFinding:
    return PlanContractFinding(code=code, task_id=task.task_id, message=f"{task.title} {message}")
