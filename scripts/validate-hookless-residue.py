#!/usr/bin/env python3
"""Reject obsolete pre-hookless runtime mechanisms in source and built output."""

from __future__ import annotations

import re
from pathlib import Path

from validation_utils import fail_many


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATHS = (
    "runtime",
    "src/hook-runtime",
    "src/runtime_governance",
    "src/process_governance",
    "src/executor_backends",
    "src/business_intelligence",
    "src/project_memory",
    "src/repository_intelligence",
    "src/trajectory",
    "src/validation_broker",
    "src/registry/specialist-packs.yaml",
    "src/registry/review-packs.yaml",
    "src/registry/routing-rules.yaml",
    "src/registry/stage-model.yaml",
    "scripts/validate-hooks.py",
    "tests/hook_runtime",
    "tests/hooks",
    "tests/runtime_governance",
    "tests/project_memory",
    "tests/repository_intelligence",
    "tests/trajectory",
    "tests/validation_broker",
    "tests/telemetry",
    "scripts/validate-validation-broker.py",
    "scripts/validate-trajectory.py",
    "scripts/validate-project-memory.py",
    "scripts/validate-repository-graph.py",
    "evals/codex-live",
    "reports/codex-live-runs",
    "reports/codex-live-benchmark-summary.json",
    "reports/codex-live-benchmark-summary.md",
    "reports/hookless-baseline-88f1800.json",
    "reports/hookless-baseline-88f1800.md",
    ".github/workflows/codex-live-evidence.yml",
    ".github/workflows/recommended-release-readiness.yml",
    "scripts/codex_live_benchmark_lib.py",
    "scripts/generate-codex-live-summary.py",
    "scripts/grade-codex-live-benchmarks.py",
    "scripts/live_observation.py",
    "scripts/parse-codex-jsonl.py",
    "scripts/run-codex-live-benchmarks.py",
    "scripts/stage-recommended-release.py",
    "scripts/validate-adoption-thresholds.py",
    "scripts/validate-codex-live-benchmark-reports.py",
    "scripts/validate-codex-live-logs.py",
    "scripts/validate-release-behavior.py",
    "tests/test_codex_live_benchmarks.py",
    "tests/test_release_behavior.py",
    "tests/scripts/test_routing_scenario_authority.py",
    ".dev/validation-p0-fixes.tmp",
    ".dev/validation-p0-fixes-remaining.tmp",
)
FORBIDDEN_CLI_TOKENS = (
    "--with-hooks",
    "--without-hooks",
    "--hook-profile",
    "--professional-injection",
    "activation-level",
)
FORBIDDEN_HOOKLESS_AI_CONTENT_TOKENS = (
    "tests/hook_runtime",
    "tests/fixtures/hooks",
    "tests/hooks",
    "hook reminder behavior",
    "hook fixture",
)
FORBIDDEN_HOOKLESS_AI_CONTENT_PATTERNS = {
    "tests/hook_runtime": re.compile(
        r"(?<![a-z0-9_-])tests/hook_runtime(?![a-z0-9_-])", re.IGNORECASE
    ),
    "tests/fixtures/hooks": re.compile(
        r"(?<![a-z0-9_-])tests/fixtures/hooks(?![a-z0-9_-])", re.IGNORECASE
    ),
    "tests/hooks": re.compile(
        r"(?<![a-z0-9_-])tests/hooks(?![a-z0-9_-])", re.IGNORECASE
    ),
    "hook reminder behavior": re.compile(
        r"\bhook reminder behavior\b", re.IGNORECASE
    ),
    "hook fixture": re.compile(r"\bhook fixture\b", re.IGNORECASE),
}
FORBIDDEN_AI_CONTENT_TOKENS = (
    "repository_graph:",
    "project_memory:",
    "execution_observable",
    "finding_id",
    "runtime_id",
    "capsule_origin",
    "dispatch_cursor",
    "evidence_ledger",
    "runtime_digest",
    "runtime_projection",
    "process_phase_ledger",
    "route_repair",
    *FORBIDDEN_HOOKLESS_AI_CONTENT_TOKENS,
)
FORBIDDEN_LIVE_BENCHMARK_TOKENS = (
    "codex_live_benchmark_lib",
    "run-codex-live-benchmarks.py",
    "generate-codex-live-summary.py",
    "grade-codex-live-benchmarks.py",
    "validate-codex-live-benchmark-reports.py",
    "validate-codex-live-logs.py",
    "live_observation.py",
    "parse-codex-jsonl.py",
    "stage-recommended-release.py",
    "validate-adoption-thresholds.py",
    "validate-release-behavior.py",
    "CHANGEFORGE_RUN_CODEX_LIVE",
    "CHANGEFORGE_LIVE_OBSERVER",
    "--require-live",
)
LIVE_BENCHMARK_TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".tmp",
    ".yaml",
    ".yml",
}
LIVE_BENCHMARK_TOKEN_ALLOWLIST = {
    Path("scripts/validate-hookless-residue.py"),
    Path("tests/scripts/test_validate_hookless_residue.py"),
}
OBSOLETE_DISPLAY_NAMES = ("Change Impact Analyzer",)
OBSOLETE_DISPLAY_NAME_ALLOWLIST = {
    Path("config/professionalism-baseline.yaml"),
    Path("scripts/validate-skill-routing.py"),
    Path("scripts/validate-hookless-residue.py"),
}
FORBIDDEN_BYTECODE_STEMS = tuple(
    sorted(
        {
            Path(value).stem
            for value in FORBIDDEN_PATHS
            if Path(value).suffix == ".py"
        }
    )
)


def _forbidden_path_errors(root: Path) -> list[str]:
    return [
        f"forbidden path remains: {value}"
        for value in FORBIDDEN_PATHS
        if (root / value).exists()
    ]


def _is_live_benchmark_text(path: Path) -> bool:
    if path.suffix in LIVE_BENCHMARK_TEXT_SUFFIXES:
        return True
    if path.suffix:
        return False
    with path.open("rb") as stream:
        return stream.read(2) == b"#!"


def _live_benchmark_token_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or not _is_live_benchmark_text(path)
            or any(part in {".git", ".venv", "venv", "__pycache__", "dist"} for part in path.parts)
        ):
            continue
        relative = path.relative_to(root)
        if any(
            relative == Path(value) or Path(value) in relative.parents
            for value in FORBIDDEN_PATHS
        ):
            continue
        if relative in LIVE_BENCHMARK_TOKEN_ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in FORBIDDEN_LIVE_BENCHMARK_TOKENS:
            if token in text:
                errors.append(f"{relative} contains removed live-benchmark token {token!r}")
    return errors


def _forbidden_bytecode_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*.pyc"):
        if not path.is_file() or "__pycache__" not in path.parts:
            continue
        for stem in FORBIDDEN_BYTECODE_STEMS:
            if path.name == f"{stem}.pyc" or path.name.startswith(f"{stem}."):
                errors.append(
                    f"{path.relative_to(root)} is bytecode for removed source {stem!r}"
                )
                break
    return errors


def _forbidden_ai_content_token_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for path in (root / "src").rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        folded = text.casefold()
        for token in FORBIDDEN_AI_CONTENT_TOKENS:
            if token in FORBIDDEN_HOOKLESS_AI_CONTENT_TOKENS:
                continue
            if token in folded:
                errors.append(
                    f"{path.relative_to(root)} contains obsolete AI protocol token {token}"
                )
        for block in re.split(r"\n\s*\n", text):
            normalized = " ".join(block.split())
            for token, pattern in FORBIDDEN_HOOKLESS_AI_CONTENT_PATTERNS.items():
                matches = list(pattern.finditer(normalized))
                if any(
                    not _is_historical_hookless_prohibition(
                        normalized, match, pattern
                    )
                    for match in matches
                ):
                    errors.append(
                        f"{path.relative_to(root)} contains obsolete AI protocol token {token}"
                    )
    return errors


def _is_historical_hookless_prohibition(
    block: str,
    token_match: re.Match[str],
    token_pattern: re.Pattern[str],
) -> bool:
    subject = token_pattern.pattern
    optional_subject_suffix = r"(?:\s+(?:path|directory|fixture|behavior))?"
    prohibition = r"(?:must not|do not|never)"
    restore = r"(?:restor(?:e|ed)|reintroduc(?:e|ed))"
    safe_patterns = (
        re.compile(
            rf"\b(?:removed|obsolete|forbidden)\b\s+(?:the\s+)?"
            rf"{subject}{optional_subject_suffix}\s+{prohibition}\s+"
            rf"(?:be\s+)?{restore}\b",
            re.IGNORECASE,
        ),
        re.compile(
            rf"{subject}{optional_subject_suffix}\s+{prohibition}\s+"
            rf"(?:be\s+)?{restore}\b",
            re.IGNORECASE,
        ),
        re.compile(
            rf"\b{prohibition}\s+{restore}\s+"
            rf"(?:(?:the|a|an|this|that|these|those|removed|obsolete|forbidden)\s+){{0,4}}"
            rf"{subject}{optional_subject_suffix}",
            re.IGNORECASE,
        ),
    )
    return any(
        safe.start() <= token_match.start() and token_match.end() <= safe.end()
        for pattern in safe_patterns
        for safe in pattern.finditer(block)
    )


def main() -> int:
    errors = _forbidden_path_errors(ROOT)
    errors.extend(_live_benchmark_token_errors(ROOT))
    errors.extend(_forbidden_bytecode_errors(ROOT))
    for path in (
        ROOT / "scripts" / "build.py",
        ROOT / "installers" / "install.py",
        ROOT / "installers" / "upgrade.py",
        ROOT / "installers" / "uninstall.py",
        ROOT / "installers" / "doctor.py",
    ):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_CLI_TOKENS:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)} contains obsolete CLI token {token}")
    errors.extend(_forbidden_ai_content_token_errors(ROOT))
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in {".md", ".yaml", ".yml", ".json", ".py"}
            or ".git" in path.parts
            or "dist" in path.parts
        ):
            continue
        relative = path.relative_to(ROOT)
        if relative in OBSOLETE_DISPLAY_NAME_ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for display_name in OBSOLETE_DISPLAY_NAMES:
            if display_name in text:
                errors.append(f"{relative} contains obsolete display name {display_name!r}")
    dist = ROOT / "dist"
    if dist.is_dir():
        legacy_copilot = dist / "copilot" / "project" / ".github" / "copilot" / "agents"
        if legacy_copilot.exists():
            errors.append(f"built residue directory: {legacy_copilot.relative_to(ROOT)}")
        for path in dist.rglob("*"):
            if path.is_dir() and path.name in {".changeforge-packs", ".changeforge-control", "hooks", "runtime_governance"}:
                errors.append(f"built residue directory: {path.relative_to(ROOT)}")
            if path.is_file() and (
                path.name == ".changeforge-hook-manifest.json"
                or path.name in {"changeforge-hooks.json", "settings.changeforge-hooks.fragment.json", "hooks.json"}
                or path.name.startswith("changeforge_") and path.suffix == ".py"
            ):
                errors.append(f"built residue file: {path.relative_to(ROOT)}")
    if errors:
        return fail_many("validate-hookless-residue", errors)
    print("validate-hookless-residue: source, CLI, build, and installation paths are free of obsolete runtime mechanisms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
