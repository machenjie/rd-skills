from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import MappingProxyType
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import deterministic_route_oracle as ORACLE
import validation_utils as VALIDATION
from validation_utils import load_yaml_file


ORACLE_PATH = ROOT / "scripts" / "deterministic_route_oracle.py"
CASES_PATH = ROOT / "evals" / "routing" / "cases.yaml"
REPAIR177_SSOT_PATHS = (
    CASES_PATH,
    ROOT / "evals" / "routing" / "capability-coverage-cases.yaml",
    ROOT / "evals" / "capability-coverage" / "matrix.yaml",
    ROOT / "evals" / "capability-coverage" / "admission-cases.yaml",
)
REPAIR177_SSOT_OLD_PROMPT = (
    "Analyze a domain invariant and forbidden lifecycle transition."
)
REPAIR177_SSOT_NEW_PROMPT = (
    "Analyze a domain invariant and model the domain lifecycle transition."
)
WAVE1A_ROUTING_CASE_IDS = (
    "wave1a-stack-architecture-analysis",
    "wave1a-stack-accepted-brief-review",
    "wave1a-module-boundary-major-brief-review",
    "wave1a-config-frontend",
    "wave1a-config-installed-client",
    "wave1a-config-backend",
    "wave1a-config-data-middleware",
    "wave1a-config-platform-infrastructure",
    "wave1a-config-integration",
    "wave1a-config-repository-tooling",
    "wave1a-config-owner-unknown",
    "wave1a-dependency-frontend",
    "wave1a-dependency-installed-client",
    "wave1a-dependency-backend",
    "wave1a-dependency-data-middleware",
    "wave1a-dependency-platform-infrastructure",
    "wave1a-dependency-integration",
    "wave1a-dependency-repository-tooling",
    "wave1a-stack-language-negative",
    "wave1a-stack-fixed-negative",
    "wave1a-stack-invalid-brief-negative",
    "wave1a-stack-unaccepted-brief-negative",
    "wave1a-stack-stale-brief-negative",
    "wave1a-config-generic-negative",
    "wave1a-config-build-only-negative",
    "wave1a-config-secret-only-negative",
    "wave1a-dependency-package-mechanics-negative",
    "wave1a-dependency-lockfile-negative",
    "wave1a-dependency-advisory-keyword-negative",
    "wave1a-sandbox-dev-only-negative",
)

EXPECTED_DIRECT_RETURN_COUNT = 0
SPLIT_GUARD_RULE_IDS = {
    "review-ambiguous-structure-repository-first",
    "repository-tooling-ambiguous",
    "repository-tooling-layer-budget",
    "backend-effects-ambiguous",
    "backend-layer-budget",
    "distributed-effect-ambiguous",
    "installed-filesystem-ambiguous",
    "security-anti-input-shape",
    "security-anti-scanner-report",
    "minimality-analysis",
    "reliability-signal-analysis",
    "repository-first-default",
}
SPECIALIST_SIGNAL_RULE_IDS = {
    "explicit-architecture-tradeoff",
    "explicit-test-data-analysis",
    "explicit-authentication-authorization-analysis",
}
CANDIDATE_PRESELECTION_FIELDS = {
    "eligible_foundation_layer3_skills",
    "eligible_domain_layer3_skills",
    "eligible_layer3_skills",
    "reserved_domain_capacity",
    "layer3_overflow",
}
PAYMENT_FOUNDATION_PROMPT = (
    "Prepare a repository-backed payment retry change. Trace validation through "
    "policy, transaction, persistence, and external effects. Inspect exact owners, "
    "consumers, tests, contracts, configuration, and generated impacts."
)
CLOUD_BOUNDARY_SUFFIX = (
    "The change also crosses a cloud account, workload identity, regional "
    "failure-domain, KMS, and provider API boundary."
)
FOUR_FOUNDATION_REVIEW_PROMPT = (
    "Independently review the accepted current source-backed Engineering Brief for "
    "a material architecture critical path. Decide the algorithm and data "
    "structure, language and runtime, strongest feasible solution alternative, "
    "and technology stack."
)
ACTIVATION_V2_139C_FALLBACK_ROUTE_BYTES = (
    b'{"layer3_skills":["repository-context-map"],"path":"analyzed",'
    b'"primary_skill":"engineering-change-analysis","profile":"analysis-agent",'
    b'"review_skill":"architecture-impact-reviewer"}'
)
ACTIVATION_V2_139C_FALLBACK_TRACE_BYTES = (
    b'{"route_result":{"layer3_skills":["repository-context-map"],'
    b'"path":"analyzed","primary_skill":"engineering-change-analysis",'
    b'"profile":"analysis-agent","review_skill":"architecture-impact-reviewer"},'
    b'"selected_candidate":{"candidate_id":"repository-first-default",'
    b'"candidate_type":"fallback-route",'
    b'"evidence":["no-eligible-specific-candidate"]}}'
)
FOUR_FOUNDATION_BINDING = (
    "cf.brief-review-binding/v1"
    "|task_id=activation-v3-four-foundation"
    "|assignment_id=activation-v3-four-foundation"
    "|review_skill=high-risk-design-review"
    "|artifact_kind=engineering-brief"
    "|artifact_id=brief-four-foundation"
    "|artifact_sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    "|source_state_sha256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    "|currentness_status=verified"
    "|currentness_proof_sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    "|acceptance_status=accepted"
    "|acceptance_evidence_sha256=dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
    "|binding_sha256=2f2e7334aec5962e11c57f23d689a29d4bc29ed6aa250816377cda01714702b8"
)
CRITICAL_CASE_IDS = {
    "t2b-critical-backend-owner",
    "t2b-critical-backend-placement",
    "t2b-critical-backend-acceptance",
    "t2b-critical-backend-verification",
    "t2b-critical-backend-rollback",
    "t2b-critical-backend-revert",
}
PREPARATION_CASE_IDS = {
    "t2b-preparation-backend-repair",
    "t2b-preparation-tenant-authorization",
    "t2b-preparation-payment",
    "t2b-preparation-ai",
    "t2b-preparation-platform",
}
TIE_CASE_IDS = {
    "t2b-critical-preparation-tie",
    "t2b-critical-preparation-tie-reversed",
}
CONTROL_CASE_IDS = {
    "t2b-backend-resolved-direct",
    "t2b-backend-negated-unknown-direct",
    "t2b-repair-owner-not-unknown-direct",
    "t2b-repair-rollback-no-longer-unknown-direct",
    "t2b-repair-no-owner-unknown-direct",
    "t2b-repair-unrelated-unknown-direct",
    "t2b-dedicated-tenant-authorization-analysis",
    "t2b-dedicated-payment-analysis",
    "t2b-dedicated-ai-analysis",
    "t2b-dedicated-platform-owner",
    "t2b-bare-backend-plan-not-preparation",
}
CRITICAL_FIELDS = (
    "owner",
    "authority",
    "placement",
    "acceptance",
    "verification",
    "rollback",
)
UNKNOWN_STATES = (
    "unknown",
    "unresolved",
    "undecided",
    "not yet known",
)
RESOLVED_FIELD_FORMS = (
    "is not unknown",
    "not unknown",
    "is no longer unknown",
    "no longer unknown",
    "is known",
    "known",
    "is resolved",
    "resolved",
    "is decided",
    "decided",
    "is fixed",
    "fixed",
)
FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
TEST_STRATEGY_ACTIVATION_ID = "foundation-activation-test-strategy"
FOUNDATION_MATCHER_HELPER = "_foundation_runtime_matcher_matches"
REPAIR177_TARGETS = (
    "business-rule-extraction",
    "state-machine-modeling",
)
REPAIR177_ACTIVATION_IDS = (
    "foundation-activation-business-rule-extraction",
    "foundation-activation-state-machine-modeling",
)
REPAIR177_COMPOSITE_ID = "foundation-activation-composite"
REPAIR177_COMPARISON_FIELDS = (
    "precedence",
    "path",
    "profile",
    "primary_skill",
    "review_skill",
    "stage",
    "precedence_class",
)
REPAIR177_REQUEST_PREFIXES = (
    (),
    ("please",),
    ("please", "carefully"),
    ("kindly",),
    ("could", "you"),
    ("could", "you", "please"),
    ("would", "you"),
    ("can", "you"),
    ("we", "need", "to"),
    ("we", "should"),
)
REPAIR177_FUNCTION_TOKENS = (
    "a",
    "an",
    "the",
    "whether",
    "why",
    "how",
    "which",
    "what",
    "if",
)
REPAIR177_BUSINESS_OBJECTS = (
    "business invariant",
    "business invariants",
    "domain invariant",
    "domain invariants",
    "business policy",
    "business policies",
    "domain policy",
    "domain policies",
    "business calculation",
    "business calculations",
    "domain calculation",
    "domain calculations",
    "business constraint",
    "business constraints",
    "domain constraint",
    "domain constraints",
    "business rule",
    "business rules",
    "domain rule",
    "domain rules",
    "business decision authority",
    "domain decision authority",
)
REPAIR177_STATE_OBJECTS = (
    "state machine",
    "state machines",
    "lifecycle state",
    "lifecycle states",
    "lifecycle transition",
    "lifecycle transitions",
    "allowed transition",
    "allowed transitions",
    "allowed lifecycle transition",
    "allowed lifecycle transitions",
    "forbidden transition",
    "forbidden transitions",
    "forbidden lifecycle transition",
    "forbidden lifecycle transitions",
    "state guard",
    "state guards",
    "transition guard",
    "transition guards",
    "terminal state",
    "terminal states",
)
REPAIR177_BUSINESS_MODIFIERS = (
    "accepted",
    "current",
    "existing",
    "material",
)
REPAIR177_STATE_MODIFIERS = (
    "accepted",
    "current",
    "existing",
    "material",
    "proposed",
    "target",
)
REPAIR177_REPAIR5_CORPUS = (
    ("P01", "Analyze a domain invariant and forbidden lifecycle transition.", True, True),
    ("P02", "Analyze the business rule.", True, False),
    ("P03", "Analyze current business constraints.", True, False),
    ("P04", "Model the lifecycle states.", False, True),
    ("P05", "Extract domain policies.", True, False),
    ("P06", "Analyse business calculations.", True, False),
    ("P07", "Analyze domain decision authority.", True, False),
    ("P08", "Model state guards.", False, True),
    ("P09", "Analyze forbidden lifecycle transitions.", False, True),
    ("P10", "Analyze business constraints, domain policies, and terminal states.", True, True),
    ("P11", "Extract business invariants and model lifecycle states.", True, True),
    ("P12", "Analyze the current material domain rule.", True, False),
    ("P13", "Model state machines.", False, True),
    ("P14", "Analyze lifecycle transitions.", False, True),
    ("P15", "Model allowed transitions.", False, True),
    ("P16", "Analyze forbidden transitions.", False, True),
    ("P17", "Model allowed lifecycle transitions.", False, True),
    ("P18", "Analyze transition guards.", False, True),
    ("P19", "Model terminal states.", False, True),
    ("R01", "Please analyze business rules.", True, False),
    ("R02", "Please carefully extract domain constraints.", True, False),
    ("R03", "Kindly model lifecycle states.", False, True),
    ("R04", "Could you analyze domain invariants.", True, False),
    ("R05", "Could you please model state guards.", False, True),
    ("R06", "Would you model state machines.", False, True),
    ("R07", "Can you analyze domain decision authority.", True, False),
    ("R08", "We need to extract business calculations.", True, False),
    ("R09", "We should model terminal states.", False, True),
    ("A01", "Analyze the database constraints.", False, False),
    ("A02", "Analyze the Terraform policy.", False, False),
    ("A03", "Analyze the loop invariant.", False, False),
    ("A04", "Analyze the guard clause.", False, False),
    ("B01", "Analyze the accepted Brief and skip a domain invariant.", False, False),
    ("B02", "Analyze the accepted Brief and skips a domain invariant.", False, False),
    ("B03", "Analyze the accepted Brief and skipped a domain invariant.", False, False),
    ("B04", "Analyze the accepted Brief and skipping a domain invariant.", False, False),
    ("B05", "Analyze the accepted Brief and ignore a domain invariant.", False, False),
    ("B06", "Analyze the accepted Brief and ignores a domain invariant.", False, False),
    ("B07", "Analyze the accepted Brief and ignored a domain invariant.", False, False),
    ("B08", "Analyze the accepted Brief and ignoring a domain invariant.", False, False),
    ("B09", "Analyze the accepted Brief and exclude a domain invariant.", False, False),
    ("B10", "Analyze the accepted Brief and excludes a domain invariant.", False, False),
    ("B11", "Analyze the accepted Brief and excluded a domain invariant.", False, False),
    ("B12", "Analyze the accepted Brief and excluding a domain invariant.", False, False),
    ("B13", "Analyze the accepted Brief and omit a domain invariant.", False, False),
    ("B14", "Analyze the accepted Brief and omits a domain invariant.", False, False),
    ("B15", "Analyze the accepted Brief and omitted a domain invariant.", False, False),
    ("B16", "Analyze the accepted Brief and omitting a domain invariant.", False, False),
    ("C01", "Analyze a domain invariant and skip forbidden lifecycle transition.", True, False),
    ("C02", "Model a state machine and ignore business constraints.", False, True),
    ("C03", "Analyze a domain policy and exclude terminal states.", True, False),
    ("C04", "Model lifecycle states and omit domain rules.", False, True),
    ("N01", "Could they model lifecycle states.", False, False),
    ("N02", "The model has lifecycle states.", False, False),
    ("N03", "A data extract includes business constraints.", False, False),
    ("N04", "Could you not model lifecycle states.", False, False),
    ("N05", "Please do not analyze business rules.", False, False),
    ("N06", "We should not extract domain policies.", False, False),
    ("N07", "Our team should model lifecycle states.", False, False),
    ("N08", "The algorithm and model lifecycle states.", False, False),
    ("G01", "Analyze the accepted Brief with a domain invariant as background.", False, False),
    ("G02", "Analyze a domain invariant only as background.", False, False),
    ("G03", "Analyze a domain invariant as historical context.", False, False),
    ("G04", "Analyze a domain invariant for background context only.", False, False),
    ("G05", "Analyze only as background a domain invariant.", False, False),
    ("G06", "Analyze as historical context a domain invariant.", False, False),
    ("G07", "Analyze for background context only a domain invariant.", False, False),
    ("G08", "Analyze a domain invariant background.", False, False),
    ("G09", "Analyze a domain invariant as context only, but extract business constraints.", True, False),
    ("G10", "Model lifecycle states as background only, but analyze terminal states.", False, True),
    ("G11", "Analyze domain invariants as historical context, but analyze domain invariants.", True, False),
    ("X01", "Model business invariants.", False, False),
    ("X02", "Extract lifecycle states.", False, False),
    ("X03", "Extract business invariants and implement the change.", False, False),
    ("X04", "Implement model lifecycle states.", False, False),
    ("X05", "Do not extract business invariants.", False, False),
    ("X06", "Never model lifecycle states.", False, False),
    ("X07", "Do not extract business invariants, but model lifecycle states.", False, True),
    ("W01", "Analyze one two three four business constraints.", True, False),
    ("W02", "Analyze one two three four five business constraints.", False, False),
    ("W03", "Analyze one two three four and terminal states.", False, True),
    ("W04", "Analyze one two three four five and terminal states.", False, False),
)
REPAIR177_CORPUS = (
    ("R6-01", "Analyze a domain invariant and leave forbidden lifecycle transitions unchanged.", True, False, "match", "suppressed-leave"),
    ("R6-02", "Analyze a domain invariant and lifecycle states remain unchanged.", True, False, "match", "suppressed-carry"),
    ("R6-03", "Analyze whether a domain invariant is unchanged.", True, False, "direct-postfix", "no-occurrence"),
    ("R6-04", "Analyze whether the domain lifecycle transitions are unchanged.", False, True, "no-occurrence", "direct-postfix"),
    ("R6-05", "Analyze whether business policies are not required.", True, False, "direct-postfix", "no-occurrence"),
    ("R6-06", "Analyze whether the business state guards are not required.", False, True, "no-occurrence", "direct-postfix"),
    ("R6-07", "Analyze whether domain decision authority is out of scope.", True, False, "direct-postfix", "no-occurrence"),
    ("R6-08", "Analyze whether the domain terminal states are out of scope.", False, True, "no-occurrence", "direct-postfix"),
    ("R6-09", "Analyze domain policies and keep lifecycle states unchanged.", True, False, "match", "suppressed-keep"),
    ("R6-10", "Analyze the domain lifecycle states and keep business policies out of scope.", False, True, "suppressed-keep", "match"),
    ("R6-11", "Analyze what leaves lifecycle states unchanged.", False, False, "no-occurrence", "suppressed-leave"),
    ("R6-12", "Analyze why the change left lifecycle states unchanged.", False, False, "no-occurrence", "suppressed-leave"),
    ("R6-13", "Analyze the process leaving lifecycle states unchanged.", False, False, "no-occurrence", "suppressed-leave"),
    ("R6-14", "Analyze what keeps business policies out of scope.", False, False, "suppressed-keep", "no-occurrence"),
    ("R6-15", "Analyze why the change kept business policies out of scope.", False, False, "suppressed-keep", "no-occurrence"),
    ("R6-16", "Analyze the process keeping business policies out of scope.", False, False, "suppressed-keep", "no-occurrence"),
    ("R6-17", "Leave forbidden lifecycle transitions unchanged; model the domain allowed lifecycle transitions.", False, True, "no-occurrence", "direct-second-clause"),
    ("R6-18", "Lifecycle states remain unchanged; analyze a business state guard.", False, True, "no-occurrence", "direct-second-clause"),
    ("R6-19", "Business policies are not required; extract domain constraints.", True, False, "direct-second-clause", "no-occurrence"),
    ("R6-20", "Domain decision authority is out of scope; analyze business calculations.", True, False, "direct-second-clause", "no-occurrence"),
    ("R6-21", "Keep domain policies out of scope; extract business constraints.", True, False, "direct-second-clause", "no-occurrence"),
    ("R6-22", "A parser state machine is unchanged; model the domain lifecycle states.", False, True, "no-occurrence", "direct-second-clause"),
    ("R6-23", "Model the domain lifecycle states and extract business invariants.", True, True, "direct", "direct"),
    ("R6-24", "Analyze a domain invariant and model the domain lifecycle transition.", True, True, "direct", "direct"),
    ("R6-25", "Model the domain lifecycle states and document business invariants.", False, True, "barrier", "direct"),
    ("R6-26", "Model the domain lifecycle states and implement business invariants.", False, False, "mutation-mask", "mutation-mask"),
    ("R6-27", "Analyze a parser state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R6-28", "Analyze a React component state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R6-30", "Analyze a business state machine.", False, True, "no-occurrence", "direct"),
    ("R6-31", "Analyze lifecycle states for an order workflow.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R6-32", "Analyze domain constraints for order settlement.", True, False, "direct", "no-occurrence"),
    ("R7-01", "Analyze why the domain lifecycle states remain unchanged.", False, True, "no-occurrence", "direct-postfix"),
    ("R7-02", "Analyze a compiler state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R7-03", "Analyze a TCP state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R7-04", "Analyze a UI component state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R7-05", "Analyze a protocol state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R7-06", "Analyze a domain state machine.", False, True, "no-occurrence", "direct"),
    ("R7-07", "Analyze a product state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R7-08", "Analyze an order workflow state machine.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R7-09", "Analyze a product lifecycle state machine.", False, False, "no-occurrence", "owner-absent"),
    ("R7-10", "Analyze compiler state machines.", False, False, "no-occurrence", "owner-absent"),
    ("R7-11", "Analyze product workflow state machines.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R7-12", "Analyze a React component state machine for product workflow.", False, False, "no-occurrence", "owner-absent"),
    ("R8-N01", "Analyze Android lifecycle states for business workflow.", False, False, "no-occurrence", "owner-conflict"),
    ("R8-N02", "Analyze Kubernetes lifecycle transitions for domain workflow.", False, False, "no-occurrence", "owner-conflict"),
    ("R8-N03", "Analyze React transition guards for business workflow.", False, False, "no-occurrence", "owner-conflict"),
    ("R8-N04", "Analyze the Android domain lifecycle states.", False, False, "no-occurrence", "owner-conflict"),
    ("R8-N05", "Analyze Kubernetes business lifecycle transitions.", False, False, "no-occurrence", "owner-conflict"),
    ("R8-N06", "Analyze React domain transition guards.", False, False, "no-occurrence", "owner-conflict"),
    ("R8-N07", "Analyze a domain invariant and domain lifecycle states remain unchanged.", True, False, "match", "suppressed-carry"),
    ("R8-N08", "Analyze a domain invariant and leave business forbidden lifecycle transitions unchanged.", True, False, "match", "suppressed-leave"),
    ("R8-P01", "Analyze domain lifecycle states.", False, True, "no-occurrence", "match"),
    ("R8-P02", "Analyze business lifecycle transitions.", False, True, "no-occurrence", "match"),
    ("R8-P03", "Analyze business transition guards.", False, True, "no-occurrence", "match"),
    ("R8-P04", "Analyze domain terminal states.", False, True, "no-occurrence", "match"),
    ("R9-N01", "Analyze workflow lifecycle states.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R9-N02", "Analyze CI workflow lifecycle states.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R9-N03", "Analyze orchestration workflow lifecycle transitions.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R9-N04", "Analyze user workflow transition guards.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R9-N05", "Analyze interaction workflow terminal states.", False, False, "no-occurrence", "workflow-nonowner"),
    ("R6-29", "Analyze the database domain constraints.", False, False, "owner-conflict", "no-occurrence"),
    ("R10-N01", "Analyze compiler domain invariant.", False, False, "owner-conflict", "no-occurrence"),
    ("R10-N02", "Analyze infrastructure domain policy.", False, False, "owner-conflict", "no-occurrence"),
    ("R10-N03", "Analyze parser business rule.", False, False, "owner-conflict", "no-occurrence"),
    ("R10-N04", "Analyze current domain invariant.", True, False, "match", "no-occurrence"),
    ("R10-N05", "Analyze the material business policy.", True, False, "match", "no-occurrence"),
    ("R10-P01", "Analyze domain constraints.", True, False, "match", "no-occurrence"),
    ("R10-P02", "Analyze a domain invariant.", True, False, "match", "no-occurrence"),
    ("R10-P03", "Analyze business policy.", True, False, "match", "no-occurrence"),
    ("R10-P04", "Analyze business rules.", True, False, "match", "no-occurrence"),
    ("R10-P05", "Analyze how domain policy applies.", True, False, "match", "no-occurrence"),
    ("R10-P06", "Analyze which business rule applies.", True, False, "match", "no-occurrence"),
    ("R10-P07", "Analyze if a domain constraint applies.", True, False, "match", "no-occurrence"),
    ("R11-P01", "Analyze existing domain invariant.", True, False, "match", "no-occurrence"),
    ("R11-P02", "Analyze current domain lifecycle states.", False, True, "no-occurrence", "match"),
    ("R11-P03", "Analyze existing business transition guards.", False, True, "no-occurrence", "match"),
    ("R11-P04", "Analyze material domain lifecycle transition.", False, True, "no-occurrence", "match"),
    ("R11-P05", "Analyze accepted business rule.", True, False, "match", "no-occurrence"),
    ("R11-P06", "Analyze proposed domain state machine.", False, True, "no-occurrence", "match"),
    ("R11-N01", "Analyze current compiler domain invariant.", False, False, "owner-conflict", "no-occurrence"),
    ("R11-N02", "Analyze existing database domain constraints.", False, False, "owner-conflict", "no-occurrence"),
    ("R11-N03", "Analyze material Android domain lifecycle states.", False, False, "no-occurrence", "owner-conflict"),
    ("R11-N04", "Analyze proposed React business transition guards.", False, False, "no-occurrence", "owner-conflict"),
    ("R12-N01", "Analyze a new domain invariant.", False, False, "owner-conflict", "no-occurrence"),
    ("R12-N02", "Analyze a revised business policy.", False, False, "owner-conflict", "no-occurrence"),
    ("R12-N03", "Analyze the target domain lifecycle state.", False, True, "no-occurrence", "match"),
    ("R13-N01", "Analyze the target Android domain lifecycle state.", False, False, "no-occurrence", "owner-conflict"),
)
FOUNDATION_MATCHER_CLAUSE_SEPARATORS = (
    ".",
    "!",
    "?",
    ";",
    ".!?;",
    " while ",
    " but ",
    " although ",
    " whereas ",
    " yet ",
    ", while ",
    ", but ",
    ", although ",
    ", whereas ",
    ", yet ",
)
FOUNDATION_MATCHER_NON_SEPARATORS = (
    ", ",
    " and ",
    " or ",
    ": ",
)
FOUNDATION_MATCHER_ANALYSIS_VERBS = (
    "analyze",
    "analyse",
)
FOUNDATION_MATCHER_SELECTION_VERBS = (
    "select",
    "selects",
    "selected",
    "selecting",
    "choose",
    "chooses",
    "chosen",
    "choosing",
)
FOUNDATION_MATCHER_MUTATION_VERBS = (
    "add",
    "build",
    "change",
    "create",
    "fix",
    "implement",
    "migrate",
    "plan",
    "prepare",
    "refactor",
    "repair",
    "update",
    "write",
)
FOUNDATION_MATCHER_NEGATORS = (
    "do not",
    "must not",
    "should not",
    "will not",
    "never",
    "not to",
    "without",
)


def _test_strategy_runtime_matcher() -> dict[str, object]:
    rows = load_yaml_file(FOUNDATION_REGISTRY)["foundation_skills"]
    matches = [
        row["activation"]["runtime_matcher"]
        for row in rows
        if row.get("activation", {}).get("id")
        == TEST_STRATEGY_ACTIVATION_ID
    ]
    if len(matches) != 1:
        raise AssertionError(
            "the canonical registry must contain exactly one test-strategy "
            "runtime matcher"
        )
    return copy.deepcopy(next(iter(matches)))


def _foundation_matcher_matches(prompt: str) -> bool:
    matcher = getattr(ORACLE, FOUNDATION_MATCHER_HELPER, None)
    if not callable(matcher):
        raise AssertionError(
            f"{FOUNDATION_MATCHER_HELPER} is missing or not callable"
        )
    return bool(matcher(prompt, _test_strategy_runtime_matcher()))


def _repair177_runtime_matchers() -> dict[str, dict[str, object]]:
    rows = load_yaml_file(FOUNDATION_REGISTRY)["foundation_skills"]
    matchers = {
        row["name"]: copy.deepcopy(row["activation"]["runtime_matcher"])
        for row in rows
        if row.get("name") in REPAIR177_TARGETS
        and isinstance(row.get("activation"), dict)
        and isinstance(row["activation"].get("runtime_matcher"), dict)
    }
    if tuple(matchers) != REPAIR177_TARGETS:
        raise AssertionError(
            "Repair177 requires both registry-owned occurrence matchers in "
            f"Foundation order; found {tuple(matchers)!r}"
        )
    return matchers


def _repair177_static_runtime_matchers() -> dict[str, dict[str, object]]:
    def matcher(
        *,
        atom: str,
        actions: list[str],
        objects: tuple[str, ...],
        mode: str,
        modifiers: tuple[str, ...],
    ) -> dict[str, object]:
        return {
            "contract": "foundation-occurrence-matcher/v1",
            "rollout": "enabled",
            "action": "analysis-only",
            "combine": "any",
            "relations": [
                {
                    "atom": atom,
                    "operator": "governed-object-occurrence",
                    "scope": "bounded-clause",
                    "actions": actions,
                    "objects": list(objects),
                    "owner_relation": {
                        "mode": mode,
                        "qualifiers": ["business", "domain"],
                    },
                    "non_owner_modifiers": list(modifiers),
                }
            ],
        }

    return {
        "business-rule-extraction": matcher(
            atom="business-rule-occurrence",
            actions=["analyze", "analyse", "extract"],
            objects=REPAIR177_BUSINESS_OBJECTS,
            mode="intrinsic-qualified-object",
            modifiers=REPAIR177_BUSINESS_MODIFIERS,
        ),
        "state-machine-modeling": matcher(
            atom="state-machine-occurrence",
            actions=["analyze", "analyse", "model"],
            objects=REPAIR177_STATE_OBJECTS,
            mode="immediate-qualified-subject",
            modifiers=REPAIR177_STATE_MODIFIERS,
        ),
    }


def _repair177_match(
    prompt: str,
    target: str,
    *,
    matchers: dict[str, dict[str, object]] | None = None,
) -> bool:
    evaluator = getattr(ORACLE, FOUNDATION_MATCHER_HELPER, None)
    if not callable(evaluator):
        raise AssertionError(
            f"{FOUNDATION_MATCHER_HELPER} is missing or not callable"
        )
    selected = _repair177_runtime_matchers() if matchers is None else matchers
    return bool(evaluator(prompt, copy.deepcopy(selected[target])))


def _repair177_route(prompt: str, case_id: str) -> dict[str, object]:
    return ORACLE.route_with_trace(
        prompt,
        main_execution=_test_main_execution(f"repair177-{case_id}"),
    )


def _repair177_final_route(
    observed: dict[str, object],
) -> dict[str, object]:
    return observed["route_decision"]["route_result"]


def _repair177_projection_by_name() -> dict[str, dict[str, object]]:
    projections = VALIDATION.foundation_runtime_matcher_authority(
        load_yaml_file(FOUNDATION_REGISTRY),
        context="Repair177 canonical Foundation authority",
    )
    return {
        projection["name"]: projection
        for projection in projections
        if projection["name"] in REPAIR177_TARGETS
    }


def _repair177_static_projections() -> dict[str, dict[str, object]]:
    canonical = _repair177_projection_by_name()
    matchers = _repair177_static_runtime_matchers()
    return {
        name: {
            "name": name,
            "activation_id": activation_id,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "domain-impact-modeler",
            "review_skill": "architecture-impact-reviewer",
            "semantic_atoms": [
                matchers[name]["relations"][0]["atom"]
            ],
            "matcher_evidence": copy.deepcopy(
                canonical[name]["matcher_evidence"]
            ),
            "runtime_matcher": matchers[name],
        }
        for name, activation_id in zip(
            REPAIR177_TARGETS,
            REPAIR177_ACTIVATION_IDS,
            strict=True,
        )
    }


def _repair177_collect_prompt_occurrences(
    value: object,
    *,
    source: str,
    pointer: tuple[object, ...] = (),
) -> list[tuple[str, list[object], str]]:
    found: list[tuple[str, list[object], str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = (*pointer, key)
            if key == "prompt":
                if not isinstance(child, str):
                    raise AssertionError("every recursive prompt must be text")
                found.append((source, list(child_pointer), child))
            found.extend(
                _repair177_collect_prompt_occurrences(
                    child,
                    source=source,
                    pointer=child_pointer,
                )
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(
                _repair177_collect_prompt_occurrences(
                    child,
                    source=source,
                    pointer=(*pointer, index),
                )
            )
    return found


def _string_values(value: object) -> set[str]:
    values: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, str):
            values.add(item)
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple, set, frozenset)):
            for child in item:
                visit(child)

    visit(value)
    return values


def _direct_rule_ids() -> list[str]:
    tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
    route_impl = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_route_impl"
    )
    returns: list[ast.Return] = []

    class DirectReturnVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_Return(self, node: ast.Return) -> None:
            returns.append(node)

    visitor = DirectReturnVisitor()
    for statement in route_impl.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        visitor.visit(statement)
    rule_ids: list[str] = []
    for node in returns:
        value = node.value
        if (
            not isinstance(value, ast.Call)
            or not isinstance(value.func, ast.Name)
            or value.func.id != "result"
        ):
            continue
        rule_id = next(
            (
                item.value.value
                for item in value.keywords
                if item.arg == "rule_id"
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            ),
            None,
        )
        if rule_id is not None:
            rule_ids.append(rule_id)
    return rule_ids


def _candidate_rule_ids() -> list[str]:
    tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
    foundation = VALIDATION.load_yaml_file(
        ROOT / "src/registry/foundation-skills.yaml"
    )
    direct_blueprints = [
        (
            record["selector_id"],
            tuple(record["selectable_layer3"]),
            tuple(record["positive_evidence"][:-1]),
            record["owner_bindings"][0]["primary_skill"],
            record["owner_bindings"][0]["review_skill"],
        )
        for record in foundation["selector_authority"]["selectors"]
        if record["source"]["kind"] == "direct-static"
    ]
    direct_selector_ids = [
        selector_id
        for (
            selector_id,
            _foundations,
            _evidence,
            _primary,
            _review,
        ) in direct_blueprints
    ]
    route_impl = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_route_impl"
    )
    rule_ids: list[str] = []
    for node in ast.walk(route_impl):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_candidate"
        ):
            rule_id = next(
                (
                    item.value.value
                    for item in node.keywords
                    if item.arg == "rule_id"
                    and isinstance(item.value, ast.Constant)
                    and isinstance(item.value.value, str)
                ),
                None,
            )
            if rule_id is not None:
                rule_ids.append(rule_id)
    return [*direct_selector_ids, *rule_ids]


def _t2b_cases() -> dict[str, dict[str, object]]:
    cases = load_yaml_file(CASES_PATH)["cases"]
    selected_ids = (
        CRITICAL_CASE_IDS
        | PREPARATION_CASE_IDS
        | TIE_CASE_IDS
        | CONTROL_CASE_IDS
    )
    return {
        str(case["id"]): case
        for case in cases
        if isinstance(case, dict) and case.get("id") in selected_ids
    }


def _observed(case: dict[str, object]) -> dict[str, object]:
    return ORACLE.route_with_trace(
        str(case["prompt"]),
        main_execution=case["main_execution"],
    )


def _test_main_execution(task_id: str) -> dict[str, object]:
    return {
        "producer": "main-control-agent",
        "task_id": task_id,
        "execution_level": "L4",
        "level_basis": {
            "trigger_evaluations": [
                {
                    "id": "public-api-event-schema-compatibility",
                    "status": "matched",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": f"task:{task_id}:routing-api",
                    "plausible_critical": False,
                }
            ],
            "l1_eligibility": [],
            "l2_eligibility": [],
            "l5_assurance_eligibility": [],
            "l5_confirmation": "not-required",
            "obligations": ["high-risk pre-implementation evidence"],
            "unresolved": [],
            "edit_status": "allowed",
        },
    }


def _four_foundation_main_execution() -> dict[str, object]:
    task_id = "activation-v3-four-foundation"
    return {
        "producer": "main-control-agent",
        "task_id": task_id,
        "execution_level": "L4",
        "level_basis": {
            "trigger_evaluations": [
                {
                    "id": "major-architecture-or-physical-safety",
                    "status": "matched",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": FOUR_FOUNDATION_BINDING,
                    "plausible_critical": False,
                },
                {
                    "id": "unknown-critical-boundary",
                    "status": "not_matched",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": f"task:{task_id}:critical-boundary-resolved",
                    "plausible_critical": False,
                },
            ],
            "l1_eligibility": [],
            "l2_eligibility": [],
            "l5_assurance_eligibility": [],
            "l5_confirmation": "not-required",
            "obligations": ["high-risk pre-implementation evidence"],
            "unresolved": [],
            "edit_status": "allowed",
        },
    }


def _artifact_review_candidate(
    *,
    high_risk: bool,
    artifact_binding_id: str | None,
) -> dict[str, object]:
    if high_risk:
        foundations = ["release-rollback"]
        return {
            "candidate_id": "high-risk-architecture-plan",
            "candidate_type": "explicit-route",
            "evidence": ["high-risk-multiple-tasks"],
            "precedence": 5,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": foundations,
            "review_skill": "high-risk-design-review",
            "artifact_binding_id": artifact_binding_id,
            "eligible_foundation_layer3_skills": foundations,
            "eligible_domain_layer3_skills": [],
            "eligible_layer3_skills": foundations,
            "reserved_domain_capacity": 0,
            "layer3_overflow": False,
        }
    return {
        "candidate_id": "engineering-artifact-review",
        "candidate_type": "artifact-review-route",
        "evidence": ["engineering-brief", "task-plan"],
        "precedence": 3,
        "path": "direct",
        "profile": "review-agent",
        "primary_skill": "engineering-artifact-review",
        "layer3_skills": [],
        "review_skill": "engineering-artifact-review",
        "artifact_binding_id": artifact_binding_id,
        "eligible_foundation_layer3_skills": [],
        "eligible_domain_layer3_skills": [],
        "eligible_layer3_skills": [],
        "reserved_domain_capacity": 0,
        "layer3_overflow": False,
    }


def _wave1a_bound_high_risk_candidate(
    candidate_id: str,
    foundations: list[str],
    *,
    artifact_binding_id: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "explicit-route",
        "evidence": [candidate_id],
        "precedence": 5,
        "path": "direct",
        "profile": "review-agent",
        "primary_skill": "high-risk-design-review",
        "layer3_skills": list(foundations),
        "review_skill": "high-risk-design-review",
        "artifact_binding_id": artifact_binding_id,
        "rule_id": candidate_id,
        "stage": "review",
        "precedence_class": "high-risk-analysis",
        "candidate_layer3_context": {
            "kind": "fixed",
            "foundation_requests": list(foundations),
            "domain_requests": [],
        },
        "eligible_foundation_layer3_skills": list(foundations),
        "eligible_domain_layer3_skills": [],
        "eligible_layer3_skills": list(foundations),
        "reserved_domain_capacity": 0,
        "layer3_overflow": False,
    }


def _projected_route(observed: dict[str, object]) -> dict[str, object]:
    decision = observed["route_decision"]
    result = decision["route_result"]
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }


def _projected_decision(decision: dict[str, object]) -> dict[str, object]:
    result = decision["route_result"]
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _nested_mapping_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key
            for child in value.values()
            for key in _nested_mapping_keys(child)
        }
    if isinstance(value, list):
        return {
            key
            for child in value
            for key in _nested_mapping_keys(child)
        }
    return set()


def _activation_v2_139b_authority() -> dict[str, object]:
    domain_data = load_yaml_file(DOMAIN_REGISTRY)
    professional_data = load_yaml_file(PROFESSIONAL_REGISTRY)
    professional_authority = VALIDATION.professional_routing_authority(
        PROFESSIONAL_REGISTRY
    )
    return {
        "domain_specs": ORACLE.domain_route_specs(domain_data),
        "domain_authority": VALIDATION.domain_modifier_routing_authority(
            domain_data,
            professional_data,
        ),
        "layer3_authority_by_primary": professional_authority[
            "layer3_candidates_by_primary"
        ],
        "maximum_layer3": professional_data[
            "automatic_routing_policy"
        ]["implementation_owner"]["accepted"]["layer3"]["max"],
    }


def _activation_v2_139b_fixed_candidate(
    candidate_id: str,
    *,
    primary_skill: str,
    profile: str,
    path: str,
    review_skill: str,
    domains: list[str],
    foundations: list[str],
    evidence: list[str],
    reason: str | None = None,
) -> dict[str, object]:
    candidate = {
        "candidate_id": candidate_id,
        "candidate_type": "explicit-route",
        "evidence": list(evidence),
        "precedence": 5,
        "path": path,
        "profile": profile,
        "primary_skill": primary_skill,
        "layer3_skills": [*domains, *foundations],
        "review_skill": review_skill,
        "rule_id": candidate_id,
        "stage": "activation-v2-139b-fixed",
        "precedence_class": "activation-v2-139b-fixed",
        "candidate_layer3_context": {
            "kind": "fixed",
            "foundation_requests": list(foundations),
            "domain_requests": list(domains),
        },
    }
    if reason is not None:
        candidate["reason"] = reason
    return candidate


ACTIVATION_V2_139C_CONTEXT_SCHEMAS = {
    "fixed": {
        "kind",
        "foundation_requests",
        "domain_requests",
    },
    "preparation": {
        "kind",
        "domain_requests",
        "risk",
        "owners",
        "support_foundations",
        "support_rule_ids",
    },
    "review-generic": {
        "kind",
        "domain_requests",
        "support_foundations",
        "review_regression",
        "repeat_failure",
        "owner_internal_refactor",
    },
    "review-risk": {
        "kind",
        "domain_requests",
        "risk_candidate_id",
        "risk_evidence",
        "risk_foundations",
        "support_foundations",
        "review_regression",
    },
}
ACTIVATION_V2_139C_PRIVATE_FIELDS = {
    "candidate_layer3_context",
    *CANDIDATE_PRESELECTION_FIELDS,
    "source_candidate_ids",
}
ACTIVATION_V2_139C_CONFLICT_REASON = (
    "domain-layer3-authorization-conflict"
)
ACTIVATION_V2_139C_MARKER_PREFIX = "domain-layer3-incompatible:"


class _ActivationV2139CBuiltCandidatesCaptured(Exception):
    pass


def _activation_v2_139c_implementation_policy() -> dict[str, object]:
    professional_data = load_yaml_file(PROFESSIONAL_REGISTRY)
    return VALIDATION.professional_automatic_routing_authority(
        professional_data,
        context="activation-v2-139c-professional-authority",
    )["policy"]["implementation_owner"]


def _activation_v2_139c_capture_built_candidates(
    prompt: str,
    *,
    task_id: str,
) -> list[dict[str, object]]:
    real_builder = ORACLE._build_route_candidates
    captured: list[dict[str, object]] = []

    def capture(*args, **kwargs):
        built = real_builder(*args, **kwargs)
        captured.extend(copy.deepcopy(built))
        raise _ActivationV2139CBuiltCandidatesCaptured

    with mock.patch.object(
        ORACLE,
        "_build_route_candidates",
        side_effect=capture,
    ):
        try:
            ORACLE.route_with_trace(
                prompt,
                main_execution=_test_main_execution(task_id),
            )
        except _ActivationV2139CBuiltCandidatesCaptured:
            pass
    if not captured:
        raise AssertionError(
            "[activation-v2-139c-build-capture] builder returned no candidates"
        )
    return captured


def _activation_v2_139c_call_builder(
    raw_candidates: list[dict[str, object]],
    route_candidates: list[dict[str, object]],
    *,
    prompt: str,
) -> list[dict[str, object]]:
    authority = _activation_v2_139b_authority()
    return ORACLE._build_route_candidates(
        raw_candidates,
        route_candidates,
        normalized_text=" ".join(prompt.casefold().split()),
        implementation_policy=(
            _activation_v2_139c_implementation_policy()
        ),
        domain_specs=authority["domain_specs"],
    )


def _activation_v2_139c_candidate(
    candidate_id: str,
    *,
    candidate_type: str,
    precedence: int,
    path: str,
    profile: str,
    primary_skill: str,
    foundations: list[str],
    domains: list[str],
    review_skill: str,
    evidence: list[str],
    context: dict[str, object],
    routing_family: str | None = None,
) -> dict[str, object]:
    candidate: dict[str, object] = {
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "evidence": list(evidence),
        "precedence": precedence,
        "path": path,
        "profile": profile,
        "primary_skill": primary_skill,
        "layer3_skills": [*domains, *foundations],
        "review_skill": review_skill,
        "rule_id": candidate_id,
        "stage": "activation-v2-139c",
        "precedence_class": "activation-v2-139c",
        "candidate_layer3_context": copy.deepcopy(context),
    }
    if routing_family is not None:
        candidate["routing_family"] = routing_family
    return candidate


def _activation_v2_139c_fixed_candidate(
    candidate_id: str,
    *,
    candidate_type: str = "explicit-route",
    precedence: int = 5,
    path: str = "direct",
    profile: str = "task-agent",
    primary_skill: str = "backend-change-builder",
    foundations: list[str] | None = None,
    domains: list[str] | None = None,
    review_skill: str = "ai-code-review-refactor",
    evidence: list[str] | None = None,
    routing_family: str | None = None,
) -> dict[str, object]:
    actual_foundations = [] if foundations is None else foundations
    actual_domains = [] if domains is None else domains
    return _activation_v2_139c_candidate(
        candidate_id,
        candidate_type=candidate_type,
        precedence=precedence,
        path=path,
        profile=profile,
        primary_skill=primary_skill,
        foundations=actual_foundations,
        domains=actual_domains,
        review_skill=review_skill,
        evidence=(
            [f"{candidate_id}-evidence"]
            if evidence is None
            else evidence
        ),
        context={
            "kind": "fixed",
            "foundation_requests": list(actual_foundations),
            "domain_requests": list(actual_domains),
        },
        routing_family=routing_family,
    )


def _activation_v2_139c_enrich(
    candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    return ORACLE._enrich_route_candidates(
        candidates,
        **_activation_v2_139b_authority(),
    )


def _activation_v2_139c_candidate_by_id(
    candidates: list[dict[str, object]],
    candidate_id: str,
) -> dict[str, object]:
    matches = [
        candidate
        for candidate in candidates
        if candidate.get("candidate_id") == candidate_id
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one {candidate_id!r}, got {matches!r}"
        )
    return matches[0]


@contextmanager
def _activation_v2_139b_direct_enrichment_isolation():
    stage_patches = (
        mock.patch.object(
            ORACLE,
            "_build_route_candidates",
            side_effect=AssertionError(
                "[activation-v2-139b-isolation] candidate construction "
                "must not run"
            ),
        ),
        mock.patch.object(
            ORACLE,
            "_select_route_cohort_candidate",
            side_effect=AssertionError(
                "[activation-v2-139b-isolation] candidate selection "
                "must not run"
            ),
        ),
        mock.patch.object(
            ORACLE,
            "_project_route_selection",
            side_effect=AssertionError(
                "[activation-v2-139b-isolation] route projection "
                "must not run"
            ),
        ),
    )
    with stage_patches[0] as build:
        with stage_patches[1] as select:
            with stage_patches[2] as project:
                try:
                    yield
                finally:
                    build.assert_not_called()
                    select.assert_not_called()
                    project.assert_not_called()


def _critical_candidate_evidence(prompt: str) -> list[str]:
    raw_candidates = ORACLE.route_with_trace(
        prompt,
        main_execution=_test_main_execution("t2g-critical-evidence"),
    )["winner_trace"][
        "raw_candidates"
    ]
    candidates = [
        item
        for item in raw_candidates
        if item["candidate_id"] == "critical-unknown"
    ]
    if not candidates:
        return []
    if len(candidates) != 1:
        raise AssertionError(
            f"expected at most one critical-unknown candidate, got {candidates!r}"
        )
    return list(candidates[0]["evidence"])


class RouteCandidateCohortTests(unittest.TestCase):
    def test_repair10_s_batch_public_foundation_route_and_trace_contracts(
        self,
    ) -> None:
        cases = (
            {
                "s_id": "S01",
                "positive": {
                    "case_id": (
                        "capcov-admission-foundation-"
                        "cryptography-key-lifecycle-decision"
                    ),
                    "prompt": (
                        "Analyze a cryptographic construction and key "
                        "lifecycle decision for nonce, ciphertext envelope, "
                        "rotation, recovery, and destruction."
                    ),
                    "route": {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": [
                            "secret-configuration-security",
                            "cryptography-key-lifecycle",
                        ],
                        "review_skill": "security-privacy-gate",
                    },
                    "winner_id": "cryptography-key-lifecycle",
                    "winner_evidence": [
                        "cryptographic-construction-or-key-lifecycle",
                        "foundation-selector:cryptography-key-lifecycle",
                    ],
                    "selector_id": "cryptography-key-lifecycle",
                    "selector_raw_count": 1,
                    "selector_contract": (
                        [
                            "secret-configuration-security",
                            "cryptography-key-lifecycle",
                        ],
                        [
                            "cryptographic-construction-or-key-lifecycle",
                            "foundation-selector:"
                            "cryptography-key-lifecycle",
                        ],
                    ),
                    "winner_sources": [
                        (
                            "cryptography-key-lifecycle",
                            [
                                "secret-configuration-security",
                                "cryptography-key-lifecycle",
                            ],
                            [
                                "cryptographic-construction-or-key-lifecycle",
                                "foundation-selector:"
                                "cryptography-key-lifecycle",
                            ],
                        )
                    ],
                    "raw_source_ids": [
                        "cryptography-key-lifecycle"
                    ],
                    "forbidden_route_skills": [],
                },
                "negative": {
                    "case_id": (
                        "capcov-admission-foundation-"
                        "cryptography-key-lifecycle-adjacent-negative"
                    ),
                    "prompt": (
                        "Analyze authentication token validation with no key "
                        "lifecycle decision."
                    ),
                    "route": {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": [],
                        "review_skill": "security-privacy-gate",
                    },
                    "winner_id": "privacy-or-token-security",
                    "winner_evidence": [
                        "privacy-decision-or-token-validation"
                    ],
                    "selector_id": "cryptography-key-lifecycle",
                    "selector_raw_count": 0,
                    "selector_contract": None,
                    "winner_sources": [],
                    "raw_source_ids": [],
                    "forbidden_route_skills": [
                        "secret-configuration-security",
                        "cryptography-key-lifecycle",
                    ],
                },
            },
            {
                "s_id": "S02",
                "positive": {
                    "case_id": "security-anti-reliability-only",
                    "prompt": (
                        "Review a reliability-only failure with no abuse or "
                        "privacy risk, including outage degradation and "
                        "recovery behavior."
                    ),
                    "route": {
                        "path": "direct",
                        "profile": "review-agent",
                        "primary_skill": "reliability-observability-gate",
                        "layer3_skills": [
                            "degradation-circuit-breaking",
                            "observability",
                            "backup-recovery",
                        ],
                        "review_skill": "reliability-observability-gate",
                    },
                    "winner_id": "review-reliability-risk",
                    "winner_evidence": [
                        "material-outage-risk",
                        "material-degradation-risk",
                        "material-recovery-risk",
                        "reliability-only",
                        "no-abuse-or-privacy-risk",
                        "foundation-selector:"
                        "security-anti-reliability-only",
                        "dynamic-helper:_review_risk_layer3",
                        "foundation-selector:"
                        "dynamic-foundation:backup-recovery",
                    ],
                    "selector_id": "security-anti-reliability-only",
                    "selector_raw_count": 1,
                    "selector_contract": (
                        [
                            "degradation-circuit-breaking",
                            "observability",
                        ],
                        [
                            "reliability-only",
                            "no-abuse-or-privacy-risk",
                            "foundation-selector:"
                            "security-anti-reliability-only",
                        ],
                    ),
                    "winner_sources": [
                        (
                            "security-anti-reliability-only",
                            [
                                "degradation-circuit-breaking",
                                "observability",
                            ],
                            [
                                "reliability-only",
                                "no-abuse-or-privacy-risk",
                                "foundation-selector:"
                                "security-anti-reliability-only",
                            ],
                        ),
                        (
                            "dynamic-foundation:backup-recovery",
                            ["backup-recovery"],
                            [
                                "dynamic-helper:_review_risk_layer3",
                                "foundation-selector:"
                                "dynamic-foundation:backup-recovery",
                            ],
                        ),
                    ],
                    "raw_source_ids": None,
                    "forbidden_route_skills": [],
                },
                "negative": {
                    "case_id": "reliability-anti-logging-field",
                    "prompt": (
                        "Implement structured redacted logs for a logging "
                        "field-only change with no reliability decision."
                    ),
                    "route": {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "logging-design-gate",
                        "layer3_skills": ["logging-error-handling"],
                        "review_skill": "logging-design-gate",
                    },
                    "winner_id": (
                        "implementation-owner:logging-design-gate"
                    ),
                    "winner_evidence": [
                        "diagnostic-record-surface",
                        "effect-changed",
                        "explicit-implementation-action",
                        "dynamic-helper:_review_risk_layer3",
                        "foundation-selector:"
                        "dynamic-foundation:logging-error-handling",
                    ],
                    "selector_id": "security-anti-reliability-only",
                    "selector_raw_count": 0,
                    "selector_contract": None,
                    "winner_sources": [
                        (
                            "dynamic-foundation:logging-error-handling",
                            ["logging-error-handling"],
                            [
                                "dynamic-helper:_review_risk_layer3",
                                "foundation-selector:"
                                "dynamic-foundation:"
                                "logging-error-handling",
                            ],
                        )
                    ],
                    "raw_source_ids": [
                        "dynamic-foundation:logging-error-handling"
                    ],
                    "forbidden_route_skills": [
                        "degradation-circuit-breaking",
                        "observability",
                        "backup-recovery",
                        "reliability-observability-gate",
                    ],
                },
            },
            {
                "s_id": "S03",
                "positive": {
                    "case_id": (
                        "alias-ssrf-threat-professional-precedence"
                    ),
                    "prompt": (
                        "Analyze an SSRF URL fetch threat for an "
                        "authenticated service account, with no "
                        "authorization handoff or policy change."
                    ),
                    "route": {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": [
                            "threat-modeling",
                            "web-security",
                        ],
                        "review_skill": "security-privacy-gate",
                    },
                    "winner_id": (
                        "ssrf-threat-professional-precedence"
                    ),
                    "winner_evidence": [
                        "ssrf-url-fetch-threat-analysis",
                        "ssrf",
                        "url-fetch",
                        "foundation-selector:ssrf-url-fetch-analysis",
                    ],
                    "selector_id": "ssrf-url-fetch-analysis",
                    "selector_raw_count": 0,
                    "selector_contract": None,
                    "winner_sources": [
                        (
                            "ssrf-url-fetch-analysis",
                            ["threat-modeling", "web-security"],
                            [
                                "ssrf",
                                "url-fetch",
                                "foundation-selector:"
                                "ssrf-url-fetch-analysis",
                            ],
                        )
                    ],
                    "raw_source_ids": ["ssrf-url-fetch-analysis"],
                    "forbidden_route_skills": [],
                },
                "negative": {
                    "case_id": "security-anti-input-shape",
                    "prompt": (
                        "With an accepted Engineering Brief, analyze an input "
                        "shape change with no security sink."
                    ),
                    "route": {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "data-api-contract-changer",
                        "layer3_skills": ["api-contract-design"],
                        "review_skill": "architecture-impact-reviewer",
                    },
                    "winner_id": "security-anti-input-shape",
                    "winner_evidence": [
                        "input-shape-change",
                        "no-security-sink",
                        "foundation-selector:security-anti-input-shape",
                    ],
                    "selector_id": "ssrf-url-fetch-analysis",
                    "selector_raw_count": 0,
                    "selector_contract": None,
                    "winner_sources": [
                        (
                            "security-anti-input-shape",
                            ["api-contract-design"],
                            [
                                "input-shape-change",
                                "no-security-sink",
                                "foundation-selector:"
                                "security-anti-input-shape",
                            ],
                        )
                    ],
                    "raw_source_ids": ["security-anti-input-shape"],
                    "forbidden_route_skills": [
                        "threat-modeling",
                        "web-security",
                        "security-privacy-gate",
                    ],
                },
            },
            {
                "s_id": "S04",
                "positive": {
                    "case_id": (
                        "capcov-admission-foundation-"
                        "tenant-isolation-decision"
                    ),
                    "prompt": (
                        "Analyze tenant isolation across storage, cache, "
                        "queue, execution context, telemetry, and "
                        "administrative paths."
                    ),
                    "route": {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": [
                            "permission-boundary-modeling",
                            "tenant-isolation",
                        ],
                        "review_skill": "security-privacy-gate",
                    },
                    "winner_id": "tenant-isolation-security",
                    "winner_evidence": [
                        "tenant-isolation",
                        "propagated-boundary",
                        "foundation-selector:tenant-isolation-security",
                    ],
                    "selector_id": "tenant-isolation-security",
                    "selector_raw_count": 1,
                    "selector_contract": (
                        [
                            "permission-boundary-modeling",
                            "tenant-isolation",
                        ],
                        [
                            "tenant-isolation",
                            "propagated-boundary",
                            "foundation-selector:"
                            "tenant-isolation-security",
                        ],
                    ),
                    "winner_sources": [
                        (
                            "tenant-isolation-security",
                            [
                                "permission-boundary-modeling",
                                "tenant-isolation",
                            ],
                            [
                                "tenant-isolation",
                                "propagated-boundary",
                                "foundation-selector:"
                                "tenant-isolation-security",
                            ],
                        )
                    ],
                    "raw_source_ids": ["tenant-isolation-security"],
                    "forbidden_route_skills": [],
                },
                "negative": {
                    "case_id": (
                        "capcov-admission-foundation-"
                        "tenant-isolation-adjacent-negative"
                    ),
                    "prompt": (
                        "Analyze telemetry retention and deletion with no "
                        "tenant boundary change."
                    ),
                    "route": {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": ["privacy-data-lifecycle"],
                        "review_skill": "security-privacy-gate",
                    },
                    "winner_id": "privacy-or-token-security",
                    "winner_evidence": [
                        "privacy-decision-or-token-validation",
                        "personal-data-purpose",
                        "retention",
                        "foundation-selector:personal-data-lifecycle",
                    ],
                    "selector_id": "tenant-isolation-security",
                    "selector_raw_count": 0,
                    "selector_contract": None,
                    "winner_sources": [
                        (
                            "personal-data-lifecycle",
                            ["privacy-data-lifecycle"],
                            [
                                "personal-data-purpose",
                                "retention",
                                "foundation-selector:"
                                "personal-data-lifecycle",
                            ],
                        )
                    ],
                    "raw_source_ids": ["personal-data-lifecycle"],
                    "forbidden_route_skills": [
                        "permission-boundary-modeling",
                        "tenant-isolation",
                    ],
                },
            },
        )
        self.assertEqual(
            ("S01", "S02", "S03", "S04"),
            tuple(record["s_id"] for record in cases),
        )

        for record in cases:
            for polarity in ("positive", "negative"):
                case = record[polarity]
                with self.subTest(
                    s_id=record["s_id"],
                    polarity=polarity,
                    case_id=case["case_id"],
                ):
                    observed = ORACLE.route_with_trace(
                        case["prompt"],
                        main_execution=_test_main_execution(
                            case["case_id"]
                        ),
                    )
                    trace = observed["winner_trace"]
                    raw = trace["raw_candidates"]
                    winner = trace["selected_candidate"]
                    raw_ids = [
                        candidate["candidate_id"]
                        for candidate in raw
                    ]
                    raw_sources = [
                        (
                            source["candidate_id"],
                            source["foundations"],
                            source["evidence"],
                        )
                        for candidate in raw
                        for source in candidate.get(
                            "source_foundation_candidates",
                            [],
                        )
                    ]
                    winner_sources = [
                        (
                            source["candidate_id"],
                            source["foundations"],
                            source["evidence"],
                        )
                        for source in winner.get(
                            "source_foundation_candidates",
                            [],
                        )
                    ]

                    self.assertEqual(
                        case["route"],
                        _projected_route(observed),
                    )
                    self.assertEqual(
                        case["winner_id"],
                        winner["candidate_id"],
                    )
                    self.assertEqual(
                        [case["winner_id"]],
                        winner["source_candidate_ids"],
                    )
                    self.assertEqual(
                        case["winner_evidence"],
                        winner["evidence"],
                    )
                    self.assertEqual(
                        case["winner_sources"],
                        winner_sources,
                    )
                    self.assertEqual(
                        1,
                        raw_ids.count(case["winner_id"]),
                    )
                    selector_candidates = [
                        candidate
                        for candidate in raw
                        if candidate["candidate_id"]
                        == case["selector_id"]
                    ]
                    self.assertEqual(
                        case["selector_raw_count"],
                        len(selector_candidates),
                    )
                    if case["selector_contract"] is not None:
                        selector = selector_candidates[0]
                        self.assertEqual(
                            case["selector_contract"][0],
                            selector["layer3_skills"],
                        )
                        self.assertEqual(
                            case["selector_contract"][1],
                            selector["evidence"],
                        )
                        self.assertEqual(
                            [
                                (
                                    case["selector_id"],
                                    case["selector_contract"][0],
                                    case["selector_contract"][1],
                                )
                            ],
                            [
                                (
                                    source["candidate_id"],
                                    source["foundations"],
                                    source["evidence"],
                                )
                                for source in selector[
                                    "source_foundation_candidates"
                                ]
                            ],
                        )
                    expected_raw_source_ids = case[
                        "raw_source_ids"
                    ]
                    if expected_raw_source_ids is not None:
                        self.assertEqual(
                            expected_raw_source_ids,
                            [source[0] for source in raw_sources],
                        )
                    if polarity == "negative":
                        self.assertNotIn(
                            case["selector_id"],
                            raw_ids,
                        )
                        self.assertNotIn(
                            case["selector_id"],
                            [source[0] for source in raw_sources],
                        )
                        self.assertNotIn(
                            case["selector_id"],
                            [source[0] for source in winner_sources],
                        )
                    route_surface = {
                        case["route"]["primary_skill"],
                        case["route"]["review_skill"],
                        *case["route"]["layer3_skills"],
                    }
                    self.assertTrue(
                        set(
                            case["forbidden_route_skills"]
                        ).isdisjoint(route_surface)
                    )

    def test_external_integration_repair_cases_each_own_expected_route(
        self,
    ) -> None:
        cases = load_yaml_file(CASES_PATH)["cases"]
        missing_expected = [
            case.get("id")
            for case in cases
            if not isinstance(case.get("expected"), dict)
        ]
        self.assertEqual([], missing_expected)
        by_id = {case["id"]: case for case in cases}
        fail_closed = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        self.assertEqual(
            fail_closed,
            by_id[
                "t2c-repair-conflict-reliability-logging"
            ]["expected"],
        )
        self.assertEqual(
            fail_closed,
            by_id[
                "external-integration-combined-reliability-conflict"
            ]["expected"],
        )

    def test_external_integration_conjunction_polarity_is_concern_local(
        self,
    ) -> None:
        external_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "review_skill": "ai-code-review-refactor",
        }
        cases = {
            "consumer-then-failure-unchanged": (
                "Analyze an external integration downstream consumer "
                "compatibility changes and timeout and cancellation meanings "
                "remain unchanged.",
                ["consumer-impact-analysis"],
            ),
            "failure-unchanged-then-consumer": (
                "Analyze an external integration timeout and cancellation "
                "meanings remain unchanged and downstream consumer "
                "compatibility changes.",
                ["consumer-impact-analysis"],
            ),
            "failure-then-consumer-unchanged": (
                "Analyze an external integration timeout and cancellation "
                "meanings change and downstream consumer compatibility "
                "remains unchanged.",
                ["failure-contract-design"],
            ),
            "consumer-unchanged-then-failure": (
                "Analyze an external integration downstream consumer "
                "compatibility remains unchanged and timeout and "
                "cancellation meanings change.",
                ["failure-contract-design"],
            ),
            "consumer-with-negated-failure": (
                "Analyze an external integration downstream consumer "
                "compatibility changes and do not change timeout or "
                "cancellation meanings.",
                ["consumer-impact-analysis"],
            ),
            "failure-with-negated-consumer": (
                "Analyze an external integration timeout and cancellation "
                "meanings change and do not change downstream consumer "
                "compatibility.",
                ["failure-contract-design"],
            ),
        }
        observed = {}
        for label, (prompt, expected_layer3) in cases.items():
            routed = ORACLE.route_with_trace(
                prompt,
                main_execution=_test_main_execution(
                    f"{self._testMethodName}:{label}"
                ),
            )
            observed[label] = _projected_route(routed)
            self.assertEqual(
                {
                    **external_route,
                    "layer3_skills": expected_layer3,
                },
                observed[label],
            )

    def test_external_integration_negation_forms_are_scope_local(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )
        cases = {
            "without-consumer-comma-failure": (
                "Analyze an external integration without changing downstream "
                "consumer compatibility, change timeout/cancellation "
                "meanings.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "without-consumer-and-failure": (
                "Analyze an external integration without changing downstream "
                "consumer compatibility and change timeout and cancellation "
                "meanings.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "without-failure-comma-consumer": (
                "Analyze an external integration without changing timeout/"
                "cancellation meanings, change downstream consumer "
                "compatibility.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "without-failure-and-consumer": (
                "Analyze an external integration without changing timeout "
                "and cancellation meanings and change downstream consumer "
                "compatibility.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "consumer-while-not-changing-failure": (
                "Analyze an external integration downstream consumer "
                "compatibility changes while not changing timeout/"
                "cancellation meanings.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "failure-while-not-changing-consumer": (
                "Analyze an external integration timeout and cancellation "
                "meanings change while not changing downstream consumer "
                "compatibility.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "consumer-while-not-changing-degradation": (
                "Analyze an external integration downstream consumer "
                "compatibility changes while not changing degradation "
                "mechanics.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "not-changing-degradation-while-consumer": (
                "Analyze an external integration not changing degradation "
                "mechanics while downstream consumer compatibility changes.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "failure-while-not-changing-degradation": (
                "Analyze an external integration timeout and cancellation "
                "meanings change while not changing degradation mechanics; "
                "downstream consumer compatibility remains unchanged.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "not-changing-degradation-while-failure": (
                "Analyze an external integration not changing degradation "
                "mechanics while timeout and cancellation meanings change; "
                "downstream consumer compatibility remains unchanged.",
                failure_alias,
                ["failure-contract-design"],
            ),
        }
        for label, (
            prompt,
            expected_candidate_id,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [expected_candidate_id],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_reliability_requires_behavior_semantics(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )
        reliability_alias = "reliability-signal-analysis"
        field_cases = {
            "consumer-degradation-status-field": (
                "Analyze an external integration downstream consumer "
                "contract change for a degradation status field; timeout and "
                "cancellation meanings remain unchanged.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "consumer-outage-reason-enum": (
                "Analyze an external integration downstream consumer "
                "contract change for an outage reason enum; failure contract "
                "semantics remain unchanged.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "consumer-slo-label": (
                "Analyze an external integration downstream consumer "
                "contract change for an SLO label; failure contract semantics "
                "remain unchanged.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "failure-degradation-status-field": (
                "Analyze an external integration failure contract change for "
                "a degradation status field; downstream consumer "
                "compatibility remains unchanged.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "failure-outage-reason-enum": (
                "Analyze an external integration failure contract change for "
                "an outage reason enum; downstream consumer compatibility "
                "remains unchanged.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "failure-slo-label": (
                "Analyze an external integration failure contract change for "
                "an SLO label; downstream consumer compatibility remains "
                "unchanged.",
                failure_alias,
                ["failure-contract-design"],
            ),
        }
        for label, (
            prompt,
            expected_candidate_id,
            expected_layer3,
        ) in field_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [expected_candidate_id],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertNotIn(
                    reliability_alias,
                    [
                        candidate["candidate_id"]
                        for candidate in trace["excluded_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

        conflict_cases = {
            "consumer-degradation-behavior": (
                "Analyze an external integration downstream consumer "
                "compatibility change; degradation behavior changes.",
                consumer_alias,
            ),
            "failure-degradation-policy": (
                "Analyze an external integration timeout and cancellation "
                "meanings change; degradation policy changes; downstream "
                "consumer compatibility remains unchanged.",
                failure_alias,
            ),
            "consumer-timeout-behavior": (
                "Analyze an external integration downstream consumer "
                "compatibility change; timeout behavior changes.",
                consumer_alias,
            ),
            "failure-retry-behavior": (
                "Analyze an external integration failure contract meanings "
                "change; retry behavior changes; downstream consumer "
                "compatibility remains unchanged.",
                failure_alias,
            ),
            "consumer-fallback-behavior": (
                "Analyze an external integration downstream consumer "
                "compatibility change; fallback behavior changes.",
                consumer_alias,
            ),
            "failure-circuit-behavior": (
                "Analyze an external integration failure contract meanings "
                "change; circuit-breaker behavior changes; downstream "
                "consumer compatibility remains unchanged.",
                failure_alias,
            ),
            "consumer-recovery-risk": (
                "Analyze an external integration downstream consumer "
                "compatibility change; recovery risk changes.",
                consumer_alias,
            ),
        }
        for label, (
            prompt,
            external_candidate_id,
        ) in conflict_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [external_candidate_id, reliability_alias],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                selected = trace["selected_candidate"]
                self.assertEqual(
                    "route-contract-conflict",
                    selected["candidate_id"],
                )
                self.assertEqual(
                    "equal-precedence-route-contract-conflict",
                    selected["reason"],
                )
                self.assertEqual(
                    [external_candidate_id, reliability_alias],
                    selected["source_candidate_ids"],
                )
                self.assertEqual(
                    ["repository-context-map"],
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_contract_change_timeout_is_scope_local(
        self,
    ) -> None:
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )
        cases = {
            "failure-then-timeout-field": (
                "Analyze an external integration failure contract change; "
                "timeout telemetry field remains unchanged; downstream "
                "consumer compatibility remains unchanged."
            ),
            "timeout-field-then-failure": (
                "Analyze an external integration timeout telemetry field "
                "remains unchanged; failure contract change; downstream "
                "consumer compatibility remains unchanged."
            ),
            "failure-then-cancellation-label": (
                "Analyze an external integration failure contract change; "
                "cancellation telemetry label remains unchanged; downstream "
                "consumer compatibility remains unchanged."
            ),
            "cancellation-label-then-failure": (
                "Analyze an external integration cancellation telemetry "
                "label remains unchanged; failure contract change; "
                "downstream consumer compatibility remains unchanged."
            ),
            "failure-then-timeout-behavior": (
                "Analyze an external integration failure contract change; "
                "timeout telemetry behavior remains unchanged; downstream "
                "consumer compatibility remains unchanged."
            ),
            "timeout-behavior-then-failure": (
                "Analyze an external integration timeout telemetry behavior "
                "remains unchanged; failure contract change; downstream "
                "consumer compatibility remains unchanged."
            ),
        }
        for label, prompt in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    [failure_alias],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    ["failure-contract-design"],
                    _projected_route(observed)["layer3_skills"],
                )

        combined_cases = {
            "timeout-contract-change": (
                "Analyze an external integration timeout contract change."
            ),
            "cancellation-contract-change": (
                "Analyze an external integration cancellation contract "
                "change."
            ),
        }
        for label, prompt in combined_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    ["external-integration-analysis"],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    [
                        "consumer-impact-analysis",
                        "failure-contract-design",
                    ],
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_reliability_requires_local_object_action(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )
        reliability_alias = "reliability-signal-analysis"
        metadata_cases = {
            "degradation-behavior-field": (
                "Analyze an external integration downstream consumer "
                "compatibility change; degradation behavior field changes.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "outage-risk-label": (
                "Analyze an external integration failure contract change; "
                "outage risk label changes; downstream consumer "
                "compatibility remains unchanged.",
                failure_alias,
                ["failure-contract-design"],
            ),
            "recovery-policy-identifier": (
                "Analyze an external integration downstream consumer "
                "compatibility change; recovery policy identifier changes.",
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
        }
        split_cases = {}
        for delimiter, token in {
            "comma": ", ",
            "and": " and ",
            "while": " while ",
            "slash": "/",
        }.items():
            split_cases[f"{delimiter}-subject-first"] = (
                "Analyze an external integration downstream consumer "
                f"compatibility changes; degradation{token}behavior changes."
            )
            split_cases[f"{delimiter}-semantics-first"] = (
                "Analyze an external integration downstream consumer "
                f"compatibility changes; behavior changes{token}degradation."
            )
        split_cases.update(
            {
                "object-then-action": (
                    "Analyze an external integration downstream consumer "
                    "compatibility changes; degradation behavior, changes."
                ),
                "action-then-object": (
                    "Analyze an external integration downstream consumer "
                    "compatibility changes; changes, degradation behavior."
                ),
            }
        )
        for label, (
            prompt,
            expected_candidate_id,
            expected_layer3,
        ) in metadata_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    [expected_candidate_id],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )
        for label, prompt in split_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [consumer_alias],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertNotIn(
                    reliability_alias,
                    [
                        candidate["candidate_id"]
                        for candidate in trace["excluded_candidates"]
                    ],
                )

        positive_cases = {
            "degradation-behavior": (
                "Analyze an external integration downstream consumer "
                "compatibility change; degradation behavior changes.",
                consumer_alias,
            ),
            "outage-risk": (
                "Analyze an external integration failure contract change; "
                "outage risk changes; downstream consumer compatibility "
                "remains unchanged.",
                failure_alias,
            ),
            "recovery-policy": (
                "Analyze an external integration downstream consumer "
                "compatibility change; recovery policy changes.",
                consumer_alias,
            ),
            "fallback-mechanics": (
                "Analyze an external integration failure contract change; "
                "fallback mechanics change; downstream consumer "
                "compatibility remains unchanged.",
                failure_alias,
            ),
        }
        for label, (
            prompt,
            external_candidate_id,
        ) in positive_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [external_candidate_id, reliability_alias],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    "route-contract-conflict",
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertEqual(
                    "equal-precedence-route-contract-conflict",
                    trace["selected_candidate"]["reason"],
                )

        non_external = ORACLE.route_with_trace(
            "Analyze a degradation behavior field change.",
            main_execution=_test_main_execution(
                f"{self._testMethodName}:non-external-legacy"
            ),
        )
        self.assertEqual(
            [reliability_alias],
            [
                candidate["candidate_id"]
                for candidate in non_external[
                    "winner_trace"
                ]["raw_candidates"]
            ],
        )

    def test_external_integration_contradictory_effects_fail_closed(
        self,
    ) -> None:
        cases = {
            "consumer-same-clause": (
                "Analyze an external integration downstream consumer "
                "compatibility both changes and remains unchanged; failure "
                "contract semantics remain unchanged.",
                "consumer",
            ),
            "consumer-changed-first": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; downstream consumer compatibility "
                "remains unchanged; failure contract semantics remain "
                "unchanged.",
                "consumer",
            ),
            "consumer-unchanged-first": (
                "Analyze an external integration downstream consumer "
                "compatibility remains unchanged; downstream consumer "
                "compatibility changes; failure contract semantics remain "
                "unchanged.",
                "consumer",
            ),
            "failure-same-clause": (
                "Analyze an external integration failure contract both "
                "changes and remains unchanged; downstream consumer "
                "compatibility remains unchanged.",
                "failure",
            ),
            "failure-changed-first": (
                "Analyze an external integration failure contract changes; "
                "failure contract remains unchanged; downstream consumer "
                "compatibility remains unchanged.",
                "failure",
            ),
            "failure-unchanged-first": (
                "Analyze an external integration failure contract remains "
                "unchanged; failure contract changes; downstream consumer "
                "compatibility remains unchanged.",
                "failure",
            ),
            "reliability-same-clause": (
                "Analyze an external integration degradation behavior both "
                "changes and remains unchanged; downstream consumer and "
                "failure contract semantics remain unchanged.",
                "reliability",
            ),
            "reliability-changed-first": (
                "Analyze an external integration degradation behavior "
                "changes; degradation behavior remains unchanged; downstream "
                "consumer and failure contract semantics remain unchanged.",
                "reliability",
            ),
            "reliability-unchanged-first": (
                "Analyze an external integration degradation behavior "
                "remains unchanged; degradation behavior changes; downstream "
                "consumer and failure contract semantics remain unchanged.",
                "reliability",
            ),
        }
        fail_closed = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        prohibited_ids = {
            "external-integration-analysis",
            "external-integration-consumer-impact-analysis",
            "external-integration-failure-contract-analysis",
            "reliability-signal-analysis",
        }
        for label, (prompt, concern) in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                selected = trace["selected_candidate"]
                self.assertEqual(fail_closed, _projected_route(observed))
                self.assertEqual(
                    ["critical-unknown"],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    "critical-unknown",
                    selected["candidate_id"],
                )
                self.assertIn(
                    "critical-source:external-integration-"
                    f"{concern}-effect-contradiction",
                    selected["evidence"],
                )
                self.assertEqual(
                    "highest-semantic-precedence",
                    selected["reason"],
                )
                self.assertTrue(
                    prohibited_ids.isdisjoint(
                        {
                            candidate["candidate_id"]
                            for candidate in [
                                *trace["raw_candidates"],
                                *trace["excluded_candidates"],
                            ]
                        }
                    )
                )

        singleton_cases = {
            "consumer-changed-failure-unchanged": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; failure contract semantics remain "
                "unchanged.",
                "external-integration-consumer-impact-analysis",
                ["consumer-impact-analysis"],
            ),
            "failure-changed-consumer-unchanged": (
                "Analyze an external integration failure contract changes; "
                "downstream consumer compatibility remains unchanged.",
                "external-integration-failure-contract-analysis",
                ["failure-contract-design"],
            ),
            "consumer-changed-reliability-unchanged": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; degradation behavior remains "
                "unchanged; failure contract semantics remain unchanged.",
                "external-integration-consumer-impact-analysis",
                ["consumer-impact-analysis"],
            ),
        }
        for label, (
            prompt,
            expected_candidate_id,
            expected_layer3,
        ) in singleton_cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    [expected_candidate_id],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_structured_records_are_finite_and_ordered(
        self,
    ) -> None:
        record_type = getattr(
            ORACLE,
            "_ExternalConcernEffectRecord",
            None,
        )
        builder = getattr(
            ORACLE,
            "_build_external_concern_effect_records",
            None,
        )
        self.assertTrue(
            isinstance(record_type, type),
            "R4 requires one private external concern/effect record",
        )
        self.assertTrue(
            callable(builder),
            "R4 requires one private external record builder",
        )
        records = builder(
            "Analyze an external integration downstream consumer "
            "compatibility changes; degradation recovery mechanics change. "
            "Analyze a local service outage risk change. "
            "Analyze an external integration failure contract changes; "
            "retry fallback policy changes."
        )
        self.assertTrue(
            all(isinstance(record, record_type) for record in records)
        )
        self.assertEqual(
            [
                (
                    0,
                    0,
                    "consumer",
                    "compatibility",
                    "compatibility",
                    "changed",
                ),
                (
                    0,
                    1,
                    "reliability",
                    "recovery",
                    "mechanics",
                    "changed",
                ),
                (
                    1,
                    0,
                    "failure",
                    "failure contract",
                    "contract",
                    "changed",
                ),
                (
                    1,
                    1,
                    "reliability",
                    "fallback",
                    "policy",
                    "changed",
                ),
            ],
            [
                (
                    record.session_id,
                    record.clause_id,
                    record.concern,
                    record.subject_alias,
                    record.semantic_head,
                    record.effect,
                )
                for record in records
            ],
        )
        self.assertEqual(
            (),
            builder(
                "Analyze an external integration subscriber agreement "
                "changes; resilience posture changes."
            ),
            "open-ended aliases must not enter the finite record vocabulary",
        )

    def test_external_integration_structured_sessions_block_leakage(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        cases = {
            "later-non-external-reliability": (
                "Analyze an external integration downstream consumer "
                "compatibility changes. Degradation behavior changes.",
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "external-subject-only-then-reliability": (
                "Analyze an external integration. Degradation behavior "
                "changes.",
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "earlier-non-external-reliability": (
                "Degradation behavior changes. Analyze an external "
                "integration downstream consumer compatibility changes.",
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "same-session-reliability": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; degradation behavior changes.",
                [
                    consumer_alias,
                    "reliability-signal-analysis",
                ],
                ["repository-context-map"],
            ),
        }
        for label, (
            prompt,
            expected_raw_ids,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    expected_raw_ids,
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_prefix_action_stays_clause_local(
        self,
    ) -> None:
        cases = {
            "consumer": (
                "Change an external integration downstream consumer "
                "compatibility.",
                "consumer",
                "external-integration-consumer-impact-analysis",
                ["consumer-impact-analysis"],
            ),
            "failure": (
                "Update an external integration failure contract.",
                "failure",
                "external-integration-failure-contract-analysis",
                ["failure-contract-design"],
            ),
            "reliability": (
                "Change an external integration degradation behavior.",
                "reliability",
                "reliability-signal-analysis",
                [
                    "degradation-circuit-breaking",
                    "observability",
                ],
            ),
        }
        for label, (
            prompt,
            expected_concern,
            expected_candidate,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                records = (
                    ORACLE._build_external_concern_effect_records(prompt)
                )
                self.assertEqual(
                    [(expected_concern, "changed")],
                    [
                        (record.concern, record.effect)
                        for record in records
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    [expected_candidate],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_local_subject_terminates_session(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        cases = {
            "local-service-after-member": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; local service degradation behavior "
                "changes.",
                [("consumer", "changed")],
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "bare-then-local-service": (
                "Analyze an external integration; local service degradation "
                "behavior changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "local-database-after-member": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; local database outage risk changes.",
                [("consumer", "changed")],
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "different-unlisted-subject-after-member": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; internal queue degradation behavior "
                "changes.",
                [("consumer", "changed")],
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
        }
        for label, (
            prompt,
            expected_records,
            expected_candidates,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                records = (
                    ORACLE._build_external_concern_effect_records(prompt)
                )
                self.assertEqual(
                    expected_records,
                    [
                        (record.concern, record.effect)
                        for record in records
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    expected_candidates,
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

    def _assert_external_semantic_critical_unknown(
        self,
        *,
        prompt: str,
        concern: str,
        label: str,
    ) -> dict[str, object]:
        observed = ORACLE.route_with_trace(
            prompt,
            main_execution=_test_main_execution(
                f"{self._testMethodName}:{label}"
            ),
        )
        trace = observed["winner_trace"]
        selected = trace["selected_candidate"]
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            _projected_route(observed),
        )
        self.assertEqual(
            ["critical-unknown"],
            [
                candidate["candidate_id"]
                for candidate in trace["raw_candidates"]
            ],
        )
        self.assertEqual("critical-unknown", selected["candidate_id"])
        self.assertIn(
            "critical-source:external-integration-"
            f"{concern}-effect-contradiction",
            selected["evidence"],
        )
        self.assertEqual(
            "highest-semantic-precedence",
            selected["reason"],
        )
        prohibited_ids = {
            "external-integration-analysis",
            "external-integration-consumer-impact-analysis",
            "external-integration-failure-contract-analysis",
            "reliability-signal-analysis",
        }
        self.assertTrue(
            prohibited_ids.isdisjoint(
                {
                    candidate["candidate_id"]
                    for candidate in [
                        *trace["raw_candidates"],
                        *trace["excluded_candidates"],
                    ]
                }
            )
        )
        return observed

    def test_external_integration_r3_semantic_ssot_and_binding_contract(
        self,
    ) -> None:
        semantics = getattr(
            ORACLE,
            "_EXTERNAL_RELATION_SEMANTICS",
            None,
        )
        classifier = getattr(
            ORACLE,
            "_classify_external_relation_semantics",
            None,
        )
        binding_type = getattr(
            ORACLE,
            "_ExternalEffectScopeBinding",
            None,
        )
        binding_builder = getattr(
            ORACLE,
            "_build_external_effect_scope_bindings",
            None,
        )
        resolver = getattr(
            ORACLE,
            "_resolve_external_binding_effect",
            None,
        )
        self.assertIsInstance(semantics, MappingProxyType)
        self.assertTrue(callable(classifier))
        self.assertTrue(isinstance(binding_type, type))
        self.assertTrue(callable(binding_builder))
        self.assertTrue(callable(resolver))
        self.assertEqual(
            {
                "change",
                "modification",
            },
            set(semantics["direct_effect_nominals"]),
        )
        self.assertEqual(
            {
                ("reference", "to"),
                ("documentation", "about"),
                ("example", "mentioning"),
            },
            set(semantics["wrapper_operators"]),
        )
        self.assertEqual(
            {"service", "database", "queue"},
            set(semantics["different_owner_heads"]),
        )
        self.assertEqual(
            {"deployment", "client", "failover"},
            set(semantics["same_context_heads"]),
        )
        self.assertEqual(
            {"local", "internal"},
            set(semantics["owner_modifiers"]),
        )
        self.assertEqual(
            {"unrelated"},
            set(semantics["uncertain_owner_modifiers"]),
        )
        self.assertEqual(
            "client",
            semantics["surface_to_canonical"]["clients"],
        )

        source = ORACLE_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            "_EXTERNAL_DIFFERENT_SUBJECT_OWNER_RE",
            source,
        )
        self.assertNotIn("def _external_scope_effect(", source)
        self.assertEqual(
            1,
            source.count("_EXTERNAL_RELATION_SEMANTICS ="),
        )
        self.assertEqual(
            1,
            source.count(
                "def _classify_external_relation_semantics("
            ),
        )
        self.assertEqual(
            1,
            source.count("def _resolve_external_binding_effect("),
        )

    def test_external_integration_r3_action_relation_and_polarity_matrix(
        self,
    ) -> None:
        negative_cases = {
            "consumer": (
                "Do not change an external integration downstream consumer "
                "compatibility.",
                "consumer",
            ),
            "failure": (
                "Never update an external integration failure contract.",
                "failure",
            ),
            "reliability": (
                "Should not change an external integration degradation "
                "behavior.",
                "reliability",
            ),
        }
        for label, (prompt, concern) in negative_cases.items():
            with self.subTest(kind="negative-direct", label=label):
                bindings = (
                    ORACLE._build_external_effect_scope_bindings(prompt)
                )
                relevant = [
                    binding
                    for binding in bindings
                    if binding.concern == concern
                ]
                self.assertEqual(1, len(relevant))
                binding = relevant[0]
                self.assertEqual("direct", binding.action_relation)
                self.assertEqual("unchanged", binding.action_polarity)
                self.assertIsNotNone(binding.action_prefix_span)
                records = (
                    ORACLE._build_external_concern_effect_records(prompt)
                )
                self.assertEqual(
                    [(concern, "unchanged")],
                    [
                        (record.concern, record.effect)
                        for record in records
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    ["repository-first-default"],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    ["repository-context-map"],
                    _projected_route(observed)["layer3_skills"],
                )

        direct_nominals = {
            "change": (
                "Implement a change to an external integration failure "
                "contract."
            ),
            "modification": (
                "Implement a modification to an external integration "
                "failure contract."
            ),
        }
        for nominal, prompt in direct_nominals.items():
            with self.subTest(kind="direct-nominal", nominal=nominal):
                binding = (
                    ORACLE._build_external_effect_scope_bindings(prompt)[0]
                )
                self.assertEqual("direct", binding.action_relation)
                self.assertEqual(
                    "direct-effect",
                    binding.semantic_category,
                )
                self.assertIn(nominal, binding.semantic_evidence)
                records = (
                    ORACLE._build_external_concern_effect_records(prompt)
                )
                self.assertEqual(
                    [("failure", "changed")],
                    [
                        (record.concern, record.effect)
                        for record in records
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{nominal}"
                    ),
                )
                self.assertEqual(
                    ["external-integration-failure-contract-analysis"],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    ["failure-contract-design"],
                    _projected_route(observed)["layer3_skills"],
                )

        prompt = (
            "Implement an adjustment to an external integration failure "
            "contract."
        )
        binding = ORACLE._build_external_effect_scope_bindings(prompt)[0]
        self.assertEqual("unbound", binding.action_relation)
        self.assertEqual("unknown", binding.semantic_category)
        self.assertEqual(
            [("failure", "ambiguous")],
            [
                (record.concern, record.effect)
                for record
                in ORACLE._build_external_concern_effect_records(prompt)
            ],
        )
        self._assert_external_semantic_critical_unknown(
            prompt=prompt,
            concern="failure",
            label="adjustment-to",
        )

    def test_external_integration_r3_wrapper_and_unbound_matrix(
        self,
    ) -> None:
        wrapper_cases = {
            "documentation-about": (
                "Update documentation about an external integration "
                "downstream consumer compatibility.",
                "consumer",
            ),
            "reference-to": (
                "Update a reference to an external integration failure "
                "contract.",
                "failure",
            ),
            "example-mentioning": (
                "Change an example mentioning an external integration "
                "degradation behavior.",
                "reliability",
            ),
        }
        for label, (prompt, concern) in wrapper_cases.items():
            with self.subTest(kind="wrapper", label=label):
                binding = (
                    ORACLE._build_external_effect_scope_bindings(prompt)[0]
                )
                self.assertEqual(
                    "wrapper-reference",
                    binding.action_relation,
                )
                self.assertEqual("wrapper", binding.semantic_category)
                self.assertEqual(
                    [(concern, "adjacent-only")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    ["repository-first-default"],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )

        unbound_cases = {
            "documentation-to": (
                "Update documentation to an external integration downstream "
                "consumer compatibility.",
                "consumer",
            ),
            "reference-about": (
                "Update a reference about an external integration failure "
                "contract.",
                "failure",
            ),
            "guide-about": (
                "Update a guide about an external integration downstream "
                "consumer compatibility.",
                "consumer",
            ),
            "material-around": (
                "Update material around an external integration failure "
                "contract.",
                "failure",
            ),
        }
        for label, (prompt, concern) in unbound_cases.items():
            with self.subTest(kind="unbound", label=label):
                binding = (
                    ORACLE._build_external_effect_scope_bindings(prompt)[0]
                )
                self.assertEqual("unbound", binding.action_relation)
                self.assertEqual("unknown", binding.semantic_category)
                self.assertEqual(
                    [(concern, "ambiguous")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern=concern,
                    label=label,
                )

    def test_external_integration_r3_different_owner_matrix(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        cases = {
            "pre-service": (
                "Analyze an external integration local service degradation "
                "behavior changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "pre-database": (
                "Analyze an external integration local database outage risk "
                "changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "pre-queue": (
                "Analyze an external integration internal queue degradation "
                "behavior changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "post-service-embedded": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; degradation behavior in a local "
                "service changes.",
                [("consumer", "changed")],
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "post-database-embedded": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; outage risk for a local database "
                "changes.",
                [("consumer", "changed")],
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "post-queue-embedded": (
                "Analyze an external integration downstream consumer "
                "compatibility changes; degradation behavior in an internal "
                "queue changes.",
                [("consumer", "changed")],
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "post-service-bare": (
                "Analyze an external integration; degradation behavior in a "
                "local service changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "post-database-bare": (
                "Analyze an external integration; outage risk for a local "
                "database changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "post-queue-bare": (
                "Analyze an external integration; degradation behavior in an "
                "internal queue changes.",
                [],
                ["repository-first-default"],
                ["repository-context-map"],
            ),
        }
        for label, (
            prompt,
            expected_records,
            expected_raw_ids,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                bindings = (
                    ORACLE._build_external_effect_scope_bindings(prompt)
                )
                reliability_bindings = [
                    binding
                    for binding in bindings
                    if binding.concern == "reliability"
                ]
                self.assertEqual(1, len(reliability_bindings))
                self.assertEqual(
                    "explicit-different",
                    reliability_bindings[0].continuation_owner,
                )
                self.assertEqual(
                    expected_records,
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    expected_raw_ids,
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )

    def test_external_integration_r3_context_and_unknown_owner_matrix(
        self,
    ) -> None:
        context_cases = {
            "deployment": (
                "Change an external integration fallback policy for a local "
                "deployment.",
                "deployment",
            ),
            "failover": (
                "Analyze an external integration degradation behavior for "
                "local failover changes.",
                "failover",
            ),
            "clients": (
                "Analyze an external integration degradation behavior for "
                "local clients changes.",
                "client",
            ),
        }
        for label, (prompt, canonical_head) in context_cases.items():
            with self.subTest(kind="same-context", label=label):
                reliability_bindings = [
                    binding
                    for binding in (
                        ORACLE
                        ._build_external_effect_scope_bindings(prompt)
                    )
                    if binding.concern == "reliability"
                ]
                self.assertEqual(1, len(reliability_bindings))
                binding = reliability_bindings[0]
                self.assertEqual(
                    "same-external-context",
                    binding.continuation_owner,
                )
                self.assertEqual(
                    "same-context",
                    binding.semantic_category,
                )
                self.assertIn(
                    canonical_head,
                    binding.semantic_evidence,
                )
                self.assertEqual(
                    [("reliability", "changed")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    ["reliability-signal-analysis"],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    [
                        "degradation-circuit-breaking",
                        "observability",
                    ],
                    _projected_route(observed)["layer3_skills"],
                )

        ambiguous_cases = {
            "unknown-appliance": (
                "Analyze an external integration degradation behavior for a "
                "local appliance changes."
            ),
            "unrelated-service": (
                "Analyze an external integration; degradation behavior in an "
                "unrelated service changes."
            ),
            "conflicting-heads": (
                "Analyze an external integration degradation behavior for a "
                "local database deployment changes."
            ),
        }
        for label, prompt in ambiguous_cases.items():
            with self.subTest(kind="ambiguous-owner", label=label):
                reliability_bindings = [
                    binding
                    for binding in (
                        ORACLE
                        ._build_external_effect_scope_bindings(prompt)
                    )
                    if binding.concern == "reliability"
                ]
                self.assertEqual(1, len(reliability_bindings))
                self.assertEqual(
                    "ambiguous",
                    reliability_bindings[0].continuation_owner,
                )
                self.assertEqual(
                    [("reliability", "ambiguous")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern="reliability",
                    label=label,
                )

        no_owner_cases = {
            "head-without-modifier": (
                "Analyze an external integration degradation behavior for a "
                "database changes."
            ),
            "context-head-outside-phrase": (
                "Analyze an external integration deployment degradation "
                "behavior changes."
            ),
            "modifier-outside-session": (
                "Analyze local deployment planning. Change an external "
                "integration degradation behavior."
            ),
        }
        for label, prompt in no_owner_cases.items():
            with self.subTest(kind="no-owner-shape", label=label):
                records = (
                    ORACLE._build_external_concern_effect_records(prompt)
                )
                self.assertEqual(
                    [("reliability", "changed")],
                    [
                        (record.concern, record.effect)
                        for record in records
                    ],
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                self.assertEqual(
                    ["reliability-signal-analysis"],
                    [
                        candidate["candidate_id"]
                        for candidate in observed[
                            "winner_trace"
                        ]["raw_candidates"]
                    ],
                )

    def test_external_integration_r3_p1_owner_shape_requires_full_proof(
        self,
    ) -> None:
        ambiguous_cases = {
            "unknown-modifier-known-owner": (
                "Analyze an external integration degradation behavior for "
                "a remote database changes.",
                ("remote", "database"),
            ),
            "unknown-modifier-known-context": (
                "Analyze an external integration degradation behavior for "
                "a partner deployment changes.",
                ("partner", "deployment"),
            ),
            "incomplete-known-modifier": (
                "Analyze an external integration local degradation "
                "behavior changes.",
                ("local",),
            ),
            "unrecognized-owner-relation": (
                "Analyze an external integration degradation behavior "
                "beside a local database changes.",
                ("beside", "local", "database"),
            ),
        }
        for label, (prompt, expected_evidence) in (
            ambiguous_cases.items()
        ):
            with self.subTest(kind="unproven-owner", label=label):
                reliability_bindings = [
                    binding
                    for binding in (
                        ORACLE
                        ._build_external_effect_scope_bindings(prompt)
                    )
                    if binding.concern == "reliability"
                ]
                self.assertEqual(1, len(reliability_bindings))
                binding = reliability_bindings[0]
                self.assertEqual(
                    "ambiguous",
                    binding.continuation_owner,
                )
                self.assertEqual("unknown", binding.semantic_category)
                for token in expected_evidence:
                    self.assertIn(token, binding.semantic_evidence)
                self.assertEqual(
                    [("reliability", "ambiguous")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern="reliability",
                    label=label,
                )

        classifier_cases = {
            "proved-different": (
                "for a local database changes",
                "different-owner",
            ),
            "proved-same": (
                "for a local deployment changes",
                "same-context",
            ),
            "proved-no-owner": (
                "changes",
                "none",
            ),
            "unknown-modifier": (
                "for a remote database changes",
                "unknown",
            ),
            "incomplete-head": (
                "local",
                "unknown",
            ),
            "unknown-relation": (
                "beside a local database changes",
                "unknown",
            ),
        }
        for label, (phrase, expected_category) in (
            classifier_cases.items()
        ):
            with self.subTest(kind="classifier-state", label=label):
                classification = (
                    ORACLE._classify_external_relation_semantics(
                        phrase,
                        relation_context="continuation-owner",
                    )
                )
                self.assertEqual(
                    expected_category,
                    classification.category,
                )

        no_owner_prompt = (
            "Analyze an external integration degradation behavior changes."
        )
        no_owner_binding = (
            ORACLE._build_external_effect_scope_bindings(
                no_owner_prompt
            )[0]
        )
        self.assertEqual(
            "explicit-external",
            no_owner_binding.continuation_owner,
        )
        self.assertEqual(
            [("reliability", "changed")],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE
                    ._build_external_concern_effect_records(
                        no_owner_prompt
                    )
                )
            ],
        )
        no_owner_observed = ORACLE.route_with_trace(
            no_owner_prompt,
            main_execution=_test_main_execution(
                f"{self._testMethodName}:proved-no-owner"
            ),
        )
        self.assertEqual(
            ["reliability-signal-analysis"],
            [
                candidate["candidate_id"]
                for candidate in no_owner_observed[
                    "winner_trace"
                ]["raw_candidates"]
            ],
        )

        semantic_sources = "\n".join(
            (
                repr(ORACLE._EXTERNAL_RELATION_SEMANTICS),
                inspect.getsource(
                    ORACLE._classify_external_relation_semantics
                ),
                inspect.getsource(
                    ORACLE._external_owner_relation_phrases
                ),
            )
        )
        self.assertNotIn("remote", semantic_sources)

    def _assert_external_r5_binding_spans_are_local(
        self,
        binding: object,
    ) -> None:
        scope = binding.scope
        self.assertEqual(
            "external integration",
            scope[slice(*binding.external_subject_span)],
        )
        self.assertEqual(
            binding.subject_alias,
            scope[slice(*binding.subject_span)],
        )
        self.assertEqual(
            binding.semantic_head,
            scope[slice(*binding.head_span)],
        )
        if binding.concern_prefix_span is not None:
            self.assertRegex(
                scope[slice(*binding.concern_prefix_span)],
                r"^(?:no|without)\b",
            )
        if binding.shared_terminal_effect_span is not None:
            self.assertIn(
                scope[slice(*binding.shared_terminal_effect_span)],
                ORACLE._EXTERNAL_RELATION_SEMANTICS[
                    "effect_action_surfaces"
                ],
            )
        self.assertEqual(
            binding.action_verb,
            scope[slice(*binding.action_span)],
        )
        for candidate_span in binding.owner_candidate_spans:
            self.assertTrue(
                scope[slice(*candidate_span)].strip()
            )
        self.assertEqual(
            binding.predicate_scope,
            scope[slice(*binding.effect_window_span)],
        )
        barrier_start, barrier_end = binding.barrier_span
        self.assertGreaterEqual(barrier_start, binding.head_span[1])
        self.assertGreaterEqual(barrier_end, barrier_start)
        self.assertLessEqual(barrier_end, len(scope))

    def test_external_integration_r5_owner_totality_metadata_and_none(
        self,
    ) -> None:
        ambiguous_owner_cases = {
            "one-opaque-token": (
                "Analyze an external integration degradation behavior for "
                "a widget changes."
            ),
            "two-opaque-tokens": (
                "Analyze an external integration degradation behavior for "
                "a remote appliance changes."
            ),
            "three-opaque-tokens": (
                "Analyze an external integration degradation behavior for "
                "a very remote appliance changes."
            ),
        }
        for label, prompt in ambiguous_owner_cases.items():
            with self.subTest(kind="for-totality", label=label):
                binding = (
                    ORACLE._build_external_effect_scope_bindings(prompt)[0]
                )
                self.assertEqual(
                    "ambiguous",
                    binding.continuation_owner,
                )
                self.assertEqual("unknown", binding.semantic_category)
                self.assertEqual(
                    [("reliability", "ambiguous")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern="reliability",
                    label=label,
                )

        malformed_for_cases = {
            "missing-article": (
                "Analyze an external integration degradation behavior for "
                "widget changes."
            ),
            "repeated-article": (
                "Analyze an external integration degradation behavior for "
                "a an widget changes."
            ),
            "repeated-relation": (
                "Analyze an external integration degradation behavior for "
                "for a widget changes."
            ),
            "too-many-residuals": (
                "Analyze an external integration degradation behavior for "
                "a one two three four changes."
            ),
            "residual-action": (
                "Analyze an external integration degradation behavior for "
                "a widget update changes."
            ),
            "residual-unchanged-tail": (
                "Analyze an external integration degradation behavior for "
                "a widget remains unchanged changes."
            ),
        }
        for label, prompt in malformed_for_cases.items():
            with self.subTest(kind="malformed-for", label=label):
                binding = (
                    ORACLE._build_external_effect_scope_bindings(prompt)[0]
                )
                self.assertEqual(
                    "ambiguous",
                    binding.continuation_owner,
                )
                self.assertEqual("unknown", binding.semantic_category)
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern="reliability",
                    label=label,
                )

        for label, fragment in {
            "degradation-status-field": (
                "for a degradation status field"
            ),
            "outage-reason-enum": "for an outage reason enum",
            "slo-label": "for an slo label",
        }.items():
            with self.subTest(kind="metadata", label=label):
                classification = (
                    ORACLE._classify_external_relation_semantics(
                        fragment,
                        relation_context="continuation-owner",
                        concern="consumer",
                    )
                )
                self.assertEqual(
                    "metadata-qualifier",
                    classification.category,
                )

        metadata_cross_negatives = {
            "in-relation": "in a degradation status field",
            "owner-modifier": (
                "for a local degradation status field"
            ),
            "semantic-head-descriptor": (
                "for a degradation behavior field"
            ),
            "leftover": (
                "for a degradation status field extra"
            ),
            "action-descriptor": (
                "for a degradation update field"
            ),
        }
        for label, fragment in metadata_cross_negatives.items():
            prompt = (
                "Analyze an external integration downstream consumer "
                f"contract change {fragment}."
            )
            with self.subTest(kind="metadata-negative", label=label):
                consumer_bindings = [
                    binding
                    for binding in (
                        ORACLE
                        ._build_external_effect_scope_bindings(prompt)
                    )
                    if binding.concern == "consumer"
                ]
                self.assertEqual(1, len(consumer_bindings))
                self.assertEqual(
                    "ambiguous",
                    consumer_bindings[0].continuation_owner,
                )
                self.assertEqual(
                    "unknown",
                    consumer_bindings[0].semantic_category,
                )
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern="consumer",
                    label=label,
                )

        in_prompt = (
            "Analyze an external integration degradation behavior in a "
            "widget changes."
        )
        in_binding = (
            ORACLE._build_external_effect_scope_bindings(in_prompt)[0]
        )
        self.assertEqual(
            "explicit-external",
            in_binding.continuation_owner,
        )
        self.assertEqual(
            [("reliability", "changed")],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE._build_external_concern_effect_records(
                        in_prompt
                    )
                )
            ],
        )

        known_head_prompt = (
            "Analyze an external integration degradation behavior for a "
            "database changes."
        )
        known_head_binding = (
            ORACLE._build_external_effect_scope_bindings(
                known_head_prompt
            )[0]
        )
        self.assertEqual(
            "explicit-external",
            known_head_binding.continuation_owner,
        )
        self.assertEqual(
            [("reliability", "changed")],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE._build_external_concern_effect_records(
                        known_head_prompt
                    )
                )
            ],
        )

        no_owner_prompt = (
            "Analyze an external integration degradation behavior changes."
        )
        no_owner_scopes = ORACLE._external_session_scopes(
            no_owner_prompt
        )
        self.assertTrue(no_owner_scopes)
        self.assertTrue(
            all(len(scope_row) == 3 for scope_row in no_owner_scopes)
        )
        no_owner_binding = (
            ORACLE._build_external_effect_scope_bindings(
                no_owner_prompt
            )[0]
        )
        self.assertEqual(
            "explicit-external",
            no_owner_binding.continuation_owner,
        )
        self.assertEqual(
            [("reliability", "changed")],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE._build_external_concern_effect_records(
                        no_owner_prompt
                    )
                )
            ],
        )

    def test_external_integration_r5_local_coordinates_and_barriers(
        self,
    ) -> None:
        c1_prompt = (
            "Analyze an external integration degradation behavior changes "
            "then update degradation behavior for a local deployment "
            "changes."
        )
        c1_bindings = (
            ORACLE._build_external_effect_scope_bindings(c1_prompt)
        )
        self.assertEqual(1, len(c1_bindings))
        c1_binding = c1_bindings[0]
        self.assertEqual("reliability", c1_binding.concern)
        self.assertEqual(
            "same-external-context",
            c1_binding.continuation_owner,
        )
        self.assertEqual(
            "degradation",
            c1_binding.scope[slice(*c1_binding.subject_span)],
        )
        self.assertEqual(
            "behavior",
            c1_binding.scope[slice(*c1_binding.head_span)],
        )
        self.assertGreater(
            c1_binding.subject_span[0],
            c1_binding.scope.index("update"),
        )
        self.assertEqual(
            ["for a local deployment changes"],
            [
                c1_binding.scope[slice(*candidate_span)]
                for candidate_span in c1_binding.owner_candidate_spans
            ],
        )
        self.assertEqual(
            [("reliability", "changed")],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE._build_external_concern_effect_records(
                        c1_prompt
                    )
                )
            ],
        )

        c2_prompt = (
            "Analyze an external integration degradation behavior for a "
            "widget changes then update documentation for a widget."
        )
        c2_variant = c2_prompt.replace(
            "documentation for a widget",
            "documentation for a database",
        )
        c2_observations = []
        for label, prompt in {
            "identical-later-text": c2_prompt,
            "changed-later-text": c2_variant,
        }.items():
            with self.subTest(kind="next-action-barrier", label=label):
                binding = (
                    ORACLE._build_external_effect_scope_bindings(prompt)[0]
                )
                self.assertEqual(
                    "ambiguous",
                    binding.continuation_owner,
                )
                self.assertEqual("unknown", binding.semantic_category)
                self.assertEqual(
                    ["for a widget changes"],
                    [
                        binding.scope[slice(*candidate_span)]
                        for candidate_span
                        in binding.owner_candidate_spans
                    ],
                )
                self.assertEqual(
                    "then",
                    binding.scope[slice(*binding.barrier_span)],
                )
                self.assertNotIn(
                    "documentation",
                    binding.predicate_scope,
                )
                c2_observations.append(
                    (
                        binding.continuation_owner,
                        binding.semantic_category,
                        tuple(
                            binding.scope[slice(*candidate_span)]
                            for candidate_span
                            in binding.owner_candidate_spans
                        ),
                        ORACLE._aggregate_external_concern_effect_records(
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        ),
                    )
                )
                self._assert_external_semantic_critical_unknown(
                    prompt=prompt,
                    concern="reliability",
                    label=label,
                )
        self.assertEqual(c2_observations[0], c2_observations[1])

        c3_prompt = (
            "Analyze an external integration degradation behavior for a "
            "local deployment changes then update degradation behavior for "
            "a local deployment changes."
        )
        c3_without_earlier = (
            "Analyze an external integration then update degradation "
            "behavior for a local deployment changes."
        )
        c3_observations = []
        for label, prompt in {
            "repeated": c3_prompt,
            "earlier-deleted": c3_without_earlier,
        }.items():
            with self.subTest(kind="latest-selection", label=label):
                bindings = (
                    ORACLE._build_external_effect_scope_bindings(prompt)
                )
                self.assertEqual(1, len(bindings))
                binding = bindings[0]
                self.assertEqual(
                    "same-external-context",
                    binding.continuation_owner,
                )
                self.assertEqual(
                    ["for a local deployment changes"],
                    [
                        binding.scope[slice(*candidate_span)]
                        for candidate_span
                        in binding.owner_candidate_spans
                    ],
                )
                self.assertEqual(
                    [("reliability", "changed")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )
                c3_observations.append(
                    (
                        binding.continuation_owner,
                        binding.semantic_category,
                        ORACLE._aggregate_external_concern_effect_records(
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        ),
                    )
                )
        self.assertEqual(c3_observations[0], c3_observations[1])

        c4_prompt = (
            "Analyze an external integration timeout and contract change "
            "for a degradation status field."
        )
        c4_whole_parse = ORACLE._parse_normalized_task_request(
            " ".join(c4_prompt.casefold().split())
        )
        c4_scopes = ORACLE._external_session_scopes(
            c4_prompt,
            parsed=c4_whole_parse,
        )
        self.assertEqual(1, len(c4_scopes))
        self.assertEqual(3, len(c4_scopes[0]))
        c4_scope = c4_scopes[0][2]
        self.assertIn("timeout contract change", c4_scope)
        self.assertNotIn("timeout and contract", c4_scope)
        with mock.patch.object(
            ORACLE,
            "_parse_normalized_task_request",
            wraps=ORACLE._parse_normalized_task_request,
        ) as local_parse:
            c4_bindings = (
                ORACLE._build_external_effect_scope_bindings(
                    c4_prompt,
                    parsed=c4_whole_parse,
                )
            )
        self.assertEqual(len(c4_scopes), local_parse.call_count)
        self.assertEqual(
            [scope for _session, _clause, scope in c4_scopes],
            [call.args[0] for call in local_parse.call_args_list],
        )
        self.assertEqual(
            ["consumer", "failure"],
            [binding.concern for binding in c4_bindings],
        )
        for binding in c4_bindings:
            with self.subTest(kind="rewrite-local-span", concern=binding.concern):
                self._assert_external_r5_binding_spans_are_local(binding)
                self.assertEqual(
                    ["change for a degradation status field"],
                    [
                        binding.scope[slice(*candidate_span)]
                        for candidate_span
                        in binding.owner_candidate_spans
                    ],
                )
                self.assertEqual(
                    "metadata-qualifier",
                    binding.semantic_category,
                )
        c4_records = (
            ORACLE._build_external_concern_effect_records(c4_prompt)
        )
        self.assertEqual(
            [("consumer", "changed"), ("failure", "changed")],
            [
                (record.concern, record.effect)
                for record in c4_records
            ],
        )
        self.assertEqual(
            ("changed", "changed", "adjacent-only"),
            ORACLE._aggregate_external_concern_effect_records(c4_records),
        )

        inherited_scope_cases = {
            "consumer-unchanged-failure-changed-comma": (
                "Analyze an external integration without changing downstream "
                "consumer compatibility, change timeout/cancellation "
                "meanings.",
                [("consumer", "unchanged"), ("failure", "changed")],
                "consumer",
                "failure",
            ),
            "consumer-unchanged-failure-changed-and": (
                "Analyze an external integration without changing downstream "
                "consumer compatibility and change timeout and cancellation "
                "meanings.",
                [("consumer", "unchanged"), ("failure", "changed")],
                "consumer",
                "failure",
            ),
            "failure-unchanged-consumer-changed-comma": (
                "Analyze an external integration without changing timeout/"
                "cancellation meanings, change downstream consumer "
                "compatibility.",
                [("failure", "unchanged"), ("consumer", "changed")],
                "failure",
                "consumer",
            ),
            "failure-unchanged-consumer-changed-and": (
                "Analyze an external integration without changing timeout "
                "and cancellation meanings and change downstream consumer "
                "compatibility.",
                [("failure", "unchanged"), ("consumer", "changed")],
                "failure",
                "consumer",
            ),
        }
        for label, (
            prompt,
            expected_effects,
            unchanged_concern,
            changed_concern,
        ) in inherited_scope_cases.items():
            with self.subTest(kind="inherited-scope", label=label):
                bindings = (
                    ORACLE._build_external_effect_scope_bindings(prompt)
                )
                by_concern = {
                    binding.concern: binding for binding in bindings
                }
                unchanged_binding = by_concern[unchanged_concern]
                self.assertEqual(
                    "without changing ",
                    unchanged_binding.scope[
                        slice(*unchanged_binding.concern_prefix_span)
                    ],
                )
                changed_binding = by_concern[changed_concern]
                self.assertEqual("direct", changed_binding.action_relation)
                self.assertEqual("change", changed_binding.action_verb)
                self.assertEqual((0, 6), changed_binding.action_span)
                self.assertEqual(
                    expected_effects,
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )

        shared_prompt = (
            "Analyze an external integration downstream consumer "
            "compatibility and retryable versus terminal outcome meaning "
            "change; degradation and recovery mechanics change."
        )
        shared_bindings = (
            ORACLE._build_external_effect_scope_bindings(shared_prompt)
        )
        shared_contract_bindings = [
            binding
            for binding in shared_bindings
            if binding.concern in {"consumer", "failure"}
        ]
        self.assertEqual(
            ["change", "change"],
            [
                binding.scope[
                    slice(*binding.shared_terminal_effect_span)
                ]
                for binding in shared_contract_bindings
            ],
        )
        self.assertEqual(
            [" ", " meaning change"],
            [
                binding.predicate_scope
                for binding in shared_contract_bindings
            ],
            "same-object evidence must not widen the R5 predicate windows",
        )
        self.assertIsNone(
            next(
                binding
                for binding in shared_bindings
                if binding.concern == "reliability"
            ).shared_terminal_effect_span
        )
        self.assertEqual(
            [
                ("consumer", "changed"),
                ("failure", "changed"),
                ("reliability", "changed"),
            ],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE
                    ._build_external_concern_effect_records(shared_prompt)
                )
            ],
        )

        self.assertEqual(
            (),
            ORACLE._build_external_effect_scope_bindings(
                "Change downstream consumer compatibility."
            ),
        )
        no_share_prompts = {
            "different-actions": (
                "Analyze an external integration downstream consumer "
                "compatibility then update retryable versus terminal "
                "outcome meaning change."
            ),
            "different-scopes": (
                "Analyze an external integration downstream consumer "
                "compatibility; retryable versus terminal outcome meaning "
                "change."
            ),
            "different-sessions": (
                "Analyze an external integration downstream consumer "
                "compatibility. Analyze an external integration retryable "
                "versus terminal outcome meaning change."
            ),
            "multiple-terminal-effects": (
                "Analyze an external integration downstream consumer "
                "compatibility and retryable versus terminal outcome "
                "meaning change changes."
            ),
            "metadata-tail": (
                "Analyze an external integration downstream consumer "
                "contract and failure contract change for a degradation "
                "status field."
            ),
            "wrapper": (
                "Analyze a reference to an external integration downstream "
                "consumer compatibility and retryable versus terminal "
                "outcome meaning change."
            ),
        }
        for label, prompt in no_share_prompts.items():
            with self.subTest(kind="shared-terminal-negative", label=label):
                self.assertTrue(
                    all(
                        binding.shared_terminal_effect_span is None
                        for binding in (
                            ORACLE
                            ._build_external_effect_scope_bindings(prompt)
                        )
                    )
                )

        contradictory_shared_prompt = (
            "Do not change an external integration downstream consumer "
            "compatibility and retryable versus terminal outcome meaning "
            "change."
        )
        self.assertEqual(
            [("consumer", "ambiguous"), ("failure", "ambiguous")],
            [
                (record.concern, record.effect)
                for record in (
                    ORACLE._build_external_concern_effect_records(
                        contradictory_shared_prompt
                    )
                )
            ],
        )

    def test_external_integration_r5_registered_non_parser_terminal_effects(
        self,
    ) -> None:
        expected_effect_action_surfaces = {
            "change": "change",
            "changes": "change",
            "changed": "change",
            "changing": "change",
            "choose": "choose",
            "decide": "decide",
            "define": "define",
            "implement": "implement",
            "model": "model",
            "redesign": "redesign",
            "update": "update",
            "updates": "update",
            "updated": "update",
        }
        effect_action_surfaces = dict(
            ORACLE._EXTERNAL_RELATION_SEMANTICS[
                "effect_action_surfaces"
            ]
        )
        self.assertEqual(
            expected_effect_action_surfaces,
            effect_action_surfaces,
            "the independent oracle must close the registered surface set",
        )

        prompt_template = (
            "Analyze an external integration downstream consumer "
            "compatibility and retryable versus terminal outcome meaning "
            "{}."
        )
        parser_registered_surfaces = {
            surface
            for surface in expected_effect_action_surfaces
            if any(
                lexeme.lexeme == surface
                for lexeme in (
                    ORACLE._parse_normalized_task_request(
                        prompt_template.format(surface).casefold()
                    ).task_actions.lexemes
                )
            )
        }
        self.assertEqual(
            {"change", "implement", "update"},
            parser_registered_surfaces,
        )
        expected_non_parser_surfaces = {
            "changes",
            "changed",
            "changing",
            "choose",
            "decide",
            "define",
            "model",
            "redesign",
            "updates",
            "updated",
        }
        non_parser_surfaces = (
            set(effect_action_surfaces)
            - parser_registered_surfaces
        )
        self.assertEqual(
            expected_non_parser_surfaces,
            non_parser_surfaces,
        )

        for surface in sorted(expected_non_parser_surfaces):
            prompt = prompt_template.format(surface)
            with self.subTest(kind="registered-positive", surface=surface):
                bindings = (
                    ORACLE._build_external_effect_scope_bindings(prompt)
                )
                contract_bindings = [
                    binding
                    for binding in bindings
                    if binding.concern in {"consumer", "failure"}
                ]
                self.assertEqual(
                    ["consumer", "failure"],
                    [binding.concern for binding in contract_bindings],
                )
                shared_spans = [
                    binding.shared_terminal_effect_span
                    for binding in contract_bindings
                ]
                self.assertTrue(
                    all(span is not None for span in shared_spans),
                    f"{surface!r} must bind one shared terminal span",
                )
                self.assertEqual(
                    [surface, surface],
                    [
                        binding.scope[slice(*span)]
                        for binding, span in zip(
                            contract_bindings,
                            shared_spans,
                            strict=True,
                        )
                        if span is not None
                    ],
                )
                self.assertEqual(
                    [("consumer", "changed"), ("failure", "changed")],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(prompt)
                        )
                    ],
                )

        no_share_prompts = {
            "duplicate-terminal": (
                "Analyze an external integration downstream consumer "
                "compatibility and retryable versus terminal outcome "
                "meaning changes changes."
            ),
            "multiple-terminal-surfaces": (
                "Analyze an external integration downstream consumer "
                "compatibility and retryable versus terminal outcome "
                "meaning changed updated."
            ),
            "cross-object": (
                "Analyze an external integration downstream consumer "
                "compatibility and retryable versus terminal outcome "
                "meaning, then change documentation."
            ),
        }
        for label, prompt in no_share_prompts.items():
            with self.subTest(kind="registered-negative", label=label):
                contract_bindings = [
                    binding
                    for binding in (
                        ORACLE
                        ._build_external_effect_scope_bindings(prompt)
                    )
                    if binding.concern in {"consumer", "failure"}
                ]
                self.assertEqual(
                    ["consumer", "failure"],
                    [binding.concern for binding in contract_bindings],
                )
                self.assertTrue(
                    all(
                        binding.shared_terminal_effect_span is None
                        for binding in contract_bindings
                    )
                )

    def test_external_integration_r5_consumer_alias_chain_prefix(
        self,
    ) -> None:
        source = ORACLE_PATH.read_text(encoding="utf-8")
        with self.subTest(contract="alias-ssot"):
            self.assertEqual(
                1,
                source.count("_EXTERNAL_CONSUMER_ALIASES ="),
            )
            self.assertEqual(
                (
                    "downstream",
                    "consumer",
                    "compatibility",
                    "schema",
                ),
                tuple(
                    alias
                    for alias, _pattern
                    in ORACLE._EXTERNAL_CONSUMER_ALIASES
                ),
                "the consumer alias SSOT must declare the contiguous chain",
            )
            cluster_source = inspect.getsource(
                ORACLE._external_concern_cluster_start
            )
            self.assertIn(
                "_EXTERNAL_CONSUMER_ALIASES",
                cluster_source,
            )
            for prohibited_duplicate in (
                '"downstream"',
                '"compatibility"',
                '"schema"',
            ):
                self.assertNotIn(
                    prohibited_duplicate,
                    cluster_source,
                    "cluster membership must derive from the alias SSOT",
                )

        prompt = (
            "Analyze an external integration without changing downstream "
            "consumer compatibility schema, change timeout/cancellation "
            "meanings."
        )
        bindings = ORACLE._build_external_effect_scope_bindings(prompt)
        by_concern = {
            binding.concern: binding for binding in bindings
        }
        consumer_binding = by_concern["consumer"]
        failure_binding = by_concern["failure"]
        with self.subTest(contract="full-contiguous-chain"):
            self.assertIsNotNone(
                consumer_binding.concern_prefix_span
            )
            self.assertEqual(
                "without changing ",
                consumer_binding.scope[
                    slice(*consumer_binding.concern_prefix_span)
                ],
            )
            self.assertIsNone(failure_binding.concern_prefix_span)
            self.assertEqual(
                [("consumer", "unchanged"), ("failure", "changed")],
                [
                    (record.concern, record.effect)
                    for record in (
                        ORACLE
                        ._build_external_concern_effect_records(prompt)
                    )
                ],
            )

        invalid_chains = {
            "out-of-order": (
                "Analyze an external integration without changing consumer "
                "downstream compatibility schema, change timeout/"
                "cancellation meanings."
            ),
            "non-contiguous": (
                "Analyze an external integration without changing "
                "downstream consumer api compatibility schema, change "
                "timeout/cancellation meanings."
            ),
        }
        for label, invalid_prompt in invalid_chains.items():
            with self.subTest(kind="invalid-alias-chain", label=label):
                invalid_bindings = (
                    ORACLE
                    ._build_external_effect_scope_bindings(invalid_prompt)
                )
                invalid_by_concern = {
                    binding.concern: binding
                    for binding in invalid_bindings
                }
                self.assertIsNone(
                    invalid_by_concern[
                        "consumer"
                    ].concern_prefix_span
                )
                self.assertEqual(
                    [
                        ("consumer", "adjacent-only"),
                        ("failure", "changed"),
                    ],
                    [
                        (record.concern, record.effect)
                        for record in (
                            ORACLE
                            ._build_external_concern_effect_records(
                                invalid_prompt
                            )
                        )
                    ],
                )

    def test_external_integration_r5_structure_contract(
        self,
    ) -> None:
        source = ORACLE_PATH.read_text(encoding="utf-8")
        semantics = ORACLE._EXTERNAL_RELATION_SEMANTICS
        self.assertIsInstance(semantics, MappingProxyType)
        self.assertIn("metadata_head_surfaces", semantics)
        self.assertEqual(
            1,
            source.count("_EXTERNAL_RELATION_SEMANTICS ="),
        )
        self.assertEqual(
            1,
            source.count(
                "def _classify_external_relation_semantics("
            ),
        )
        self.assertEqual(
            1,
            source.count("def _external_owner_relation_phrases("),
        )
        self.assertEqual(
            1,
            source.count(
                "def _build_external_effect_scope_bindings("
            ),
        )
        self.assertEqual(
            1,
            source.count("def _resolve_external_binding_effect("),
        )

        builder_source = inspect.getsource(
            ORACLE._build_external_effect_scope_bindings
        )
        helper_source = inspect.getsource(
            ORACLE._external_owner_relation_phrases
        )
        classifier_source = inspect.getsource(
            ORACLE._classify_external_relation_semantics
        )
        combined_source = "\n".join(
            (builder_source, helper_source, classifier_source)
        )
        self.assertEqual(
            1,
            builder_source.count(
                "_parse_normalized_task_request(scope)"
            ),
        )
        self.assertNotIn(".find(", combined_source)
        self.assertNotIn(".index(", combined_source)
        self.assertNotIn("global_delta", combined_source)
        self.assertNotIn("offset_conversion", combined_source)
        for prohibited_token in (
            "widget",
            "appliance",
            "remote",
        ):
            self.assertNotIn(prohibited_token, combined_source)

        binding_fields = tuple(
            ORACLE._ExternalEffectScopeBinding.__dataclass_fields__
        )
        self.assertIn("owner_candidate_spans", binding_fields)
        self.assertIn("effect_window_span", binding_fields)
        self.assertIn("barrier_span", binding_fields)
        self.assertIn("action_span", binding_fields)
        self.assertIn("concern_prefix_span", binding_fields)
        self.assertIn("shared_terminal_effect_span", binding_fields)
        self.assertNotIn("global_external_subject_span", binding_fields)

        self.assertEqual(
            ("normalized", "source"),
            tuple(ORACLE._TaskSpan.__dataclass_fields__),
        )
        self.assertEqual(
            (
                "source_text",
                "normalized_text",
                "actions",
                "objects",
                "lexemes",
                "issues",
                "blocking_terminal_spans",
            ),
            tuple(ORACLE._TaskActionParse.__dataclass_fields__),
        )
        self.assertEqual(
            ("value", "task_actions"),
            tuple(ORACLE._ParsedTaskRequest.__dataclass_fields__),
        )

        cardinality_prompt = (
            "Analyze an external integration downstream consumer "
            "compatibility changes then update downstream consumer "
            "compatibility changes and degradation behavior changes."
        )
        for _session_id, _clause_id, scope in (
            ORACLE._external_session_scopes(cardinality_prompt)
        ):
            concerns = [
                concern
                for concern, *_rest
                in ORACLE._external_concern_selections(scope)
            ]
            self.assertEqual(len(concerns), len(set(concerns)))

    def test_external_integration_shared_head_uses_latest_local_subject(
        self,
    ) -> None:
        builder = getattr(
            ORACLE,
            "_build_external_concern_effect_records",
            None,
        )
        aggregator = getattr(
            ORACLE,
            "_aggregate_external_concern_effect_records",
            None,
        )
        self.assertTrue(callable(builder))
        self.assertTrue(callable(aggregator))
        cases = {
            "latest-recovery": (
                "Analyze an external integration degradation recovery "
                "mechanics change.",
                ("recovery", "mechanics", "changed"),
                "changed",
            ),
            "latest-degradation": (
                "Analyze an external integration recovery degradation "
                "policy changes.",
                ("degradation", "policy", "changed"),
                "changed",
            ),
            "metadata-head": (
                "Analyze an external integration degradation behavior field "
                "changes.",
                None,
                "adjacent-only",
            ),
            "split-action": (
                "Analyze an external integration degradation behavior, "
                "changes.",
                ("degradation", "behavior", "adjacent-only"),
                "adjacent-only",
            ),
            "barrier-latest-subject": (
                "Analyze an external integration degradation, recovery "
                "mechanics changes.",
                ("recovery", "mechanics", "changed"),
                "changed",
            ),
        }
        for label, (
            prompt,
            expected_record,
            expected_effect,
        ) in cases.items():
            with self.subTest(label=label):
                records = builder(prompt)
                reliability_records = [
                    record
                    for record in records
                    if record.concern == "reliability"
                ]
                if expected_record is None:
                    self.assertEqual([], reliability_records)
                else:
                    self.assertEqual(
                        [expected_record],
                        [
                            (
                                record.subject_alias,
                                record.semantic_head,
                                record.effect,
                            )
                            for record in reliability_records
                        ],
                    )
                self.assertEqual(
                    expected_effect,
                    aggregator(records)[2],
                )

        conflict = ORACLE.route_with_trace(
            "Analyze an external integration downstream consumer "
            "compatibility changes; degradation recovery mechanics change.",
            main_execution=_test_main_execution(
                f"{self._testMethodName}:shared-head-conflict"
            ),
        )
        self.assertEqual(
            [
                "external-integration-consumer-impact-analysis",
                "reliability-signal-analysis",
            ],
            [
                candidate["candidate_id"]
                for candidate in conflict[
                    "winner_trace"
                ]["raw_candidates"]
            ],
        )
        self.assertEqual(
            "route-contract-conflict",
            conflict["winner_trace"][
                "selected_candidate"
            ]["candidate_id"],
        )

    def test_external_integration_unchanged_reliability_does_not_compete(
        self,
    ) -> None:
        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )
        reliability_alias = "reliability-signal-analysis"
        cases = {
            "consumer-degradation-unchanged": (
                "Analyze an external integration downstream consumer "
                "compatibility change; degradation mechanics remain "
                "unchanged.",
                [consumer_alias],
                ["consumer-impact-analysis"],
            ),
            "failure-mechanics-unchanged": (
                "Analyze an external integration timeout and cancellation "
                "meaning change; degradation, retry, and fallback mechanics "
                "remain unchanged; downstream consumer compatibility remains "
                "unchanged.",
                [failure_alias],
                ["failure-contract-design"],
            ),
            "pure-degradation-unchanged": (
                "Analyze an external integration degradation mechanics that "
                "remain unchanged; consumer and failure contract semantics "
                "remain unchanged.",
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "pure-degradation-negated": (
                "Analyze an external integration without a degradation "
                "mechanics change; consumer and failure contract semantics "
                "remain unchanged.",
                ["repository-first-default"],
                ["repository-context-map"],
            ),
            "positive-consumer-degradation": (
                "Analyze an external integration downstream consumer "
                "compatibility change; degradation mechanics change.",
                [consumer_alias, reliability_alias],
                ["repository-context-map"],
            ),
            "positive-failure-retry-fallback": (
                "Analyze an external integration timeout and cancellation "
                "meaning change; retry attempts, backoff budget, and fallback "
                "mechanics change; downstream consumer compatibility remains "
                "unchanged.",
                [failure_alias, reliability_alias],
                ["repository-context-map"],
            ),
        }
        for label, (
            prompt,
            expected_raw_ids,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"{self._testMethodName}:{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    expected_raw_ids,
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_layer3,
                    _projected_route(observed)["layer3_skills"],
                )
                if reliability_alias not in expected_raw_ids:
                    self.assertNotIn(
                        reliability_alias,
                        [
                            candidate["candidate_id"]
                            for candidate
                            in trace["excluded_candidates"]
                        ],
                    )

        non_external = ORACLE.route_with_trace(
            "Analyze degradation mechanics that remain unchanged.",
            main_execution=_test_main_execution(
                f"{self._testMethodName}:non-external-legacy"
            ),
        )
        self.assertEqual(
            [reliability_alias],
            [
                candidate["candidate_id"]
                for candidate in non_external[
                    "winner_trace"
                ]["raw_candidates"]
            ],
        )

    def test_external_integration_member_public_trace_contract(
        self,
    ) -> None:
        case_ids = {
            "external-integration-consumer-only",
            "external-integration-failure-only",
            "external-integration-consumer-reliability-conflict",
            "external-integration-failure-reliability-conflict",
            "external-integration-combined-reliability-conflict",
        }
        fixtures = {
            case["id"]: case
            for case in load_yaml_file(CASES_PATH)["cases"]
            if case.get("id") in case_ids
        }
        self.assertEqual(case_ids, set(fixtures))

        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )
        reliability_alias = "reliability-signal-analysis"
        canonical_selector = "external-integration-analysis"
        singleton_expectations = {
            "external-integration-consumer-only": (
                consumer_alias,
                ["consumer-impact-analysis"],
            ),
            "external-integration-failure-only": (
                failure_alias,
                ["failure-contract-design"],
            ),
        }
        conflict_expectations = {
            "external-integration-consumer-reliability-conflict": [
                consumer_alias,
                reliability_alias,
            ],
            "external-integration-failure-reliability-conflict": [
                failure_alias,
                reliability_alias,
            ],
            "external-integration-combined-reliability-conflict": [
                canonical_selector,
                reliability_alias,
            ],
        }

        for case_id, fixture in fixtures.items():
            with self.subTest(case_id=case_id):
                observed = ORACLE.route_with_trace(
                    fixture["prompt"],
                    main_execution=copy.deepcopy(
                        fixture["main_execution"]
                    ),
                )
                self.assertEqual(
                    fixture["expected"],
                    _projected_route(observed),
                )
                trace = observed["winner_trace"]
                raw = trace["raw_candidates"]
                raw_ids = [
                    candidate["candidate_id"] for candidate in raw
                ]
                selected = trace["selected_candidate"]
                excluded = trace["excluded_candidates"]

                if case_id in singleton_expectations:
                    alias_id, member_subset = (
                        singleton_expectations[case_id]
                    )
                    self.assertEqual([alias_id], raw_ids)
                    self.assertEqual(alias_id, raw[0]["rule_id"])
                    self.assertNotIn("source_candidate_ids", raw[0])
                    self.assertEqual(
                        member_subset,
                        raw[0]["layer3_skills"],
                    )
                    self.assertEqual(
                        [alias_id],
                        selected["source_candidate_ids"],
                    )
                    self.assertEqual(
                        "highest-semantic-precedence",
                        selected["reason"],
                    )
                    self.assertEqual([], excluded)
                    external_candidate = raw[0]
                else:
                    expected_source_ids = conflict_expectations[case_id]
                    self.assertEqual(expected_source_ids, raw_ids)
                    self.assertEqual(
                        "route-contract-conflict",
                        selected["candidate_id"],
                    )
                    self.assertEqual(
                        expected_source_ids,
                        selected["source_candidate_ids"],
                    )
                    self.assertEqual(
                        "equal-precedence-route-contract-conflict",
                        selected["reason"],
                    )
                    self.assertEqual(
                        expected_source_ids,
                        [
                            candidate["candidate_id"]
                            for candidate in excluded
                        ],
                    )
                    self.assertEqual(
                        ["ambiguous-route-contract"] * 2,
                        [
                            candidate["reason"]
                            for candidate in excluded
                        ],
                    )
                    self.assertTrue(
                        all(
                            "source_candidate_ids" not in candidate
                            for candidate in raw
                        )
                    )
                    self.assertTrue(
                        all(
                            "source_candidate_ids" not in candidate
                            for candidate in excluded
                        )
                    )
                    external_candidate = raw[0]

                self.assertEqual(
                    external_candidate["candidate_id"],
                    external_candidate["rule_id"],
                )
                self.assertEqual(
                    [canonical_selector],
                    [
                        row["candidate_id"]
                        for row in external_candidate[
                            "source_foundation_candidates"
                        ]
                    ],
                )
                self.assertEqual(
                    [
                        "consumer-impact-analysis",
                        "failure-contract-design",
                    ],
                    external_candidate[
                        "source_foundation_candidates"
                    ][0]["foundations"],
                )
                self.assertEqual(
                    "foundation-selector:external-integration-analysis",
                    external_candidate["evidence"][-1],
                )
                self.assertTrue(
                    set(selected["source_candidate_ids"]).issubset(
                        set(raw_ids)
                    )
                )

    def test_external_integration_member_repair_preserves_package_route_contract(
        self,
    ) -> None:
        package_case = next(
            case
            for case in load_yaml_file(CASES_PATH)["cases"]
            if case.get("id") == "structure-package-supply-chain-not-reuse"
        )
        package_route = _projected_route(
            ORACLE.route_with_trace(
                package_case["prompt"],
                main_execution=copy.deepcopy(package_case["main_execution"]),
            )
        )
        self.assertEqual("engineering-change-analysis", package_route["primary_skill"])
        self.assertEqual(
            ["package-dependency-management"],
            package_route["layer3_skills"],
        )
        self.assertNotIn(
            "dependency-vulnerability-scanning",
            package_route["layer3_skills"],
        )
        self.assertNotEqual(
            [
                "package-dependency-management",
                "dependency-vulnerability-scanning",
            ],
            package_route["layer3_skills"],
        )

    def test_converted_inventory_has_exact_delta_and_retained_controls(
        self,
    ) -> None:
        direct_rule_ids = _direct_rule_ids()
        candidate_rule_ids = _candidate_rule_ids()
        oracle_literals = {
            node.value
            for node in ast.walk(
                ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
            )
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }
        obsolete_test_strategy_literals = {
            "explicit test strategy decision",
            "explicit-test-strategy-analysis",
            "explicit-test-strategy-decision",
        }
        self.assertEqual(
            set(),
            obsolete_test_strategy_literals & oracle_literals,
            "registry-enabled Foundation routing must remove every static "
            "test-strategy route literal from the oracle",
        )
        self.assertEqual(EXPECTED_DIRECT_RETURN_COUNT, len(direct_rule_ids))
        self.assertEqual(len(candidate_rule_ids), len(set(candidate_rule_ids)))
        self.assertTrue(
            SPECIALIST_SIGNAL_RULE_IDS.issubset(candidate_rule_ids)
        )
        self.assertTrue(
            SPLIT_GUARD_RULE_IDS.issubset(candidate_rule_ids)
        )
        self.assertNotIn("explicit-test-strategy-analysis", candidate_rule_ids)
        self.assertIn("owner-internal-structure-analysis", candidate_rule_ids)
        self.assertNotIn("architecture-boundary-fallback", candidate_rule_ids)
        self.assertNotIn(
            "legacy-downstream",
            ORACLE_PATH.read_text(encoding="utf-8"),
        )

    def test_foundation_runtime_matcher_clause_polarity_and_connector_matrix(
        self,
    ) -> None:
        self.assertTrue(
            callable(getattr(ORACLE, FOUNDATION_MATCHER_HELPER, None)),
            f"{FOUNDATION_MATCHER_HELPER} is missing or not callable",
        )
        selection = (
            "Select test levels, observable failure oracles, and omissions."
        )
        self.assertTrue(
            _foundation_matcher_matches(
                "Analyze several material failure mechanisms. "
                f"{selection} No single command has been fixed."
            ),
            "different complete predicates may match different bounded clauses",
        )

        for separator in FOUNDATION_MATCHER_CLAUSE_SEPARATORS:
            with self.subTest(separator=separator):
                self.assertFalse(
                    _foundation_matcher_matches(
                        "Analyze several material failures"
                        f"{separator}mechanisms are still open. "
                        f"{selection} No single command has been fixed."
                    ),
                    "term groups from one predicate must not splice across "
                    f"the bounded-clause separator {separator!r}",
                )
        for connector in FOUNDATION_MATCHER_NON_SEPARATORS:
            with self.subTest(connector=connector):
                self.assertTrue(
                    _foundation_matcher_matches(
                        "Analyze several material failures"
                        f"{connector}mechanisms. {selection} "
                        "No single command has been fixed."
                    ),
                    "comma, conjunction, disjunction, and colon are not "
                    f"bounded-clause separators: {connector!r}",
                )

        absent_positive_forms = (
            "No single command has been fixed.",
            "Proceed without a single command.",
            "A single command unfixed.",
            "An unfixed single command remains undecided.",
            "A single command is not fixed.",
            "A single command has not been fixed.",
        )
        absent_negative_forms = (
            "A single command missing.",
            "A single command fixed.",
            "A single command already fixed.",
        )
        positive_prefix = (
            "Analyze several material failure mechanisms. "
            f"{selection} "
        )
        runtime_matcher = _test_strategy_runtime_matcher()
        absent_predicate = next(
            predicate
            for predicate in runtime_matcher["predicates"]
            if predicate["polarity"] == "absent"
        )
        matcher_subject_terms = {
            term
            for group in absent_predicate["term_groups"]
            for term in group
        }
        subject_missing_form = "The proof portfolio remains open."
        self.assertFalse(
            any(
                term in subject_missing_form.casefold()
                for term in matcher_subject_terms
            ),
            "the subject-missing control must contain no matcher subject term",
        )
        self.assertFalse(
            _foundation_matcher_matches(
                positive_prefix + subject_missing_form
            ),
            "a genuinely missing absent-predicate subject must not satisfy "
            "absence",
        )
        for absent_form in absent_positive_forms:
            with self.subTest(absent_form=absent_form):
                self.assertTrue(
                    _foundation_matcher_matches(
                        positive_prefix + absent_form
                    ),
                    f"{absent_form!r} must satisfy the absent predicate",
                )
        for present_form in absent_negative_forms:
            with self.subTest(present_form=present_form):
                self.assertFalse(
                    _foundation_matcher_matches(
                        positive_prefix + present_form
                    ),
                    f"{present_form!r} must violate the absent predicate",
                )

        self.assertFalse(
            _foundation_matcher_matches(
                "Analyze several material failure mechanisms. "
                "Do not select test levels, observable failure oracles, or "
                "omissions. No single command has been fixed."
            ),
            "a negated selection cannot satisfy a selection action",
        )
        for action in ("implement", "prepare"):
            with self.subTest(non_negated_action=action):
                self.assertFalse(
                    _foundation_matcher_matches(
                        positive_prefix
                        + "No single command has been fixed. "
                        + f"{action} regression tests."
                    ),
                    "a non-negated mutation or preparation action must "
                    "invalidate an analysis-only matcher",
                )

    def test_foundation_runtime_matcher_closed_action_vocabulary_and_negators(
        self,
    ) -> None:
        self.assertTrue(
            callable(getattr(ORACLE, FOUNDATION_MATCHER_HELPER, None)),
            f"{FOUNDATION_MATCHER_HELPER} is missing or not callable",
        )
        proof_clause = "several material failure mechanisms"
        selection_terms = (
            "test levels, observable failure oracles, and omissions"
        )
        fixed_absent = "No single command has been fixed."

        for verb in FOUNDATION_MATCHER_ANALYSIS_VERBS:
            with self.subTest(analysis_verb=verb):
                self.assertTrue(
                    _foundation_matcher_matches(
                        f"{verb} {proof_clause}. Select {selection_terms}. "
                        f"{fixed_absent}"
                    )
                )
        self.assertFalse(
            _foundation_matcher_matches(
                f"Review {proof_clause}. Select {selection_terms}. "
                f"{fixed_absent}"
            ),
            "analysis vocabulary is closed to analyze/analyse",
        )

        for verb in FOUNDATION_MATCHER_SELECTION_VERBS:
            with self.subTest(selection_verb=verb):
                self.assertTrue(
                    _foundation_matcher_matches(
                        f"Analyze {proof_clause}. {verb} {selection_terms}. "
                        f"{fixed_absent}"
                    )
                )
        self.assertFalse(
            _foundation_matcher_matches(
                f"Analyze {proof_clause}. Decide {selection_terms}. "
                f"{fixed_absent}"
            ),
            "selection vocabulary is closed to select/choose inflections",
        )
        self.assertFalse(
            _foundation_matcher_matches(
                f"Analyze {proof_clause}. Chose {selection_terms}. "
                f"{fixed_absent}"
            ),
            "the undeclared near-miss 'chose' cannot satisfy selection",
        )

        accepted_prefix = (
            f"Analyze {proof_clause}. Select {selection_terms}. "
            f"{fixed_absent} "
        )
        for verb in FOUNDATION_MATCHER_MUTATION_VERBS:
            with self.subTest(mutation_verb=verb):
                self.assertFalse(
                    _foundation_matcher_matches(
                        accepted_prefix + f"{verb} regression tests."
                    ),
                    f"non-negated {verb!r} must violate analysis-only action",
                )
        self.assertTrue(
            _foundation_matcher_matches(
                accepted_prefix + "Implemented regression tests are context."
            ),
            "mutation vocabulary is closed to the exact declared verbs",
        )

        for negator in FOUNDATION_MATCHER_NEGATORS:
            with self.subTest(negator=negator, action="mutation"):
                self.assertTrue(
                    _foundation_matcher_matches(
                        accepted_prefix
                        + f"{negator} implement regression tests."
                    ),
                    f"{negator!r} must negate the adjacent mutation action",
                )
            with self.subTest(negator=negator, action="selection"):
                self.assertFalse(
                    _foundation_matcher_matches(
                        f"Analyze {proof_clause}. {negator} select "
                        f"{selection_terms}. {fixed_absent}"
                    ),
                    f"{negator!r} must negate the adjacent selection action",
                )
        self.assertFalse(
            _foundation_matcher_matches(
                accepted_prefix + "Hardly implement regression tests."
            ),
            "near-negators outside the closed vocabulary cannot negate mutation",
        )

    def test_two_enabled_foundation_matchers_call_authority_once_and_conflict(
        self,
    ) -> None:
        canonical = load_yaml_file(FOUNDATION_REGISTRY)
        canonical_authority = (
            VALIDATION.foundation_runtime_matcher_authority(
                canonical,
                context="two-enabled-foundation-runtime-matchers",
            )
        )
        self.assertEqual(
            [
                "business-rule-extraction",
                "state-machine-modeling",
                "test-strategy",
            ],
            [row["name"] for row in canonical_authority],
            "the runtime matcher inventory must remain the closed canonical "
            "three-row authority",
        )
        expected_authority = [
            copy.deepcopy(canonical_authority[index])
            for index in (0, 2)
        ]
        expected_ids = [
            row["activation_id"]
            for row in expected_authority
        ]
        expected_atoms = {
            row["activation_id"]: row["semantic_atoms"]
            for row in expected_authority
        }
        real_authority = ORACLE.foundation_runtime_matcher_authority
        real_selector = ORACLE._select_route_cohort_candidate

        def select_canonical_authority_subset(*args, **kwargs):
            projections = real_authority(*args, **kwargs)
            self.assertEqual(
                [row["name"] for row in canonical_authority],
                [row["name"] for row in projections],
                "the controlled subset must still invoke and validate the "
                "complete canonical authority",
            )
            return [
                copy.deepcopy(projections[index])
                for index in (0, 2)
            ]

        with (
            mock.patch.object(
                ORACLE,
                "foundation_runtime_matcher_authority",
                side_effect=select_canonical_authority_subset,
                create=True,
            ) as authority,
            mock.patch.object(
                ORACLE,
                "_foundation_runtime_matcher_matches",
                return_value=True,
            ),
            mock.patch.object(
                ORACLE,
                "_select_route_cohort_candidate",
                wraps=real_selector,
            ) as selector,
        ):
            observed = ORACLE.route_with_trace(
                "Analyze several material failure mechanisms. Select test "
                "levels, observable failure oracles, and omissions. No single "
                "command has been fixed.",
                main_execution=_test_main_execution(
                    "foundation-runtime-matcher-two-enabled"
                ),
            )

        self.assertEqual(
            1,
            authority.call_count,
            "the public Foundation runtime matcher authority must be called "
            "exactly once by each route",
        )
        self.assertEqual(
            1,
            selector.call_count,
            "the real cohort selector must be called exactly once",
        )
        selector_candidates, *_selector_options = selector.call_args.args
        matcher_candidates = [
            candidate
            for candidate in selector_candidates
            if candidate.get("candidate_id") in expected_ids
        ]
        self.assertEqual(
            expected_ids,
            [candidate["candidate_id"] for candidate in matcher_candidates],
            "all matching authority rows must reach the selector in registry "
            "order",
        )
        self.assertEqual(
            [
                {
                    "candidate_id": candidate["candidate_id"],
                    "stage": "foundation-activation",
                    "precedence_class": "foundation-activation",
                    "semantic_atoms": expected_atoms[
                        candidate["candidate_id"]
                    ],
                }
                for candidate in matcher_candidates
            ],
            [
                {
                    "candidate_id": candidate["candidate_id"],
                    "stage": candidate.get("stage"),
                    "precedence_class": candidate.get("precedence_class"),
                    "semantic_atoms": candidate.get("semantic_atoms"),
                }
                for candidate in matcher_candidates
            ],
            "registry-driven candidates must use target-neutral activation "
            "metadata and retain their own semantic atoms",
        )
        winner = observed["winner_trace"]
        raw_matcher_candidates = [
            candidate
            for candidate in winner["raw_candidates"]
            if candidate.get("candidate_id") in expected_ids
        ]
        excluded_matcher_candidates = [
            candidate
            for candidate in winner["excluded_candidates"]
            if candidate.get("candidate_id") in expected_ids
        ]
        for collection_name, candidates in (
            ("raw", raw_matcher_candidates),
            ("excluded", excluded_matcher_candidates),
        ):
            self.assertEqual(
                set(expected_ids),
                {candidate["candidate_id"] for candidate in candidates},
                f"{collection_name} candidates must retain both authority rows",
            )
            for candidate in candidates:
                candidate_id = candidate["candidate_id"]
                self.assertEqual(
                    expected_atoms[candidate_id],
                    candidate.get("semantic_atoms"),
                    f"{collection_name} {candidate_id} lost semantic atoms",
                )
        for candidate_id in expected_ids:
            raw_candidate = next(
                candidate
                for candidate in raw_matcher_candidates
                if candidate["candidate_id"] == candidate_id
            )
            excluded_candidate = next(
                candidate
                for candidate in excluded_matcher_candidates
                if candidate["candidate_id"] == candidate_id
            )
            self.assertIsNot(
                raw_candidate["semantic_atoms"],
                excluded_candidate["semantic_atoms"],
                f"{candidate_id} raw/excluded semantic atoms must not alias",
            )
        first_raw_candidate, second_raw_candidate = raw_matcher_candidates
        self.assertIsNot(
            first_raw_candidate["semantic_atoms"],
            second_raw_candidate["semantic_atoms"],
            "different authority rows must own independent semantic atoms",
        )

        selected = winner["selected_candidate"]
        self.assertNotIn(
            "semantic_atoms",
            selected,
            "the derived conflict must not invent semantic atoms",
        )
        self.assertNotIn(
            "semantic_atoms",
            winner,
            "the projected winner must not inherit source semantic atoms",
        )
        self.assertEqual(
            {
                "candidate_id": "route-contract-conflict",
                "reason": "equal-precedence-route-contract-conflict",
                "source_candidate_ids": sorted(expected_ids),
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                "candidate_id": selected["candidate_id"],
                "reason": selected["reason"],
                "source_candidate_ids": selected["source_candidate_ids"],
                "path": selected["path"],
                "profile": selected["profile"],
                "primary_skill": selected["primary_skill"],
                "layer3_skills": selected["layer3_skills"],
                "review_skill": selected["review_skill"],
            },
            "different matching route contracts must fail closed through the "
            "real selector",
        )
        route_decision = observed["route_decision"]
        route_result = route_decision["route_result"]
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
                "route_once": True,
                "trace_route_once": "proven",
            },
            {
                "path": route_decision["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
                "route_once": route_decision["route_once"],
                "trace_route_once": winner["route_once"],
            },
            "the conflict must produce the final fail-closed route-once "
            "envelope",
        )
        domain_names = {
            row["name"]
            for row in load_yaml_file(DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual(
            {
                "raw_domain_intersection": set(),
                "excluded_domain_intersection": set(),
                "final_domain_intersection": set(),
            },
            {
                "raw_domain_intersection": (
                    _string_values(raw_matcher_candidates) & domain_names
                ),
                "excluded_domain_intersection": (
                    _string_values(excluded_matcher_candidates) & domain_names
                ),
                "final_domain_intersection": (
                    set(route_result["layer3_skills"]) & domain_names
                ),
            },
            "Foundation matcher conflict handling must remain Domain-empty",
        )

    def test_authoritative_t2b_routes_match_expected_contracts(self) -> None:
        cases = _t2b_cases()
        expected_ids = (
            CRITICAL_CASE_IDS
            | PREPARATION_CASE_IDS
            | TIE_CASE_IDS
            | CONTROL_CASE_IDS
        )
        self.assertEqual(expected_ids, set(cases))
        for case_id, case in cases.items():
            with self.subTest(case_id=case_id):
                observed = _observed(case)
                actual_route = _projected_route(observed)
                if case_id != "t2b-preparation-backend-repair":
                    self.assertEqual(case["expected"], actual_route)
                    continue

                winner = observed["winner_trace"]
                decision = observed["route_decision"]
                raw_owner_ids = [
                    candidate["candidate_id"]
                    for candidate in winner["raw_candidates"]
                    if candidate.get("candidate_type")
                    == "automatic-implementation-owner"
                ]
                domain_names = {
                    row["name"]
                    for row in load_yaml_file(DOMAIN_REGISTRY)[
                        "domain_skills"
                    ]
                }
                public_domains = [
                    row["skill"]
                    for row in ORACLE.classify_domain_modifiers(
                        str(case["prompt"])
                    )
                    if row["eligible"] and row["skill"] in domain_names
                ]
                mismatches: list[str] = []
                expected_owner_ids = [
                    "implementation-owner:backend-change-builder"
                ]
                if raw_owner_ids != expected_owner_ids:
                    mismatches.append(
                        "mismatch=raw-automatic-owner; "
                        f"expected={expected_owner_ids!r}; "
                        f"actual={raw_owner_ids!r}"
                    )
                selected_id = winner["selected_candidate"]["candidate_id"]
                if selected_id != "implementation-preparation":
                    mismatches.append(
                        "mismatch=selected-candidate; "
                        "expected='implementation-preparation'; "
                        f"actual={selected_id!r}"
                    )
                if public_domains != []:
                    mismatches.append(
                        "mismatch=public-domain-classifier; "
                        f"expected=[]; actual={public_domains!r}"
                    )
                if decision["route_once"] is not True:
                    mismatches.append(
                        "mismatch=route-once; expected=True; "
                        f"actual={decision['route_once']!r}"
                    )
                if winner["route_once"] != "proven":
                    mismatches.append(
                        "mismatch=trace-route-once; expected='proven'; "
                        f"actual={winner['route_once']!r}"
                    )
                if winner["candidate_coverage"] != "full":
                    mismatches.append(
                        "mismatch=candidate-coverage; expected='full'; "
                        f"actual={winner['candidate_coverage']!r}"
                    )
                if actual_route != case["expected"]:
                    mismatches.append(
                        "mismatch=route-envelope; "
                        f"expected={case['expected']!r}; "
                        f"actual={actual_route!r}"
                    )
                if mismatches:
                    self.fail("\n".join(mismatches))

    def test_converted_candidate_trace_is_complete(self) -> None:
        cases = _t2b_cases()
        for case_id in sorted(
            CRITICAL_CASE_IDS | PREPARATION_CASE_IDS | TIE_CASE_IDS
        ):
            with self.subTest(case_id=case_id):
                case = cases[case_id]
                trace = _observed(case)["winner_trace"]
                for field in (
                    "raw_candidates",
                    "selected_candidate",
                    "excluded_candidates",
                ):
                    self.assertIn(field, trace)
                raw_ids = [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                ]
                cohort_ids = [
                    candidate_id
                    for candidate_id in raw_ids
                    if candidate_id
                    in {
                        "critical-unknown",
                        "implementation-preparation",
                        "review-security-risk",
                    }
                ]
                selected_id = trace["selected_candidate"]["candidate_id"]
                if case_id in TIE_CASE_IDS:
                    self.assertEqual(
                        ["critical-unknown", "implementation-preparation"],
                        cohort_ids,
                    )
                    self.assertEqual("critical-unknown", selected_id)
                elif case_id in CRITICAL_CASE_IDS:
                    self.assertEqual(["critical-unknown"], cohort_ids)
                    self.assertEqual("critical-unknown", selected_id)
                else:
                    expected_ids = ["implementation-preparation"]
                    if case_id == "t2b-preparation-tenant-authorization":
                        expected_ids.append("review-security-risk")
                    self.assertEqual(expected_ids, cohort_ids)
                    self.assertEqual(
                        "implementation-preparation",
                        selected_id,
                    )
                self.assertEqual(
                    sorted(
                        item["precedence"]
                        for item in trace["raw_candidates"]
                    ),
                    [
                        item["precedence"]
                        for item in trace["raw_candidates"]
                    ],
                )
                self.assertTrue(
                    all(
                        item["candidate_id"] != selected_id
                        for item in trace["excluded_candidates"]
                    )
                )
                if selected_id == "critical-unknown":
                    decision = _observed(case)["route_decision"]
                    self.assertEqual(
                        {"producer", "task_id"},
                        set(case["main_execution"]),
                    )
                    self.assertIsNone(
                        decision["main_execution_provenance"]
                    )
                    self.assertIsNone(
                        decision["route_result"]["execution_level"]
                    )
                    self.assertIsNone(
                        decision["route_result"]["level_basis"]
                    )
                else:
                    handoff = trace["deferred_handoff"]
                    self.assertEqual("unresolved", handoff["status"])
                    expected_deferred = {
                        "t2b-preparation-platform": [
                            "infrastructure-as-code-safety"
                        ],
                    }.get(case_id, [])
                    self.assertEqual(
                        expected_deferred,
                        handoff["deferred_layer3"],
                    )

    def test_control_routes_do_not_collect_converted_candidates(self) -> None:
        cases = _t2b_cases()
        for case_id in sorted(CONTROL_CASE_IDS):
            with self.subTest(case_id=case_id):
                trace = _observed(cases[case_id])["winner_trace"]
                raw = trace["raw_candidates"]
                owner_candidates = [
                    item
                    for item in raw
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ]
                self.assertFalse(
                    any(
                        item["candidate_id"]
                        in {
                            "critical-unknown",
                            "implementation-preparation",
                        }
                        for item in raw
                    )
                )
                if owner_candidates:
                    self.assertEqual(1, len(owner_candidates))
                    self.assertEqual(
                        "automatic-implementation-owner",
                        trace["selected_candidate"]["candidate_type"],
                    )
                    self.assertFalse(
                        any(
                            item["candidate_type"] == "fallback-route"
                            for item in raw
                        )
                    )
                else:
                    self.assertEqual(1, len(raw))
                    if raw[0]["candidate_type"] == "fallback-route":
                        self.assertEqual(
                            ["no-eligible-specific-candidate"],
                            trace["selected_candidate"]["evidence"],
                        )
                    else:
                        self.assertEqual(
                            "explicit-route",
                            trace["selected_candidate"]["candidate_type"],
                        )
                    self.assertEqual([], trace["excluded_candidates"])

    def test_split_rules_retain_local_specialist_ambiguity(self) -> None:
        probes = {
            "owner-blast-radius-analysis": (
                "Find the owner and blast radius of this cross-call behavior."
            ),
            "review-ambiguous-structure-repository-first": (
                "Review the actual diff where whether a new wrapper is needed "
                "is unknown."
            ),
            "repository-tooling-ambiguous": (
                "Implement a repository-owned generator with provider variants "
                "whose design pattern is unknown."
            ),
            "backend-effects-ambiguous": (
                "Implement backend provider variants whose design pattern is unknown."
            ),
        }
        for expected_rule_id, prompt in probes.items():
            with self.subTest(rule_id=expected_rule_id):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t2g-split-{expected_rule_id}"
                    ),
                )
                self.assertEqual(
                    expected_rule_id,
                    observed["winner_trace"]["rule_id"],
                )

    def test_owner_internal_structure_analysis_is_typed_and_not_critical(
        self,
    ) -> None:
        prompts = (
            (
                "The accepted owner is PaymentsService. Analyze because owner-internal "
                "implementation structure reuse or deliberate separation remains unresolved."
            ),
            (
                "Analyze because owner-internal implementation structure reuse or deliberate "
                "separation remains unresolved. The accepted owner is PaymentsService."
            ),
            (
                "The established owner is PaymentsService. Analyze the unresolved owner-private "
                "implementation structure choice between reusing the existing helper and "
                "retaining a deliberately separate implementation."
            ),
            (
                "For the known owner BillingService, analyze an undecided owner-internal "
                "implementation structure tradeoff: keep an intentionally separate private "
                "implementation or reuse the compatible serializer."
            ),
            (
                "Analyze the owner-private implementation structure alternatives: retain a "
                "deliberately separate copy or reuse the current validator. That structure "
                "decision remains unresolved. The owner is accepted."
            ),
            (
                "The owner is known. The owner-internal implementation structure decision is "
                "unresolved: reuse the current mapper or keep a deliberately separate "
                "implementation. Analyze it."
            ),
        )
        for index, prompt in enumerate(prompts):
            with self.subTest(index=index):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-structure-owner-internal-{index}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    "owner-internal-structure-analysis",
                    trace["selected_candidate"]["candidate_id"],
                )
                raw_ids = [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                ]
                self.assertIn("owner-internal-structure-analysis", raw_ids)
                self.assertNotIn("critical-unknown", raw_ids)
                self.assertEqual(
                    {
                        "analysis-only-action",
                        "explicit-known-owner",
                        "owner-internal-implementation-structure",
                        "reuse-and-deliberate-separation-alternatives",
                        "unresolved-structure-decision",
                        "foundation-selector:"
                        "owner-internal-structure-analysis",
                    },
                    set(trace["selected_candidate"]["evidence"]),
                )
                self.assertEqual(
                    {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "architecture-impact-reviewer",
                        "layer3_skills": ["implementation-structure-design"],
                        "review_skill": "architecture-impact-reviewer",
                    },
                    _projected_route(observed),
                )

        fixed = ORACLE.route_with_trace(
            "The accepted owner is PaymentsService. Analyze owner-internal "
            "implementation structure; reuse and deliberate separation are "
            "already fixed.",
            main_execution=_test_main_execution(
                "t3-structure-owner-internal-fixed"
            ),
        )
        fixed_trace = fixed["winner_trace"]
        self.assertEqual(
            "critical-unknown",
            fixed_trace["selected_candidate"]["candidate_id"],
        )
        self.assertFalse(
            any(
                item["candidate_id"] == "owner-internal-structure-analysis"
                for item in fixed_trace["raw_candidates"]
            )
        )

    def test_owner_internal_structure_analysis_requires_complete_task_local_evidence(
        self,
    ) -> None:
        controls = {
            "unknown-owner": (
                "Analyze the unresolved owner-private implementation structure tradeoff between "
                "reuse and a deliberately separate implementation; the owner is unknown.",
                "critical-unknown",
            ),
            "fixed-decision": (
                "The accepted owner is PaymentsService. Analyze the owner-private implementation "
                "structure tradeoff between reuse and a separate implementation; the decision "
                "is resolved and placement is fixed.",
                "critical-unknown",
            ),
            "reuse-only": (
                "The accepted owner is PaymentsService. Analyze an unresolved owner-private "
                "implementation structure decision about reusing the existing helper.",
                "critical-unknown",
            ),
            "separate-only": (
                "The accepted owner is PaymentsService. Analyze an unresolved owner-private "
                "implementation structure decision about retaining a deliberately separate "
                "implementation.",
                "critical-unknown",
            ),
            "cross-module-public": (
                "The accepted owner is PaymentsService. Analyze a cross-module public export "
                "change and an unresolved owner-private implementation structure tradeoff "
                "between reuse and a deliberately separate implementation.",
                "module-boundary-analysis",
            ),
            "backend-implementation": (
                "Implement an accepted backend service change using the fixed owner-private "
                "implementation structure decision: reuse the current helper rather than keep "
                "a deliberately separate implementation.",
                "implementation-owner:backend-change-builder",
            ),
            "repository-implementation": (
                "Implement an accepted repository-owned generator source change. The editable "
                "template, derived artifact, committed policy, and freshness check are known; "
                "apply the fixed owner-private implementation structure decision by keeping a "
                "deliberately separate helper instead of reusing the current helper.",
                "implementation-owner:repository-tooling-change-builder",
            ),
            "actual-diff-review": (
                "Review the actual diff where a duplicate owner-private helper was consolidated "
                "and a private class moved inside the same module with behavior preserved.",
                "review-generic",
            ),
            "scattered-keywords": (
                "The accepted owner is PaymentsService. Analyze documentation mentioning "
                "owner-private implementation structure. Reuse terminology is resolved in the "
                "guide; a separate editorial question remains unresolved.",
                "repository-first-default",
            ),
        }
        for label, (prompt, expected_candidate) in controls.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-owner-internal-negative-{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    expected_candidate,
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertFalse(
                    any(
                        item["candidate_id"]
                        == "owner-internal-structure-analysis"
                        for item in trace["raw_candidates"]
                    )
                )

    def test_owner_internal_structure_analysis_preserves_independent_critical_evidence(
        self,
    ) -> None:
        internal = (
            "The established owner is PaymentsService. Analyze the unresolved "
            "owner-private implementation structure choice between reusing the "
            "existing helper and retaining a deliberately separate implementation."
        )
        combined = {
            "public-boundary-after": (
                f"{internal} The cross-module public export change remains unresolved.",
                [
                    "critical-owner-unknown",
                    "critical-source:module-boundary",
                ],
            ),
            "dependency-boundary-before": (
                "The dependency edge change remains undecided. "
                f"{internal}",
                [
                    "critical-owner-unknown",
                    "critical-source:module-boundary",
                ],
            ),
            "placement-after": (
                f"{internal} Destination placement is unknown.",
                ["critical-placement-unknown"],
            ),
            "verification-after": (
                f"{internal} Verification is unknown.",
                ["critical-verification-unknown"],
            ),
        }
        owner_evidence = {
            "analysis-only-action",
            "explicit-known-owner",
            "owner-internal-implementation-structure",
            "reuse-and-deliberate-separation-alternatives",
            "unresolved-structure-decision",
            "foundation-selector:owner-internal-structure-analysis",
        }
        expected_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for label, (prompt, expected_critical_evidence) in combined.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-owner-internal-critical-{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [
                        "critical-unknown",
                        "owner-internal-structure-analysis",
                    ],
                    [
                        item["candidate_id"]
                        for item in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    "critical-unknown",
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertEqual(
                    expected_critical_evidence,
                    trace["selected_candidate"]["evidence"],
                )
                self.assertEqual(
                    ["owner-internal-structure-analysis"],
                    [
                        item["candidate_id"]
                        for item in trace["excluded_candidates"]
                    ],
                )
                self.assertEqual(
                    owner_evidence,
                    set(trace["excluded_candidates"][0]["evidence"]),
                )
                self.assertEqual(
                    expected_route,
                    _projected_route(observed),
                )

        standalone = ORACLE.route_with_trace(
            "Analyze a cross-module public export change that remains unresolved.",
            main_execution=_test_main_execution(
                "t3-owner-internal-critical-standalone-boundary"
            ),
        )
        standalone_trace = standalone["winner_trace"]
        self.assertEqual(
            ["critical-unknown"],
            [
                item["candidate_id"]
                for item in standalone_trace["raw_candidates"]
            ],
        )
        self.assertEqual(
            [
                "critical-owner-unknown",
                "critical-source:module-boundary",
            ],
            standalone_trace["selected_candidate"]["evidence"],
        )
        self.assertEqual([], standalone_trace["excluded_candidates"])

    def test_negated_implementation_does_not_create_owner_candidates(
        self,
    ) -> None:
        cases = {
            "node-business-rule": (
                "Analyze a Node.js backend business rule with no runtime or "
                "core-library behavior change; do not implement it.",
                "repository-first-default",
                "engineering-change-analysis",
                ["repository-context-map"],
            ),
            "filesystem-safety": (
                "Analyze a backend utility that atomically replaces a local file "
                "while checking path containment and symlink behavior; do not "
                "implement it.",
                "repository-first-default",
                "engineering-change-analysis",
                ["repository-context-map"],
            ),
            "design-pattern": (
                "Analyze whether backend provider variants have a current "
                "substitution contract, lifecycle, and extension force that "
                "justify a design pattern; do not implement it.",
                "design-pattern-analysis",
                "architecture-impact-reviewer",
                ["design-pattern-selection"],
            ),
            "minimality": (
                "Analyze whether a new pass-through wrapper is needed for accepted "
                "behavior; it has no current variation, lifecycle, protocol, or "
                "extension force; do not implement it.",
                "minimality-analysis",
                "engineering-change-analysis",
                ["minimal-correct-implementation"],
            ),
        }
        for label, (
            prompt,
            expected_rule,
            expected_primary,
            expected_layer3,
        ) in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-edge-shared-action-{label}"
                    ),
                )
                trace = observed["winner_trace"]
                result = observed["route_decision"]["route_result"]
                self.assertEqual(expected_rule, trace["rule_id"])
                self.assertEqual(expected_primary, result["primary_skill"])
                self.assertEqual(expected_layer3, result["layer3_skills"])
                self.assertFalse(
                    any(
                        item["candidate_id"].startswith(
                            "implementation-owner:"
                        )
                        for item in trace["raw_candidates"]
                    )
                )

    def test_audit_integrity_candidates_honor_clause_local_action_polarity(
        self,
    ) -> None:
        analysis = (
            "Analyze audit evidence integrity for missing-record detection and "
            "tamper verification."
        )
        for action in ("update", "change"):
            negative = (
                f"Do not {action} audit evidence integrity for protected audit "
                "storage and export."
            )
            for prompt in (
                negative,
                f"{analysis} {negative}",
                f"{negative} {analysis}",
            ):
                with self.subTest(action=action, prompt=prompt):
                    observed = ORACLE.route_with_trace(
                        prompt,
                        main_execution=_test_main_execution(
                            f"t3-edge-audit-{action}-negative"
                        ),
                    )
                    trace = observed["winner_trace"]
                    result = observed["route_decision"]["route_result"]
                    self.assertEqual("audit-integrity-change", trace["rule_id"])
                    self.assertEqual(
                        "security-privacy-gate",
                        result["primary_skill"],
                    )
                    self.assertFalse(
                        any(
                            item["candidate_id"].startswith(
                                "implementation-owner:"
                            )
                            for item in trace["raw_candidates"]
                        )
                    )

        expected_implementation_candidate = {
            "candidate_id": "implementation-owner:logging-design-gate",
            "rule_id": "audit-integrity-change",
            "routing_family": "logging",
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "logging-design-gate",
            "layer3_skills": ["audit-evidence-integrity"],
            "review_skill": "logging-design-gate",
            "precedence": 4,
        }
        implementation_prompts = (
            (
                "Update",
                "Update audit evidence integrity for protected audit storage "
                "and export.",
            ),
            (
                "Change",
                "Change audit evidence integrity for protected audit storage "
                "and export.",
            ),
            (
                "Implement",
                "Implement audit evidence integrity for protected audit storage "
                "and export.",
            ),
            (
                "tamper-evident",
                "Implement tamper-evident audit storage and verification.",
            ),
        )
        for label, prompt in implementation_prompts:
            with self.subTest(implementation=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-edge-audit-{label.casefold()}-positive"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    ["implementation-owner:logging-design-gate"],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_implementation_candidate,
                    {
                        field: trace["selected_candidate"].get(field)
                        for field in expected_implementation_candidate
                    },
                )
                self.assertEqual(
                    [
                        "diagnostic-record-surface",
                        "effect-changed",
                        "explicit-implementation-action",
                        "audit-evidence-integrity",
                        "foundation-selector:audit-integrity-change",
                    ],
                    trace["selected_candidate"]["evidence"],
                )
                self.assertEqual(
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "logging-design-gate",
                        "layer3_skills": ["audit-evidence-integrity"],
                        "review_skill": "logging-design-gate",
                    },
                    _projected_route(observed),
                )

        expected_review_candidate = {
            "candidate_id": "audit-integrity-change",
            "rule_id": "audit-integrity-change",
            "routing_family": None,
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": ["audit-evidence-integrity"],
            "review_skill": "security-privacy-gate",
            "precedence": 5,
            "evidence": [
                "audit-evidence-integrity",
                "foundation-selector:audit-integrity-change",
            ],
        }
        review_prompts = (
            (
                "explicit-audit-review",
                "Review audit evidence integrity for missing-record detection "
                "and tamper verification.",
            ),
            (
                "actual-diff-audit-review",
                "Review the actual diff for audit evidence integrity and "
                "tamper verification.",
            ),
            (
                "tamper-evident-audit-review",
                "Review tamper-evident audit storage and verification.",
            ),
        )
        for label, prompt in review_prompts:
            with self.subTest(review=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-edge-audit-{label}"
                    ),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    ["audit-integrity-change"],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                self.assertEqual(
                    expected_review_candidate,
                    {
                        field: trace["selected_candidate"].get(field)
                        for field in expected_review_candidate
                    },
                )
                self.assertEqual(
                    {
                        "path": "direct",
                        "profile": "review-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": ["audit-evidence-integrity"],
                        "review_skill": "security-privacy-gate",
                    },
                    _projected_route(observed),
                )
                self.assertFalse(
                    any(
                        candidate["candidate_id"]
                        in {"review-logging-risk", "review-generic"}
                        for candidate in trace["raw_candidates"]
                    )
                )

        expected_generic_logging = {
            "candidate_id": "implementation-owner:logging-design-gate",
            "rule_id": None,
            "routing_family": "logging",
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "logging-design-gate",
            "layer3_skills": ["logging-error-handling"],
            "review_skill": "logging-design-gate",
            "precedence": 4,
        }
        mixed_logging_prompts = (
            (
                "Implement a structured redacted logging schema for events "
                "adjacent to the audit pipeline."
            ),
            (
                "Implement a structured redacted logging schema for descriptive "
                "audit records."
            ),
            (
                "Implement a structured redacted logging schema that records "
                "whether an audit exporter is enabled."
            ),
            (
                "Implement a structured redacted logging schema; audit evidence "
                "integrity remains unchanged."
            ),
            (
                "Implement a structured redacted logging schema; do not change "
                "audit evidence integrity."
            ),
            "Implement logs. Do not analyze audit evidence integrity.",
        )
        for index, prompt in enumerate(mixed_logging_prompts):
            with self.subTest(mixed=index, prompt=prompt):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-edge-audit-mixed-{index}"
                    ),
                )
                trace = observed["winner_trace"]
                raw_owners = [
                    item
                    for item in trace["raw_candidates"]
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ]
                self.assertEqual(1, len(raw_owners))
                for candidate in (
                    raw_owners[0],
                    trace["selected_candidate"],
                ):
                    self.assertEqual(
                        expected_generic_logging,
                        {
                            field: candidate.get(field)
                            for field in expected_generic_logging
                        },
                    )
                self.assertEqual(
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "logging-design-gate",
                        "layer3_skills": ["logging-error-handling"],
                        "review_skill": "logging-design-gate",
                    },
                    _projected_route(observed),
                )
                self.assertFalse(
                    any(
                        item["candidate_id"] == "audit-integrity-change"
                        or "audit-evidence-integrity"
                        in item.get("layer3_skills", [])
                        for item in trace["raw_candidates"]
                    )
                )

        strict_prompts = (
            (
                "Implement a structured redacted logging schema. Analyze audit "
                "evidence integrity for missing-record detection and tamper "
                "verification."
            ),
            (
                "Analyze audit evidence integrity for missing-record detection "
                "and tamper verification. Implement a structured redacted "
                "logging schema."
            ),
        )
        strict_observations = []
        expected_source_ids = [
            "audit-integrity-change",
            "implementation-owner:logging-design-gate",
        ]
        expected_conflict_evidence = [
            "audit-evidence-integrity",
            "diagnostic-record-surface",
            "dynamic-helper:_review_risk_layer3",
            "effect-changed",
            "explicit-implementation-action",
            "foundation-selector:audit-integrity-change",
            "foundation-selector:dynamic-foundation:logging-error-handling",
        ]
        expected_conflict_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for index, prompt in enumerate(strict_prompts):
            with self.subTest(strict=index, prompt=prompt):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"t3-edge-audit-strict-{index}"
                    ),
                )
                trace = observed["winner_trace"]
                selected = trace["selected_candidate"]
                self.assertEqual(
                    {
                        "candidate_id": "route-contract-conflict",
                        "candidate_type": "derived-conflict",
                        "evidence": expected_conflict_evidence,
                        "source_candidate_ids": expected_source_ids,
                        "precedence": 4,
                        "reason": "equal-precedence-route-contract-conflict",
                        **expected_conflict_route,
                    },
                    {
                        field: selected.get(field)
                        for field in (
                            "candidate_id",
                            "candidate_type",
                            "evidence",
                            "source_candidate_ids",
                            "precedence",
                            "reason",
                            *expected_conflict_route,
                        )
                    },
                )
                self.assertEqual(
                    expected_conflict_route,
                    _projected_route(observed),
                )
                self.assertEqual(
                    [
                        "implementation-owner:logging-design-gate",
                        "audit-integrity-change",
                    ],
                    [
                        candidate["candidate_id"]
                        for candidate in trace["raw_candidates"]
                    ],
                )
                expected_exclusions = [
                    {
                        **copy.deepcopy(candidate),
                        "reason": "ambiguous-route-contract",
                    }
                    for candidate in trace["raw_candidates"]
                ]
                self.assertEqual(
                    expected_exclusions,
                    trace["excluded_candidates"],
                )
                strict_observations.append(observed)

        self.assertEqual(
            2,
            len(strict_observations),
            "both strict prompt orders must produce complete observations",
        )
        self.assertEqual(
            _canonical_json_bytes(
                {
                    "selected": strict_observations[0]["winner_trace"][
                        "selected_candidate"
                    ],
                    "excluded": strict_observations[0]["winner_trace"][
                        "excluded_candidates"
                    ],
                }
            ),
            _canonical_json_bytes(
                {
                    "selected": strict_observations[1]["winner_trace"][
                        "selected_candidate"
                    ],
                    "excluded": strict_observations[1]["winner_trace"][
                        "excluded_candidates"
                    ],
                }
            ),
        )

        strict_pair = copy.deepcopy(
            strict_observations[0]["winner_trace"]["raw_candidates"]
        )
        admission = ORACLE.oracle_admission_authority()
        policy = _activation_v2_139c_implementation_policy()
        expected_strict_candidates = {
            "implementation-owner:logging-design-gate": {
                "candidate_type": "automatic-implementation-owner",
                "routing_family": "logging",
                "rule_id": None,
                "precedence": 4,
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "logging-design-gate",
                "layer3_skills": ["logging-error-handling"],
                "review_skill": "logging-design-gate",
                "evidence": [
                    "diagnostic-record-surface",
                    "effect-changed",
                    "explicit-implementation-action",
                    "dynamic-helper:_review_risk_layer3",
                    "foundation-selector:"
                    "dynamic-foundation:logging-error-handling",
                ],
            },
            "audit-integrity-change": {
                "candidate_type": "explicit-route",
                "routing_family": None,
                "rule_id": "audit-integrity-change",
                "precedence": 5,
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "security-privacy-gate",
                "layer3_skills": ["audit-evidence-integrity"],
                "review_skill": "security-privacy-gate",
                "evidence": [
                    "audit-evidence-integrity",
                    "foundation-selector:audit-integrity-change",
                ],
            },
        }
        for candidate in strict_pair:
            expected = expected_strict_candidates[candidate["candidate_id"]]
            self.assertEqual(
                expected,
                {
                    field: candidate.get(field)
                    for field in expected
                },
            )
            ORACLE._validate_foundation_candidate(
                candidate,
                candidate["layer3_skills"],
                admission_authority=admission,
            )

        selector_arguments = {
            "implementation_policy": policy,
            "audit_analysis_conflict": True,
            "admission_authority": admission,
        }
        direct_forward = ORACLE._select_route_cohort_candidate(
            strict_pair,
            **selector_arguments,
        )
        direct_reverse = ORACLE._select_route_cohort_candidate(
            list(reversed(strict_pair)),
            **selector_arguments,
        )
        self.assertEqual(direct_forward, direct_reverse)

        unrelated = {
            "candidate_id": "repository-first-default",
            "candidate_type": "fallback-route",
            "evidence": ["no-eligible-specific-candidate"],
            "precedence": 6,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "rule_id": "repository-first-default",
            "stage": "fallback",
            "precedence_class": "repository-first",
        }
        invalid_cardinalities = {
            "missing": strict_pair[:1],
            "duplicate": [
                strict_pair[0],
                copy.deepcopy(strict_pair[0]),
                strict_pair[1],
            ],
            "third-unrelated": [*strict_pair, unrelated],
        }
        for label, candidates in invalid_cardinalities.items():
            with self.subTest(invalid_cardinality=label):
                with self.assertRaises(ORACLE.RoutingIntegrityError):
                    ORACLE._select_route_cohort_candidate(
                        copy.deepcopy(candidates),
                        **selector_arguments,
                    )

        strict_mutations = {
            "type": (0, "candidate_type", "converted-cohort"),
            "family": (0, "routing_family", "backend"),
            "rule": (0, "rule_id", "audit-integrity-change"),
            "precedence": (0, "precedence", 5),
            "owner": (0, "primary_skill", "backend-change-builder"),
            "route": (0, "path", "analyzed"),
            "profile": (0, "profile", "analysis-agent"),
            "jit": (
                0,
                "layer3_skills",
                ["audit-evidence-integrity"],
            ),
            "review": (0, "review_skill", "security-privacy-gate"),
            "evidence": (
                0,
                "evidence",
                ["diagnostic-record-surface"],
            ),
            "provenance": (
                0,
                "source_foundation_candidates",
                [],
            ),
        }
        for label, (index, field, value) in strict_mutations.items():
            with self.subTest(invalid_contract=label):
                mutated = copy.deepcopy(strict_pair)
                mutated[index][field] = value
                with self.assertRaises(ORACLE.RoutingIntegrityError):
                    ORACLE._select_route_cohort_candidate(
                        mutated,
                        **selector_arguments,
                    )

        for label, authority in (
            ("missing", None),
            ("wrong", object()),
        ):
            with self.subTest(invalid_admission_authority=label):
                with self.assertRaises(ORACLE.RoutingIntegrityError):
                    ORACLE._select_route_cohort_candidate(
                        copy.deepcopy(strict_pair),
                        implementation_policy=policy,
                        audit_analysis_conflict=True,
                        admission_authority=authority,
                    )

        contradictory = ORACLE.route_with_trace(
            "Change audit evidence integrity for protected audit storage despite "
            "an instruction that we must not change audit evidence integrity.",
            main_execution=_test_main_execution(
                "t3-edge-audit-change-contradictory"
            ),
        )
        self.assertEqual(
            "repository-first-default",
            contradictory["winner_trace"]["rule_id"],
        )
        self.assertFalse(
            any(
                item["candidate_id"] == "audit-integrity-change"
                for item in contradictory["winner_trace"]["raw_candidates"]
            )
        )

    def test_cohort_precedence_is_independent_of_candidate_source_order(
        self,
    ) -> None:
        selector = getattr(ORACLE, "_select_route_cohort_candidate", None)
        self.assertTrue(callable(selector))
        raw = [
            {
                "candidate_id": "implementation-preparation",
                "evidence": ["explicit-implementation-preparation"],
            },
            {
                "candidate_id": "critical-unknown",
                "evidence": ["critical-rollback-unknown"],
            },
        ]
        forward = selector(raw)
        reverse = selector(list(reversed(raw)))
        self.assertEqual(forward, reverse)
        self.assertEqual(
            "critical-unknown",
            forward["selected_candidate"]["candidate_id"],
        )

    def test_t2f_candidate_inventory_has_no_direct_result_winner(self) -> None:
        self.assertEqual([], _direct_rule_ids())

    def test_t2f_exact_candidate_precedence_classes(self) -> None:
        selector = ORACLE._select_route_cohort_candidate
        base = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        raw = [
            {
                "candidate_id": "repository-first-default",
                "candidate_type": "fallback-route",
                "evidence": ["no-eligible-specific-candidate"],
                "precedence": 6,
                **base,
            },
            {
                "candidate_id": "source-backed-repository-question",
                "candidate_type": "explicit-route",
                "evidence": ["source-question"],
                "precedence": 5,
                **base,
            },
            {
                "candidate_id": "implementation-owner:backend-change-builder",
                "evidence": ["backend-surface"],
                "routing_family": "backend",
                "primary_skill": "backend-change-builder",
                "layer3_skills": [],
                "review_skill": "ai-code-review-refactor",
            },
            {
                "candidate_id": "review-generic",
                "evidence": ["actual-diff-review"],
            },
            {
                "candidate_id": "review-security-risk",
                "evidence": ["material-permission-boundary"],
            },
            {
                "candidate_id": "implementation-preparation",
                "evidence": ["explicit-implementation-preparation"],
            },
            {
                "candidate_id": "critical-unknown",
                "evidence": ["critical-owner-unknown"],
            },
        ]
        selected = selector(raw)
        self.assertEqual(
            [0, 1, 2, 3, 4, 5, 6],
            [item["precedence"] for item in selected["raw_candidates"]],
        )
        self.assertEqual(
            "critical-unknown",
            selected["selected_candidate"]["candidate_id"],
        )

    def test_t2f_same_contract_merges_evidence_without_id_winner(self) -> None:
        selector = ORACLE._select_route_cohort_candidate
        contract = {
            "candidate_type": "explicit-route",
            "precedence": 5,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        raw = [
            {
                "candidate_id": "z-source",
                "evidence": ["z-evidence"],
                **contract,
            },
            {
                "candidate_id": "a-source",
                "evidence": ["a-evidence"],
                **contract,
            },
        ]
        forward = selector(raw)
        reverse = selector(list(reversed(raw)))
        self.assertEqual(forward, reverse)
        selected = forward["selected_candidate"]
        self.assertEqual(
            "merged-route-candidate",
            selected["candidate_id"],
        )
        self.assertEqual(["a-evidence", "z-evidence"], selected["evidence"])
        self.assertEqual(["a-source", "z-source"], selected["source_candidate_ids"])

    def test_t2f_equal_precedence_different_routes_is_typed_conflict(
        self,
    ) -> None:
        selector = ORACLE._select_route_cohort_candidate
        raw = [
            {
                "candidate_id": "documentation-only-change",
                "candidate_type": "explicit-route",
                "evidence": ["documentation-change"],
                "precedence": 5,
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "change-documentation-gate",
                "layer3_skills": ["documentation-generation"],
                "review_skill": "change-documentation-gate",
            },
            {
                "candidate_id": "source-backed-repository-question",
                "candidate_type": "explicit-route",
                "evidence": ["repository-source-evidence"],
                "precedence": 5,
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
        ]
        forward = selector(raw)
        reverse = selector(list(reversed(raw)))
        self.assertEqual(forward, reverse)
        selected = forward["selected_candidate"]
        self.assertEqual("route-contract-conflict", selected["candidate_id"])
        self.assertEqual("derived-conflict", selected["candidate_type"])
        self.assertEqual(
            ["documentation-only-change", "source-backed-repository-question"],
            selected["source_candidate_ids"],
        )
        self.assertEqual(
            "engineering-change-analysis",
            selected["primary_skill"],
        )

    def test_t2f_empty_unmatched_default_has_closed_reason(self) -> None:
        observed = ORACLE.route_with_trace(
            "Summarize this bounded repository observation.",
            main_execution=_test_main_execution("t2g-fallback"),
        )
        self.assertEqual(
            "repository-first-default",
            observed["winner_trace"]["selected_candidate"]["candidate_id"],
        )
        self.assertEqual(
            ["no-eligible-specific-candidate"],
            observed["winner_trace"]["selected_candidate"]["evidence"],
        )

    def test_t2f_specific_candidate_is_source_order_independent(self) -> None:
        fragments = (
            "Implement an accepted backend service stream backpressure change.",
            "Ask a question using repository source evidence.",
        )
        left = ORACLE.route_with_trace(
            " ".join(fragments),
            main_execution=_test_main_execution("t2g-order-left"),
        )
        right = ORACLE.route_with_trace(
            " ".join(reversed(fragments)),
            main_execution=_test_main_execution("t2g-order-right"),
        )
        self.assertEqual(_projected_route(left), _projected_route(right))
        self.assertEqual(
            left["winner_trace"]["selected_candidate"],
            right["winner_trace"]["selected_candidate"],
        )
        self.assertEqual(
            "implementation-owner:backend-change-builder",
            left["winner_trace"]["selected_candidate"]["candidate_id"],
        )

    def test_activation_v3_candidate_contract_keeps_binding_private(self) -> None:
        errors: list[str] = []
        contract_fields = getattr(
            ORACLE,
            "ROUTE_CANDIDATE_CONTRACT_FIELDS",
            (),
        )
        if "artifact_binding_id" not in contract_fields:
            errors.append(
                "private binding identity is absent from the candidate contract"
            )
        if "artifact_binding_id" in ORACLE.ROUTE_CONTRACT_FIELDS:
            errors.append("private binding identity widened the public contract")

        parameters = inspect.signature(
            ORACLE._build_route_candidates
        ).parameters
        expected_names = (
            "raw_candidates",
            "route_candidates",
            "normalized_text",
            "implementation_policy",
            "domain_specs",
            "admission_authority",
        )
        if tuple(parameters) != expected_names:
            errors.append(
                f"builder signature names changed: {tuple(parameters)!r}"
            )
        else:
            for name in expected_names[:2]:
                if (
                    parameters[name].kind
                    is not inspect.Parameter.POSITIONAL_OR_KEYWORD
                ):
                    errors.append(f"builder positional parameter changed: {name}")
            for name in expected_names[2:]:
                expected_default = (
                    None
                    if name == "admission_authority"
                    else inspect.Parameter.empty
                )
                if (
                    parameters[name].kind
                    is not inspect.Parameter.KEYWORD_ONLY
                    or parameters[name].default
                    is not expected_default
                ):
                    errors.append(f"builder keyword-only parameter changed: {name}")

        binding_id = f"brb1:{'1' * 64}"
        builder_inputs = (
            [
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=binding_id,
                ),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=binding_id,
                ),
            ],
            [
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=binding_id,
                ),
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=binding_id,
                ),
            ],
        )
        try:
            built = _activation_v2_139c_call_builder(
                *copy.deepcopy(builder_inputs),
                prompt="Review the engineering brief and task plan.",
            )
        except Exception as exc:  # pragma: no cover - aggregate Red evidence
            errors.append(f"direct builder rejected inputs: {type(exc).__name__}")
        else:
            if "artifact_binding_id" in _nested_mapping_keys(built):
                errors.append("direct builder retained a private input key")
            if any(
                value.startswith("brb1:")
                for value in _string_values(built)
            ):
                errors.append("direct builder retained a private input token")

        fallback = {
            "candidate_id": "repository-first-default",
            "candidate_type": "fallback-route",
            "evidence": ["no-eligible-specific-candidate"],
            "precedence": 6,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "artifact_binding_id": binding_id,
        }
        invalid_candidates = {
            "nonartifact-legal-token": fallback,
            "wrong-prefix": _artifact_review_candidate(
                high_risk=True,
                artifact_binding_id=f"brb2:{'1' * 64}",
            ),
            "wrong-length": _artifact_review_candidate(
                high_risk=True,
                artifact_binding_id=f"brb1:{'1' * 63}",
            ),
            "uppercase": _artifact_review_candidate(
                high_risk=True,
                artifact_binding_id=f"brb1:{'A' * 64}",
            ),
            "wrong-type": _artifact_review_candidate(
                high_risk=True,
                artifact_binding_id=159,
            ),
        }
        for label, candidate in invalid_candidates.items():
            try:
                ORACLE._select_route_cohort_candidate([candidate])
            except ORACLE.RoutingIntegrityError:
                continue
            except Exception as exc:  # pragma: no cover - aggregate Red evidence
                errors.append(
                    f"{label} raised {type(exc).__name__}, not routing integrity"
                )
            else:
                errors.append(f"{label} was accepted by the direct selector")
        self.assertEqual(
            [],
            errors,
            "[activation-v3-candidate-contract] the builder contract must "
            "remain exact, direct inputs must be scrubbed, and only canonical "
            "artifact-writer tokens may reach selection",
        )

    def test_activation_v3_same_binding_refines_generic_to_high_risk_both_orders(
        self,
    ) -> None:
        binding_id = f"brb1:{'1' * 64}"
        generic = _artifact_review_candidate(
            high_risk=False,
            artifact_binding_id=binding_id,
        )
        high_risk = _artifact_review_candidate(
            high_risk=True,
            artifact_binding_id=binding_id,
        )
        selector = ORACLE._select_route_cohort_candidate
        captured_inputs = {
            "forward": [generic, high_risk],
            "reverse": [high_risk, generic],
        }
        forward = selector(copy.deepcopy(captured_inputs["forward"]))
        reverse = selector(copy.deepcopy(captured_inputs["reverse"]))
        for label, candidates in captured_inputs.items():
            self.assertEqual(
                [binding_id, binding_id],
                sorted(
                    candidate["artifact_binding_id"]
                    for candidate in candidates
                ),
                f"[same-binding-selector-input:{label}] both artifact writers "
                "must carry the canonical private token into selection",
            )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            "high-risk-architecture-plan",
            forward["selected_candidate"]["candidate_id"],
            "[same-binding-specialist-refinement] high-risk review must refine "
            "the generic review for the same artifact",
        )
        generic_exclusion = next(
            candidate
            for candidate in forward["excluded_candidates"]
            if candidate["candidate_id"] == "engineering-artifact-review"
        )
        self.assertEqual(
            "specialist-refinement-same-artifact",
            generic_exclusion["reason"],
        )
        self.assertEqual(3, forward["selected_candidate"]["precedence"])
        self.assertEqual(
            [
                "engineering-artifact-review",
                "high-risk-architecture-plan",
            ],
            forward["selected_candidate"]["source_candidate_ids"],
        )
        for label, selection in (
            ("forward", forward),
            ("reverse", reverse),
        ):
            for surface in (
                "selected_candidate",
                "raw_candidates",
                "excluded_candidates",
            ):
                value = selection[surface]
                self.assertNotIn(
                    "artifact_binding_id",
                    _nested_mapping_keys(value),
                    f"[same-binding-selector-output:{label}:{surface}] "
                    "private key leaked recursively",
                )
                self.assertFalse(
                    any(
                        item.startswith("brb1:")
                        for item in _string_values(value)
                    ),
                    f"[same-binding-selector-output:{label}:{surface}] "
                    "private token leaked recursively",
                )
        critical = {
            "candidate_id": "critical-unknown",
            "evidence": ["critical-owner-unknown"],
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        self.assertEqual(
            "critical-unknown",
            selector([generic, high_risk, critical])["selected_candidate"][
                "candidate_id"
            ],
            "[artifact-group-before-v2] the resolved artifact group must "
            "re-enter ordinary V2 precedence at its minimum precedence",
        )
        fallback = {
            "candidate_id": "repository-first-default",
            "candidate_type": "fallback-route",
            "evidence": ["no-eligible-specific-candidate"],
            "precedence": 6,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        self.assertEqual(
            "high-risk-architecture-plan",
            selector([fallback, high_risk, generic])["selected_candidate"][
                "candidate_id"
            ],
        )

    def test_activation_v3_different_bindings_conflict_both_orders(self) -> None:
        generic = _artifact_review_candidate(
            high_risk=False,
            artifact_binding_id=f"brb1:{'1' * 64}",
        )
        high_risk = _artifact_review_candidate(
            high_risk=True,
            artifact_binding_id=f"brb1:{'2' * 64}",
        )
        selector = ORACLE._select_route_cohort_candidate
        forward = selector([generic, high_risk])
        reverse = selector([high_risk, generic])
        self.assertEqual(forward, reverse)
        selected = forward["selected_candidate"]
        self.assertEqual(
            "artifact-binding-conflict",
            selected.get("reason"),
            "[different-binding-conflict] precedence must not merge or refine "
            "different artifacts",
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                field: selected.get(field)
                for field in ORACLE.ROUTE_CONTRACT_FIELDS
            },
        )
        self.assertEqual("derived-conflict", selected["candidate_type"])
        self.assertEqual(3, selected["precedence"])
        self.assertEqual(
            [
                "engineering-artifact-review",
                "high-risk-architecture-plan",
            ],
            selected["source_candidate_ids"],
        )
        self.assertNotIn("artifact_binding_id", selected)

    def test_activation_v3_high_risk_candidate_cannot_mix_missing_binding(
        self,
    ) -> None:
        errors: list[str] = []
        first_binding = f"brb1:{'1' * 64}"
        second_binding = f"brb1:{'2' * 64}"
        for label, token in (
            ("first", first_binding),
            ("second", second_binding),
        ):
            digest = token.removeprefix("brb1:")
            if (
                not token.startswith("brb1:")
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                errors.append(f"{label}: conflict token fixture is not valid")

        def omitted_candidate(*, high_risk: bool) -> dict[str, object]:
            candidate = _artifact_review_candidate(
                high_risk=high_risk,
                artifact_binding_id=None,
            )
            candidate.pop("artifact_binding_id")
            return candidate

        safe_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        high_risk_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["release-rollback"],
            "review_skill": "high-risk-design-review",
        }
        ordinary_route = {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "engineering-artifact-review",
            "layer3_skills": [],
            "review_skill": "engineering-artifact-review",
        }

        lone_high_risk = omitted_candidate(high_risk=True)
        try:
            high_risk_selection = ORACLE._select_route_cohort_candidate(
                [lone_high_risk]
            )
        except Exception as exc:  # pragma: no cover - aggregate Red evidence
            errors.append(
                "lone-high-risk-omitted: legacy route was rejected with "
                f"{type(exc).__name__}"
            )
        else:
            high_risk_selected = high_risk_selection["selected_candidate"]
            expected_high_risk = {
                "candidate_id": "high-risk-architecture-plan",
                "candidate_type": "explicit-route",
                "reason": "highest-semantic-precedence",
                "precedence": 5,
                "source_candidate_ids": ["high-risk-architecture-plan"],
                **high_risk_route,
            }
            observed_high_risk = {
                field: high_risk_selected.get(field)
                for field in expected_high_risk
            }
            if observed_high_risk != expected_high_risk:
                errors.append(
                    "lone-high-risk-omitted: legacy candidate differs: "
                    f"{observed_high_risk!r}"
                )
            if (
                "artifact_binding_id"
                in _nested_mapping_keys(high_risk_selection)
            ):
                errors.append(
                    "lone-high-risk-omitted: private binding key leaked"
                )
            if any(
                value.startswith("brb1:")
                for value in _string_values(high_risk_selection)
            ):
                errors.append(
                    "lone-high-risk-omitted: private binding token leaked"
                )

        lone_ordinary = omitted_candidate(high_risk=False)
        try:
            ordinary_selection = ORACLE._select_route_cohort_candidate(
                [lone_ordinary]
            )
        except Exception as exc:  # pragma: no cover - aggregate Red evidence
            errors.append(
                "lone-ordinary-missing: legacy route was rejected with "
                f"{type(exc).__name__}"
            )
        else:
            ordinary_selected = ordinary_selection["selected_candidate"]
            expected_ordinary = {
                "candidate_id": "engineering-artifact-review",
                "candidate_type": "artifact-review-route",
                "reason": "highest-semantic-precedence",
                "precedence": 3,
                "source_candidate_ids": ["engineering-artifact-review"],
                **ordinary_route,
            }
            observed_ordinary = {
                field: ordinary_selected.get(field)
                for field in expected_ordinary
            }
            if observed_ordinary != expected_ordinary:
                errors.append(
                    "lone-ordinary-omitted: legacy candidate differs: "
                    f"{observed_ordinary!r}"
                )
            if (
                "artifact_binding_id"
                in _nested_mapping_keys(ordinary_selection)
            ):
                errors.append(
                    "lone-ordinary-omitted: private key leaked into output"
                )
            if any(
                value.startswith("brb1:")
                for value in _string_values(ordinary_selection)
            ):
                errors.append(
                    "lone-ordinary-omitted: private token leaked into output"
                )

        lone_ordinary_none = _artifact_review_candidate(
            high_risk=False,
            artifact_binding_id=None,
        )
        try:
            ordinary_none_selection = ORACLE._select_route_cohort_candidate(
                [lone_ordinary_none]
            )
        except Exception as exc:  # pragma: no cover - aggregate Red evidence
            errors.append(
                "lone-ordinary-none: raised "
                f"{type(exc).__name__}, expected a normal derived conflict"
            )
        else:
            ordinary_none_selected = ordinary_none_selection[
                "selected_candidate"
            ]
            expected_ordinary_none = {
                "candidate_id": "route-contract-conflict",
                "candidate_type": "derived-conflict",
                "reason": "binding-missing",
                "precedence": lone_ordinary_none["precedence"],
                "source_candidate_ids": ["engineering-artifact-review"],
                **safe_route,
            }
            observed_ordinary_none = {
                field: ordinary_none_selected.get(field)
                for field in expected_ordinary_none
            }
            if observed_ordinary_none != expected_ordinary_none:
                errors.append(
                    "lone-ordinary-none: derived candidate differs: "
                    f"{observed_ordinary_none!r}"
                )
            if (
                "artifact_binding_id"
                in _nested_mapping_keys(ordinary_none_selection)
            ):
                errors.append(
                    "lone-ordinary-none: private binding key leaked"
                )
            if any(
                value.startswith("brb1:")
                for value in _string_values(ordinary_none_selection)
            ):
                errors.append(
                    "lone-ordinary-none: private binding token leaked"
                )

        omitted_pair = (
            omitted_candidate(high_risk=False),
            omitted_candidate(high_risk=True),
        )
        try:
            omitted_forward = ORACLE._select_route_cohort_candidate(
                list(omitted_pair)
            )
            omitted_reverse = ORACLE._select_route_cohort_candidate(
                list(reversed(omitted_pair))
            )
        except Exception as exc:  # pragma: no cover - aggregate Red evidence
            errors.append(
                f"both-omitted: legacy V2 selection raised {type(exc).__name__}"
            )
        else:
            if omitted_forward != omitted_reverse:
                errors.append("both-omitted: source order changed selection")
            omitted_selected = omitted_forward["selected_candidate"]
            expected_omitted = {
                "candidate_id": "engineering-artifact-review",
                "candidate_type": "artifact-review-route",
                "reason": "highest-semantic-precedence",
                "precedence": 3,
                "source_candidate_ids": ["engineering-artifact-review"],
                **ordinary_route,
            }
            observed_omitted = {
                field: omitted_selected.get(field)
                for field in expected_omitted
            }
            if observed_omitted != expected_omitted:
                errors.append(
                    "both-omitted: ordinary V2 precedence differs: "
                    f"{observed_omitted!r}"
                )
            for order, selection in (
                ("forward", omitted_forward),
                ("reverse", omitted_reverse),
            ):
                if "artifact_binding_id" in _nested_mapping_keys(selection):
                    errors.append(
                        f"both-omitted:{order}: private binding key leaked"
                    )
                if any(
                    value.startswith("brb1:")
                    for value in _string_values(selection)
                ):
                    errors.append(
                        f"both-omitted:{order}: private binding token leaked"
                    )

        cases = {
            "high-risk-missing": (
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=first_binding,
                ),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=None,
                ),
            ),
            "generic-missing": (
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=None,
                ),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=first_binding,
                ),
            ),
            "canonical-generic-high-risk-omitted": (
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=first_binding,
                ),
                omitted_candidate(high_risk=True),
            ),
            "generic-omitted-canonical-high-risk": (
                omitted_candidate(high_risk=False),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=first_binding,
                ),
            ),
            "ordinary-none-high-risk-omitted": (
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=None,
                ),
                omitted_candidate(high_risk=True),
            ),
            "ordinary-omitted-high-risk-none": (
                omitted_candidate(high_risk=False),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=None,
                ),
            ),
            "both-missing": (
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=None,
                ),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=None,
                ),
            ),
            "distinct-bindings": (
                _artifact_review_candidate(
                    high_risk=False,
                    artifact_binding_id=first_binding,
                ),
                _artifact_review_candidate(
                    high_risk=True,
                    artifact_binding_id=second_binding,
                ),
            ),
        }
        for label, candidates in cases.items():
            try:
                forward = ORACLE._select_route_cohort_candidate(
                    list(candidates)
                )
                reverse = ORACLE._select_route_cohort_candidate(
                    list(reversed(candidates))
                )
            except Exception as exc:  # pragma: no cover - aggregate Red evidence
                errors.append(f"{label}: raised {type(exc).__name__}")
                continue
            if forward != reverse:
                errors.append(f"{label}: source order changed selection")
                continue
            selected = forward["selected_candidate"]
            expected_reason = (
                "artifact-binding-conflict"
                if label == "distinct-bindings"
                else "binding-missing"
            )
            if selected.get("reason") != expected_reason:
                errors.append(
                    f"{label}: expected {expected_reason!r}, found "
                    f"{selected.get('reason')!r}"
                )
            if {
                field: selected.get(field)
                for field in ORACLE.ROUTE_CONTRACT_FIELDS
            } != safe_route:
                errors.append(f"{label}: safe fallback route differs")
            if selected.get("precedence") != 3:
                errors.append(f"{label}: artifact group lost min precedence")
            if selected.get("source_candidate_ids") != [
                "engineering-artifact-review",
                "high-risk-architecture-plan",
            ]:
                errors.append(f"{label}: source candidate provenance differs")
            for order, selection in (
                ("forward", forward),
                ("reverse", reverse),
            ):
                if "artifact_binding_id" in _nested_mapping_keys(selection):
                    errors.append(
                        f"{label}:{order}: private binding key leaked"
                    )
                if any(
                    value.startswith("brb1:")
                    for value in _string_values(selection)
                ):
                    errors.append(
                        f"{label}:{order}: private binding token leaked"
                    )
        self.assertEqual(
            [],
            errors,
            "[high-risk-binding-presence] omitted fields preserve legacy V2 "
            "selection, while declared missing, mixed-presence, or distinct "
            "bindings fail closed without source-order or privacy drift",
        )

    def test_activation_v3_binding_writer_privacy_and_provenance_are_end_to_end(
        self,
    ) -> None:
        errors: list[str] = []
        main_execution = _four_foundation_main_execution()
        binding_digest = FOUR_FOUNDATION_BINDING.rsplit(
            "|binding_sha256=",
            1,
        )[1]
        binding_id = f"brb1:{binding_digest}"
        expected_writer_ids = {
            "engineering-artifact-review",
            "high-risk-architecture-plan",
        }
        prompt = (
            "Review the engineering brief and task plan. Analyze high-risk "
            "multiple tasks; architecture, module boundaries, and dependency "
            "graph are accepted and fixed."
        )
        captured_batches: list[list[dict[str, object]]] = []
        captured_selections: list[dict[str, object]] = []
        real_selector = ORACLE._select_route_cohort_candidate

        def capture(candidates, **kwargs):
            captured_batches.append(copy.deepcopy(candidates))
            selection = real_selector(candidates, **kwargs)
            captured_selections.append(copy.deepcopy(selection))
            return selection

        outputs: dict[str, dict[str, object]] = {}
        with mock.patch.object(
            ORACLE,
            "_select_route_cohort_candidate",
            side_effect=capture,
        ):
            for api_name in ("route", "route_with_trace"):
                try:
                    outputs[api_name] = getattr(ORACLE, api_name)(
                        prompt,
                        main_execution=copy.deepcopy(main_execution),
                    )
                except Exception as exc:  # pragma: no cover - aggregate Red evidence
                    errors.append(
                        f"{api_name} rejected valid binding: "
                        f"{type(exc).__name__}"
                    )

        if len(captured_batches) != 2 or len(captured_selections) != 2:
            errors.append("both public APIs must run one captured selector")
        for index, batch in enumerate(captured_batches):
            bound_candidates = [
                candidate
                for candidate in batch
                if "artifact_binding_id" in candidate
            ]
            observed_writers = {
                candidate["candidate_id"]
                for candidate in bound_candidates
            }
            if observed_writers != expected_writer_ids:
                errors.append(
                    f"batch {index}: binding writers={sorted(observed_writers)}"
                )
            if any(
                candidate["artifact_binding_id"] != binding_id
                for candidate in bound_candidates
            ):
                errors.append(f"batch {index}: binding token differs")

        for index, selection in enumerate(captured_selections):
            selected = selection["selected_candidate"]
            if selected.get("candidate_id") != "high-risk-architecture-plan":
                errors.append(f"selection {index}: specialist did not refine")
            if selected.get("precedence") != 3:
                errors.append(f"selection {index}: min precedence differs")
            if selected.get("source_candidate_ids") != [
                "engineering-artifact-review",
                "high-risk-architecture-plan",
            ]:
                errors.append(f"selection {index}: source provenance differs")
            for surface in (
                "selected_candidate",
                "raw_candidates",
                "excluded_candidates",
            ):
                value = selection[surface]
                if "artifact_binding_id" in _nested_mapping_keys(value):
                    errors.append(
                        f"selection {index}:{surface}: private key leaked"
                    )
                if any(
                    item.startswith("brb1:")
                    for item in _string_values(value)
                ):
                    errors.append(
                        f"selection {index}:{surface}: private token leaked"
                    )

        public_outputs = {
            "route": outputs.get("route"),
            "route_with_trace": outputs.get("route_with_trace"),
        }
        for api_name, output in public_outputs.items():
            if output is None:
                continue
            if "artifact_binding_id" in _nested_mapping_keys(output):
                errors.append(f"{api_name}: private key leaked recursively")
            if any(
                item.startswith("brb1:")
                for item in _string_values(output)
            ):
                errors.append(f"{api_name}: private token leaked recursively")
            decision = (
                output
                if api_name == "route"
                else output.get("route_decision")
            )
            if not isinstance(decision, dict):
                errors.append(f"{api_name}: route decision is missing")
                continue
            if decision.get("main_execution_provenance") is not None:
                errors.append(f"{api_name}: analyzed Main provenance leaked")
            result = decision.get("route_result")
            if (
                not isinstance(result, dict)
                or result.get("review_skill") != "high-risk-design-review"
            ):
                errors.append(f"{api_name}: high-risk writer was not projected")
            elif (
                result.get("execution_level") is not None
                or result.get("level_basis") is not None
            ):
                errors.append(f"{api_name}: analyzed execution metadata leaked")
        self.assertEqual(
            [],
            errors,
            "[activation-v3-binding-end-to-end] only the two artifact writers "
            "may carry private provenance, both APIs must suppress analyzed "
            "Main execution metadata, and no private field or token may escape",
        )

    def test_activation_v2_139a_enrichment_helper_preserves_candidate_identity(
        self,
    ) -> None:
        def absent_helper_sentinel(
            candidates,
            **_authority,
        ):
            return list(candidates)

        enricher = getattr(
            ORACLE,
            "_enrich_route_candidates",
            absent_helper_sentinel,
        )
        candidates = [
            {
                "candidate_id": "activation-v2-139a-first",
                "candidate_type": "converted-cohort",
                "evidence": ["first-evidence"],
                "layer3_skills": ["repository-context-map"],
            },
            {
                "candidate_id": "activation-v2-139a-second",
                "candidate_type": "explicit-route",
                "evidence": ["second-evidence"],
                "layer3_skills": [],
            },
        ]
        original_records = list(candidates)
        original_content = copy.deepcopy(candidates)
        with _activation_v2_139b_direct_enrichment_isolation():
            enriched = enricher(
                candidates,
                domain_specs={},
                domain_authority={},
                layer3_authority_by_primary={},
                maximum_layer3=3,
            )
        self.assertIs(
            candidates,
            enriched,
            "[activation-v2-139a-identity] enrichment must return the exact "
            "supplied candidate list",
        )
        self.assertEqual(original_content, candidates)
        self.assertTrue(
            all(
                actual is original
                for actual, original in zip(
                    candidates,
                    original_records,
                    strict=True,
                )
            )
        )

    def test_activation_v2_139b_fixed_payment_and_foundations_enrich_in_place(
        self,
    ) -> None:
        authority = _activation_v2_139b_authority()
        foundations = [
            "data-side-effect-flow-tracing",
            "repository-impact-inspection",
        ]
        domains = ["payment-trading-extension"]
        layer3_by_primary = authority["layer3_authority_by_primary"]
        domain_authority = authority["domain_authority"]
        self.assertTrue(
            set([*domains, *foundations])
            <= set(layer3_by_primary["engineering-change-analysis"])
        )
        self.assertIn(
            "engineering-change-analysis",
            domain_authority["domains_by_name"][
                "payment-trading-extension"
            ]["used_by"],
        )
        candidate = _activation_v2_139b_fixed_candidate(
            "activation-v2-139b-payment-foundations",
            primary_skill="engineering-change-analysis",
            profile="analysis-agent",
            path="analyzed",
            review_skill="architecture-impact-reviewer",
            domains=domains,
            foundations=foundations,
            evidence=["ordinary-fixed-payment-evidence"],
        )
        original_keys = set(candidate)
        candidates = [candidate]
        with _activation_v2_139b_direct_enrichment_isolation():
            enriched = ORACLE._enrich_route_candidates(
                candidates,
                **authority,
            )
        self.assertIs(candidates, enriched)
        self.assertIs(candidate, enriched[0])
        self.assertEqual(
            set(ORACLE.ROUTE_CANDIDATE_LAYER3_FIELDS),
            set(candidate) - original_keys,
        )
        self.assertEqual(
            foundations,
            candidate["eligible_foundation_layer3_skills"],
        )
        self.assertEqual(
            domains,
            candidate["eligible_domain_layer3_skills"],
        )
        self.assertEqual(
            [*domains, *foundations],
            candidate["eligible_layer3_skills"],
        )
        self.assertEqual(
            candidate["eligible_layer3_skills"],
            candidate["layer3_skills"],
        )
        self.assertEqual(1, candidate["reserved_domain_capacity"])
        self.assertFalse(candidate["layer3_overflow"])

    def test_activation_v2_139b_reversed_domains_use_registry_order_and_overflow(
        self,
    ) -> None:
        authority = _activation_v2_139b_authority()
        domain_authority = authority["domain_authority"]
        registry_domains = [
            domain
            for domain in domain_authority["domain_order"]
            if domain
            in {
                "payment-trading-extension",
                "cloud-platform-extension",
            }
        ]
        self.assertEqual(
            [
                "payment-trading-extension",
                "cloud-platform-extension",
            ],
            registry_domains,
        )
        foundations = [
            "data-side-effect-flow-tracing",
            "repository-impact-inspection",
        ]
        requested_domains = [
            "cloud-platform-extension",
            "payment-trading-extension",
        ]
        self.assertTrue(
            set([*requested_domains, *foundations])
            <= set(
                authority["layer3_authority_by_primary"][
                    "engineering-change-analysis"
                ]
            )
        )
        candidate = _activation_v2_139b_fixed_candidate(
            "activation-v2-139b-reversed-domains",
            primary_skill="engineering-change-analysis",
            profile="analysis-agent",
            path="analyzed",
            review_skill="architecture-impact-reviewer",
            domains=requested_domains,
            foundations=foundations,
            evidence=["ordinary-reversed-domain-evidence"],
        )
        with _activation_v2_139b_direct_enrichment_isolation():
            ORACLE._enrich_route_candidates([candidate], **authority)
        self.assertTrue(candidate.get("layer3_overflow"))
        self.assertEqual(
            registry_domains,
            candidate.get("eligible_domain_layer3_skills"),
        )
        self.assertEqual(
            [*registry_domains, *foundations],
            candidate.get("eligible_layer3_skills"),
        )
        self.assertEqual(
            candidate.get("eligible_layer3_skills"),
            candidate["layer3_skills"],
        )
        self.assertEqual(2, candidate.get("reserved_domain_capacity"))
        self.assertEqual(4, len(candidate["eligible_layer3_skills"]))

    def test_activation_v2_139b_four_foundations_overflow_without_domain_capacity(
        self,
    ) -> None:
        authority = _activation_v2_139b_authority()
        foundations = [
            "algorithm-data-structure-selection",
            "language-runtime-selection",
            "solution-optimality-evaluation",
            "technology-stack-selection",
        ]
        actual_foundations = [
            skill
            for skill in authority["layer3_authority_by_primary"][
                "high-risk-design-review"
            ]
            if skill in set(foundations)
        ]
        self.assertEqual(foundations, actual_foundations)
        self.assertEqual(3, authority["maximum_layer3"])
        candidate = _activation_v2_139b_fixed_candidate(
            "activation-v2-139b-four-foundations",
            primary_skill="high-risk-design-review",
            profile="review-agent",
            path="direct",
            review_skill="high-risk-design-review",
            domains=[],
            foundations=foundations,
            evidence=["ordinary-four-foundation-evidence"],
        )
        with _activation_v2_139b_direct_enrichment_isolation():
            ORACLE._enrich_route_candidates([candidate], **authority)
        self.assertTrue(candidate.get("layer3_overflow"))
        self.assertEqual(
            foundations,
            candidate.get("eligible_foundation_layer3_skills"),
        )
        self.assertEqual(
            [],
            candidate.get("eligible_domain_layer3_skills"),
        )
        self.assertEqual(
            foundations,
            candidate.get("eligible_layer3_skills"),
        )
        self.assertEqual(
            candidate.get("eligible_layer3_skills"),
            candidate["layer3_skills"],
        )
        self.assertEqual(0, candidate.get("reserved_domain_capacity"))

    def test_activation_v2_139b_ai_domain_authority_is_exact_and_candidate_local(
        self,
    ) -> None:
        authority = _activation_v2_139b_authority()
        domain = "ai-product-extension"
        layer3_by_primary = authority["layer3_authority_by_primary"]
        domain_authority = authority["domain_authority"]
        expected_owners = {
            "ai-code-review-refactor",
            "backend-change-builder",
            "data-middleware-change-builder",
            "engineering-change-analysis",
            "frontend-change-builder",
            "installed-client-change-builder",
            "integration-change-builder",
            "security-privacy-gate",
        }
        self.assertEqual(
            expected_owners,
            set(domain_authority["domains_by_name"][domain]["used_by"]),
        )
        self.assertIn(
            "task-agent",
            domain_authority["domains_by_name"][domain]["role_support"],
        )
        for owner in expected_owners:
            with self.subTest(owner=owner):
                self.assertIn(domain, layer3_by_primary[owner])
        self.assertNotIn(domain, layer3_by_primary["quality-test-gate"])
        self.assertNotIn(
            "quality-test-gate",
            domain_authority["domains_by_name"][domain]["used_by"],
        )
        incompatible = _activation_v2_139b_fixed_candidate(
            "activation-v2-139b-incompatible-ai",
            primary_skill="quality-test-gate",
            profile="task-agent",
            path="direct",
            review_skill="ai-code-review-refactor",
            domains=[domain],
            foundations=[],
            evidence=["ordinary-backend-evidence"],
            reason="ordinary-backend-reason",
        )
        compatible = _activation_v2_139b_fixed_candidate(
            "activation-v2-139b-compatible-ai",
            primary_skill="engineering-change-analysis",
            profile="analysis-agent",
            path="analyzed",
            review_skill="architecture-impact-reviewer",
            domains=[domain],
            foundations=[],
            evidence=["ordinary-analysis-evidence"],
            reason="ordinary-analysis-reason",
        )
        with _activation_v2_139b_direct_enrichment_isolation():
            ORACLE._enrich_route_candidates(
                [incompatible, compatible],
                **authority,
            )
        self.assertEqual(
            [
                "ordinary-backend-evidence",
                *sorted(
                    {
                        "domain-layer3-incompatible:"
                        "ai-product-extension:professional-layer3",
                        "domain-layer3-incompatible:"
                        "ai-product-extension:reciprocity",
                    }
                ),
            ],
            incompatible["evidence"],
        )
        self.assertEqual(
            "ordinary-backend-reason",
            incompatible["reason"],
        )
        self.assertEqual(
            [],
            incompatible.get("eligible_domain_layer3_skills"),
        )
        self.assertEqual([], incompatible.get("eligible_layer3_skills"))
        self.assertEqual([], incompatible["layer3_skills"])
        self.assertEqual(
            [domain],
            compatible.get("eligible_domain_layer3_skills"),
        )
        self.assertEqual(
            [domain],
            compatible.get("eligible_layer3_skills"),
        )
        self.assertEqual([domain], compatible["layer3_skills"])
        self.assertEqual(
            ["ordinary-analysis-evidence"],
            compatible["evidence"],
        )
        self.assertEqual(
            "ordinary-analysis-reason",
            compatible["reason"],
        )

    def test_ai_product_routes_reach_exact_authoritative_surfaces(self) -> None:
        cases = (
            (
                "backend",
                "Implement an accepted backend service prompt workflow where "
                "a model decision changes response behavior under delegated "
                "authority.",
                "backend-change-builder",
                ["ai-product-extension"],
            ),
            (
                "frontend",
                "Implement an accepted browser frontend component where prompt "
                "content enters model context and changes generated summary "
                "behavior.",
                "frontend-change-builder",
                [
                    "ai-product-extension",
                    "web-platform-professional-usage",
                ],
            ),
            (
                "data-middleware",
                "Implement an accepted database middleware retrieval pipeline "
                "where embedding retrieval enters model context.",
                "data-middleware-change-builder",
                ["ai-product-extension"],
            ),
            (
                "integration",
                "Implement an accepted external integration adapter where "
                "prompt content enters model context and changes provider "
                "response handling.",
                "integration-change-builder",
                ["ai-product-extension"],
            ),
            (
                "installed-client",
                "Implement an accepted Android installed application screen "
                "where prompt content enters model context and changes "
                "generated summary behavior.",
                "installed-client-change-builder",
                ["ai-product-extension", "android-platform-extension"],
            ),
            (
                "actual-diff-review",
                "Review the actual diff where backend prompt content enters "
                "model context and changes generated summary behavior.",
                "ai-code-review-refactor",
                ["ai-product-extension", "code-review"],
            ),
        )
        for case_id, prompt, primary, layer3 in cases:
            with self.subTest(case=case_id):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_test_main_execution(
                        f"ai-domain-owner-{case_id}"
                    ),
                )
                self.assertEqual(
                    {
                        "path": "direct",
                        "profile": (
                            "review-agent"
                            if primary == "ai-code-review-refactor"
                            else "task-agent"
                        ),
                        "primary_skill": primary,
                        "layer3_skills": layer3,
                        "review_skill": "ai-code-review-refactor",
                    },
                    _projected_route(observed),
                )
                self.assertEqual(
                    1,
                    _projected_route(observed)["layer3_skills"].count(
                        "ai-product-extension"
                    ),
                )
                self.assertEqual(
                    "L4",
                    observed["route_decision"]["route_result"][
                        "execution_level"
                    ],
                )

    def test_ai_product_owner_routes_preserve_negative_and_gate_boundaries(
        self,
    ) -> None:
        cases = (
            (
                "provider-sdk-no-behavior",
                "Implement an accepted backend provider SDK version update; "
                "model, prompt, retrieval, embedding, evaluation, and AI data "
                "behavior remain unchanged.",
                "backend-change-builder",
                [],
                "ai-code-review-refactor",
            ),
            (
                "ordinary-algorithm",
                "Implement an accepted backend static search ranking algorithm "
                "with no model decision.",
                "backend-change-builder",
                [],
                "ai-code-review-refactor",
            ),
            (
                "background-only-diff",
                "Review the actual diff for background worker scheduling; model "
                "and prompt behavior remain unchanged.",
                "ai-code-review-refactor",
                ["code-review"],
                "ai-code-review-refactor",
            ),
            (
                "security-ai-diff",
                "Review the actual diff for a material tenant authorization "
                "permission bypass across a trust boundary where prompt content "
                "enters model context.",
                "security-privacy-gate",
                [
                    "ai-product-extension",
                    "permission-boundary-modeling",
                    "threat-modeling",
                ],
                "security-privacy-gate",
            ),
        )
        for case_id, prompt, primary, layer3, review in cases:
            with self.subTest(case=case_id):
                route = _projected_route(
                    ORACLE.route_with_trace(
                        prompt,
                        main_execution=_test_main_execution(
                            f"ai-domain-boundary-{case_id}"
                        ),
                    )
                )
                self.assertEqual(primary, route["primary_skill"])
                self.assertEqual(layer3, route["layer3_skills"])
                self.assertEqual(review, route["review_skill"])

        no_diff = _projected_route(
            ORACLE.route_with_trace(
                "Review prompt and model terminology without an actual diff.",
                main_execution=_test_main_execution(
                    "ai-domain-boundary-no-diff"
                ),
            )
        )
        self.assertNotEqual("ai-code-review-refactor", no_diff["primary_skill"])

        multi_surface = _projected_route(
            ORACLE.route_with_trace(
                "Implement accepted backend service and browser frontend "
                "component prompt behavior where content enters model context.",
                main_execution=_test_main_execution(
                    "ai-domain-boundary-multi-surface"
                ),
            )
        )
        self.assertEqual("analyzed", multi_surface["path"])
        self.assertEqual(
            "engineering-change-analysis",
            multi_surface["primary_skill"],
        )

    def test_ai_product_layer3_budget_preserves_exact_three_and_overflow(
        self,
    ) -> None:
        exact_three = _projected_route(
            ORACLE.route_with_trace(
                "Implement an accepted Android installed application screen "
                "accessibility behavior change where prompt content enters "
                "model context.",
                main_execution=_test_main_execution(
                    "ai-domain-budget-exact-three"
                ),
            )
        )
        self.assertEqual("direct", exact_three["path"])
        self.assertEqual(
            "installed-client-change-builder",
            exact_three["primary_skill"],
        )
        self.assertEqual(
            [
                "ai-product-extension",
                "android-platform-extension",
                "accessibility-inclusive-design",
            ],
            exact_three["layer3_skills"],
        )

        overflow = ORACLE.route_with_trace(
            "Implement an accepted Android installed application screen "
            "accessibility behavior and runtime configuration policy change "
            "where prompt content enters model context.",
            main_execution=_test_main_execution(
                "ai-domain-budget-overflow-four"
            ),
        )
        self.assertEqual(
            "foundation-layer3-overflow",
            overflow["winner_trace"]["selected_candidate"]["candidate_id"],
        )
        self.assertEqual(
            [
                "ai-product-extension",
                "android-platform-extension",
                "accessibility-inclusive-design",
                "configuration-runtime-policy",
            ],
            overflow["winner_trace"]["deferred_handoff"]["deferred_layer3"],
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            _projected_route(overflow),
        )

    def test_activation_v2_139b_compatible_mixed_preserves_ordinary_metadata(
        self,
    ) -> None:
        authority = _activation_v2_139b_authority()
        domain = "payment-trading-extension"
        foundation = "failure-diagnosis"
        domain_authority = authority["domain_authority"]
        self.assertIn(
            domain,
            authority["layer3_authority_by_primary"][
                "backend-change-builder"
            ],
        )
        self.assertIn(
            "backend-change-builder",
            domain_authority["domains_by_name"][domain]["used_by"],
        )
        self.assertIn(
            "task-agent",
            domain_authority["domains_by_name"][domain]["role_support"],
        )
        ordinary_evidence = [
            "ordinary-prefix-evidence",
            "ordinary-secondary-evidence",
        ]
        candidate = _activation_v2_139b_fixed_candidate(
            "activation-v2-139b-compatible-payment",
            primary_skill="backend-change-builder",
            profile="task-agent",
            path="direct",
            review_skill="ai-code-review-refactor",
            domains=[domain],
            foundations=[foundation],
            evidence=ordinary_evidence,
            reason="ordinary-compatible-reason",
        )
        with _activation_v2_139b_direct_enrichment_isolation():
            ORACLE._enrich_route_candidates([candidate], **authority)
        self.assertEqual(
            [domain],
            candidate.get("eligible_domain_layer3_skills"),
        )
        self.assertEqual(
            [foundation],
            candidate.get("eligible_foundation_layer3_skills"),
        )
        self.assertEqual(
            [domain, foundation],
            candidate.get("eligible_layer3_skills"),
        )
        self.assertEqual(
            candidate.get("eligible_layer3_skills"),
            candidate["layer3_skills"],
        )
        self.assertEqual(ordinary_evidence, candidate["evidence"])
        self.assertEqual(
            "ordinary-compatible-reason",
            candidate["reason"],
        )
        self.assertFalse(
            any(
                evidence.startswith("domain-layer3-incompatible:")
                for evidence in candidate["evidence"]
            )
        )
        self.assertEqual(1, candidate.get("reserved_domain_capacity"))
        self.assertFalse(candidate.get("layer3_overflow"))

    def test_activation_v2_139b_fixed_invalid_inputs_fail_closed(
        self,
    ) -> None:
        authority = _activation_v2_139b_authority()
        domain_authority = authority["domain_authority"]
        self.assertIn(
            "ai-product-extension",
            domain_authority["domains_by_professional"][
                "engineering-change-analysis"
            ],
        )
        self.assertEqual(
            ["analysis-agent", "task-agent", "review-agent"],
            domain_authority["domains_by_name"][
                "ai-product-extension"
            ]["role_support"],
        )

        def candidate(
            case_id: str,
            *,
            domains: list[str],
            foundations: list[str],
        ) -> dict[str, object]:
            return _activation_v2_139b_fixed_candidate(
                f"activation-v2-139b-invalid-{case_id}",
                primary_skill="engineering-change-analysis",
                profile="analysis-agent",
                path="analyzed",
                review_skill="architecture-impact-reviewer",
                domains=domains,
                foundations=foundations,
                evidence=[f"ordinary-invalid-{case_id}-evidence"],
            )

        unknown = candidate(
            "unknown",
            domains=["unknown-layer3-skill"],
            foundations=[],
        )
        duplicate_foundation = candidate(
            "duplicate-foundation",
            domains=[],
            foundations=[
                "repository-context-map",
                "repository-context-map",
            ],
        )
        duplicate_domain = candidate(
            "duplicate-domain",
            domains=[
                "payment-trading-extension",
                "payment-trading-extension",
            ],
            foundations=[],
        )
        missing_primary_authority = copy.deepcopy(authority)
        del missing_primary_authority["layer3_authority_by_primary"][
            "engineering-change-analysis"
        ]
        malformed_reciprocity = copy.deepcopy(authority)
        malformed_reciprocity["domain_authority"][
            "domains_by_professional"
        ]["engineering-change-analysis"].remove("ai-product-extension")
        malformed_role = copy.deepcopy(authority)
        malformed_role["domain_authority"]["domains_by_name"][
            "ai-product-extension"
        ]["role_support"] = "analysis-agent"
        extra_context_key = candidate(
            "extra-context-key",
            domains=[],
            foundations=["repository-context-map"],
        )
        extra_context_key["candidate_layer3_context"]["extra"] = True
        missing_context_key = candidate(
            "missing-context-key",
            domains=[],
            foundations=["repository-context-map"],
        )
        del missing_context_key["candidate_layer3_context"][
            "foundation_requests"
        ]
        malformed_foundation_type = candidate(
            "malformed-foundation-type",
            domains=[],
            foundations=["repository-context-map"],
        )
        malformed_foundation_type["candidate_layer3_context"][
            "foundation_requests"
        ] = "repository-context-map"
        malformed_domain_type = candidate(
            "malformed-domain-type",
            domains=["payment-trading-extension"],
            foundations=[],
        )
        malformed_domain_type["candidate_layer3_context"][
            "domain_requests"
        ] = [1]
        valid_ai = candidate(
            "authority",
            domains=["ai-product-extension"],
            foundations=[],
        )
        cases = (
            ("unknown-request", unknown, authority),
            ("duplicate-foundation", duplicate_foundation, authority),
            ("duplicate-domain", duplicate_domain, authority),
            (
                "missing-primary-authority",
                valid_ai,
                missing_primary_authority,
            ),
            ("malformed-reciprocity", valid_ai, malformed_reciprocity),
            ("malformed-role-authority", valid_ai, malformed_role),
            ("extra-context-key", extra_context_key, authority),
            ("missing-context-key", missing_context_key, authority),
            (
                "malformed-foundation-type",
                malformed_foundation_type,
                authority,
            ),
            (
                "malformed-domain-type",
                malformed_domain_type,
                authority,
            ),
        )
        for label, invalid, invalid_authority in cases:
            with self.subTest(case=label):
                with self.assertRaises(ORACLE.RoutingIntegrityError):
                    with _activation_v2_139b_direct_enrichment_isolation():
                        ORACLE._enrich_route_candidates(
                            [copy.deepcopy(invalid)],
                            **invalid_authority,
                        )

    def test_activation_v2_139a_three_prompts_remain_fallback_controls(
        self,
    ) -> None:
        controls = (
            (
                PAYMENT_FOUNDATION_PROMPT,
                _test_main_execution("activation-v2-139a-payment"),
            ),
            (
                f"{PAYMENT_FOUNDATION_PROMPT} {CLOUD_BOUNDARY_SUFFIX}",
                _test_main_execution("activation-v2-139a-payment-cloud"),
            ),
            (
                FOUR_FOUNDATION_REVIEW_PROMPT,
                _four_foundation_main_execution(),
            ),
        )
        expected_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for prompt, main_execution in controls:
            with self.subTest(prompt=prompt):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=main_execution,
                )
                selected = observed["winner_trace"]["selected_candidate"]
                self.assertEqual(
                    "repository-first-default",
                    selected["candidate_id"],
                )
                self.assertEqual("fallback-route", selected["candidate_type"])
                self.assertEqual(
                    ["no-eligible-specific-candidate"],
                    selected["evidence"],
                )
                self.assertEqual(expected_route, _projected_route(observed))

    def test_critical_unknown_explicit_grammar_binds_one_state_to_one_field(
        self,
    ) -> None:
        for field in CRITICAL_FIELDS:
            expected = [f"critical-{field}-unknown"]
            other_fields = ", ".join(
                item for item in CRITICAL_FIELDS if item != field
            )
            for state in UNKNOWN_STATES:
                for copula in ("is", "remains"):
                    expression = f"{field} {copula} {state}"
                    prompt = (
                        "Implement an accepted backend service change; "
                        f"{expression} while {other_fields} are known."
                    )
                    with self.subTest(
                        field=field,
                        form="field-first",
                        copula=copula,
                        state=state,
                    ):
                        self.assertEqual(
                            expected,
                            _critical_candidate_evidence(prompt),
                        )
                prompt = (
                    "Implement an accepted backend service change; "
                    f"{state} {field} while {other_fields} are known."
                )
                with self.subTest(
                    field=field,
                    form="state-first",
                    state=state,
                ):
                    self.assertEqual(
                        expected,
                        _critical_candidate_evidence(prompt),
                    )

    def test_critical_unknown_resolved_and_negated_forms_do_not_trigger(
        self,
    ) -> None:
        for field in CRITICAL_FIELDS:
            other_fields = ", ".join(
                item for item in CRITICAL_FIELDS if item != field
            )
            for resolved_form in RESOLVED_FIELD_FORMS:
                prompt = (
                    "Implement an accepted backend service change; "
                    f"{field} {resolved_form} while {other_fields} are known."
                )
                with self.subTest(
                    field=field,
                    resolved_form=resolved_form,
                ):
                    self.assertEqual(
                        [],
                        _critical_candidate_evidence(prompt),
                    )
            prompt = (
                "Implement an accepted backend service change; "
                f"no {field} is unknown while {other_fields} are known."
            )
            with self.subTest(field=field, resolved_form="no-field"):
                self.assertEqual([], _critical_candidate_evidence(prompt))

    def test_critical_unknown_mixed_clause_emits_exactly_one_evidence_item(
        self,
    ) -> None:
        for field in CRITICAL_FIELDS:
            known_fields = ", ".join(
                item for item in CRITICAL_FIELDS if item != field
            )
            prompt = (
                "Implement an accepted backend service change; "
                f"{field} is unknown while {known_fields} are known."
            )
            with self.subTest(field=field):
                self.assertEqual(
                    [f"critical-{field}-unknown"],
                    _critical_candidate_evidence(prompt),
                )

    def test_unrelated_unknown_text_does_not_create_critical_evidence(
        self,
    ) -> None:
        prompt = (
            "Implement an accepted backend service change for an unknown "
            "display color while owner, authority, placement, acceptance, "
            "verification, and rollback are known."
        )
        self.assertEqual([], _critical_candidate_evidence(prompt))

    def test_critical_unknown_detector_has_no_cross_field_regex_windows(
        self,
    ) -> None:
        source = inspect.getsource(ORACLE._critical_unknown_evidence)
        self.assertNotIn("{0,80}", source)
        self.assertNotIn("{0,180}", source)

    def test_139c_automatic_owner_is_fully_materialized_with_fixed_context(
        self,
    ) -> None:
        candidates = _activation_v2_139c_capture_built_candidates(
            "Implement an accepted backend service change.",
            task_id="activation-v2-139c-owner-materialization",
        )
        owner = _activation_v2_139c_candidate_by_id(
            candidates,
            "implementation-owner:backend-change-builder",
        )
        self.assertEqual(
            {
                "kind": "fixed",
                "foundation_requests": [],
                "domain_requests": [],
            },
            owner.get("candidate_layer3_context"),
            "[activation-v2-139c-owner-context] automatic owners must be "
            "materialized with one closed fixed context",
        )
        self.assertEqual(
            {
                "candidate_id": "implementation-owner:backend-change-builder",
                "candidate_type": "automatic-implementation-owner",
                "precedence": 4,
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "backend-change-builder",
                "layer3_skills": [],
                "review_skill": "ai-code-review-refactor",
                "routing_family": "backend",
            },
            {
                field: owner.get(field)
                for field in (
                    "candidate_id",
                    "candidate_type",
                    "precedence",
                    "path",
                    "profile",
                    "primary_skill",
                    "layer3_skills",
                    "review_skill",
                    "routing_family",
                )
            },
        )

    def test_139c_preparation_has_closed_context_and_materialized_contract(
        self,
    ) -> None:
        candidates = _activation_v2_139c_capture_built_candidates(
            "Prepare a backend repair before editing.",
            task_id="activation-v2-139c-preparation-materialization",
        )
        owner = _activation_v2_139c_candidate_by_id(
            candidates,
            "implementation-owner:backend-change-builder",
        )
        preparation = _activation_v2_139c_candidate_by_id(
            candidates,
            "implementation-preparation",
        )
        self.assertEqual(
            {
                "kind": "preparation",
                "domain_requests": [],
                "risk": None,
                "owners": [
                    {
                        "candidate_id": owner["candidate_id"],
                        "routing_family": "backend",
                        "primary_skill": "backend-change-builder",
                        "foundation_requests": [],
                        "review_skill": "ai-code-review-refactor",
                        "evidence": owner["evidence"],
                    }
                ],
                "support_foundations": [],
                "support_rule_ids": [],
            },
            preparation.get("candidate_layer3_context"),
            "[activation-v2-139c-preparation-context] preparation must own "
            "one closed materialized decision context",
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "ai-code-review-refactor",
            },
            {
                field: preparation.get(field)
                for field in ORACLE.ROUTE_CONTRACT_FIELDS
            },
        )

    def test_139c_artifact_review_has_fixed_context(self) -> None:
        candidate = _activation_v2_139c_candidate_by_id(
            _activation_v2_139c_capture_built_candidates(
                "Review the engineering brief and task plan.",
                task_id="activation-v2-139c-artifact-review",
            ),
            "engineering-artifact-review",
        )
        self.assertEqual(
            {
                "kind": "fixed",
                "foundation_requests": [],
                "domain_requests": [],
            },
            candidate.get("candidate_layer3_context"),
            "[activation-v2-139c-artifact-fixed] artifact review must enter "
            "enrichment through a closed fixed context",
        )
        self.assertEqual(
            {
                "path": "direct",
                "profile": "review-agent",
                "primary_skill": "engineering-artifact-review",
                "layer3_skills": [],
                "review_skill": "engineering-artifact-review",
            },
            {
                field: candidate.get(field)
                for field in ORACLE.ROUTE_CONTRACT_FIELDS
            },
        )

    def test_139c_review_generic_has_review_generic_context(self) -> None:
        candidate = _activation_v2_139c_candidate_by_id(
            _activation_v2_139c_capture_built_candidates(
                "Review the actual diff for an owner-internal refactor with "
                "behavior preserved.",
                task_id="activation-v2-139c-review-generic",
            ),
            "review-generic",
        )
        self.assertEqual(
            {
                "kind": "review-generic",
                "domain_requests": [],
                "support_foundations": ["refactoring"],
                "review_regression": False,
                "repeat_failure": False,
                "owner_internal_refactor": True,
            },
            candidate.get("candidate_layer3_context"),
            "[activation-v2-139c-review-generic-context] generic review "
            "inputs must be captured before selection",
        )
        self.assertEqual(
            ["refactoring"],
            candidate.get("layer3_skills"),
        )

    def test_139c_review_risk_has_review_risk_context(self) -> None:
        candidates = _activation_v2_139c_capture_built_candidates(
            "Review the actual diff for a material tenant authorization "
            "permission bypass across a trust boundary.",
            task_id="activation-v2-139c-review-risk",
        )
        risk = _activation_v2_139c_candidate_by_id(
            candidates,
            "review-security-risk",
        )
        expected_foundations = ORACLE._review_risk_layer3(
            "review-security-risk",
            risk["evidence"],
        )
        self.assertEqual(
            {
                "kind": "review-risk",
                "domain_requests": [],
                "risk_candidate_id": "review-security-risk",
                "risk_evidence": risk["evidence"],
                "risk_foundations": expected_foundations,
                "support_foundations": [],
                "review_regression": False,
            },
            risk.get("candidate_layer3_context"),
            "[activation-v2-139c-review-risk-context] review risk must carry "
            "one closed owner-local composition context",
        )
        self.assertEqual(expected_foundations, risk.get("layer3_skills"))

    def test_139c_critical_explicit_and_fallback_have_fixed_contexts(
        self,
    ) -> None:
        critical_candidates = _activation_v2_139c_capture_built_candidates(
            "Implement a backend service change, but the owner is unknown.",
            task_id="activation-v2-139c-critical-fixed",
        )
        explicit_candidates = _activation_v2_139c_capture_built_candidates(
            "Write migration documentation.",
            task_id="activation-v2-139c-explicit-fixed",
        )
        fallback_candidates = _activation_v2_139c_capture_built_candidates(
            "Summarize this bounded repository observation.",
            task_id="activation-v2-139c-fallback-fixed",
        )
        self.assertEqual(
            [
                "critical-unknown",
                "implementation-owner:backend-change-builder",
            ],
            [
                candidate["candidate_id"]
                for candidate in critical_candidates
            ],
            "[activation-v2-139c-critical-order] critical and owner "
            "candidates must retain source order",
        )
        self.assertEqual(
            ["migration-documentation"],
            [
                candidate["candidate_id"]
                for candidate in explicit_candidates
            ],
        )
        self.assertEqual(
            ["repository-first-default"],
            [
                candidate["candidate_id"]
                for candidate in fallback_candidates
            ],
        )
        critical = critical_candidates[0]
        self.assertEqual(
            {
                "kind": "fixed",
                "foundation_requests": ["repository-context-map"],
                "domain_requests": [],
            },
            critical.get("candidate_layer3_context"),
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                field: critical.get(field)
                for field in ORACLE.ROUTE_CONTRACT_FIELDS
            },
        )
        for candidate, foundations in (
            (explicit_candidates[0], ["documentation-generation"]),
            (fallback_candidates[0], ["repository-context-map"]),
        ):
            self.assertEqual(
                {
                    "kind": "fixed",
                    "foundation_requests": foundations,
                    "domain_requests": [],
                },
                candidate.get("candidate_layer3_context"),
            )

    def test_139c_preparation_precedence_is_candidate_local(self) -> None:
        risk = {
            "candidate_id": "review-security-risk",
            "evidence": ["material-permission-boundary"],
            "foundation_requests": [
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            "review_skill": "security-privacy-gate",
        }
        owner = {
            "candidate_id": "implementation-owner:backend-change-builder",
            "routing_family": "backend",
            "primary_skill": "backend-change-builder",
            "foundation_requests": ["failure-diagnosis"],
            "review_skill": "ai-code-review-refactor",
            "evidence": ["backend-surface"],
        }
        second_owner = {
            "candidate_id": "implementation-owner:frontend-change-builder",
            "routing_family": "frontend",
            "primary_skill": "frontend-change-builder",
            "foundation_requests": ["frontend-testing"],
            "review_skill": "ai-code-review-refactor",
            "evidence": ["frontend-surface"],
        }
        cases = (
            (
                "risk",
                {
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": risk,
                    "owners": [owner],
                    "support_foundations": ["consumer-impact-analysis"],
                    "support_rule_ids": ["support-rule"],
                },
                ["permission-boundary-modeling", "threat-modeling"],
                "security-privacy-gate",
            ),
            (
                "one-owner",
                {
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": None,
                    "owners": [owner],
                    "support_foundations": ["consumer-impact-analysis"],
                    "support_rule_ids": ["support-rule"],
                },
                ["failure-diagnosis"],
                "ai-code-review-refactor",
            ),
            (
                "multiple-owner-support",
                {
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": None,
                    "owners": [owner, second_owner],
                    "support_foundations": ["consumer-impact-analysis"],
                    "support_rule_ids": ["support-rule"],
                },
                ["consumer-impact-analysis"],
                "architecture-impact-reviewer",
            ),
            (
                "support",
                {
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": None,
                    "owners": [],
                    "support_foundations": ["consumer-impact-analysis"],
                    "support_rule_ids": ["support-rule"],
                },
                ["consumer-impact-analysis"],
                "architecture-impact-reviewer",
            ),
            (
                "repository-fallback",
                {
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": None,
                    "owners": [],
                    "support_foundations": [],
                    "support_rule_ids": [],
                },
                ["repository-context-map"],
                "architecture-impact-reviewer",
            ),
        )
        for label, context, foundations, review_skill in cases:
            candidate = _activation_v2_139c_candidate(
                "implementation-preparation",
                candidate_type="converted-cohort",
                precedence=1,
                path="analyzed",
                profile="analysis-agent",
                primary_skill="engineering-change-analysis",
                foundations=foundations,
                domains=[],
                review_skill=review_skill,
                evidence=["explicit-implementation-preparation"],
                context=context,
            )
            try:
                _activation_v2_139c_enrich([candidate])
            except ORACLE.RoutingIntegrityError as exc:
                self.fail(
                    "[activation-v2-139c-preparation-precedence] valid "
                    f"{label} context was rejected: {exc}"
                )
            self.assertEqual(
                foundations,
                candidate["eligible_foundation_layer3_skills"],
            )
            self.assertEqual(review_skill, candidate["review_skill"])

    def test_139c_preparation_owner_duplicates_and_conflicts(self) -> None:
        first = _activation_v2_139c_fixed_candidate(
            "implementation-owner:backend-change-builder",
            candidate_type="automatic-implementation-owner",
            precedence=4,
            routing_family="backend",
            foundations=["failure-diagnosis"],
            evidence=["z-owner-evidence"],
        )
        duplicate = copy.deepcopy(first)
        duplicate["evidence"] = ["a-owner-evidence"]
        _activation_v2_139c_enrich([first, duplicate])
        policy = _activation_v2_139c_implementation_policy()
        forward = ORACLE._select_route_cohort_candidate(
            [first, duplicate],
            implementation_policy=policy,
        )["selected_candidate"]
        reverse = ORACLE._select_route_cohort_candidate(
            [duplicate, first],
            implementation_policy=policy,
        )["selected_candidate"]
        self.assertEqual(
            forward,
            reverse,
            "[activation-v2-139c-owner-order] owner merging must be "
            "deterministic across provisional source order",
        )
        self.assertEqual(
            ["a-owner-evidence", "z-owner-evidence"],
            forward["evidence"],
            "[activation-v2-139c-owner-identity] equal owner identities and "
            "contracts must merge sorted unique evidence",
        )
        self.assertEqual(
            "implementation-owner:backend-change-builder",
            forward["candidate_id"],
        )
        self.assertEqual(
            ["implementation-owner:backend-change-builder"],
            forward["source_candidate_ids"],
        )

        noncanonical = copy.deepcopy(first)
        noncanonical["candidate_id"] = "implementation-owner:backend-alias"
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            ORACLE._select_route_cohort_candidate(
                [noncanonical],
                implementation_policy=policy,
            )

        foundation_conflict = _activation_v2_139c_fixed_candidate(
            "implementation-owner:backend-change-builder",
            candidate_type="automatic-implementation-owner",
            precedence=4,
            routing_family="backend",
            foundations=["regression-testing"],
            evidence=["foundation-conflict-evidence"],
        )
        _activation_v2_139c_enrich([foundation_conflict])
        foundation_result = ORACLE._select_route_cohort_candidate(
            [first, foundation_conflict],
            implementation_policy=policy,
        )["selected_candidate"]
        self.assertEqual(
            "route-contract-conflict",
            foundation_result["candidate_id"],
        )

        review_conflict = copy.deepcopy(first)
        review_conflict["review_skill"] = "quality-test-gate"
        review_result = ORACLE._select_route_cohort_candidate(
            [first, review_conflict],
            implementation_policy=policy,
        )["selected_candidate"]
        self.assertEqual(
            "route-contract-conflict",
            review_result["candidate_id"],
        )

    def test_139c_nonfixed_context_schema_fails_closed_after_valid_base(
        self,
    ) -> None:
        risk = {
            "candidate_id": "review-security-risk",
            "evidence": ["material-permission-boundary"],
            "foundation_requests": [
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            "review_skill": "security-privacy-gate",
        }
        owner = {
            "candidate_id": "implementation-owner:backend-change-builder",
            "routing_family": "backend",
            "primary_skill": "backend-change-builder",
            "foundation_requests": ["failure-diagnosis"],
            "review_skill": "ai-code-review-refactor",
            "evidence": ["backend-surface"],
        }

        def make_candidate(
            candidate_id: str,
            *,
            context: dict[str, object],
            primary: str,
            profile: str,
            path: str,
            foundations: list[str],
            domains: list[str] | None = None,
            review: str,
            evidence: list[str],
        ) -> dict[str, object]:
            return _activation_v2_139c_candidate(
                candidate_id,
                candidate_type="converted-cohort",
                precedence=ORACLE.ROUTE_COHORT_PRECEDENCE.get(
                    candidate_id,
                    2,
                ),
                path=path,
                profile=profile,
                primary_skill=primary,
                foundations=foundations,
                domains=[] if domains is None else domains,
                review_skill=review,
                evidence=evidence,
                context=context,
            )

        pristine = {
            "preparation-empty": make_candidate(
                "implementation-preparation",
                context={
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": None,
                    "owners": [],
                    "support_foundations": [],
                    "support_rule_ids": [],
                },
                primary="engineering-change-analysis",
                profile="analysis-agent",
                path="analyzed",
                foundations=["repository-context-map"],
                review="architecture-impact-reviewer",
                evidence=["preparation-valid-evidence"],
            ),
            "preparation-risk": make_candidate(
                "implementation-preparation",
                context={
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": copy.deepcopy(risk),
                    "owners": [],
                    "support_foundations": [],
                    "support_rule_ids": [],
                },
                primary="engineering-change-analysis",
                profile="analysis-agent",
                path="analyzed",
                foundations=[
                    "permission-boundary-modeling",
                    "threat-modeling",
                ],
                review="security-privacy-gate",
                evidence=["preparation-risk-valid-evidence"],
            ),
            "preparation-owner": make_candidate(
                "implementation-preparation",
                context={
                    "kind": "preparation",
                    "domain_requests": [],
                    "risk": None,
                    "owners": [copy.deepcopy(owner)],
                    "support_foundations": [],
                    "support_rule_ids": [],
                },
                primary="engineering-change-analysis",
                profile="analysis-agent",
                path="analyzed",
                foundations=["failure-diagnosis"],
                review="ai-code-review-refactor",
                evidence=["preparation-owner-valid-evidence"],
            ),
            "review-generic": make_candidate(
                "review-generic",
                context={
                    "kind": "review-generic",
                    "domain_requests": [],
                    "support_foundations": [],
                    "review_regression": False,
                    "repeat_failure": False,
                    "owner_internal_refactor": False,
                },
                primary="ai-code-review-refactor",
                profile="review-agent",
                path="direct",
                foundations=["code-review"],
                review="ai-code-review-refactor",
                evidence=["review-generic-valid-evidence"],
            ),
            "review-risk": make_candidate(
                "review-security-risk",
                context={
                    "kind": "review-risk",
                    "domain_requests": [],
                    "risk_candidate_id": "review-security-risk",
                    "risk_evidence": ["material-permission-boundary"],
                    "risk_foundations": [
                        "permission-boundary-modeling",
                        "threat-modeling",
                    ],
                    "support_foundations": [],
                    "review_regression": False,
                },
                primary="security-privacy-gate",
                profile="review-agent",
                path="direct",
                foundations=[
                    "permission-boundary-modeling",
                    "threat-modeling",
                ],
                review="security-privacy-gate",
                evidence=["material-permission-boundary"],
            ),
        }

        for label, source in pristine.items():
            candidate = copy.deepcopy(source)
            try:
                _activation_v2_139c_enrich([candidate])
            except ORACLE.RoutingIntegrityError as exc:
                self.fail(
                    "[activation-v2-139c-valid-first] valid "
                    f"{label} context was rejected: {exc}"
                )

        invalid: list[tuple[str, dict[str, object]]] = []
        for label, source in pristine.items():
            extra = copy.deepcopy(source)
            extra["candidate_layer3_context"]["extra"] = True
            invalid.append((f"{label}-extra-key", extra))
            missing = copy.deepcopy(source)
            missing["candidate_layer3_context"].pop("domain_requests")
            invalid.append((f"{label}-missing-key", missing))

        malformed_risk = copy.deepcopy(pristine["preparation-risk"])
        malformed_risk["candidate_layer3_context"]["risk"].pop("evidence")
        invalid.append(("malformed-risk", malformed_risk))

        malformed_owner = copy.deepcopy(pristine["preparation-owner"])
        malformed_owner["candidate_layer3_context"]["owners"][0].pop(
            "routing_family"
        )
        invalid.append(("malformed-owner", malformed_owner))

        multiple_risks = copy.deepcopy(pristine["preparation-risk"])
        multiple_risks["candidate_layer3_context"]["risk"] = [
            copy.deepcopy(risk),
            {
                **copy.deepcopy(risk),
                "candidate_id": "review-release-risk",
                "review_skill": "delivery-release-gate",
            },
        ]
        invalid.append(("multiple-risks", multiple_risks))

        wrong_type = copy.deepcopy(pristine["review-generic"])
        wrong_type["candidate_layer3_context"]["domain_requests"] = ()
        invalid.append(("wrong-list-type", wrong_type))

        blank_string = copy.deepcopy(pristine["preparation-owner"])
        blank_string["candidate_layer3_context"]["owners"][0][
            "evidence"
        ] = [""]
        invalid.append(("blank-owner-evidence", blank_string))

        untrimmed_string = copy.deepcopy(pristine["preparation-risk"])
        untrimmed_string["candidate_layer3_context"]["risk"][
            "evidence"
        ] = [" material-permission-boundary "]
        invalid.append(("untrimmed-risk-evidence", untrimmed_string))

        duplicate_list = copy.deepcopy(pristine["preparation-owner"])
        duplicate_list["candidate_layer3_context"]["owners"][0][
            "foundation_requests"
        ] = ["failure-diagnosis", "failure-diagnosis"]
        invalid.append(("duplicate-owner-foundations", duplicate_list))

        duplicate_support = copy.deepcopy(pristine["review-generic"])
        duplicate_support["candidate_layer3_context"][
            "support_foundations"
        ] = ["minimal-correct-implementation"] * 2
        invalid.append(("duplicate-support-foundations", duplicate_support))

        reversed_domains = make_candidate(
            "review-generic",
            context={
                "kind": "review-generic",
                "domain_requests": [
                    "cloud-platform-extension",
                    "payment-trading-extension",
                ],
                "support_foundations": [],
                "review_regression": False,
                "repeat_failure": False,
                "owner_internal_refactor": False,
            },
            primary="ai-code-review-refactor",
            profile="review-agent",
            path="direct",
            foundations=["code-review"],
            domains=[
                "cloud-platform-extension",
                "payment-trading-extension",
            ],
            review="ai-code-review-refactor",
            evidence=["review-generic-domain-order"],
        )
        invalid.append(("domain-registry-order", reversed_domains))

        overlap = make_candidate(
            "review-generic",
            context={
                "kind": "review-generic",
                "domain_requests": ["payment-trading-extension"],
                "support_foundations": ["payment-trading-extension"],
                "review_regression": False,
                "repeat_failure": False,
                "owner_internal_refactor": False,
            },
            primary="ai-code-review-refactor",
            profile="review-agent",
            path="direct",
            foundations=["payment-trading-extension"],
            domains=["payment-trading-extension"],
            review="ai-code-review-refactor",
            evidence=["review-generic-overlap"],
        )
        invalid.append(("foundation-domain-overlap", overlap))

        risk_review_contradiction = copy.deepcopy(
            pristine["preparation-risk"]
        )
        risk_review_contradiction["candidate_layer3_context"]["risk"][
            "review_skill"
        ] = "delivery-release-gate"
        invalid.append(
            ("preparation-risk-review-contradiction", risk_review_contradiction)
        )

        risk_identity_contradiction = copy.deepcopy(pristine["review-risk"])
        risk_identity_contradiction["candidate_layer3_context"][
            "risk_candidate_id"
        ] = "review-release-risk"
        invalid.append(
            ("review-risk-identity-contradiction", risk_identity_contradiction)
        )

        risk_foundation_contradiction = copy.deepcopy(
            pristine["review-risk"]
        )
        risk_foundation_contradiction["candidate_layer3_context"][
            "risk_foundations"
        ] = ["release-rollback", "version-compatibility"]
        invalid.append(
            (
                "review-risk-foundation-contradiction",
                risk_foundation_contradiction,
            )
        )

        regression_in_support = copy.deepcopy(pristine["review-generic"])
        regression_in_support["candidate_layer3_context"][
            "support_foundations"
        ] = ["regression-testing"]
        invalid.append(("regression-must-use-flag", regression_in_support))

        integer_boolean = copy.deepcopy(pristine["review-generic"])
        integer_boolean["candidate_layer3_context"][
            "review_regression"
        ] = 1
        invalid.append(("exact-boolean", integer_boolean))

        for label, candidate in invalid:
            with self.subTest(mutation=label):
                with self.assertRaises(ORACLE.RoutingIntegrityError):
                    _activation_v2_139c_enrich([candidate])

    def test_139c_review_generic_precedence(self) -> None:
        cases = (
            (
                "repeat",
                {
                    "kind": "review-generic",
                    "domain_requests": [],
                    "support_foundations": ["minimal-correct-implementation"],
                    "review_regression": True,
                    "repeat_failure": True,
                    "owner_internal_refactor": True,
                },
                ["repeat-failure-analysis"],
            ),
            (
                "refactor",
                {
                    "kind": "review-generic",
                    "domain_requests": [],
                    "support_foundations": ["minimal-correct-implementation"],
                    "review_regression": True,
                    "repeat_failure": False,
                    "owner_internal_refactor": True,
                },
                ["refactoring"],
            ),
            (
                "support-regression",
                {
                    "kind": "review-generic",
                    "domain_requests": [],
                    "support_foundations": [
                        "minimal-correct-implementation",
                    ],
                    "review_regression": True,
                    "repeat_failure": False,
                    "owner_internal_refactor": False,
                },
                [
                    "minimal-correct-implementation",
                    "regression-testing",
                ],
            ),
            (
                "regression-flag-only",
                {
                    "kind": "review-generic",
                    "domain_requests": [],
                    "support_foundations": [],
                    "review_regression": True,
                    "repeat_failure": False,
                    "owner_internal_refactor": False,
                },
                ["regression-testing"],
            ),
            (
                "default",
                {
                    "kind": "review-generic",
                    "domain_requests": [],
                    "support_foundations": [],
                    "review_regression": False,
                    "repeat_failure": False,
                    "owner_internal_refactor": False,
                },
                ["code-review"],
            ),
        )
        for label, context, foundations in cases:
            candidate = _activation_v2_139c_candidate(
                "review-generic",
                candidate_type="converted-cohort",
                precedence=3,
                path="direct",
                profile="review-agent",
                primary_skill="ai-code-review-refactor",
                foundations=foundations,
                domains=[],
                review_skill="ai-code-review-refactor",
                evidence=["actual-diff-review"],
                context=context,
            )
            try:
                _activation_v2_139c_enrich([candidate])
            except ORACLE.RoutingIntegrityError as exc:
                self.fail(
                    "[activation-v2-139c-review-generic-precedence] "
                    f"valid {label} context was rejected: {exc}"
                )
            self.assertEqual(
                foundations,
                candidate["eligible_foundation_layer3_skills"],
            )

    def test_android_accessibility_review_suppresses_generic_fallback(
        self,
    ) -> None:
        candidates = _activation_v2_139c_capture_built_candidates(
            "Review the actual diff for an Android application accessibility "
            "behavior change affecting TalkBack and Switch Access.",
            task_id="android-accessibility-review-specialist",
        )
        candidate = _activation_v2_139c_candidate_by_id(
            candidates,
            "review-generic",
        )
        self.assertEqual(
            ["accessibility-inclusive-design"],
            candidate["candidate_layer3_context"]["support_foundations"],
        )
        self.assertNotIn("code-review", candidate["layer3_skills"])

    def test_139c_review_risk_composition(self) -> None:
        foundations = [
            "permission-boundary-modeling",
            "threat-modeling",
            "regression-testing",
        ]
        context = {
            "kind": "review-risk",
            "domain_requests": [],
            "risk_candidate_id": "review-security-risk",
            "risk_evidence": ["material-permission-boundary"],
            "risk_foundations": [
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            "support_foundations": ["minimal-correct-implementation"],
            "review_regression": True,
        }
        candidate = _activation_v2_139c_candidate(
            "review-security-risk",
            candidate_type="converted-cohort",
            precedence=2,
            path="direct",
            profile="review-agent",
            primary_skill="security-privacy-gate",
            foundations=foundations,
            domains=[],
            review_skill="security-privacy-gate",
            evidence=["material-permission-boundary"],
            context=context,
        )
        try:
            _activation_v2_139c_enrich([candidate])
        except ORACLE.RoutingIntegrityError as exc:
            self.fail(
                "[activation-v2-139c-review-risk-composition] valid "
                f"review-risk context was rejected: {exc}"
            )
        self.assertEqual(
            "review-security-risk",
            candidate["candidate_layer3_context"]["risk_candidate_id"],
        )
        self.assertEqual(
            foundations,
            candidate["eligible_foundation_layer3_skills"],
        )
        self.assertNotIn(
            "minimal-correct-implementation",
            candidate["eligible_foundation_layer3_skills"],
            "[activation-v2-139c-review-risk-filter] support Foundations "
            "outside the risk owner's authority must remain local exclusions",
        )
        self.assertEqual(3, len(candidate["eligible_layer3_skills"]))
        self.assertFalse(candidate["layer3_overflow"])

    def test_139c_build_strips_only_reserved_spoof_values(self) -> None:
        def spoof(reason: str) -> dict[str, object]:
            return {
                "candidate_id": "implementation-preparation",
                "evidence": [
                    "before-evidence-byte",
                    f"{ACTIVATION_V2_139C_MARKER_PREFIX}spoof:reciprocity",
                    ACTIVATION_V2_139C_CONFLICT_REASON,
                    "after-evidence-byte",
                ],
                "candidate_layer3_context": {"kind": "spoof"},
                "eligible_foundation_layer3_skills": ["spoof-foundation"],
                "eligible_domain_layer3_skills": ["spoof-domain"],
                "eligible_layer3_skills": ["spoof-layer3"],
                "reserved_domain_capacity": 99,
                "layer3_overflow": True,
                "source_candidate_ids": ["spoof-source"],
                "reason": reason,
            }

        try:
            built = _activation_v2_139c_call_builder(
                [spoof(ACTIVATION_V2_139C_CONFLICT_REASON)],
                [],
                prompt="Prepare this repository change before editing.",
            )
        except TypeError as exc:
            self.fail(
                "[activation-v2-139c-builder-contract] builder rejected its "
                f"accepted prompt-authority contract: {exc}"
            )
        reserved_reason = _activation_v2_139c_candidate_by_id(
            built,
            "implementation-preparation",
        )
        self.assertEqual(
            [
                "before-evidence-byte",
                ACTIVATION_V2_139C_CONFLICT_REASON,
                "after-evidence-byte",
            ],
            reserved_reason["evidence"],
            "[activation-v2-139c-spoof-evidence] build must remove only "
            "reserved-prefix evidence while preserving byte value and order",
        )
        self.assertEqual(
            ACTIVATION_V2_139C_CONTEXT_SCHEMAS["preparation"],
            set(reserved_reason["candidate_layer3_context"]),
        )
        self.assertTrue(
            ACTIVATION_V2_139C_PRIVATE_FIELDS.isdisjoint(
                set(reserved_reason)
                - {"candidate_layer3_context"}
            )
        )
        self.assertNotIn("reason", reserved_reason)

        ordinary_reason_text = "ordinary-reason:Preserve-Byte-Order"
        ordinary_built = _activation_v2_139c_call_builder(
            [spoof(ordinary_reason_text)],
            [],
            prompt="Prepare this repository change before editing.",
        )
        ordinary_reason = _activation_v2_139c_candidate_by_id(
            ordinary_built,
            "implementation-preparation",
        )
        self.assertEqual(ordinary_reason_text, ordinary_reason["reason"])
        self.assertEqual(
            reserved_reason["evidence"],
            ordinary_reason["evidence"],
        )

    def test_139c_incompatible_provisional_winner_derives_contract_conflict(
        self,
    ) -> None:
        task_id = "activation-v2-139c-marker-winner"
        observed = ORACLE.route_with_trace(
            "Select regression tests and validate final changed paths where a "
            "model decision has delegated authority.",
            main_execution=_test_main_execution(task_id),
        )
        trace = observed["winner_trace"]
        selected = trace["selected_candidate"]
        self.assertEqual(
            "route-contract-conflict",
            selected["candidate_id"],
            "[activation-v2-139c-marker-winner] an incompatible provisional "
            "winner must fail closed",
        )
        marker_evidence = [
            item
            for item in selected["evidence"]
            if item.startswith(ACTIVATION_V2_139C_MARKER_PREFIX)
        ]
        self.assertEqual(
            [
                "domain-layer3-incompatible:ai-product-extension:"
                "professional-layer3",
                "domain-layer3-incompatible:ai-product-extension:reciprocity",
            ],
            marker_evidence,
            "[activation-v2-139c-marker-order] incompatibility markers must "
            "remain in deterministic reason order",
        )
        self.assertEqual(
            {
                "candidate_type": "derived-conflict",
                "reason": ACTIVATION_V2_139C_CONFLICT_REASON,
                "source_candidate_ids": [
                    "implementation-owner:quality-test-gate"
                ],
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                field: selected[field]
                for field in (
                    "candidate_type",
                    "reason",
                    "source_candidate_ids",
                    *ORACLE.ROUTE_CONTRACT_FIELDS,
                )
            },
        )
        provisional = _activation_v2_139c_candidate_by_id(
            trace["raw_candidates"],
            "implementation-owner:quality-test-gate",
        )
        self.assertEqual(
            {
                field: provisional[field]
                for field in CANDIDATE_PRESELECTION_FIELDS
            },
            {
                field: selected[field]
                for field in CANDIDATE_PRESELECTION_FIELDS
            },
            "[activation-v2-139c-conflict-private-copy] the five enrichment "
            "fields must copy into the derived trace candidate",
        )
        self.assertEqual(
            [
                {
                    "id": "route-evidence-1",
                    "kind": "routing_candidate",
                    "task_id": task_id,
                    "source_anchor": ACTIVATION_V2_139C_CONFLICT_REASON,
                }
            ],
            observed["route_decision"]["selection_evidence"][
                "task_evidence"
            ],
            "[activation-v2-139c-public-conflict-evidence] public task "
            "evidence must expose only the stable conflict reason",
        )

    def test_139c_incompatible_loser_is_local(self) -> None:
        winner = _activation_v2_139c_fixed_candidate(
            "critical-unknown",
            candidate_type="converted-cohort",
            precedence=0,
            path="analyzed",
            profile="analysis-agent",
            primary_skill="engineering-change-analysis",
            foundations=["repository-context-map"],
            review_skill="architecture-impact-reviewer",
            evidence=["critical-owner-unknown"],
        )
        loser = _activation_v2_139c_fixed_candidate(
            "implementation-owner:quality-test-gate",
            candidate_type="automatic-implementation-owner",
            precedence=4,
            primary_skill="quality-test-gate",
            domains=["ai-product-extension"],
            routing_family="test-validation",
            evidence=["ordinary-owner-evidence"],
        )
        _activation_v2_139c_enrich([winner, loser])
        selection = ORACLE._select_route_cohort_candidate(
            [loser, winner],
            implementation_policy=(
                _activation_v2_139c_implementation_policy()
            ),
        )
        self.assertEqual(
            "critical-unknown",
            selection["selected_candidate"]["candidate_id"],
        )
        self.assertNotEqual(
            "route-contract-conflict",
            selection["selected_candidate"]["candidate_id"],
        )
        excluded_owner = _activation_v2_139c_candidate_by_id(
            selection["excluded_candidates"],
            "implementation-owner:quality-test-gate",
        )
        self.assertTrue(
            any(
                item.startswith(ACTIVATION_V2_139C_MARKER_PREFIX)
                for item in excluded_owner["evidence"]
            )
        )

    def test_139c_same_contract_merge_with_marker_fails_closed(self) -> None:
        incompatible = _activation_v2_139c_fixed_candidate(
            "a-incompatible-source",
            primary_skill="quality-test-gate",
            domains=["ai-product-extension"],
            evidence=["ordinary-a-evidence"],
        )
        compatible = _activation_v2_139c_fixed_candidate(
            "z-compatible-source",
            primary_skill="quality-test-gate",
            evidence=["ordinary-z-evidence"],
        )
        _activation_v2_139c_enrich([incompatible, compatible])
        selected = ORACLE._select_route_cohort_candidate(
            [compatible, incompatible],
        )["selected_candidate"]
        self.assertEqual(
            "route-contract-conflict",
            selected["candidate_id"],
            "[activation-v2-139c-marker-merge] a same-contract merge must not "
            "launder an authorization marker",
        )
        self.assertEqual(
            ACTIVATION_V2_139C_CONFLICT_REASON,
            selected["reason"],
        )
        self.assertEqual(
            ["a-incompatible-source", "z-compatible-source"],
            selected["source_candidate_ids"],
        )

    def test_139c_ordinary_projection_uses_selected_canonical_layer3(
        self,
    ) -> None:
        captured: dict[str, object] = {}
        real_projector = ORACLE._project_route_selection

        def capture(projector, cohort_selection):
            captured.update(copy.deepcopy(cohort_selection))
            return real_projector(projector, cohort_selection)

        prompt = (
            "Implement an accepted backend payment ledger retry domain object "
            "with accounting reconciliation."
        )
        with mock.patch.object(
            ORACLE,
            "_project_route_selection",
            side_effect=capture,
        ):
            observed = ORACLE.route_with_trace(
                prompt,
                main_execution=_test_main_execution(
                    "activation-v2-139c-canonical-projection"
                ),
            )
        selected = captured["selected_candidate"]
        expected = [
            "payment-trading-extension",
            "domain-object-identification",
        ]
        self.assertEqual(
            expected,
            selected["eligible_layer3_skills"],
            "[activation-v2-139c-project-selected] projector input must "
            "already carry the selected candidate's canonical Layer 3",
        )
        self.assertEqual(
            selected["eligible_layer3_skills"],
            _projected_route(observed)["layer3_skills"],
            "[activation-v2-139c-public-selected-layer3] the public Layer 3 "
            "list must exactly copy the selected candidate's eligible list",
        )

    def test_139c_projector_copies_only_controlled_canonical_winner(
        self,
    ) -> None:
        winner = _activation_v2_139c_candidate(
            "review-generic",
            candidate_type="converted-cohort",
            precedence=3,
            path="direct",
            profile="review-agent",
            primary_skill="ai-code-review-refactor",
            foundations=["code-review"],
            domains=[],
            review_skill="ai-code-review-refactor",
            evidence=["actual-diff-review"],
            context={
                "kind": "review-generic",
                "domain_requests": [],
                "support_foundations": [],
                "review_regression": False,
                "repeat_failure": False,
                "owner_internal_refactor": False,
            },
        )
        winner.update(
            {
                "eligible_foundation_layer3_skills": ["code-review"],
                "eligible_domain_layer3_skills": [],
                "eligible_layer3_skills": ["code-review"],
                "reserved_domain_capacity": 0,
                "layer3_overflow": False,
                "source_candidate_ids": ["review-generic"],
            }
        )
        loser = _activation_v2_139c_fixed_candidate(
            "review-refactoring-change",
            path="direct",
            profile="review-agent",
            primary_skill="ai-code-review-refactor",
            foundations=["refactoring"],
            review_skill="ai-code-review-refactor",
            evidence=["refactoring-change"],
        )
        loser.update(
            {
                "eligible_foundation_layer3_skills": ["refactoring"],
                "eligible_domain_layer3_skills": [],
                "eligible_layer3_skills": ["refactoring"],
                "reserved_domain_capacity": 0,
                "layer3_overflow": False,
                "reason": "lower-precedence-than-review-generic",
            }
        )
        cohort = {
            "raw_candidates": [copy.deepcopy(winner), copy.deepcopy(loser)],
            "selected_candidate": copy.deepcopy(winner),
            "excluded_candidates": [copy.deepcopy(loser)],
        }
        self.assertTrue(
            ACTIVATION_V2_139C_PRIVATE_FIELDS
            <= set(cohort["selected_candidate"]),
            "[activation-v2-139c-projector-fixture] controlled winner must "
            "actually contain every private integration field",
        )
        with mock.patch.object(
            ORACLE,
            "_select_route_cohort_candidate",
            return_value=copy.deepcopy(cohort),
        ):
            observed = ORACLE.route_with_trace(
                "Summarize this bounded repository observation.",
                main_execution=_test_main_execution(
                    "activation-v2-139c-controlled-projector"
                ),
            )
        self.assertEqual(
            ["code-review"],
            _projected_route(observed)["layer3_skills"],
            "[activation-v2-139c-projector-winner-only] projection must copy "
            "only the controlled canonical winner",
        )
        trace = observed["winner_trace"]
        self.assertEqual(cohort["raw_candidates"], trace["raw_candidates"])
        self.assertEqual(
            cohort["excluded_candidates"],
            trace["excluded_candidates"],
        )
        refactoring_partition_rows = [
            row
            for row in observed["route_decision"]["selection_evidence"][
                "layer3_candidates"
            ]
            if row["skill"] == "refactoring"
        ]
        self.assertEqual(
            [
                {
                    "skill": "refactoring",
                    "eligible": False,
                    "evidence_ids": ["route-evidence-1"],
                    "rejection_reasons": [
                        "not-selected-by-layer3-route-evidence"
                    ],
                }
            ],
            refactoring_partition_rows,
        )
        self.assertTrue(
            ACTIVATION_V2_139C_PRIVATE_FIELDS.isdisjoint(
                set(observed["route_decision"])
                | set(observed["route_decision"]["route_result"])
            )
        )
        self.assertTrue(
            ACTIVATION_V2_139C_PRIVATE_FIELDS.isdisjoint(
                _nested_mapping_keys(
                    observed["route_decision"]["selection_evidence"]
                )
            ),
            "[activation-v2-139c-projector-private-nesting] no private "
            "candidate field may leak through nested selection evidence",
        )

    def test_139c_top_overflow_wins_before_marker_and_loser_overflow_is_local(
        self,
    ) -> None:
        overflow = _activation_v2_139c_fixed_candidate(
            "implementation-owner:quality-test-gate",
            candidate_type="automatic-implementation-owner",
            precedence=4,
            primary_skill="quality-test-gate",
            foundations=[
                "test-strategy",
                "regression-testing",
                "unit-testing",
                "integration-testing",
            ],
            domains=["ai-product-extension"],
            routing_family="test-validation",
            evidence=["ordinary-overflow-evidence"],
        )
        _activation_v2_139c_enrich([overflow])
        self.assertTrue(overflow["layer3_overflow"])
        marker_evidence = [
            item
            for item in overflow["evidence"]
            if item.startswith(ACTIVATION_V2_139C_MARKER_PREFIX)
        ]
        top = ORACLE._select_route_cohort_candidate(
            [overflow],
            implementation_policy=(
                _activation_v2_139c_implementation_policy()
            ),
        )
        selected = top["selected_candidate"]
        self.assertEqual(
            "foundation-layer3-overflow",
            selected["candidate_id"],
            "[activation-v2-139c-overflow-first] top overflow must win before "
            "authorization-marker derivation",
        )
        for surface in ("raw_candidates", "excluded_candidates"):
            retained = _activation_v2_139c_candidate_by_id(
                top[surface],
                "implementation-owner:quality-test-gate",
            )
            self.assertTrue(retained["layer3_overflow"])
            self.assertEqual(
                marker_evidence,
                [
                    item
                    for item in retained["evidence"]
                    if item.startswith(ACTIVATION_V2_139C_MARKER_PREFIX)
                ],
                "[activation-v2-139c-overflow-trace] raw and excluded "
                "overflow candidates must retain their private marker state",
            )

        winner = _activation_v2_139c_fixed_candidate(
            "critical-unknown",
            candidate_type="converted-cohort",
            precedence=0,
            path="analyzed",
            profile="analysis-agent",
            primary_skill="engineering-change-analysis",
            foundations=["repository-context-map"],
            review_skill="architecture-impact-reviewer",
            evidence=["critical-owner-unknown"],
        )
        _activation_v2_139c_enrich([winner])
        local = ORACLE._select_route_cohort_candidate(
            [overflow, winner],
            implementation_policy=(
                _activation_v2_139c_implementation_policy()
            ),
        )
        self.assertEqual(
            "critical-unknown",
            local["selected_candidate"]["candidate_id"],
        )
        lower_overflow = _activation_v2_139c_candidate_by_id(
            local["excluded_candidates"],
            "implementation-owner:quality-test-gate",
        )
        self.assertTrue(lower_overflow["layer3_overflow"])
        self.assertEqual(
            marker_evidence,
            [
                item
                for item in lower_overflow["evidence"]
                if item.startswith(ACTIVATION_V2_139C_MARKER_PREFIX)
            ],
        )
        self.assertFalse(
            local["selected_candidate"]["layer3_overflow"],
            "[activation-v2-139c-lower-overflow-local] a lower candidate's "
            "overflow state must not contaminate the selected critical route",
        )
        self.assertFalse(
            any(
                item.startswith(ACTIVATION_V2_139C_MARKER_PREFIX)
                for item in local["selected_candidate"]["evidence"]
            )
        )

    def test_139c_three_no_matcher_prompt_controls_remain_fallback(self) -> None:
        prompts = (
            PAYMENT_FOUNDATION_PROMPT,
            f"{PAYMENT_FOUNDATION_PROMPT} {CLOUD_BOUNDARY_SUFFIX}",
            FOUR_FOUNDATION_REVIEW_PROMPT,
        )
        for index, prompt in enumerate(prompts):
            with self.subTest(index=index):
                main_execution = (
                    _four_foundation_main_execution()
                    if index == 2
                    else _test_main_execution(
                        f"activation-v2-139c-fallback-{index}"
                    )
                )
                decision = ORACLE.route(
                    prompt,
                    main_execution=copy.deepcopy(main_execution),
                )
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=copy.deepcopy(main_execution),
                )
                selected = observed["winner_trace"]["selected_candidate"]
                self.assertEqual(
                    "repository-first-default",
                    selected["candidate_id"],
                )
                self.assertEqual(
                    ["no-eligible-specific-candidate"],
                    selected["evidence"],
                )
                self.assertEqual(
                    {
                        "path": "analyzed",
                        "profile": "analysis-agent",
                        "primary_skill": "engineering-change-analysis",
                        "layer3_skills": ["repository-context-map"],
                        "review_skill": "architecture-impact-reviewer",
                    },
                    _projected_route(observed),
                )
                self.assertEqual(
                    ACTIVATION_V2_139C_FALLBACK_ROUTE_BYTES,
                    _canonical_json_bytes(_projected_decision(decision)),
                    "[activation-v2-139c-frozen-route] control route bytes "
                    "must remain unchanged",
                )
                self.assertEqual(
                    ACTIVATION_V2_139C_FALLBACK_TRACE_BYTES,
                    _canonical_json_bytes(
                        {
                            "route_result": _projected_route(observed),
                            "selected_candidate": {
                                "candidate_id": selected["candidate_id"],
                                "candidate_type": selected["candidate_type"],
                                "evidence": selected["evidence"],
                            },
                        }
                    ),
                    "[activation-v2-139c-frozen-trace] control trace bytes "
                    "must remain unchanged",
                )

    def test_repair177_original_82_corpus(self) -> None:
        self.assertEqual(82, len(REPAIR177_REPAIR5_CORPUS))
        self.assertEqual(
            82,
            len({row[0] for row in REPAIR177_REPAIR5_CORPUS}),
        )
        self.assertEqual(
            82,
            len({row[1] for row in REPAIR177_REPAIR5_CORPUS}),
        )
        self.assertEqual(
            [
                *(f"P{index:02d}" for index in range(1, 20)),
                *(f"R{index:02d}" for index in range(1, 10)),
                *(f"A{index:02d}" for index in range(1, 5)),
                *(f"B{index:02d}" for index in range(1, 17)),
                *(f"C{index:02d}" for index in range(1, 5)),
                *(f"N{index:02d}" for index in range(1, 9)),
                *(f"G{index:02d}" for index in range(1, 12)),
                *(f"X{index:02d}" for index in range(1, 8)),
                *(f"W{index:02d}" for index in range(1, 5)),
            ],
            [row[0] for row in REPAIR177_REPAIR5_CORPUS],
        )
        self.assertEqual(
            {"business_matches": 19, "state_matches": 22},
            {
                "business_matches": sum(
                    row[2] for row in REPAIR177_REPAIR5_CORPUS
                ),
                "state_matches": sum(
                    row[3] for row in REPAIR177_REPAIR5_CORPUS
                ),
            },
        )

        matchers = _repair177_static_runtime_matchers()
        mismatches: list[str] = []
        for case_id, prompt, business, state in REPAIR177_REPAIR5_CORPUS:
            try:
                actual = (
                    _repair177_match(
                        prompt,
                        "business-rule-extraction",
                        matchers=matchers,
                    ),
                    _repair177_match(
                        prompt,
                        "state-machine-modeling",
                        matchers=matchers,
                    ),
                )
            except Exception as exc:
                mismatches.append(
                    "generic occurrence evaluator rejected the selected "
                    f"{case_id} row: {type(exc).__name__}: {exc}"
                )
                break
            expected = (business, state)
            if actual != expected:
                mismatches.append(
                    f"{case_id}: expected B/S={expected!r}; actual={actual!r}; "
                    f"prompt={prompt!r}"
                )
        self.assertEqual([], mismatches)

    def test_repair177_named_prompt_transition_preserves_identity_and_outcomes(
        self,
    ) -> None:
        predecessor = {
            "cases": [
                {
                    "id": "domain-invariant",
                    "prompt": REPAIR177_SSOT_OLD_PROMPT,
                },
                {
                    "id": "unrelated",
                    "prompt": "Document a markdown paragraph.",
                },
            ]
        }
        successor = copy.deepcopy(predecessor)
        successor["cases"][0]["prompt"] = REPAIR177_SSOT_NEW_PROMPT

        old_occurrences = _repair177_collect_prompt_occurrences(
            predecessor,
            source="synthetic-routing.yaml",
        )
        new_occurrences = _repair177_collect_prompt_occurrences(
            successor,
            source="synthetic-routing.yaml",
        )
        self.assertEqual(
            [(source, pointer) for source, pointer, _prompt in old_occurrences],
            [(source, pointer) for source, pointer, _prompt in new_occurrences],
        )
        changed = [
            (old, new)
            for old, new in zip(old_occurrences, new_occurrences, strict=True)
            if old != new
        ]
        self.assertEqual(
            [
                (
                    (
                        "synthetic-routing.yaml",
                        ["cases", 0, "prompt"],
                        REPAIR177_SSOT_OLD_PROMPT,
                    ),
                    (
                        "synthetic-routing.yaml",
                        ["cases", 0, "prompt"],
                        REPAIR177_SSOT_NEW_PROMPT,
                    ),
                )
            ],
            changed,
        )

        old_outcomes = [
            _foundation_matcher_matches(prompt)
            for _source, _pointer, prompt in old_occurrences
        ]
        new_outcomes = [
            _foundation_matcher_matches(prompt)
            for _source, _pointer, prompt in new_occurrences
        ]
        self.assertEqual(old_outcomes, new_outcomes)
        self.assertEqual([False, False], new_outcomes)

    def test_repair177_final_87_corpus(self) -> None:
        self.assertEqual(87, len(REPAIR177_CORPUS))
        self.assertEqual(87, len({row[0] for row in REPAIR177_CORPUS}))
        self.assertEqual(87, len({row[1] for row in REPAIR177_CORPUS}))
        self.assertEqual(
            {
                "business_matches": 25,
                "state_matches": 22,
                "business_owner_conflicts": 8,
                "state_owner_conflicts": 9,
            },
            {
                "business_matches": sum(
                    row[2] for row in REPAIR177_CORPUS
                ),
                "state_matches": sum(row[3] for row in REPAIR177_CORPUS),
                "business_owner_conflicts": sum(
                    row[4] == "owner-conflict"
                    for row in REPAIR177_CORPUS
                ),
                "state_owner_conflicts": sum(
                    row[5] == "owner-conflict"
                    for row in REPAIR177_CORPUS
                ),
            },
        )
        self.assertEqual(
            [
                "R6-29",
                "R10-N01",
                "R10-N02",
                "R10-N03",
                "R10-N04",
                "R10-N05",
                "R10-P01",
                "R10-P02",
                "R10-P03",
                "R10-P04",
                "R10-P05",
                "R10-P06",
                "R10-P07",
            ],
            [
                row[0]
                for row in REPAIR177_CORPUS
                if row[0] == "R6-29" or row[0].startswith("R10-")
            ],
            "R6-29 is moved, not duplicated; R10-N05 is the unique added row",
        )

        matchers = _repair177_static_runtime_matchers()
        mismatches: list[str] = []
        for (
            case_id,
            prompt,
            business,
            state,
            business_status,
            state_status,
        ) in REPAIR177_CORPUS:
            try:
                actual = (
                    _repair177_match(
                        prompt,
                        "business-rule-extraction",
                        matchers=matchers,
                    ),
                    _repair177_match(
                        prompt,
                        "state-machine-modeling",
                        matchers=matchers,
                    ),
                )
            except Exception as exc:
                mismatches.append(
                    "generic occurrence evaluator rejected the selected "
                    f"{case_id} row: {type(exc).__name__}: {exc}"
                )
                break
            expected = (business, state)
            if actual != expected:
                mismatches.append(
                    f"{case_id}[B={business_status},S={state_status}]: "
                    f"expected {expected!r}; actual={actual!r}; "
                    f"prompt={prompt!r}"
                )
        self.assertEqual([], mismatches)

    def test_repair177_prefix_function_object_and_modifier_authority(
        self,
    ) -> None:
        self.assertEqual(10, len(REPAIR177_REQUEST_PREFIXES))
        self.assertEqual(9, len(REPAIR177_FUNCTION_TOKENS))
        self.assertEqual(22, len(REPAIR177_BUSINESS_OBJECTS))
        self.assertEqual(20, len(REPAIR177_STATE_OBJECTS))
        self.assertEqual(4, len(REPAIR177_BUSINESS_MODIFIERS))
        self.assertEqual(6, len(REPAIR177_STATE_MODIFIERS))
        matchers = _repair177_static_runtime_matchers()

        failures: list[str] = []
        evaluator_unavailable = False

        def expect(
            label: str,
            prompt: str,
            business: bool,
            state: bool,
        ) -> None:
            nonlocal evaluator_unavailable
            if evaluator_unavailable:
                return
            try:
                actual = (
                    _repair177_match(
                        prompt,
                        "business-rule-extraction",
                        matchers=matchers,
                    ),
                    _repair177_match(
                        prompt,
                        "state-machine-modeling",
                        matchers=matchers,
                    ),
                )
            except Exception as exc:
                evaluator_unavailable = True
                failures.append(
                    "generic occurrence evaluator rejected the first selected "
                    f"matrix row {label}: {type(exc).__name__}: {exc}"
                )
                return
            if actual != (business, state):
                failures.append(
                    f"{label}: expected {(business, state)!r}, "
                    f"found {actual!r}: {prompt!r}"
                )

        for prefix in REPAIR177_REQUEST_PREFIXES:
            prefix_text = " ".join(prefix)
            business_prompt = " ".join(
                part
                for part in (
                    prefix_text,
                    "analyze domain constraints",
                )
                if part
            )
            state_prompt = " ".join(
                part
                for part in (
                    prefix_text,
                    "model business lifecycle states",
                )
                if part
            )
            expect(
                f"prefix-business-{prefix!r}",
                business_prompt,
                True,
                False,
            )
            expect(
                f"prefix-state-{prefix!r}",
                state_prompt,
                False,
                True,
            )

        function_prompts = {
            "a": "Analyze a domain invariant.",
            "an": "Analyze an existing domain invariant.",
            "the": "Analyze the domain invariant.",
            "whether": "Analyze whether a domain invariant applies.",
            "why": "Analyze why the domain invariant applies.",
            "how": "Analyze how the domain invariant applies.",
            "which": "Analyze which domain invariant applies.",
            "what": "Analyze what domain invariant applies.",
            "if": "Analyze if a domain invariant applies.",
        }
        self.assertEqual(
            set(REPAIR177_FUNCTION_TOKENS),
            set(function_prompts),
        )
        for token, prompt in function_prompts.items():
            expect(f"function-{token}", prompt, True, False)

        for action in ("analyze", "analyse", "extract"):
            for object_name in REPAIR177_BUSINESS_OBJECTS:
                expect(
                    f"business-action-object-{action}-{object_name}",
                    f"{action} {object_name}",
                    True,
                    False,
                )
        for action in ("analyze", "analyse", "model"):
            for qualifier in ("business", "domain"):
                for object_name in REPAIR177_STATE_OBJECTS:
                    expect(
                        "state-action-object-"
                        f"{action}-{qualifier}-{object_name}",
                        f"{action} {qualifier} {object_name}",
                        False,
                        True,
                    )

        for modifier in REPAIR177_BUSINESS_MODIFIERS:
            expect(
                f"business-modifier-{modifier}",
                f"Analyze {modifier} domain invariant.",
                True,
                False,
            )
        for modifier in REPAIR177_STATE_MODIFIERS:
            expect(
                f"state-modifier-{modifier}",
                f"Analyze {modifier} business lifecycle transition.",
                False,
                True,
            )

        for prompt in (
            "Analyze a new domain invariant.",
            "Analyze a revised business policy.",
            "Analyze the target domain invariant.",
            "Analyze the proposed business rule.",
            "Analyze a new domain lifecycle state.",
            "Analyze a revised business transition guard.",
        ):
            expect(f"closed-modifier-{prompt}", prompt, False, False)
        for prompt in (
            "Analyze workflow lifecycle states.",
            "Analyze product workflow transition guards.",
            "Analyze a workflow state machine.",
        ):
            expect(f"workflow-never-owner-{prompt}", prompt, False, False)
        for prompt in (
            "Analyze database domain constraints.",
            "Analyze compiler business policies.",
            "Analyze Android domain lifecycle states.",
            "Analyze React business transition guards.",
        ):
            expect(f"lexical-owner-conflict-{prompt}", prompt, False, False)
        for prompt, business, state in (
            (
                "Analyze domain lifecycle states and extract business "
                "invariants.",
                True,
                True,
            ),
            (
                "Extract business invariants and model domain lifecycle "
                "states.",
                True,
                True,
            ),
            (
                "Analyze domain forbidden lifecycle transitions.",
                False,
                True,
            ),
            (
                "Analyze a domain invariant and keep business lifecycle "
                "states unchanged.",
                True,
                False,
            ),
            (
                "Business policies remain unchanged; extract domain "
                "constraints.",
                True,
                False,
            ),
            (
                "Model domain lifecycle states and document business rules.",
                False,
                True,
            ),
            (
                "Model domain lifecycle states and implement business rules.",
                False,
                False,
            ),
        ):
            expect(
                f"precedence-{prompt}",
                prompt,
                business,
                state,
            )

        self.assertEqual([], failures)

    def test_repair177_foundation_composer_c1_through_c6(self) -> None:
        projections = _repair177_static_projections()
        self.assertEqual(REPAIR177_TARGETS, tuple(projections))

        with mock.patch.object(
            ORACLE,
            "foundation_runtime_matcher_authority",
            return_value=list(projections.values()),
        ):
            business = _repair177_route(
                "Analyze business policies.",
                "composer-c1-business",
            )
            state = _repair177_route(
                "Model the domain lifecycle states.",
                "composer-c2-state",
            )
        expected_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "domain-impact-modeler",
            "review_skill": "architecture-impact-reviewer",
        }
        for label, observed, name, activation_id in (
            (
                "C1",
                business,
                "business-rule-extraction",
                REPAIR177_ACTIVATION_IDS[0],
            ),
            (
                "C2",
                state,
                "state-machine-modeling",
                REPAIR177_ACTIVATION_IDS[1],
            ),
        ):
            winner = observed["winner_trace"]
            selected = winner["selected_candidate"]
            route_result = _repair177_final_route(observed)
            self.assertEqual(activation_id, selected["candidate_id"], label)
            self.assertEqual([name], route_result["layer3_skills"], label)
            self.assertEqual(
                expected_route,
                {
                    "path": observed["route_decision"]["path"],
                    "profile": route_result["start_profile"],
                    "primary_skill": route_result["primary_skill"],
                    "review_skill": route_result["review_skill"],
                },
                label,
            )

        normal_prompt = (
            "Analyze a domain invariant and model the domain lifecycle "
            "transition."
        )
        with mock.patch.object(
            ORACLE,
            "foundation_runtime_matcher_authority",
            return_value=list(projections.values()),
        ):
            normal = _repair177_route(
                normal_prompt,
                "composer-c3-normal-discovery",
            )

        original_build = ORACLE._build_route_candidates
        reversed_discovery: list[list[str]] = []

        def reverse_foundation_discovery(*args, **kwargs):
            candidates = original_build(*args, **kwargs)
            copied = copy.deepcopy(candidates)
            indexes = [
                index
                for index, candidate in enumerate(copied)
                if candidate.get("candidate_id")
                in REPAIR177_ACTIVATION_IDS
                and candidate.get("stage") == "foundation-activation"
                and candidate.get("precedence_class")
                == "foundation-activation"
            ]
            if len(indexes) == 2:
                replacements = [
                    copied[index]
                    for index in reversed(indexes)
                ]
                for index, replacement in zip(
                    indexes,
                    replacements,
                    strict=True,
                ):
                    copied[index] = replacement
            reversed_discovery.append(
                [copied[index]["candidate_id"] for index in indexes]
            )
            return copied

        with (
            mock.patch.object(
                ORACLE,
                "foundation_runtime_matcher_authority",
                return_value=list(projections.values()),
            ),
            mock.patch.object(
                ORACLE,
                "_build_route_candidates",
                side_effect=reverse_foundation_discovery,
            ),
        ):
            reversed_observed = _repair177_route(
                normal_prompt,
                "composer-c4-reversed-discovery",
            )
        self.assertEqual(
            [list(reversed(REPAIR177_ACTIVATION_IDS))],
            reversed_discovery,
            "C4 must intercept the complete real discovery cohort containing "
            "both target Foundation activations",
        )

        def canonical_composite(
            observed: dict[str, object],
        ) -> bytes:
            selected = observed["winner_trace"]["selected_candidate"]
            route_result = _repair177_final_route(observed)
            self.assertEqual(
                REPAIR177_COMPOSITE_ID,
                selected["candidate_id"],
            )
            projection_values = list(projections.values())
            self.assertEqual(
                {
                    "source_candidate_ids": list(
                        REPAIR177_ACTIVATION_IDS
                    ),
                    "layer3_skills": list(REPAIR177_TARGETS),
                    "semantic_atoms": [
                        atom
                        for projection in projection_values
                        for atom in projection["semantic_atoms"]
                    ],
                    "evidence": list(
                        dict.fromkeys(
                            item
                            for projection in projection_values
                            for item in (
                                *projection["matcher_evidence"],
                                "foundation-selector:"
                                f"{projection['activation_id']}",
                            )
                        )
                    ),
                },
                {
                    "source_candidate_ids": selected[
                        "source_candidate_ids"
                    ],
                    "layer3_skills": selected["layer3_skills"],
                    "semantic_atoms": selected["semantic_atoms"],
                    "evidence": selected["evidence"],
                },
                "C3/C4 composite unions and provenance must follow "
                "Foundation Registry order",
            )
            self.assertEqual(
                list(REPAIR177_TARGETS),
                route_result["layer3_skills"],
            )
            return _canonical_json_bytes(
                {
                    "selected": selected,
                    "route": _projected_route(observed),
                }
            )

        self.assertEqual(
            canonical_composite(normal),
            canonical_composite(reversed_observed),
            "C4 reversing actual discovery order must yield a byte-identical "
            "canonical composite and final route",
        )

        mutations = {
            "precedence": 4,
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "engineering-change-analysis",
            "review_skill": "quality-test-gate",
            "stage": "foundation-activation-mutated",
            "precedence_class": "analysis-mode",
        }
        self.assertEqual(
            set(REPAIR177_COMPARISON_FIELDS),
            set(mutations),
        )
        authority_failure_patterns = {
            "primary_skill": "changed identity",
            "review_skill": "undeclared selector owner binding",
        }
        structural_conflicts: list[str] = []
        for field, value in mutations.items():
            mutation_proofs: list[tuple[str, list[str]]] = []

            def mutate_second_foundation(*args, **kwargs):
                candidates = original_build(*args, **kwargs)
                copied = copy.deepcopy(candidates)
                matches = [
                    candidate
                    for candidate in copied
                    if candidate.get("candidate_id")
                    in REPAIR177_ACTIVATION_IDS
                    and candidate.get("stage") == "foundation-activation"
                    and candidate.get("precedence_class")
                    == "foundation-activation"
                ]
                if len(matches) == 2:
                    before = copy.deepcopy(matches[1])
                    matches[1][field] = value
                    mutation_proofs.append(
                        (
                            matches[1]["candidate_id"],
                            sorted(
                                key
                                for key in set(before) | set(matches[1])
                                if before.get(key) != matches[1].get(key)
                            ),
                        )
                    )
                return copied

            with (
                mock.patch.object(
                    ORACLE,
                    "foundation_runtime_matcher_authority",
                    return_value=list(projections.values()),
                ),
                mock.patch.object(
                    ORACLE,
                    "_build_route_candidates",
                    side_effect=mutate_second_foundation,
                ),
            ):
                expected_failure = authority_failure_patterns.get(field)
                if expected_failure is not None:
                    with self.assertRaisesRegex(
                        ORACLE.RoutingIntegrityError,
                        expected_failure,
                    ):
                        _repair177_route(
                            normal_prompt,
                            f"composer-c5-{field}",
                        )
                else:
                    observed = _repair177_route(
                        normal_prompt,
                        f"composer-c5-{field}",
                    )
            self.assertEqual(
                [(REPAIR177_ACTIVATION_IDS[1], [field])],
                mutation_proofs,
                f"C5 must mutate only the second target candidate's {field}",
            )
            if expected_failure is not None:
                continue
            structural_conflicts.append(field)
            selected = observed["winner_trace"]["selected_candidate"]
            self.assertEqual(
                "route-contract-conflict",
                selected["candidate_id"],
                f"C5 changed {field} must conflict",
            )
            self.assertEqual(
                "derived-conflict",
                selected["candidate_type"],
                f"C5 changed {field} must produce a typed conflict",
            )
            self.assertEqual(
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
                _projected_route(observed),
            )
            self.assertFalse(
                set(REPAIR177_TARGETS)
                & set(_repair177_final_route(observed)["layer3_skills"]),
                "C5 cannot publish a partial Foundation composition",
            )
        self.assertEqual(
            [
                "precedence",
                "path",
                "profile",
                "stage",
                "precedence_class",
            ],
            structural_conflicts,
            "C5 only ordinary route fields may reach conflict composition",
        )

        canonical_projections = list(projections.values())
        overflow_foundations = (
            "audit-evidence-integrity",
            "authentication-authorization",
            "privacy-data-lifecycle",
            "authentication-security",
        )
        admission = ORACLE.oracle_admission_authority()
        records_by_foundation = {
            record.foundations[0]: record
            for record in admission.foundation_selectors
            if len(record.foundations) == 1
            and record.foundations[0] in overflow_foundations
        }
        self.assertEqual(
            set(overflow_foundations),
            set(records_by_foundation),
            "C6 overflow must use four real admitted Foundation selectors",
        )
        overflow: list[dict[str, object]] = []
        for name in overflow_foundations:
            record = records_by_foundation[name]
            compatible_owners = [
                owner
                for owner in record.owner_bindings
                if (
                    owner.primary_skill,
                    owner.review_skill,
                )
                == ("security-privacy-gate", "security-privacy-gate")
            ]
            self.assertEqual(
                1,
                len(compatible_owners),
                f"C6 {name} must retain exactly one admitted compatible "
                "security owner pair",
            )
            owner = compatible_owners[0]
            overflow.append(
                {
                    "name": name,
                    "activation_id": record.selector_id,
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": owner.primary_skill,
                    "review_skill": owner.review_skill,
                    "semantic_atoms": [record.evidence_ids[0]],
                    "matcher_evidence": list(record.evidence_ids[:-1]),
                    "runtime_matcher": copy.deepcopy(
                        canonical_projections[0]["runtime_matcher"]
                    ),
                }
            )
        with (
            mock.patch.object(
                ORACLE,
                "foundation_runtime_matcher_authority",
                return_value=overflow,
            ),
            mock.patch.object(
                ORACLE,
                "_foundation_runtime_matcher_matches",
                return_value=True,
            ),
        ):
            observed = _repair177_route(
                normal_prompt,
                "composer-c6-overflow",
            )
        selected = observed["winner_trace"]["selected_candidate"]
        self.assertEqual(
            "foundation-layer3-overflow",
            selected["candidate_id"],
            "C6 more than three compatible activations must fail closed",
        )
        self.assertEqual(
            ["repository-context-map"],
            _repair177_final_route(observed)["layer3_skills"],
        )
        self.assertFalse(
            set(REPAIR177_TARGETS)
            & set(_repair177_final_route(observed)["layer3_skills"]),
            "C6 cannot publish a truncated or partial Foundation composition",
        )

    def test_repair177_no_fixed_layer3_bypass_same_pattern(self) -> None:
        oracle_tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
        route_impl = next(
            (
                node
                for node in oracle_tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "_route_impl"
            ),
            None,
        )
        self.assertIsNotNone(route_impl)
        if route_impl is None:
            return

        target_set = set(REPAIR177_TARGETS)
        projection_calls = 0
        forbidden_calls: list[tuple[int, list[str]]] = []
        for node in ast.walk(route_impl):
            if (
                not isinstance(node, ast.Call)
                or not isinstance(node.func, ast.Name)
                or node.func.id != "add_candidate"
                or len(node.args) < 4
            ):
                continue
            layer3_arg = node.args[3]
            literals = {
                child.value
                for child in ast.walk(layer3_arg)
                if isinstance(child, ast.Constant)
                and isinstance(child.value, str)
            }
            canonical_projection = (
                isinstance(layer3_arg, ast.List)
                and len(layer3_arg.elts) == 1
                and isinstance(layer3_arg.elts[0], ast.Subscript)
                and isinstance(layer3_arg.elts[0].value, ast.Name)
                and layer3_arg.elts[0].value.id == "projection"
                and isinstance(layer3_arg.elts[0].slice, ast.Constant)
                and layer3_arg.elts[0].slice.value == "name"
            )
            if canonical_projection:
                projection_calls += 1
            if literals & target_set:
                forbidden_calls.append(
                    (node.lineno, sorted(literals & target_set))
                )
        self.assertEqual(
            1,
            projection_calls,
            "only the canonical registry projection may construct target "
            "Foundation candidates",
        )
        self.assertEqual(
            [],
            forbidden_calls,
            "direct add_candidate calls may not contain either Repair177 "
            "Layer 3 target, regardless of guard or evidence naming",
        )

        obsolete_guards = [
            node.lineno
            for node in ast.walk(route_impl)
            if isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Constant)
                and child.value == "domain invariant"
                for child in ast.walk(node.test)
            )
        ]
        self.assertEqual(
            [],
            obsolete_guards,
            "the obsolete fixed domain-invariant branch must be absent",
        )

        canonical = VALIDATION.foundation_runtime_matcher_authority(
            load_yaml_file(FOUNDATION_REGISTRY),
            context="Repair177 projection-removal proof",
        )
        without_targets = [
            projection
            for projection in canonical
            if projection["name"] not in REPAIR177_TARGETS
        ]
        prompts = (
            "Analyze business policies.",
            "Model domain lifecycle states.",
            "Analyze a domain invariant and model the domain lifecycle "
            "transition.",
        )
        with mock.patch.object(
            ORACLE,
            "foundation_runtime_matcher_authority",
            return_value=without_targets,
        ):
            observations = [
                _repair177_route(prompt, f"projection-removed-{index}")
                for index, prompt in enumerate(prompts)
            ]
        for observed in observations:
            raw_values = _string_values(
                observed["winner_trace"]["raw_candidates"]
            )
            final_values = set(
                _repair177_final_route(observed)["layer3_skills"]
            )
            self.assertEqual(set(), target_set & raw_values)
            self.assertEqual(set(), target_set & final_values)

    def test_repair177_formal_dual_activation_route_and_trace(self) -> None:
        formal_prompt = REPAIR177_SSOT_NEW_PROMPT
        cases = load_yaml_file(CASES_PATH)["cases"]
        fixture_rows = [
            case
            for case in cases
            if case.get("id") == "domain-invariant"
        ]
        self.assertEqual(1, len(fixture_rows))
        fixture = fixture_rows[0]
        self.assertEqual(formal_prompt, fixture["prompt"])
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "domain-impact-modeler",
                "layer3_skills": [
                    "business-rule-extraction",
                    "state-machine-modeling",
                ],
                "review_skill": "architecture-impact-reviewer",
            },
            fixture["expected"],
        )

        execution = fixture["main_execution"]
        traced = ORACLE.route_with_trace(
            fixture["prompt"],
            main_execution=copy.deepcopy(execution),
        )
        public = ORACLE.route(
            fixture["prompt"],
            main_execution=copy.deepcopy(execution),
        )
        self.assertEqual(public, traced["route_decision"])
        route_result = _repair177_final_route(traced)
        self.assertEqual(
            fixture["expected"],
            {
                "path": traced["route_decision"]["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            },
        )

        raw_composites = [
            candidate
            for candidate in traced["winner_trace"]["raw_candidates"]
            if candidate.get("candidate_id") == REPAIR177_COMPOSITE_ID
        ]
        self.assertEqual(
            [
                {
                    "candidate_id": REPAIR177_COMPOSITE_ID,
                    "source_candidate_ids": list(
                        REPAIR177_ACTIVATION_IDS
                    ),
                }
            ],
            [
                {
                    "candidate_id": candidate["candidate_id"],
                    "source_candidate_ids": candidate[
                        "source_candidate_ids"
                    ],
                }
                for candidate in raw_composites
            ],
        )
        selected = traced["winner_trace"]["selected_candidate"]
        self.assertEqual(
            {
                "candidate_id": REPAIR177_COMPOSITE_ID,
                "source_candidate_ids": list(REPAIR177_ACTIVATION_IDS),
            },
            {
                "candidate_id": selected["candidate_id"],
                "source_candidate_ids": selected["source_candidate_ids"],
            },
        )

    def test_wave1a_same_binding_high_risk_specialists_merge_red(
        self,
    ) -> None:
        prompt = (
            "Independently review the accepted current source-backed "
            "Engineering Brief for a material architecture critical path "
            "that commits to a new web framework and managed datastore and "
            "changes major module ownership, public surface, dependency "
            "direction, and shared-state authority."
        )
        observed = ORACLE.route_with_trace(
            prompt,
            main_execution=copy.deepcopy(
                _four_foundation_main_execution()
            ),
        )
        authority_order = [
            skill
            for skill in ORACLE.professional_routing_authority()[
                "layer3_candidates_by_primary"
            ]["high-risk-design-review"]
            if skill
            in {
                "module-boundary-design",
                "technology-stack-selection",
            }
        ]
        self.assertEqual(
            [
                "technology-stack-selection",
                "module-boundary-design",
            ],
            authority_order,
        )
        self.assertEqual(
            {
                "path": "direct",
                "profile": "review-agent",
                "primary_skill": "high-risk-design-review",
                "layer3_skills": authority_order,
                "review_skill": "high-risk-design-review",
            },
            _projected_route(observed),
        )
        selected = observed["winner_trace"]["selected_candidate"]
        self.assertEqual(
            "merged-route-candidate",
            selected["candidate_id"],
        )
        self.assertEqual(
            [
                "high-risk-module-boundary-review",
                "high-risk-technology-stack-review",
            ],
            selected["source_candidate_ids"],
        )

    def test_wave1a_bound_specialist_merge_is_deterministic_and_fail_closed(
        self,
    ) -> None:
        first_binding = f"brb1:{'1' * 64}"
        second_binding = f"brb1:{'2' * 64}"
        module = _wave1a_bound_high_risk_candidate(
            "high-risk-module-boundary-review",
            ["module-boundary-design"],
            artifact_binding_id=first_binding,
        )
        stack = _wave1a_bound_high_risk_candidate(
            "high-risk-technology-stack-review",
            ["technology-stack-selection"],
            artifact_binding_id=first_binding,
        )
        authority = ORACLE.professional_routing_authority()[
            "layer3_candidates_by_primary"
        ]
        selection_kwargs = {
            "implementation_policy": (
                _activation_v2_139c_implementation_policy()
            ),
            "admission_authority": ORACLE.oracle_admission_authority(),
            "layer3_authority_by_primary": authority,
        }

        forward = ORACLE._select_route_cohort_candidate(
            [module, stack],
            **selection_kwargs,
        )
        reverse = ORACLE._select_route_cohort_candidate(
            [stack, module],
            **selection_kwargs,
        )
        self.assertEqual(
            _canonical_json_bytes(forward),
            _canonical_json_bytes(reverse),
        )
        selected = forward["selected_candidate"]
        self.assertEqual("merged-route-candidate", selected["candidate_id"])
        self.assertEqual(
            [
                "technology-stack-selection",
                "module-boundary-design",
            ],
            selected["layer3_skills"],
        )
        self.assertEqual(
            [
                "high-risk-module-boundary-review",
                "high-risk-technology-stack-review",
            ],
            selected["source_candidate_ids"],
        )
        self.assertNotIn(
            "artifact_binding_id",
            _nested_mapping_keys(forward),
        )
        self.assertFalse(
            any(
                value.startswith("brb1:")
                for value in _string_values(forward)
            )
        )

        single = ORACLE._select_route_cohort_candidate(
            [module],
            **selection_kwargs,
        )["selected_candidate"]
        self.assertEqual(
            {
                "candidate_id": "high-risk-module-boundary-review",
                "layer3_skills": ["module-boundary-design"],
                "primary_skill": "high-risk-design-review",
                "review_skill": "high-risk-design-review",
            },
            {
                key: single[key]
                for key in (
                    "candidate_id",
                    "layer3_skills",
                    "primary_skill",
                    "review_skill",
                )
            },
        )

        distinct_binding = copy.deepcopy(stack)
        distinct_binding["artifact_binding_id"] = second_binding
        binding_conflict = ORACLE._select_route_cohort_candidate(
            [module, distinct_binding],
            **selection_kwargs,
        )["selected_candidate"]
        self.assertEqual(
            "route-contract-conflict",
            binding_conflict["candidate_id"],
        )
        self.assertEqual(
            "artifact-binding-conflict",
            binding_conflict["reason"],
        )

        for field, forged_value in (
            ("path", "analyzed"),
            ("profile", "analysis-agent"),
            ("primary_skill", "architecture-impact-reviewer"),
            ("review_skill", "architecture-impact-reviewer"),
            ("stage", "structure"),
            ("precedence_class", "architecture-boundary"),
        ):
            forged = copy.deepcopy(stack)
            forged[field] = forged_value
            conflict = ORACLE._select_route_cohort_candidate(
                [module, forged],
                **selection_kwargs,
            )["selected_candidate"]
            self.assertEqual(
                "route-contract-conflict",
                conflict["candidate_id"],
                field,
            )
        precedence_forge = copy.deepcopy(stack)
        precedence_forge["precedence"] = 3
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            ORACLE._select_route_cohort_candidate(
                [module, precedence_forge],
                **selection_kwargs,
            )

        overflow_module = _wave1a_bound_high_risk_candidate(
            "high-risk-module-boundary-review",
            ["release-rollback", "module-boundary-design"],
            artifact_binding_id=first_binding,
        )
        overflow_stack = _wave1a_bound_high_risk_candidate(
            "high-risk-technology-stack-review",
            [
                "solution-optimality-evaluation",
                "technology-stack-selection",
            ],
            artifact_binding_id=first_binding,
        )
        overflow = ORACLE._select_route_cohort_candidate(
            [overflow_module, overflow_stack],
            **selection_kwargs,
        )["selected_candidate"]
        self.assertEqual(
            "foundation-layer3-overflow",
            overflow["candidate_id"],
        )
        self.assertEqual(
            [
                "release-rollback",
                "solution-optimality-evaluation",
                "technology-stack-selection",
                "module-boundary-design",
            ],
            overflow["eligible_layer3_skills"],
        )
        self.assertEqual(
            [
                "high-risk-module-boundary-review",
                "high-risk-technology-stack-review",
            ],
            overflow["source_candidate_ids"],
        )

    def test_wave1a_stack_boundary_and_unknown_owner_candidates_red(
        self,
    ) -> None:
        rows = {
            row["id"]: row
            for row in load_yaml_file(CASES_PATH)["cases"]
        }
        target_ids = (
            "wave1a-stack-architecture-analysis",
            "wave1a-stack-accepted-brief-review",
            "wave1a-module-boundary-major-brief-review",
            "wave1a-config-owner-unknown",
            "structure-package-supply-chain-not-reuse",
        )
        required_foundation = {
            "wave1a-stack-architecture-analysis": (
                "technology-stack-selection"
            ),
            "wave1a-stack-accepted-brief-review": (
                "technology-stack-selection"
            ),
            "wave1a-module-boundary-major-brief-review": (
                "module-boundary-design"
            ),
            "wave1a-config-owner-unknown": (
                "configuration-runtime-policy"
            ),
            "structure-package-supply-chain-not-reuse": (
                "package-dependency-management"
            ),
        }
        forbidden_foundation = {
            "structure-package-supply-chain-not-reuse": (
                "dependency-vulnerability-scanning"
            ),
        }
        failures: list[str] = []
        for case_id in target_ids:
            row = rows[case_id]
            observed = ORACLE.route_with_trace(
                row["prompt"],
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            actual = _projected_route(observed)
            expected = row["expected"]
            foundation = required_foundation[case_id]
            raw = observed["winner_trace"]["raw_candidates"]
            carriers = [
                candidate
                for candidate in raw
                if foundation in candidate.get("layer3_skills", [])
            ]
            if not carriers:
                failures.append(
                    f"{case_id}: missing-candidate:{foundation}"
                )
            elif not any(
                candidate.get("primary_skill")
                == expected["primary_skill"]
                for candidate in carriers
            ):
                failures.append(
                    f"{case_id}: missing-consumer:{foundation}:"
                    f"{expected['primary_skill']}"
                )
            if actual != expected:
                failures.append(
                    f"{case_id}: route-mismatch expected={expected!r}; "
                    f"actual={actual!r}"
                )
            forbidden = forbidden_foundation.get(case_id)
            if forbidden and any(
                forbidden in candidate.get("layer3_skills", [])
                for candidate in raw
            ):
                failures.append(
                    f"{case_id}: overtriggered-candidate:{forbidden}"
                )
        self.assertEqual([], failures)

    def test_wave1a_stack_negatives_and_internal_placement_stay_green(
        self,
    ) -> None:
        rows = {
            row["id"]: row
            for row in load_yaml_file(CASES_PATH)["cases"]
        }
        negative_ids = (
            "wave1a-stack-language-negative",
            "wave1a-stack-fixed-negative",
            "wave1a-stack-invalid-brief-negative",
            "wave1a-stack-unaccepted-brief-negative",
            "wave1a-stack-stale-brief-negative",
            "structure-owner-internal-backend-placement",
            "structure-known-generator-authority-placement",
            "structure-owner-private-business-predicate-not-placement",
            "structure-relative-business-method-homonym-not-placement",
            "structure-named-generic-anaphora-ambiguous",
            "structure-passive-private-helper-move-not-request",
            "structure-fixed-helper-placement-declaration-not-request",
            "structure-owner-private-runtime-selection-not-placement",
            "structure-put-selected-file-placement",
            "structure-move-selected-file-placement",
            "structure-placement-within-selected-destination",
            "structure-tooling-within-selected-destination",
            "structure-placement-incompatible-destinations",
            "structure-placement-multiple-anaphora",
            "structure-actual-diff-private-move",
            "structure-cross-module-public-edge",
            "structure-fixed-placement-refactor",
            "structure-fixed-placement-refactor-analysis",
            "structure-unresolved-placement-is-not-refactoring",
            "structure-module-api-explicitly-unchanged",
            "structure-filesystem-safety-not-placement",
            "structure-sdk-contract-not-reuse",
            "repository-tooling-direct",
            "t2b-backend-resolved-direct",
        )
        failures: list[str] = []
        for case_id in negative_ids:
            row = rows[case_id]
            observed = ORACLE.route_with_trace(
                row["prompt"],
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            actual = _projected_route(observed)
            if actual != row["expected"]:
                failures.append(
                    f"{case_id}: expected={row['expected']!r}; "
                    f"actual={actual!r}"
                )
            selected = {
                actual["primary_skill"],
                actual["review_skill"],
                *actual["layer3_skills"],
            }
            leaked = sorted(
                selected.intersection(row.get("excluded_skills", []))
            )
            if leaked:
                failures.append(f"{case_id}: leaked={leaked!r}")
        wave_rows = [rows[case_id] for case_id in WAVE1A_ROUTING_CASE_IDS]
        for row in wave_rows:
            actual = _projected_route(
                ORACLE.route_with_trace(
                    row["prompt"],
                    main_execution=copy.deepcopy(row["main_execution"]),
                )
            )
            if len(actual["layer3_skills"]) > 3:
                failures.append(
                    f"{row['id']}: layer3-overflow="
                    f"{actual['layer3_skills']!r}"
                )
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
