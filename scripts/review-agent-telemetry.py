#!/usr/bin/env python3
"""Review real ChangeForge agent telemetry and emit reports and suggestions.

This is an offline fact-review tool. It reads the append-only telemetry JSONL
written by the hook runtime, groups it by session, and reports execution-time
gaps such as a missing route manifest, missing validation evidence, or missing
residual-risk notes. It never calls a model, never reaches the network, and
never edits ``src/registry``, ``SKILL.md``, routing rules, or capabilities.

Every emitted suggestion is a candidate for human review only. Promotion to a
golden routing case, hook fixture, or agent-behavior sample is a separate,
explicit, human-confirmed step (see ``scripts/promote-telemetry-suggestion.py``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from telemetry_utils import (
    TELEMETRY_SCHEMA_VERSION,
    dump_yaml,
    iter_repo_hashes,
    iter_session_records,
    parse_iso_datetime,
    resolve_telemetry_root,
)


REPORT_FORMATS = ("markdown", "json", "yaml")

# File extension that maps a changed file to the language professional-usage
# capability the router should have selected.
LANGUAGE_CAPABILITY_BY_EXT: dict[str, str] = {
    ".go": "go-professional-usage",
    ".java": "java-jvm-professional-usage",
    ".kt": "java-jvm-professional-usage",
    ".ts": "typescript-professional-usage",
    ".tsx": "typescript-professional-usage",
    ".js": "typescript-professional-usage",
    ".jsx": "typescript-professional-usage",
    ".py": "python-professional-usage",
    ".rs": "rust-professional-usage",
    ".cpp": "cpp-professional-usage",
    ".cc": "cpp-professional-usage",
    ".cxx": "cpp-professional-usage",
    ".hpp": "cpp-professional-usage",
    ".sh": "shell-cli-professional-usage",
    ".bash": "shell-cli-professional-usage",
    ".sql": "sql-professional-usage",
}

# Risk surface recorded by the risk gate -> capability/gate the route should own.
MIDDLEWARE_EXPECTATION: dict[str, str] = {
    "cache": "cache-design",
    "queue": "message-queue-design",
    "kubernetes": "kubernetes-gateway",
    "helm": "kubernetes-gateway",
    "spark-bigdata": "bigdata-product-extension",
    "data-api": "data-migration-design",
    "security": "authentication-authorization",
}

# Paths where structural-role keyword matches are often false positives.
FALSE_POSITIVE_PATH_HINTS = ("/test", "tests/", "fixture", "/mock", "/__tests__/")

# Path tokens that usually indicate a high-risk surface the risk gate should see.
HIGH_RISK_PATH_TOKENS = (
    "auth",
    "payment",
    "billing",
    "migration",
    "secret",
    "credential",
    "k8s",
    "kubernetes",
    "helm",
    "wallet",
    "keystore",
)

STRUCTURE_FINDING_KEYS = (
    "structure_findings",
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
)


@dataclass
class SessionSummary:
    """Aggregated telemetry facts for one session, used by issue detectors."""

    session_id: str
    repo_hash: str
    record_count: int = 0
    stop_seen: bool = False
    changed_paths: set[str] = field(default_factory=set)
    added_paths: set[str] = field(default_factory=set)
    risk_surfaces: set[str] = field(default_factory=set)
    suggested_skills: set[str] = field(default_factory=set)
    suggested_capabilities: set[str] = field(default_factory=set)
    suggested_gates: set[str] = field(default_factory=set)
    findings: dict[str, set[str]] = field(default_factory=dict)
    manifest_seen: bool = False
    validation_seen: bool = False
    residual_risk_seen: bool = False
    references_seen: bool = False

    @property
    def has_code_change(self) -> bool:
        return bool(self.changed_paths or self.risk_surfaces or self.structural_findings)

    @property
    def structural_findings(self) -> set[str]:
        merged: set[str] = set()
        for key in STRUCTURE_FINDING_KEYS:
            merged.update(self.findings.get(key, set()))
        return merged


@dataclass
class Suggestion:
    """A single human-review-only improvement candidate derived from telemetry."""

    suggestion_id: str
    type: str
    severity: str
    evidence: str
    affected_session: str
    suggested_action: str
    promotion_target: str
    requires_human_review: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.suggestion_id,
            "type": self.type,
            "severity": self.severity,
            "evidence": self.evidence,
            "affected_session": self.affected_session,
            "suggested_action": self.suggested_action,
            "promotion_target": self.promotion_target,
            "requires_human_review": self.requires_human_review,
        }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = resolve_telemetry_root(args.telemetry_root)
    since = parse_iso_datetime(args.since)
    until = parse_iso_datetime(args.until)
    if args.since and since is None:
        print(f"review-agent-telemetry: invalid --since '{args.since}'", file=sys.stderr)
        return 2
    if args.until and until is None:
        print(f"review-agent-telemetry: invalid --until '{args.until}'", file=sys.stderr)
        return 2

    repo_hashes = [args.repo_hash] if args.repo_hash else iter_repo_hashes(root)
    repo_hashes = [h for h in repo_hashes if (root / h / "sessions").is_dir()]
    if not repo_hashes:
        print("review-agent-telemetry: no samples found")
        return 0

    generated_at = datetime.now(timezone.utc).isoformat()
    date_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_records = 0
    total_sessions = 0
    total_high_severity = 0
    written: list[str] = []

    for repo_hash in repo_hashes:
        summary, suggestions = _analyze_repo(root, repo_hash, since, until)
        if summary["records"] == 0:
            continue
        summary["generated_at"] = generated_at
        total_records += summary["records"]
        total_sessions += summary["sessions"]
        total_high_severity += summary["high_severity_suggestions"]

        report_text = _render_report(args.format, repo_hash, summary, suggestions)
        suggestions_text = _render_suggestions(repo_hash, summary, suggestions, generated_at)
        report_path, suggestions_path = _output_paths(
            root, repo_hash, date_stamp, args.format, args.output_dir
        )
        _write_text(report_path, report_text)
        _write_text(suggestions_path, suggestions_text)
        written.append(str(report_path))

    if total_records == 0:
        print("review-agent-telemetry: no samples found")
        return 0

    print(
        f"review-agent-telemetry: reviewed {total_records} record(s) across "
        f"{total_sessions} session(s) in {len(written)} repo telemetry dir(s); "
        f"{total_high_severity} high-severity suggestion(s)."
    )
    for path in written:
        print(f"- report: {path}")

    if args.fail_on_high_severity and total_high_severity > 0:
        return 1
    return 0


def _analyze_repo(
    root: Path,
    repo_hash: str,
    since: datetime | None,
    until: datetime | None,
) -> tuple[dict[str, Any], list[Suggestion]]:
    records = list(iter_session_records(root, repo_hash, since=since, until=until))
    sessions = _session_summaries(records, repo_hash)
    suggestions: list[Suggestion] = []
    for session in sessions.values():
        suggestions.extend(_detect_issues(session))

    issue_counts: dict[str, int] = {}
    for suggestion in suggestions:
        issue_counts[suggestion.type] = issue_counts.get(suggestion.type, 0) + 1

    summary = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "repo_hash": repo_hash,
        "records": len(records),
        "sessions": len(sessions),
        "missed_router": issue_counts.get("missed_router", 0),
        "missed_reference": _count_metric(sessions.values(), _is_missing_reference),
        "missed_gate": _count_metric(sessions.values(), _is_missing_gate),
        "validation_evidence_missing": issue_counts.get("missed_validation_evidence", 0),
        "residual_risk_missing": issue_counts.get("missed_residual_risk", 0),
        "high_severity_suggestions": sum(1 for s in suggestions if s.severity == "high"),
        "issue_counts": issue_counts,
    }
    return summary, suggestions


def _session_summaries(
    records: list[dict[str, Any]],
    repo_hash: str,
) -> dict[str, SessionSummary]:
    sessions: dict[str, SessionSummary] = {}
    for record in records:
        session_id = str(record.get("session_id") or "unknown")
        session = sessions.setdefault(
            session_id, SessionSummary(session_id=session_id, repo_hash=repo_hash)
        )
        session.record_count += 1
        session.changed_paths.update(_string_list(record.get("changed_paths")))
        session.added_paths.update(_string_list(record.get("added_paths")))
        session.risk_surfaces.update(_string_list(record.get("risk_surfaces")))
        session.suggested_skills.update(_string_list(record.get("suggested_skills")))
        session.suggested_capabilities.update(
            _string_list(record.get("suggested_capabilities"))
        )
        session.suggested_gates.update(_string_list(record.get("suggested_gates")))
        findings = record.get("hook_findings")
        if isinstance(findings, dict):
            for key, values in findings.items():
                session.findings.setdefault(str(key), set()).update(_string_list(values))
        if record.get("hook_name") == "stop_closure_gate":
            session.stop_seen = True
            session.manifest_seen |= bool(record.get("route_manifest_detected"))
            session.validation_seen |= bool(record.get("validation_evidence_detected"))
            session.residual_risk_seen |= bool(record.get("residual_risk_detected"))
            session.references_seen |= bool(record.get("required_references_detected"))
    return sessions


def _detect_issues(session: SessionSummary) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    detectors: tuple[Callable[[SessionSummary], Suggestion | None], ...] = (
        _detect_missed_router,
        _detect_missed_implementation_structure,
        _detect_missed_reuse_evidence,
        _detect_missed_language_capability,
        _detect_missed_middleware_capability,
        _detect_missed_validation_evidence,
        _detect_missed_residual_risk,
        _detect_possible_over_routing,
        _detect_hook_false_positive,
        _detect_hook_false_negative,
    )
    for index, detector in enumerate(detectors):
        result = detector(session)
        if result is not None:
            result.suggestion_id = _suggestion_id(result.type, session, index)
            suggestions.append(result)
    return suggestions


def _detect_missed_router(session: SessionSummary) -> Suggestion | None:
    if session.stop_seen and session.has_code_change and not session.manifest_seen:
        return _suggestion(
            "missed_router",
            "high",
            f"{len(session.changed_paths)} changed path(s) but no changeforge_route manifest at stop",
            session,
            "Require change-forge-router and a changeforge_route manifest for this change.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_missed_implementation_structure(session: SessionSummary) -> Suggestion | None:
    structural = session.structural_findings
    if structural and session.stop_seen and not session.manifest_seen:
        return _suggestion(
            "missed_implementation_structure",
            "medium",
            f"structural changes ({_short(sorted(structural))}) without a route manifest",
            session,
            "Select implementation-structure-design and record reuse and placement rationale.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_missed_reuse_evidence(session: SessionSummary) -> Suggestion | None:
    reuse = session.findings.get("reuse_findings", set())
    if reuse and session.stop_seen and not session.manifest_seen:
        return _suggestion(
            "missed_reuse_evidence",
            "medium",
            f"reuse-sensitive change ({_short(sorted(reuse))}) without reuse-ladder evidence",
            session,
            "Record the reuse ladder before adding helper/common/utils/shared/service/repository code.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_missed_language_capability(session: SessionSummary) -> Suggestion | None:
    if session.manifest_seen or not session.stop_seen:
        return None
    expected = _expected_language_capabilities(session.changed_paths)
    missing = sorted(expected - session.suggested_capabilities)
    if missing:
        return _suggestion(
            "missed_language_capability",
            "medium",
            f"language files changed without {_short(missing)} capability in the route",
            session,
            f"Select the matching language professional usage capability: {', '.join(missing)}.",
            "evals/routing",
        )
    return None


def _detect_missed_middleware_capability(session: SessionSummary) -> Suggestion | None:
    if not session.risk_surfaces or session.manifest_seen or not session.stop_seen:
        return None
    expectations = sorted(
        {
            MIDDLEWARE_EXPECTATION[surface]
            for surface in session.risk_surfaces
            if surface in MIDDLEWARE_EXPECTATION
        }
    )
    if expectations:
        return _suggestion(
            "missed_middleware_capability",
            "high",
            f"middleware risk surfaces {_short(sorted(session.risk_surfaces))} without a route manifest",
            session,
            f"Select the matching capability/gate: {', '.join(expectations)}.",
            "evals/routing",
        )
    return None


def _detect_missed_validation_evidence(session: SessionSummary) -> Suggestion | None:
    if session.stop_seen and session.has_code_change and not session.validation_seen:
        return _suggestion(
            "missed_validation_evidence",
            "high",
            "stop closure without validation evidence after a code change",
            session,
            "Run and report validation commands before final handoff.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_missed_residual_risk(session: SessionSummary) -> Suggestion | None:
    if session.stop_seen and session.has_code_change and not session.residual_risk_seen:
        return _suggestion(
            "missed_residual_risk",
            "medium",
            "stop closure without a residual-risk statement after a code change",
            session,
            "State residual risk and unverified items in the final handoff.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_possible_over_routing(session: SessionSummary) -> Suggestion | None:
    small_change = len(session.changed_paths) == 1 and not session.risk_surfaces
    no_structure = not session.structural_findings
    if small_change and no_structure and len(session.suggested_skills) >= 4:
        return _suggestion(
            "possible_over_routing",
            "low",
            f"single-file change suggested many skills ({_short(sorted(session.suggested_skills))})",
            session,
            "Confirm the route is minimum sufficient; add an L1 anti-over-routing case if not.",
            "evals/routing",
        )
    return None


def _detect_hook_false_positive(session: SessionSummary) -> Suggestion | None:
    flagged = [
        finding
        for finding in session.structural_findings
        if any(hint in finding.casefold() for hint in FALSE_POSITIVE_PATH_HINTS)
    ]
    if flagged and session.manifest_seen and session.validation_seen:
        return _suggestion(
            "hook_false_positive_candidate",
            "low",
            f"structure finding on test/fixture path with complete closure: {_short(flagged)}",
            session,
            "Review whether the structure gate over-matched a test/fixture path; add a fixture test.",
            "tests/fixtures/hooks",
        )
    return None


def _detect_hook_false_negative(session: SessionSummary) -> Suggestion | None:
    if session.risk_surfaces:
        return None
    risky = sorted(
        path
        for path in session.changed_paths
        if any(token in path.casefold() for token in HIGH_RISK_PATH_TOKENS)
    )
    if risky:
        return _suggestion(
            "hook_false_negative_candidate",
            "medium",
            f"high-risk path changed without any risk-surface finding: {_short(risky)}",
            session,
            "Review whether the risk surface gate should match this path; add a fixture test.",
            "tests/fixtures/hooks",
        )
    return None


def _is_missing_reference(session: SessionSummary) -> bool:
    return session.stop_seen and session.has_code_change and not session.references_seen


def _is_missing_gate(session: SessionSummary) -> bool:
    return bool(session.risk_surfaces) and session.stop_seen and not session.manifest_seen


def _count_metric(
    sessions: Any,
    predicate: Callable[[SessionSummary], bool],
) -> int:
    return sum(1 for session in sessions if predicate(session))


def _expected_language_capabilities(paths: set[str]) -> set[str]:
    expected: set[str] = set()
    for path in paths:
        suffix = Path(path).suffix.casefold()
        capability = LANGUAGE_CAPABILITY_BY_EXT.get(suffix)
        if capability:
            expected.add(capability)
    return expected


def _suggestion(
    issue_type: str,
    severity: str,
    evidence: str,
    session: SessionSummary,
    action: str,
    promotion_target: str,
) -> Suggestion:
    return Suggestion(
        suggestion_id="",
        type=issue_type,
        severity=severity,
        evidence=evidence,
        affected_session=session.session_id,
        suggested_action=action,
        promotion_target=promotion_target,
    )


def _suggestion_id(issue_type: str, session: SessionSummary, index: int) -> str:
    digest = hashlib.sha256(f"{session.session_id}:{session.repo_hash}".encode("utf-8")).hexdigest()[:6]
    return f"{issue_type.replace('_', '-')}-{digest}-{index}"


def _render_report(
    report_format: str,
    repo_hash: str,
    summary: dict[str, Any],
    suggestions: list[Suggestion],
) -> str:
    payload = {"summary": summary, "suggestions": [s.as_dict() for s in suggestions]}
    if report_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if report_format == "yaml":
        return dump_yaml(payload)
    return _render_markdown(repo_hash, summary, suggestions, payload)


def _render_markdown(
    repo_hash: str,
    summary: dict[str, Any],
    suggestions: list[Suggestion],
    payload: dict[str, Any],
) -> str:
    lines = [
        f"# ChangeForge Agent Telemetry Review ({repo_hash})",
        "",
        "Telemetry is a runtime fact log. This report is advisory; every suggestion",
        "requires human review before promotion. Nothing here mutates skills, routing",
        "rules, or capabilities.",
        "",
        "## Summary",
        "",
        f"- repo hash: {repo_hash}",
        f"- records: {summary['records']}",
        f"- sessions: {summary['sessions']}",
        f"- missed router: {summary['missed_router']}",
        f"- missed reference: {summary['missed_reference']}",
        f"- missed gate: {summary['missed_gate']}",
        f"- validation evidence missing: {summary['validation_evidence_missing']}",
        f"- residual risk missing: {summary['residual_risk_missing']}",
        f"- high severity suggestions: {summary['high_severity_suggestions']}",
        "",
        "## Issue Counts",
        "",
    ]
    if summary["issue_counts"]:
        for issue_type, count in sorted(summary["issue_counts"].items()):
            lines.append(f"- {issue_type}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Suggestions", ""])
    if suggestions:
        lines.append("| id | type | severity | promotion target | evidence |")
        lines.append("| --- | --- | --- | --- | --- |")
        for suggestion in suggestions:
            lines.append(
                f"| {suggestion.suggestion_id} | {suggestion.type} | {suggestion.severity} "
                f"| {suggestion.promotion_target} | {suggestion.evidence} |"
            )
    else:
        lines.append("No suggestions. Telemetry closure looks complete for the reviewed window.")
    lines.extend(
        [
            "",
            "## Machine-Readable Summary",
            "",
            "```json",
            json.dumps(payload["summary"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _render_suggestions(
    repo_hash: str,
    summary: dict[str, Any],
    suggestions: list[Suggestion],
    generated_at: str,
) -> str:
    data = {
        "generated_from_telemetry": True,
        "requires_human_review": True,
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "repo_hash": repo_hash,
        "generated_at": generated_at,
        "high_severity_suggestions": summary["high_severity_suggestions"],
        "suggestions": [s.as_dict() for s in suggestions],
    }
    header = (
        "# Generated by scripts/review-agent-telemetry.py from runtime telemetry.\n"
        "# These are human-review-only candidates. Do not auto-apply.\n"
    )
    return header + dump_yaml(data)


def _output_paths(
    root: Path,
    repo_hash: str,
    date_stamp: str,
    report_format: str,
    output_dir: Path | None,
) -> tuple[Path, Path]:
    extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[report_format]
    if output_dir is not None:
        base = output_dir.expanduser()
        report = base / f"{repo_hash}-{date_stamp}-agent-telemetry-review.{extension}"
        suggestions = base / f"{repo_hash}-{date_stamp}-suggestions.yaml"
        return report, suggestions
    repo_root = root / repo_hash
    report = repo_root / "reports" / f"{date_stamp}-agent-telemetry-review.{extension}"
    suggestions = repo_root / "suggestions" / f"{date_stamp}-suggestions.yaml"
    return report, suggestions


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _short(items: list[str], limit: int = 3) -> str:
    head = items[:limit]
    suffix = "" if len(items) <= limit else ", ..."
    return ", ".join(head) + suffix


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review ChangeForge agent telemetry and emit suggestions."
    )
    parser.add_argument("--telemetry-root", type=Path, default=None)
    parser.add_argument("--repo-hash", default=None)
    parser.add_argument("--since", default=None, help="ISO date/datetime lower bound.")
    parser.add_argument("--until", default=None, help="ISO date/datetime upper bound.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--format", choices=REPORT_FORMATS, default="markdown")
    parser.add_argument(
        "--fail-on-high-severity",
        action="store_true",
        help="Exit non-zero when high-severity suggestions exist (for CI).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
