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
    "unknown",
    "setup_script_missing",
    "harness_path_unresolved",
    "dependency_install_failed",
    "python_compile_failed",
    "setup_script_failed",
)
TEST_SUITE_FAILURE_REASONS = (
    "none",
    "unknown",
    "assertion_failed",
    "harness_contract_failed",
    "test_runner_failed",
)
SECURITY_FAILURE_REASONS = (
    "none",
    "unknown",
    "assertion_failed",
    "harness_contract_failed",
    "security_runner_failed",
)
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
PROFILES = ("recommended", "full", "dev")
SANDBOXES = ("read-only", "workspace-write", "danger-full-access")
AUTH_POLICIES = ("isolated-api-key", "borrow-current", "current-home-full")
STRICT_AUTH_POLICIES = ("isolated-api-key", "borrow-current")
CODEX_ENVIRONMENT_POLICIES = ("isolated_api_key", "auth_borrowed_clean", "current_home_full")
STRICT_CODEX_ENVIRONMENT_POLICIES = ("isolated_api_key", "auth_borrowed_clean")
LIVE_EVIDENCE_LEVEL = "local_codex_cli_live_benchmark"
CURRENT_HOME_SMOKE_EVIDENCE_LEVEL = "current_home_integration_smoke"
CODEX_LIVE_EVIDENCE_SCOPES = ("smoke", "multi_case_ablation_3_run", "current_home_smoke")
STRONG_CODEX_LIVE_ASSERTION_CASE_MIN = 5
STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN = 3
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
            )
        )
    return cases


def validate_case_registry(data: Any, root: Path = ROOT) -> list[str]:
    """Return registry validation errors without raising."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["cases.yaml must be a mapping"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
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
        "prompt.md",
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
            "grading_mode",
            "publishable_for_strict",
            "benchmark_eligible",
            "benchmark_passed",
            "failure_category",
            "setup_failure_reason",
            "test_suite_failure_reason",
            "security_failure_reason",
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
            "evidence_scope_detail",
            "evidence_status",
            "effect_verdict",
            "effect_status",
            "effect_summary",
            "benchmark_mode",
            "codex_home_policy",
            "auth_policy",
            "codex_environment_policy",
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
            "setup_failure_reasons",
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
            "test_suite_failure_reason": TEST_SUITE_FAILURE_REASONS,
            "security_failure_reason": SECURITY_FAILURE_REASONS,
        }
        for field, allowed in reason_sets.items():
            value = payload.get(field)
            if value is not None and value not in allowed:
                errors.append(f"{schema_name}: invalid {field} {value}")
        for field in (
            "first_failure_excerpt",
            "setup_log_excerpt",
            "test_suite_log_excerpt",
            "security_log_excerpt",
        ):
            value = payload.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{schema_name}: {field} must be a string")
            elif isinstance(value, str) and len(value) > 1220:
                errors.append(f"{schema_name}: {field} must be bounded to about 1200 characters")
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
