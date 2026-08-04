#!/usr/bin/env python3
"""Validate route-once Professional and Layer 3 selection."""

from __future__ import annotations

import json
import re
from pathlib import Path

from deterministic_route_oracle import (
    CONCRETE_CLIENT_PLATFORM_ORDER,
    CROSS_PLATFORM_MODIFIER,
    DOMAIN_ROUTE_SPECS,
)
from validation_utils import (
    DOMAIN_MODIFIER_ONLY_ROUTING_MODE,
    NAME_RE,
    ValidationProblem,
    domain_modifier_routing_authority,
    domain_registry_contract_errors,
    fail_many,
    load_yaml_file,
    professional_automatic_routing_contract_errors,
)
from routing_scenarios import (
    load_release_routing_scenarios,
    release_routing_scenario_errors,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"analysis-agent", "task-agent", "review-agent"}
PROFESSIONAL = ROOT / "src" / "registry" / "professional-skills.yaml"
FOUNDATION = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN = ROOT / "src" / "registry" / "domain-skills.yaml"
ROUTER = ROOT / "src" / "control-skills" / "engineering-control-plane" / "references" / "professional-skill-router.md"
RELEASE_ROUTING_SCENARIOS = ROOT / "src" / "registry" / "release-routing-scenarios.yaml"
LIGHT = ROOT / "evals" / "agent-light-trajectories" / "cases.yaml"
CONTEXT_ONLY_LIGHT_CASE_IDS = {
    "source-backed-payment-retry-proof",
    "module-boundary-benchmark-review",
}
DYNAMIC_CLIENT_LAYER3_CELL = (
    "cross-platform-client-extension + proven concrete platform Domain(s)"
)


def _phase_dispatch(profile: str, phase: dict[object, object]) -> tuple[object, object, tuple[object, ...]]:
    return profile, phase.get("primary"), tuple(phase.get("layer3") or [])


def _release_routing_projection_errors(
    rows: list[dict[str, object]], router_text: str
) -> list[str]:
    errors: list[str] = []
    router_rows: dict[str, list[str]] = {}
    for line in router_text.splitlines():
        if line.startswith("|") and not line.startswith("| ---") and "Task signal" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 5:
                router_rows[cells[0]] = cells
    light_rows = {row["id"]: row for row in json.loads(LIGHT.read_text())["cases"]}
    expected_light_ids = {
        row["light_case_id"] for row in rows
    } | CONTEXT_ONLY_LIGHT_CASE_IDS
    if set(light_rows) != expected_light_ids:
        errors.append("lightweight trajectory ids differ from release routing scenarios")
    for row in rows:
        label = str(row["id"])
        router = row["router"]
        expected = router["expected"]
        cells = router_rows.get(router["trigger"])
        projected = [expected["profile"], expected["primary"], ", ".join(expected["layer3"]) or "none", expected["review"]]
        if cells is None or cells[1:] != projected:
            errors.append(f"{label}: router Markdown row drifts from release routing projection")
        light = light_rows.get(row["light_case_id"])
        if light is not None:
            actual = [
                (step.get("profile"), step.get("primary_skill"), tuple(step.get("layer3_skills") or []))
                for step in light["steps"] if step.get("action") == "dispatch"
            ]
            expected_dispatches = []
            if row["analysis"]:
                expected_dispatches.append(_phase_dispatch("analysis-agent", row["analysis"]))
            expected_dispatches.extend(_phase_dispatch("task-agent", task) for task in row["tasks"])
            if row["review"]:
                expected_dispatches.append(_phase_dispatch("review-agent", row["review"]))
            repeats = len(actual) // len(expected_dispatches) if expected_dispatches and len(actual) % len(expected_dispatches) == 0 else 0
            if not repeats or actual != expected_dispatches * repeats:
                errors.append(
                    f"{label}: lightweight dispatch projection drifts from release routing scenario"
                )
    return errors


def parse_layer3_cell(cell: str) -> tuple[list[str], str | None]:
    """Parse one exact, comma-separated Layer 3 selection cell."""

    if cell == "none":
        return [], None
    if cell == DYNAMIC_CLIENT_LAYER3_CELL:
        return [CROSS_PLATFORM_MODIFIER], None
    names = cell.split(", ")
    if not names or any(NAME_RE.fullmatch(name) is None for name in names):
        return [], "must contain exact kebab-case Skill names or 'none'"
    if ", ".join(names) != cell:
        return [], "must use comma-space separators between exact Skill names"
    if len(names) > 3:
        return names, "must select no more than three Layer 3 Skills"
    if len(names) != len(set(names)):
        return names, "must not select duplicate Layer 3 Skills"
    return names, None


def validate_router_row(
    cells: list[str],
    professional: dict[object, dict[object, object]],
    layer3: dict[object, dict[object, object]],
    *,
    source: str = "<router row>",
) -> list[str]:
    """Validate one five-cell router row against exact registry contracts."""

    errors: list[str] = []
    if len(cells) != 5:
        return [f"router row must have five columns: {source}"]
    start_profile = cells[1]
    if start_profile not in PROFILES:
        errors.append(f"router row must select exactly one supported profile: {source}")
    primary_name = cells[2]
    primary = professional.get(primary_name)
    if primary is None:
        errors.append(f"router row must select exactly one known primary Skill: {source}")
    else:
        if primary.get("task_routable") is not True:
            errors.append(f"router row selects non-routable Professional Skill {primary_name}")
        if start_profile not in primary.get("role_support", []):
            errors.append(f"router row assigns {primary_name} to unsupported profile {start_profile}")

    selected_layer3, parse_error = parse_layer3_cell(cells[3])
    if parse_error:
        errors.append(f"router row Layer 3 cell {parse_error}: {source}")
    dynamic_client_targets = cells[3] == DYNAMIC_CLIENT_LAYER3_CELL
    if dynamic_client_targets and (
        primary_name != "installed-client-change-builder"
        or not cells[0].startswith("shared installed client")
    ):
        errors.append(
            "dynamic installed-client Layer 3 selection is only valid for the "
            f"shared installed-client router row: {source}"
        )
    validated_layer3 = [
        *selected_layer3,
        *(
            CONCRETE_CLIENT_PLATFORM_ORDER
            if dynamic_client_targets
            else ()
        ),
    ]
    for selected in validated_layer3:
        layer3_entry = layer3.get(selected)
        if layer3_entry is None:
            errors.append(f"router row selects unknown Layer 3 Skill {selected!r}: {source}")
            continue
        if primary is not None and selected not in primary.get("layer3_candidates", []):
            errors.append(
                f"router row selects {selected} outside {primary_name}.layer3_candidates"
            )
        if start_profile not in layer3_entry.get("role_support", []):
            errors.append(
                f"router row assigns Layer 3 Skill {selected} to unsupported profile {start_profile}"
            )

    review_name = cells[4]
    review = professional.get(review_name)
    if review is None:
        errors.append(f"router row must select exactly one known Review Skill: {source}")
    else:
        if review.get("task_routable") is not True:
            errors.append(f"router row selects non-routable Review Skill {review_name}")
        if "review-agent" not in review.get("role_support", []):
            errors.append(f"router row Review Skill {review_name} does not support review-agent")
    return errors


def domain_router_coverage_errors(
    router_rows: list[list[str]],
    domain: dict[object, dict[object, object]],
) -> list[str]:
    """Require atomic Registry, oracle, and Router Domain contract agreement."""

    modifier_domain = {
        name: entry
        for name, entry in domain.items()
        if entry.get("routing_mode") == DOMAIN_MODIFIER_ONLY_ROUTING_MODE
    }
    routes: dict[object, list[str]] = {name: [] for name in modifier_domain}
    for cells in router_rows:
        if len(cells) != 5:
            continue
        selected, parse_error = parse_layer3_cell(cells[3])
        if parse_error:
            continue
        for name in selected:
            if name in routes:
                routes[name].append(cells[0])

    errors: list[str] = []
    registry_names = {str(name) for name in modifier_domain}
    oracle_names = set(DOMAIN_ROUTE_SPECS)
    if registry_names != oracle_names:
        errors.append(
            "Domain routing oracle names differ from Registry; "
            f"missing={sorted(registry_names - oracle_names)}; "
            f"extra={sorted(oracle_names - registry_names)}"
        )
    for name, entry in modifier_domain.items():
        signals = routes[name]
        if not signals:
            errors.append(f"Domain Skill {name!r} has no authoritative router row")
            continue
        positive_trigger_signals: list[str] = []
        positive_boundary_signals: list[str] = []
        negative_signals: list[str] = []
        for signal in signals:
            if signal.count("; excluding ") != 1:
                errors.append(
                    f"Domain Skill {name!r} Router signal must separate one "
                    "positive contract from one exclusion contract"
                )
                continue
            positive, negative = signal.split("; excluding ", 1)
            if positive.count(" with ") != 1:
                errors.append(
                    f"Domain Skill {name!r} Router positive contract must separate "
                    "trigger atoms from boundary atoms"
                )
                continue
            trigger_signal, boundary_signal = positive.split(" with ", 1)
            positive_trigger_signals.append(trigger_signal)
            positive_boundary_signals.append(boundary_signal)
            negative_signals.append(negative)
        triggers = tuple(
            value.strip().casefold()
            for value in entry.get("trigger_signals", [])
            if isinstance(value, str) and value.strip()
        )
        if not triggers:
            errors.append(f"Domain Skill {name!r} has no registry trigger")
            continue
        composite_triggers = [
            trigger
            for trigger in triggers
            if "," in trigger or ";" in trigger or " or " in trigger
        ]
        if composite_triggers:
            errors.append(
                f"Domain Skill {name!r} registry trigger must be atomic: "
                + ", ".join(composite_triggers)
            )
        spec = DOMAIN_ROUTE_SPECS.get(str(name))
        if not isinstance(spec, dict):
            continue
        families = spec.get("families")
        if not isinstance(families, dict):
            errors.append(f"Domain Skill {name!r} oracle families are invalid")
            continue
        oracle_triggers: list[str] = []
        oracle_boundaries: list[str] = []
        for family, contract in families.items():
            if not isinstance(contract, dict):
                errors.append(
                    f"Domain Skill {name!r} oracle family {family!r} is invalid"
                )
                continue
            atoms = tuple(
                str(value).strip().casefold()
                for value in contract.get("trigger_atoms", ())
                if str(value).strip()
            )
            executable = {
                str(value).strip().casefold()
                for value in contract.get("domain_signals", ())
                if str(value).strip()
            }
            qualified_raw = contract.get("qualified_domain_signals", {})
            qualified = (
                {
                    str(value).strip().casefold()
                    for value in qualified_raw
                    if str(value).strip()
                }
                if isinstance(qualified_raw, dict)
                else set()
            )
            if not isinstance(qualified_raw, dict) or any(
                not isinstance(qualifiers, (list, tuple)) or not qualifiers
                for qualifiers in qualified_raw.values()
            ):
                errors.append(
                    f"Domain Skill {name!r} oracle family {family!r} has invalid "
                    "qualified trigger atoms"
                )
            if not atoms:
                errors.append(
                    f"Domain Skill {name!r} oracle family {family!r} has no trigger atoms"
                )
            missing_executable = sorted(set(atoms) - executable - qualified)
            if missing_executable:
                errors.append(
                    f"Domain Skill {name!r} oracle family {family!r} has non-executable "
                    "trigger atoms: " + ", ".join(missing_executable)
                )
            oracle_triggers.extend(atoms)
            boundary_atoms = tuple(
                str(value).strip().casefold()
                for value in contract.get("boundary_atoms", ())
                if str(value).strip()
            )
            executable_boundaries = {
                str(value).strip().casefold()
                for value in contract.get("boundary_signals", ())
                if str(value).strip()
            }
            if not boundary_atoms:
                errors.append(
                    f"Domain Skill {name!r} oracle family {family!r} has no "
                    "boundary atoms"
                )
            missing_boundary_execution = sorted(
                set(boundary_atoms) - executable_boundaries
            )
            if missing_boundary_execution:
                errors.append(
                    f"Domain Skill {name!r} oracle family {family!r} has "
                    "non-executable boundary atoms: "
                    + ", ".join(missing_boundary_execution)
                )
            oracle_boundaries.extend(boundary_atoms)
        if len(oracle_triggers) != len(set(oracle_triggers)):
            errors.append(f"Domain Skill {name!r} repeats oracle trigger atoms")
        if set(triggers) != set(oracle_triggers):
            errors.append(
                f"Domain Skill {name!r} Registry/oracle trigger atoms differ; "
                f"registry-only={sorted(set(triggers) - set(oracle_triggers))}; "
                f"oracle-only={sorted(set(oracle_triggers) - set(triggers))}"
            )
        missing_router_triggers = sorted(
            atom
            for atom in set(triggers)
            if not any(
                _contains_contract_atom(signal, atom)
                for signal in positive_trigger_signals
            )
        )
        if missing_router_triggers:
            errors.append(
                f"Domain Skill {name!r} Router omits trigger atoms: "
                + ", ".join(missing_router_triggers)
            )
        boundaries = tuple(
            value.strip().casefold()
            for value in entry.get("boundary_signals", [])
            if isinstance(value, str) and value.strip()
        )
        if not boundaries:
            errors.append(f"Domain Skill {name!r} has no registry boundary signal")
        composite_boundaries = [
            boundary
            for boundary in boundaries
            if "," in boundary or ";" in boundary or " or " in boundary
        ]
        if composite_boundaries:
            errors.append(
                f"Domain Skill {name!r} registry boundary must be atomic: "
                + ", ".join(composite_boundaries)
            )
        if len(oracle_boundaries) != len(set(oracle_boundaries)):
            errors.append(f"Domain Skill {name!r} repeats oracle boundary atoms")
        if set(boundaries) != set(oracle_boundaries):
            errors.append(
                f"Domain Skill {name!r} Registry/oracle boundary atoms differ; "
                f"registry-only={sorted(set(boundaries) - set(oracle_boundaries))}; "
                f"oracle-only={sorted(set(oracle_boundaries) - set(boundaries))}"
            )
        missing_router_boundaries = sorted(
            atom
            for atom in set(boundaries)
            if not any(
                _contains_contract_atom(signal, atom)
                for signal in positive_boundary_signals
            )
        )
        if missing_router_boundaries:
            errors.append(
                f"Domain Skill {name!r} Router omits boundary atoms: "
                + ", ".join(missing_router_boundaries)
            )
        anti_triggers = tuple(
            value.strip().casefold()
            for value in entry.get("anti_trigger_signals", [])
            if isinstance(value, str) and value.strip()
        )
        if not anti_triggers:
            errors.append(f"Domain Skill {name!r} has no registry anti-trigger")
            continue
        anti_atoms = tuple(
            str(value).strip().casefold()
            for value in spec.get("anti_atoms", ())
            if str(value).strip()
        )
        if not anti_atoms:
            errors.append(f"Domain Skill {name!r} oracle has no anti-trigger atoms")
            continue
        registry_anti_text = " ".join(anti_triggers)
        missing_registry_anti = sorted(
            atom
            for atom in anti_atoms
            if not _contains_contract_atom(registry_anti_text, atom)
        )
        if missing_registry_anti:
            errors.append(
                f"Domain Skill {name!r} Registry omits oracle anti-trigger atoms: "
                + ", ".join(missing_registry_anti)
            )
        missing_router_anti = sorted(
            atom
            for atom in anti_atoms
            if not any(
                _contains_contract_atom(signal, atom) for signal in negative_signals
            )
        )
        if missing_router_anti:
            errors.append(
                f"Domain Skill {name!r} Router omits anti-trigger atoms: "
                + ", ".join(missing_router_anti)
            )
    return errors


def _contains_contract_atom(text: str, atom: str) -> bool:
    """Match one contract atom without accepting identifier substrings."""

    normalized = text.casefold()
    right = r"(?![a-z0-9+])" if atom == "c" else r"(?![a-z0-9])"
    return re.search(rf"(?<![a-z0-9]){re.escape(atom)}{right}", normalized) is not None


def main() -> int:
    errors: list[str] = []
    try:
        professional_data = load_yaml_file(PROFESSIONAL)
        pro_entries = professional_data.get("professional_skills", [])
        foundation_entries = load_yaml_file(FOUNDATION).get("foundation_skills", [])
        domain_data = load_yaml_file(DOMAIN)
        domain_entries = domain_data.get("domain_skills", [])
    except (ValidationProblem, AttributeError) as exc:
        errors.append(str(exc))
        return fail_many("validate-skill-routing", errors)
    errors.extend(
        professional_automatic_routing_contract_errors(
            professional_data,
            "professional-skills.yaml",
        )
    )
    errors.extend(domain_registry_contract_errors(domain_data))
    try:
        domain_modifier_routing_authority(domain_data, professional_data)
    except ValidationProblem as exc:
        errors.append(str(exc))
    by_name = {entry.get("name"): entry for entry in pro_entries if isinstance(entry, dict)}
    domain_by_name = {
        entry.get("name"): entry
        for entry in domain_entries
        if isinstance(entry, dict)
    }
    layer3 = {
        entry.get("name"): entry
        for entry in [*foundation_entries, *domain_entries]
        if isinstance(entry, dict)
    }
    for name, entry in by_name.items():
        candidates = entry.get("layer3_candidates")
        if not isinstance(candidates, list):
            errors.append(f"{name}: layer3_candidates must be a list")
            continue
        if len(candidates) != len(set(candidates)):
            errors.append(f"{name}: layer3_candidates must not contain duplicates")
        for candidate in candidates:
            if candidate not in layer3:
                errors.append(f"{name}: unknown Layer 3 candidate {candidate!r}")
    if not ROUTER.is_file():
        errors.append("missing professional-skill-router.md")
        return fail_many("validate-skill-routing", errors)
    text = ROUTER.read_text(encoding="utf-8")
    folded = text.casefold()
    for phrase in ("route once per task", "one primary professional skill", "zero to three", "engineering-change-analysis", "ordinary multi-task work uses combined final diff review", "do not load the full foundation or domain catalog"):
        if phrase not in folded:
            errors.append(f"router missing {phrase!r}")
    router_rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "Task signal" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        router_rows.append(cells)
        errors.extend(validate_router_row(cells, by_name, layer3, source=line))
        signal, _profile, primary, _selected, review = cells
        folded_signal = signal.casefold()
        if "ordinary multiple" in folded_signal:
            if primary != "engineering-change-analysis" or review == "high-risk-design-review":
                errors.append("ordinary multi-task route must use unified analysis without high-risk design review")
        if "high-risk multiple" in folded_signal:
            if primary != "engineering-change-analysis" or review != "high-risk-design-review":
                errors.append("high-risk multi-task route must use unified analysis and high-risk design review")
        if primary == "task-dag-planner" and "accepted engineering brief" not in folded_signal:
            errors.append("task-dag-planner requires an accepted Engineering Brief in its route signal")
        if primary == "change-impact-analyzer":
            errors.append("obsolete split analysis primary change-impact-analyzer is forbidden")
    errors.extend(domain_router_coverage_errors(router_rows, domain_by_name))
    try:
        errors.extend(
            _release_routing_projection_errors(
                load_release_routing_scenarios(RELEASE_ROUTING_SCENARIOS),
                text,
            )
        )
    except (ValidationProblem, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    if errors:
        return fail_many("validate-skill-routing", errors)
    print("validate-skill-routing: route-once primary, Layer 3, and review mappings are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
