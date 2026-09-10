"""Source-owned expertise examples shared by routing and code-generation validation."""
from pathlib import Path
from typing import Any
from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from validation_utils import ValidationProblem, load_yaml_file

EXPECTED_CODEGEN_CASE_IDS = {f"{category}/{case}" for category, cases in EXPECTED_BENCHMARKS.items() for case in cases}


def release_routing_scenario_errors(rows: list[dict[str, Any]]) -> list[str]:
    errors = []
    for field in ("id", "codegen_case_id"):
        values = [row.get(field) for row in rows]
        if any(not isinstance(value, str) or not value for value in values) or len(set(value for value in values if isinstance(value, str))) != len(values):
            errors.append(f"release routing {field} values must be unique non-empty identities")
    for row in rows:
        if not isinstance(row.get("codegen_case_id"), str) or row["codegen_case_id"] not in EXPECTED_CODEGEN_CASE_IDS:
            errors.append(f"{row.get('id')}: codegen case does not exist")
        router = row.get("router", {})
        expected = router.get("expected", {})
        if not router.get("trigger") or expected.get("profile") not in {"analysis-agent", "task-agent", "review-agent"} or not expected.get("primary"):
            errors.append(f"{row.get('id')}: missing expertise projection")
        for field in ("layer3",):
            selected = expected.get(field)
            if not isinstance(selected, list) or any(not isinstance(item, str) or not item for item in selected) or len(selected) > 3 or len(set(selected)) != len(selected):
                errors.append(f"{row.get('id')}: invalid Layer 3 selection")
        override = row.get("codegen_layer3", [])
        if not isinstance(override, list) or any(not isinstance(item, str) or not item for item in override) or len(override) > 3 or len(set(override)) != len(override):
            errors.append(f"{row.get('id')}: invalid codegen Layer 3 selection")
    return errors


def load_release_routing_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = load_yaml_file(path)
    rows = payload.get("scenarios") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows or payload.get("schema_version") != 2 or payload.get("kind") != "changeforge.release_routing_scenarios":
        raise ValidationProblem(f"{path}: invalid release routing examples")
    errors = release_routing_scenario_errors(rows)
    if errors:
        raise ValidationProblem(f"{path}: " + "; ".join(errors))
    return rows


def project_release_route_hints(scenario: dict[str, Any]) -> dict[str, Any]:
    expected = scenario["router"]["expected"]
    profile = expected["profile"]
    return {
        "work_path": "direct-task" if profile == "task-agent" else "review-only" if profile == "review-agent" else "diagnosis" if scenario["id"] == "diagnosis" else "analyzed-work",
        "agent_profile": profile,
        "primary_skill": expected["primary"],
        "layer3_skills": scenario.get("codegen_layer3", expected["layer3"]),
        "review_skill": expected["primary"] if profile == "review-agent" else None,
    }
