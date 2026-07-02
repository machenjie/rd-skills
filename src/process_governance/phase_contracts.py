"""Process phase contract constants shared by runtime validators."""

from __future__ import annotations


CORE_PHASES = ("pdd", "ddd", "sdd", "tdd")
REQUIRED_PROCESS_FIELDS = {
    "pdd": ("problem", "acceptance_criteria", "constraints", "validation_signal"),
    "ddd": ("domain_terms", "invariants", "ownership_decision", "side_effect_boundaries"),
    "sdd": ("modules", "public_api", "error_contract", "failure_modes", "logging_decision"),
    "tdd": (
        "acceptance_to_tests",
        "invariant_to_tests_or_code",
        "public_api_to_tests",
        "failure_mode_tests",
        "validation_commands",
    ),
}
GENERIC_TRACE_MARKERS = (
    "requested benchmark behavior is observable through public api",
    "expected behavior is observable through public api or documented setup/test contract",
    "candidate passes deterministic assertion-backed grading benchmark",
    "business rules remain in the owning domain",
    "side effects remain outside pure domain",
    "candidate public api",
    "starter repository public api",
    "validation command recorded",
)
GENERIC_DDD_MARKERS = (
    "keeps business rules in the owning domain",
    "keeps side effects outside pure domain",
    "business rules remain in the owning domain",
    "side effects remain outside pure domain",
)
GENERIC_PUBLIC_API_MARKERS = ("candidate public api", "starter repository public api")
SDD_ASSUMPTION_POLICY_MARKER = "block_when_wrong_answer_changes"
SDD_CHOICE_STATUSES = {"required", "resolved", "not_required", "assumed_with_rationale"}
SDD_NO_CHOICE_RATIONALE_FIELDS = (
    "no_design_choice_rationale",
    "no_material_design_choice_rationale",
    "design_choice_rationale",
)
SDD_SPECIFIC_RATIONALE_MARKERS = (
    "source",
    "constraint",
    "repository convention",
    "repo convention",
    "existing convention",
    "existing pattern",
    "reuse evidence",
    "prompt",
    "fixture",
    "explicit user",
    "user specified",
)
SDD_GENERIC_RATIONALES = {
    "no choice needed",
    "no decision needed",
    "not needed",
    "not required",
    "none",
    "n/a",
    "na",
}
SDD_MATERIAL_CHOICE_KEYWORDS = (
    "new module",
    "new directory",
    "new public api",
    "public api",
    "public export",
    "shared utility",
    "common/shared",
    "abstraction",
    "interface",
    "protocol",
    "adapter",
    "cache",
    "queue",
    "async",
    "worker",
    "migration",
    "rollback",
    "config switch",
    "feature flag",
    "external dependency",
    "service boundary",
    "data ownership",
    "permission",
    "auth",
    "security",
    "tenant",
    "payment",
    "irreversible",
    "privacy",
)
SDD_HIGH_RISK_SAFE_ASSUMPTION_KEYWORDS = (
    "public api",
    "public export",
    "contract",
    "architecture",
    "data",
    "data model",
    "schema",
    "security",
    "permission",
    "auth",
    "tenant",
    "migration",
    "rollback",
    "irreversible",
    "payment",
    "privacy",
)
SDD_SAFE_ASSUMPTION_MARKER_GROUPS = (
    ("local", "same file", "single file", "module-local", "within existing"),
    ("reversible", "can be reverted", "easy to revert", "revertible"),
    ("conventional", "repository convention", "existing convention", "existing pattern"),
    ("acceptance-neutral", "acceptance neutral", "does not change acceptance", "no acceptance change"),
)


__all__ = [
    "CORE_PHASES",
    "GENERIC_DDD_MARKERS",
    "GENERIC_PUBLIC_API_MARKERS",
    "GENERIC_TRACE_MARKERS",
    "REQUIRED_PROCESS_FIELDS",
    "SDD_ASSUMPTION_POLICY_MARKER",
    "SDD_CHOICE_STATUSES",
    "SDD_GENERIC_RATIONALES",
    "SDD_HIGH_RISK_SAFE_ASSUMPTION_KEYWORDS",
    "SDD_MATERIAL_CHOICE_KEYWORDS",
    "SDD_NO_CHOICE_RATIONALE_FIELDS",
    "SDD_SAFE_ASSUMPTION_MARKER_GROUPS",
    "SDD_SPECIFIC_RATIONALE_MARKERS",
]
