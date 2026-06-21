#!/usr/bin/env python3
"""Generate a public, conservative benchmark summary from local evidence."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    LIVE_EVIDENCE_LEVEL,
    MODE_DEFAULT_VARIANTS,
    STRICT_AUTH_POLICIES,
    STRICT_BENCHMARK_MODES,
    STRICT_CODEX_ENVIRONMENT_POLICIES,
    public_status_from_live,
)
from validation_utils import EXPECTED_PROFILE_TOP_LEVEL_COUNTS


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
STATUS_ORDER = ("pass", "partial", "fail", "unknown", "not_collected")
COMMITTED_SOURCE_COMMIT = "provided by release artifact / CI metadata"
MARKETPLACE_DIMENSION = "Marketplace index validation"
SKILL_EFFICACY_DIMENSION = "Skill efficacy structural fixtures"
RUNTIME_GOVERNANCE_DIMENSION = "Runtime governance structural fixtures"
EXECUTOR_ADAPTER_DIMENSION = "Executor adapter structural fixtures"
ACTIVATION_PRECISION_DIMENSION = "Activation precision benchmark"
RUNTIME_TELEMETRY_FIXTURE_DIMENSION = "Runtime telemetry fixture sample"
LIVE_RUNTIME_TELEMETRY_DIMENSION = "Live runtime telemetry sample"
EXECUTOR_LIVE_PASS_RATE_DIMENSION = "Executor adapter live pass-rate"
EXECUTOR_TOKEN_OVERHEAD_DIMENSION = "Executor adapter token overhead"
EXECUTOR_TURN_OVERHEAD_DIMENSION = "Executor adapter turn overhead"
CODEX_LIVE_BENCHMARK_DIMENSION = "Codex CLI live benchmark"
HOOK_SAFETY_DIMENSION = "Hook safety"
INSTALLATION_VALIDATION_DIMENSION = "Installation validation"
SCORECARD_REFRESH_COMMAND = (
    "python3 scripts/generate-professional-scorecard.py "
    "--out reports/professional-scorecard.md "
    "--json-out reports/professional-scorecard.json"
)
REFRESH_COMMANDS = [
    "python3 scripts/eval-routing.py",
    "python3 scripts/eval-skill-professionalism.py",
    "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
    "python3 scripts/eval-professional-benchmarks.py",
    "python3 scripts/validate-skill-efficacy-benchmarks.py",
    "python3 scripts/eval-executor-adapters.py",
    "python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks",
    "python3 scripts/run-codex-live-benchmarks.py --list",
    "python3 scripts/run-codex-live-benchmarks.py --benchmark-mode clean-paired --auth-policy borrow-current --benchmark security/ssrf-url-allowlist --dry-run --out /tmp/changeforge-codex-live-borrow-auth-dry-run",
    "python3 scripts/validate-codex-live-benchmark-reports.py --run-dir /tmp/changeforge-codex-live-borrow-auth-dry-run",
    "python3 scripts/validate-professionalism-regression.py --strict",
    "python3 scripts/validate-professional-routing-coverage.py",
    "python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md",
    "python3 scripts/build.py --profile recommended",
    "python3 scripts/build.py --profile full",
    "python3 scripts/build.py --profile dev",
    "python3 scripts/validate-runtime-reference-links.py",
    "python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md",
    "python3 scripts/validate-marketplace-index.py --profile recommended",
    "python3 scripts/validate-marketplace-index.py --profile full",
    "python3 scripts/validate-marketplace-index.py --profile dev",
    "python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json",
]


@dataclass(frozen=True)
class EvidenceItem:
    """One summarized evidence row."""

    name: str
    status: str
    source: str
    detail: str
    command: str
    evidence_level: str = "structural fixture"


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _scorecard_path_and_source(root: Path, scorecard_path: Path | None) -> tuple[Path, str]:
    """Return the scorecard path to read and the source label to render."""
    path = scorecard_path or Path("reports") / "professional-scorecard.json"
    if not path.is_absolute():
        path = root / path
    try:
        source = path.relative_to(root).as_posix()
    except ValueError:
        source = str(path)
    return path, source


def _project_version(root: Path) -> str:
    path = root / "pyproject.toml"
    if not path.exists():
        return "unknown"
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return "unknown"
    project = parsed.get("project", {})
    return str(project.get("version", "unknown")) if isinstance(project, dict) else "unknown"


def _status_from_summary(summary: dict[str, Any] | None, *, pass_key: str = "cases_checked") -> str:
    if summary is None:
        return "unknown"
    if summary.get("quality_failures") or summary.get("fail") or summary.get("missing"):
        return "fail"
    statuses = summary.get("statuses")
    if isinstance(statuses, dict):
        if statuses.get("fail") or statuses.get("missing"):
            return "fail"
        if statuses.get("needs-review") or statuses.get("partial") or statuses.get("sample-grade"):
            return "partial"
    if summary.get(pass_key) or summary.get("count"):
        return "pass"
    return "unknown"


def _release_readiness_items(root: Path) -> list[EvidenceItem]:
    path = root / "reports" / "professionalism-release-readiness.json"
    readiness = _read_json(path)
    if not isinstance(readiness, dict):
        return [
            EvidenceItem(
            "Release readiness",
            "unknown",
            "reports/professionalism-release-readiness.json",
            "report missing or invalid",
            "python3 scripts/validate-professionalism-regression.py --strict",
            "structural fixture",
        )
        ]

    routing = readiness.get("routing_coverage_summary")
    skill = readiness.get("professional_skill_coverage_summary")
    foundation = readiness.get("key_foundation_capability_coverage_summary")
    strict = readiness.get("strict_regression_status")
    return [
        EvidenceItem(
            "Routing coverage",
            _status_from_summary(routing if isinstance(routing, dict) else None),
            "reports/professionalism-release-readiness.json",
            json.dumps(routing, sort_keys=True) if isinstance(routing, dict) else "routing summary missing",
            "python3 scripts/validate-professional-routing-coverage.py",
        ),
        EvidenceItem(
            "Professional skill coverage",
            _status_from_summary(skill if isinstance(skill, dict) else None, pass_key="count"),
            "reports/professionalism-release-readiness.json",
            json.dumps(skill, sort_keys=True) if isinstance(skill, dict) else "professional skill summary missing",
            "python3 scripts/eval-skill-professionalism.py",
        ),
        EvidenceItem(
            "Foundation capability coverage",
            _status_from_summary(foundation if isinstance(foundation, dict) else None, pass_key="count"),
            "reports/professionalism-release-readiness.json",
            json.dumps(foundation, sort_keys=True) if isinstance(foundation, dict) else "foundation coverage summary missing",
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
        ),
        EvidenceItem(
            "Strict regression",
            "pass" if strict == "pass" else ("fail" if strict in {"fail", "blocked"} else "unknown"),
            "reports/professionalism-release-readiness.json",
            f"strict_regression_status={strict}",
            "python3 scripts/validate-professionalism-regression.py --strict",
            "promoted golden case",
        ),
    ]


def _direct_report_items(root: Path) -> list[EvidenceItem]:
    skill_eval = _read_json(root / "reports" / "skill-professionalism-eval.json")
    coverage = _read_json(root / "reports" / "professional-coverage-matrix.json")
    return [
        EvidenceItem(
            "Skill professionalism report",
            "pass" if isinstance(skill_eval, dict) and skill_eval.get("items") else "unknown",
            "reports/skill-professionalism-eval.json",
            f"average_score={skill_eval.get('average_score')}" if isinstance(skill_eval, dict) else "report missing",
            "python3 scripts/eval-skill-professionalism.py",
        ),
        EvidenceItem(
            "Professional coverage matrix",
            "pass" if isinstance(coverage, dict) and coverage.get("rows") else "unknown",
            "reports/professional-coverage-matrix.json",
            f"rows={len(coverage.get('rows', []))}" if isinstance(coverage, dict) else "report missing",
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
        ),
    ]


def _profile_build_items(root: Path) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for profile in PROFILES:
        path = root / "dist" / "universal" / "skills" / profile / ".changeforge-build-manifest.json"
        manifest = _read_json(path)
        if not isinstance(manifest, dict):
            items.append(
                EvidenceItem(
                    f"Profile build: {profile}",
                    "unknown",
                    str(path.relative_to(root)),
                    "build manifest missing",
                    f"python3 scripts/build.py --profile {profile}",
                )
            )
            continue
        top_level = len(manifest.get("top_level_skills", []))
        expected = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
        status = "pass" if top_level == expected else "fail"
        items.append(
            EvidenceItem(
                f"Profile build: {profile}",
                status,
                str(path.relative_to(root)),
                f"top_level={top_level}, expected={expected}",
                f"python3 scripts/build.py --profile {profile}",
            )
        )
    return items


def _scorecard_dimension_item(
    root: Path,
    dimension_name: str,
    public_name: str,
    scorecard_path: Path | None = None,
    evidence_level: str = "structural fixture",
    missing_status: str = "unknown",
) -> EvidenceItem:
    """Return one public evidence item from the generated professional scorecard."""
    path, source = _scorecard_path_and_source(root, scorecard_path)
    scorecard = _read_json(path)
    if not isinstance(scorecard, dict):
        return EvidenceItem(
            public_name,
            missing_status,
            source,
            "scorecard report missing or invalid",
            SCORECARD_REFRESH_COMMAND,
        )

    dimensions = scorecard.get("dimensions")
    if not isinstance(dimensions, list):
        return EvidenceItem(
            public_name,
            missing_status,
            source,
            "scorecard dimensions missing or invalid",
            SCORECARD_REFRESH_COMMAND,
        )

    for dimension in dimensions:
        if not isinstance(dimension, dict) or dimension.get("name") != dimension_name:
            continue
        status = str(dimension.get("status", "unknown"))
        if status not in STATUS_ORDER:
            status = "unknown"
        return EvidenceItem(
            public_name,
            status,
            source,
            str(dimension.get("detail", "detail missing")),
            str(dimension.get("verification_command", "")) or SCORECARD_REFRESH_COMMAND,
            evidence_level,
        )

    return EvidenceItem(
        public_name,
        missing_status,
        source,
        f"{dimension_name} dimension missing",
        SCORECARD_REFRESH_COMMAND,
    )


def _codex_live_benchmark_item(root: Path) -> EvidenceItem:
    """Return public evidence directly from the published Codex live summary."""
    source = "reports/codex-live-benchmark-summary.json"
    summary = _read_json(root / source)
    if not isinstance(summary, dict):
        return EvidenceItem(
            CODEX_LIVE_BENCHMARK_DIMENSION,
            "not_collected",
            source,
            "Codex live benchmark summary missing or invalid",
            "python3 scripts/run-codex-live-benchmarks.py --list",
            LIVE_EVIDENCE_LEVEL,
        )
    status = public_status_from_live(str(summary.get("status", "not_collected")))
    strict_errors = _codex_live_strict_summary_errors(summary)
    if strict_errors:
        status = "fail"
    detail = {
        "evidence_level": summary.get("evidence_level"),
        "benchmark_mode": summary.get("benchmark_mode"),
        "auth_policy": summary.get("auth_policy"),
        "codex_environment_policy": summary.get("codex_environment_policy"),
        "strict_benchmark_eligible": summary.get("strict_benchmark_eligible"),
        "run_id": summary.get("run_id"),
        "case_count": summary.get("case_count"),
        "result_count": summary.get("result_count"),
        "benchmark_eligible_result_count": summary.get("benchmark_eligible_result_count"),
        "variants": {
            variant: {
                "pass_rate": payload.get("pass_rate"),
                "security_pass_rate": payload.get("security_pass_rate"),
                "benchmark_eligible_result_count": payload.get("benchmark_eligible_result_count"),
            }
            for variant, payload in (summary.get("variants") or {}).items()
            if isinstance(payload, dict)
        },
        "delta": summary.get("delta"),
        "strict_errors": strict_errors,
        "limitations": summary.get("limitations"),
    }
    return EvidenceItem(
        CODEX_LIVE_BENCHMARK_DIMENSION,
        status,
        source,
        json.dumps(detail, sort_keys=True),
        "python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json",
        LIVE_EVIDENCE_LEVEL,
    )


def _codex_live_strict_summary_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    benchmark_mode = summary.get("benchmark_mode")
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"evidence_level must be {LIVE_EVIDENCE_LEVEL}")
    if benchmark_mode not in STRICT_BENCHMARK_MODES:
        errors.append("benchmark_mode must be clean-paired or ablation")
    if summary.get("auth_policy") not in STRICT_AUTH_POLICIES:
        errors.append("auth_policy must be borrow-current or isolated-api-key")
    if summary.get("codex_environment_policy") not in STRICT_CODEX_ENVIRONMENT_POLICIES:
        errors.append("codex_environment_policy must be auth_borrowed_clean or isolated_api_key")
    if summary.get("strict_benchmark_eligible") is not True:
        errors.append("strict_benchmark_eligible must be true")
    if int(summary.get("current_home_result_count", 0) or 0) != 0 or int(
        summary.get("current_home_full_result_count", 0) or 0
    ) != 0:
        errors.append("current-home-full results are not public benchmark evidence")
    if summary.get("user_skills_visible") is not False:
        errors.append("user skills must not be visible")
    if summary.get("user_config_loaded") is not False:
        errors.append("user config must not be loaded")
    if summary.get("user_rules_loaded") is not False:
        errors.append("user rules must not be loaded")
    if summary.get("ignore_user_config") is not True or summary.get("ignore_rules") is not True:
        errors.append("--ignore-user-config and --ignore-rules are required")
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("contaminated results are not public benchmark evidence")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("assertion-backed eligible results are required")
    variants = summary.get("variants") or {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        payload = variants.get(variant)
        if not isinstance(payload, dict) or int(payload.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"eligible assertion results are required for {variant}")
    return errors


def _additional_status_items(root: Path, scorecard_path: Path | None = None) -> list[EvidenceItem]:
    return [
        _scorecard_dimension_item(
            root,
            HOOK_SAFETY_DIMENSION,
            HOOK_SAFETY_DIMENSION,
            scorecard_path,
            missing_status="not_collected",
        ),
        _scorecard_dimension_item(
            root,
            INSTALLATION_VALIDATION_DIMENSION,
            INSTALLATION_VALIDATION_DIMENSION,
            scorecard_path,
            missing_status="not_collected",
        ),
        _scorecard_dimension_item(root, SKILL_EFFICACY_DIMENSION, SKILL_EFFICACY_DIMENSION, scorecard_path),
        _scorecard_dimension_item(root, RUNTIME_GOVERNANCE_DIMENSION, RUNTIME_GOVERNANCE_DIMENSION, scorecard_path),
        _scorecard_dimension_item(root, EXECUTOR_ADAPTER_DIMENSION, EXECUTOR_ADAPTER_DIMENSION, scorecard_path),
        _scorecard_dimension_item(root, ACTIVATION_PRECISION_DIMENSION, ACTIVATION_PRECISION_DIMENSION, scorecard_path),
        _scorecard_dimension_item(
            root,
            RUNTIME_TELEMETRY_FIXTURE_DIMENSION,
            RUNTIME_TELEMETRY_FIXTURE_DIMENSION,
            scorecard_path,
            "runtime telemetry fixture sample",
        ),
        _scorecard_dimension_item(
            root,
            LIVE_RUNTIME_TELEMETRY_DIMENSION,
            LIVE_RUNTIME_TELEMETRY_DIMENSION,
            scorecard_path,
            "live runtime telemetry sample",
            missing_status="not_collected",
        ),
        _scorecard_dimension_item(
            root,
            EXECUTOR_LIVE_PASS_RATE_DIMENSION,
            EXECUTOR_LIVE_PASS_RATE_DIMENSION,
            scorecard_path,
            "live pass-rate",
        ),
        _scorecard_dimension_item(
            root,
            EXECUTOR_TOKEN_OVERHEAD_DIMENSION,
            EXECUTOR_TOKEN_OVERHEAD_DIMENSION,
            scorecard_path,
            "token overhead",
        ),
        _scorecard_dimension_item(
            root,
            EXECUTOR_TURN_OVERHEAD_DIMENSION,
            EXECUTOR_TURN_OVERHEAD_DIMENSION,
            scorecard_path,
            "turn overhead",
        ),
        _codex_live_benchmark_item(root),
        _scorecard_dimension_item(root, MARKETPLACE_DIMENSION, MARKETPLACE_DIMENSION, scorecard_path),
    ]


def generate_summary(
    root: Path,
    *,
    source_commit: str = COMMITTED_SOURCE_COMMIT,
    scorecard_path: Path | None = None,
) -> dict[str, Any]:
    """Generate the public benchmark summary payload."""
    items = [
        *_release_readiness_items(root),
        *_direct_report_items(root),
        *_profile_build_items(root),
        *_additional_status_items(root, scorecard_path),
    ]
    status_counts = {status: 0 for status in STATUS_ORDER}
    for item in items:
        status_counts[item.status] += 1
    evidence_levels = _scorecard_evidence_levels(root, scorecard_path)
    known_unknowns = _known_unknowns(items, evidence_levels)
    return {
        "schema_version": 1,
        "generated_by": "scripts/generate-public-benchmark-summary.py",
        "repository": {
            "name": "machenjie/rd-skills",
            "version": _project_version(root),
            "source_commit": source_commit,
        },
        "status_counts": status_counts,
        "items": [asdict(item) for item in items],
        "evidence_levels": evidence_levels,
        "known_unknowns": known_unknowns,
        "refresh_commands": REFRESH_COMMANDS,
        "claim_boundary": "Local deterministic evidence only; strict Codex live A/B claims may borrow Codex authentication, but must not borrow user skills, hooks, config, or rules. Current-home smoke evidence is not a baseline comparison. Skill efficacy, activation precision, and executor adapter fixtures are structural/local evidence, not live runtime telemetry, empirical before/after performance, external popularity, adoption, marketplace availability, or market claim evidence.",
    }


def _known_unknowns(
    items: list[EvidenceItem],
    evidence_levels: dict[str, dict[str, str]],
) -> list[str]:
    """Return de-duplicated unknown/not-collected item and evidence-level names."""
    names: list[str] = []
    for item in items:
        if item.status in {"unknown", "not_collected"}:
            names.append(_known_unknown_name(item.name))
    for level, detail in evidence_levels.items():
        if detail.get("status") in {"unknown", "not_collected"}:
            names.append(_known_unknown_name(level))
    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        deduped.append(name)
    return deduped


def _known_unknown_name(name: str) -> str:
    mapping = {
        "runtime telemetry fixture sample": "Runtime telemetry fixture sample",
        RUNTIME_TELEMETRY_FIXTURE_DIMENSION: "Runtime telemetry fixture sample",
        "live runtime telemetry sample": "Live runtime telemetry sample",
        LIVE_RUNTIME_TELEMETRY_DIMENSION: "Live runtime telemetry sample",
        "live pass-rate": "Live pass-rate",
        EXECUTOR_LIVE_PASS_RATE_DIMENSION: "Live pass-rate",
        "token overhead": "Token overhead",
        EXECUTOR_TOKEN_OVERHEAD_DIMENSION: "Token overhead",
        "turn overhead": "Turn overhead",
        EXECUTOR_TURN_OVERHEAD_DIMENSION: "Turn overhead",
        "local_codex_cli_live_benchmark": "Codex CLI live benchmark",
        CODEX_LIVE_BENCHMARK_DIMENSION: "Codex CLI live benchmark",
    }
    return mapping.get(name, name)


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the summary payload as Markdown."""
    repo = payload["repository"]
    lines = [
        "# Public Benchmark Summary",
        "",
        "This generated summary reports local deterministic ChangeForge evidence. Skill efficacy, activation precision, and executor adapter fixtures are structural/local evidence, not live runtime telemetry, live pass-rate, or empirical before/after agent-performance proof. It does not claim external popularity, marketplace availability, or market adoption.",
        "",
        "## Repository",
        "",
        f"- Repository: `{repo['name']}`",
        f"- Version: `{repo['version']}`",
        f"- Source commit: `{repo['source_commit']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in payload["status_counts"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Evidence Levels", "", "| Evidence | Status | Meaning |", "| --- | --- | --- |"])
    for level, detail in payload.get("evidence_levels", {}).items():
        lines.append(f"| {level} | `{detail.get('status', 'unknown')}` | {detail.get('meaning', '')} |")
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "| Area | Status | Evidence Level | Source | Detail | Refresh Command |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["items"]:
        lines.append(
            f"| {item['name']} | `{item['status']}` | {item.get('evidence_level', 'structural fixture')} | "
            f"{item['source']} | {item['detail']} | `{item['command']}` |"
        )
    lines.extend(["", "## Known Unknowns / Not Collected", ""])
    if payload["known_unknowns"]:
        for name in payload["known_unknowns"]:
            lines.append(f"- {name}")
    else:
        lines.append("- None")
    lines.extend(["", "## Refresh Commands", "", "```bash"])
    lines.extend(payload["refresh_commands"])
    lines.extend(["```", ""])
    return "\n".join(lines)


def _scorecard_evidence_levels(root: Path, scorecard_path: Path | None) -> dict[str, dict[str, str]]:
    path, _source = _scorecard_path_and_source(root, scorecard_path)
    scorecard = _read_json(path)
    if isinstance(scorecard, dict) and isinstance(scorecard.get("evidence_levels"), dict):
        return scorecard["evidence_levels"]
    return {
        "structural fixture": {
            "status": "unknown",
            "meaning": "Local deterministic structure sample passed; not evidence of live task success.",
        },
        "runtime telemetry fixture sample": {
            "status": "not_collected",
            "meaning": "Deterministic executor-adapter fixture-derived bounded facts; not live runtime telemetry.",
        },
        "live runtime telemetry sample": {
            "status": "not_collected",
            "meaning": "Sanitized bounded facts from an actual hook runtime execution.",
        },
        "promoted golden case": {
            "status": "unknown",
            "meaning": "Human-reviewed case admitted to regression coverage.",
        },
        "live pass-rate": {
            "status": "not_collected",
            "meaning": "Measured real-task success rate.",
        },
        "token overhead": {
            "status": "not_collected",
            "meaning": "Measured additional token cost.",
        },
        "turn overhead": {
            "status": "not_collected",
            "meaning": "Measured additional turn cost.",
        },
        "local_codex_cli_live_benchmark": {
            "status": "not_collected",
            "meaning": "Opt-in local Codex CLI benchmark run with sanitized bounded artifacts.",
        },
    }


def _check_file(path: Path, expected: str) -> list[str]:
    if not path.exists():
        return [f"{path} does not exist"]
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        return [f"{path} is stale"]
    return []


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for writing or checking public benchmark summaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument(
        "--source-commit",
        default=COMMITTED_SOURCE_COMMIT,
        help="Source commit metadata for release artifacts. Committed snapshots use a stable non-HEAD label.",
    )
    parser.add_argument(
        "--scorecard",
        help="Professional scorecard JSON used for scorecard-derived dimensions. Defaults to reports/professional-scorecard.json.",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    scorecard_path = Path(args.scorecard) if args.scorecard else None
    payload = generate_summary(ROOT, source_commit=args.source_commit, scorecard_path=scorecard_path)
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    md_text = render_markdown(payload)
    out = Path(args.out)
    json_out = Path(args.json_out)
    if args.check:
        errors = [*_check_file(out, md_text), *_check_file(json_out, json_text)]
        if errors:
            for error in errors:
                print(f"generate-public-benchmark-summary: ERROR: {error}", file=sys.stderr)
            return 1
        print("generate-public-benchmark-summary: committed outputs are fresh")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md_text, encoding="utf-8")
    json_out.write_text(json_text, encoding="utf-8")
    print(f"wrote public benchmark summary to {out} and {json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
