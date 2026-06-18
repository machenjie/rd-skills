#!/usr/bin/env python3
"""Validate ChangeForge Validation Broker registry, schemas, and core policy."""

from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BROKER = SRC / "validation_broker"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker.command_resolver import resolve_validation_plan
from validation_broker.validation_policy import assess_validation_closure
from validation_broker.validation_result_parser import parse_validation_result


def main() -> int:
    errors: list[str] = []
    _validate_files(errors)
    _validate_schemas(errors)
    _validate_resolver(errors)
    _validate_parser_and_policy(errors)
    if errors:
        for error in errors:
            print(f"validate-validation-broker: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-validation-broker: validated validation broker registry, schemas, and policy.")
    return 0


def _validate_files(errors: list[str]) -> None:
    if not BROKER.is_dir():
        errors.append("missing src/validation_broker package")
        return
    for path in sorted(BROKER.rglob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path.relative_to(ROOT)} does not compile: {exc.msg}")


def _validate_schemas(errors: list[str]) -> None:
    for name in ("validation-command.v1.schema.json", "validation-result.v1.schema.json"):
        path = BROKER / "schemas" / name
        if not path.is_file():
            errors.append(f"missing schema: {path.relative_to(ROOT)}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
            continue
        if data.get("additionalProperties") is not False:
            errors.append(f"{path.relative_to(ROOT)} must set additionalProperties=false")
        serialized = json.dumps(data)
        for forbidden in ('"stdout"', '"stderr"', '"prompt"', '"env"', '"secret"'):
            if forbidden in serialized:
                errors.append(f"{path.relative_to(ROOT)} exposes forbidden field {forbidden}")


def _validate_resolver(errors: list[str]) -> None:
    cases = {
        "src/hook-runtime/scripts/changeforge_common.py": (
            "python3 scripts/validate-hooks.py",
            "python3 -m unittest discover -s tests/hook_runtime",
        ),
        "scripts/validate-hooks.py": (
            "python3 scripts/validate-hooks.py",
            "python3 -m unittest discover -s tests/hook_runtime",
        ),
        "src/registry/routing-rules.yaml": (
            "python3 scripts/validate-registry.py",
            "python3 scripts/eval-routing.py",
        ),
        "src/foundation/capabilities/test-strategy/SKILL.md": (
            "python3 scripts/validate-capabilities.py",
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
        ),
        "src/professional-skills/quality-test-gate/SKILL.md": (
            "python3 scripts/validate-skills.py",
            "python3 scripts/eval-skill-professionalism.py",
        ),
        "src/repository_intelligence/cache/repo_hash.py": (
            "python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json",
            "python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json",
        ),
        "scripts/index-repository.py": (
            "python3 scripts/index-repository.py --target . --out /tmp/changeforge-repo-graph.json",
            "python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json",
        ),
        "scripts/build-context-pack.py": (
            "python3 scripts/build-context-pack.py --task \"repository intelligence validation\" --target . --graph /tmp/changeforge-repo-graph.json --out /tmp/changeforge-context-pack.json",
            "python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json",
        ),
        "scripts/validate-repository-graph.py": (
            "python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json",
        ),
        "scripts/validate-context-pack.py": (
            "python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json",
        ),
        "src/project_memory/privacy.py": (
            "python3 scripts/validate-project-memory.py",
            "python3 -m unittest discover -s tests/project_memory",
        ),
        "scripts/review-project-memory.py": (
            "python3 scripts/validate-project-memory.py",
            "python3 -m unittest discover -s tests/project_memory",
        ),
        "scripts/promote-memory-candidate.py": (
            "python3 scripts/validate-project-memory.py",
            "python3 -m unittest discover -s tests/project_memory",
        ),
        "scripts/validate-project-memory.py": (
            "python3 scripts/validate-project-memory.py",
            "python3 -m unittest discover -s tests/project_memory",
        ),
        "src/trajectory/trajectory_analyzer.py": (
            "python3 scripts/validate-trajectory.py",
            "python3 -m unittest discover -s tests/trajectory",
        ),
        "scripts/inspect-trajectory.py": (
            "python3 scripts/validate-trajectory.py",
            "python3 -m unittest discover -s tests/trajectory",
        ),
        "scripts/validate-trajectory.py": (
            "python3 scripts/validate-trajectory.py",
            "python3 -m unittest discover -s tests/trajectory",
        ),
        "src/validation_broker/validation_result_parser.py": (
            "python3 scripts/validate-validation-broker.py",
            "python3 -m unittest discover -s tests/validation_broker",
        ),
        "scripts/resolve-validation.py": (
            "python3 scripts/validate-validation-broker.py",
            "python3 -m unittest discover -s tests/validation_broker",
        ),
        "scripts/validate-validation-broker.py": (
            "python3 scripts/validate-validation-broker.py",
            "python3 -m unittest discover -s tests/validation_broker",
        ),
        "scripts/review-agent-telemetry.py": (
            "python3 -m unittest discover -s tests/telemetry",
        ),
        "tests/telemetry/test_review_agent_telemetry.py": (
            "python3 -m unittest discover -s tests/telemetry",
        ),
        "evals/routing/cases.yaml": (
            "python3 scripts/eval-routing.py",
            "python3 scripts/eval-skill-professionalism.py",
        ),
        "reports/professional-scorecard.json": (
            "python3 scripts/build.py --profile recommended",
            "python3 scripts/validate-runtime-reference-links.py",
        ),
        "dist/codex/project/skill/SKILL.md": (
            "python3 scripts/build.py --profile recommended",
        ),
        "installers/install.py": (
            "python3 scripts/build.py --profile recommended",
            "python3 scripts/validate-installation.py",
        ),
        "scripts/build.py": (
            "python3 scripts/build.py --profile recommended",
            "python3 scripts/validate-installation.py",
        ),
        "docs/TELEMETRY.md": (
            "python3 -m unittest discover -s tests/telemetry",
            "python3 scripts/validate-productization-assets.py",
        ),
        "src/unowned/new_module.py": (
            "python3 -m unittest discover -s tests",
        ),
        "tests/unknown/test_sample.py": (
            "python3 -m unittest discover -s tests",
        ),
    }
    for changed_path, expected in cases.items():
        plan = resolve_validation_plan([changed_path])
        commands = _commands(plan, "recommended_commands")
        for command in expected:
            if command not in commands:
                errors.append(f"{changed_path} did not recommend {command}")
    unknown_plan = resolve_validation_plan(["experimental/unknown.file"])
    if not unknown_plan.get("conservative"):
        errors.append("unknown path must return a conservative plan")
    if "python3 -m unittest discover -s tests" not in _commands(
        unknown_plan, "recommended_commands"
    ):
        errors.append("unknown path must recommend broad tests")
    mixed_plan = resolve_validation_plan(["src/validation_broker/validation_policy.py", "unknown/file.bin"])
    if "unknown/file.bin" not in mixed_plan.get("unknown_paths", []):
        errors.append("mixed known and unknown paths must retain unknown path residual risk")


def _validate_parser_and_policy(errors: list[str]) -> None:
    weak = parse_validation_result(
        "Ran python3 scripts/validate-hooks.py.",
        changed_paths=["src/hook-runtime/scripts/changeforge_common.py"],
    )
    if weak["evidence_strength"] != "weak" or weak["outcome"] != "unknown":
        errors.append("command without outcome must be weak unknown evidence")
    negative = parse_validation_result("完成。未验证，无法运行。")
    if negative["evidence_strength"] != "negative":
        errors.append("negative validation disclosure must be negative evidence")
    zero_errors = parse_validation_result("Ran python3 scripts/validate-hooks.py: 0 errors.")
    if zero_errors["outcome"] != "pass":
        errors.append("zero-error validation output must parse as pass")
    nonzero_errors = parse_validation_result("Ran python3 scripts/validate-hooks.py: 1 error.")
    if nonzero_errors["outcome"] != "fail":
        errors.append("nonzero error validation output must parse as fail")
    stale = assess_validation_closure(
        "Done. Ran python3 scripts/validate-hooks.py, passed, exit 0.",
        {
            "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
            "risk_surfaces": ["hook-runtime"],
            "last_material_edit_index": 3,
            "last_validation_command_index": 2,
        },
    )
    result = stale["validation_result"]
    if not isinstance(result, dict) or result.get("negative_evidence_reason") != "stale":
        errors.append("validation before final edit must be stale")
    broker = stale.get("validation_broker_result")
    if not isinstance(broker, dict) or broker.get("closure_outcome") != "blocked":
        errors.append("stale validation must block the broker closure outcome")
    no_outcome = assess_validation_closure(
        "Ran python3 scripts/validate-hooks.py. Residual risk: pending outcome.",
        {
            "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
            "risk_surfaces": ["hook-runtime"],
        },
    ).get("validation_broker_result")
    if not isinstance(no_outcome, dict) or "validation_command_without_outcome" not in no_outcome.get(
        "negative_evidence",
        [],
    ):
        errors.append("command without outcome must be broker negative evidence")
    read_only = assess_validation_closure("Reviewed files only.", {"read_evidence_seen": True}).get(
        "validation_broker_result"
    )
    if not isinstance(read_only, dict) or read_only.get("closure_outcome") != "ready":
        errors.append("read-only turns must not require validation")


def _commands(plan: dict[str, object], field: str) -> list[str]:
    commands: list[str] = []
    for item in plan.get(field, []) or []:
        if isinstance(item, dict):
            commands.append(str(item.get("command", "")))
    return commands


if __name__ == "__main__":
    raise SystemExit(main())
