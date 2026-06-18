"""Deterministic validation command registry for ChangeForge."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fnmatch import fnmatch
from typing import Iterable


LEVELS = {"narrow", "module", "full", "unknown"}
SRC_PREFIX = "src/"
REGISTRY_PATH_PATTERN = SRC_PREFIX + "registry/**"


@dataclass(frozen=True)
class ValidationCommand:
    """One registry command with its intended coverage."""

    command: str
    level: str
    reason: str
    category: str
    covered_path_patterns: tuple[str, ...]
    covered_risk_surfaces: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["covered_path_patterns"] = list(self.covered_path_patterns)
        data["covered_risk_surfaces"] = list(self.covered_risk_surfaces)
        return data


REGISTRY: dict[str, dict[str, object]] = {
    "hook_runtime": {
        "path_patterns": (
            "src/hook-runtime/**",
            "tests/hook_runtime/**",
        ),
        "risk_surfaces": (
            "hook-runtime",
            "tool-permission-sandbox",
            "agent-workflow-state",
        ),
        "narrow": (
            ("python3 scripts/validate-hooks.py", "hook runtime changed"),
            ("python3 -m unittest discover -s tests/hook_runtime", "hook runtime tests changed"),
        ),
        "full": (
            ("python3 -m unittest discover -s tests", "hook runtime change can affect shared tests"),
            ("python3 scripts/build.py --profile recommended", "hook runtime must build into dist artifacts"),
        ),
    },
    "registry": {
        "path_patterns": (REGISTRY_PATH_PATTERN,),
        "risk_surfaces": ("registry", "routing", "skill-selection"),
        "narrow": (
            ("python3 scripts/validate-registry.py", "registry source changed"),
            ("python3 scripts/eval-routing.py", "routing behavior may change"),
        ),
        "full": (
            (
                "python3 scripts/validate-professional-routing-coverage.py",
                "registry changes can affect professional routing coverage",
            ),
            ("python3 scripts/build.py --profile recommended", "registry change must build into runtime artifacts"),
        ),
    },
    "capability": {
        "path_patterns": ("src/foundation/capabilities/**",),
        "risk_surfaces": ("capability", "quality-gate", "skill-authoring"),
        "narrow": (
            ("python3 scripts/validate-capabilities.py", "foundation capability changed"),
            (
                "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
                "capability coverage matrix may change",
            ),
        ),
        "full": (
            (
                "python3 scripts/validate-professionalism-regression.py --strict",
                "capability changes can regress professional behavior",
            ),
            ("python3 scripts/build.py --profile recommended", "capability change must build into runtime skills"),
        ),
    },
    "professional_skill": {
        "path_patterns": ("src/professional-skills/**",),
        "risk_surfaces": ("professional-skill", "quality-gate", "skill-authoring"),
        "narrow": (
            ("python3 scripts/validate-skills.py", "professional skill changed"),
            ("python3 scripts/eval-skill-professionalism.py", "professional skill behavior may change"),
        ),
        "full": (
            (
                "python3 scripts/eval-professional-benchmarks.py",
                "professional skill benchmark behavior may change",
            ),
            ("python3 scripts/build.py --profile recommended", "professional skill must build into runtime skills"),
        ),
    },
    "docs": {
        "path_patterns": (
            "docs/**",
            "README.md",
        ),
        "risk_surfaces": ("docs", "productization", "release-documentation"),
        "narrow": (
            ("python3 scripts/validate-productization-assets.py", "documentation or productization asset changed"),
        ),
        "full": (
            (
                "python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md --check",
                "documentation dashboard output should remain reproducible",
            ),
        ),
    },
}


UNKNOWN_COMMANDS: tuple[ValidationCommand, ...] = (
    ValidationCommand(
        command="python3 -m unittest discover -s tests",
        level="module",
        reason="unknown changed path; run the broad unit/regression suite or explain why it is not applicable",
        category="unknown",
        covered_path_patterns=("**",),
        covered_risk_surfaces=("unknown",),
    ),
    ValidationCommand(
        command="python3 scripts/build.py --profile recommended",
        level="full",
        reason="unknown changed path; ensure runtime artifacts still build or explain why no build surface changed",
        category="unknown",
        covered_path_patterns=("**",),
        covered_risk_surfaces=("unknown",),
    ),
)


VALIDATION_COMMAND_MARKERS = (
    "pytest",
    "unittest",
    "go test",
    "cargo test",
    "npm test",
    "yarn test",
    "pnpm test",
    "validate-",
    "eval-",
    "build.py",
)


def registry_commands() -> list[ValidationCommand]:
    """Return all known registry commands in deterministic order."""
    commands: list[ValidationCommand] = []
    for category, entry in REGISTRY.items():
        patterns = tuple(str(item) for item in entry["path_patterns"])
        surfaces = tuple(str(item) for item in entry["risk_surfaces"])
        for level in ("narrow", "full"):
            for command, reason in entry[level]:  # type: ignore[index]
                commands.append(
                    ValidationCommand(
                        command=str(command),
                        level=level,
                        reason=str(reason),
                        category=category,
                        covered_path_patterns=patterns,
                        covered_risk_surfaces=surfaces,
                    )
                )
    return commands


def matching_categories(changed_paths: Iterable[str]) -> list[str]:
    """Return registry categories matched by repository-relative paths."""
    categories: list[str] = []
    for path in _clean_paths(changed_paths):
        for category, entry in REGISTRY.items():
            if category in categories:
                continue
            patterns = tuple(str(item) for item in entry["path_patterns"])
            if any(fnmatch(path, pattern) for pattern in patterns):
                categories.append(category)
    return categories


def commands_for_categories(categories: Iterable[str], level: str | None = None) -> list[ValidationCommand]:
    """Return commands for registry categories, preserving registry order."""
    wanted = set(categories)
    result: list[ValidationCommand] = []
    for command in registry_commands():
        if command.category not in wanted:
            continue
        if level is not None and command.level != level:
            continue
        result.append(command)
    return _dedupe_commands(result)


def command_kind(command: str) -> str:
    """Return the strongest known kind for a command string."""
    normalized = _normalize_command(command)
    for spec in registry_commands():
        if _normalize_command(spec.command) == normalized:
            return spec.level
    if is_validation_looking(command):
        return "unknown"
    return "unknown"


def command_coverage(command: str) -> dict[str, object]:
    """Return covered path/risk metadata for a command, if known."""
    normalized = _normalize_command(command)
    for spec in registry_commands():
        if _normalize_command(spec.command) == normalized:
            return spec.to_dict()
    return {
        "command": command.strip(),
        "level": "unknown",
        "reason": "validation-looking command is not in registry",
        "category": "unknown",
        "covered_path_patterns": [],
        "covered_risk_surfaces": [],
    }


def is_validation_looking(command: str) -> bool:
    lowered = command.casefold()
    return any(marker in lowered for marker in VALIDATION_COMMAND_MARKERS)


def _dedupe_commands(commands: Iterable[ValidationCommand]) -> list[ValidationCommand]:
    result: list[ValidationCommand] = []
    seen: set[str] = set()
    for command in commands:
        key = _normalize_command(command.command)
        if key in seen:
            continue
        seen.add(key)
        result.append(command)
    return result


def _normalize_command(command: str) -> str:
    return " ".join(str(command).strip().split())


def _clean_paths(paths: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for path in paths:
        text = str(path).replace("\\", "/").strip().lstrip("./")
        if text:
            cleaned.append(text)
    return cleaned
