#!/usr/bin/env python3
"""Validate ChangeForge code generation benchmark definitions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable

from validation_utils import (
    NAME_RE,
    ValidationProblem,
    fail_many,
    heading_titles,
    load_yaml_file,
    registry_items,
    relpath,
    validate_no_personal_references,
    visible_child_dirs,
)


ROOT = Path(__file__).resolve().parents[1]
CODEGEN_DIR = ROOT / "evals" / "codegen"
REGISTRY_DIR = ROOT / "src" / "registry"

EXPECTED_BENCHMARKS: dict[str, tuple[str, ...]] = {
    "backend": (
        "idempotent-payment-create",
        "object-auth-order-read",
        "webhook-signature-replay",
    ),
    "frontend": (
        "accessible-form-error-state",
        "optimistic-ui-rollback",
    ),
    "data-api": (
        "backward-compatible-api-field",
        "large-table-online-migration",
    ),
}

VALID_COMPLEXITIES = {"L2", "L3", "L4", "L5"}
REQUIRED_ROOT_FILES = (
    "prompt.md",
    "expected-qualities.yaml",
    "review-rubric.md",
)
REQUIRED_CHILD_DIRS = (
    "starter-repo",
    "test-suite",
    "security-checks",
)
REQUIRED_LIST_FIELDS = (
    "focus",
    "expected_outcomes",
    "required_qualities",
    "forbidden_shortcuts",
    "evidence",
)
ROUTE_HINT_FIELDS = (
    "skills",
    "capabilities",
    "domain_extensions",
    "quality_gates",
)

REQUIRED_MARKDOWN_HEADINGS: dict[str, tuple[str, ...]] = {
    "prompt.md": (
        "Benchmark Prompt",
        "Task",
        "Context",
        "Requirements",
        "Constraints",
        "Deliverables",
        "Completion Evidence",
    ),
    "review-rubric.md": (
        "Review Rubric",
        "Passing Standard",
        "Scoring",
        "Automatic Failure Conditions",
        "Reviewer Notes",
    ),
    "starter-repo/README.md": (
        "Starter Repo",
        "Stack",
        "Initial State",
        "Files",
        "Constraints",
    ),
    "test-suite/README.md": (
        "Test Suite",
        "Required Checks",
        "Fixtures",
        "Expected Commands",
        "Regression Cases",
    ),
    "security-checks/README.md": (
        "Security Checks",
        "Threat Surface",
        "Required Checks",
        "Rejection Cases",
    ),
}


def _load_registry_names() -> tuple[set[str], set[str], set[str], set[str]]:
    def _names(path: Path, key: str) -> set[str]:
        if not path.is_file():
            return set()
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            return set()
        names: set[str] = set()
        for entry in registry_items(data, key, path, []):
            if isinstance(entry, dict):
                value = entry.get("name") or entry.get("id")
                if isinstance(value, str) and value:
                    names.add(value)
            elif isinstance(entry, str):
                names.add(entry)
        return names

    skills = _names(REGISTRY_DIR / "skills.yaml", "skills")
    capabilities = _names(REGISTRY_DIR / "capabilities.yaml", "capabilities")
    extensions = _names(
        REGISTRY_DIR / "domain-extensions.yaml",
        "domain_extensions",
    )
    gates = _load_quality_gates()
    return skills, capabilities, extensions, gates


def _load_quality_gates() -> set[str]:
    path = REGISTRY_DIR / "routing-rules.yaml"
    if not path.is_file():
        return set()
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return set()
    if not isinstance(data, dict):
        return set()
    return {
        str(item).strip().casefold()
        for item in data.get("quality_gates", []) or []
        if isinstance(item, str) and item.strip()
    }


def _as_string_list(value: Any) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        out.append(item.strip())
    return out


def _validate_markdown(
    path: Path,
    relative_name: str,
    errors: list[str],
) -> None:
    rel = relpath(ROOT, path)
    if not path.is_file():
        errors.append(f"{rel}: missing required markdown file")
        return

    text = path.read_text(encoding="utf-8")
    validate_no_personal_references(text, rel, errors)
    if len(text.strip()) < 120:
        errors.append(f"{rel}: benchmark content is too thin")

    required = REQUIRED_MARKDOWN_HEADINGS[relative_name]
    titles = {title.casefold() for title in heading_titles(text)}
    for title in required:
        if title.casefold() not in titles:
            errors.append(f"{rel}: missing required heading '{title}'")


def _validate_directory_readme(
    case_dir: Path,
    directory_name: str,
    errors: list[str],
) -> None:
    directory = case_dir / directory_name
    rel_dir = relpath(ROOT, directory)
    if not directory.is_dir():
        errors.append(f"{rel_dir}: missing required directory")
        return
    visible_files = [path for path in directory.iterdir() if not path.name.startswith(".")]
    if not visible_files:
        errors.append(f"{rel_dir}: directory must not be empty")
    _validate_markdown(
        directory / "README.md",
        f"{directory_name}/README.md",
        errors,
    )


def _validate_list_field(
    data: dict[str, Any],
    field: str,
    rel: str,
    errors: list[str],
) -> list[str]:
    values = _as_string_list(data.get(field))
    if values is None:
        errors.append(f"{rel}: '{field}' must be a list of non-empty strings")
        return []
    if len(values) < 2:
        errors.append(f"{rel}: '{field}' must contain at least two entries")
    return values


def _validate_membership(
    rel: str,
    field: str,
    values: Iterable[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    for value in values:
        if value not in allowed:
            errors.append(f"{rel}: {field} contains unknown name '{value}'")


def _validate_quality_gates(
    rel: str,
    gates: list[str],
    allowed_gates: set[str],
    errors: list[str],
) -> None:
    for gate in gates:
        if gate.casefold() not in allowed_gates:
            errors.append(f"{rel}: route_hints.quality_gates contains unknown gate '{gate}'")
    gate_set = {gate.casefold() for gate in gates}
    for required_gate in ("implementation gate", "test gate"):
        if required_gate not in gate_set:
            errors.append(f"{rel}: route_hints.quality_gates must include '{required_gate}'")


def _validate_expected_qualities(
    path: Path,
    category: str,
    case_id: str,
    registry_names: tuple[set[str], set[str], set[str], set[str]],
    errors: list[str],
) -> None:
    rel = relpath(ROOT, path)
    if not path.is_file():
        errors.append(f"{rel}: missing required file")
        return

    text = path.read_text(encoding="utf-8")
    validate_no_personal_references(text, rel, errors)
    try:
        loaded = load_yaml_file(path)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return
    if not isinstance(loaded, dict):
        errors.append(f"{rel}: expected-qualities.yaml must be a mapping")
        return

    if loaded.get("id") != case_id:
        errors.append(f"{rel}: 'id' must match directory name '{case_id}'")
    if loaded.get("category") != category:
        errors.append(f"{rel}: 'category' must match parent directory '{category}'")
    if loaded.get("complexity") not in VALID_COMPLEXITIES:
        errors.append(f"{rel}: 'complexity' must be one of {sorted(VALID_COMPLEXITIES)}")

    for field in REQUIRED_LIST_FIELDS:
        _validate_list_field(loaded, field, rel, errors)

    route_hints = loaded.get("route_hints")
    if not isinstance(route_hints, dict):
        errors.append(f"{rel}: 'route_hints' must be a mapping")
        return

    skills, capabilities, extensions, allowed_gates = registry_names
    route_values: dict[str, list[str]] = {}
    for field in ROUTE_HINT_FIELDS:
        values = _as_string_list(route_hints.get(field))
        if values is None:
            errors.append(f"{rel}: route_hints.{field} must be a list of strings")
            values = []
        if field != "domain_extensions" and not values:
            errors.append(f"{rel}: route_hints.{field} must not be empty")
        route_values[field] = values

    _validate_membership(rel, "route_hints.skills", route_values["skills"], skills, errors)
    _validate_membership(
        rel,
        "route_hints.capabilities",
        route_values["capabilities"],
        capabilities,
        errors,
    )
    _validate_membership(
        rel,
        "route_hints.domain_extensions",
        route_values["domain_extensions"],
        extensions,
        errors,
    )
    _validate_quality_gates(rel, route_values["quality_gates"], allowed_gates, errors)


def _validate_case(
    case_dir: Path,
    category: str,
    registry_names: tuple[set[str], set[str], set[str], set[str]],
    errors: list[str],
) -> None:
    case_id = case_dir.name
    rel = relpath(ROOT, case_dir)
    if not NAME_RE.fullmatch(case_id):
        errors.append(f"{rel}: benchmark directory must be lowercase kebab-case")

    for filename in REQUIRED_ROOT_FILES:
        path = case_dir / filename
        if filename.endswith(".md"):
            _validate_markdown(path, filename, errors)
        else:
            _validate_expected_qualities(
                path,
                category,
                case_id,
                registry_names,
                errors,
            )

    for directory_name in REQUIRED_CHILD_DIRS:
        _validate_directory_readme(case_dir, directory_name, errors)


def main() -> int:
    errors: list[str] = []

    if not CODEGEN_DIR.exists():
        print(
            "validate-codegen-benchmarks: missing evals/codegen directory.",
            file=sys.stderr,
        )
        return 1

    registry_names = _load_registry_names()
    if not all(registry_names):
        errors.append("registry data appears empty or unreadable; run validate-registry first")

    category_dirs = {path.name: path for path in visible_child_dirs(CODEGEN_DIR)}
    expected_categories = set(EXPECTED_BENCHMARKS)
    actual_categories = set(category_dirs)
    for missing in sorted(expected_categories - actual_categories):
        errors.append(f"evals/codegen: missing category '{missing}'")
    for unexpected in sorted(actual_categories - expected_categories):
        errors.append(f"evals/codegen: unexpected category '{unexpected}'")

    benchmark_count = 0
    for category, expected_case_ids in EXPECTED_BENCHMARKS.items():
        category_dir = CODEGEN_DIR / category
        case_dirs = {path.name: path for path in visible_child_dirs(category_dir)}
        expected_cases = set(expected_case_ids)
        actual_cases = set(case_dirs)
        for missing in sorted(expected_cases - actual_cases):
            errors.append(f"evals/codegen/{category}: missing benchmark '{missing}'")
        for unexpected in sorted(actual_cases - expected_cases):
            errors.append(f"evals/codegen/{category}: unexpected benchmark '{unexpected}'")
        for case_id in expected_case_ids:
            case_dir = case_dirs.get(case_id)
            if case_dir is None:
                continue
            benchmark_count += 1
            _validate_case(case_dir, category, registry_names, errors)

    if errors:
        return fail_many("validate-codegen-benchmarks", errors)

    print(
        f"validate-codegen-benchmarks: validated {benchmark_count} benchmark(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())