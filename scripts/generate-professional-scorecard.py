#!/usr/bin/env python3
"""Generate a conservative professional scorecard from local evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    CODEX_LIVE_CAPABILITY_COVERAGE_NAME,
    CODEX_LIVE_PASS_RATE_BENCHMARK_NAME,
    LIVE_EVIDENCE_LEVEL,
    codex_live_capability_coverage_status,
    codex_live_capability_repair_hints,
    codex_live_compact_detail,
    codex_live_pass_rate_status,
    codex_live_repair_hints,
)
from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    load_yaml_file,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
STATUSES = ("pass", "partial", "fail", "unknown", "not_collected")
EVIDENCE_LEVELS = {
    "structural fixture": "Local deterministic structure sample passed; not evidence of live task success.",
    "runtime telemetry fixture sample": "Deterministic executor-adapter fixture-derived bounded facts; not live runtime telemetry.",
    "live runtime telemetry sample": "Sanitized bounded facts from an actual hook runtime execution.",
    "promoted golden case": "Human-reviewed case admitted to regression coverage.",
    "live pass-rate": "Measured real-task success rate.",
    "token overhead": "Measured additional token cost.",
    "turn overhead": "Measured additional turn cost.",
    "local_codex_cli_live_benchmark": "Opt-in local Codex CLI benchmark run with sanitized bounded artifacts.",
}
RUNTIME_GOVERNANCE_FIXTURE_SUITES = {
    "executor-adapters": "executor-adapter-protocol",
    "repository-intelligence": "repository-graph-analysis",
    "project-memory": "project-memory-governance",
    "validation-broker": "validation-broker",
    "trajectory": "execution-trajectory-analysis",
}
CONTEXT_CONTROL_OVERHEAD_DIMENSION = "context_control_overhead"
HIGH_CONTEXT_INPUT_TOKEN_OVERHEAD_PCT = 100.0
HIGH_CONTEXT_OUTPUT_TOKEN_OVERHEAD_PCT = 25.0
STRICT_PROFILE_BUILD_DIMENSIONS = (
    "Registry source counts",
    "Profile build reproducibility",
    "Example coverage",
    "Productization assets",
)
PRODUCTIZATION_ASSETS = (
    "docs/QUICKSTART.md",
    "docs/BENCHMARKS.md",
    "docs/SCORECARD.md",
    "docs/SCORECARD_DASHBOARD.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
    "docs/COMPARISON.md",
    "docs/OPEN_SOURCE_READINESS.md",
    "docs/LICENSE_DECISION.md",
    "reports/README.md",
    "reports/professional-scorecard.md",
    "reports/professional-scorecard.json",
    "reports/executor-adapter-eval.md",
    "reports/executor-adapter-eval.json",
    "reports/activation-precision.md",
    "reports/activation-precision.json",
    "reports/runtime-telemetry-sample.json",
    "reports/hook-validation.md",
    "reports/hook-validation.json",
    "reports/installation-validation.md",
    "reports/installation-validation.json",
    "reports/public-benchmark-summary.md",
    "reports/public-benchmark-summary.json",
    "reports/context-control-plane-eval.md",
    "reports/context-control-plane-eval.json",
    "config/open-source-release.yaml",
    "schemas/marketplace-index.schema.json",
    "scripts/generate-professional-scorecard.py",
    "scripts/eval-context-control-plane.py",
    "scripts/eval-executor-adapters.py",
    "scripts/eval-activation-precision.py",
    "scripts/generate-public-benchmark-summary.py",
    "scripts/generate-examples-showcase.py",
    "scripts/generate-marketplace-catalog.py",
    "scripts/render-scorecard-dashboard.py",
    "scripts/quickstart.py",
    "scripts/validate-open-source-readiness.py",
    "scripts/export-marketplace-index.py",
    "scripts/validate-marketplace-index.py",
    "scripts/validate-examples.py",
)


VALIDATION_COMMANDS = [
    "python3 scripts/validate-skills.py",
    "python3 scripts/validate-capabilities.py",
    "python3 scripts/validate-domain-extensions.py",
    "python3 scripts/validate-registry.py",
    "python3 scripts/validate-skill-body-links.py",
    "python3 scripts/validate-skill-content-size.py",
    "python3 scripts/validate-skill-efficacy-benchmarks.py",
    "python3 scripts/eval-context-control-plane.py",
    "python3 scripts/eval-executor-adapters.py",
    "python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks",
    "python3 scripts/audit-skill-content.py",
    "python3 scripts/eval-routing.py",
    "python3 scripts/eval-agent-behavior.py",
    "python3 scripts/eval-skill-professionalism.py",
    "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
    "python3 scripts/eval-professional-benchmarks.py",
    "python3 scripts/validate-professionalism-regression.py",
    "python3 scripts/validate-professionalism-regression.py --strict",
    "python3 scripts/validate-professional-routing-coverage.py",
    "python3 scripts/validate-stage-routing-architecture.py",
    "python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md",
    "python3 scripts/eval-pressure-behavior.py",
    "python3 -m unittest discover -s tests",
    "python3 scripts/validate-codegen-benchmarks.py",
    "python3 scripts/run-codegen-benchmarks.py --limit 3",
    "python3 scripts/run-codex-live-benchmarks.py --list",
    "python3 scripts/run-codex-live-benchmarks.py --benchmark-mode ablation --auth-policy borrow-current --benchmark security/ssrf-url-allowlist --dry-run --out /tmp/changeforge-codex-live-ablation-dry-run",
    "python3 scripts/validate-codex-live-benchmark-reports.py --run-dir /tmp/changeforge-codex-live-ablation-dry-run",
    "python3 scripts/validate-report-consistency.py",
    "python3 scripts/build.py --profile recommended",
    "python3 scripts/build.py --profile full",
    "python3 scripts/build.py --profile dev",
    "python3 scripts/validate-runtime-reference-links.py",
    "python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md",
    "python3 scripts/validate-marketplace-index.py --profile recommended",
    "python3 scripts/validate-marketplace-index.py --profile full",
    "python3 scripts/validate-marketplace-index.py --profile dev",
    "python3 scripts/validate-examples.py",
    "python3 scripts/validate-productization-assets.py",
    "python3 scripts/validate-open-source-readiness.py",
    "python3 scripts/generate-public-benchmark-summary.py --check --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json",
    "python3 scripts/generate-examples-showcase.py --check --out docs/SHOWCASE.md",
    "python3 scripts/generate-marketplace-catalog.py --profile recommended --check --out docs/MARKETPLACE_CATALOG.md",
    "python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md --check",
]


@dataclass
class Dimension:
    name: str
    status: str
    source: str
    verification_command: str
    fix_hint: str
    detail: str

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"invalid status for {self.name}: {self.status}")


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _source_counts(root: Path) -> dict[str, int]:
    skills = load_yaml_file(root / "src" / "registry" / "skills.yaml").get("skills", [])
    capabilities = load_yaml_file(root / "src" / "registry" / "capabilities.yaml").get("capabilities", [])
    extensions = load_yaml_file(root / "src" / "registry" / "domain-extensions.yaml").get("domain_extensions", [])
    return {
        "professional_skills": len(skills),
        "foundation_capabilities": len(capabilities),
        "domain_extensions": len(extensions),
    }


def profile_manifest_status(manifest: dict[str, Any] | None, profile: str) -> tuple[str, str]:
    """Return status/detail for one build manifest without inferring missing data as pass."""
    if manifest is None:
        return "unknown", "build manifest not found"

    expected_top_level = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
    checks = {
        "profile": manifest.get("profile") == profile,
        "top_level": len(manifest.get("top_level_skills", [])) == expected_top_level,
        "professional_skills": len(manifest.get("professional_skills", [])) == EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "foundation_capabilities": len(manifest.get("foundation_capabilities", [])) == EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "compiled_foundation_capabilities": len(manifest.get("compiled_foundation_capabilities", []))
        == EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "domain_extensions": len(manifest.get("domain_extensions", [])) == EXPECTED_DOMAIN_EXTENSION_COUNT,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return "fail", "failed checks: " + ", ".join(failed)
    return "pass", f"{profile} top-level count is {expected_top_level}"


def _build_manifest(root: Path, profile: str) -> dict[str, Any] | None:
    return _read_json(root / "dist" / "universal" / "skills" / profile / ".changeforge-build-manifest.json")


def _load_open_source_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_open_source_readiness",
        ROOT / "scripts" / "validate-open-source-readiness.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-open-source-readiness.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def open_source_readiness_status(root: Path) -> tuple[str, str]:
    """Return conservative open-source readiness status and check details."""
    result = _load_open_source_validator().evaluate_open_source_readiness(root)
    return result.status, result.detail


def productization_assets_status(root: Path) -> tuple[str, str]:
    """Return status/detail for productization assets the scorecard depends on."""
    missing = [rel_path for rel_path in PRODUCTIZATION_ASSETS if not (root / rel_path).is_file()]
    if missing:
        return "fail", "missing: " + ", ".join(missing)
    return "pass", "required productization assets present"


def validation_report_status(root: Path, rel_path: str) -> tuple[str, str]:
    """Return status/detail for machine-readable validation reports."""
    report = _read_json(root / rel_path)
    if not isinstance(report, dict):
        return "not_collected", f"{rel_path} missing or invalid"

    required = {"schema_version", "generated_by", "status", "errors", "summary"}
    missing = sorted(field for field in required if field not in report)
    if missing:
        return "fail", "missing validation report fields: " + ", ".join(missing)

    status = str(report.get("status"))
    if status not in {"pass", "fail", "partial"}:
        return "fail", f"invalid validation report status: {status}"
    errors = report.get("errors")
    if not isinstance(errors, list):
        return "fail", "validation report errors field must be a list"
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return "fail", "validation report summary field must be an object"
    if status == "pass" and errors:
        return "fail", "status pass but errors is non-empty"
    if status == "fail" and not errors:
        return "fail", "status fail but errors is empty; report is inconsistent"

    detail = {
        "generated_by": report.get("generated_by"),
        "error_count": len(errors),
        "summary": summary,
    }
    return status, json.dumps(detail, sort_keys=True)


def _load_validate_examples():
    spec = importlib.util.spec_from_file_location(
        "validate_examples",
        ROOT / "scripts" / "validate-examples.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-examples.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_validate_marketplace_index():
    spec = importlib.util.spec_from_file_location(
        "validate_marketplace_index",
        ROOT / "scripts" / "validate-marketplace-index.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-marketplace-index.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def examples_status(root: Path) -> tuple[str, str]:
    """Return status/detail from the same validator used by CI."""
    errors = _load_validate_examples().validate_examples(root)
    if errors:
        return "fail", "; ".join(errors[:5])
    return "pass", "showcase examples validate"


def marketplace_index_status(root: Path) -> tuple[str, str]:
    """Return status/detail from the marketplace index validator for all profiles."""
    validator = _load_validate_marketplace_index()
    errors_by_profile: dict[str, list[str]] = {}
    for profile in PROFILES:
        errors = validator.validate_profile(root, profile)
        if errors:
            errors_by_profile[profile] = errors
    if errors_by_profile:
        detail = {
            profile: errors[:3]
            for profile, errors in errors_by_profile.items()
        }
        return "fail", json.dumps(detail, sort_keys=True)
    return "pass", "recommended, full, and dev marketplace indexes validate"


def skill_efficacy_status(root: Path) -> tuple[str, str]:
    """Return conservative structural status for local skill efficacy fixtures."""
    benchmark_dir = root / "evals" / "skill-efficacy"
    if not benchmark_dir.is_dir():
        return "fail", "evals/skill-efficacy directory missing"

    paths = sorted(benchmark_dir.glob("*.yaml"))
    if len(paths) < 3:
        return "fail", f"fixtures={len(paths)}, expected_at_least=3"

    valid_verdicts = {"structural_pass", "measured_pass", "inconclusive", "blocked"}
    verdicts: dict[str, int] = {}
    reviewed_count = 0
    candidate_ignored = 0
    token_not_collected = 0
    turn_not_collected = 0
    invalid: list[str] = []
    for path in paths:
        data = load_yaml_file(path)
        if not isinstance(data, dict):
            invalid.append(path.name)
            continue
        if _human_review_candidate(data):
            candidate_ignored += 1
            continue
        reviewed_count += 1
        verdict = data.get("verdict")
        status = verdict.get("status") if isinstance(verdict, dict) else None
        if not isinstance(status, str) or status not in valid_verdicts:
            invalid.append(path.name)
            continue
        verdicts[status] = verdicts.get(status, 0) + 1
        metrics = data.get("metrics")
        if isinstance(metrics, dict):
            if metrics.get("token_overhead_pct") == "not_collected":
                token_not_collected += 1
            if metrics.get("turn_overhead_pct") == "not_collected":
                turn_not_collected += 1

    detail = {
        "fixtures": reviewed_count,
        "candidate_fixtures_ignored": candidate_ignored,
        "verdicts": verdicts,
        "live_pass_rate": "not_collected",
        "token_overhead": "not_collected"
        if token_not_collected == reviewed_count
        else "partially_collected",
        "turn_overhead": "not_collected"
        if turn_not_collected == reviewed_count
        else "partially_collected",
        "evidence_boundary": "structural/local fixtures only; no empirical before/after agent performance",
        "evidence_levels": {
            "structural fixture": reviewed_count,
            "runtime telemetry fixture sample": "not_collected",
            "live runtime telemetry sample": "not_collected",
            "promoted golden case": "not_collected",
            "live pass-rate": "not_collected",
            "token overhead": "not_collected",
            "turn overhead": "not_collected",
        },
    }
    if reviewed_count < 3:
        detail["invalid"] = invalid + ["reviewed_fixture_count_below_3"]
        return "fail", json.dumps(detail, sort_keys=True)
    if invalid:
        detail["invalid"] = invalid
        return "fail", json.dumps(detail, sort_keys=True)
    return "pass", json.dumps(detail, sort_keys=True)


def runtime_governance_fixture_status(root: Path) -> tuple[str, str]:
    """Return structural fixture coverage for runtime-governance capability suites."""
    rows: dict[str, dict[str, Any]] = {}
    invalid: list[str] = []
    candidate_ignored_total = 0
    for suite, required_capability in RUNTIME_GOVERNANCE_FIXTURE_SUITES.items():
        suite_dir = root / "evals" / suite
        paths = sorted(suite_dir.glob("*.yaml")) if suite_dir.is_dir() else []
        reviewed_paths = []
        candidate_ignored = 0
        for path in paths:
            data = load_yaml_file(path)
            if isinstance(data, dict) and _human_review_candidate(data):
                candidate_ignored += 1
                continue
            reviewed_paths.append(path)
        candidate_ignored_total += candidate_ignored
        hit_count = 0
        for path in reviewed_paths:
            data = load_yaml_file(path)
            expected = data.get("expected_capabilities") if isinstance(data, dict) else None
            if isinstance(expected, list) and required_capability in {str(item).strip() for item in expected}:
                hit_count += 1
        if len(reviewed_paths) < 3 or hit_count < 3:
            invalid.append(suite)
        rows[suite] = {
            "fixtures": len(reviewed_paths),
            "candidate_fixtures_ignored": candidate_ignored,
            "required_capability": required_capability,
            "required_capability_hits": hit_count,
        }
    detail = {
        "suites": rows,
        "total_fixtures": sum(row["fixtures"] for row in rows.values()),
        "candidate_fixtures_ignored": candidate_ignored_total,
        "evidence_boundary": "structural/local fixtures only; no live empirical pass-rate or runtime overhead evidence",
        "evidence_levels": {
            "structural fixture": sum(row["fixtures"] for row in rows.values()),
            "runtime telemetry fixture sample": "not_collected",
            "live runtime telemetry sample": "not_collected",
            "promoted golden case": "not_collected",
            "live pass-rate": "not_collected",
            "token overhead": "not_collected",
            "turn overhead": "not_collected",
        },
    }
    if invalid:
        detail["invalid"] = invalid
        return "fail", json.dumps(detail, sort_keys=True)
    return "pass", json.dumps(detail, sort_keys=True)


def context_control_overhead_status(root: Path) -> tuple[str, str]:
    """Return the context-control fixture and overhead policy status."""
    report = _read_json(root / "reports" / "context-control-plane-eval.json")
    if not isinstance(report, dict):
        return "not_collected", "reports/context-control-plane-eval.json missing or invalid"
    overhead = report.get("context_control_overhead")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    structural_fixture_status = (
        "pass"
        if report.get("status") in {"pass", "partial"} and summary.get("failed") == 0
        else "fail"
        if report.get("status") == "fail" or isinstance(summary.get("failed"), int)
        else "unknown"
    )
    detail = {
        "eval_status": report.get("status", "unknown"),
        "fixture_status": report.get("fixture_status", "unknown"),
        "release_status": report.get("release_status", "unknown"),
        "structural_fixture_status": structural_fixture_status,
        "structural_fixture_failed_count": summary.get("failed", "unknown"),
        "status": "fail",
        "overhead_status": "fail",
        "input_token_overhead_pct": None,
        "output_token_overhead_pct": None,
        "turn_overhead": None,
        "command_delta": None,
        "pass_rate_delta": None,
        "live_pass_rate": {"status": "not_collected", "pass_rate_delta": None},
        "token_overhead": {"status": "not_collected", "input_pct": None, "output_pct": None},
        "turn_overhead_detail": {"status": "not_collected", "turn_overhead": None},
        "runtime_telemetry": {"status": "not_collected"},
        "quality_improvement_claim_allowed": False,
        "overhead_policy_verdict": "context_control_overhead missing",
        "evidence_boundary": "missing",
    }
    if isinstance(overhead, dict):
        detail.update(
            {
                "status": overhead.get("status", "unknown"),
                "overhead_status": overhead.get("overhead_status", overhead.get("status", "unknown")),
                "input_token_overhead_pct": overhead.get("input_token_overhead_pct"),
                "output_token_overhead_pct": overhead.get("output_token_overhead_pct"),
                "turn_overhead": overhead.get("turn_overhead"),
                "command_delta": overhead.get("command_delta"),
                "pass_rate_delta": overhead.get("pass_rate_delta"),
                "live_pass_rate": overhead.get("live_pass_rate", detail["live_pass_rate"]),
                "token_overhead": overhead.get("token_overhead", detail["token_overhead"]),
                "turn_overhead_detail": overhead.get("turn_overhead_detail", detail["turn_overhead_detail"]),
                "runtime_telemetry": overhead.get("runtime_telemetry", detail["runtime_telemetry"]),
                "quality_improvement_claim_allowed": bool(overhead.get("quality_improvement_claim_allowed")),
                "overhead_policy_verdict": overhead.get("overhead_policy_verdict"),
                "evidence_boundary": overhead.get("evidence_boundary"),
            }
        )
    report_status = str(report.get("status") or "unknown")
    if report_status == "fail":
        return "fail", json.dumps(detail, sort_keys=True)
    if report_status not in {"pass", "partial"}:
        detail["invalid_status"] = report_status
        return "fail", json.dumps(detail, sort_keys=True)
    status = str(detail.get("status") or "unknown")
    if status not in STATUSES:
        detail["invalid_status"] = status
        return "fail", json.dumps(detail, sort_keys=True)
    if _context_control_high_token_overhead(detail) and status == "pass":
        detail["invalid_status"] = "pass_with_high_token_overhead_without_p2_governance"
        return "fail", json.dumps(detail, sort_keys=True)
    release_status = str(detail.get("release_status") or report_status)
    if release_status == "fail":
        return "fail", json.dumps(detail, sort_keys=True)
    if release_status == "partial" and status != "fail":
        return "partial", json.dumps(detail, sort_keys=True)
    if release_status == "pass" and status != "pass":
        detail["invalid_status"] = f"eval_pass_with_{status}_overhead"
        return "fail", json.dumps(detail, sort_keys=True)
    return status, json.dumps(detail, sort_keys=True)


def _context_control_high_token_overhead(detail: dict[str, Any]) -> bool:
    input_overhead = detail.get("input_token_overhead_pct")
    output_overhead = detail.get("output_token_overhead_pct")
    return (
        isinstance(input_overhead, int | float)
        and float(input_overhead) > HIGH_CONTEXT_INPUT_TOKEN_OVERHEAD_PCT
    ) or (
        isinstance(output_overhead, int | float)
        and float(output_overhead) > HIGH_CONTEXT_OUTPUT_TOKEN_OVERHEAD_PCT
    )


def executor_adapter_eval_status(root: Path) -> tuple[str, str]:
    """Return deterministic executor adapter evaluation status."""
    report = _read_json(root / "reports" / "executor-adapter-eval.json")
    if not isinstance(report, dict):
        return "unknown", "reports/executor-adapter-eval.json missing or invalid"
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return "unknown", "executor adapter summary missing"
    detail = {
        "case_count": summary.get("case_count", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "coverage_targets": summary.get("coverage_targets", []),
        "pressure_cases": summary.get("pressure_cases", []),
        "live_pass_rate": (summary.get("live_pass_rate") or {}).get("status", "not_collected"),
        "token_overhead": (summary.get("token_overhead") or {}).get("status", "not_collected"),
        "turn_overhead": (summary.get("turn_overhead") or {}).get("status", "not_collected"),
        "evidence_boundary": "deterministic local fixtures only; no live runtime pass-rate or overhead measurement",
    }
    if report.get("status") != "pass" or summary.get("failed"):
        return "fail", json.dumps(detail, sort_keys=True)
    return "pass", json.dumps(detail, sort_keys=True)


def activation_precision_status(root: Path) -> tuple[str, str]:
    """Return status for the activation precision benchmark report."""
    status, detail = validation_report_status(root, "reports/activation-precision.json")
    if status != "pass":
        return status, detail
    report = _read_json(root / "reports" / "activation-precision.json")
    summary = report.get("summary") if isinstance(report, dict) else {}
    if report.get("mode") != "built":
        return "fail", "activation precision report must be generated in built runtime mode"
    if not report.get("runtime_index"):
        return "fail", "activation precision report missing built runtime route index path"
    required_metrics = {
        "stage_accuracy",
        "skill_precision",
        "skill_recall",
        "capability_precision",
        "capability_recall",
        "reference_precision",
        "reference_recall",
        "language_fp_rate",
        "language_fn_rate",
        "risk_surface_fp_rate",
        "risk_surface_fn_rate",
        "overroute_rate",
    }
    missing = sorted(metric for metric in required_metrics if metric not in summary)
    if missing:
        return "fail", "missing activation precision metrics: " + ", ".join(missing)
    return status, detail


def runtime_telemetry_fixture_sample_status(root: Path) -> tuple[str, str]:
    """Return status for the sanitized fixture-derived runtime telemetry sample."""
    sample = _read_json(root / "reports" / "runtime-telemetry-sample.json")
    if not isinstance(sample, dict):
        return "not_collected", "reports/runtime-telemetry-sample.json missing or invalid"
    required = {
        "runtime",
        "sample_kind",
        "evidence_level",
        "event_count",
        "normalized_event_kinds",
        "degraded_event_count",
        "validation_freshness_cases",
        "closure_verdicts",
        "unsupported_checks",
        "privacy_redaction_count",
    }
    missing = sorted(field for field in required if field not in sample)
    if missing:
        return "fail", "missing telemetry fields: " + ", ".join(missing)
    if sample.get("source") != "deterministic-fixture-bounded-facts":
        return "fail", "fixture sample source must be deterministic-fixture-bounded-facts"
    if sample.get("sample_kind") != "runtime_telemetry_fixture_sample":
        return "fail", "fixture sample_kind must be runtime_telemetry_fixture_sample"
    if sample.get("evidence_level") != "runtime telemetry fixture sample":
        return "fail", "fixture evidence_level must be runtime telemetry fixture sample"
    detail = {
        "source": sample.get("source", ""),
        "sample_kind": sample.get("sample_kind", ""),
        "evidence_level": sample.get("evidence_level", ""),
        "runtime": sample.get("runtime", ""),
        "event_count": sample.get("event_count"),
        "degraded_event_count": sample.get("degraded_event_count"),
        "privacy_redaction_count": sample.get("privacy_redaction_count"),
        "token_overhead": (sample.get("token_overhead") or {}).get("status", "not_collected"),
        "turn_overhead": (sample.get("turn_overhead") or {}).get("status", "not_collected"),
    }
    return "pass", json.dumps(detail, sort_keys=True)


def runtime_telemetry_sample_status(root: Path) -> tuple[str, str]:
    """Backward-compatible alias for the fixture-derived telemetry sample status."""
    return runtime_telemetry_fixture_sample_status(root)


def live_runtime_telemetry_sample_status(root: Path) -> tuple[str, str]:
    """Return status for a live runtime telemetry sample, when separately collected."""
    sample = _read_json(root / "reports" / "live-runtime-telemetry-sample.json")
    if not isinstance(sample, dict):
        return "not_collected", "reports/live-runtime-telemetry-sample.json missing or invalid"
    required = {
        "runtime",
        "sample_kind",
        "evidence_level",
        "event_count",
        "normalized_event_kinds",
        "privacy_redaction_count",
    }
    missing = sorted(field for field in required if field not in sample)
    if missing:
        return "fail", "missing live telemetry fields: " + ", ".join(missing)
    if sample.get("source") == "deterministic-fixture-bounded-facts":
        return "fail", "live telemetry sample cannot use deterministic fixture source"
    if sample.get("sample_kind") != "live_runtime_telemetry_sample":
        return "fail", "live sample_kind must be live_runtime_telemetry_sample"
    if sample.get("evidence_level") != "live runtime telemetry sample":
        return "fail", "live evidence_level must be live runtime telemetry sample"
    detail = {
        "source": sample.get("source", ""),
        "sample_kind": sample.get("sample_kind", ""),
        "evidence_level": sample.get("evidence_level", ""),
        "runtime": sample.get("runtime", ""),
        "event_count": sample.get("event_count"),
        "privacy_redaction_count": sample.get("privacy_redaction_count"),
    }
    return "pass", json.dumps(detail, sort_keys=True)


def executor_adapter_metric_status(root: Path, metric: str) -> tuple[str, str]:
    """Return live/overhead metric collection status from executor adapter report."""
    report = _read_json(root / "reports" / "executor-adapter-eval.json")
    if not isinstance(report, dict):
        return "not_collected", "executor adapter report missing"
    summary = report.get("summary")
    metric_payload = summary.get(metric) if isinstance(summary, dict) else None
    status = metric_payload.get("status") if isinstance(metric_payload, dict) else "not_collected"
    detail = metric_payload.get("detail") if isinstance(metric_payload, dict) else "not collected"
    if status == "measured":
        return "pass", str(detail)
    return "not_collected", str(detail or "not collected")


def codex_live_pass_rate_benchmark_status(root: Path) -> tuple[str, str]:
    """Return pass-rate quality status for a published opt-in Codex CLI live summary."""
    summary = _read_json(root / "reports" / "codex-live-benchmark-summary.json")
    if not isinstance(summary, dict):
        return "not_collected", "reports/codex-live-benchmark-summary.json missing or invalid"
    status, strict_errors, readiness_warnings = codex_live_pass_rate_status(summary)
    detail = codex_live_compact_detail(
        summary,
        status=status,
        strict_errors=strict_errors,
        readiness_warnings=readiness_warnings,
    )
    return status, json.dumps(detail, sort_keys=True)


def codex_live_capability_coverage_benchmark_status(root: Path) -> tuple[str, str]:
    """Return core capability coverage status for a published opt-in Codex CLI live summary."""
    summary = _read_json(root / "reports" / "codex-live-benchmark-summary.json")
    if not isinstance(summary, dict):
        return "not_collected", "reports/codex-live-benchmark-summary.json missing or invalid"
    status, strict_errors, readiness_warnings = codex_live_capability_coverage_status(summary)
    detail = codex_live_compact_detail(
        summary,
        status=status,
        strict_errors=strict_errors,
        readiness_warnings=readiness_warnings,
    )
    return status, json.dumps(detail, sort_keys=True)


def codex_live_benchmark_status(root: Path) -> tuple[str, str]:
    """Backward-compatible aggregate status for legacy callers."""
    pass_status, pass_detail = codex_live_pass_rate_benchmark_status(root)
    capability_status, capability_detail = codex_live_capability_coverage_benchmark_status(root)
    return _weaker_status(pass_status, capability_status), json.dumps(
        {
            "pass_rate": _json_detail(pass_detail),
            "capability_coverage": _json_detail(capability_detail),
        },
        sort_keys=True,
    )


def _json_detail(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {"detail": value}
    return parsed if isinstance(parsed, dict) else {"detail": parsed}


def _codex_live_strict_summary_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    benchmark_mode = summary.get("benchmark_mode")
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"Codex live summary evidence_level must be {LIVE_EVIDENCE_LEVEL}")
    if benchmark_mode not in STRICT_BENCHMARK_MODES:
        errors.append("Codex live summary benchmark_mode must be clean-paired or ablation")
    if summary.get("auth_policy") not in STRICT_AUTH_POLICIES:
        errors.append("Codex live summary auth_policy must be borrow-current or isolated-api-key")
    if summary.get("codex_environment_policy") not in STRICT_CODEX_ENVIRONMENT_POLICIES:
        errors.append("Codex live summary must use a strict Codex environment policy")
    if summary.get("strict_benchmark_eligible") is not True:
        errors.append("Codex live summary requires strict_benchmark_eligible=true")
    if int(summary.get("current_home_result_count", 0) or 0) != 0 or int(
        summary.get("current_home_full_result_count", 0) or 0
    ) != 0:
        errors.append("Codex live summary must not include current-home-full results")
    if summary.get("user_skills_visible") is not False:
        errors.append("Codex live summary requires user_skills_visible=false")
    if summary.get("user_config_loaded") is not False:
        errors.append("Codex live summary requires user_config_loaded=false")
    if summary.get("user_rules_loaded") is not False:
        errors.append("Codex live summary requires user_rules_loaded=false")
    if summary.get("ignore_user_config") is not True or summary.get("ignore_rules") is not True:
        errors.append("Codex live summary requires --ignore-user-config and --ignore-rules")
    if summary.get("plugins_disabled") is not True:
        errors.append("Codex live summary requires --disable plugins")
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("Codex live summary must not include contaminated results")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("Codex live summary requires assertion-backed eligible results")
    if not isinstance(summary.get("failure_categories"), dict):
        errors.append("Codex live summary requires failure_categories")
    if summary.get("dominant_failure_category") not in {
        "none",
        "codex_exec_failed",
        "install_failed",
        "setup_failed",
        "test_suite_failed",
        "security_checks_failed",
        "contaminated",
        "grading_not_collected",
        "telemetry_only",
    }:
        errors.append("Codex live summary requires dominant_failure_category")
    if summary.get("dominant_setup_failure_reason") not in {
        "none",
        "missing_env_root",
        "missing_harness",
        "setup_script_missing",
        "setup_script_modified_bad_path",
        "dependency_install_failed",
        "python_compile_failed",
        "candidate_removed_required_file",
        "permission_denied",
        "shell_error",
        "unknown",
    }:
        errors.append("Codex live summary requires dominant_setup_failure_reason")
    if summary.get("dominant_setup_failure_subreason") not in {
        "none",
        "candidate_modified_setup",
        "starter_fragile_path",
        "missing_env_root",
        "wrong_cwd",
        "missing_harness",
        "classifier_uncertain",
        "unknown",
    }:
        errors.append("Codex live summary requires dominant_setup_failure_subreason")
    if not isinstance(summary.get("setup_failure_subreasons"), dict):
        errors.append("Codex live summary requires setup_failure_subreasons")
    unknown_rate = summary.get("unknown_setup_failure_rate")
    if not isinstance(unknown_rate, int | float) or not 0 <= float(unknown_rate) <= 1:
        errors.append("Codex live summary requires unknown_setup_failure_rate")
    if summary.get("effect_verdict") not in {"inconclusive", "positive", "mixed", "neutral", "negative"}:
        errors.append("Codex live summary requires effect_verdict")
    if summary.get("effect_status") not in {"inconclusive", "improved", "mixed", "neutral", "regression"}:
        errors.append("Codex live summary requires effect_status")
    if not isinstance(summary.get("effect_summary"), dict):
        errors.append("Codex live summary requires effect_summary")
    if summary.get("effect_verdict") == "positive" and summary.get("dominant_setup_failure_reason") == "unknown":
        errors.append("Codex live summary cannot claim positive effect while unknown setup failures dominate")
    if not isinstance(summary.get("cases_summary"), dict):
        errors.append("Codex live summary requires cases_summary")
    variants = summary.get("variants") or {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        payload = variants.get(variant)
        if not isinstance(payload, dict) or int(payload.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"Codex live summary requires eligible assertion results for {variant}")
    if benchmark_mode == "ablation":
        delta = summary.get("delta") or {}
        for key in (
            "skills_only_clean_vs_baseline_clean",
            "skills_with_hooks_clean_vs_skills_only_clean",
            "skills_with_hooks_clean_vs_baseline_clean",
        ):
            if key not in delta:
                errors.append(f"Codex live ablation summary requires delta.{key}")
    return errors


def _summary_status(name: str, value: dict[str, Any]) -> str:
    if name == "Routing coverage":
        if value.get("hidden_risks_needing_manual_review", 0) or value.get("cases_without_forbidden", 0):
            return "partial"
        return "pass" if value.get("cases_checked") else "unknown"
    if name == "Professional benchmarks":
        if value.get("quality_failures", 0):
            return "fail"
        return "pass" if value.get("comparison_cases_checked") else "unknown"
    if name == "Foundation capability coverage":
        statuses = value.get("statuses", {})
        if statuses.get("fail") or statuses.get("missing"):
            return "fail"
        if statuses.get("needs-review") or statuses.get("partial") or statuses.get("sample-grade"):
            return "partial"
        return "pass" if value.get("count") else "unknown"
    if name == "Professional skill coverage":
        statuses = value.get("statuses", {})
        if statuses.get("fail") or statuses.get("missing"):
            return "fail"
        if statuses.get("needs-review") or statuses.get("partial") or statuses.get("sample-grade"):
            return "partial"
        return "pass" if value.get("count") == EXPECTED_PROFESSIONAL_SKILL_COUNT else "partial"
    return "partial"


def _human_review_candidate(data: dict[str, Any]) -> bool:
    return data.get("generated_from_telemetry") is True and data.get("requires_human_review") is True


def _release_readiness_dimension(reports_dir: Path, key: str, *, name: str, command: str, fix_hint: str) -> Dimension:
    readiness = _read_json(reports_dir / "professionalism-release-readiness.json")
    if readiness is None:
        return Dimension(name, "not_collected", "reports/professionalism-release-readiness.json missing", command, fix_hint, "Run the professionalism release checks first.")

    value = readiness.get(key)
    if isinstance(value, str):
        if value in {"pass", "ready", "strict-release-ready"}:
            status = "pass"
        elif value in {"blocked", "fail", "failed"}:
            status = "fail"
        else:
            status = "partial"
        return Dimension(name, status, "reports/professionalism-release-readiness.json", command, fix_hint, f"{key}: {value}")

    if isinstance(value, dict):
        return Dimension(name, _summary_status(name, value), "reports/professionalism-release-readiness.json", command, fix_hint, json.dumps(value, sort_keys=True))

    return Dimension(name, "unknown", "reports/professionalism-release-readiness.json", command, fix_hint, f"{key} not present")


def collect_dimensions(root: Path, reports_dir: Path) -> tuple[list[Dimension], dict[str, Any]]:
    """Collect scorecard dimensions from registries, build manifests, and reports."""
    counts = _source_counts(root)
    registry_status = "pass" if counts == {
        "professional_skills": EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "foundation_capabilities": EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "domain_extensions": EXPECTED_DOMAIN_EXTENSION_COUNT,
    } else "fail"

    dimensions = [
        Dimension(
            "Registry source counts",
            registry_status,
            "src/registry/*.yaml",
            "python3 scripts/validate-registry.py",
            "Fix registry entries or expected count constants so they agree.",
            json.dumps(counts, sort_keys=True),
        )
    ]

    profile_details: dict[str, Any] = {}
    profile_statuses: list[str] = []
    for profile in PROFILES:
        manifest = _build_manifest(root, profile)
        status, detail = profile_manifest_status(manifest, profile)
        profile_statuses.append(status)
        profile_details[profile] = {
            "status": status,
            "detail": detail,
            "manifest": str(
                Path("dist")
                / "universal"
                / "skills"
                / profile
                / ".changeforge-build-manifest.json"
            ),
        }

    if any(status == "fail" for status in profile_statuses):
        profile_status = "fail"
    elif any(status in {"unknown", "not_collected"} for status in profile_statuses):
        profile_status = "unknown"
    else:
        profile_status = "pass"
    dimensions.append(
        Dimension(
            "Profile build reproducibility",
            profile_status,
            "dist/universal/skills/*/.changeforge-build-manifest.json",
            "python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev",
            "Rebuild all profiles and investigate any manifest count mismatch.",
            json.dumps(profile_details, sort_keys=True),
        )
    )

    dimensions.extend(
        [
            _release_readiness_dimension(
                reports_dir,
                "routing_coverage_summary",
                name="Routing coverage",
                command="python3 scripts/validate-professional-routing-coverage.py",
                fix_hint="Add or repair routing fixtures for uncovered hidden risks.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "professional_skill_coverage_summary",
                name="Professional skill coverage",
                command="python3 scripts/eval-skill-professionalism.py",
                fix_hint="Repair weak professional skill sections without keyword stuffing.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "key_foundation_capability_coverage_summary",
                name="Foundation capability coverage",
                command="python3 scripts/eval-skill-professionalism.py --coverage-matrix",
                fix_hint="Improve selected capability evidence contracts and references.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "benchmark_coverage_summary",
                name="Professional benchmarks",
                command="python3 scripts/eval-professional-benchmarks.py",
                fix_hint="Repair failing benchmark cases or comparison fixtures.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "strict_regression_status",
                name="Professionalism regression",
                command="python3 scripts/validate-professionalism-regression.py --strict",
                fix_hint="Resolve release blockers or record reviewed baseline decisions.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "promoted_agent_samples_strict_status",
                name="Promoted agent samples",
                command="python3 scripts/eval-professional-agent-samples.py --promoted-only --strict",
                fix_hint="Repair promoted samples that miss route, evidence, or residual risk obligations.",
            ),
        ]
    )

    skill_efficacy_dimension_status, skill_efficacy_detail = skill_efficacy_status(root)
    dimensions.append(
        Dimension(
            "Skill efficacy structural fixtures",
            skill_efficacy_dimension_status,
            "evals/skill-efficacy and scripts/validate-skill-efficacy-benchmarks.py",
            "python3 scripts/validate-skill-efficacy-benchmarks.py",
            "Repair skill-efficacy fixture structure; do not claim live pass-rate evidence without measured runs.",
            skill_efficacy_detail,
        )
    )

    runtime_fixture_status, runtime_fixture_detail = runtime_governance_fixture_status(root)
    dimensions.append(
        Dimension(
            "Runtime governance structural fixtures",
            runtime_fixture_status,
            "evals/executor-adapters, evals/repository-intelligence, evals/project-memory, evals/validation-broker, evals/trajectory",
            "python3 scripts/validate-professional-routing-coverage.py",
            "Repair runtime-governance fixture structure; do not treat structural fixtures as live runtime pass-rate evidence.",
            runtime_fixture_detail,
        )
    )

    context_control_status, context_control_detail = context_control_overhead_status(root)
    dimensions.append(
        Dimension(
            CONTEXT_CONTROL_OVERHEAD_DIMENSION,
            context_control_status,
            "reports/context-control-plane-eval.json",
            "python3 scripts/eval-context-control-plane.py",
            "Repair context-control fixtures or collect lower-overhead live evidence before claiming context-control quality improvement.",
            context_control_detail,
        )
    )

    executor_status, executor_detail = executor_adapter_eval_status(root)
    dimensions.append(
        Dimension(
            "Executor adapter structural fixtures",
            executor_status,
            "evals/executor-adapter and reports/executor-adapter-eval.json",
            "python3 scripts/eval-executor-adapters.py",
            "Repair executor adapter fixture expectations or adapter normalization until deterministic cases pass.",
            executor_detail,
        )
    )

    activation_status, activation_detail = activation_precision_status(root)
    dimensions.append(
        Dimension(
            "Activation precision benchmark",
            activation_status,
            "evals/activation and reports/activation-precision.json",
            "python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks",
            "Repair stage/skill/capability/reference/language/risk fixture expectations or resolver precision until all activation metrics pass.",
            activation_detail,
        )
    )

    telemetry_status, telemetry_detail = runtime_telemetry_fixture_sample_status(root)
    dimensions.append(
        Dimension(
            "Runtime telemetry fixture sample",
            telemetry_status,
            "reports/runtime-telemetry-sample.json",
            "python3 scripts/eval-executor-adapters.py",
            "Generate a sanitized bounded fixture-derived telemetry sample and keep it clearly labeled as non-live evidence.",
            telemetry_detail,
        )
    )
    live_telemetry_status, live_telemetry_detail = live_runtime_telemetry_sample_status(root)
    dimensions.append(
        Dimension(
            "Live runtime telemetry sample",
            live_telemetry_status,
            "reports/live-runtime-telemetry-sample.json",
            "manual live runtime collection with sanitized bounded facts",
            "Collect a real hook-runtime sample before changing this status from not_collected; do not use executor adapter fixtures for this dimension.",
            live_telemetry_detail,
        )
    )

    for metric, name in (
        ("live_pass_rate", "Executor adapter live pass-rate"),
        ("token_overhead", "Executor adapter token overhead"),
        ("turn_overhead", "Executor adapter turn overhead"),
    ):
        metric_status, metric_detail = executor_adapter_metric_status(root, metric)
        dimensions.append(
            Dimension(
                name,
                metric_status,
                "reports/executor-adapter-eval.json",
                "python3 scripts/eval-executor-adapters.py",
                "Collect a real measured run before changing this status from not_collected.",
                metric_detail,
            )
        )

    codex_live_summary = _read_json(root / "reports" / "codex-live-benchmark-summary.json")
    codex_live_pass_rate_status_value, codex_live_pass_rate_detail = codex_live_pass_rate_benchmark_status(root)
    codex_live_pass_rate_fix_hint = (
        "; ".join(codex_live_repair_hints(codex_live_summary if isinstance(codex_live_summary, dict) else None))
        if codex_live_pass_rate_status_value != "pass"
        else "Keep canonical reports generated from the strongest strict ablation evidence."
    )
    dimensions.append(
        Dimension(
            CODEX_LIVE_PASS_RATE_BENCHMARK_NAME,
            codex_live_pass_rate_status_value,
            "reports/codex-live-benchmark-summary.json",
            "python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json",
            codex_live_pass_rate_fix_hint,
            codex_live_pass_rate_detail,
        )
    )
    codex_live_capability_status_value, codex_live_capability_detail = (
        codex_live_capability_coverage_benchmark_status(root)
    )
    codex_live_capability_fix_hint = (
        "; ".join(
            codex_live_capability_repair_hints(codex_live_summary if isinstance(codex_live_summary, dict) else None)
        )
        if codex_live_capability_status_value != "pass"
        else "Keep every core capability backed by run assertion evidence and explicit process traces."
    )
    dimensions.append(
        Dimension(
            CODEX_LIVE_CAPABILITY_COVERAGE_NAME,
            codex_live_capability_status_value,
            "reports/codex-live-benchmark-summary.json and evals/codex-live/capability-matrix.yaml",
            "python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json",
            codex_live_capability_fix_hint,
            codex_live_capability_detail,
        )
    )

    example_status, example_detail = examples_status(root)
    dimensions.append(
        Dimension(
            "Example coverage",
            example_status,
            "examples/ and scripts/validate-examples.py",
            "python3 scripts/validate-examples.py",
            "Repair showcase scenario prompts, expected routes, evidence files, or routing fixture links.",
            example_detail,
        )
    )

    productization_status, productization_detail = productization_assets_status(root)
    dimensions.append(
        Dimension(
            "Productization assets",
            productization_status,
            "docs/productization assets, schemas, and scripts",
            "python3 scripts/validate-productization-assets.py",
            "Restore required productization docs, schema, or scripts.",
            productization_detail,
        )
    )

    marketplace_status, marketplace_detail = marketplace_index_status(root)
    dimensions.append(
        Dimension(
            "Marketplace index validation",
            marketplace_status,
            "scripts/validate-marketplace-index.py",
            "python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev",
            "Rebuild all profiles and repair marketplace index schema, visibility, or runtime path mismatches.",
            marketplace_detail,
        )
    )

    open_source_status, open_source_detail = open_source_readiness_status(root)
    dimensions.append(
        Dimension(
            "Open-source readiness",
            open_source_status,
            "config/open-source-release.yaml, docs/LICENSE_DECISION.md, docs/OPEN_SOURCE_READINESS.md, pyproject.toml, CONTRIBUTING.md, SECURITY.md, LICENSE",
            "python3 scripts/validate-open-source-readiness.py",
            "Owner must select an OSI license, update package metadata, confirm contribution licensing, and configure private vulnerability reporting before open-source publication.",
            open_source_detail,
        )
    )

    hook_status, hook_detail = validation_report_status(root, "reports/hook-validation.json")
    dimensions.append(
        Dimension(
            "Hook safety",
            hook_status,
            "reports/hook-validation.json",
            "python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md",
            "Run hook validation and inspect hook runtime changes; hooks must remain advisory and fail-open unless explicitly stricter.",
            hook_detail,
        )
    )
    installation_status, installation_detail = validation_report_status(
        root,
        "reports/installation-validation.json",
    )
    dimensions.append(
        Dimension(
            "Installation validation",
            installation_status,
            "reports/installation-validation.json",
            "python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md",
            "Run installation validation after rebuilding all profiles.",
            installation_detail,
        )
    )

    metadata = {
        "source_counts": counts,
        "profile_counts": profile_details,
        "validation_commands": [
            {
                "command": command,
                "status": "not_collected",
                "note": "Run command directly; this scorecard does not infer pass/fail from stdout.",
            }
            for command in VALIDATION_COMMANDS
        ],
    }
    return dimensions, metadata


def _summary(dimensions: list[Dimension]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for dimension in dimensions:
        counts[dimension.status] += 1
    return counts


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the scorecard JSON payload as Markdown."""
    lines = [
        "# Professional Scorecard",
        "",
        "This scorecard is generated from local registry, build, and report evidence. Missing machine-readable evidence is shown as `not_collected` or `unknown`, not as pass.",
        "",
        "## Summary",
        "",
    ]
    for status, count in payload["status_summary"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Evidence Levels", "", "| Evidence | Status | Meaning |", "| --- | --- | --- |"])
    for level, detail in payload["evidence_levels"].items():
        lines.append(f"| {level} | `{detail['status']}` | {detail['meaning']} |")
    lines.extend(["", "## Dimensions", "", "| Dimension | Status | Source | Verification |", "| --- | --- | --- | --- |"])
    for dimension in payload["dimensions"]:
        lines.append(
            f"| {dimension['name']} | `{dimension['status']}` | {dimension['source']} | `{dimension['verification_command']}` |"
        )
    _append_context_control_overhead_detail(lines, payload)
    _append_codex_live_benchmark_detail(lines, payload)
    lines.extend(["", "## Profile Counts", ""])
    for profile, detail in payload["profile_counts"].items():
        lines.append(f"- `{profile}`: `{detail['status']}` - {detail['detail']}")
    lines.extend(["", "## Repair Hints", ""])
    for dimension in payload["dimensions"]:
        if dimension["status"] != "pass":
            lines.append(f"- {dimension['name']}: {dimension['fix_hint']}")
    lines.append("")
    return "\n".join(lines)


def _append_context_control_overhead_detail(lines: list[str], payload: dict[str, Any]) -> None:
    for dimension in payload.get("dimensions", []):
        if not isinstance(dimension, dict) or dimension.get("name") != CONTEXT_CONTROL_OVERHEAD_DIMENSION:
            continue
        detail = _json_detail(str(dimension.get("detail", "")))
        lines.extend(["", "## Context Control Overhead", ""])
        for field in (
            "eval_status",
            "fixture_status",
            "structural_fixture_status",
            "overhead_status",
            "release_status",
            "status",
            "quality_improvement_claim_allowed",
            "input_token_overhead_pct",
            "output_token_overhead_pct",
            "turn_overhead",
            "command_delta",
            "pass_rate_delta",
            "live_pass_rate",
            "token_overhead",
            "turn_overhead_detail",
            "runtime_telemetry",
            "overhead_policy_verdict",
            "evidence_boundary",
        ):
            lines.append(f"- {field}: `{_markdown_detail_value(detail.get(field, 'not_collected'))}`")
        return


def _append_codex_live_benchmark_detail(lines: list[str], payload: dict[str, Any]) -> None:
    live_dimensions = [
        dimension
        for dimension in payload.get("dimensions", [])
        if isinstance(dimension, dict)
        and dimension.get("name") in {CODEX_LIVE_PASS_RATE_BENCHMARK_NAME, CODEX_LIVE_CAPABILITY_COVERAGE_NAME}
    ]
    if not live_dimensions:
        return

    lines.extend(["", "## Codex CLI Live Benchmark", ""])
    for dimension in live_dimensions:
        detail = _json_detail(str(dimension.get("detail", "")))
        lines.append(f"### {dimension.get('name', 'Codex CLI live benchmark')}")
        for field in (
            "run_id",
            "effect_verdict",
            "evidence_status",
            "benchmark_passed_result_count",
            "benchmark_eligible_result_count",
        ):
            lines.append(f"- {field}: `{_markdown_detail_value(detail.get(field, 'not_collected'))}`")
        variants = detail.get("variants")
        hooks = variants.get("skills_with_hooks_clean") if isinstance(variants, dict) else None
        if isinstance(hooks, dict):
            lines.append(
                "- skills_with_hooks_clean.pass_rate: "
                f"`{_markdown_detail_value(hooks.get('pass_rate', 'not_collected'))}`"
            )
        lines.append("")


def _markdown_detail_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def generate_scorecard(root: Path, reports_dir: Path) -> dict[str, Any]:
    """Generate the complete scorecard payload."""
    dimensions, metadata = collect_dimensions(root, reports_dir)
    dimension_payload = [asdict(dimension) for dimension in dimensions]
    return {
        "schema_version": 1,
        "generated_by": "scripts/generate-professional-scorecard.py",
        "status_summary": _summary(dimensions),
        "evidence_levels": _evidence_levels(dimensions),
        "dimensions": dimension_payload,
        **metadata,
    }


def _evidence_levels(dimensions: list[Dimension]) -> dict[str, dict[str, str]]:
    promoted_status = _status_for_dimension(dimensions, "Promoted agent samples")
    runtime_fixture_sample_status = _status_for_dimension(dimensions, "Runtime telemetry fixture sample")
    live_runtime_sample_status = _status_for_dimension(dimensions, "Live runtime telemetry sample")
    live_pass_rate_status = _status_for_dimension(dimensions, "Executor adapter live pass-rate")
    token_overhead_status = _status_for_dimension(dimensions, "Executor adapter token overhead")
    turn_overhead_status = _status_for_dimension(dimensions, "Executor adapter turn overhead")
    codex_live_pass_rate_status_value = _status_for_dimension(dimensions, CODEX_LIVE_PASS_RATE_BENCHMARK_NAME)
    codex_live_capability_status_value = _status_for_dimension(dimensions, CODEX_LIVE_CAPABILITY_COVERAGE_NAME)
    codex_live_benchmark_status_value = _weaker_status(
        codex_live_pass_rate_status_value,
        codex_live_capability_status_value,
    )
    return {
        level: {
            "status": _evidence_level_status(
                level,
                promoted_status,
                runtime_fixture_sample_status,
                live_runtime_sample_status,
                live_pass_rate_status,
                token_overhead_status,
                turn_overhead_status,
                codex_live_benchmark_status_value,
            ),
            "meaning": meaning,
        }
        for level, meaning in EVIDENCE_LEVELS.items()
    }


def _status_for_dimension(dimensions: list[Dimension], name: str) -> str:
    for dimension in dimensions:
        if dimension.name == name:
            return dimension.status
    return "unknown"


def _weaker_status(*statuses: str) -> str:
    """Return the weakest report status for combined evidence-level display."""
    order = ("fail", "partial", "not_collected", "unknown", "pass")
    cleaned = [status if status in STATUSES else "unknown" for status in statuses]
    for status in order:
        if status in cleaned:
            return status
    return "unknown"


def _evidence_level_status(
    level: str,
    promoted_status: str,
    runtime_fixture_sample_status: str,
    live_runtime_sample_status: str,
    live_pass_rate_status: str,
    token_overhead_status: str,
    turn_overhead_status: str,
    codex_live_benchmark_status_value: str,
) -> str:
    if level == "structural fixture":
        return "pass"
    if level == "runtime telemetry fixture sample":
        return runtime_fixture_sample_status if runtime_fixture_sample_status in STATUSES else "unknown"
    if level == "live runtime telemetry sample":
        return live_runtime_sample_status if live_runtime_sample_status in STATUSES else "not_collected"
    if level == "promoted golden case":
        return promoted_status if promoted_status in STATUSES else "unknown"
    if level == "live pass-rate":
        return live_pass_rate_status if live_pass_rate_status in STATUSES else "not_collected"
    if level == "token overhead":
        return token_overhead_status if token_overhead_status in STATUSES else "not_collected"
    if level == "turn overhead":
        return turn_overhead_status if turn_overhead_status in STATUSES else "not_collected"
    if level == "local_codex_cli_live_benchmark":
        return (
            codex_live_benchmark_status_value
            if codex_live_benchmark_status_value in STATUSES
            else "not_collected"
        )
    return "not_collected"


def strict_profile_build_errors(payload: dict[str, Any]) -> list[str]:
    """Return strict profile-build smoke errors without requiring release-only reports."""
    dimensions = {
        str(dimension.get("name")): str(dimension.get("status"))
        for dimension in payload.get("dimensions", [])
        if isinstance(dimension, dict)
    }
    errors: list[str] = []
    for name in STRICT_PROFILE_BUILD_DIMENSIONS:
        status = dimensions.get(name)
        if status != "pass":
            errors.append(f"{name} must be pass for --strict-profile-builds, got {status or 'missing'}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for writing Markdown and JSON scorecards."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Markdown output path.")
    parser.add_argument("--json-out", required=True, help="JSON output path.")
    parser.add_argument("--reports-dir", default=str(ROOT / "reports"))
    parser.add_argument(
        "--strict-profile-builds",
        action="store_true",
        help="Fail when build/profile/productization smoke dimensions are missing or not passing.",
    )
    args = parser.parse_args(argv)

    payload = generate_scorecard(ROOT, Path(args.reports_dir))
    json_out = Path(args.json_out)
    md_out = Path(args.out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote professional scorecard to {md_out} and {json_out}")
    if args.strict_profile_builds:
        errors = strict_profile_build_errors(payload)
        if errors:
            for error in errors:
                print(f"generate-professional-scorecard: ERROR: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
