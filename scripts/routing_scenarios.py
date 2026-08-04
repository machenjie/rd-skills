"""Load and project the authored core release-routing scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from validation_utils import ValidationProblem, load_yaml_file


SPECIALIZED_HIGH_RISK_RELEASE_ROUTES = {
    "analyzed SSRF or URL-fetch security implementation (`implementation-preparation`)": {
        "light_case_id": "security-ssrf-boundary",
        "codegen_case_id": "security/ssrf-url-allowlist",
        "analysis_layer3": {"threat-modeling", "web-security"},
        "task_layer3": {"threat-modeling", "web-security"},
        "task_primary": "security-privacy-gate",
    },
    "analyzed cache stampede or cache-contention reliability implementation (`implementation-preparation`)": {
        "light_case_id": "cache-stampede-reliability",
        "codegen_case_id": "reliability/redis-cache-stampede-protection",
        "analysis_layer3": {
            "concurrency-control",
            "degradation-circuit-breaking",
            "observability",
        },
        "task_layer3": {
            "concurrency-control",
            "degradation-circuit-breaking",
            "observability",
        },
        "task_primary": "reliability-observability-gate",
    },
}
EXPECTED_CODEGEN_CASE_IDS = {
    f"{category}/{case_id}"
    for category, case_ids in EXPECTED_BENCHMARKS.items()
    for case_id in case_ids
}


def release_routing_scenario_errors(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(set(ids)):
        errors.append("release routing scenario ids must be unique")
    codegen_case_ids = [
        row.get("codegen_case_id") for row in rows if isinstance(row, dict)
    ]
    valid_codegen_case_ids = [
        value
        for value in codegen_case_ids
        if isinstance(value, str) and value.strip()
    ]
    if len(valid_codegen_case_ids) != len(set(valid_codegen_case_ids)):
        errors.append("release routing codegen_case_id values must be unique")
    for row in rows:
        label = str(row.get("id"))
        codegen_case_id = row.get("codegen_case_id")
        if not isinstance(codegen_case_id, str) or not codegen_case_id.strip():
            errors.append(f"{label}: codegen_case_id must be a non-empty string")
        elif codegen_case_id not in EXPECTED_CODEGEN_CASE_IDS:
            errors.append(
                f"{label}: codegen_case_id {codegen_case_id!r} is not listed in "
                "EXPECTED_BENCHMARKS"
            )
        router = row.get("router")
        expected = router.get("expected") if isinstance(router, dict) else None
        analysis = row.get("analysis")
        tasks = row.get("tasks")
        review = row.get("review")
        codegen_layer3 = row.get("codegen_layer3")
        if not isinstance(expected, dict) or not isinstance(tasks, list):
            errors.append(f"{label}: router or task contract is invalid")
            continue
        if codegen_layer3 is not None and (
            not isinstance(codegen_layer3, list)
            or any(
                not isinstance(value, str) or not value.strip()
                for value in codegen_layer3
            )
            or len(codegen_layer3) > 3
            or len(codegen_layer3) != len(set(codegen_layer3))
        ):
            errors.append(
                f"{label}: codegen_layer3 must contain at most three unique "
                "non-empty Skill names"
            )
        first = analysis or (tasks[0] if tasks else review)
        first_profile = "analysis-agent" if analysis else "task-agent" if tasks else "review-agent"
        if not isinstance(first, dict) or {
            "profile": first_profile,
            "primary": first.get("primary"),
            "layer3": first.get("layer3"),
        } != {key: expected.get(key) for key in ("profile", "primary", "layer3")}:
            errors.append(f"{label}: router expected route must match the first phase")
        exemption = row.get("review_exemption")
        if isinstance(review, dict):
            if exemption is not None or expected.get("review") != review.get("primary"):
                errors.append(f"{label}: router review must match the final review phase")
            if any(task.get("review") != review.get("primary") for task in tasks if isinstance(task, dict)):
                errors.append(f"{label}: task review must match the final review phase")
        elif not (
            row.get("control_path") == "diagnosis"
            and exemption == "diagnosis-only"
            and analysis
            and not tasks
            and isinstance(expected.get("review"), str)
        ):
            errors.append(f"{label}: missing final review requires an explicit diagnosis-only exemption")
    by_trigger = {
        row.get("router", {}).get("trigger"): row
        for row in rows
        if isinstance(row.get("router"), dict)
    }
    for trigger, contract in SPECIALIZED_HIGH_RISK_RELEASE_ROUTES.items():
        row = by_trigger.get(trigger)
        if not isinstance(row, dict):
            errors.append(f"missing specialized high-risk release route: {trigger}")
            continue
        label = str(row.get("id"))
        if row.get("light_case_id") != contract["light_case_id"]:
            errors.append(f"{label}: specialized signal has the wrong lightweight case")
        if row.get("codegen_case_id") != contract["codegen_case_id"]:
            errors.append(f"{label}: specialized signal has the wrong codegen case")
        analysis_layer3 = set(contract["analysis_layer3"])
        task_layer3 = set(contract["task_layer3"])
        phases = [
            ("router expected", row["router"].get("expected"), analysis_layer3),
            ("analysis", row.get("analysis"), analysis_layer3),
            *(
                (f"task {index}", task, task_layer3)
                for index, task in enumerate(row.get("tasks") or [], start=1)
            ),
        ]
        for phase_name, phase, required_layer3 in phases:
            selected = set(phase.get("layer3") or []) if isinstance(phase, dict) else set()
            missing = sorted(required_layer3 - selected)
            if missing:
                errors.append(
                    f"{label}: {phase_name} requires Layer 3 {', '.join(missing)} for {trigger}"
                )
        tasks = row.get("tasks") or []
        if not tasks or any(
            not isinstance(task, dict)
            or task.get("primary") != contract["task_primary"]
            for task in tasks
        ):
            errors.append(
                f"{label}: specialized signal requires task primary {contract['task_primary']}"
            )
    return errors


def load_release_routing_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = load_yaml_file(path)
    rows = payload.get("scenarios") if isinstance(payload, dict) else None
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 2
        or payload.get("kind") != "changeforge.release_routing_scenarios"
        or not isinstance(rows, list)
        or len(rows) != 11
    ):
        raise ValidationProblem(
            f"{path}: release routing scenario authority must use schema_version 2, "
            "kind changeforge.release_routing_scenarios, and exactly 11 core release scenarios"
        )
    required = {"id", "router", "light_case_id", "codegen_case_id", "control_path", "analysis", "tasks", "review"}
    allowed = required | {"review_exemption", "codegen_layer3"}
    if any(not isinstance(row, dict) or not required <= set(row) or not set(row) <= allowed for row in rows):
        raise ValidationProblem(f"{path}: release routing scenario fields are invalid")
    for row in rows:
        if not isinstance(row["tasks"], list) or not isinstance(row["router"], dict):
            raise ValidationProblem(f"{path}: release routing scenario phase fields are invalid")
    errors = release_routing_scenario_errors(rows)
    if errors:
        raise ValidationProblem(f"{path}: " + "; ".join(errors))
    return rows


def project_release_contract(scenario: dict[str, Any]) -> dict[str, Any]:
    analysis = scenario["analysis"]
    review = scenario["review"]
    tasks = scenario["tasks"]
    return {
        "case_id": scenario["codegen_case_id"],
        "control_path": scenario["control_path"],
        "primary_skill": analysis["primary"] if analysis else tasks[0]["primary"] if tasks else review["primary"],
        "task_skill": tasks[0]["primary"] if len(tasks) == 1 else None,
        "review_skill": review["primary"] if review else None,
        "tasks": [{"task_id": task["task_id"], "skill": task["primary"], "review_skill": task["review"]} for task in tasks],
    }


def project_release_route_hints(scenario: dict[str, Any]) -> dict[str, Any]:
    tasks = scenario["tasks"]
    review = scenario["review"]
    analysis = scenario["analysis"]
    phase = tasks[0] if tasks else review if review else analysis
    work_paths = {"direct": "direct-task", "analyzed": "analyzed-work", "diagnosis": "diagnosis", "review-only": "review-only"}
    profile = "task-agent" if tasks else "review-agent" if review else "analysis-agent"
    return {
        "work_path": work_paths[scenario["control_path"]],
        "agent_profile": profile,
        "primary_skill": phase["primary"],
        "layer3_skills": scenario.get("codegen_layer3", phase["layer3"]),
        "review_skill": review["primary"] if review else None,
    }
