"""Resolve affected tests from validation plans."""

from __future__ import annotations

from typing import Iterable

from .command_resolver import resolve_validation_plan


def affected_validation_commands(
    changed_paths: Iterable[str],
    risk_surfaces: Iterable[str] = (),
    stage: str = "",
    repo_context: dict | None = None,
) -> list[dict[str, object]]:
    """Return narrow/module commands that should be run near the changed paths."""
    plan = resolve_validation_plan(
        changed_paths,
        risk_surfaces=risk_surfaces,
        stage=stage,
        repo_context=repo_context,
    )
    return list(plan.get("recommended_commands", []))
