#!/usr/bin/env python3
"""Shared helpers for opt-in Codex CLI live benchmarks."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "codex-live" / "cases.yaml"
CAPABILITY_MATRIX_PATH = ROOT / "evals" / "codex-live" / "capability-matrix.yaml"
STATUSES = ("not_collected", "skipped_not_opted_in", "partial", "collected", "failed")
ARTIFACT_STATUSES = ("collected", "partial", "failed")
GRADING_STATUSES = ("passed", "failed", "not_collected", "telemetry_only", "contaminated")
FAILURE_CATEGORIES = (
    "none",
    "codex_exec_failed",
    "install_failed",
    "setup_failed",
    "test_suite_failed",
    "security_checks_failed",
    "contaminated",
    "grading_not_collected",
    "telemetry_only",
)
SETUP_FAILURE_REASONS = (
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
)
SETUP_FAILURE_SUBREASONS = (
    "none",
    "candidate_modified_setup",
    "starter_fragile_path",
    "missing_env_root",
    "wrong_cwd",
    "missing_harness",
    "classifier_uncertain",
    "unknown",
)
SETUP_CONTRACT_FIELDS = (
    "candidate_setup_exists",
    "candidate_setup_hash_changed",
    "candidate_setup_mentions_changeforge_codegen_root",
    "candidate_setup_uses_fixed_parent_traversal",
    "candidate_setup_invokes_codegen_harness",
)
TEST_SUITE_FAILURE_REASONS = (
    "none",
    "assertion_failed",
    "missing_test_script",
    "python_import_failed",
    "python_compile_failed",
    "behavior_failed",
    "unknown",
)
SECURITY_FAILURE_REASONS = (
    "none",
    "assertion_failed",
    "missing_security_script",
    "sensitive_log_leak",
    "unsafe_network_policy",
    "unknown",
)
FIRST_FAILURE_STAGES = ("setup", "test_suite", "security_checks", "assertion_files", "none")
EFFECT_VERDICTS = ("inconclusive", "positive", "mixed", "neutral", "negative")
EFFECT_STATUSES = ("inconclusive", "improved", "mixed", "neutral", "regression")
PUBLIC_STATUSES = ("pass", "partial", "fail", "unknown", "not_collected")
VARIANTS = ("baseline_clean", "skills_only_clean", "skills_with_hooks_clean", "current_home_smoke")
STRICT_BENCHMARK_MODES = ("clean-paired", "ablation")
BENCHMARK_MODES = (*STRICT_BENCHMARK_MODES, "current-home-smoke")
MODE_DEFAULT_VARIANTS = {
    "clean-paired": ("baseline_clean", "skills_with_hooks_clean"),
    "ablation": ("baseline_clean", "skills_only_clean", "skills_with_hooks_clean"),
    "current-home-smoke": ("current_home_smoke",),
}
GRADING_MODES = ("assertion", "telemetry_only")
CASE_TIERS = ("core", "level1", "experimental")
PROFILES = ("recommended", "full", "dev")
SANDBOXES = ("read-only", "workspace-write", "danger-full-access")
AUTH_POLICIES = ("isolated-api-key", "borrow-current", "current-home-full")
STRICT_AUTH_POLICIES = ("isolated-api-key", "borrow-current")
CODEX_ENVIRONMENT_POLICIES = ("isolated_api_key", "auth_borrowed_clean", "current_home_full")
STRICT_CODEX_ENVIRONMENT_POLICIES = ("isolated_api_key", "auth_borrowed_clean")
LIVE_EVIDENCE_LEVEL = "local_codex_cli_live_benchmark"
CURRENT_HOME_SMOKE_EVIDENCE_LEVEL = "current_home_integration_smoke"
CODEX_LIVE_LEGACY_BENCHMARK_NAME = "Codex CLI live benchmark"
CODEX_LIVE_PASS_RATE_BENCHMARK_NAME = "Codex CLI live pass-rate benchmark"
CODEX_LIVE_CAPABILITY_COVERAGE_NAME = "Codex CLI live capability coverage"
CODEX_LIVE_EVIDENCE_SCOPES = ("smoke", "multi_case_ablation_3_run", "current_home_smoke")
STRONG_CODEX_LIVE_ASSERTION_CASE_MIN = 5
STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN = 3
STRONG_CODEX_LIVE_EVIDENCE_SCOPE = "multi_case_ablation_3_run"
CORE_CAPABILITY_IDS = (
    "professional_injection_activation",
    "staged_injection_precision",
    "repository_graph_context_pack",
    "project_memory_governance",
    "validation_broker_freshness",
    "pdd_ddd_sdd_tdd_review_flow",
    "minimal_correct_implementation_ladder",
    "pua_or_pressure_resistance",
    "execution_trajectory_review",
    "professional_logging_decision",
    "context_compaction_retention",
)
PROCESS_EVIDENCE_CAPABILITY_IDS = frozenset(
    {
        "professional_injection_activation",
        "staged_injection_precision",
        "repository_graph_context_pack",
        "project_memory_governance",
        "validation_broker_freshness",
        "pdd_ddd_sdd_tdd_review_flow",
        "pua_or_pressure_resistance",
        "execution_trajectory_review",
        "professional_logging_decision",
        "context_compaction_retention",
    }
)
CAPABILITY_QUALITY_READY_REQUIRED_IDS = frozenset(
    {
        "professional_injection_activation",
        "staged_injection_precision",
        "pdd_ddd_sdd_tdd_review_flow",
        "validation_broker_freshness",
        "minimal_correct_implementation_ladder",
        "professional_logging_decision",
        "context_compaction_retention",
    }
)
LARGE_QUALITY_IMPROVEMENT_MIN_CAPABILITY_COUNT = 6
REQUIRED_ABLATION_DELTAS = (
    "skills_only_clean_vs_baseline_clean",
    "skills_with_hooks_clean_vs_skills_only_clean",
    "skills_with_hooks_clean_vs_baseline_clean",
)
BASELINE_CONTAMINATION_SIGNALS = (
    "ChangeForge",
    "rd-skills",
    "changeforge_route",
    "changeforge_stage_route",
    "changeforge_implementation_preflight",
    "selected_skills",
    "selected_capabilities",
    "required_quality_gates",
    "implementation_preflight",
    ".agent",
    ".agents",
    ".changeforge",
    "hook-runtime",
    "professional injection",
    "professional-injection",
    "change-forge-router",
)
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+"),
    re.compile(r"CODEX_API_KEY\s*="),
    re.compile(r"OPENAI_API_KEY\s*="),
    re.compile(r"auth\.json"),
    re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|bearer[_-]?token|refresh[_-]?token)\s*[:=]\s*"
        r"(?=[A-Za-z0-9_./+=-]{20,})(?=[A-Za-z0-9_./+=-]*[A-Z0-9])[A-Za-z0-9_./+=-]+"
    ),
)
FORBIDDEN_ABSOLUTE_USER_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s\"'<>]+"),
    re.compile(r"/home/[^\s\"'<>]+"),
    re.compile(r"/private/var/[^\s\"'<>]+"),
    re.compile(r"/var/folders/[^\s\"'<>]+"),
    re.compile(r"/tmp/[^\s\"'<>]+"),
    re.compile(r"[A-Za-z]:\\Users\\[^\s\"'<>]+"),
)
RAW_ARTIFACT_FILENAMES = frozenset({"events.jsonl"})
CODEGEN_HARNESS_ENV_PATTERN = re.compile(r"(?i)\bCHANGEFORGE_CODEGEN_[A-Z0-9_]+\b")
REQUIRED_CAPABILITY_ARTIFACTS = (
    "process-trace.json",
    "result.json",
    "grading/grading-result.json",
    "events.redacted.jsonl",
    "final.md",
    "diff.patch",
)


@dataclass(frozen=True)
class CodexLiveCase:
    """One validated Codex live benchmark case."""

    id: str
    category: str
    codegen_case: str
    enabled: bool
    variants: tuple[str, ...]
    task_prompt: Path
    starter_repo: Path
    grading_benchmark: str
    grading_mode: str
    publishable_for_strict: bool
    tier: str
    coverage_dimensions: tuple[str, ...]


@dataclass(frozen=True)
class CodexLiveCapability:
    """One declared core capability in the live benchmark matrix."""

    id: str
    title: str
    description: str
    expected_runtime_signal: str
    linked_live_cases: tuple[str, ...]
    linked_assertions: tuple[str, ...]
    required_variants: tuple[str, ...]
    publishable_for_strict: bool
    quality_pass_criteria: str
    evidence_kind: str
    failure_interpretation: str
    current_status: str


def utc_stamp() -> str:
    """Return a filesystem-safe UTC timestamp."""
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write stable JSON with parent creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any | None:
    """Read JSON, returning None when the file is absent."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def safe_case_segment(case_id: str) -> str:
    """Convert a case id into a single safe path segment."""
    return case_id.replace("/", "__")


def relpath(root: Path, path: Path) -> str:
    """Return a stable relative path when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_case_registry(path: Path = CASES_PATH, root: Path = ROOT) -> list[CodexLiveCase]:
    """Load and validate the Codex live benchmark registry."""
    data = load_yaml_file(path)
    errors = validate_case_registry(data, root)
    if errors:
        raise ValidationProblem("; ".join(errors))
    cases: list[CodexLiveCase] = []
    for raw in data.get("cases", []):
        cases.append(
            CodexLiveCase(
                id=str(raw["id"]),
                category=str(raw["category"]),
                codegen_case=str(raw["codegen_case"]),
                enabled=bool(raw["enabled"]),
                variants=tuple(str(variant) for variant in raw["variants"]),
                task_prompt=(root / str(raw["task_prompt"])).resolve(),
                starter_repo=(root / str(raw["starter_repo"])).resolve(),
                grading_benchmark=str(raw["grading_benchmark"]),
                grading_mode=str(raw["grading_mode"]),
                publishable_for_strict=bool(raw["publishable_for_strict"]),
                tier=str(raw.get("tier", "core")),
                coverage_dimensions=tuple(str(item) for item in raw.get("coverage_dimensions", [raw["category"]])),
            )
        )
    return cases


def load_capability_matrix(path: Path = CAPABILITY_MATRIX_PATH) -> list[CodexLiveCapability]:
    """Load and validate the Codex live core capability matrix."""
    data = load_yaml_file(path)
    errors = validate_capability_matrix(data)
    if errors:
        raise ValidationProblem("; ".join(errors))
    capabilities = []
    for raw in data.get("core_capabilities", []):
        capabilities.append(
            CodexLiveCapability(
                id=str(raw["id"]),
                title=str(raw["title"]),
                description=str(raw["description"]),
                expected_runtime_signal=str(raw["expected_runtime_signal"]),
                linked_live_cases=tuple(str(item) for item in raw["linked_live_cases"]),
                linked_assertions=tuple(str(item) for item in raw["linked_assertions"]),
                required_variants=tuple(str(item) for item in raw["required_variants"]),
                publishable_for_strict=bool(raw["publishable_for_strict"]),
                quality_pass_criteria=str(raw["quality_pass_criteria"]),
                evidence_kind=str(raw["evidence_kind"]),
                failure_interpretation=str(raw["failure_interpretation"]),
                current_status=str(raw["current_status"]),
            )
        )
    return capabilities


def validate_capability_matrix(data: Any) -> list[str]:
    """Return live capability matrix validation errors without raising."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["capability matrix must be a mapping"]
    if data.get("kind") != "changeforge.codex_live_capability_matrix":
        errors.append("kind must be changeforge.codex_live_capability_matrix")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    required_variants = data.get("required_variants")
    if (
        not isinstance(required_variants, list)
        or tuple(str(item) for item in required_variants) != MODE_DEFAULT_VARIANTS["ablation"]
    ):
        errors.append("required_variants must equal baseline_clean, skills_only_clean, skills_with_hooks_clean")
    capabilities = data.get("core_capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        return [*errors, "core_capabilities must be a non-empty list"]
    seen: set[str] = set()
    required_fields = {
        "id",
        "title",
        "description",
        "expected_runtime_signal",
        "linked_live_cases",
        "linked_assertions",
        "required_variants",
        "publishable_for_strict",
        "quality_pass_criteria",
        "evidence_kind",
        "failure_interpretation",
        "current_status",
    }
    for index, raw in enumerate(capabilities):
        prefix = f"core_capabilities[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue
        missing = sorted(required_fields - set(raw))
        if missing:
            errors.append(f"{prefix}: missing {', '.join(missing)}")
            continue
        capability_id = str(raw["id"])
        if capability_id in seen:
            errors.append(f"{prefix}: duplicate id {capability_id}")
        seen.add(capability_id)
        if capability_id not in CORE_CAPABILITY_IDS:
            errors.append(f"{prefix}: unknown core capability id {capability_id}")
        for field in ("linked_live_cases", "linked_assertions", "required_variants"):
            value = raw.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{prefix}: {field} must be a non-empty list of strings")
        invalid_variants = sorted({str(item) for item in raw.get("required_variants", [])} - set(VARIANTS))
        if invalid_variants:
            errors.append(f"{prefix}: invalid variants {', '.join(invalid_variants)}")
        if raw.get("publishable_for_strict") is not True:
            errors.append(f"{prefix}: publishable_for_strict must be true for core live capabilities")
        for field in (
            "title",
            "description",
            "expected_runtime_signal",
            "quality_pass_criteria",
            "evidence_kind",
            "failure_interpretation",
            "current_status",
        ):
            if not isinstance(raw.get(field), str) or not str(raw.get(field)).strip():
                errors.append(f"{prefix}: {field} must be a non-empty string")
    missing_core = sorted(set(CORE_CAPABILITY_IDS) - seen)
    if missing_core:
        errors.append("core_capabilities missing required ids: " + ", ".join(missing_core))
    return errors


def validate_case_registry(data: Any, root: Path = ROOT) -> list[str]:
    """Return registry validation errors without raising."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["cases.yaml must be a mapping"]
    schema_version = data.get("schema_version")
    if schema_version not in {1, 2}:
        errors.append("schema_version must be 1 or 2")
    if data.get("kind") != "changeforge.codex_live_benchmark_cases":
        errors.append("kind must be changeforge.codex_live_benchmark_cases")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return [*errors, "cases must be a non-empty list"]

    seen_ids: set[str] = set()
    for index, raw in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue
        required = {
            "id",
            "category",
            "codegen_case",
            "enabled",
            "variants",
            "task_prompt",
            "starter_repo",
            "grading_benchmark",
            "grading_mode",
            "publishable_for_strict",
        }
        if schema_version == 2:
            required.update({"tier", "coverage_dimensions"})
        missing = sorted(required - set(raw))
        if missing:
            errors.append(f"{prefix}: missing {', '.join(missing)}")
            continue
        case_id = str(raw["id"])
        category = str(raw["category"])
        codegen_case = str(raw["codegen_case"])
        if case_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {case_id}")
        seen_ids.add(case_id)
        expected_id = f"{category}/{codegen_case}"
        if case_id != expected_id:
            errors.append(f"{prefix}: id must equal {expected_id}")
        expected_cases = EXPECTED_BENCHMARKS.get(category, ())
        if codegen_case not in expected_cases:
            errors.append(f"{prefix}: {category}/{codegen_case} is not in codegen benchmark manifest")
        if str(raw["grading_benchmark"]) != expected_id:
            errors.append(f"{prefix}: grading_benchmark must equal {expected_id}")
        grading_mode = str(raw.get("grading_mode"))
        if grading_mode not in GRADING_MODES:
            errors.append(f"{prefix}: grading_mode must be one of {', '.join(GRADING_MODES)}")
        has_real_assertions = bool(case_assertion_files(category, codegen_case, root))
        if grading_mode == "assertion" and not has_real_assertions:
            errors.append(f"{prefix}: grading_mode assertion requires real pytest assertion files")
        publishable = raw.get("publishable_for_strict")
        if not isinstance(publishable, bool):
            errors.append(f"{prefix}: publishable_for_strict must be boolean")
        elif publishable and grading_mode != "assertion":
            errors.append(f"{prefix}: publishable_for_strict requires grading_mode assertion")
        tier = str(raw.get("tier", "core"))
        if tier not in CASE_TIERS:
            errors.append(f"{prefix}: tier must be one of {', '.join(CASE_TIERS)}")
        coverage_dimensions = raw.get("coverage_dimensions", [category])
        if (
            not isinstance(coverage_dimensions, list)
            or not coverage_dimensions
            or any(not isinstance(item, str) or not item.strip() for item in coverage_dimensions)
        ):
            errors.append(f"{prefix}: coverage_dimensions must be a non-empty list of strings")
        elif len(set(coverage_dimensions)) != len(coverage_dimensions):
            errors.append(f"{prefix}: coverage_dimensions must not contain duplicates")
        variants = raw.get("variants")
        if not isinstance(variants, list) or not variants:
            errors.append(f"{prefix}: variants must be a non-empty list")
        else:
            invalid = sorted({str(variant) for variant in variants} - set(VARIANTS))
            if invalid:
                errors.append(f"{prefix}: invalid variants {', '.join(invalid)}")
        if not isinstance(raw.get("enabled"), bool):
            errors.append(f"{prefix}: enabled must be boolean")
        for field in ("task_prompt", "starter_repo"):
            rel = str(raw[field])
            path = root / rel
            if _is_external_path(rel):
                errors.append(f"{prefix}: {field} must be repository-relative without network URLs or parent traversal")
            elif not path.exists():
                errors.append(f"{prefix}: {field} does not exist: {rel}")
    return errors


def _is_external_path(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() or "://" in value or ".." in path.parts


def case_assertion_files(category: str, case_name: str, root: Path = ROOT) -> tuple[Path, ...]:
    """Return real pytest assertion files for a codegen benchmark case."""
    case_root = root / "evals" / "codegen" / category / case_name
    test_roots = (
        case_root / "test-suite" / "tests",
        case_root / "security-checks" / "security_tests",
    )
    assertion_files: list[Path] = []
    for test_root in test_roots:
        if not test_root.exists():
            continue
        for test_file in sorted(test_root.glob("test_*.py")):
            try:
                text = test_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "assert " in text or "self.assert" in text or "pytest.raises" in text or "raise AssertionError" in text:
                assertion_files.append(test_file)
    return tuple(assertion_files)


def _scan_text_artifacts(path: Path, *, include_raw: bool = False) -> list[Path]:
    if not path.exists():
        return []
    paths = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
    if include_raw:
        return paths
    return [item for item in paths if item.name not in RAW_ARTIFACT_FILENAMES]


def scan_forbidden_secrets(path: Path, *, include_raw: bool = False) -> list[str]:
    """Scan text artifacts for forbidden secret patterns."""
    findings: list[str] = []
    if not path.exists():
        return findings
    for item in _scan_text_artifacts(path, include_raw=include_raw):
        try:
            text = item.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{relpath(ROOT, item)} matches forbidden secret pattern {pattern.pattern}")
                break
    return findings


def scan_forbidden_absolute_user_paths(path: Path, *, include_raw: bool = False) -> list[str]:
    """Scan report artifacts for local user absolute path leakage."""
    findings: list[str] = []
    for item in _scan_text_artifacts(path, include_raw=include_raw):
        try:
            text = item.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in FORBIDDEN_ABSOLUTE_USER_PATH_PATTERNS:
            if pattern.search(text):
                findings.append(f"{relpath(ROOT, item)} exposes local absolute path pattern {pattern.pattern}")
                break
    return findings


def redact_report_text(text: str) -> str:
    """Redact local absolute user paths before persisting report text artifacts."""
    redacted = text
    for pattern in FORBIDDEN_ABSOLUTE_USER_PATH_PATTERNS:
        redacted = pattern.sub("<local-path>", redacted)
    return redacted


def detect_baseline_contamination(run_dir: Path) -> dict[str, Any]:
    """Detect ChangeForge/user-level state leakage in a baseline artifact directory."""
    candidate_files = (
        "final.md",
        "diff.patch",
        "git-status.txt",
        "codex-command.redacted.json",
        "events.metrics.json",
    )
    signals: set[str] = set()
    files: set[str] = set()
    for filename in candidate_files:
        path = run_dir / filename
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        text = CODEGEN_HARNESS_ENV_PATTERN.sub("", text)
        lowered = text.lower()
        for signal in BASELINE_CONTAMINATION_SIGNALS:
            if signal.lower() in lowered:
                signals.add(signal)
                files.add(filename)
    return {
        "contaminated": bool(signals),
        "signals": sorted(signals),
        "files": sorted(files),
    }


def validate_status(status: Any) -> str:
    """Normalize a live-run status."""
    value = str(status)
    return value if value in STATUSES else "failed"


def public_status_from_live(status: str) -> str:
    """Map live benchmark status into scorecard/public status vocabulary."""
    if status == "collected":
        return "pass"
    if status == "partial":
        return "partial"
    if status == "failed":
        return "fail"
    return "not_collected"


def codex_live_evidence_scope_ready(summary: dict[str, Any]) -> bool:
    """Return the strict readiness flag from either the top-level or nested summary field."""
    if summary.get("evidence_scope_ready") is True:
        return True
    detail = summary.get("evidence_scope_detail")
    return isinstance(detail, dict) and detail.get("evidence_scope_ready") is True


def codex_live_strict_artifact_errors(summary: dict[str, Any]) -> list[str]:
    """Return errors for strict, sanitized live benchmark artifact validity.

    This validates whether a summary is a trustworthy local artifact. It does not
    mean the artifact is strong enough to support a broad live benchmark pass.
    Clean-paired smoke runs can pass this artifact check and still be partial.
    """
    errors: list[str] = []
    required = (
        "schema_version",
        "generated_by",
        "status",
        "evidence_level",
        "benchmark_mode",
        "auth_policy",
        "codex_environment_policy",
        "strict_benchmark_eligible",
        "run_id",
        "case_count",
        "assertion_case_count",
        "result_count",
        "benchmark_eligible_result_count",
        "contaminated_result_count",
        "current_home_result_count",
        "current_home_full_result_count",
        "user_skills_visible",
        "user_config_loaded",
        "user_rules_loaded",
        "ignore_user_config",
        "ignore_rules",
        "plugins_disabled",
        "variants",
        "delta",
    )
    missing = sorted(field for field in required if field not in summary)
    if missing:
        errors.append("missing Codex live summary fields: " + ", ".join(missing))
    benchmark_mode = summary.get("benchmark_mode")
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"evidence_level must be {LIVE_EVIDENCE_LEVEL}")
    if benchmark_mode not in STRICT_BENCHMARK_MODES:
        errors.append("benchmark_mode must be clean-paired or ablation")
    if summary.get("auth_policy") not in STRICT_AUTH_POLICIES:
        errors.append(f"auth_policy {summary.get('auth_policy')!r} must be borrow-current or isolated-api-key")
    if summary.get("codex_environment_policy") not in STRICT_CODEX_ENVIRONMENT_POLICIES:
        errors.append(
            f"codex_environment_policy {summary.get('codex_environment_policy')!r} "
            "must be auth_borrowed_clean or isolated_api_key"
        )
    if summary.get("strict_benchmark_eligible") is not True:
        errors.append("strict_benchmark_eligible must be true")
    if int(summary.get("current_home_result_count", 0) or 0) != 0 or int(
        summary.get("current_home_full_result_count", 0) or 0
    ) != 0:
        errors.append("current-home-full results are not public benchmark evidence")
    if summary.get("user_skills_visible") is not False:
        errors.append("user_skills_visible must be false")
    if summary.get("user_config_loaded") is not False:
        errors.append("user_config_loaded must be false")
    if summary.get("user_rules_loaded") is not False:
        errors.append("user_rules_loaded must be false")
    if summary.get("ignore_user_config") is not True:
        errors.append("ignore_user_config must be true")
    if summary.get("ignore_rules") is not True:
        errors.append("ignore_rules must be true")
    if summary.get("plugins_disabled") is not True:
        errors.append("plugins_disabled must be true")
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("contaminated results are not public benchmark evidence")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("assertion-backed eligible results are required")
    if summary.get("effect_verdict") not in EFFECT_VERDICTS:
        errors.append("effect_verdict is required")
    if summary.get("effect_status") not in EFFECT_STATUSES:
        errors.append("effect_status is required")

    variants = summary.get("variants") if isinstance(summary.get("variants"), dict) else {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        payload = variants.get(variant)
        if not isinstance(payload, dict):
            errors.append(f"variant {variant} is required")
            continue
        if int(payload.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"eligible assertion results are required for {variant}")
        if variant == "baseline_clean" and payload.get("changeforge_install_source") != "none":
            errors.append("baseline_clean must not install ChangeForge")
        if variant == "skills_only_clean":
            if payload.get("changeforge_install_source") != "current_repository":
                errors.append("skills_only_clean must use current_repository install source")
            if payload.get("changeforge_hooks_enabled") is not False:
                errors.append("skills_only_clean must not enable project-level hooks")
        if variant == "skills_with_hooks_clean":
            if payload.get("changeforge_install_source") != "current_repository":
                errors.append("skills_with_hooks_clean must use current_repository install source")
            if payload.get("changeforge_hooks_enabled") is not True:
                errors.append("skills_with_hooks_clean must enable project-level hooks")
        if payload.get("user_level_install_used") is not False:
            errors.append(f"{variant} requires user_level_install_used=false")

    if benchmark_mode == "ablation":
        delta = summary.get("delta") if isinstance(summary.get("delta"), dict) else {}
        for key in REQUIRED_ABLATION_DELTAS:
            if key not in delta:
                errors.append(f"ablation delta.{key} is required")
    return errors


def codex_live_evidence_readiness_warnings(summary: dict[str, Any]) -> list[str]:
    """Return reasons a strict artifact is not broad pass-rate benchmark evidence."""
    warnings: list[str] = []
    benchmark_mode = str(summary.get("benchmark_mode") or "")
    evidence_scope = str(summary.get("evidence_scope") or "")
    if benchmark_mode != "ablation":
        warnings.append("run ablation mode")
    if evidence_scope == "smoke":
        warnings.append("clean-paired smoke is diagnostic evidence only")
    if evidence_scope != STRONG_CODEX_LIVE_EVIDENCE_SCOPE:
        warnings.append(f"evidence_scope must be {STRONG_CODEX_LIVE_EVIDENCE_SCOPE}")
    if not codex_live_evidence_scope_ready(summary):
        warnings.append("evidence_scope_ready must be true")
    if summary.get("effect_status") == "inconclusive" or summary.get("effect_verdict") == "inconclusive":
        warnings.append("effect_status/effect_verdict is inconclusive")
    if int(summary.get("assertion_case_count", 0) or 0) < STRONG_CODEX_LIVE_ASSERTION_CASE_MIN:
        warnings.append(f"need >= {STRONG_CODEX_LIVE_ASSERTION_CASE_MIN} assertion-backed cases")
    detail = summary.get("evidence_scope_detail")
    observed_runs = None
    if isinstance(detail, dict):
        observed_runs = detail.get("observed_min_runs_per_required_variant")
    if not isinstance(observed_runs, int | float):
        observed_runs = _observed_min_runs_from_variants(summary)
    if int(observed_runs or 0) < STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN:
        warnings.append(f"need >= {STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN} runs per variant")
    variants = summary.get("variants") if isinstance(summary.get("variants"), dict) else {}
    missing_variants = [variant for variant in MODE_DEFAULT_VARIANTS["ablation"] if variant not in variants]
    if missing_variants:
        warnings.append("include required variants: " + ", ".join(missing_variants))
    return _dedupe(warnings)


def codex_live_process_warning(summary: dict[str, Any]) -> str | None:
    """Return a warning when process evidence is inferred-only rather than explicit."""
    process = summary.get("process_compliance_summary")
    if not isinstance(process, dict):
        return "process_compliance_summary missing"
    raw_trace_count = process.get("process_trace_count", 0)
    if raw_trace_count == "not_collected":
        return "process_trace_count not_collected"
    trace_count = int(raw_trace_count or 0)
    if trace_count <= 0:
        return "process_trace_count is 0"
    present_rates = [
        process.get("pdd_present_rate"),
        process.get("ddd_present_rate"),
        process.get("sdd_present_rate"),
        process.get("tdd_present_rate"),
    ]
    if all(isinstance(value, int | float) and float(value) == 0.0 for value in present_rates):
        return "process_trace_inferred_only: explicit PDD/DDD/SDD/TDD traces were not captured"
    fallback_rate = process.get("required_field_fallback_rate")
    if isinstance(fallback_rate, int | float) and float(fallback_rate) > 0.5:
        return "process_trace_fallback_heavy: required field fallback rate exceeds 0.5"
    return None


def codex_live_pass_rate_status(summary: dict[str, Any] | None) -> tuple[str, list[str], list[str]]:
    """Return pass-rate benchmark status plus strict errors and readiness warnings."""
    if not isinstance(summary, dict):
        return "not_collected", [], ["summary missing"]
    strict_errors = codex_live_strict_artifact_errors(summary)
    if strict_errors:
        return "fail", strict_errors, []
    status = str(summary.get("status") or "not_collected")
    if status == "failed":
        return "fail", [], ["summary status is failed"]
    if status in {"not_collected", "skipped_not_opted_in"}:
        return "not_collected", [], ["summary not collected"]
    readiness_warnings = codex_live_evidence_readiness_warnings(summary)
    if status == "partial" or readiness_warnings:
        return "partial", [], readiness_warnings
    if status == "collected":
        return "pass", [], []
    return "not_collected", [], [f"summary status {status!r} is not recognized"]


def codex_live_scorecard_status(summary: dict[str, Any] | None) -> tuple[str, list[str], list[str]]:
    """Backward-compatible alias for pass-rate benchmark status."""
    return codex_live_pass_rate_status(summary)


def codex_live_capability_coverage_status(summary: dict[str, Any] | None) -> tuple[str, list[str], list[str]]:
    """Return core capability coverage status plus errors and warnings."""
    if not isinstance(summary, dict):
        return "not_collected", [], ["summary missing"]
    coverage = codex_live_capability_coverage_summary(summary)
    status = str(coverage.get("status") or "not_collected")
    errors = [str(error) for error in coverage.get("errors", [])] if isinstance(coverage.get("errors"), list) else []
    warnings = [
        str(reason)
        for item in coverage.get("items", [])
        if isinstance(item, dict)
        for reason in item.get("reasons", [])
        if isinstance(reason, str)
    ]
    if status not in PUBLIC_STATUSES:
        return "fail", [f"invalid capability coverage status {status!r}"], warnings
    return status, errors, _dedupe(warnings)


def codex_live_capability_coverage_summary(
    summary: dict[str, Any],
    *,
    capabilities: list[CodexLiveCapability] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Evaluate live core capability coverage from a summary and matrix."""
    errors: list[str] = []
    if capabilities is None:
        try:
            capabilities = load_capability_matrix()
        except Exception as exc:
            return {
                "status": "not_collected",
                "matrix_path": relpath(root, CAPABILITY_MATRIX_PATH),
                "core_capability_count": len(CORE_CAPABILITY_IDS),
                "items": [],
                "errors": [f"capability matrix missing or invalid: {exc}"],
            }
    case_metadata = _live_case_metadata(root)
    items = [
        _capability_coverage_item(capability, summary, case_metadata, root=root)
        for capability in capabilities
    ]
    declared_ids = {item["id"] for item in items}
    for missing_id in sorted(set(CORE_CAPABILITY_IDS) - declared_ids):
        items.append(
            {
                "id": missing_id,
                "title": missing_id,
                "linked_cases": [],
                "run_status": "not_collected",
                "assertion_status": "not_collected",
                "evidence_collected": False,
                "status": "not_collected",
                "reasons": ["capability missing from matrix"],
            }
        )
    status_counts = {status: 0 for status in PUBLIC_STATUSES}
    for item in items:
        status = str(item.get("status") or "unknown")
        status_counts[status if status in status_counts else "unknown"] += 1
    if status_counts["fail"]:
        status = "fail"
    elif status_counts["partial"] or status_counts["not_collected"] or status_counts["unknown"]:
        status = "partial"
    elif items:
        status = "pass"
    else:
        status = "not_collected"
    pass_ids = [str(item["id"]) for item in items if item.get("status") == "pass"]
    return {
        "status": status,
        "matrix_path": relpath(root, CAPABILITY_MATRIX_PATH),
        "core_capability_count": len(items),
        "pass_count": status_counts["pass"],
        "partial_count": status_counts["partial"],
        "fail_count": status_counts["fail"],
        "not_collected_count": status_counts["not_collected"],
        "assertion_backed_coverage_count": len(pass_ids),
        "assertion_backed_covered_capabilities": pass_ids,
        "required_quality_ready_capabilities": sorted(CAPABILITY_QUALITY_READY_REQUIRED_IDS),
        "quality_ready_required_pass": sorted(CAPABILITY_QUALITY_READY_REQUIRED_IDS & set(pass_ids)),
        "items": items,
        "errors": errors,
    }


def _capability_coverage_item(
    capability: CodexLiveCapability,
    summary: dict[str, Any],
    case_metadata: dict[str, dict[str, Any]],
    *,
    root: Path,
) -> dict[str, Any]:
    linked_cases = list(capability.linked_live_cases)
    case_results = [
        _capability_case_result(case_id, capability, summary, case_metadata, root=root)
        for case_id in linked_cases
    ]
    run_status = _combined_case_status(case_results, "run_status")
    assertion_status = _combined_case_status(case_results, "assertion_status")
    process_warning = codex_live_process_warning(summary)
    process_required = capability.id in PROCESS_EVIDENCE_CAPABILITY_IDS
    process_ok = not process_required or process_warning is None
    evidence_collected = bool(case_results) and any(case.get("evidence_collected") is True for case in case_results)
    reasons = [
        str(reason)
        for case in case_results
        for reason in case.get("reasons", [])
        if isinstance(reason, str)
    ]
    if process_required and process_warning:
        reasons.append(process_warning)
    if not linked_cases:
        status = "partial"
        reasons.append("capability has no linked live case")
    elif any(case.get("assertion_status") == "fail" for case in case_results):
        status = "fail"
    elif all(case.get("assertion_status") == "pass" for case in case_results) and process_ok:
        status = "pass"
    elif any(case.get("run_status") == "not_registered" for case in case_results):
        status = "partial"
    elif any(case.get("run_status") == "not_run" for case in case_results):
        status = "partial"
    else:
        status = "partial"
    return {
        "id": capability.id,
        "title": capability.title,
        "linked_cases": linked_cases,
        "linked_assertions": list(capability.linked_assertions),
        "required_variants": list(capability.required_variants),
        "publishable_for_strict": capability.publishable_for_strict,
        "run_status": run_status,
        "assertion_status": assertion_status,
        "evidence_collected": evidence_collected and process_ok,
        "process_evidence_required": process_required,
        "process_evidence_status": "pass" if process_ok else "partial",
        "case_results": case_results,
        "status": status,
        "reasons": _dedupe(reasons),
        "failure_interpretation": capability.failure_interpretation,
    }


def _capability_case_result(
    case_id: str,
    capability: CodexLiveCapability,
    summary: dict[str, Any],
    case_metadata: dict[str, dict[str, Any]],
    *,
    root: Path,
) -> dict[str, Any]:
    metadata = case_metadata.get(case_id)
    cases_summary = summary.get("cases_summary") if isinstance(summary.get("cases_summary"), dict) else {}
    payload = cases_summary.get(case_id) if isinstance(cases_summary, dict) else None
    reasons: list[str] = []
    if not isinstance(metadata, dict):
        return {
            "case_id": case_id,
            "run_status": "not_registered",
            "assertion_status": "not_collected",
            "evidence_collected": False,
            "reasons": ["linked case is not registered in cases.yaml"],
        }
    if metadata.get("grading_mode") != "assertion" or metadata.get("publishable_for_strict") is not True:
        reasons.append("linked case is not assertion-backed publishable strict evidence")
    if not isinstance(payload, dict):
        return {
            "case_id": case_id,
            "run_status": "not_run",
            "assertion_status": "not_collected",
            "evidence_collected": False,
            "reasons": [*reasons, "linked case was not run in this summary"],
        }
    variants = payload.get("variants") if isinstance(payload.get("variants"), dict) else {}
    missing_variants = [variant for variant in capability.required_variants if variant not in variants]
    if missing_variants:
        reasons.append("missing required variants: " + ", ".join(missing_variants))
    baseline = variants.get("baseline_clean") if isinstance(variants, dict) else None
    if isinstance(baseline, dict) and int(((baseline.get("failure_categories") or {}).get("contaminated", 0)) or 0) > 0:
        reasons.append("baseline contamination detected")
        assertion_status = "fail"
    else:
        assertion_status = _skills_variant_assertion_status(variants)
    artifact_status, artifact_reasons, artifact_evidence_collected = _capability_artifact_status(
        summary,
        case_id,
        capability,
    )
    reasons.extend(artifact_reasons)
    if artifact_status == "fail":
        assertion_status = "fail"
    elif artifact_status == "partial" and assertion_status == "pass":
        assertion_status = "partial"
    run_status = "run" if not missing_variants else "missing_required_variant"
    evidence_collected = (
        assertion_status == "pass"
        and artifact_evidence_collected
        and not missing_variants
        and not reasons
    )
    return {
        "case_id": case_id,
        "run_status": run_status,
        "assertion_status": assertion_status,
        "evidence_collected": evidence_collected,
        "artifact_evidence_status": artifact_status,
        "artifact_evidence": _bounded_artifact_evidence(summary, case_id),
        "reasons": _dedupe(reasons),
    }


def _capability_artifact_status(
    summary: dict[str, Any],
    case_id: str,
    capability: CodexLiveCapability,
) -> tuple[str, list[str], bool]:
    evidence = _bounded_artifact_evidence(summary, case_id)
    reasons: list[str] = []
    if not evidence:
        return "partial", ["run artifact evidence missing for linked case"], False
    status = "pass"
    for variant in capability.required_variants:
        variant_evidence = evidence.get(variant)
        if not isinstance(variant_evidence, dict):
            status = "partial"
            reasons.append(f"{variant}: run artifact evidence missing")
            continue
        runs = int(variant_evidence.get("runs", 0) or 0)
        artifact_runs = int(variant_evidence.get("artifact_backed_run_count", 0) or 0)
        if runs <= 0:
            status = "partial"
            reasons.append(f"{variant}: no artifact-backed runs recorded")
            continue
        if artifact_runs < runs:
            status = "partial"
            reasons.append(f"{variant}: missing required run artifacts")
        missing = variant_evidence.get("missing_required_artifacts")
        if isinstance(missing, dict) and missing:
            status = "partial"
            reasons.append(f"{variant}: missing artifacts {', '.join(sorted(missing))}")
        if int(variant_evidence.get("self_report_only_count", 0) or 0) > 0:
            status = "partial"
            reasons.append(f"{variant}: CAPABILITY_EVIDENCE.md is not backed by run metadata artifacts")
        if variant_evidence.get("privacy_redaction_status") == "fail":
            status = "fail"
            reasons.append(f"{variant}: forbidden raw prompt, secret, command output, or absolute path leaked")
        if variant in {"skills_only_clean", "skills_with_hooks_clean"}:
            route_count = int(variant_evidence.get("route_process_evidence_count", 0) or 0)
            if route_count < runs:
                status = "partial"
                reasons.append(f"{variant}: explicit route/process evidence missing")
        if variant == "skills_with_hooks_clean":
            hook_count = int(variant_evidence.get("hook_bounded_evidence_count", 0) or 0)
            if hook_count < runs:
                status = "partial"
                reasons.append(f"{variant}: hook-specific bounded evidence missing")
    if capability.id == "context_compaction_retention":
        compact_status, compact_reasons = _compact_artifact_status(evidence)
        reasons.extend(compact_reasons)
        if compact_status == "fail":
            status = "fail"
        elif compact_status == "partial" and status == "pass":
            status = "partial"
    return status, _dedupe(reasons), status == "pass"


def _compact_artifact_status(evidence: dict[str, Any]) -> tuple[str, list[str]]:
    hooks = evidence.get("skills_with_hooks_clean") if isinstance(evidence.get("skills_with_hooks_clean"), dict) else {}
    compact = hooks.get("compact") if isinstance(hooks.get("compact"), dict) else {}
    reasons: list[str] = []
    status = "pass"
    if int(compact.get("pre_compact_snapshot_count", 0) or 0) <= 0:
        status = "fail"
        reasons.append("pre_compact snapshot evidence missing")
    if int(compact.get("post_compact_reinject_count", 0) or 0) <= 0:
        status = "fail"
        reasons.append("post_compact reinjection evidence missing")
    if compact.get("privacy_redaction_status") != "pass":
        status = "fail"
        reasons.append("compaction privacy redaction did not pass")
    if compact.get("context_retention_status") != "pass":
        status = "fail"
        reasons.append("context retention status is not pass")
    if compact.get("compact_after_repair_continuation_status") != "pass":
        status = "fail"
        reasons.append("post-compact repair continuation evidence missing")
    missing = compact.get("missing_required_context_fields")
    if isinstance(missing, list) and missing:
        status = "fail"
        reasons.append("missing compact context fields: " + ", ".join(str(item) for item in missing))
    return status, reasons


def _bounded_artifact_evidence(summary: dict[str, Any], case_id: str) -> dict[str, Any]:
    evidence = summary.get("capability_artifact_evidence")
    if not isinstance(evidence, dict):
        return {}
    case_evidence = evidence.get(case_id)
    if not isinstance(case_evidence, dict):
        return {}
    return {
        str(variant): payload
        for variant, payload in case_evidence.items()
        if isinstance(payload, dict)
    }


def _skills_variant_assertion_status(variants: dict[str, Any]) -> str:
    statuses: list[str] = []
    for variant in ("skills_only_clean", "skills_with_hooks_clean"):
        payload = variants.get(variant)
        if not isinstance(payload, dict):
            statuses.append("not_collected")
            continue
        eligible = int(payload.get("benchmark_eligible_result_count", 0) or 0)
        passed = int(payload.get("benchmark_passed_result_count", 0) or 0)
        if eligible <= 0:
            statuses.append("not_collected")
        elif passed < eligible:
            statuses.append("fail")
        else:
            statuses.append("pass")
    if "fail" in statuses:
        return "fail"
    if all(status == "pass" for status in statuses):
        return "pass"
    return "partial"


def _combined_case_status(case_results: list[dict[str, Any]], field: str) -> str:
    if not case_results:
        return "not_collected"
    values = [str(item.get(field) or "not_collected") for item in case_results]
    if "fail" in values:
        return "fail"
    if all(value in {"run", "pass"} for value in values):
        return "run" if field == "run_status" else "pass"
    if any(value == "not_registered" for value in values):
        return "not_registered"
    if any(value == "not_run" for value in values):
        return "not_run"
    return "partial"


def _live_case_metadata(root: Path) -> dict[str, dict[str, Any]]:
    try:
        cases = load_case_registry(root=root)
    except Exception:
        return {}
    return {
        case.id: {
            "grading_mode": case.grading_mode,
            "publishable_for_strict": case.publishable_for_strict,
            "coverage_dimensions": list(case.coverage_dimensions),
            "enabled": case.enabled,
        }
        for case in cases
    }


def codex_live_compact_detail(
    summary: dict[str, Any],
    *,
    status: str,
    strict_errors: list[str] | None = None,
    readiness_warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build bounded detail for scorecard/public report consistency checks."""
    variants = summary.get("variants") if isinstance(summary.get("variants"), dict) else {}
    coverage = summary.get("coverage_summary") if isinstance(summary.get("coverage_summary"), dict) else {}
    cost = summary.get("cost_summary") if isinstance(summary.get("cost_summary"), dict) else {}
    capability = codex_live_capability_coverage_summary(summary)
    return {
        "evidence_status": status,
        "evidence_level": summary.get("evidence_level"),
        "evidence_scope": summary.get("evidence_scope"),
        "evidence_scope_ready": codex_live_evidence_scope_ready(summary),
        "effect_status": summary.get("effect_status"),
        "effect_verdict": summary.get("effect_verdict"),
        "benchmark_mode": summary.get("benchmark_mode"),
        "auth_policy": summary.get("auth_policy"),
        "codex_environment_policy": summary.get("codex_environment_policy"),
        "strict_benchmark_eligible": summary.get("strict_benchmark_eligible"),
        "run_id": summary.get("run_id"),
        "case_count": summary.get("case_count"),
        "assertion_case_count": summary.get("assertion_case_count"),
        "result_count": summary.get("result_count"),
        "benchmark_eligible_result_count": summary.get("benchmark_eligible_result_count"),
        "benchmark_passed_result_count": summary.get("benchmark_passed_result_count"),
        "coverage_summary": {
            "registered_live_case_count": coverage.get("registered_live_case_count"),
            "registered_publishable_assertion_case_count": coverage.get("registered_publishable_assertion_case_count"),
            "actual_run_case_count": coverage.get("actual_run_case_count"),
            "actual_run_assertion_case_count": coverage.get("actual_run_assertion_case_count"),
            "actual_run_case_coverage_rate": coverage.get("actual_run_case_coverage_rate"),
        },
        "variants": {
            variant: {
                "run_count": payload.get("run_count"),
                "case_count": payload.get("case_count"),
                "pass_rate": payload.get("pass_rate"),
                "security_pass_rate": payload.get("security_pass_rate"),
                "security_assertion_failure_rate": payload.get("security_assertion_failure_rate"),
                "security_check_execution_failure_rate": payload.get("security_check_execution_failure_rate"),
                "benchmark_eligible_result_count": payload.get("benchmark_eligible_result_count"),
                "benchmark_passed_result_count": payload.get("benchmark_passed_result_count"),
                "average_usage": payload.get("average_usage"),
                "average_metrics": payload.get("average_metrics"),
            }
            for variant, payload in variants.items()
            if isinstance(payload, dict)
        },
        "delta": summary.get("delta"),
        "quality_improvement_summary": summary.get("quality_improvement_summary"),
        "capability_coverage_summary": {
            "status": capability.get("status"),
            "core_capability_count": capability.get("core_capability_count"),
            "pass_count": capability.get("pass_count"),
            "partial_count": capability.get("partial_count"),
            "fail_count": capability.get("fail_count"),
            "not_collected_count": capability.get("not_collected_count"),
            "assertion_backed_coverage_count": capability.get("assertion_backed_coverage_count"),
            "assertion_backed_covered_capabilities": capability.get("assertion_backed_covered_capabilities"),
            "items": [
                {
                    "id": item.get("id"),
                    "linked_cases": item.get("linked_cases"),
                    "run_status": item.get("run_status"),
                    "assertion_status": item.get("assertion_status"),
                    "evidence_collected": item.get("evidence_collected"),
                    "status": item.get("status"),
                    "reasons": list(item.get("reasons", []))[:6] if isinstance(item.get("reasons"), list) else [],
                }
                for item in capability.get("items", [])
                if isinstance(item, dict)
            ],
        },
        "compact_context_summary": summary.get("compact_context_summary"),
        "case_result_summary": summary.get("case_result_summary"),
        "cost_summary": {
            "cost_adjusted_delta": cost.get("cost_adjusted_delta"),
            "cost_caveat": cost.get("cost_caveat"),
            "cost_is_telemetry_only": cost.get("cost_is_telemetry_only"),
            "telemetry_only_note": cost.get("telemetry_only_note"),
        },
        "process_compliance_summary": summary.get("process_compliance_summary"),
        "limitations": summary.get("limitations"),
        "strict_errors": strict_errors or [],
        "readiness_warnings": readiness_warnings or [],
    }


def codex_live_repair_hints(summary: dict[str, Any] | None) -> list[str]:
    """Return concise repair hints for non-pass Codex live benchmark evidence."""
    if not isinstance(summary, dict):
        return ["run ablation mode", "include skills_only_clean", "use >=5 assertion-backed cases", "use >=3 runs per variant", "regenerate canonical reports"]
    status, strict_errors, readiness_warnings = codex_live_scorecard_status(summary)
    if status == "pass":
        return []
    hints = [
        "run ablation mode",
        "include skills_only_clean",
        "use >=5 assertion-backed cases",
        "use >=3 runs per variant",
        "regenerate canonical reports",
    ]
    return _dedupe([*readiness_warnings, *strict_errors, *hints])


def codex_live_capability_repair_hints(summary: dict[str, Any] | None) -> list[str]:
    """Return concise repair hints for non-pass live capability coverage."""
    if not isinstance(summary, dict):
        return ["add capability matrix", "register assertion-backed live cases", "run strict ablation", "collect explicit process traces"]
    coverage = codex_live_capability_coverage_summary(summary)
    if coverage.get("status") == "pass":
        return []
    hints = [
        "register every core capability linked case",
        "run linked cases in baseline_clean, skills_only_clean, and skills_with_hooks_clean",
        "keep linked cases assertion-backed and publishable_for_strict=true",
        "collect explicit process-trace evidence instead of inferred/fallback fields",
        "rerun reports after capability cases pass",
    ]
    reasons = [
        str(reason)
        for item in coverage.get("items", [])
        if isinstance(item, dict)
        for reason in item.get("reasons", [])
        if isinstance(reason, str)
    ]
    return _dedupe([*reasons[:8], *hints])


def _observed_min_runs_from_variants(summary: dict[str, Any]) -> int:
    variants = summary.get("variants") if isinstance(summary.get("variants"), dict) else {}
    runs = [
        int((variants.get(variant) or {}).get("run_count", 0) or 0)
        for variant in MODE_DEFAULT_VARIANTS["ablation"]
    ]
    return min(runs) if runs else 0


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def redact_codex_command(command: list[str]) -> list[str]:
    """Redact command paths that could expose local run directories."""
    redacted: list[str] = []
    skip_next = False
    for index, value in enumerate(command):
        if skip_next:
            skip_next = False
            continue
        if value == "--output-last-message" and index + 1 < len(command):
            redacted.extend([value, "<final.md>"])
            skip_next = True
            continue
        if value.startswith("/Users/") or value.startswith("/home/"):
            redacted.append("<local-path>")
            continue
        redacted.append(value)
    return redacted


def schema_required_fields(schema_name: str) -> tuple[str, ...]:
    """Return required fields for the local schemas without a jsonschema dependency."""
    mapping = {
        "run-manifest": (
            "schema_version",
            "generated_by",
            "run_id",
            "status",
            "benchmark_mode",
            "dry_run",
            "live_execution_allowed",
            "live_execution_effective",
            "cases",
            "variants",
            "runs_per_variant",
            "sandbox",
            "auth_policy",
            "codex_environment_policy",
            "limitations",
        ),
        "case-result": (
            "schema_version",
            "generated_by",
            "case_id",
            "variant",
            "run_index",
            "status",
            "artifact_status",
            "grading_status",
            "benchmark_mode",
            "codex_home_mode",
            "auth_policy",
            "codex_environment_policy",
            "changeforge_install_source",
            "changeforge_profile",
            "changeforge_hooks_enabled",
            "user_level_install_used",
            "grading_mode",
            "publishable_for_strict",
            "benchmark_eligible",
            "benchmark_passed",
            "failure_category",
            "setup_failure_reason",
            "setup_failure_subreason",
            "setup_contract",
            "test_suite_failure_reason",
            "security_failure_reason",
            "first_failure_stage",
            "first_failure_excerpt",
            "setup_log_excerpt",
            "test_suite_log_excerpt",
            "security_log_excerpt",
            "contamination",
            "environment",
            "paths",
            "grading",
            "metrics",
            "limitations",
        ),
        "summary": (
            "schema_version",
            "generated_by",
            "status",
            "evidence_level",
            "evidence_scope",
            "evidence_scope_ready",
            "evidence_scope_detail",
            "evidence_status",
            "effect_verdict",
            "effect_status",
            "effect_summary",
            "benchmark_mode",
            "codex_home_policy",
            "auth_policy",
            "codex_environment_policy",
            "changeforge_install_source",
            "changeforge_profile",
            "changeforge_hooks_enabled",
            "user_level_install_used",
            "strict_benchmark_eligible",
            "run_id",
            "case_count",
            "assertion_case_count",
            "telemetry_only_case_count",
            "result_count",
            "benchmark_eligible_result_count",
            "benchmark_passed_result_count",
            "not_collected_grading_count",
            "telemetry_only_result_count",
            "contaminated_result_count",
            "failure_categories",
            "dominant_failure_category",
            "setup_failure_reasons",
            "dominant_setup_failure_reason",
            "setup_failure_subreasons",
            "dominant_setup_failure_subreason",
            "unknown_setup_failure_rate",
            "test_suite_failure_reasons",
            "security_failure_reasons",
            "current_home_result_count",
            "current_home_full_result_count",
            "user_skills_visible",
            "user_config_loaded",
            "user_rules_loaded",
            "ignore_user_config",
            "ignore_rules",
            "plugins_disabled",
            "variants",
            "delta",
            "cases",
            "cases_summary",
            "coverage_summary",
            "limitations",
        ),
    }
    return mapping[schema_name]


def validate_required_fields(payload: Any, schema_name: str) -> list[str]:
    """Validate required fields and common live status constraints."""
    if not isinstance(payload, dict):
        return [f"{schema_name}: payload must be an object"]
    errors = [
        f"{schema_name}: missing required field {field}"
        for field in schema_required_fields(schema_name)
        if field not in payload
    ]
    status = payload.get("status")
    if status is not None and status not in STATUSES:
        errors.append(f"{schema_name}: invalid status {status}")
    if schema_name == "case-result":
        artifact_status = payload.get("artifact_status")
        if artifact_status is not None and artifact_status not in ARTIFACT_STATUSES:
            errors.append(f"{schema_name}: invalid artifact_status {artifact_status}")
        grading_status = payload.get("grading_status")
        if grading_status is not None and grading_status not in GRADING_STATUSES:
            errors.append(f"{schema_name}: invalid grading_status {grading_status}")
        failure_category = payload.get("failure_category")
        if failure_category is not None and failure_category not in FAILURE_CATEGORIES:
            errors.append(f"{schema_name}: invalid failure_category {failure_category}")
        reason_sets = {
            "setup_failure_reason": SETUP_FAILURE_REASONS,
            "setup_failure_subreason": SETUP_FAILURE_SUBREASONS,
            "test_suite_failure_reason": TEST_SUITE_FAILURE_REASONS,
            "security_failure_reason": SECURITY_FAILURE_REASONS,
        }
        for field, allowed in reason_sets.items():
            value = payload.get(field)
            if value is not None and value not in allowed:
                errors.append(f"{schema_name}: invalid {field} {value}")
        first_failure_stage = payload.get("first_failure_stage")
        if first_failure_stage is not None and first_failure_stage not in FIRST_FAILURE_STAGES:
            errors.append(f"{schema_name}: invalid first_failure_stage {first_failure_stage}")
        setup_contract = payload.get("setup_contract")
        if not isinstance(setup_contract, dict):
            errors.append(f"{schema_name}: setup_contract must be an object")
        else:
            for field in SETUP_CONTRACT_FIELDS:
                if not isinstance(setup_contract.get(field), bool):
                    errors.append(f"{schema_name}: setup_contract.{field} must be boolean")
        for field in (
            "first_failure_excerpt",
            "setup_log_excerpt",
            "test_suite_log_excerpt",
            "security_log_excerpt",
        ):
            value = payload.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{schema_name}: {field} must be a string")
            elif isinstance(value, str) and len(value) > 1200:
                errors.append(f"{schema_name}: {field} must be bounded to 1200 characters")
    if schema_name == "summary":
        verdict = payload.get("effect_verdict")
        if verdict is not None and verdict not in EFFECT_VERDICTS:
            errors.append(f"{schema_name}: invalid effect_verdict {verdict}")
        effect_status = payload.get("effect_status")
        if effect_status is not None and effect_status not in EFFECT_STATUSES:
            errors.append(f"{schema_name}: invalid effect_status {effect_status}")
    limitations = payload.get("limitations")
    if limitations is not None and (not isinstance(limitations, list) or not limitations):
        errors.append(f"{schema_name}: limitations must be a non-empty list")
    if schema_name == "summary" and payload.get("evidence_level") not in (
        LIVE_EVIDENCE_LEVEL,
        CURRENT_HOME_SMOKE_EVIDENCE_LEVEL,
    ):
        errors.append(
            f"{schema_name}: evidence_level must be {LIVE_EVIDENCE_LEVEL} or {CURRENT_HOME_SMOKE_EVIDENCE_LEVEL}"
        )
    return errors


def print_errors(label: str, errors: list[str]) -> int:
    """Print validation errors and return an exit status."""
    if not errors:
        return 0
    for error in errors:
        print(f"{label}: ERROR: {error}", file=sys.stderr)
    return 1
