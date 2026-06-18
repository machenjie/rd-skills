#!/usr/bin/env python3
"""Final handoff closure contract for ChangeForge hook runtime."""

from __future__ import annotations

from dataclasses import dataclass, field

from changeforge_adapter_capabilities import AdapterCapabilities, adapter_capabilities_for


@dataclass(frozen=True)
class ClosureContract:
    requires_route_manifest: bool = True
    requires_stage_route: bool = False
    requires_repository_context: bool = False
    requires_implementation_preflight: bool = False
    requires_validation_evidence: bool = True
    requires_review_evidence: bool = False
    requires_residual_risk: bool = True
    adapter_supports_blocking: bool = False
    closure_status: str = "pass"
    missing_items: list[str] = field(default_factory=list)

    @classmethod
    def from_state(
        cls,
        state: dict | None,
        *,
        route_manifest_complete: bool,
        stage_route_present: bool = False,
        repository_context_present: bool = False,
        implementation_preflight_complete: bool = False,
        validation_evidence_present: bool = False,
        review_evidence_present: bool = False,
        residual_risk_present: bool = False,
        capabilities: AdapterCapabilities | None = None,
        runtime: str = "generic",
        block_mode: bool = False,
    ) -> "ClosureContract":
        state = state if isinstance(state, dict) else {}
        capabilities = capabilities or adapter_capabilities_for(runtime)
        profile = _profile(state)
        if profile == "silent":
            return cls(
                requires_route_manifest=False,
                requires_validation_evidence=False,
                requires_residual_risk=False,
                adapter_supports_blocking=capabilities.supports_blocking,
            )
        engineering = profile == "engineering"
        requires_route = engineering
        requires_repo = engineering
        requires_preflight = engineering and bool(
            state.get("changed_paths")
            or state.get("implementation_preflight_required")
            or state.get("edit_without_preflight_seen")
            or state.get("post_edit_confirmed_preflight_gap")
        )
        requires_validation = engineering
        requires_review = str(state.get("turn_stage") or "") in {"review", "code-review", "repair", "bug-fix"}
        requires_risk = True
        missing: list[str] = []
        if requires_route and not route_manifest_complete:
            missing.append("route_manifest")
        if engineering and bool(state.get("stage_route_present")) and not stage_route_present:
            missing.append("stage_route")
        if requires_repo and not repository_context_present:
            missing.append("repository_context")
        if requires_preflight and not implementation_preflight_complete:
            missing.append("implementation_preflight")
        if requires_validation and not validation_evidence_present:
            missing.append("validation")
        if requires_review and not review_evidence_present:
            missing.append("review_evidence")
        if requires_risk and not residual_risk_present:
            missing.append("risk")
        status = "pass"
        if missing:
            status = "block" if block_mode and capabilities.supports_blocking else "warn"
        return cls(
            requires_route_manifest=requires_route,
            requires_stage_route=engineering and bool(state.get("stage_route_present")),
            requires_repository_context=requires_repo,
            requires_implementation_preflight=requires_preflight,
            requires_validation_evidence=requires_validation,
            requires_review_evidence=requires_review,
            requires_residual_risk=requires_risk,
            adapter_supports_blocking=capabilities.supports_blocking,
            closure_status=status,
            missing_items=_unique(missing),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "requires_route_manifest": self.requires_route_manifest,
            "requires_stage_route": self.requires_stage_route,
            "requires_repository_context": self.requires_repository_context,
            "requires_implementation_preflight": self.requires_implementation_preflight,
            "requires_validation_evidence": self.requires_validation_evidence,
            "requires_review_evidence": self.requires_review_evidence,
            "requires_residual_risk": self.requires_residual_risk,
            "adapter_supports_blocking": self.adapter_supports_blocking,
            "closure_status": self.closure_status,
            "missing_items": list(self.missing_items),
        }


def _profile(state: dict) -> str:
    stage = str(state.get("turn_stage") or "").strip()
    if stage in {"", "question", "unknown", "no_engineering_action"}:
        return "silent"
    if stage in {"read", "review", "requirement-intake", "code-review"} and not state.get("changed_paths"):
        return "read_review"
    return "engineering"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


__all__ = ["ClosureContract"]
