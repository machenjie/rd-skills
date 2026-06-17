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
from datetime import datetime, timedelta, timezone
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
DEFAULT_RECENCY_HALF_LIFE_DAYS = 2.0
RECENT_WINDOW = timedelta(hours=24)
SEVERITY_PRIORITY_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}
READ_ONLY_COMMAND_PROGRAMS = {
    "cat",
    "find",
    "grep",
    "head",
    "ls",
    "nl",
    "pwd",
    "rg",
    "sed",
    "stat",
    "tail",
    "tree",
    "wc",
}

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

# The four references the router must always declare for its own self-use.
ROUTER_SELF_REFERENCES = frozenset({
    "references/routing-rules.md",
    "references/skill-registry.md",
    "references/capability-index.md",
    "references/domain-extension-index.md",
})

# The completion-evidence detection family. Only unverified_completion_claim is
# detectable from fact-only telemetry today; the rest are surfaced through
# completion-evidence pressure evals and human review, because fact telemetry
# does not capture claim wording, per-command granularity, or delegation chains.
COMPLETION_EVIDENCE_DETECTION_TYPES = (
    "unverified_completion_claim",
    "success_language_without_evidence",
    "partial_validation_overclaimed",
    "stale_validation_reused",
    "delegated_agent_report_trusted_without_independent_check",
)

# Detection types a human may promote into a pressure scenario (evals/pressure)
# in addition to the suggestion's default routing or behavior-sample target.
PRESSURE_CANDIDATE_TYPES = frozenset({
    "missed_router",
    "missed_implementation_structure",
    "missed_validation_evidence",
    "validation_command_without_outcome",
    "missed_residual_risk",
    "unverified_completion_claim",
})

# Suggestion types that fire only because the route manifest did not name a
# capability. When the session emitted no route manifest at all, missed_router
# is the single actionable root cause and these are downstream cascades of that
# one gap; resolving the missing manifest is the prerequisite for assessing
# them. They stay primary when a manifest was present but simply omitted the
# capability, because that is a real, independently actionable manifest gap.
MANIFEST_DERIVED_SUGGESTION_TYPES = frozenset({
    "missed_implementation_structure",
    "missed_reuse_evidence",
    "missed_language_capability",
    "missed_middleware_capability",
})


@dataclass
class SessionSummary:
    """Aggregated telemetry facts for one session, used by issue detectors."""

    session_id: str
    repo_hash: str
    record_count: int = 0
    stop_seen: bool = False
    last_seen_at: datetime | None = None
    changed_paths: set[str] = field(default_factory=set)
    added_paths: set[str] = field(default_factory=set)
    risk_surfaces: set[str] = field(default_factory=set)
    changed_path_risk_surfaces: set[str] = field(default_factory=set)
    command_risk_surfaces: set[str] = field(default_factory=set)
    closure_risk_surfaces: set[str] = field(default_factory=set)
    risk_surface_split_seen: bool = False
    command_programs: set[str] = field(default_factory=set)
    suggested_skills: set[str] = field(default_factory=set)
    suggested_capabilities: set[str] = field(default_factory=set)
    suggested_gates: set[str] = field(default_factory=set)
    findings: dict[str, set[str]] = field(default_factory=dict)
    manifest_seen: bool = False
    validation_command_seen: bool = False
    validation_seen: bool = False
    residual_risk_seen: bool = False
    references_seen: bool = False
    completion_language_seen: bool = False
    stage_manifest_seen: bool = False
    manifest_current_stage: str = ""
    manifest_selected_skills: set[str] = field(default_factory=set)
    manifest_selected_capabilities: set[str] = field(default_factory=set)
    manifest_selected_domain_extensions: set[str] = field(default_factory=set)
    manifest_required_references: set[str] = field(default_factory=set)
    manifest_required_quality_gates: set[str] = field(default_factory=set)
    manifest_skipped_quality_gates: set[str] = field(default_factory=set)

    @property
    def has_code_change(self) -> bool:
        return bool(self.changed_paths or self.structural_findings)

    @property
    def effective_risk_surfaces(self) -> set[str]:
        """Risk surfaces that should be treated as engineering closure facts."""
        if self.closure_risk_surfaces:
            return set(self.closure_risk_surfaces)
        if self.changed_path_risk_surfaces:
            return set(self.changed_path_risk_surfaces)
        if self.risk_surface_split_seen:
            return set()
        if self.changed_paths or self.structural_findings or self._legacy_mutating_command_seen:
            return set(self.risk_surfaces)
        return set()

    @property
    def has_engineering_surface(self) -> bool:
        return self.has_code_change or bool(self.effective_risk_surfaces)

    @property
    def read_only_command_risk_surfaces(self) -> set[str]:
        if self.risk_surface_split_seen:
            return self.command_risk_surfaces - self.effective_risk_surfaces
        if self.risk_surfaces and not self.has_code_change and self._legacy_read_only_command_seen:
            return set(self.risk_surfaces)
        return set()

    @property
    def is_non_trivial(self) -> bool:
        """A change that should carry a stage manifest, not a single trivial edit."""
        return len(self.changed_paths) > 1 or bool(self.effective_risk_surfaces) or bool(
            self.structural_findings
        )

    @property
    def manifest_selected(self) -> set[str]:
        """Capabilities and domain extensions the route manifest actually named."""
        return self.manifest_selected_capabilities | self.manifest_selected_domain_extensions

    @property
    def structural_findings(self) -> set[str]:
        merged: set[str] = set()
        for key in STRUCTURE_FINDING_KEYS:
            merged.update(self.findings.get(key, set()))
        return merged

    @property
    def _legacy_read_only_command_seen(self) -> bool:
        return bool(self.command_programs) and all(
            program.casefold() in READ_ONLY_COMMAND_PROGRAMS
            for program in self.command_programs
        )

    @property
    def _legacy_mutating_command_seen(self) -> bool:
        return any(
            program.casefold() not in READ_ONLY_COMMAND_PROGRAMS
            for program in self.command_programs
        )


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
    pressure_candidate: bool = False
    cascading: bool = False
    cascading_from: str = ""
    session_last_timestamp_utc: str = ""
    recency_weight: float = 1.0
    priority_score: float = 0.0
    recent_24h: bool = False

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
            "pressure_candidate": self.pressure_candidate,
            "cascading": self.cascading,
            "cascading_from": self.cascading_from,
            "session_last_timestamp_utc": self.session_last_timestamp_utc,
            "recency_weight": self.recency_weight,
            "priority_score": self.priority_score,
            "recent_24h": self.recent_24h,
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
        summary, suggestions = _analyze_repo(
            root,
            repo_hash,
            since,
            until,
            recency_half_life_days=args.recency_half_life_days,
        )
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
    *,
    recency_half_life_days: float,
) -> tuple[dict[str, Any], list[Suggestion]]:
    records = list(iter_session_records(root, repo_hash, since=since, until=until))
    sessions = _session_summaries(records, repo_hash)
    suggestions: list[Suggestion] = []
    for session in sessions.values():
        suggestions.extend(_detect_issues(session))
    latest_seen_at = _latest_seen_at(sessions.values())
    _apply_recency_scores(suggestions, sessions, latest_seen_at, recency_half_life_days)

    issue_counts: dict[str, int] = {}
    for suggestion in suggestions:
        issue_counts[suggestion.type] = issue_counts.get(suggestion.type, 0) + 1

    code_change_closures = sum(
        1 for session in sessions.values() if session.stop_seen and session.has_code_change
    )
    engineering_surface_closures = sum(
        1
        for session in sessions.values()
        if session.stop_seen and session.has_engineering_surface
    )
    risk_surface_closures = sum(
        1
        for session in sessions.values()
        if session.stop_seen and session.effective_risk_surfaces
    )
    read_only_risk_surface_closures = sum(
        1
        for session in sessions.values()
        if session.stop_seen
        and session.read_only_command_risk_surfaces
        and not session.has_engineering_surface
    )
    route_manifest_closures = sum(
        1
        for session in sessions.values()
        if session.stop_seen and session.has_engineering_surface and session.manifest_seen
    )
    route_manifest_adoption = (
        round(route_manifest_closures / engineering_surface_closures, 4)
        if engineering_surface_closures
        else 0.0
    )
    weighted_issue_scores = _weighted_issue_scores(suggestions)
    recent_24h_issue_counts = _recent_issue_counts(suggestions)

    summary = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "repo_hash": repo_hash,
        "records": len(records),
        "sessions": len(sessions),
        "latest_timestamp_utc": latest_seen_at.isoformat() if latest_seen_at else "",
        "recency_half_life_days": recency_half_life_days,
        "code_change_closures": code_change_closures,
        "engineering_surface_closures": engineering_surface_closures,
        "risk_surface_closures": risk_surface_closures,
        "read_only_risk_surface_closures": read_only_risk_surface_closures,
        "route_manifest_closures": route_manifest_closures,
        "route_manifest_adoption": route_manifest_adoption,
        "missed_router": issue_counts.get("missed_router", 0),
        "missed_reference": _count_metric(sessions.values(), _is_missing_reference),
        "incomplete_required_references": _count_metric(
            sessions.values(), _is_incomplete_required_references
        ),
        "missed_gate": _count_metric(sessions.values(), _is_missing_gate),
        "validation_evidence_missing": issue_counts.get("missed_validation_evidence", 0),
        "validation_command_without_outcome": issue_counts.get(
            "validation_command_without_outcome", 0
        ),
        "unverified_completion_claims": issue_counts.get("unverified_completion_claim", 0),
        "residual_risk_missing": issue_counts.get("missed_residual_risk", 0),
        "pressure_candidate_suggestions": sum(1 for s in suggestions if s.pressure_candidate),
        "primary_suggestions": sum(1 for s in suggestions if not s.cascading),
        "cascading_suggestions": sum(1 for s in suggestions if s.cascading),
        "high_severity_suggestions": sum(1 for s in suggestions if s.severity == "high"),
        "issue_counts": issue_counts,
        "weighted_issue_scores": weighted_issue_scores,
        "recent_24h_issue_counts": recent_24h_issue_counts,
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
        timestamp = parse_iso_datetime(str(record.get("timestamp_utc") or ""))
        if timestamp and (session.last_seen_at is None or timestamp > session.last_seen_at):
            session.last_seen_at = timestamp
        session.changed_paths.update(_string_list(record.get("changed_paths")))
        session.added_paths.update(_string_list(record.get("added_paths")))
        session.risk_surfaces.update(_string_list(record.get("risk_surfaces")))
        changed_path_risk_surfaces = _string_list(record.get("changed_path_risk_surfaces"))
        command_risk_surfaces = _string_list(record.get("command_risk_surfaces"))
        closure_risk_surfaces = _string_list(record.get("closure_risk_surfaces"))
        if changed_path_risk_surfaces or command_risk_surfaces or closure_risk_surfaces:
            session.risk_surface_split_seen = True
        session.changed_path_risk_surfaces.update(changed_path_risk_surfaces)
        session.command_risk_surfaces.update(command_risk_surfaces)
        session.closure_risk_surfaces.update(closure_risk_surfaces)
        command_program = str(record.get("command_program") or "").strip()
        if command_program:
            session.command_programs.add(command_program)
        session.validation_command_seen |= bool(record.get("validation_command_detected"))
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
            session.completion_language_seen |= bool(
                record.get("completion_language_detected")
            )
            session.stage_manifest_seen |= bool(record.get("stage_manifest_detected"))
            stage = record.get("manifest_current_stage")
            if isinstance(stage, str) and stage.strip():
                session.manifest_current_stage = stage.strip()
            session.manifest_selected_skills.update(
                _string_list(record.get("manifest_selected_skills"))
            )
            session.manifest_selected_capabilities.update(
                _string_list(record.get("manifest_selected_capabilities"))
            )
            session.manifest_selected_domain_extensions.update(
                _string_list(record.get("manifest_selected_domain_extensions"))
            )
            session.manifest_required_references.update(
                _string_list(record.get("manifest_required_references"))
            )
            session.manifest_required_quality_gates.update(
                _string_list(record.get("manifest_required_quality_gates"))
            )
            session.manifest_skipped_quality_gates.update(
                _string_list(record.get("manifest_skipped_quality_gates"))
            )
    return sessions


def _detect_issues(session: SessionSummary) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    detectors: tuple[Callable[[SessionSummary], Suggestion | None], ...] = (
        _detect_missed_router,
        _detect_missed_implementation_structure,
        _detect_missed_reuse_evidence,
        _detect_missed_language_capability,
        _detect_missed_middleware_capability,
        _detect_missed_stage_manifest,
        _detect_missed_validation_evidence,
        _detect_validation_command_without_outcome,
        _detect_unverified_completion_claim,
        _detect_missed_residual_risk,
        _detect_possible_over_routing,
        _detect_hook_false_positive,
        _detect_hook_false_negative,
        _detect_incomplete_required_references,
    )
    for index, detector in enumerate(detectors):
        result = detector(session)
        if result is not None:
            result.suggestion_id = _suggestion_id(result.type, session, index)
            suggestions.append(result)
    # A session that emitted no route manifest already raises missed_router as
    # its root cause. The capability/structure/reuse gaps it also raises are
    # downstream of that one missing manifest, so mark them as cascading rather
    # than counting them as independent, separately actionable findings.
    if not session.manifest_seen:
        for suggestion in suggestions:
            if suggestion.type in MANIFEST_DERIVED_SUGGESTION_TYPES:
                suggestion.cascading = True
                suggestion.cascading_from = "missed_router"
    return suggestions


def _detect_missed_router(session: SessionSummary) -> Suggestion | None:
    if session.stop_seen and session.has_engineering_surface and not session.manifest_seen:
        return _suggestion(
            "missed_router",
            "high",
            f"{len(session.changed_paths)} changed path(s), {len(session.effective_risk_surfaces)} closure risk surface(s), but no changeforge_route manifest at stop",
            session,
            "Require change-forge-router and a changeforge_route manifest for this change.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_missed_implementation_structure(session: SessionSummary) -> Suggestion | None:
    structural = session.structural_findings
    if not (structural and session.stop_seen):
        return None
    if "implementation-structure-design" in session.manifest_selected_capabilities:
        return None
    detail = (
        "route manifest omits implementation-structure-design"
        if session.manifest_seen
        else "no route manifest"
    )
    return _suggestion(
        "missed_implementation_structure",
        "medium",
        f"structural changes ({_short(sorted(structural))}) but {detail}",
        session,
        "Select implementation-structure-design and record reuse and placement rationale.",
        "evals/agent-behavior/samples",
    )


def _detect_missed_reuse_evidence(session: SessionSummary) -> Suggestion | None:
    reuse = session.findings.get("reuse_findings", set())
    if not (reuse and session.stop_seen):
        return None
    if "implementation-structure-design" in session.manifest_selected_capabilities:
        return None
    detail = (
        "route manifest omits implementation-structure-design"
        if session.manifest_seen
        else "no reuse-ladder evidence"
    )
    return _suggestion(
        "missed_reuse_evidence",
        "medium",
        f"reuse-sensitive change ({_short(sorted(reuse))}) with {detail}",
        session,
        "Record the reuse ladder before adding helper/common/utils/shared/service/repository code.",
        "evals/agent-behavior/samples",
    )


def _detect_missed_language_capability(session: SessionSummary) -> Suggestion | None:
    if not session.stop_seen:
        return None
    expected = _expected_language_capabilities(session.changed_paths)
    if not expected:
        return None
    missing = sorted(expected - session.manifest_selected_capabilities)
    if not missing:
        return None
    detail = "route manifest omits" if session.manifest_seen else "no route manifest selects"
    return _suggestion(
        "missed_language_capability",
        "medium",
        f"language files changed but {detail} {_short(missing)}",
        session,
        f"Select the matching language professional usage capability: {', '.join(missing)}.",
        "evals/routing",
    )


def _detect_missed_middleware_capability(session: SessionSummary) -> Suggestion | None:
    risk_surfaces = session.effective_risk_surfaces
    if not risk_surfaces or not session.stop_seen:
        return None
    expectations = {
        MIDDLEWARE_EXPECTATION[surface]
        for surface in risk_surfaces
        if surface in MIDDLEWARE_EXPECTATION
    }
    missing = sorted(expectations - session.manifest_selected)
    if not missing:
        return None
    detail = "route manifest omits" if session.manifest_seen else "no route manifest selects"
    return _suggestion(
        "missed_middleware_capability",
        "high",
        f"middleware risk surfaces {_short(sorted(risk_surfaces))} but {detail} {_short(missing)}",
        session,
        f"Select the matching capability/gate: {', '.join(missing)}.",
        "evals/routing",
    )


def _detect_missed_stage_manifest(session: SessionSummary) -> Suggestion | None:
    if not (session.stop_seen and session.manifest_seen):
        return None
    if session.stage_manifest_seen or not session.is_non_trivial:
        return None
    return _suggestion(
        "missed_stage_manifest",
        "medium",
        "non-trivial change emitted changeforge_route but no changeforge_stage_route",
        session,
        "Emit a changeforge_stage_route naming the current stage and explicitly skipped capabilities.",
        "evals/agent-behavior/samples",
    )


def _detect_missed_validation_evidence(session: SessionSummary) -> Suggestion | None:
    if (
        session.stop_seen
        and session.has_engineering_surface
        and not session.validation_command_seen
        and not session.validation_seen
    ):
        return _suggestion(
            "missed_validation_evidence",
            "high",
            "stop closure without any observed validation command or validation evidence",
            session,
            "Run and report validation commands before final handoff.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_validation_command_without_outcome(session: SessionSummary) -> Suggestion | None:
    if (
        session.stop_seen
        and session.has_engineering_surface
        and session.validation_command_seen
        and not session.validation_seen
    ):
        return _suggestion(
            "validation_command_without_outcome",
            "high",
            "validation-looking command was observed but stop closure reported no outcome",
            session,
            "Report the validation command outcome, exit code, output summary, or artifact before claiming completion.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_missed_residual_risk(session: SessionSummary) -> Suggestion | None:
    if session.stop_seen and session.has_engineering_surface and not session.residual_risk_seen:
        return _suggestion(
            "missed_residual_risk",
            "medium",
            "stop closure without a residual-risk statement after a code change",
            session,
            "State residual risk and unverified items in the final handoff.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_unverified_completion_claim(session: SessionSummary) -> Suggestion | None:
    """Completion language at stop with a code change but no validation evidence.

    This is the fact-detectable member of the completion-evidence family
    (see COMPLETION_EVIDENCE_DETECTION_TYPES). The presence-only completion
    signal comes from the Stop gate; this detector pairs it with the absence of
    validation evidence. It never reads prompts or output, only recorded facts.
    """
    if (
        session.stop_seen
        and session.has_engineering_surface
        and session.completion_language_seen
        and not session.validation_seen
    ):
        return _suggestion(
            "unverified_completion_claim",
            "high",
            "stop closure used completion language but recorded no validation evidence",
            session,
            "Bind the completion claim to a fresh validation command and outcome, or "
            "replace it with a not-verified disclosure (status, why not run, residual "
            "risk, exact command). Route through agent-execution-discipline and "
            "quality-test-gate.",
            "evals/agent-behavior/samples",
        )
    return None


def _detect_possible_over_routing(session: SessionSummary) -> Suggestion | None:
    small_change = len(session.changed_paths) == 1 and not session.effective_risk_surfaces
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
    if session.effective_risk_surfaces:
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
    return session.stop_seen and session.has_engineering_surface and not session.references_seen


def _is_incomplete_required_references(session: SessionSummary) -> bool:
    """True when references were seen but one or more router self-references are absent."""
    if not (session.stop_seen and session.has_engineering_surface and session.references_seen):
        return False
    return not ROUTER_SELF_REFERENCES.issubset(session.manifest_required_references)


def _detect_incomplete_required_references(session: SessionSummary) -> Suggestion | None:
    if not (session.stop_seen and session.has_engineering_surface and session.references_seen):
        return None
    missing = sorted(ROUTER_SELF_REFERENCES - session.manifest_required_references)
    if not missing:
        return None
    return _suggestion(
        "incomplete_required_references",
        "medium",
        "route manifest required_references missing router self-reference(s): " + _short(missing),
        session,
        "Add all four router self-use references to required_references in the changeforge_route manifest.",
        "evals/agent-behavior/samples",
    )


def _is_missing_gate(session: SessionSummary) -> bool:
    if not (session.effective_risk_surfaces and session.stop_seen):
        return False
    return not session.manifest_required_quality_gates and not session.manifest_skipped_quality_gates


def _count_metric(
    sessions: Any,
    predicate: Callable[[SessionSummary], bool],
) -> int:
    return sum(1 for session in sessions if predicate(session))


def _latest_seen_at(sessions: Any) -> datetime | None:
    latest: datetime | None = None
    for session in sessions:
        if session.last_seen_at and (latest is None or session.last_seen_at > latest):
            latest = session.last_seen_at
    return latest


def _apply_recency_scores(
    suggestions: list[Suggestion],
    sessions: dict[str, SessionSummary],
    latest_seen_at: datetime | None,
    half_life_days: float,
) -> None:
    for suggestion in suggestions:
        session = sessions.get(suggestion.affected_session)
        last_seen_at = session.last_seen_at if session else None
        suggestion.session_last_timestamp_utc = last_seen_at.isoformat() if last_seen_at else ""
        weight = _recency_weight(last_seen_at, latest_seen_at, half_life_days)
        suggestion.recency_weight = round(weight, 4)
        severity_weight = SEVERITY_PRIORITY_WEIGHT.get(suggestion.severity, 1.0)
        suggestion.priority_score = round(weight * severity_weight, 4)
        suggestion.recent_24h = bool(
            latest_seen_at
            and last_seen_at
            and latest_seen_at - last_seen_at <= RECENT_WINDOW
        )


def _recency_weight(
    timestamp: datetime | None,
    latest_seen_at: datetime | None,
    half_life_days: float,
) -> float:
    if timestamp is None or latest_seen_at is None or half_life_days <= 0:
        return 1.0
    age_days = max((latest_seen_at - timestamp).total_seconds() / 86400.0, 0.0)
    return 0.5 ** (age_days / half_life_days)


def _weighted_issue_scores(suggestions: list[Suggestion]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for suggestion in suggestions:
        scores[suggestion.type] = round(
            scores.get(suggestion.type, 0.0) + suggestion.priority_score,
            4,
        )
    return dict(sorted(scores.items(), key=lambda item: (-item[1], item[0])))


def _recent_issue_counts(suggestions: list[Suggestion]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for suggestion in suggestions:
        if not suggestion.recent_24h:
            continue
        counts[suggestion.type] = counts.get(suggestion.type, 0) + 1
    return dict(sorted(counts.items()))


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
        pressure_candidate=issue_type in PRESSURE_CANDIDATE_TYPES,
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
        f"- latest timestamp: {summary['latest_timestamp_utc'] or 'unknown'}",
        f"- recency half-life days: {summary['recency_half_life_days']}",
        f"- code change closures: {summary['code_change_closures']}",
        f"- engineering surface closures: {summary['engineering_surface_closures']}",
        f"- risk surface closures: {summary['risk_surface_closures']}",
        f"- read-only risk surface closures: {summary['read_only_risk_surface_closures']}",
        f"- route manifest adoption: {_format_adoption(summary)}",
        f"- missed router: {summary['missed_router']}",
        f"- missed reference: {summary['missed_reference']}",
        f"- incomplete required references: {summary['incomplete_required_references']}",
        f"- missed gate: {summary['missed_gate']}",
        f"- validation evidence missing: {summary['validation_evidence_missing']}",
        f"- validation command without outcome: {summary['validation_command_without_outcome']}",
        f"- unverified completion claims: {summary['unverified_completion_claims']}",
        f"- residual risk missing: {summary['residual_risk_missing']}",
        f"- pressure candidate suggestions: {summary['pressure_candidate_suggestions']}",
        f"- primary suggestions: {summary['primary_suggestions']}",
        f"- cascading suggestions: {summary['cascading_suggestions']}",
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
    lines.extend(["", "## Recency Weighted Scores", ""])
    if summary["weighted_issue_scores"]:
        for issue_type, score in summary["weighted_issue_scores"].items():
            recent = summary["recent_24h_issue_counts"].get(issue_type, 0)
            lines.append(f"- {issue_type}: priority {score:g}, recent 24h {recent}")
    else:
        lines.append("- none")
    lines.extend(["", "## Suggestions", ""])
    if not suggestions:
        lines.append("No suggestions. Telemetry closure looks complete for the reviewed window.")
    else:
        primary = [s for s in suggestions if not s.cascading]
        cascading = [s for s in suggestions if s.cascading]
        lines.append(
            "Primary suggestions are independently actionable root causes. Cascading "
            "suggestions exist only because the session emitted no route manifest; fix "
            "the missing route manifest (missed_router) first and they clear together."
        )
        lines.extend(["", f"### Primary ({len(primary)})", ""])
        lines.extend(_suggestion_table(primary))
        lines.extend(
            ["", f"### Cascading from a missing route manifest ({len(cascading)})", ""]
        )
        lines.extend(_suggestion_table(cascading))
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


def _format_adoption(summary: dict[str, Any]) -> str:
    """Render route-manifest adoption as ``present/closures (NN%)``."""
    closures = int(summary.get("engineering_surface_closures", 0) or 0)
    present = int(summary.get("route_manifest_closures", 0) or 0)
    rate = float(summary.get("route_manifest_adoption", 0.0) or 0.0)
    return f"{present}/{closures} ({rate * 100:.0f}%)"


def _suggestion_table(suggestions: list[Suggestion]) -> list[str]:
    if not suggestions:
        return ["None."]
    rows = [
        "| id | type | severity | priority | promotion target | evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for suggestion in suggestions:
        rows.append(
            f"| {suggestion.suggestion_id} | {suggestion.type} | {suggestion.severity} "
            f"| {suggestion.priority_score:g} | {suggestion.promotion_target} | {suggestion.evidence} |"
        )
    return rows


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
        "--recency-half-life-days",
        type=float,
        default=DEFAULT_RECENCY_HALF_LIFE_DAYS,
        help="Half-life in days for priority_score weighting. Use 0 to disable decay.",
    )
    parser.add_argument(
        "--fail-on-high-severity",
        action="store_true",
        help="Exit non-zero when high-severity suggestions exist (for CI).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
