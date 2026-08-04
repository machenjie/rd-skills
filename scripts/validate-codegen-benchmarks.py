#!/usr/bin/env python3
"""Validate ChangeForge code generation benchmark definitions."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

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

from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from routing_scenarios import (
    load_release_routing_scenarios,
    project_release_contract,
    project_release_route_hints,
)


ROOT = Path(__file__).resolve().parents[1]
CODEGEN_DIR = ROOT / "evals" / "codegen"
REGISTRY_DIR = ROOT / "src" / "registry"
RELEASE_ROUTING_SCENARIOS = ROOT / "src" / "registry" / "release-routing-scenarios.yaml"

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
    "work_path",
    "agent_profile",
    "primary_skill",
    "layer3_skills",
    "review_skill",
)
VALID_WORK_PATHS = {"direct-task", "analyzed-work", "diagnosis", "review-only"}
WORK_PATH_PROFILE = {
    "direct-task": "task-agent",
    "analyzed-work": "task-agent",
    "diagnosis": "analysis-agent",
    "review-only": "review-agent",
}
FIXED_DEPTH_ROOT_LOOKUP_RE = re.compile(r"(\.\./){2,}|(\.\.\\){2,}|parents\[[1-9]")

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


def _load_registry_entries() -> tuple[
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, set[str]],
]:
    def _entries(path: Path, key: str) -> dict[str, set[str]]:
        if not path.is_file():
            return {}
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            return {}
        entries: dict[str, set[str]] = {}
        for entry in registry_items(data, key, path, []):
            if isinstance(entry, dict):
                value = entry.get("name") or entry.get("id")
                roles = entry.get("role_support") or []
                if isinstance(value, str) and value and isinstance(roles, list):
                    entries[value] = {
                        role for role in roles if isinstance(role, str) and role
                    }
        return entries

    professional = _entries(
        REGISTRY_DIR / "professional-skills.yaml",
        "professional_skills",
    )
    professional_candidates: dict[str, set[str]] = {}
    professional_path = REGISTRY_DIR / "professional-skills.yaml"
    try:
        professional_data = load_yaml_file(professional_path)
    except ValidationProblem:
        professional_data = {}
    for entry in registry_items(
        professional_data,
        "professional_skills",
        professional_path,
        [],
    ):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        candidates = _as_string_list(entry.get("layer3_candidates"))
        if (
            isinstance(name, str)
            and entry.get("task_routable") is True
            and candidates is not None
        ):
            professional_candidates[name] = set(candidates)
    layer3 = _entries(REGISTRY_DIR / "foundation-skills.yaml", "foundation_skills")
    layer3.update(_entries(REGISTRY_DIR / "domain-skills.yaml", "domain_skills"))
    return professional, professional_candidates, layer3


def _load_release_routing_projections(errors: list[str]) -> dict[str, dict[str, Any]]:
    """Project core release-routing scenarios into codegen quality metadata."""
    try:
        rows = load_release_routing_scenarios(RELEASE_ROUTING_SCENARIOS)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return {}
    projections: dict[str, dict[str, Any]] = {}
    for row in rows:
        codegen_case_id = row["codegen_case_id"]
        if codegen_case_id in projections:
            errors.append(
                "release routing projection contains duplicate codegen_case_id "
                f"{codegen_case_id!r}"
            )
            continue
        projections[codegen_case_id] = {
            "release_contract": project_release_contract(row),
            "route_hints": project_release_route_hints(row),
        }
    return projections


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


def _markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    level: int | None = None
    pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        if match.group(2).strip().casefold() == heading.casefold():
            start = index + 1
            level = len(match.group(1))
            break
    if start is None or level is None:
        return ""
    out: list[str] = []
    for line in lines[start:]:
        match = pattern.match(line)
        if match and len(match.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def _expected_commands_from_readme(path: Path) -> list[str]:
    section = _markdown_section(path.read_text(encoding="utf-8"), "Expected Commands")
    return [match.strip() for match in re.findall(r"`([^`]+)`", section)]


def _expected_commands_from_script(path: Path) -> list[str]:
    commands: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*#\s*expected-command:\s*(.+?)\s*$", line)
        if match:
            commands.append(match.group(1).strip())
    return commands


def _validate_expected_command_contract(case_dir: Path, errors: list[str]) -> None:
    readme_path = case_dir / "test-suite" / "README.md"
    run_path = case_dir / "test-suite" / "run.sh"
    if not readme_path.is_file() or not run_path.is_file():
        return
    readme_commands = _expected_commands_from_readme(readme_path)
    script_commands = _expected_commands_from_script(run_path)
    if not readme_commands:
        errors.append(f"{relpath(ROOT, readme_path)}: Expected Commands must declare run.sh")
    elif readme_commands != script_commands:
        errors.append(
            f"{relpath(ROOT, readme_path)}: Expected Commands {readme_commands!r} "
            f"do not match {relpath(ROOT, run_path)} metadata {script_commands!r}"
        )


def _real_assertion_files(case_dir: Path) -> list[Path]:
    roots = (
        case_dir / "test-suite" / "tests",
        case_dir / "security-checks" / "security_tests",
    )
    return sorted(
        path
        for root in roots
        if root.is_dir()
        for path in root.rglob("test_*.py")
        if path.is_file()
    )


def _validate_assertion_contract(case_dir: Path, errors: list[str]) -> None:
    for path in _real_assertion_files(case_dir):
        rel = relpath(ROOT, path)
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            compile(text, str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"{rel}: invalid assertion syntax: {exc}")
            continue
        runnable_signal = (
            "def main(" in text
            or "unittest.TestCase" in text
            or re.search(
                r"(?m)^def test_[a-zA-Z0-9_]+\(\)\s*(?:->\s*[^:]+)?\s*:",
                text,
            )
            is not None
        )
        if not runnable_signal:
            errors.append(
                f"{rel}: assertion must define main(), unittest.TestCase, or a "
                "zero-argument test function"
            )


def _validate_readme_categories(errors: list[str]) -> None:
    path = CODEGEN_DIR / "README.md"
    if not path.is_file():
        errors.append("evals/codegen/README.md: missing benchmark documentation")
        return
    text = path.read_text(encoding="utf-8")
    documented = set(re.findall(r"(?m)^  ([a-z0-9-]+)/\s*$", text))
    expected = set(EXPECTED_BENCHMARKS)
    if documented != expected:
        errors.append(
            "evals/codegen/README.md: category list differs from manifest; "
            f"missing={sorted(expected - documented)}, extra={sorted(documented - expected)}"
        )


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


def _validate_named_role(
    rel: str,
    field: str,
    value: Any,
    entries: dict[str, set[str]],
    required_role: str,
    errors: list[str],
) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{rel}: route_hints.{field} must be a non-empty string")
        return
    roles = entries.get(value)
    if roles is None:
        errors.append(f"{rel}: route_hints.{field} contains unknown name '{value}'")
    elif required_role not in roles:
        errors.append(
            f"{rel}: route_hints.{field} '{value}' does not support {required_role}"
        )


def _validate_expected_qualities(
    path: Path,
    category: str,
    case_id: str,
    registry_entries: tuple[
        dict[str, set[str]],
        dict[str, set[str]],
        dict[str, set[str]],
    ],
    release_routing_projections: dict[str, dict[str, Any]],
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

    codegen_case_id = f"{category}/{case_id}"
    projection = release_routing_projections.get(codegen_case_id)
    actual_release_contract = loaded.get("release_contract")
    expected_release_contract = projection.get("release_contract") if projection else None
    if (
        expected_release_contract is not None
        and actual_release_contract != expected_release_contract
    ):
        errors.append(
            f"{rel}: release_contract disagrees with release-routing-scenarios.yaml projection"
        )
    if expected_release_contract is None and actual_release_contract is not None:
        errors.append(f"{rel}: release_contract has no core release routing scenario")

    route_hints = loaded.get("route_hints")
    if not isinstance(route_hints, dict):
        errors.append(f"{rel}: 'route_hints' must be a mapping")
        return
    if projection is not None and route_hints != projection["route_hints"]:
        errors.append(f"{rel}: route_hints disagree with release-routing-scenarios.yaml projection")

    unexpected_fields = set(route_hints) - set(ROUTE_HINT_FIELDS)
    for field in sorted(unexpected_fields):
        errors.append(f"{rel}: obsolete or unknown route_hints field '{field}'")

    work_path = route_hints.get("work_path")
    if work_path not in VALID_WORK_PATHS:
        errors.append(
            f"{rel}: route_hints.work_path must be one of {sorted(VALID_WORK_PATHS)}"
        )
    agent_profile = route_hints.get("agent_profile")
    expected_profile = WORK_PATH_PROFILE.get(str(work_path))
    if agent_profile != expected_profile:
        errors.append(
            f"{rel}: route_hints.agent_profile must be {expected_profile!r} for {work_path!r} work"
        )

    professional, professional_candidates, layer3 = registry_entries
    primary_skill = route_hints.get("primary_skill")
    _validate_named_role(
        rel,
        "primary_skill",
        primary_skill,
        professional,
        str(expected_profile or "task-agent"),
        errors,
    )
    if route_hints.get("review_skill") is not None:
        _validate_named_role(
            rel,
            "review_skill",
            route_hints.get("review_skill"),
            professional,
            "review-agent",
            errors,
        )
    if isinstance(primary_skill, str) and primary_skill not in professional_candidates:
        errors.append(
            f"{rel}: route_hints.primary_skill '{primary_skill}' is not task-routable"
        )
    review_skill = route_hints.get("review_skill")
    if isinstance(review_skill, str) and review_skill not in professional_candidates:
        errors.append(
            f"{rel}: route_hints.review_skill '{review_skill}' is not task-routable"
        )

    layer3_values = _as_string_list(route_hints.get("layer3_skills"))
    if layer3_values is None:
        errors.append(f"{rel}: route_hints.layer3_skills must be a list of strings")
        layer3_values = []
    if len(layer3_values) > 3:
        errors.append(f"{rel}: route_hints.layer3_skills must contain at most 3 entries")
    if len(set(layer3_values)) != len(layer3_values):
        errors.append(f"{rel}: route_hints.layer3_skills must not contain duplicates")
    for value in layer3_values:
        roles = layer3.get(value)
        if roles is None:
            errors.append(
                f"{rel}: route_hints.layer3_skills contains unknown name '{value}'"
            )
        elif expected_profile not in roles:
            errors.append(
                f"{rel}: route_hints.layer3_skills '{value}' does not support {expected_profile}"
            )
        elif isinstance(primary_skill, str) and value not in professional_candidates.get(
            primary_skill, set()
        ):
            errors.append(
                f"{rel}: route_hints.layer3_skills '{value}' is not a targeted "
                f"reference of primary Skill '{primary_skill}'"
            )


def _validate_case(
    case_dir: Path,
    category: str,
    registry_entries: tuple[
        dict[str, set[str]],
        dict[str, set[str]],
        dict[str, set[str]],
    ],
    release_routing_projections: dict[str, dict[str, Any]],
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
                registry_entries,
                release_routing_projections,
                errors,
            )

    for directory_name in REQUIRED_CHILD_DIRS:
        _validate_directory_readme(case_dir, directory_name, errors)
    _validate_expected_command_contract(case_dir, errors)
    _validate_starter_setup_contract(case_dir, errors)
    _validate_assertion_contract(case_dir, errors)


def _validate_starter_setup_contract(case_dir: Path, errors: list[str]) -> None:
    setup_path = case_dir / "starter-repo" / "setup.sh"
    rel = relpath(ROOT, setup_path)
    if not setup_path.is_file():
        errors.append(f"{rel}: missing required setup script")
        return
    text = setup_path.read_text(encoding="utf-8", errors="replace")
    if "CHANGEFORGE_CODEGEN_ROOT" not in text:
        errors.append(f"{rel}: setup script must honor CHANGEFORGE_CODEGEN_ROOT")
    if "codegen_benchmark_harness.py" not in text:
        errors.append(f"{rel}: setup script must invoke codegen_benchmark_harness.py")
    if FIXED_DEPTH_ROOT_LOOKUP_RE.search(text):
        errors.append(f"{rel}: setup script must not use fixed-depth parent traversal")
    if ".parents" not in text and "find_codegen_root" not in text:
        errors.append(f"{rel}: setup script must use a parent walk or shared root-location helper")


def main() -> int:
    errors: list[str] = []

    if not CODEGEN_DIR.exists():
        print(
            "validate-codegen-benchmarks: missing evals/codegen directory.",
            file=sys.stderr,
        )
        return 1

    registry_entries = _load_registry_entries()
    if not all(registry_entries):
        errors.append("registry data appears empty or unreadable; run validate-registry first")
    release_routing_projections = _load_release_routing_projections(errors)

    category_dirs = {path.name: path for path in visible_child_dirs(CODEGEN_DIR)}
    _validate_readme_categories(errors)
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
            _validate_case(
                case_dir,
                category,
                registry_entries,
                release_routing_projections,
                errors,
            )

    assertion_backed_count = sum(
        bool(_real_assertion_files(CODEGEN_DIR / category / case_id))
        for category, case_ids in EXPECTED_BENCHMARKS.items()
        for case_id in case_ids
    )
    if assertion_backed_count < 3:
        errors.append("codegen suite requires at least three assertion-backed benchmarks")

    if errors:
        return fail_many("validate-codegen-benchmarks", errors)

    print(
        f"validate-codegen-benchmarks: validated {benchmark_count} benchmark(s); "
        f"assertion-backed={assertion_backed_count}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
