from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import inspect
import json
import sys
import unittest
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import get_type_hints
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import capability_coverage as CAPABILITY_COVERAGE  # noqa: E402
import deterministic_route_oracle as ORACLE  # noqa: E402
import validation_utils as VALIDATION  # noqa: E402


PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
FOUNDATION_REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src/registry/domain-skills.yaml"
ADMISSION_CASES = ROOT / "evals/capability-coverage/admission-cases.yaml"
ROUTING_CASES = ROOT / "evals/routing/cases.yaml"
ORACLE_PATH = ROOT / "scripts/deterministic_route_oracle.py"
VALIDATION_PATH = ROOT / "scripts/validation_utils.py"
CAPABILITY_COVERAGE_PATH = ROOT / "scripts/capability_coverage.py"

AUTHORITY_CONTRACT = "changeforge.oracle-admission-authority/v1"
FOUNDATION_PROVENANCE_DIGEST = (
    "cf33cee669ad4d53592b76a94703715097e72d2a5688c16feb4916263f436a93"
)
PRIMARY_SKILL_DIGEST = (
    "b742f0d00594d178882479f7388e235bf2b387451d164b74fc76940434498f73"
)
REVIEW_SKILL_DIGEST = (
    "39c2e2a2f513294f19b6354588d2222fbfaf9ad17921411303545ed5bb0a0b10"
)
FOUNDATION_SOURCE_COUNTS = {
    "direct-static": 45,
    "dynamic-helper-only": 21,
    "runtime-matcher": 3,
}
FOUNDATION_EFFECTS = ("selected", "domain-owned", "adjacent", "simple")
WAVE1A_FOUNDATIONS = (
    "configuration-runtime-policy",
    "dependency-vulnerability-scanning",
    "technology-stack-selection",
)
WAVE1A_FOUNDATION_TRIPLES = frozenset(
    {
        ("foundation", skill, effect)
        for skill in WAVE1A_FOUNDATIONS
        for effect in FOUNDATION_EFFECTS
    }
)
SOURCE_FOUNDATION_CANDIDATE_FIELDS = frozenset(
    {
        "candidate_id",
        "foundations",
        "evidence",
        "owner_binding",
    }
)
SOURCE_FOUNDATION_OWNER_BINDING_FIELDS = frozenset(
    {"primary_skill", "review_skill"}
)
PROFESSIONAL_EFFECTS = (
    "true-conflict",
    "multitask",
    "direct-task",
    "selected",
    "alternate-owner",
)
DOMAIN_EFFECTS = (
    "explicit",
    "unknown",
    "non-target",
    "cross-platform",
    "language-negative",
    "release-framework-mismatch",
)
PHASE2_F01_PROFESSIONAL_TRIPLES = frozenset(
    {
        ("professional", "change-documentation-gate", "selected"),
        ("professional", "change-documentation-gate", "alternate-owner"),
        ("professional", "change-documentation-gate", "direct-task"),
        ("professional", "change-documentation-gate", "multitask"),
        ("professional", "data-api-contract-changer", "selected"),
        ("professional", "data-api-contract-changer", "alternate-owner"),
        ("professional", "data-api-contract-changer", "direct-task"),
        ("professional", "data-api-contract-changer", "multitask"),
        ("professional", "data-middleware-change-builder", "selected"),
        (
            "professional",
            "data-middleware-change-builder",
            "alternate-owner",
        ),
        ("professional", "data-middleware-change-builder", "direct-task"),
        ("professional", "data-middleware-change-builder", "multitask"),
        (
            "professional",
            "data-middleware-change-builder",
            "true-conflict",
        ),
        ("professional", "delivery-release-gate", "selected"),
        ("professional", "delivery-release-gate", "alternate-owner"),
        ("professional", "delivery-release-gate", "direct-task"),
        ("professional", "delivery-release-gate", "multitask"),
        ("professional", "domain-impact-modeler", "selected"),
        ("professional", "domain-impact-modeler", "alternate-owner"),
        ("professional", "domain-impact-modeler", "direct-task"),
        ("professional", "domain-impact-modeler", "multitask"),
        ("professional", "engineering-artifact-review", "selected"),
        (
            "professional",
            "engineering-artifact-review",
            "alternate-owner",
        ),
        ("professional", "engineering-artifact-review", "direct-task"),
        ("professional", "engineering-artifact-review", "multitask"),
        ("professional", "engineering-change-analysis", "selected"),
        (
            "professional",
            "engineering-change-analysis",
            "alternate-owner",
        ),
        ("professional", "engineering-change-analysis", "direct-task"),
        ("professional", "engineering-change-analysis", "multitask"),
        ("professional", "experience-impact-modeler", "selected"),
        (
            "professional",
            "experience-impact-modeler",
            "alternate-owner",
        ),
        ("professional", "experience-impact-modeler", "direct-task"),
        ("professional", "experience-impact-modeler", "multitask"),
        ("professional", "integration-change-builder", "selected"),
        (
            "professional",
            "integration-change-builder",
            "alternate-owner",
        ),
        ("professional", "integration-change-builder", "direct-task"),
        ("professional", "integration-change-builder", "multitask"),
        ("professional", "integration-change-builder", "true-conflict"),
        ("professional", "logging-design-gate", "selected"),
        ("professional", "logging-design-gate", "alternate-owner"),
        ("professional", "logging-design-gate", "direct-task"),
        ("professional", "logging-design-gate", "multitask"),
        ("professional", "logging-design-gate", "true-conflict"),
        ("professional", "reliability-observability-gate", "selected"),
        (
            "professional",
            "reliability-observability-gate",
            "alternate-owner",
        ),
        (
            "professional",
            "reliability-observability-gate",
            "direct-task",
        ),
        ("professional", "reliability-observability-gate", "multitask"),
        ("professional", "security-privacy-gate", "selected"),
        ("professional", "security-privacy-gate", "alternate-owner"),
        ("professional", "security-privacy-gate", "direct-task"),
        ("professional", "security-privacy-gate", "multitask"),
        ("professional", "task-dag-planner", "selected"),
        ("professional", "task-dag-planner", "alternate-owner"),
        ("professional", "task-dag-planner", "direct-task"),
        ("professional", "task-dag-planner", "multitask"),
    }
)
PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES = frozenset(
    {
        ("foundation", "architecture-tradeoff-analysis", "selected"),
        (
            "foundation",
            "architecture-tradeoff-analysis",
            "domain-owned",
        ),
        ("foundation", "architecture-tradeoff-analysis", "adjacent"),
        ("foundation", "architecture-tradeoff-analysis", "simple"),
        ("foundation", "test-data-management", "selected"),
        ("foundation", "test-data-management", "domain-owned"),
        ("foundation", "test-data-management", "adjacent"),
        ("foundation", "test-data-management", "simple"),
        ("foundation", "authentication-authorization", "selected"),
        (
            "foundation",
            "authentication-authorization",
            "domain-owned",
        ),
        ("foundation", "authentication-authorization", "adjacent"),
        ("foundation", "authentication-authorization", "simple"),
        ("foundation", "repeat-failure-analysis", "selected"),
        ("foundation", "repeat-failure-analysis", "domain-owned"),
        ("foundation", "repeat-failure-analysis", "adjacent"),
        ("foundation", "repeat-failure-analysis", "simple"),
    }
)
PHASE2_F03_FOUNDATIONS = frozenset(
    {
        "acceptance-standard-definition",
        "requirement-clarification",
        "business-rule-extraction",
        "state-machine-modeling",
        "design-system-rules",
        "interaction-state-modeling",
        "task-dag-decomposition",
    }
)
PHASE2_F03_FOUNDATION_TRIPLES = frozenset(
    {
        ("foundation", skill, effect)
        for skill in PHASE2_F03_FOUNDATIONS
        for effect in FOUNDATION_EFFECTS
    }
)
PHASE2_F03_PREDECESSOR_ROW_COUNT = 241
PHASE2_F03_PREDECESSOR_ROWS_SHA256 = (
    "c9f6ac21dcbd2cd5febad3bad244e36355e6646af8d63cf69af0c4c3e50fbc97"
)
PHASE2_F03_ADJACENT_FOUNDATIONS = {
    "acceptance-standard-definition": ["requirement-clarification"],
    "requirement-clarification": ["acceptance-standard-definition"],
    "business-rule-extraction": ["state-machine-modeling"],
    "state-machine-modeling": ["business-rule-extraction"],
    "design-system-rules": ["interaction-state-modeling"],
    "interaction-state-modeling": ["design-system-rules"],
    "task-dag-decomposition": ["repository-context-map"],
}
PHASE2_F04_FOUNDATIONS = frozenset(
    {
        "code-clarity-maintainability",
        "code-review",
        "concurrency-control",
        "design-pattern-selection",
        "domain-object-identification",
        "implementation-structure-design",
        "minimal-correct-implementation",
        "module-boundary-design",
        "refactoring",
        "repository-context-map",
        "package-dependency-management",
    }
)
PHASE2_F04_FOUNDATION_TRIPLES = frozenset(
    {
        ("foundation", skill, effect)
        for skill in PHASE2_F04_FOUNDATIONS
        for effect in FOUNDATION_EFFECTS
    }
)
PHASE2_F04_PREDECESSOR_ROW_COUNT = 269
PHASE2_F04_PREDECESSOR_ROWS_SHA256 = (
    "eee1ebdf32e5fd8f484dce22366d28417a8434636311984f6d07af9b87475676"
)
PHASE2_F04_ADJACENT_FOUNDATIONS = {
    "code-clarity-maintainability": ["code-review"],
    "code-review": ["code-clarity-maintainability"],
    "concurrency-control": ["design-pattern-selection"],
    "design-pattern-selection": ["concurrency-control"],
    "domain-object-identification": [
        "business-rule-extraction",
        "state-machine-modeling",
    ],
    "implementation-structure-design": ["module-boundary-design"],
    "minimal-correct-implementation": ["refactoring"],
    "module-boundary-design": ["implementation-structure-design"],
    "refactoring": ["minimal-correct-implementation"],
    "repository-context-map": ["package-dependency-management"],
    "package-dependency-management": ["repository-context-map"],
}
PHASE2_A_GROUPS = (('A01',
  'integration-change-builder',
  'ai-code-review-refactor',
  ('consumer-impact-analysis', 'failure-contract-design')),
 ('A02',
  'reliability-observability-gate',
  'reliability-observability-gate',
  ('degradation-circuit-breaking',)),
 ('A03', 'security-privacy-gate', 'security-privacy-gate', ('web-security',)),
 ('A04',
  'integration-change-builder',
  'ai-code-review-refactor',
  ('contract-testing', 'idempotency-retry-design')),
 ('A05',
  'reliability-observability-gate',
  'reliability-observability-gate',
  ('observability', 'backup-recovery')),
 ('A06',
  'security-privacy-gate',
  'security-privacy-gate',
  ('permission-boundary-modeling',
   'threat-modeling',
   'authentication-security',
   'secret-configuration-security')),
 ('A07',
  'data-api-contract-changer',
  'architecture-impact-reviewer',
  ('api-contract-design',
   'model-boundary-mapping',
   'sdk-library-contract-design')),
 ('A08',
  'delivery-release-gate',
  'delivery-release-gate',
  ('version-compatibility', 'data-migration-design', 'release-rollback')),
 ('A09',
  'repository-tooling-change-builder',
  'ai-code-review-refactor',
  ('build-tool-professional-usage', 'targeted-validation-selection')),
 ('A10',
  'frontend-change-builder',
  'ai-code-review-refactor',
  ('state-management-design',)),
 ('A11',
  'quality-test-gate',
  'ai-code-review-refactor',
  ('regression-testing',)),
 ('A12',
  'backend-change-builder',
  'reliability-observability-gate',
  ('failure-diagnosis',)),
 ('A13',
  'logging-design-gate',
  'logging-design-gate',
  ('logging-error-handling',)),
 ('A14',
  'data-middleware-change-builder',
  'quality-test-gate',
  ('transaction-consistency',)),
 ('A15',
  'change-documentation-gate',
  'change-documentation-gate',
  ('documentation-generation',)))
PHASE2_A_FOUNDATIONS = frozenset({'api-contract-design',
           'authentication-security',
           'backup-recovery',
           'build-tool-professional-usage',
           'consumer-impact-analysis',
           'contract-testing',
           'data-migration-design',
           'degradation-circuit-breaking',
           'documentation-generation',
           'failure-contract-design',
           'failure-diagnosis',
           'idempotency-retry-design',
           'logging-error-handling',
           'model-boundary-mapping',
           'observability',
           'permission-boundary-modeling',
           'regression-testing',
           'release-rollback',
           'sdk-library-contract-design',
           'secret-configuration-security',
           'state-management-design',
           'targeted-validation-selection',
           'threat-modeling',
           'transaction-consistency',
           'version-compatibility',
           'web-security'})
PHASE2_A_FOUNDATION_TRIPLES = frozenset(
    {
        ("foundation", skill, effect)
        for skill in PHASE2_A_FOUNDATIONS
        for effect in FOUNDATION_EFFECTS
    }
)
PHASE2_A_PREDECESSOR_ROW_COUNT = 313
PHASE2_A_PREDECESSOR_ROWS_SHA256 = (
    "260ad68541c4fe4f7618249709890dd14537c75984e07c225a67073b9dc62ea2"
)
PHASE2_A_SELECTED_PRIMARY_OVERRIDES = {'consumer-impact-analysis': 'engineering-change-analysis',
 'failure-contract-design': 'engineering-change-analysis',
 'idempotency-retry-design': 'engineering-change-analysis',
 'data-migration-design': 'engineering-change-analysis',
 'failure-diagnosis': 'engineering-change-analysis'}
PHASE2_A_CUMULATIVE_ROW_COUNTS = {'A01': 321,
 'A02': 325,
 'A03': 329,
 'A04': 337,
 'A05': 345,
 'A06': 361,
 'A07': 373,
 'A08': 385,
 'A09': 393,
 'A10': 397,
 'A11': 401,
 'A12': 405,
 'A13': 409,
 'A14': 413,
 'A15': 417}
SPECIAL_SELECTORS = {
    "architecture-tradeoff-analysis": {
        "selector_id": "explicit-architecture-tradeoff",
        "primary_skill": "architecture-impact-reviewer",
        "review_skill": "architecture-impact-reviewer",
        "prompt": "Analyze an explicit architecture tradeoff.",
        "source_evidence": ("explicit-architecture-tradeoff",),
        "evidence_ids": (
            "explicit-architecture-tradeoff",
            "foundation-selector:explicit-architecture-tradeoff",
        ),
    },
    "test-data-management": {
        "selector_id": "explicit-test-data-analysis",
        "primary_skill": "quality-test-gate",
        "review_skill": "quality-test-gate",
        "prompt": "Analyze an explicit test-data decision.",
        "source_evidence": ("explicit-test-data-decision",),
        "evidence_ids": (
            "explicit-test-data-decision",
            "foundation-selector:explicit-test-data-analysis",
        ),
    },
    "authentication-authorization": {
        "selector_id": (
            "explicit-authentication-authorization-analysis"
        ),
        "primary_skill": "security-privacy-gate",
        "review_skill": "security-privacy-gate",
        "prompt": (
            "Analyze an explicit authentication and authorization handoff "
            "decision."
        ),
        "source_evidence": (
            "explicit-authentication-authorization-handoff",
        ),
        "evidence_ids": (
            "explicit-authentication-authorization-handoff",
            "foundation-selector:"
            "explicit-authentication-authorization-analysis",
        ),
    },
    "repeat-failure-analysis": {
        "selector_id": "review-repeat-failure",
        "primary_skill": "ai-code-review-refactor",
        "review_skill": "ai-code-review-refactor",
        "prompt": (
            "Review the actual diff after the same repair path failed twice."
        ),
        "source_evidence": ("actual-diff", "repeated-failure"),
        "evidence_ids": (
            "actual-diff",
            "repeated-failure",
            "foundation-selector:review-repeat-failure",
        ),
    },
}
FOUNDATION_ALIAS_PRODUCER_FIXTURES = (
    {
        "fixture_id": "alias-api-compatibility-artifact",
        "prompt": (
            "With an accepted Engineering Brief, analyze only the API "
            "compatibility artifact."
        ),
        "alias_id": "api-compatibility-artifact",
        "source_ids": ("production-release-decision",),
        "primary_skill": "data-api-contract-changer",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-backend-effects-ambiguous",
        "prompt": (
            "Implement a backend service where local filesystem mutation "
            "both changes and remains unchanged."
        ),
        "alias_id": "backend-effects-ambiguous",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-backend-layer-budget",
        "prompt": (
            "Implement a Node.js backend service that atomically replaces "
            "a local file, changes Kotlin coroutine behavior, changes .NET "
            "async disposal behavior, and chooses provider variants with a "
            "current substitution contract."
        ),
        "alias_id": "backend-layer-budget",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-data-consistency-artifact",
        "prompt": (
            "With an accepted Engineering Brief, analyze only the data "
            "consistency and recovery artifact."
        ),
        "alias_id": "data-consistency-artifact",
        "source_ids": ("distributed-workflow-analysis",),
        "primary_skill": "data-middleware-change-builder",
        "review_skill": "quality-test-gate",
    },
    {
        "fixture_id": "alias-distributed-effect-ambiguous",
        "prompt": (
            "Analyze a distributed workflow recovery where a participant "
            "effect is labeled both changes unchanged in conflicting "
            "evidence."
        ),
        "alias_id": "distributed-effect-ambiguous",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-documentation-only-change",
        "prompt": (
            "Update a source comment that mentions the provider pattern; "
            "runtime behavior, variation, lifecycle, protocol, "
            "concurrency, and extension forces are unchanged."
        ),
        "alias_id": "documentation-only-change",
        "source_ids": ("security-anti-scanner-report",),
        "primary_skill": "change-documentation-gate",
        "review_skill": "change-documentation-gate",
    },
    {
        "fixture_id": "alias-failure-diagnosis-analysis",
        "prompt": (
            "Diagnose the root cause of a failing background worker from "
            "logs tests and source evidence."
        ),
        "alias_id": "failure-diagnosis-analysis",
        "source_ids": ("incident-response-coordination",),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "reliability-observability-gate",
    },
    {
        "fixture_id": "alias-generic-security-risk",
        "prompt": "Analyze tenant authorization and object permission security.",
        "alias_id": "generic-security-risk",
        "source_ids": (
            "ssrf-url-fetch-analysis",
            "tenant-isolation-security",
        ),
        "primary_skill": "security-privacy-gate",
        "review_skill": "security-privacy-gate",
    },
    {
        "fixture_id": "alias-high-risk-architecture-plan",
        "prompt": (
            "Analyze release and rollback risk for high-risk multiple tasks "
            "after the architecture, module boundaries, and dependency "
            "graph are accepted and fixed."
        ),
        "alias_id": "high-risk-architecture-plan",
        "source_ids": ("production-release-decision",),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "high-risk-design-review",
    },
    {
        "fixture_id": "alias-installed-filesystem-ambiguous",
        "prompt": (
            "Implement an installed client where local filesystem mutation "
            "both changes and remains unchanged."
        ),
        "alias_id": "installed-filesystem-ambiguous",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-migration-documentation",
        "prompt": (
            "Update public migration documentation and validate examples; "
            "Linux graphical desktop session and D-Bus behavior remain "
            "unchanged."
        ),
        "alias_id": "migration-documentation",
        "source_ids": ("security-anti-scanner-report",),
        "primary_skill": "change-documentation-gate",
        "review_skill": "change-documentation-gate",
    },
    {
        "fixture_id": "alias-minimality-analysis",
        "prompt": (
            "Review the actual diff's complexity delete list and a new "
            "pass-through wrapper that has no current variation, lifecycle, "
            "protocol, or extension force."
        ),
        "alias_id": "minimality-analysis",
        "source_ids": ("review-minimality-change",),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-owner-blast-radius-analysis",
        "prompt": (
            "Find the owner and blast radius of ordinary deterministic "
            "search ranking; model, prompt, embedding, retrieval, and "
            "agent-tool behavior are absent."
        ),
        "alias_id": "owner-blast-radius-analysis",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-package-supply-chain-analysis",
        "prompt": (
            "Analyze whether to install a new package because of a current "
            "capability gap. There is no known vulnerability, but an "
            "incompatible-license decision, a package-provenance trust "
            "failure, and bounded package-risk acceptance require resolution; "
            "local reuse placement is fixed."
        ),
        "alias_id": "package-supply-chain-analysis",
        "source_ids": (
            "package-dependency-analysis",
            "dynamic-foundation:dependency-vulnerability-scanning",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
        "member_subset": (
            "package-dependency-management",
            "dependency-vulnerability-scanning",
        ),
    },
    {
        "fixture_id": "alias-privacy-or-token-security",
        "prompt": (
            "Analyze telemetry retention and deletion."
        ),
        "alias_id": "privacy-or-token-security",
        "source_ids": ("personal-data-lifecycle",),
        "primary_skill": "security-privacy-gate",
        "review_skill": "security-privacy-gate",
    },
    {
        "fixture_id": "alias-production-rollout-fallback",
        "prompt": (
            "Review a production rollout with compatibility stop signals "
            "and rollback."
        ),
        "alias_id": "production-rollout-fallback",
        "source_ids": ("production-release-decision",),
        "primary_skill": "delivery-release-gate",
        "review_skill": "delivery-release-gate",
    },
    {
        "fixture_id": "alias-public-api-analysis",
        "prompt": "Change a public API field with compatibility for old consumers.",
        "alias_id": "public-api-analysis",
        "source_ids": (
            "production-release-decision",
            "security-anti-input-shape",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-reliability-signal-analysis",
        "prompt": (
            "Review outage degradation SLO metrics and recovery behavior."
        ),
        "alias_id": "reliability-signal-analysis",
        "source_ids": ("security-anti-reliability-only",),
        "primary_skill": "reliability-observability-gate",
        "review_skill": "reliability-observability-gate",
    },
    {
        "fixture_id": "alias-ssrf-threat-professional-precedence",
        "prompt": (
            "Analyze an SSRF URL fetch threat for an authenticated service "
            "account, with no authorization handoff or policy change."
        ),
        "alias_id": "ssrf-threat-professional-precedence",
        "source_ids": ("ssrf-url-fetch-analysis",),
        "primary_skill": "security-privacy-gate",
        "review_skill": "security-privacy-gate",
    },
    {
        "fixture_id": "alias-test-strategy-professional-precedence",
        "prompt": (
            "Analyze which proof portfolio should cover several failure "
            "mechanisms and choose test levels and failure oracles; test data "
            "fixtures and cleanup are already fixed."
        ),
        "alias_id": "test-strategy-professional-precedence",
        "source_ids": ("foundation-activation-test-strategy",),
        "primary_skill": "quality-test-gate",
        "review_skill": "quality-test-gate",
    },
    {
        "fixture_id": "alias-repository-first-default",
        "prompt": (
            "Analyze a RAG assistant where tenant-scoped retrieval enters "
            "model context and the agent may call a side-effecting tool with "
            "delegated authority."
        ),
        "alias_id": "repository-first-default",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-repository-tooling-ambiguous",
        "prompt": (
            "Implement a repository-owned generator where local filesystem "
            "mutation both changes and remains unchanged."
        ),
        "alias_id": "repository-tooling-ambiguous",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-repository-tooling-layer-budget",
        "prompt": (
            "Implement an accepted repository-owned generator source change "
            "that atomically replaces a local file while choosing a pattern "
            "for provider variants with a current substitution contract."
        ),
        "alias_id": "repository-tooling-layer-budget",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-review-domain-pattern-only",
        "prompt": (
            "Review the actual diff that implements backend provider "
            "variants with a current substitution contract, lifecycle, and "
            "extension force."
        ),
        "alias_id": "review-domain-pattern-structure",
        "source_ids": ("design-pattern-analysis",),
        "primary_skill": "ai-code-review-refactor",
        "review_skill": "ai-code-review-refactor",
    },
    {
        "fixture_id": "alias-review-domain-object-only",
        "prompt": (
            "Review the actual diff that classifies Order as an entity and "
            "aggregate root, Money as an immutable value object, and Order "
            "as the writer authority."
        ),
        "alias_id": "review-domain-pattern-structure",
        "source_ids": ("domain-object-analysis",),
        "primary_skill": "ai-code-review-refactor",
        "review_skill": "ai-code-review-refactor",
    },
    {
        "fixture_id": "alias-review-domain-pattern-double",
        "prompt": (
            "Review the actual diff for a domain object implementation; "
            "review the actual diff for provider variants with a "
            "substitution contract."
        ),
        "alias_id": "review-domain-pattern-structure",
        "source_ids": (
            "design-pattern-analysis",
            "domain-object-analysis",
        ),
        "primary_skill": "ai-code-review-refactor",
        "review_skill": "ai-code-review-refactor",
    },
    {
        "fixture_id": "alias-review-refactoring-fixed",
        "prompt": (
            "Review the actual diff for a behavior-preserving move whose "
            "owner and final placement were already accepted."
        ),
        "alias_id": "review-refactoring-change",
        "source_ids": ("refactor-fixed-destination",),
        "primary_skill": "ai-code-review-refactor",
        "review_skill": "ai-code-review-refactor",
    },
    {
        "fixture_id": "alias-review-refactoring-owner-double",
        "prompt": (
            "Review the actual diff where a duplicate owner-private helper "
            "was consolidated and a private class moved inside the same "
            "module with behavior preserved."
        ),
        "alias_id": "review-refactoring-change",
        "source_ids": (
            "owner-internal-structure-analysis",
            "refactor-fixed-destination",
        ),
        "primary_skill": "ai-code-review-refactor",
        "review_skill": "ai-code-review-refactor",
    },
    {
        "fixture_id": "alias-secret-rotation",
        "prompt": (
            "Analyze secret rotation with no cryptographic construction."
        ),
        "alias_id": "secret-rotation",
        "source_ids": ("cryptography-key-lifecycle",),
        "primary_skill": "security-privacy-gate",
        "review_skill": "security-privacy-gate",
    },
    {
        "fixture_id": "alias-source-backed-repository-question",
        "prompt": (
            "Using repository source evidence, explain which module owns a "
            "Flutter shared installed client for concrete platform targets "
            "including iOS."
        ),
        "alias_id": "source-backed-repository-question",
        "source_ids": (
            "review-ambiguous-structure-repository-first",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "architecture-impact-reviewer",
    },
    {
        "fixture_id": "alias-experience-interaction-analysis",
        "prompt": (
            "Analyze a user flow's loading and error interaction states and "
            "state transitions; no design token or component decision is "
            "requested."
        ),
        "alias_id": "experience-interaction-analysis",
        "source_ids": ("user-flow-analysis",),
        "primary_skill": "experience-impact-modeler",
        "review_skill": "ai-code-review-refactor",
        "member_subset": ("interaction-state-modeling",),
    },
    {
        "fixture_id": "alias-experience-design-system-analysis",
        "prompt": (
            "Analyze a user flow's design tokens, components, spacing, and "
            "typography; no interaction state or transition decision is "
            "requested."
        ),
        "alias_id": "experience-design-system-analysis",
        "source_ids": ("user-flow-analysis",),
        "primary_skill": "experience-impact-modeler",
        "review_skill": "ai-code-review-refactor",
        "member_subset": ("design-system-rules",),
    },
    {
        "fixture_id": "alias-external-integration-consumer-impact-analysis",
        "prompt": (
            "Analyze an external integration downstream consumer "
            "compatibility change; retryable versus terminal outcomes and "
            "timeout cancellation meaning remain unchanged."
        ),
        "alias_id": "external-integration-consumer-impact-analysis",
        "source_ids": ("external-integration-analysis",),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "ai-code-review-refactor",
        "member_subset": ("consumer-impact-analysis",),
    },
    {
        "fixture_id": "alias-external-integration-failure-contract-analysis",
        "prompt": (
            "Analyze an external integration retryable versus terminal "
            "outcome and timeout cancellation meaning change; downstream "
            "consumer compatibility remains unchanged."
        ),
        "alias_id": "external-integration-failure-contract-analysis",
        "source_ids": ("external-integration-analysis",),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "ai-code-review-refactor",
        "member_subset": ("failure-contract-design",),
    },
    {
        "fixture_id": "alias-incident-response-coordination-observability",
        "prompt": (
            "Coordinate an active multi-responder incident with command, "
            "mitigation, communications, and handoff."
        ),
        "alias_id": "incident-response-coordination-observability",
        "source_ids": (
            "incident-response-coordination",
            "security-anti-reliability-only",
        ),
        "primary_skill": "incident-response-coordinator",
        "review_skill": "reliability-observability-gate",
        "member_subset": ("failure-diagnosis", "observability"),
    },
    {
        "fixture_id": "alias-database-migration-coexistence-rollback",
        "prompt": (
            "Plan a database migration with backfill coexistence and "
            "rollback."
        ),
        "alias_id": "database-migration-coexistence-rollback",
        "source_ids": (
            "database-migration-analysis",
            "distributed-workflow-analysis",
            "production-release-decision",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "delivery-release-gate",
        "member_subset": (
            "data-migration-design",
            "transaction-consistency",
            "release-rollback",
        ),
    },
    {
        "fixture_id": "alias-cache-stampede-reliability-controls",
        "prompt": (
            "Analyze Redis cache stampede contention with single-flight "
            "refresh safe degradation and hot-key observability."
        ),
        "alias_id": "cache-stampede-reliability-controls",
        "source_ids": (
            "cache-stampede-analysis",
            "security-anti-reliability-only",
        ),
        "primary_skill": "engineering-change-analysis",
        "review_skill": "reliability-observability-gate",
        "member_subset": (
            "concurrency-control",
            "degradation-circuit-breaking",
            "observability",
        ),
    },
)
INACTIVE_NO_SELECTOR_FOUNDATIONS = (
    "algorithm-data-structure-selection",
    "language-runtime-selection",
    "solution-optimality-evaluation",
)
INACTIVE_NEGATIVE_PROMPTS = {
    "algorithm-data-structure-selection": (
        "Review a draft algorithm and data structure note without an "
        "accepted current source-backed Engineering Brief."
    ),
    "language-runtime-selection": (
        "Review language runtime documentation without an accepted bound "
        "Engineering Brief."
    ),
    "solution-optimality-evaluation": (
        "Compare solution alternatives in an unaccepted draft note."
    ),
}
DYNAMIC_SELECTOR_HELPERS = (
    "_implementation_owner_layer3",
    "_review_risk_layer3",
    "_build_route_candidates",
)
PRIVATE_FOUNDATION_OWNER_SPEC = "_FoundationSelectorOwnerBindingSpec"
PRIVATE_FOUNDATION_SPEC = "_FoundationSelectorSpec"
PRIVATE_FOUNDATION_OWNER_FIELDS = (
    "primary_skill",
    "review_skill",
)
PRIVATE_FOUNDATION_SPEC_FIELDS = (
    "selector_id",
    "foundations",
    "evidence_ids",
    "owner_bindings",
)
PRIVATE_FOUNDATION_OWNER_ANNOTATIONS = (
    ("primary_skill", ("name", "str")),
    ("review_skill", ("name", "str")),
)
PRIVATE_FOUNDATION_SPEC_ANNOTATIONS = (
    ("selector_id", ("name", "str")),
    ("foundations", ("tuple", "str", "...")),
    ("evidence_ids", ("tuple", "str", "...")),
    (
        "owner_bindings",
        (
            "tuple",
            PRIVATE_FOUNDATION_OWNER_SPEC,
            "...",
        ),
    ),
)


def _lf_grammar(values: Iterable[str]) -> bytes:
    return "".join(f"{value}\n" for value in sorted(values)).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _function_node(path: Path, name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one function {name!r}; actual={len(matches)}"
        )
    return matches[0]


def _function_from_tree(
    tree: ast.Module,
    name: str,
) -> ast.FunctionDef:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one function {name!r}; actual={len(matches)}"
        )
    return matches[0]


def _scope_nodes(node: ast.AST) -> list[ast.AST]:
    """Walk one lexical scope without interpreting nested definitions."""

    observed: list[ast.AST] = []

    def visit(current: ast.AST) -> None:
        observed.append(current)
        for child in ast.iter_child_nodes(current):
            if isinstance(
                child,
                (
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.Lambda,
                ),
            ):
                continue
            visit(child)

    visit(node)
    return observed


def _annotation_shape(node: ast.AST) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return ("name", node.id)
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "tuple"
        and isinstance(node.slice, ast.Tuple)
        and len(node.slice.elts) == 2
        and isinstance(node.slice.elts[0], ast.Name)
        and isinstance(node.slice.elts[1], ast.Constant)
        and node.slice.elts[1].value is Ellipsis
    ):
        return ("tuple", node.slice.elts[0].id, "...")
    return None


def _private_spec_class(
    tree: ast.Module,
    name: str,
    annotations: tuple[tuple[str, tuple[str, ...]], ...],
) -> ast.ClassDef:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"[R0-private-spec-declaration] expected exactly one {name}; "
            f"actual={len(matches)}"
        )
    declaration = matches[0]
    declared_fields = tuple(
        statement.target.id
        for statement in declaration.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    )
    fields = tuple(field for field, _annotation in annotations)
    if declared_fields != fields:
        raise AssertionError(
            f"[R0-private-spec-schema] {name} fields must be {fields!r}; "
            f"actual={declared_fields!r}"
        )
    declared_annotations = tuple(
        (
            statement.target.id,
            _annotation_shape(statement.annotation),
        )
        for statement in declaration.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    )
    if declared_annotations != annotations:
        raise AssertionError(
            f"[R0-private-spec-schema] {name} annotations must be "
            f"{annotations!r}; actual={declared_annotations!r}"
        )
    defaults = [
        statement.target.id
        for statement in declaration.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.value is not None
    ]
    if defaults:
        raise AssertionError(
            f"[R0-private-spec-schema] {name} fields must not define "
            f"defaults or default factories; actual={defaults!r}"
        )
    dataclass_decorators = [
        decorator
        for decorator in declaration.decorator_list
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "dataclass"
    ]
    if len(dataclass_decorators) != 1:
        raise AssertionError(
            f"[R0-private-spec-schema] {name} must use one dataclass "
            "decorator"
        )
    options = {
        keyword.arg: keyword.value
        for keyword in dataclass_decorators[0].keywords
        if keyword.arg is not None
    }
    if not all(
        isinstance(options.get(option), ast.Constant)
        and options[option].value is True
        for option in ("frozen", "slots")
    ):
        raise AssertionError(
            f"[R0-private-spec-schema] {name} must be frozen and slotted"
        )
    return declaration


def _constructor_aliases(
    tree: ast.Module,
    constructor_name: str,
) -> set[str]:
    aliases = {constructor_name}
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, (ast.Assign, ast.AnnAssign))
    ]
    changed = True
    while changed:
        changed = False
        for statement in assignments:
            value = statement.value
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            if (
                isinstance(value, ast.Name)
                and value.id in aliases
            ):
                for target in targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id not in aliases
                    ):
                        aliases.add(target.id)
                        changed = True
    return aliases


def _constructor_fields(
    call: ast.Call,
    fields: tuple[str, ...],
    *,
    label: str,
) -> dict[str, ast.AST]:
    if len(call.args) > len(fields) or any(
        keyword.arg is None for keyword in call.keywords
    ):
        raise AssertionError(
            f"[R0-private-spec-literal] {label} constructor shape is invalid"
        )
    values = {
        field: value
        for field, value in zip(fields, call.args, strict=False)
    }
    for keyword in call.keywords:
        assert keyword.arg is not None
        if keyword.arg not in fields or keyword.arg in values:
            raise AssertionError(
                f"[R0-private-spec-literal] {label} constructor field "
                f"{keyword.arg!r} is duplicate or unknown"
            )
        values[keyword.arg] = keyword.value
    if set(values) != set(fields):
        raise AssertionError(
            f"[R0-private-spec-literal] {label} constructor must define "
            f"{fields!r}"
        )
    return values


def _literal_sequence(node: ast.AST) -> tuple[ast.AST, ...] | None:
    while (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "tuple"}
        and len(node.args) == 1
        and not node.keywords
    ):
        node = node.args[0]
    if isinstance(node, (ast.List, ast.Tuple)):
        return tuple(node.elts)
    return None


def _literal_text(node: ast.AST) -> str | None:
    return (
        node.value
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        else None
    )


def _literal_text_sequence(node: ast.AST) -> tuple[str, ...] | None:
    values = _literal_sequence(node)
    if values is None:
        return None
    text = tuple(_literal_text(value) for value in values)
    return (
        tuple(value for value in text if value is not None)
        if all(value is not None for value in text)
        else None
    )


def _decode_owner_binding(
    node: ast.AST,
    *,
    owner_aliases: set[str],
) -> tuple[str, str] | None:
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in owner_aliases
    ):
        return None
    values = _constructor_fields(
        node,
        PRIVATE_FOUNDATION_OWNER_FIELDS,
        label=PRIVATE_FOUNDATION_OWNER_SPEC,
    )
    primary = _literal_text(values["primary_skill"])
    review = _literal_text(values["review_skill"])
    if primary is None or review is None:
        return None
    return primary, review


def _decode_foundation_spec(
    call: ast.Call,
    *,
    owner_aliases: set[str],
) -> dict[str, object] | None:
    values = _constructor_fields(
        call,
        PRIVATE_FOUNDATION_SPEC_FIELDS,
        label=PRIVATE_FOUNDATION_SPEC,
    )
    selector_id = _literal_text(values["selector_id"])
    foundations = _literal_text_sequence(values["foundations"])
    evidence_ids = _literal_text_sequence(values["evidence_ids"])
    owner_nodes = _literal_sequence(values["owner_bindings"])
    if (
        selector_id is None
        or foundations is None
        or evidence_ids is None
        or owner_nodes is None
    ):
        return None
    owner_bindings = tuple(
        _decode_owner_binding(node, owner_aliases=owner_aliases)
        for node in owner_nodes
    )
    if any(binding is None for binding in owner_bindings):
        return None
    normalized_bindings = tuple(
        binding
        for binding in owner_bindings
        if binding is not None
    )
    text_groups = (
        ("selector_id", (selector_id,)),
        ("foundations", foundations),
        ("evidence_ids", evidence_ids),
        (
            "owner_bindings",
            tuple(
                item
                for binding in normalized_bindings
                for item in binding
            ),
        ),
    )
    for label, items in text_groups:
        if any(
            not item
            or item != item.strip()
            for item in items
        ):
            raise AssertionError(
                f"[R0-private-spec-literal] {label} must contain nonblank "
                "trimmed text"
            )
    if (
        not foundations
        or len(foundations) != len(set(foundations))
        or not evidence_ids
        or len(evidence_ids) != len(set(evidence_ids))
        or not normalized_bindings
        or len(normalized_bindings) != len(set(normalized_bindings))
    ):
        raise AssertionError(
            "[R0-private-spec-literal] selector tuples and owner pairs must "
            "be nonempty and unique"
        )
    terminal = f"foundation-selector:{selector_id}"
    if evidence_ids[-1] != terminal or evidence_ids.count(terminal) != 1:
        raise AssertionError(
            "[R0-private-spec-evidence] selector terminal marker must occur "
            "exactly once at the end"
        )
    return {
        "selector_id": selector_id,
        "foundations": foundations,
        "evidence_ids": evidence_ids,
        "owner_bindings": normalized_bindings,
        "line": call.lineno,
        "column": call.col_offset,
    }


def _scope_assignments(node: ast.AST) -> dict[str, ast.AST]:
    candidates: dict[str, list[ast.AST]] = {}
    for child in _scope_nodes(node):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    candidates.setdefault(target.id, []).append(child.value)
        elif (
            isinstance(child, ast.AnnAssign)
            and isinstance(child.target, ast.Name)
            and child.value is not None
        ):
            candidates.setdefault(child.target.id, []).append(child.value)
        elif (
            isinstance(child, ast.For)
            and isinstance(child.target, ast.Name)
        ):
            candidates.setdefault(child.target.id, []).append(child.iter)
    return {
        name: values[0]
        for name, values in candidates.items()
        if len(values) == 1
    }


def _resolve_expression(
    node: ast.AST,
    assignments: Mapping[str, ast.AST],
    *,
    seen: frozenset[str] = frozenset(),
) -> ast.AST:
    if (
        isinstance(node, ast.Name)
        and node.id in assignments
        and node.id not in seen
    ):
        return _resolve_expression(
            assignments[node.id],
            assignments,
            seen=seen | {node.id},
        )
    return node


def _projection(
    node: ast.AST,
    root: str,
    assignments: Mapping[str, ast.AST],
) -> tuple[tuple[str, ...], tuple[int, ...]] | None:
    node = _resolve_expression(node, assignments)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "tuple"}
        and len(node.args) == 1
        and not node.keywords
    ):
        node = _resolve_expression(node.args[0], assignments)

    attributes: list[str] = []
    indexes: list[int] = []
    while True:
        if not (
            isinstance(node, ast.Name)
            and node.id == root
        ):
            node = _resolve_expression(node, assignments)
        if isinstance(node, ast.Attribute):
            attributes.append(node.attr)
            node = node.value
            continue
        if isinstance(node, ast.Subscript):
            index = node.slice
            if (
                not isinstance(index, ast.Constant)
                or type(index.value) is not int
                or index.value < 0
            ):
                return None
            indexes.append(index.value)
            node = node.value
            continue
        break
    if not isinstance(node, ast.Name) or node.id != root:
        return None
    return tuple(reversed(attributes)), tuple(reversed(indexes))


def _call_keyword(call: ast.Call, name: str) -> ast.AST | None:
    matches = [
        keyword.value
        for keyword in call.keywords
        if keyword.arg == name
    ]
    return matches[0] if len(matches) == 1 else None


def _spec_driven_add_candidate(
    call: ast.Call,
    root: str,
    assignments: Mapping[str, ast.AST],
) -> int | None:
    if (
        not isinstance(call.func, ast.Name)
        or call.func.id != "add_candidate"
        or len(call.args) < 5
    ):
        return None
    selector = _call_keyword(call, "rule_id")
    evidence = _call_keyword(call, "match_evidence")
    if selector is None or evidence is None:
        return None
    expected = {
        "selector": (("selector_id",), ()),
        "foundations": (("foundations",), ()),
        "evidence": (("evidence_ids",), ()),
    }
    actual = {
        "selector": _projection(selector, root, assignments),
        "foundations": _projection(call.args[3], root, assignments),
        "evidence": _projection(evidence, root, assignments),
    }
    if actual != expected:
        return None
    primary = _projection(call.args[2], root, assignments)
    review = _projection(call.args[4], root, assignments)
    if (
        primary is None
        or review is None
        or primary[0] != ("owner_bindings", "primary_skill")
        or review[0] != ("owner_bindings", "review_skill")
        or len(primary[1]) != 1
        or primary[1] != review[1]
    ):
        return None
    return primary[1][0]


def _call_arguments(
    call: ast.Call,
    function: ast.FunctionDef,
) -> dict[str, ast.AST]:
    parameters = [
        *function.args.posonlyargs,
        *function.args.args,
    ]
    if len(call.args) > len(parameters) or any(
        keyword.arg is None for keyword in call.keywords
    ):
        return {}
    values = {
        parameter.arg: value
        for parameter, value in zip(
            parameters,
            call.args,
            strict=False,
        )
    }
    parameter_names = {parameter.arg for parameter in parameters}
    for keyword in call.keywords:
        assert keyword.arg is not None
        if (
            keyword.arg not in parameter_names
            or keyword.arg in values
        ):
            return {}
        values[keyword.arg] = keyword.value
    return values


def _spec_wrapper_binding(
    function: ast.FunctionDef,
) -> tuple[str, int] | None:
    calls = [
        node
        for node in _scope_nodes(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "add_candidate"
    ]
    if len(calls) != 1:
        return None
    assignments = _scope_assignments(function)
    parameter_names = [
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
        )
    ]
    matches = [
        (parameter, owner_index)
        for parameter in parameter_names
        if (
            owner_index := _spec_driven_add_candidate(
                calls[0],
                parameter,
                assignments,
            )
        )
        is not None
    ]
    return matches[0] if len(matches) == 1 else None


def _spec_nodes_from_expression(
    node: ast.AST,
    assignments: Mapping[str, ast.AST],
    literal_calls: Mapping[int, dict[str, object]],
    *,
    seen: frozenset[str] = frozenset(),
) -> set[int]:
    if id(node) in literal_calls:
        return {id(node)}
    if isinstance(node, ast.Name):
        if node.id in seen or node.id not in assignments:
            return set()
        return _spec_nodes_from_expression(
            assignments[node.id],
            assignments,
            literal_calls,
            seen=seen | {node.id},
        )
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return {
            spec_id
            for element in node.elts
            for spec_id in _spec_nodes_from_expression(
                element.value
                if isinstance(element, ast.Starred)
                else element,
                assignments,
                literal_calls,
                seen=seen,
            )
        }
    return set()


def _local_add_candidate_builder(
    route_impl: ast.FunctionDef,
) -> ast.FunctionDef:
    builders = [
        node
        for node in route_impl.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "add_candidate"
    ]
    if len(builders) != 1:
        raise AssertionError(
            "[R0-private-spec-binding] expected one local add_candidate "
            "builder"
        )
    return builders[0]


def _candidate_builder_mapping(
    builder: ast.FunctionDef,
) -> dict[str, ast.AST]:
    candidate_mappings = [
        node
        for node in ast.walk(builder)
        if isinstance(node, ast.Dict)
        and any(
            isinstance(key, ast.Constant)
            and key.value == "candidate_id"
            for key in node.keys
        )
    ]
    if len(candidate_mappings) != 1:
        raise AssertionError(
            "[R0-private-spec-binding] add_candidate must build one closed "
            "candidate mapping"
        )
    return {
        key.value: value
        for key, value in zip(
            candidate_mappings[0].keys,
            candidate_mappings[0].values,
            strict=True,
        )
        if isinstance(key, ast.Constant)
        and isinstance(key.value, str)
    }


def _exact_parameter_projection(
    node: ast.AST,
    parameter: str,
    assignments: Mapping[str, ast.AST],
    *,
    sequence_wrapper: bool,
) -> bool:
    node = _resolve_expression(node, assignments)
    if isinstance(node, ast.Name):
        return node.id == parameter
    if not sequence_wrapper:
        return False
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in {"list", "tuple"}
        or len(node.args) != 1
        or node.keywords
    ):
        return False
    value = _resolve_expression(node.args[0], assignments)
    return isinstance(value, ast.Name) and value.id == parameter


def _simple_candidate_builder_contract(
    route_impl: ast.FunctionDef,
) -> None:
    builder = _local_add_candidate_builder(route_impl)
    mapping = _candidate_builder_mapping(builder)
    assignments = _scope_assignments(builder)
    required = {
        "candidate_id": ("rule_id", False),
        "rule_id": ("rule_id", False),
        "evidence": ("match_evidence", True),
        "primary_skill": ("primary", False),
        "layer3_skills": ("layer3", True),
        "review_skill": ("review", False),
    }
    for field, (parameter, sequence_wrapper) in required.items():
        value = mapping.get(field)
        if value is None or not _exact_parameter_projection(
            value,
            parameter,
            assignments,
            sequence_wrapper=sequence_wrapper,
        ):
            raise AssertionError(
                f"[R0-private-spec-binding] candidate {field!r} must derive "
                f"exactly from {parameter!r}"
            )


def _add_candidate_foundation_payload(
    route_impl: ast.FunctionDef,
) -> tuple[int, str]:
    builder = _local_add_candidate_builder(route_impl)
    mapping = _candidate_builder_mapping(builder)
    layer3_value = mapping.get("layer3_skills")
    if layer3_value is None:
        raise AssertionError(
            "[R0-raw-foundation-emitter] add_candidate lacks layer3_skills"
        )
    assignments = _scope_assignments(builder)
    parameters = [
        *builder.args.posonlyargs,
        *builder.args.args,
    ]
    matches = [
        (index, parameter.arg)
        for index, parameter in enumerate(parameters)
        if _exact_parameter_projection(
            layer3_value,
            parameter.arg,
            assignments,
            sequence_wrapper=True,
        )
    ]
    if len(matches) != 1:
        raise AssertionError(
            "[R0-raw-foundation-emitter] expected exactly one Foundation "
            "payload parameter"
        )
    return matches[0]


def _foundation_selector_spec_contracts(
    tree: ast.Module,
) -> list[dict[str, object]]:
    _private_spec_class(
        tree,
        PRIVATE_FOUNDATION_SPEC,
        PRIVATE_FOUNDATION_SPEC_ANNOTATIONS,
    )
    _private_spec_class(
        tree,
        PRIVATE_FOUNDATION_OWNER_SPEC,
        PRIVATE_FOUNDATION_OWNER_ANNOTATIONS,
    )
    owner_aliases = _constructor_aliases(
        tree,
        PRIVATE_FOUNDATION_OWNER_SPEC,
    )
    spec_aliases = _constructor_aliases(
        tree,
        PRIVATE_FOUNDATION_SPEC,
    )
    literal_calls: dict[int, dict[str, object]] = {}
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.func.id not in spec_aliases
        ):
            continue
        decoded = _decode_foundation_spec(
            node,
            owner_aliases=owner_aliases,
        )
        if decoded is not None:
            literal_calls[id(node)] = decoded
    if not literal_calls:
        raise AssertionError(
            "[R0-private-spec-literal] no literal Foundation selector specs"
        )

    route_impl = _function_from_tree(tree, "_route_impl")
    _simple_candidate_builder_contract(route_impl)
    assignments = _scope_assignments(route_impl)
    nested_functions = {
        node.name: node
        for node in route_impl.body
        if isinstance(node, ast.FunctionDef)
        and node.name != "add_candidate"
    }
    wrapper_bindings = {
        name: binding
        for name, function in nested_functions.items()
        if (binding := _spec_wrapper_binding(function)) is not None
    }
    emissions: dict[int, list[int]] = {
        spec_id: [] for spec_id in literal_calls
    }
    for call in (
        node
        for node in _scope_nodes(route_impl)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    ):
        if call.func.id == "add_candidate":
            roots = [
                name
                for name, expression in assignments.items()
                if _spec_nodes_from_expression(
                    expression,
                    assignments,
                    literal_calls,
                )
            ]
            for root in roots:
                owner_index = _spec_driven_add_candidate(
                    call,
                    root,
                    assignments,
                )
                if owner_index is None:
                    continue
                for spec_id in _spec_nodes_from_expression(
                    ast.Name(id=root, ctx=ast.Load()),
                    assignments,
                    literal_calls,
                ):
                    emissions[spec_id].append(owner_index)
            continue
        binding = wrapper_bindings.get(call.func.id)
        function = nested_functions.get(call.func.id)
        if binding is None or function is None:
            continue
        spec_parameter, owner_index = binding
        arguments = _call_arguments(call, function)
        spec_argument = arguments.get(spec_parameter)
        if spec_argument is None:
            continue
        for spec_id in _spec_nodes_from_expression(
            spec_argument,
            assignments,
            literal_calls,
        ):
            emissions[spec_id].append(owner_index)

    contracts: list[dict[str, object]] = []
    for spec_id, decoded in literal_calls.items():
        owner_indexes = emissions[spec_id]
        owner_bindings = decoded["owner_bindings"]
        assert isinstance(owner_bindings, tuple)
        if not owner_indexes:
            selector_id = decoded["selector_id"]
            alias_owner_pairs = {
                (primary_skill, review_skill)
                for bindings
                in ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS.values()
                for source_ids, primary_skill, review_skill in bindings
                if selector_id in source_ids
            }
            owner_indexes = [
                index
                for index, owner_binding in enumerate(owner_bindings)
                if owner_binding in alias_owner_pairs
            ]
        if len(owner_indexes) != 1:
            raise AssertionError(
                "[R0-private-spec-binding] every literal spec must reach "
                "add_candidate exactly once through a direct, one-helper, "
                "or declared alias-only "
                f"edge; selector={decoded['selector_id']!r}; "
                f"actual={len(owner_indexes)}"
            )
        owner_index = owner_indexes[0]
        if owner_index >= len(owner_bindings):
            raise AssertionError(
                "[R0-private-spec-binding] effective owner index is outside "
                f"selector {decoded['selector_id']!r}"
            )
        primary, review = owner_bindings[owner_index]
        contracts.append(
            {
                **decoded,
                "primary_skill": primary,
                "review_skill": review,
            }
        )
    contracts.sort(
        key=lambda contract: (
            contract["line"],
            contract["column"],
        )
    )
    selector_ids = [
        contract["selector_id"] for contract in contracts
    ]
    foundations = [
        foundation
        for contract in contracts
        for foundation in contract["foundations"]
    ]
    if len(selector_ids) != len(set(selector_ids)):
        raise AssertionError(
            "[R0-private-spec-uniqueness] duplicate selector ownership"
        )
    if len(foundations) != len(set(foundations)):
        raise AssertionError(
            "[R0-private-spec-uniqueness] duplicate Foundation ownership"
        )
    return contracts


def _literal_strings(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
    }


def _keyword_literal(call: ast.Call, name: str) -> str | None:
    value = next(
        (
            keyword.value
            for keyword in call.keywords
            if keyword.arg == name
        ),
        None,
    )
    return (
        value.value
        if isinstance(value, ast.Constant)
        and isinstance(value.value, str)
        else None
    )


def _ordered_foundation_literals(
    node: ast.AST,
    foundation_names: set[str],
) -> tuple[str, ...]:
    observed: list[str] = []
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and child.value in foundation_names
            and child.value not in observed
        ):
            observed.append(child.value)
    return tuple(observed)


def _raw_foundation_add_candidate_emissions(
    tree: ast.Module,
    foundation_names: set[str],
) -> list[tuple[int, str | None, tuple[str, ...]]]:
    route_impl = _function_from_tree(tree, "_route_impl")
    payload_index, payload_name = _add_candidate_foundation_payload(
        route_impl
    )
    emissions: list[tuple[int, str | None, tuple[str, ...]]] = []
    for node in ast.walk(route_impl):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.func.id != "add_candidate"
        ):
            continue
        positional = (
            node.args[payload_index]
            if len(node.args) > payload_index
            else None
        )
        keyword_values = [
            keyword.value
            for keyword in node.keywords
            if keyword.arg == payload_name
        ]
        if positional is not None and keyword_values:
            raise AssertionError(
                "[R0-raw-foundation-emitter] add_candidate Foundation "
                "payload is bound by both position and keyword"
            )
        if len(keyword_values) > 1:
            raise AssertionError(
                "[R0-raw-foundation-emitter] add_candidate Foundation "
                "payload keyword is duplicated"
            )
        payload = (
            positional
            if positional is not None
            else keyword_values[0]
            if keyword_values
            else None
        )
        if payload is None:
            continue
        literal_foundations = _ordered_foundation_literals(
            payload,
            foundation_names,
        )
        if literal_foundations:
            emissions.append(
                (
                    node.lineno,
                    _keyword_literal(node, "rule_id"),
                    literal_foundations,
                )
            )
    return emissions


def _private_spec_is_declared(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ClassDef)
        and node.name == PRIVATE_FOUNDATION_SPEC
        for node in tree.body
    )


def _direct_foundation_inventory_from_tree(
    tree: ast.Module,
    foundation_names: set[str],
) -> set[str]:
    if _private_spec_is_declared(tree):
        return {
            foundation
            for contract in _foundation_selector_spec_contracts(tree)
            for foundation in contract["foundations"]
        }
    return {
        foundation
        for _line, _selector_id, foundations
        in _raw_foundation_add_candidate_emissions(
            tree,
            foundation_names,
        )
        for foundation in foundations
    }


def _source_selector_inventory(
    foundation_registry: object,
) -> dict[str, tuple[str, ...]]:
    rows = (
        foundation_registry.get("foundation_skills")
        if isinstance(foundation_registry, dict)
        else None
    )
    if not isinstance(rows, list):
        raise AssertionError("Foundation registry lacks foundation_skills")
    foundation_names = {
        row["name"]
        for row in rows
        if isinstance(row, dict)
        and row.get("delivery_scope") == "product"
        and isinstance(row.get("name"), str)
    }
    tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
    direct = _direct_foundation_inventory_from_tree(
        tree,
        foundation_names,
    )
    helper_literals = set().union(
        *(
            _literal_strings(_function_node(ORACLE_PATH, symbol))
            & foundation_names
            for symbol in DYNAMIC_SELECTOR_HELPERS
        )
    )
    runtime = {
        projection["name"]
        for projection in VALIDATION.foundation_runtime_matcher_authority(
            copy.deepcopy(foundation_registry),
            context="source-derived R0 selector inventory",
        )
    }
    dynamic = helper_literals - direct - runtime
    return {
        "direct-static": tuple(sorted(direct)),
        "dynamic-helper-only": tuple(sorted(dynamic)),
        "runtime-matcher": tuple(sorted(runtime)),
    }


def _source_professional_inventory(
    professional_registry: object,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    rows = (
        professional_registry.get("professional_skills")
        if isinstance(professional_registry, dict)
        else None
    )
    if not isinstance(rows, list):
        raise AssertionError(
            "Professional registry lacks professional_skills"
        )
    primary = tuple(
        sorted(
            row["name"]
            for row in rows
            if isinstance(row, dict)
            and row.get("task_routable") is True
            and row.get("name") != "high-risk-design-review"
        )
    )
    review = tuple(
        sorted(
            row["name"]
            for row in rows
            if isinstance(row, dict)
            and row.get("task_routable") is True
            and "review-agent" in row.get("role_support", [])
        )
    )
    return primary, review


def _direct_selector_contract(
    foundation: str,
    foundation_names: set[str],
) -> dict[str, object]:
    del foundation_names
    tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
    matches = [
        contract
        for contract in _foundation_selector_spec_contracts(tree)
        if foundation in contract["foundations"]
    ]
    if len(matches) != 1:
        raise AssertionError(
            "expected exactly one private spec source for Foundation "
            f"{foundation!r}; actual={len(matches)}"
        )
    contract = matches[0]
    evidence_ids = contract["evidence_ids"]
    assert isinstance(evidence_ids, tuple)
    return {
        "selector_id": contract["selector_id"],
        "foundations": contract["foundations"],
        "primary_skill": contract["primary_skill"],
        "review_skill": contract["review_skill"],
        "source_evidence": evidence_ids[:-1],
        "evidence_ids": evidence_ids,
        "line": contract["line"],
    }


def _is_ordered_subsequence(
    expected: Sequence[str],
    actual: Sequence[str],
) -> bool:
    remaining = iter(actual)
    return all(
        any(item == expected_item for item in remaining)
        for expected_item in expected
    )


def _carries_source_foundation_candidates(
    candidate: Mapping[str, object],
) -> bool:
    return "source_foundation_candidates" in candidate


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _contains_mapping_key(value: object, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(
            _contains_mapping_key(item, target)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_mapping_key(item, target) for item in value)
    return False


def _private_spec_fixture_source() -> str:
    return """
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class _FoundationSelectorOwnerBindingSpec:
    primary_skill: str
    review_skill: str

@dataclass(frozen=True, slots=True)
class _FoundationSelectorSpec:
    selector_id: str
    foundations: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    owner_bindings: tuple[_FoundationSelectorOwnerBindingSpec, ...]

OwnerAlias = _FoundationSelectorOwnerBindingSpec
SpecAlias = _FoundationSelectorSpec

def _route_impl():
    def add_candidate(
        path,
        profile,
        primary,
        layer3,
        review,
        *,
        rule_id,
        match_evidence,
    ):
        candidate = {
            "candidate_id": rule_id,
            "candidate_type": "explicit-route",
            "evidence": list(match_evidence),
            "path": path,
            "profile": profile,
            "primary_skill": primary,
            "layer3_skills": list(layer3),
            "review_skill": review,
            "rule_id": rule_id,
        }
        consume(candidate)

    def deliver(unit):
        binding = unit.owner_bindings[0]
        add_candidate(
            "analyzed",
            "analysis-agent",
            binding.primary_skill,
            list(unit.foundations),
            binding.review_skill,
            match_evidence=tuple(unit.evidence_ids),
            rule_id=unit.selector_id,
        )

    first = SpecAlias(
        owner_bindings=(
            OwnerAlias(
                review_skill="review-a",
                primary_skill="primary-a",
            ),
        ),
        evidence_ids=(
            "evidence-a",
            "foundation-selector:selector-a",
        ),
        foundations=list(("foundation-a", "foundation-c")),
        selector_id="selector-a",
    )
    first_alias = first
    deliver(first_alias)
    second = _FoundationSelectorSpec(
        "selector-b",
        ("foundation-b",),
        tuple(("evidence-b", "foundation-selector:selector-b")),
        tuple([
            _FoundationSelectorOwnerBindingSpec(
                "primary-b",
                "review-b",
            ),
        ]),
    )
    deliver(second)
    third = SpecAlias(
        "selector-d",
        ("foundation-d",),
        (
            "evidence-d",
            "foundation-selector:selector-d",
        ),
        (
            OwnerAlias("primary-d", "review-d"),
        ),
    )
    third_binding = third.owner_bindings[0]
    add_candidate(
        "analyzed",
        "analysis-agent",
        third_binding.primary_skill,
        list(third.foundations),
        third_binding.review_skill,
        rule_id=third.selector_id,
        match_evidence=list(third.evidence_ids),
    )
"""


def _main_execution(task_id: str) -> dict[str, object]:
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


class FoundationSelectorAuthorityRedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.professional = VALIDATION.load_yaml_file(PROFESSIONAL_REGISTRY)
        cls.foundation = VALIDATION.load_yaml_file(FOUNDATION_REGISTRY)
        cls.domain = VALIDATION.load_yaml_file(DOMAIN_REGISTRY)
        cls.admission = VALIDATION.load_yaml_file(ADMISSION_CASES)
        cls.routing = VALIDATION.load_yaml_file(ROUTING_CASES)
        cls.foundation_rows = {
            row["name"]: row
            for row in cls.foundation["foundation_skills"]
        }
        cls.professional_rows = {
            row["name"]: row
            for row in cls.professional["professional_skills"]
        }

    def test_r3_execution_fixture_migration_is_exactly_579_v2_only_rows(
        self,
    ) -> None:
        expected_basis_fields = set(
            VALIDATION.EXECUTION_LEVEL_MODEL["level_basis_fields"]
        )
        expected_counts = {
            ROUTING_CASES: 103,
            ROOT / "evals/routing/capability-coverage-cases.yaml": 47,
            ADMISSION_CASES: 429,
        }

        def active_executions(value: object) -> list[dict[str, object]]:
            found: list[dict[str, object]] = []
            if isinstance(value, dict):
                execution = value.get("main_execution")
                if (
                    isinstance(execution, dict)
                    and isinstance(execution.get("level_basis"), dict)
                ):
                    found.append(execution)
                for child in value.values():
                    found.extend(active_executions(child))
            elif isinstance(value, list):
                for child in value:
                    found.extend(active_executions(child))
            return found

        total = 0
        for path, expected_count in expected_counts.items():
            with self.subTest(path=path.relative_to(ROOT)):
                executions = active_executions(
                    VALIDATION.load_yaml_file(path)
                )
                self.assertEqual(expected_count, len(executions))
                self.assertTrue(
                    all(
                        set(execution["level_basis"])
                        == expected_basis_fields
                        for execution in executions
                    )
                )
                total += len(executions)
        self.assertEqual(579, total)

        legacy_checkpoint_digests = {
            PHASE2_A_PREDECESSOR_ROW_COUNT: (
                "d3f44baa2d9b98f2712900ca5d5ef54b4a762544ddcc4549cbdeeca4368e4b72"
            ),
            PHASE2_F03_PREDECESSOR_ROW_COUNT: (
                "cd965934eb9373f2d36a11e99bc7c251a1345ca25bea66c8c96567d2c8854473"
            ),
            PHASE2_F04_PREDECESSOR_ROW_COUNT: (
                "fc87d0b7fde7632aa6e4cead664a538c21a7f057b2cff3d43c6e5a9cc68dac43"
            ),
        }

        def remove_v2_only_fields(value: object) -> None:
            if isinstance(value, dict):
                basis = value.get("level_basis")
                if isinstance(basis, dict):
                    for field in (
                        "l1_eligibility",
                        "l5_assurance_eligibility",
                        "l5_confirmation",
                    ):
                        basis.pop(field, None)
                for child in value.values():
                    remove_v2_only_fields(child)
            elif isinstance(value, list):
                for child in value:
                    remove_v2_only_fields(child)

        for row_count, legacy_digest in legacy_checkpoint_digests.items():
            with self.subTest(legacy_projection_rows=row_count):
                predecessor = copy.deepcopy(
                    self.admission["cases"][:row_count]
                )
                remove_v2_only_fields(predecessor)
                predecessor_bytes = json.dumps(
                    predecessor,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                self.assertEqual(
                    legacy_digest,
                    hashlib.sha256(predecessor_bytes).hexdigest(),
                )

    def _assert_private_spec_ast_mutations(self) -> None:
        source = _private_spec_fixture_source()
        contracts = _foundation_selector_spec_contracts(
            ast.parse(source)
        )
        self.assertEqual(
            [
                {
                    "selector_id": "selector-a",
                    "foundations": (
                        "foundation-a",
                        "foundation-c",
                    ),
                    "evidence_ids": (
                        "evidence-a",
                        "foundation-selector:selector-a",
                    ),
                    "owner_bindings": (
                        ("primary-a", "review-a"),
                    ),
                    "primary_skill": "primary-a",
                    "review_skill": "review-a",
                },
                {
                    "selector_id": "selector-b",
                    "foundations": ("foundation-b",),
                    "evidence_ids": (
                        "evidence-b",
                        "foundation-selector:selector-b",
                    ),
                    "owner_bindings": (
                        ("primary-b", "review-b"),
                    ),
                    "primary_skill": "primary-b",
                    "review_skill": "review-b",
                },
                {
                    "selector_id": "selector-d",
                    "foundations": ("foundation-d",),
                    "evidence_ids": (
                        "evidence-d",
                        "foundation-selector:selector-d",
                    ),
                    "owner_bindings": (
                        ("primary-d", "review-d"),
                    ),
                    "primary_skill": "primary-d",
                    "review_skill": "review-d",
                },
            ],
            [
                {
                    key: contract[key]
                    for key in (
                        "selector_id",
                        "foundations",
                        "evidence_ids",
                        "owner_bindings",
                        "primary_skill",
                        "review_skill",
                    )
                }
                for contract in contracts
            ],
        )
        spec_declaration = """
@dataclass(frozen=True, slots=True)
class _FoundationSelectorSpec:
    selector_id: str
    foundations: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    owner_bindings: tuple[_FoundationSelectorOwnerBindingSpec, ...]
"""
        mutations = {
            "missing-spec-declaration": source.replace(
                spec_declaration,
                "",
                1,
            ),
            "duplicate-spec-declaration": source.replace(
                spec_declaration,
                f"{spec_declaration}\n{spec_declaration}",
                1,
            ),
            "duplicate-selector": source.replace(
                '"selector-b"',
                '"selector-a"',
            ).replace(
                "foundation-selector:selector-b",
                "foundation-selector:selector-a",
            ),
            "duplicate-foundation-owner": source.replace(
                '"foundation-b"',
                '"foundation-a"',
            ),
            "wrong-selector-binding": source.replace(
                "rule_id=unit.selector_id",
                'rule_id="detached-selector"',
            ),
            "transformed-selector-binding": source.replace(
                "rule_id=unit.selector_id",
                "rule_id=unit.selector_id[::-1]",
            ),
            "wrong-foundation-binding": source.replace(
                "list(unit.foundations)",
                '["foundation-a"]',
            ),
            "transformed-foundation-binding": source.replace(
                "list(unit.foundations)",
                "list(unit.foundations)[::-1]",
            ),
            "wrong-evidence-binding": source.replace(
                "match_evidence=tuple(unit.evidence_ids)",
                'match_evidence=["detached-evidence"]',
            ),
            "transformed-evidence-binding": source.replace(
                "match_evidence=tuple(unit.evidence_ids)",
                "match_evidence=tuple(unit.evidence_ids)[::-1]",
            ),
            "wrong-primary-binding": source.replace(
                "            binding.primary_skill,\n",
                '            "detached-primary",\n',
                1,
            ),
            "conditional-primary-binding": source.replace(
                "            binding.primary_skill,\n",
                (
                    "            binding.primary_skill if True "
                    'else "detached-primary",\n'
                ),
                1,
            ),
            "wrong-review-binding": source.replace(
                "            binding.review_skill,\n",
                '            "detached-review",\n',
                1,
            ),
            "conditional-review-binding": source.replace(
                "            binding.review_skill,\n",
                (
                    "            binding.review_skill if True "
                    'else "detached-review",\n'
                ),
                1,
            ),
            "transformed-candidate-id": source.replace(
                '"candidate_id": rule_id,',
                '"candidate_id": rule_id[::-1],',
            ),
            "transformed-rule-id": source.replace(
                '"rule_id": rule_id,',
                '"rule_id": rule_id[::-1],',
            ),
            "transformed-candidate-evidence": source.replace(
                '"evidence": list(match_evidence),',
                '"evidence": list(match_evidence)[::-1],',
            ),
            "transformed-candidate-foundations": source.replace(
                '"layer3_skills": list(layer3),',
                '"layer3_skills": list(layer3)[::-1],',
            ),
            "conditional-candidate-primary": source.replace(
                '"primary_skill": primary,',
                (
                    '"primary_skill": primary if True '
                    'else "detached-primary",'
                ),
            ),
            "conditional-candidate-review": source.replace(
                '"review_skill": review,',
                (
                    '"review_skill": review if True '
                    'else "detached-review",'
                ),
            ),
            "evidence-order": source.replace(
                '"evidence-a",\n'
                '            "foundation-selector:selector-a",',
                '"foundation-selector:selector-a",\n'
                '            "evidence-a",',
            ),
            "terminal-marker": source.replace(
                "foundation-selector:selector-a",
                "foundation-selector:wrong-selector",
                1,
            ),
            "dead-spec-hardcoded-candidate": source.replace(
                "    deliver(second)\n",
                """
    add_candidate(
        "analyzed",
        "analysis-agent",
        "primary-b",
        ["foundation-b"],
        "review-b",
        rule_id="selector-b",
        match_evidence=[
            "evidence-b",
            "foundation-selector:selector-b",
        ],
    )
""",
            ),
        }
        annotation_mutations = {
            "owner-primary-wrong-annotation": (
                "    primary_skill: str\n",
                "    primary_skill: int\n",
            ),
            "owner-review-wrong-annotation": (
                "    review_skill: str\n",
                "    review_skill: int\n",
            ),
            "selector-id-wrong-annotation": (
                "    selector_id: str\n",
                "    selector_id: int\n",
            ),
            "foundations-wrong-element-annotation": (
                "    foundations: tuple[str, ...]\n",
                "    foundations: tuple[int, ...]\n",
            ),
            "foundations-wrong-container-annotation": (
                "    foundations: tuple[str, ...]\n",
                "    foundations: list[str]\n",
            ),
            "evidence-ids-wrong-element-annotation": (
                "    evidence_ids: tuple[str, ...]\n",
                "    evidence_ids: tuple[int, ...]\n",
            ),
            "evidence-ids-wrong-container-annotation": (
                "    evidence_ids: tuple[str, ...]\n",
                "    evidence_ids: list[str]\n",
            ),
            "owner-bindings-wrong-element-annotation": (
                (
                    "    owner_bindings: tuple["
                    "_FoundationSelectorOwnerBindingSpec, ...]\n"
                ),
                "    owner_bindings: tuple[str, ...]\n",
            ),
            "owner-bindings-wrong-container-annotation": (
                (
                    "    owner_bindings: tuple["
                    "_FoundationSelectorOwnerBindingSpec, ...]\n"
                ),
                (
                    "    owner_bindings: list["
                    "_FoundationSelectorOwnerBindingSpec]\n"
                ),
            ),
        }
        for label, (original, replacement) in (
            annotation_mutations.items()
        ):
            mutations[label] = source.replace(
                original,
                replacement,
                1,
            )
        field_defaults = {
            "owner-primary": ("    primary_skill: str", "str"),
            "owner-review": ("    review_skill: str", "str"),
            "selector-id": ("    selector_id: str", "str"),
            "foundations": (
                "    foundations: tuple[str, ...]",
                "tuple",
            ),
            "evidence-ids": (
                "    evidence_ids: tuple[str, ...]",
                "tuple",
            ),
            "owner-bindings": (
                (
                    "    owner_bindings: tuple["
                    "_FoundationSelectorOwnerBindingSpec, ...]"
                ),
                "tuple",
            ),
        }
        for label, (declaration, factory) in field_defaults.items():
            mutations[f"{label}-default"] = source.replace(
                declaration,
                f"{declaration} = None",
                1,
            )
            mutations[f"{label}-default-factory"] = source.replace(
                declaration,
                f"{declaration} = field(default_factory={factory})",
                1,
            )
        for label, mutated in mutations.items():
            with self.subTest(private_spec_mutation=label):
                with self.assertRaises(AssertionError):
                    _foundation_selector_spec_contracts(
                        ast.parse(mutated)
                    )

        legacy_union_source = source.replace(
            "    deliver(second)\n",
            """
    deliver(second)
    add_candidate(
        "analyzed",
        "analysis-agent",
        "legacy-primary",
        ["foundation-legacy"],
        "legacy-review",
        rule_id="legacy-selector",
        match_evidence=["legacy-evidence"],
    )
""",
            1,
        )
        legacy_union_tree = ast.parse(legacy_union_source)
        self.assertNotIn(
            "foundation-legacy",
            _direct_foundation_inventory_from_tree(
                legacy_union_tree,
                {
                    "foundation-a",
                    "foundation-b",
                    "foundation-c",
                    "foundation-d",
                    "foundation-legacy",
                },
            ),
        )
        self.assertEqual(
            [("legacy-selector", ("foundation-legacy",))],
            [
                (selector_id, foundations)
                for _line, selector_id, foundations
                in _raw_foundation_add_candidate_emissions(
                    legacy_union_tree,
                    {
                        "foundation-a",
                        "foundation-b",
                        "foundation-c",
                        "foundation-d",
                        "foundation-legacy",
                    },
                )
            ],
        )

        keyword_raw_source = source.replace(
            "    deliver(second)\n",
            """
    deliver(second)
    add_candidate(
        "analyzed",
        "analysis-agent",
        "keyword-primary",
        review="keyword-review",
        layer3=["foundation-keyword"],
        rule_id="keyword-selector",
        match_evidence=["keyword-evidence"],
    )
""",
            1,
        )
        self.assertEqual(
            [("keyword-selector", ("foundation-keyword",))],
            [
                (selector_id, foundations)
                for _line, selector_id, foundations
                in _raw_foundation_add_candidate_emissions(
                    ast.parse(keyword_raw_source),
                    {
                        "foundation-a",
                        "foundation-b",
                        "foundation-c",
                        "foundation-d",
                        "foundation-keyword",
                    },
                )
            ],
        )

        duplicate_payload_source = source.replace(
            "    deliver(second)\n",
            """
    deliver(second)
    add_candidate(
        "analyzed",
        "analysis-agent",
        "duplicate-primary",
        ["foundation-positional"],
        review="duplicate-review",
        layer3=["foundation-keyword"],
        rule_id="duplicate-selector",
        match_evidence=["duplicate-evidence"],
    )
""",
            1,
        )
        with self.assertRaises(AssertionError):
            _raw_foundation_add_candidate_emissions(
                ast.parse(duplicate_payload_source),
                {
                    "foundation-a",
                    "foundation-b",
                    "foundation-c",
                    "foundation-d",
                    "foundation-keyword",
                    "foundation-positional",
                },
            )

        mixed_tree = ast.parse(
            mutations["dead-spec-hardcoded-candidate"]
        )
        spec_foundations = {
            foundation
            for contract in _foundation_selector_spec_contracts(
                ast.parse(source)
            )
            for foundation in contract["foundations"]
        }
        self.assertEqual(
            {
                "foundation-a",
                "foundation-b",
                "foundation-c",
                "foundation-d",
            },
            spec_foundations,
        )
        self.assertEqual(
            [
                (
                    "selector-b",
                    ("foundation-b",),
                )
            ],
            [
                (selector_id, foundations)
                for _line, selector_id, foundations
                in _raw_foundation_add_candidate_emissions(
                    mixed_tree,
                    {
                        "foundation-a",
                        "foundation-b",
                        "foundation-c",
                        "foundation-d",
                    },
                )
            ],
        )

    def _authority_api(
        self,
        r0_id: str,
    ) -> tuple[type, type, type, type, Callable[..., object]]:
        names = (
            "FoundationSelectorSource",
            "FoundationSelectorOwnerBinding",
            "FoundationSelectorRecord",
            "OracleAdmissionAuthority",
            "oracle_admission_authority",
        )
        values = tuple(getattr(ORACLE, name, None) for name in names)
        missing = [
            name
            for name, value in zip(names, values, strict=True)
            if value is None
            or (
                name == "oracle_admission_authority"
                and not callable(value)
            )
        ]
        if missing:
            self.fail(
                f"[{r0_id}-missing-authority-api] expected "
                f"{list(names)!r}; actual missing={missing!r}"
            )
        source_type, binding_type, record_type, authority_type, factory = values
        for name, value in zip(names[:4], values[:4], strict=True):
            if not isinstance(value, type) or not dataclasses.is_dataclass(value):
                self.fail(
                    f"[{r0_id}-authority-api-shape] expected {name}="
                    f"dataclass type; actual={value!r}"
                )
        return (
            source_type,
            binding_type,
            record_type,
            authority_type,
            factory,
        )

    def _authority(self, r0_id: str) -> object:
        *_, factory = self._authority_api(r0_id)
        return factory(
            foundation_registry=copy.deepcopy(self.foundation),
            professional_registry=copy.deepcopy(self.professional),
        )

    def _foundation_records(
        self,
        authority: object,
    ) -> tuple[object, ...]:
        records = getattr(authority, "foundation_selectors", None)
        self.assertIsInstance(records, tuple)
        return records

    def _record_for_foundation(
        self,
        authority: object,
        foundation: str,
    ) -> object:
        matches = [
            record
            for record in self._foundation_records(authority)
            if foundation in record.foundations
        ]
        self.assertEqual(
            1,
            len(matches),
            f"expected one selector record for {foundation!r}",
        )
        return matches[0]

    def _record_for_selector(
        self,
        authority: object,
        selector_id: str,
    ) -> object:
        matches = [
            record
            for record in self._foundation_records(authority)
            if record.selector_id == selector_id
        ]
        self.assertEqual(
            1,
            len(matches),
            f"expected one selector record for {selector_id!r}",
        )
        return matches[0]

    def _route_case(self, case_id: str) -> dict[str, object]:
        rows = [
            row
            for row in self.routing["cases"]
            if row.get("id") == case_id
        ]
        self.assertEqual(1, len(rows), f"expected routing case {case_id!r}")
        row = rows[0]
        return ORACLE.route_with_trace(
            row["prompt"],
            main_execution=copy.deepcopy(row["main_execution"]),
        )

    def _route_case_with_built_candidate_mutation(
        self,
        case_id: str,
        candidate_id: str,
        mutation: Callable[[dict[str, object]], None],
    ) -> dict[str, object]:
        original = ORACLE._build_route_candidates

        def mutated_builder(
            *args: object,
            **kwargs: object,
        ) -> list[dict[str, object]]:
            candidates = original(*args, **kwargs)
            matches = [
                candidate
                for candidate in candidates
                if candidate.get("candidate_id") == candidate_id
            ]
            self.assertEqual(
                1,
                len(matches),
                f"expected one built candidate {candidate_id!r}",
            )
            mutation(matches[0])
            return candidates

        with mock.patch.object(
            ORACLE,
            "_build_route_candidates",
            side_effect=mutated_builder,
        ):
            return self._route_case(case_id)

    def _route_case_with_enriched_candidate_replacement(
        self,
        case_id: str,
        candidate_id: str,
        replacement: Mapping[str, object],
    ) -> dict[str, object]:
        original = ORACLE._enrich_route_candidates

        def replaced_enricher(
            *args: object,
            **kwargs: object,
        ) -> list[dict[str, object]]:
            candidates = original(*args, **kwargs)
            indexes = [
                index
                for index, candidate in enumerate(candidates)
                if candidate.get("candidate_id") == candidate_id
            ]
            self.assertEqual(
                1,
                len(indexes),
                f"expected one enriched candidate {candidate_id!r}",
            )
            candidates[indexes[0]] = copy.deepcopy(dict(replacement))
            return candidates

        with mock.patch.object(
            ORACLE,
            "_enrich_route_candidates",
            side_effect=replaced_enricher,
        ):
            return self._route_case(case_id)

    def _replace_foundation_route_binding(
        self,
        candidate: dict[str, object],
        *,
        primary_skill: str,
        review_skill: str,
        candidate_id: str | None = None,
        routing_family: str | None = None,
    ) -> None:
        candidate["primary_skill"] = primary_skill
        candidate["review_skill"] = review_skill
        if candidate_id is not None:
            candidate["candidate_id"] = candidate_id
        if routing_family is not None:
            candidate["routing_family"] = routing_family
        rows = candidate.get("source_foundation_candidates")
        self.assertIsInstance(rows, list)
        self.assertTrue(rows)
        for row in rows:
            self.assertIsInstance(row, dict)
            row["owner_binding"] = {
                "primary_skill": primary_skill,
                "review_skill": review_skill,
            }

    def _assert_record_candidate_parity(
        self,
        record: object,
        candidate: Mapping[str, object],
        *,
        surface: str,
    ) -> None:
        candidate_ids = (
            candidate.get("candidate_id"),
            candidate.get("rule_id"),
        )
        self.assertIn(
            record.selector_id,
            candidate_ids,
            f"{surface} lost selector_id={record.selector_id!r}",
        )
        candidate_foundations = tuple(
            item
            for item in candidate.get("layer3_skills", [])
            if item in self.foundation_rows
        )
        self.assertEqual(
            record.foundations,
            candidate_foundations,
            f"{surface} changed Foundation order or identity",
        )
        candidate_evidence = candidate.get("evidence")
        self.assertIsInstance(candidate_evidence, list)
        self.assertTrue(
            _is_ordered_subsequence(
                record.evidence_ids,
                tuple(candidate_evidence),
            ),
            f"{surface} lost or reordered selector evidence; "
            f"expected={record.evidence_ids!r}; "
            f"actual={candidate_evidence!r}",
        )
        candidate_binding = (
            candidate.get("primary_skill"),
            candidate.get("review_skill"),
        )
        owner_bindings = {
            (binding.primary_skill, binding.review_skill)
            for binding in record.owner_bindings
        }
        self.assertIn(
            candidate_binding,
            owner_bindings,
            f"{surface} used an undeclared selector owner binding",
        )

    def _assert_candidate_contract(
        self,
        expected: Mapping[str, object],
        candidate: Mapping[str, object],
        *,
        surface: str,
    ) -> None:
        self.assertIn(
            expected["selector_id"],
            (candidate.get("candidate_id"), candidate.get("rule_id")),
            f"{surface} lost selector ID",
        )
        self.assertEqual(
            tuple(expected["foundations"]),
            tuple(
                item
                for item in candidate.get("layer3_skills", [])
                if item in self.foundation_rows
            ),
            f"{surface} changed Foundation order",
        )
        self.assertEqual(
            (
                expected["primary_skill"],
                expected["review_skill"],
            ),
            (
                candidate.get("primary_skill"),
                candidate.get("review_skill"),
            ),
            f"{surface} changed owner binding",
        )
        self.assertTrue(
            _is_ordered_subsequence(
                tuple(expected["source_evidence"]),
                tuple(candidate.get("evidence", [])),
            ),
            f"{surface} lost original source evidence",
        )
        self.assertTrue(
            _is_ordered_subsequence(
                tuple(expected["evidence_ids"]),
                tuple(candidate.get("evidence", [])),
            ),
            f"{surface} lost or reordered selector evidence",
        )

    def _expected_owner_rows(
        self,
        records: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        return [
            {
                "candidate_id": record["selector_id"],
                "routing_family": record["routing_family"],
                "primary_skill": record["primary_skill"],
                "foundation_requests": list(record["foundations"]),
                "review_skill": record["review_skill"],
                "evidence": list(record["evidence_ids"]),
            }
            for record in records
        ]

    def _assert_preparation_owner_trace_contract(
        self,
        trace: Mapping[str, object],
        records: Sequence[Mapping[str, object]],
    ) -> None:
        selected = trace["selected_candidate"]
        self.assertIsInstance(selected, dict)
        self.assertEqual(
            "implementation-preparation",
            selected["candidate_id"],
        )
        context = selected["candidate_layer3_context"]
        self.assertIsInstance(context, dict)
        self.assertEqual("preparation", context["kind"])
        expected_rows = self._expected_owner_rows(records)
        owner_rows = context["owners"]
        self.assertEqual(
            expected_rows,
            owner_rows,
            "[R0-10b-owner-context-parity] selected owner context must "
            "match the exact authority projection",
        )
        owner_ids = [row["candidate_id"] for row in owner_rows]
        self.assertEqual(len(owner_ids), len(set(owner_ids)))

        expected_ids = [row["candidate_id"] for row in expected_rows]
        raw_candidates = trace["raw_candidates"]
        excluded_candidates = trace["excluded_candidates"]
        raw_owners = [
            candidate
            for candidate in raw_candidates
            if candidate.get("candidate_id") in expected_ids
        ]
        excluded_owners = [
            candidate
            for candidate in excluded_candidates
            if candidate.get("candidate_id") in expected_ids
        ]
        self.assertEqual(
            expected_ids,
            [candidate["candidate_id"] for candidate in raw_owners],
        )
        self.assertEqual(
            expected_ids,
            [candidate["candidate_id"] for candidate in excluded_owners],
        )
        for expected, raw, excluded in zip(
            expected_rows,
            raw_owners,
            excluded_owners,
            strict=True,
        ):
            raw_context = raw["candidate_layer3_context"]
            self.assertNotIn("reason", raw)
            self.assertEqual("fixed", raw_context["kind"])
            self.assertEqual(
                expected["foundation_requests"],
                raw_context["foundation_requests"],
            )
            self.assertEqual(
                expected["foundation_requests"],
                raw["eligible_foundation_layer3_skills"],
            )
            self.assertEqual(
                expected,
                {
                    "candidate_id": raw.get("candidate_id"),
                    "routing_family": raw.get("routing_family"),
                    "primary_skill": raw.get("primary_skill"),
                    "foundation_requests": raw_context[
                        "foundation_requests"
                    ],
                    "review_skill": raw.get("review_skill"),
                    "evidence": raw.get("evidence"),
                },
            )
            expected_excluded = copy.deepcopy(raw)
            expected_excluded["reason"] = (
                "lower-precedence-than-implementation-preparation"
            )
            self.assertEqual(expected_excluded, excluded)

        handoff = trace["deferred_handoff"]
        self.assertNotIn("source_owner", handoff)
        self.assertEqual(
            {
                "status": "unresolved",
                "cohorts": [
                    "layer3",
                    "review",
                    "execution-level",
                ],
                "source_rule_id": "candidate-set",
                "retained_layer3": [],
                "deferred_layer3": [
                    "infrastructure-as-code-safety"
                ],
                "review_skill": "ai-code-review-refactor",
                "reason": (
                    "candidate-layer3-not-authorized-by-"
                    "engineering-change-analysis"
                ),
            },
            handoff,
        )

    def _trace_candidate_surfaces(
        self,
        trace: Mapping[str, object],
    ) -> list[tuple[str, dict[str, object]]]:
        surfaces = [
            (f"raw_candidates[{index}]", candidate)
            for index, candidate in enumerate(trace["raw_candidates"])
        ]
        surfaces.append(
            ("selected_candidate", trace["selected_candidate"])
        )
        surfaces.extend(
            (f"excluded_candidates[{index}]", candidate)
            for index, candidate in enumerate(
                trace["excluded_candidates"]
            )
        )
        return surfaces

    def _source_foundation_evidence(
        self,
        rows: Sequence[Mapping[str, object]],
        *,
        overflow: bool,
    ) -> list[str]:
        evidence = list(
            dict.fromkeys(
                item
                for row in rows
                for item in row["evidence"]
            )
        )
        if overflow:
            evidence.append("foundation-layer3-overflow")
        return evidence

    def _assert_source_foundation_trace_contract(
        self,
        trace: Mapping[str, object],
        r0_id: str,
        source_candidates_by_id: Mapping[
            str,
            Mapping[str, object],
        ],
    ) -> list[dict[str, object]]:
        carriers: list[tuple[str, dict[str, object], list[object]]] = []
        for surface, candidate in self._trace_candidate_surfaces(trace):
            carries = _carries_source_foundation_candidates(candidate)
            if not carries:
                self.assertNotIn(
                    "source_foundation_candidates",
                    candidate,
                    f"{surface} is outside the accepted carrier predicate",
                )
                continue
            rows = candidate.get("source_foundation_candidates")
            self.assertIsInstance(
                rows,
                list,
                f"{surface} carrier requires the closed "
                "source_foundation_candidates field",
            )
            self.assertTrue(rows)
            carriers.append((surface, candidate, rows))

        self.assertNotIn("source_foundation_candidates", trace)
        if not carriers:
            return []

        authority = self._authority(r0_id)
        authority_records = self._foundation_records(authority)
        authority_selector_ids = [
            record.selector_id for record in authority_records
        ]
        self.assertEqual(
            len(authority_selector_ids),
            len(set(authority_selector_ids)),
        )
        canonical_rows_by_id: dict[str, dict[str, object]] = {}
        for surface, candidate, rows in carriers:
            candidate_ids: list[str] = []
            authority_indexes: list[int] = []
            for index, row in enumerate(rows):
                self.assertIsInstance(
                    row,
                    dict,
                    f"{surface} source row {index} must be an object",
                )
                self.assertEqual(
                    SOURCE_FOUNDATION_CANDIDATE_FIELDS,
                    set(row),
                )
                candidate_id = row["candidate_id"]
                foundations = row["foundations"]
                evidence = row["evidence"]
                owner_binding = row["owner_binding"]
                self.assertIsInstance(candidate_id, str)
                self.assertIsInstance(foundations, list)
                self.assertIsInstance(evidence, list)
                self.assertIsInstance(owner_binding, dict)
                self.assertEqual(
                    SOURCE_FOUNDATION_OWNER_BINDING_FIELDS,
                    set(owner_binding),
                )
                matches = [
                    record
                    for record in authority_records
                    if record.selector_id == candidate_id
                ]
                self.assertEqual(
                    1,
                    len(matches),
                    f"{surface} source row {candidate_id!r} must resolve "
                    "to exactly one production authority record",
                )
                record = matches[0]
                self.assertEqual(list(record.foundations), foundations)
                self.assertEqual(list(record.evidence_ids), evidence)
                selector_marker = f"foundation-selector:{candidate_id}"
                self.assertEqual(selector_marker, evidence[-1])
                self.assertEqual(1, evidence.count(selector_marker))
                bindings = {
                    (
                        binding.primary_skill,
                        binding.review_skill,
                    )
                    for binding in record.owner_bindings
                }
                self.assertIn(
                    (
                        owner_binding["primary_skill"],
                        owner_binding["review_skill"],
                    ),
                    bindings,
                )
                source_candidate = source_candidates_by_id.get(
                    candidate_id
                )
                self.assertIsInstance(
                    source_candidate,
                    dict,
                    f"{surface} source row {candidate_id!r} must resolve "
                    "to one effective trace source candidate",
                )
                effective_pair = (
                    source_candidate.get("primary_skill"),
                    source_candidate.get("review_skill"),
                )
                self.assertTrue(
                    all(
                        isinstance(value, str) and value
                        for value in effective_pair
                    )
                )
                self.assertEqual(
                    effective_pair,
                    (
                        owner_binding["primary_skill"],
                        owner_binding["review_skill"],
                    ),
                    f"{surface} source row {candidate_id!r} must use its "
                    "effective source candidate owner pair",
                )
                candidate_ids.append(candidate_id)
                authority_indexes.append(
                    authority_selector_ids.index(candidate_id)
                )
                canonical_rows_by_id.setdefault(
                    candidate_id,
                    copy.deepcopy(row),
                )
            self.assertEqual(len(candidate_ids), len(set(candidate_ids)))
            self.assertEqual(sorted(authority_indexes), authority_indexes)
            self.assertTrue(
                set(candidate_ids).issubset(source_candidates_by_id),
            )
            if candidate.get("candidate_id") in {
                "foundation-activation-composite",
                "foundation-layer3-overflow",
            }:
                source_candidate_ids = candidate.get(
                    "source_candidate_ids"
                )
                self.assertIsInstance(source_candidate_ids, list)
                self.assertEqual(candidate_ids, source_candidate_ids)
            overflow = (
                candidate["candidate_id"]
                == "foundation-layer3-overflow"
            )
            candidate_evidence = candidate.get("evidence")
            self.assertIsInstance(candidate_evidence, list)
            self.assertEqual(
                self._source_foundation_evidence(
                    rows,
                    overflow=overflow,
                ),
                candidate_evidence,
            )
            if overflow:
                self.assertEqual(
                    "foundation-layer3-overflow",
                    candidate_evidence[-1],
                )
        self.assertEqual(
            set(source_candidates_by_id),
            set(canonical_rows_by_id),
        )
        return [
            canonical_rows_by_id[selector_id]
            for selector_id in authority_selector_ids
            if selector_id in canonical_rows_by_id
        ]

    def _assert_source_foundation_mutations_detected(
        self,
        trace: Mapping[str, object],
        r0_id: str,
        *,
        overflow: bool,
    ) -> None:
        authority = self._authority(r0_id)
        authority_records = self._foundation_records(authority)
        multi_records = [
            record
            for record in authority_records
            if len(record.foundations) >= 2
        ]
        self.assertTrue(
            multi_records,
            f"[{r0_id}-mutation-multi-foundation] production authority "
            "must expose at least one multi-Foundation selector",
        )
        multi_record = multi_records[0]
        multi_binding_records = [
            record
            for record in authority_records
            if len(record.owner_bindings) >= 2
        ]
        self.assertTrue(
            multi_binding_records,
            f"[{r0_id}-mutation-multi-binding] production authority must "
            "expose at least one selector with two legal owner bindings",
        )
        multi_binding_record = multi_binding_records[0]
        binding_pairs = [
            (binding.primary_skill, binding.review_skill)
            for binding in multi_binding_record.owner_bindings
        ]
        self.assertEqual(len(binding_pairs), len(set(binding_pairs)))
        selected_ids = {
            multi_record.selector_id,
            multi_binding_record.selector_id,
        }
        other_record = next(
            record
            for record in authority_records
            if record.selector_id not in selected_ids
        )
        selected_ids.add(other_record.selector_id)
        selected_records = [
            record
            for record in authority_records
            if record.selector_id in selected_ids
        ]
        extra_record = next(
            record
            for record in authority_records
            if record.selector_id not in selected_ids
        )

        def authority_row(record: object) -> dict[str, object]:
            binding = record.owner_bindings[0]
            return {
                "candidate_id": record.selector_id,
                "foundations": list(record.foundations),
                "evidence": list(record.evidence_ids),
                "owner_binding": {
                    "primary_skill": binding.primary_skill,
                    "review_skill": binding.review_skill,
                },
            }

        accepted = copy.deepcopy(trace)
        accepted_rows = [
            authority_row(record) for record in selected_records
        ]
        source_candidates_by_id = {
            record.selector_id: {
                "primary_skill": record.owner_bindings[0].primary_skill,
                "review_skill": record.owner_bindings[0].review_skill,
            }
            for record in selected_records
        }
        for _surface, candidate in self._trace_candidate_surfaces(accepted):
            if not _carries_source_foundation_candidates(candidate):
                continue
            candidate["source_foundation_candidates"] = copy.deepcopy(
                accepted_rows
            )
            candidate["source_candidate_ids"] = [
                row["candidate_id"] for row in accepted_rows
            ]
            candidate["evidence"] = self._source_foundation_evidence(
                accepted_rows,
                overflow=overflow,
            )
        self._assert_source_foundation_trace_contract(
            accepted,
            r0_id,
            source_candidates_by_id,
        )
        selected_candidate = accepted["selected_candidate"]
        multi_id = multi_record.selector_id
        multi_binding_id = multi_binding_record.selector_id
        alternate_binding = multi_binding_record.owner_bindings[1]
        mutation_labels = (
            "extra-unrelated-row",
            "row-deletion",
            "row-reorder",
            "row-duplicate",
            "foundation-deletion",
            "foundation-reorder",
            "foundation-duplicate",
            "foundation-forge",
            "evidence-deletion",
            "evidence-reorder",
            "evidence-duplicate",
            "evidence-forge",
            "primary-owner-forge",
            "review-owner-forge",
            "legal-but-non-effective-owner-binding",
            "owner-binding-missing",
            "owner-binding-extra",
            "owner-binding-flat",
            "owner-binding-wrong-type",
            "source-ids-deletion",
            "source-ids-order",
            "source-ids-forge",
            "aggregate-evidence-deletion",
            "aggregate-evidence-order",
            "aggregate-evidence-duplicate",
            *(
                ("overflow-marker-not-last",)
                if overflow
                else ()
            ),
        )
        for label in mutation_labels:
            with self.subTest(mutation=label):
                mutated = copy.deepcopy(accepted)
                candidate = mutated["selected_candidate"]
                rows = candidate["source_foundation_candidates"]
                multi_row = next(
                    row for row in rows
                    if row["candidate_id"] == multi_id
                )
                multi_binding_row = next(
                    row for row in rows
                    if row["candidate_id"] == multi_binding_id
                )
                if label == "extra-unrelated-row":
                    rows.append(authority_row(extra_record))
                elif label == "row-deletion":
                    rows.pop()
                elif label == "row-reorder":
                    rows.reverse()
                elif label == "row-duplicate":
                    rows.append(copy.deepcopy(rows[0]))
                elif label == "foundation-deletion":
                    multi_row["foundations"].pop()
                elif label == "foundation-reorder":
                    self.assertGreaterEqual(
                        len(multi_row["foundations"]),
                        2,
                    )
                    multi_row["foundations"].reverse()
                elif label == "foundation-duplicate":
                    multi_row["foundations"].append(
                        multi_row["foundations"][0]
                    )
                elif label == "foundation-forge":
                    multi_row["foundations"][0] = (
                        "__forged-foundation__"
                    )
                elif label == "evidence-deletion":
                    multi_row["evidence"].pop()
                elif label == "evidence-reorder":
                    self.assertGreaterEqual(len(multi_row["evidence"]), 2)
                    multi_row["evidence"].reverse()
                elif label == "evidence-duplicate":
                    multi_row["evidence"].append(
                        multi_row["evidence"][0]
                    )
                elif label == "evidence-forge":
                    multi_row["evidence"][0] = "__forged-evidence__"
                elif label == "primary-owner-forge":
                    multi_row["owner_binding"]["primary_skill"] = (
                        "__forged-primary__"
                    )
                elif label == "review-owner-forge":
                    multi_row["owner_binding"]["review_skill"] = (
                        "__forged-review__"
                    )
                elif label == "legal-but-non-effective-owner-binding":
                    multi_binding_row["owner_binding"] = {
                        "primary_skill": alternate_binding.primary_skill,
                        "review_skill": alternate_binding.review_skill,
                    }
                elif label == "owner-binding-missing":
                    multi_row["owner_binding"].pop("review_skill")
                elif label == "owner-binding-extra":
                    multi_row["owner_binding"]["extra"] = "forged"
                elif label == "owner-binding-flat":
                    binding = multi_row.pop("owner_binding")
                    multi_row.update(binding)
                elif label == "owner-binding-wrong-type":
                    multi_row["owner_binding"] = []
                elif label == "source-ids-deletion":
                    candidate["source_candidate_ids"].pop()
                elif label == "source-ids-order":
                    candidate["source_candidate_ids"].reverse()
                elif label == "source-ids-forge":
                    candidate["source_candidate_ids"][0] = (
                        "__forged-source__"
                    )
                elif label == "aggregate-evidence-deletion":
                    candidate["evidence"].pop(0)
                elif label == "aggregate-evidence-order":
                    candidate["evidence"].reverse()
                elif label == "aggregate-evidence-duplicate":
                    candidate["evidence"].append(
                        candidate["evidence"][0]
                    )
                else:
                    self.assertEqual(
                        "foundation-layer3-overflow",
                        candidate["evidence"][-1],
                    )
                    candidate["evidence"] = [
                        "foundation-layer3-overflow",
                        *candidate["evidence"][:-1],
                    ]
                with self.assertRaises(AssertionError):
                    self._assert_source_foundation_trace_contract(
                        mutated,
                        r0_id,
                        source_candidates_by_id,
                    )

    def _expected_combinations_from_sources(
        self,
    ) -> set[tuple[str, str, str]]:
        primary, _review = _source_professional_inventory(
            self.professional
        )
        selectors = _source_selector_inventory(self.foundation)
        foundation_names = {
            name
            for names in selectors.values()
            for name in names
        }
        combinations = {
            ("professional", name, effect)
            for name in primary
            for effect in (
                PROFESSIONAL_EFFECTS
                if self.professional_rows[name].get("routing_family")
                else tuple(
                    item
                    for item in PROFESSIONAL_EFFECTS
                    if item != "true-conflict"
                )
            )
        }
        combinations.update(
            {
                ("foundation", foundation, effect)
                for foundation in foundation_names
                for effect in FOUNDATION_EFFECTS
            }
        )
        domain_names = {
            row["name"] for row in self.domain["domain_skills"]
        }
        routed_domain_names = {
            candidate
            for row in self.professional["professional_skills"]
            if row.get("routing_family")
            in {"installed-client", "platform-infrastructure"}
            for candidate in row.get("layer3_candidates", [])
            if candidate in domain_names
        }
        combinations.update(
            {
                ("domain", name, effect)
                for name in routed_domain_names
                for effect in DOMAIN_EFFECTS
            }
        )
        return combinations

    def test_r0_01_public_authority_is_exact_frozen_slots_api(self) -> None:
        (
            source_type,
            binding_type,
            record_type,
            authority_type,
            factory,
        ) = self._authority_api("R0-01")
        expected_fields = {
            source_type: ("kind", "symbol", "source_id"),
            binding_type: ("primary_skill", "review_skill"),
            record_type: (
                "selector_id",
                "foundations",
                "source",
                "evidence_ids",
                "owner_bindings",
            ),
            authority_type: (
                "contract",
                "foundation_selectors",
                "primary_task_skills",
                "review_task_skills",
            ),
        }
        authority = factory(
            foundation_registry=copy.deepcopy(self.foundation),
            professional_registry=copy.deepcopy(self.professional),
        )
        instances = {
            authority_type: authority,
            record_type: authority.foundation_selectors[0],
            source_type: authority.foundation_selectors[0].source,
            binding_type: authority.foundation_selectors[0].owner_bindings[0],
        }
        for data_type, fields in expected_fields.items():
            with self.subTest(data_type=data_type.__name__):
                self.assertEqual(
                    fields,
                    tuple(field.name for field in dataclasses.fields(data_type)),
                )
                self.assertTrue(data_type.__dataclass_params__.frozen)
                self.assertEqual(fields, tuple(data_type.__slots__))
                instance = instances[data_type]
                self.assertFalse(hasattr(instance, "__dict__"))
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(instance, fields[0], "mutated")

        signature = inspect.signature(factory)
        self.assertEqual(
            ("foundation_registry", "professional_registry"),
            tuple(signature.parameters),
        )
        self.assertTrue(
            all(
                parameter.kind
                is inspect.Parameter.POSITIONAL_OR_KEYWORD
                and parameter.default is None
                for parameter in signature.parameters.values()
            )
        )
        hints = get_type_hints(factory)
        self.assertEqual(object | None, hints["foundation_registry"])
        self.assertEqual(object | None, hints["professional_registry"])
        self.assertIs(authority_type, hints["return"])
        self.assertEqual(AUTHORITY_CONTRACT, authority.contract)

    def test_r0_02_foundation_inventory_and_provenance_digest(self) -> None:
        inventory = _source_selector_inventory(self.foundation)
        rows = sorted(
            f"{kind}\t{foundation}"
            for kind, foundations in inventory.items()
            for foundation in foundations
        )
        foundation_ids = [
            foundation
            for foundations in inventory.values()
            for foundation in foundations
        ]
        self.assertNotEqual(66, len(foundation_ids))
        self.assertEqual(69, len(foundation_ids))
        self.assertEqual(69, len(set(foundation_ids)))
        self.assertEqual(
            FOUNDATION_SOURCE_COUNTS,
            {
                kind: len(inventory[kind])
                for kind in FOUNDATION_SOURCE_COUNTS
            },
        )
        grammar = "".join(f"{row}\n" for row in rows).encode("utf-8")
        self.assertEqual(2822, len(grammar))
        self.assertTrue(
            grammar.startswith(
                b"direct-static\tacceptance-standard-definition\n"
            )
        )
        self.assertTrue(grammar.endswith(b"runtime-matcher\ttest-strategy\n"))
        self.assertNotIn(b"\r", grammar)
        grammar_digest = _sha256(grammar)
        self.assertNotEqual(
            "98a7f6ef756f0cfe2b8270588c5b2fb87dd8cb2c393ecee712f0a997cb54a531",
            grammar_digest,
        )
        self.assertEqual(FOUNDATION_PROVENANCE_DIGEST, grammar_digest)

    def test_r0_03_professional_primary_review_inventory_digests(self) -> None:
        primary, review = _source_professional_inventory(
            self.professional
        )
        self.assertIsInstance(primary, tuple)
        self.assertIsInstance(review, tuple)
        self.assertEqual(tuple(sorted(set(primary))), primary)
        self.assertEqual(tuple(sorted(set(review))), review)
        self.assertEqual(24, len(primary))
        self.assertEqual(10, len(review))
        primary_grammar = _lf_grammar(primary)
        review_grammar = _lf_grammar(review)
        self.assertEqual(630, len(primary_grammar))
        self.assertEqual(244, len(review_grammar))
        self.assertEqual(PRIMARY_SKILL_DIGEST, _sha256(primary_grammar))
        self.assertEqual(REVIEW_SKILL_DIGEST, _sha256(review_grammar))

    def test_r0_04_admission_target_is_105_276_48_and_complete(
        self,
    ) -> None:
        expected = self._expected_combinations_from_sources()
        counts = {
            layer: sum(1 for row in expected if row[0] == layer)
            for layer in ("professional", "foundation", "domain")
        }
        self.assertEqual(
            {"professional": 105, "foundation": 276, "domain": 48},
            counts,
        )
        self.assertNotEqual(
            {"professional": 105, "foundation": 264, "domain": 48},
            counts,
        )
        fixture_rows = self.admission["cases"]
        fixture = {
            (row["layer"], row["skill"], row["case_kind"])
            for row in fixture_rows
        }
        self.assertNotEqual(411, len(fixture_rows))
        self.assertEqual(429, len(fixture_rows))
        self.assertEqual(429, len(fixture))
        self.assertEqual(set(), fixture - expected)
        missing = expected - fixture
        self.assertNotEqual(WAVE1A_FOUNDATION_TRIPLES, missing)
        self.assertEqual(set(), missing)
        self.assertTrue(WAVE1A_FOUNDATION_TRIPLES.issubset(fixture))
        self.assertNotEqual(411, len(expected))
        self.assertEqual(429, len(expected))

    def test_r0_04b_capcov_projection_requires_authority_refactor(
        self,
    ) -> None:
        combinations = CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
        counts = {
            layer: sum(
                1
                for candidate_layer, _skill, _effect in combinations
                if candidate_layer == layer
            )
            for layer in ("professional", "foundation", "domain")
        }
        self.assertEqual(
            {
                "professional": 105,
                "foundation": 276,
                "domain": 48,
            },
            counts,
            "[R0-04b-capcov-authority-refactor] admission obligations must "
            "come from OracleAdmissionAuthority, not the broad product "
            "registry inventory",
        )
        self.assertNotEqual(
            {"professional": 105, "foundation": 264, "domain": 48},
            counts,
        )
        self.assertNotEqual(411, len(combinations))
        self.assertEqual(429, len(combinations))

    def test_r0_05_four_special_selectors_are_exact(self) -> None:
        foundation_names = set(self.foundation_rows)
        for foundation, expected in SPECIAL_SELECTORS.items():
            with self.subTest(foundation=foundation):
                source = _direct_selector_contract(
                    foundation,
                    foundation_names,
                )
                self.assertEqual(
                    {
                        "selector_id": expected["selector_id"],
                        "foundations": (foundation,),
                        "primary_skill": expected["primary_skill"],
                        "review_skill": expected["review_skill"],
                        "source_evidence": expected["source_evidence"],
                        "evidence_ids": expected["evidence_ids"],
                    },
                    {
                        key: source[key]
                        for key in (
                            "selector_id",
                            "foundations",
                            "primary_skill",
                            "review_skill",
                            "source_evidence",
                            "evidence_ids",
                        )
                    },
                )
                observed = ORACLE.route_with_trace(
                    expected["prompt"],
                    main_execution=_main_execution(
                        f"r0-05-{foundation}"
                    ),
                )
                raw = [
                    candidate
                    for candidate in observed["winner_trace"][
                        "raw_candidates"
                    ]
                    if candidate.get("candidate_id")
                    == expected["selector_id"]
                ]
                self.assertEqual(1, len(raw))
                self._assert_candidate_contract(
                    source,
                    raw[0],
                    surface=f"{foundation} raw route",
                )
        self._assert_private_spec_ast_mutations()

    def test_r0_06_enabled_runtime_matchers_are_all_and_only(self) -> None:
        projections = VALIDATION.foundation_runtime_matcher_authority(
            copy.deepcopy(self.foundation),
            context="R0-06 Foundation matcher projection",
        )
        runtime_inventory = set(
            _source_selector_inventory(self.foundation)[
                "runtime-matcher"
            ]
        )
        self.assertEqual(
            runtime_inventory,
            {projection["name"] for projection in projections},
        )
        prompts = {
            "business-rule-extraction": "Analyze business policies.",
            "state-machine-modeling": (
                "Model the domain lifecycle states."
            ),
            "test-strategy": (
                "Analyze which proof portfolio should cover several material "
                "failure mechanisms. Select the test levels, observable "
                "failure oracles, and justified omissions because no single "
                "command has been fixed."
            ),
        }
        self.assertEqual(3, len(projections))
        for projection in projections:
            with self.subTest(foundation=projection["name"]):
                observed = ORACLE.route_with_trace(
                    prompts[projection["name"]],
                    main_execution=_main_execution(
                        f"r0-06-{projection['name']}"
                    ),
                )
                matches = [
                    candidate
                    for candidate in observed["winner_trace"][
                        "raw_candidates"
                    ]
                    if candidate.get("candidate_id")
                    == projection["activation_id"]
                ]
                self.assertEqual(1, len(matches))
                expected = {
                    "selector_id": projection["activation_id"],
                    "foundations": (projection["name"],),
                    "primary_skill": projection["primary_skill"],
                    "review_skill": projection["review_skill"],
                    "source_evidence": tuple(
                        projection["matcher_evidence"]
                    ),
                    "evidence_ids": (
                        *projection["matcher_evidence"],
                        "foundation-selector:"
                        f"{projection['activation_id']}",
                    ),
                }
                self._assert_candidate_contract(
                    expected,
                    matches[0],
                    surface=f"{projection['name']} runtime route",
                )

    def test_r0_07_inactive_business_invariant_and_deferred_are_not_promoted(
        self,
    ) -> None:
        inventory = _source_selector_inventory(self.foundation)
        all_foundations = {
            foundation
            for foundations in inventory.values()
            for foundation in foundations
        }
        inactive = set(INACTIVE_NO_SELECTOR_FOUNDATIONS)
        self.assertTrue(inactive.isdisjoint(all_foundations))
        obligation_foundations = {
            skill
            for layer, skill, _effect
            in CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            if layer == "foundation"
        }
        for name in INACTIVE_NO_SELECTOR_FOUNDATIONS:
            with self.subTest(foundation=name, surface="obligations"):
                self.assertNotIn(name, obligation_foundations)
            with self.subTest(foundation=name, surface="negative-route"):
                observed = ORACLE.route_with_trace(
                    INACTIVE_NEGATIVE_PROMPTS[name],
                    main_execution=_main_execution(
                        f"r0-07-inactive-{name}"
                    ),
                )
                selected = observed["route_decision"]["route_result"][
                    "layer3_skills"
                ]
                raw_values = {
                    item
                    for candidate in observed["winner_trace"][
                        "raw_candidates"
                    ]
                    for item in candidate.get("layer3_skills", [])
                }
                self.assertNotIn(name, selected)
                self.assertNotIn(name, raw_values)
        self.assertTrue(
            {
                "business-invariant-analysis",
                "architecture-enforcement-tooling",
                "repository-impact-inspection",
            }.isdisjoint(all_foundations)
        )

    def test_r0_08_high_risk_is_review_only_but_artifact_ai_are_primary(
        self,
    ) -> None:
        primary_rows, review_rows = _source_professional_inventory(
            self.professional
        )
        primary = set(primary_rows)
        review = set(review_rows)
        self.assertNotIn("high-risk-design-review", primary)
        self.assertIn("high-risk-design-review", review)
        for name in (
            "engineering-artifact-review",
            "ai-code-review-refactor",
        ):
            self.assertIn(name, primary)
            self.assertIn(name, review)

    def test_r0_09_ast_has_no_raw_foundation_emitter_bypass(self) -> None:
        foundation_names = set(self.foundation_rows)
        tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
        raw_emissions = _raw_foundation_add_candidate_emissions(
            tree,
            foundation_names,
        )
        self.assertEqual(
            [],
            raw_emissions,
            "[R0-09-raw-foundation-emitter-bypass] every fixed Foundation "
            "candidate must be constructed from OracleAdmissionAuthority",
        )

    def test_review_ambiguous_selector_evidence_is_task_true_for_direct_and_derived_routes(
        self,
    ) -> None:
        selector_id = "review-ambiguous-structure-repository-first"
        authority = self._authority("review-ambiguous-task-evidence")
        record = self._record_for_selector(authority, selector_id)
        selector_evidence = list(record.evidence_ids)

        def assert_source_row(
            candidate: Mapping[str, object],
        ) -> None:
            self.assertEqual(
                [
                    {
                        "candidate_id": selector_id,
                        "foundations": list(record.foundations),
                        "evidence": selector_evidence,
                        "owner_binding": {
                            "primary_skill": candidate["primary_skill"],
                            "review_skill": candidate["review_skill"],
                        },
                    }
                ],
                candidate.get("source_foundation_candidates"),
            )

        direct = ORACLE.route_with_trace(
            "Review the actual diff where a new wrapper both changes "
            "and remains unchanged.",
            main_execution=_main_execution(
                "review-ambiguous-direct-task-evidence",
            ),
        )
        direct_trace = direct["winner_trace"]
        direct_candidate = direct_trace["selected_candidate"]
        self.assertEqual(selector_id, direct_candidate["candidate_id"])
        self.assertEqual(selector_evidence, direct_candidate["evidence"])
        self.assertEqual(selector_evidence, direct_trace["match_evidence"])
        self.assertEqual(
            selector_evidence,
            [
                row["source_anchor"]
                for row in direct["route_decision"][
                    "selection_evidence"
                ]["task_evidence"]
            ],
        )
        assert_source_row(direct_candidate)

        derived_cases = [
            (
                "critical-unknown",
                (
                    "Implement an accepted backend service change; owner is "
                    "unknown while authority, placement, acceptance, "
                    "verification, and rollback are known."
                ),
                "critical-unknown",
                ["critical-owner-unknown"],
            ),
            (
                "implementation-preparation",
                "Prepare implementation before editing.",
                "implementation-preparation",
                ["explicit-implementation-preparation"],
            ),
            *[
                (
                    fixture["fixture_id"],
                    fixture["prompt"],
                    fixture["alias_id"],
                    {
                        "backend-effects-ambiguous": [
                            "backend-subject",
                            "ambiguous-effect",
                        ],
                        "backend-layer-budget": [
                            "backend-subject",
                            "layer-budget-exceeded",
                        ],
                        "distributed-effect-ambiguous": [
                            "distributed-effect-ambiguous",
                        ],
                        "installed-filesystem-ambiguous": [
                            "installed-client",
                            "filesystem-effect-ambiguous",
                        ],
                        "owner-blast-radius-analysis": [
                            "owner-and-blast-radius",
                        ],
                        "repository-first-default": [
                            "no-eligible-specific-candidate",
                        ],
                        "repository-tooling-ambiguous": [
                            "repository-tooling-change",
                            "ambiguous-effect",
                        ],
                        "repository-tooling-layer-budget": [
                            "repository-tooling-change",
                            "layer-budget-exceeded",
                        ],
                        "source-backed-repository-question": [
                            "repository-source-evidence",
                            "question-or-explanation",
                        ],
                    }[fixture["alias_id"]],
                )
                for fixture in FOUNDATION_ALIAS_PRODUCER_FIXTURES
                if fixture["source_ids"] == (selector_id,)
            ],
        ]
        self.assertEqual(11, len(derived_cases))
        for label, prompt, candidate_id, expected_evidence in derived_cases:
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=_main_execution(
                        f"{label}-derived-task-evidence",
                    ),
                )
                trace = observed["winner_trace"]
                matches = [
                    candidate
                    for candidate in trace["raw_candidates"]
                    if candidate.get("candidate_id") == candidate_id
                ]
                self.assertEqual(1, len(matches))
                candidate = matches[0]
                self.assertEqual(expected_evidence, candidate["evidence"])
                assert_source_row(candidate)
                if trace["selected_candidate"]["candidate_id"] == candidate_id:
                    self.assertEqual(
                        expected_evidence,
                        trace["selected_candidate"]["evidence"],
                    )
                    self.assertEqual(
                        expected_evidence,
                        trace["match_evidence"],
                    )
                    self.assertEqual(
                        expected_evidence,
                        [
                            row["source_anchor"]
                            for row in observed["route_decision"][
                                "selection_evidence"
                            ]["task_evidence"]
                        ],
                    )

    def test_r0_10a_direct_raw_selected_and_final_parity(self) -> None:
        record = _direct_selector_contract(
            "architecture-tradeoff-analysis",
            set(self.foundation_rows),
        )
        observed = ORACLE.route_with_trace(
            "Analyze an explicit architecture tradeoff.",
            main_execution=_main_execution(
                "r0-10a-direct-selected-parity"
            ),
        )
        trace = observed["winner_trace"]
        raw = [
            candidate
            for candidate in trace["raw_candidates"]
            if candidate.get("candidate_id") == record["selector_id"]
        ]
        self.assertEqual(1, len(raw))
        self._assert_candidate_contract(
            record,
            raw[0],
            surface="raw_candidates",
        )
        self._assert_candidate_contract(
            record,
            trace["selected_candidate"],
            surface="selected_candidate",
        )
        self.assertEqual(
            record["foundations"],
            tuple(
                observed["route_decision"]["route_result"][
                    "layer3_skills"
                ]
            ),
        )

    def test_r0_10b_converted_and_deferred_parity(self) -> None:
        record = {
            "selector_id": (
                "implementation-owner:"
                "platform-infrastructure-change-builder"
            ),
            "routing_family": "platform-infrastructure",
            "foundations": ("infrastructure-as-code-safety",),
            "primary_skill": (
                "platform-infrastructure-change-builder"
            ),
            "review_skill": "ai-code-review-refactor",
            "source_evidence": (
                "effect-changed",
                "explicit-preparation-action",
                "infrastructure-definition",
            ),
            "evidence_ids": (
                "effect-changed",
                "explicit-preparation-action",
                "infrastructure-definition",
                "dynamic-helper:_implementation_owner_layer3",
                "foundation-selector:dynamic-foundation:"
                "infrastructure-as-code-safety",
            ),
        }
        observed = self._route_case("t2b-preparation-platform")
        trace = observed["winner_trace"]
        accepted = copy.deepcopy(trace)
        owner_id = record["selector_id"]
        selected_context = accepted["selected_candidate"][
            "candidate_layer3_context"
        ]
        owner_lists = {
            "owner-context": selected_context["owners"],
            "raw": [
                candidate
                for candidate in accepted["raw_candidates"]
                if candidate.get("candidate_id") == owner_id
            ],
            "excluded": [
                candidate
                for candidate in accepted["excluded_candidates"]
                if candidate.get("candidate_id") == owner_id
            ],
        }
        for rows in owner_lists.values():
            self.assertEqual(1, len(rows))
            rows[0]["evidence"] = list(record["evidence_ids"])
        self._assert_preparation_owner_trace_contract(
            accepted,
            [record],
        )

        parity_fields = (
            "candidate_id",
            "routing_family",
            "primary_skill",
            "foundation_requests",
            "review_skill",
            "evidence",
        )
        for surface in ("owner-context", "raw", "excluded"):
            for field in parity_fields:
                with self.subTest(surface=surface, field=field):
                    mutated = copy.deepcopy(accepted)
                    if surface == "owner-context":
                        row = mutated["selected_candidate"][
                            "candidate_layer3_context"
                        ]["owners"][0]
                    else:
                        row = next(
                            candidate
                            for candidate in mutated[
                                f"{surface}_candidates"
                            ]
                            if candidate.get("candidate_id") == owner_id
                        )
                    if field == "candidate_id":
                        row[field] = "__forged-owner-id__"
                    elif field == "routing_family":
                        row[field] = "__forged-family__"
                    elif field == "primary_skill":
                        row[field] = "__forged-primary__"
                    elif field == "foundation_requests":
                        if surface == "owner-context":
                            row[field] = [
                                "repository-context-map",
                                *row[field],
                            ]
                        else:
                            row["candidate_layer3_context"][field] = [
                                "repository-context-map",
                                *row["candidate_layer3_context"][field],
                            ]
                    elif field == "review_skill":
                        row[field] = "__forged-review__"
                    else:
                        row[field] = list(reversed(row[field]))
                    with self.assertRaises(AssertionError):
                        self._assert_preparation_owner_trace_contract(
                            mutated,
                            [record],
                        )

        for surface in ("owner-context", "raw", "excluded"):
            for occurrence in ("missing", "duplicate"):
                with self.subTest(
                    surface=surface,
                    occurrence=occurrence,
                ):
                    mutated = copy.deepcopy(accepted)
                    if surface == "owner-context":
                        container = mutated["selected_candidate"][
                            "candidate_layer3_context"
                        ]["owners"]
                    else:
                        container = mutated[
                            f"{surface}_candidates"
                        ]
                    row = next(
                        candidate
                        for candidate in container
                        if candidate.get("candidate_id") == owner_id
                    )
                    if occurrence == "missing":
                        container.remove(row)
                    else:
                        container.append(copy.deepcopy(row))
                    with self.assertRaises(AssertionError):
                        self._assert_preparation_owner_trace_contract(
                            mutated,
                            [record],
                        )

        for surface in ("raw", "excluded"):
            with self.subTest(surface=surface, field="reason"):
                mutated = copy.deepcopy(accepted)
                row = next(
                    candidate
                    for candidate in mutated[
                        f"{surface}_candidates"
                    ]
                    if candidate.get("candidate_id") == owner_id
                )
                if surface == "raw":
                    row["reason"] = (
                        "lower-precedence-than-implementation-preparation"
                    )
                else:
                    row["reason"] = "__forged-exclusion-reason__"
                with self.assertRaises(AssertionError):
                    self._assert_preparation_owner_trace_contract(
                        mutated,
                        [record],
                    )

        self._assert_preparation_owner_trace_contract(trace, [record])

    def test_r0_10c_merged_composite_parity(self) -> None:
        case = next(
            row
            for row in self.routing["cases"]
            if row.get("id") == "domain-invariant"
        )
        observed = ORACLE.route_with_trace(
            case["prompt"],
            main_execution=copy.deepcopy(case["main_execution"]),
        )
        public = ORACLE.route(
            case["prompt"],
            main_execution=copy.deepcopy(case["main_execution"]),
        )
        trace = observed["winner_trace"]
        selected = trace["selected_candidate"]
        trace_bytes = _canonical_json_bytes(trace)
        source_candidates_by_id = {
            candidate_id: selected
            for candidate_id in selected["source_candidate_ids"]
        }
        source_rows = self._assert_source_foundation_trace_contract(
            trace,
            "R0-10c",
            source_candidates_by_id,
        )
        self._assert_source_foundation_mutations_detected(
            trace,
            "R0-10c",
            overflow=False,
        )
        self.assertEqual(trace_bytes, _canonical_json_bytes(trace))
        self.assertEqual(public, observed["route_decision"])
        self.assertFalse(
            _contains_mapping_key(
                observed["route_decision"],
                "source_foundation_candidates",
            )
        )
        expected_ids = [row["candidate_id"] for row in source_rows]
        expected_foundations = [
            foundation
            for row in source_rows
            for foundation in row["foundations"]
        ]
        expected_evidence = tuple(
            self._source_foundation_evidence(
                source_rows,
                overflow=False,
            )
        )
        self.assertEqual(
            expected_ids,
            selected["source_candidate_ids"],
        )
        self.assertEqual(
            expected_foundations,
            selected["layer3_skills"],
        )
        self.assertEqual(
            expected_evidence,
            tuple(selected["evidence"]),
        )
        self.assertTrue(
            all(
                (
                    row["owner_binding"]["primary_skill"],
                    row["owner_binding"]["review_skill"],
                )
                == (
                    selected["primary_skill"],
                    selected["review_skill"],
                )
                for row in source_rows
            )
        )
        self.assertEqual(
            expected_foundations,
            observed["route_decision"]["route_result"]["layer3_skills"],
        )

    def test_r0_10d_conflict_preserves_sources_and_fails_closed(
        self,
    ) -> None:
        projections = VALIDATION.foundation_runtime_matcher_authority(
            copy.deepcopy(self.foundation),
            context="R0-10d matcher projections",
        )
        projections = copy.deepcopy(
            [projections[0], projections[2]]
        )
        records = [
            {
                "selector_id": projection["activation_id"],
                "foundations": (projection["name"],),
                "primary_skill": projection["primary_skill"],
                "review_skill": projection["review_skill"],
                "source_evidence": tuple(
                    projection["matcher_evidence"]
                ),
                "evidence_ids": (
                    *projection["matcher_evidence"],
                    "foundation-selector:"
                    f"{projection['activation_id']}",
                ),
            }
            for projection in projections
        ]
        with (
            mock.patch.object(
                ORACLE,
                "foundation_runtime_matcher_authority",
                return_value=projections,
            ),
            mock.patch.object(
                ORACLE,
                "_foundation_runtime_matcher_matches",
                return_value=True,
            ),
        ):
            observed = ORACLE.route_with_trace(
                "Analyze a bounded domain decision.",
                main_execution=_main_execution(
                    "r0-10d-conflict-parity"
                ),
            )
        trace = observed["winner_trace"]
        self._assert_source_foundation_trace_contract(
            trace,
            "R0-10d",
            {
                candidate["candidate_id"]: candidate
                for candidate in trace["raw_candidates"]
                if "source_foundation_candidates" in candidate
            },
        )
        self.assertEqual(
            "route-contract-conflict",
            trace["selected_candidate"]["candidate_id"],
        )
        self.assertEqual(
            [record["selector_id"] for record in records],
            trace["selected_candidate"]["source_candidate_ids"],
        )
        raw_by_id = {
            candidate["candidate_id"]: candidate
            for candidate in trace["raw_candidates"]
        }
        excluded_by_id = {
            candidate["candidate_id"]: candidate
            for candidate in trace["excluded_candidates"]
        }
        for record in records:
            self._assert_candidate_contract(
                record,
                raw_by_id[record["selector_id"]],
                surface="conflict raw_candidates",
            )
            self.assertEqual(
                raw_by_id[record["selector_id"]]["evidence"],
                excluded_by_id[record["selector_id"]]["evidence"],
            )
        self.assertTrue(
            set(record["foundations"][0] for record in records).isdisjoint(
                observed["route_decision"]["route_result"][
                    "layer3_skills"
                ]
            )
        )

    def test_r0_10e_overflow_preserves_order_and_fails_closed(self) -> None:
        names = (
            "audit-evidence-integrity",
            "authentication-authorization",
            "privacy-data-lifecycle",
            "authentication-security",
        )
        template = VALIDATION.foundation_runtime_matcher_authority(
            copy.deepcopy(self.foundation),
            context="R0-10e matcher projection",
        )[0]
        projection_by_name = {
            projection["name"]: projection
            for projection in VALIDATION.foundation_runtime_matcher_authority(
                copy.deepcopy(self.foundation),
                context="R0-10e source projections",
            )
        }
        records = []
        for name in names:
            if name in projection_by_name:
                projection = projection_by_name[name]
                records.append(
                    {
                        "selector_id": projection["activation_id"],
                        "foundations": (name,),
                        "primary_skill": "security-privacy-gate",
                        "review_skill": "security-privacy-gate",
                        "source_evidence": tuple(
                            projection["matcher_evidence"]
                        ),
                        "evidence_ids": (
                            *projection["matcher_evidence"],
                            "foundation-selector:"
                            f"{projection['activation_id']}",
                        ),
                    }
                )
            else:
                source = _direct_selector_contract(
                    name,
                    set(self.foundation_rows),
                )
                source["primary_skill"] = "security-privacy-gate"
                source["review_skill"] = "security-privacy-gate"
                records.append(source)
        projections = []
        for record, name in zip(records, names, strict=True):
            projection = copy.deepcopy(template)
            projection.update(
                {
                    "name": name,
                    "activation_id": record["selector_id"],
                    "primary_skill": "security-privacy-gate",
                    "review_skill": "security-privacy-gate",
                    "matcher_evidence": list(record["evidence_ids"]),
                }
            )
            projections.append(projection)
        execution = _main_execution("r0-10e-overflow-parity")
        with (
            mock.patch.object(
                ORACLE,
                "foundation_runtime_matcher_authority",
                return_value=projections,
            ),
            mock.patch.object(
                ORACLE,
                "_foundation_runtime_matcher_matches",
                return_value=True,
            ),
        ):
            observed = ORACLE.route_with_trace(
                "Analyze a bounded domain decision.",
                main_execution=copy.deepcopy(execution),
            )
            public = ORACLE.route(
                "Analyze a bounded domain decision.",
                main_execution=copy.deepcopy(execution),
            )
        trace = observed["winner_trace"]
        selected = trace["selected_candidate"]
        trace_bytes = _canonical_json_bytes(trace)
        source_candidates_by_id = {
            projection["activation_id"]: projection
            for projection in projections
        }
        self.assertEqual(
            set(source_candidates_by_id),
            set(selected["source_candidate_ids"]),
        )
        source_rows = self._assert_source_foundation_trace_contract(
            trace,
            "R0-10e",
            source_candidates_by_id,
        )
        self._assert_source_foundation_mutations_detected(
            trace,
            "R0-10e",
            overflow=True,
        )
        self.assertEqual(trace_bytes, _canonical_json_bytes(trace))
        self.assertEqual(public, observed["route_decision"])
        self.assertFalse(
            _contains_mapping_key(
                observed["route_decision"],
                "source_foundation_candidates",
            )
        )
        self.assertEqual(
            "foundation-layer3-overflow",
            selected["candidate_id"],
        )
        self.assertEqual(
            [row["candidate_id"] for row in source_rows],
            selected["source_candidate_ids"],
        )
        self.assertTrue(
            all(
                (
                    row["owner_binding"]["primary_skill"],
                    row["owner_binding"]["review_skill"],
                )
                == (
                    source_candidates_by_id[row["candidate_id"]][
                        "primary_skill"
                    ],
                    source_candidates_by_id[row["candidate_id"]][
                        "review_skill"
                    ],
                )
                for row in source_rows
            )
        )
        self.assertTrue(
            set(names).isdisjoint(
                observed["route_decision"]["route_result"][
                    "layer3_skills"
                ]
            )
        )

    def test_r0_10f_derived_owner_overflow_is_not_foundation_carrier(
        self,
    ) -> None:
        prompt = (
            "Implement a Node.js backend service stream pipeline that "
            "atomically replaces a local file and includes Kotlin coroutine "
            "code plus C# CancellationToken async disposal behavior."
        )
        execution = _main_execution("r0-10f-owner-overflow-negative")
        observed = ORACLE.route_with_trace(
            prompt,
            main_execution=copy.deepcopy(execution),
        )
        public = ORACLE.route(
            prompt,
            main_execution=copy.deepcopy(execution),
        )
        trace = observed["winner_trace"]
        selected = trace["selected_candidate"]
        self.assertEqual(
            {
                "candidate_id",
                "candidate_type",
                "eligible_domain_layer3_skills",
                "eligible_foundation_layer3_skills",
                "eligible_layer3_skills",
                "evidence",
                "layer3_overflow",
                "layer3_skills",
                "path",
                "precedence",
                "primary_skill",
                "profile",
                "reason",
                "reserved_domain_capacity",
                "review_skill",
                "source_candidate_ids",
            },
            set(selected),
        )
        selected_bytes = _canonical_json_bytes(selected)
        self.assertEqual(731, len(selected_bytes))
        self.assertEqual(
            "7fb0067283865ee05cb4b90a4dbeaf7cd8987a9e5cf7fe70a978b3921e92fa88",
            _sha256(selected_bytes),
        )
        self.assertEqual(
            ["foundation-layer3-overflow"],
            selected["evidence"],
        )
        route_result = observed["route_decision"]["route_result"]
        self.assertEqual(
            {
                "path": "analyzed",
                "route_once": True,
                "start_profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                "path": observed["route_decision"]["path"],
                "route_once": observed["route_decision"]["route_once"],
                "start_profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            },
        )
        self.assertFalse(_carries_source_foundation_candidates(selected))
        self.assertTrue(
            _contains_mapping_key(
                trace,
                "source_foundation_candidates",
            )
        )
        self.assertFalse(
            _contains_mapping_key(
                observed["route_decision"],
                "source_foundation_candidates",
            )
        )
        authority = self._authority("R0-10f")
        owner_candidates = [
            candidate
            for candidate in trace["raw_candidates"]
            if candidate["candidate_id"].startswith(
                "implementation-owner:"
            )
        ]
        self.assertTrue(owner_candidates)
        for candidate in owner_candidates:
            foundations = set(
                candidate["eligible_foundation_layer3_skills"]
            )
            expected_records = [
                record
                for record in self._foundation_records(authority)
                if foundations.intersection(record.foundations)
            ]
            expected_ids = [
                record.selector_id for record in expected_records
            ]
            source_rows = candidate["source_foundation_candidates"]
            self.assertEqual(
                expected_ids,
                [row["candidate_id"] for row in source_rows],
            )
            self.assertTrue(
                all(
                    row["evidence"][-1]
                    == f"foundation-selector:{row['candidate_id']}"
                    for row in source_rows
                )
            )
            self.assertFalse(
                any(
                    item.startswith(
                        "foundation-selector:implementation-owner:"
                    )
                    for item in candidate["evidence"]
                )
            )
        self.assertEqual(
            "7fb0067283865ee05cb4b90a4dbeaf7cd8987a9e5cf7fe70a978b3921e92fa88",
            _sha256(_canonical_json_bytes(selected)),
        )
        self.assertEqual(public, observed["route_decision"])

    def test_r0_10g_foundation_alias_resolves_exact_source_row(self) -> None:
        authority = self._authority("R0-10g")
        record = self._record_for_foundation(
            authority,
            "documentation-generation",
        )
        trace = self._route_case("documentation")["winner_trace"]
        selected = trace["selected_candidate"]
        self.assertEqual("migration-documentation", selected["candidate_id"])
        self.assertEqual(
            [
                {
                    "candidate_id": record.selector_id,
                    "foundations": list(record.foundations),
                    "evidence": list(record.evidence_ids),
                    "owner_binding": {
                        "primary_skill": selected["primary_skill"],
                        "review_skill": selected["review_skill"],
                    },
                }
            ],
            selected.get("source_foundation_candidates"),
            "[R0-10g-alias-authority-bypass] a noncanonical route ID may "
            "not carry a Foundation without its exact selector source row",
        )
        self.assertTrue(
            _is_ordered_subsequence(
                record.evidence_ids,
                tuple(selected["evidence"]),
            )
        )

    def test_r0_10h_missing_selector_terminal_fails_closed(self) -> None:
        def remove_terminal(candidate: dict[str, object]) -> None:
            candidate["evidence"].remove(
                "foundation-selector:security-anti-input-shape"
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "lost exact selector evidence",
        ):
            self._route_case_with_built_candidate_mutation(
                "security-anti-input-shape",
                "security-anti-input-shape",
                remove_terminal,
            )

    def test_r0_10i_fabricated_selector_terminal_fails_closed(self) -> None:
        def add_terminal(candidate: dict[str, object]) -> None:
            candidate["evidence"].append(
                "foundation-selector:fabricated-terminal"
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector terminal",
        ):
            self._route_case_with_built_candidate_mutation(
                "security-anti-input-shape",
                "security-anti-input-shape",
                add_terminal,
            )

    def test_r0_10j_registry_compatible_primary_forge_fails_closed(
        self,
    ) -> None:
        def forge_primary(candidate: dict[str, object]) -> None:
            candidate["primary_skill"] = "data-middleware-change-builder"

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector owner binding",
        ):
            self._route_case_with_built_candidate_mutation(
                "backend-idempotency",
                "backend-idempotency-analysis",
                forge_primary,
            )

    def test_r0_10k_registry_compatible_review_forge_fails_closed(
        self,
    ) -> None:
        def forge_review(candidate: dict[str, object]) -> None:
            candidate["review_skill"] = "ai-code-review-refactor"

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector owner binding",
        ):
            self._route_case_with_built_candidate_mutation(
                "security-anti-input-shape",
                "security-anti-input-shape",
                forge_review,
            )

    def test_r0_10l_unknown_rule_with_foundation_fails_closed(
        self,
    ) -> None:
        def forge_rule(candidate: dict[str, object]) -> None:
            candidate["candidate_id"] = "fabricated-foundation-rule"
            candidate["rule_id"] = "fabricated-foundation-rule"

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "unknown Foundation route rule",
        ):
            self._route_case_with_built_candidate_mutation(
                "security-anti-input-shape",
                "security-anti-input-shape",
                forge_rule,
            )

    def test_r0_10m_canonical_route_rejects_record_internal_pair_swap(
        self,
    ) -> None:
        def swap_to_other_record_pair(candidate: dict[str, object]) -> None:
            self._replace_foundation_route_binding(
                candidate,
                primary_skill="engineering-change-analysis",
                review_skill="architecture-impact-reviewer",
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector owner binding",
        ):
            self._route_case_with_built_candidate_mutation(
                "release",
                "production-release-decision",
                swap_to_other_record_pair,
            )

    def test_r0_10n_alias_rejects_record_internal_pair_swap(self) -> None:
        def swap_to_other_record_pair(candidate: dict[str, object]) -> None:
            self._replace_foundation_route_binding(
                candidate,
                primary_skill="engineering-change-analysis",
                review_skill="architecture-impact-reviewer",
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector owner binding",
        ):
            self._route_case_with_built_candidate_mutation(
                "accepted-api-analysis",
                "api-compatibility-artifact",
                swap_to_other_record_pair,
            )

    def test_r0_10o_dynamic_route_rejects_other_exact_owner_scope(
        self,
    ) -> None:
        def swap_to_other_dynamic_scope(
            candidate: dict[str, object],
        ) -> None:
            self._replace_foundation_route_binding(
                candidate,
                candidate_id=(
                    "implementation-owner:"
                    "repository-tooling-change-builder"
                ),
                routing_family="repository-tooling",
                primary_skill="repository-tooling-change-builder",
                review_skill="ai-code-review-refactor",
            )
            evidence = candidate["evidence"]
            self.assertIsInstance(evidence, list)
            evidence.remove("backend-surface")
            evidence.append("repository-developer-tool")

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "classifier origin",
        ):
            self._route_case_with_built_candidate_mutation(
                "structure-filesystem-safety-not-placement",
                "implementation-owner:backend-change-builder",
                swap_to_other_dynamic_scope,
            )

    def test_r0_10p_alias_map_producer_and_literal_closure(self) -> None:
        literal_variants = {
            (
                fixture["alias_id"],
                fixture["source_ids"],
                fixture["primary_skill"],
                fixture["review_skill"],
            )
            for fixture in FOUNDATION_ALIAS_PRODUCER_FIXTURES
        }
        self.assertEqual(37, len(FOUNDATION_ALIAS_PRODUCER_FIXTURES))
        self.assertEqual(37, len(literal_variants))

        production_variants = {
            (alias_id, source_ids, primary_skill, review_skill)
            for alias_id, bindings in (
                ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS.items()
            )
            for source_ids, primary_skill, review_skill in bindings
        }
        literal_alias_ids = {
            fixture["alias_id"]
            for fixture in FOUNDATION_ALIAS_PRODUCER_FIXTURES
        }
        route_impl = _function_node(ORACLE_PATH, "_route_impl")
        producer_alias_ids = {
            keyword.value.value
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Call)
            for keyword in node.keywords
            if keyword.arg == "rule_id"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
            and keyword.value.value
            in ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS
        }
        self.assertEqual(
            set(ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS),
            producer_alias_ids,
        )
        self.assertEqual(producer_alias_ids, literal_alias_ids)
        self.assertEqual(production_variants, literal_variants)
        self.assertEqual(
            {
                fixture["alias_id"]: fixture["member_subset"]
                for fixture in FOUNDATION_ALIAS_PRODUCER_FIXTURES
                if "member_subset" in fixture
            },
            getattr(ORACLE, "_FOUNDATION_ALIAS_MEMBER_SUBSETS", {}),
        )

        for fixture in FOUNDATION_ALIAS_PRODUCER_FIXTURES:
            with self.subTest(fixture=fixture["fixture_id"]):
                observed = ORACLE.route_with_trace(
                    fixture["prompt"],
                    main_execution=_main_execution(
                        fixture["fixture_id"],
                    ),
                )
                matches = [
                    candidate
                    for candidate
                    in observed["winner_trace"]["raw_candidates"]
                    if candidate.get("candidate_id")
                    == fixture["alias_id"]
                ]
                self.assertEqual(1, len(matches))
                candidate = matches[0]
                self.assertEqual(
                    fixture["source_ids"],
                    tuple(
                        row["candidate_id"]
                        for row in candidate[
                            "source_foundation_candidates"
                        ]
                    ),
                )
                self.assertEqual(
                    (
                        fixture["primary_skill"],
                        fixture["review_skill"],
                    ),
                    (
                        candidate["primary_skill"],
                        candidate["review_skill"],
                    ),
                )
                if "member_subset" in fixture:
                    self.assertEqual(
                        list(fixture["member_subset"]),
                        candidate["layer3_skills"],
                    )

    def test_r0_10p2_experience_member_alias_tampering_fails_closed(
        self,
    ) -> None:
        record = self._record_for_selector(
            self._authority("R0-10p2"),
            "user-flow-analysis",
        )
        self.assertEqual(
            (
                "interaction-state-modeling",
                "design-system-rules",
            ),
            record.foundations,
        )

        def unknown_rule(candidate: dict[str, object]) -> None:
            candidate["candidate_id"] = "unknown-experience-rule"
            candidate["rule_id"] = "unknown-experience-rule"

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "unknown Foundation route rule",
        ):
            self._route_case_with_built_candidate_mutation(
                "experience-analysis",
                "experience-interaction-analysis",
                unknown_rule,
            )

        def swap_owner(candidate: dict[str, object]) -> None:
            self._replace_foundation_route_binding(
                candidate,
                primary_skill="frontend-change-builder",
                review_skill="ai-code-review-refactor",
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector owner binding",
        ):
            self._route_case_with_built_candidate_mutation(
                "experience-analysis",
                "experience-interaction-analysis",
                swap_owner,
            )

        def remove_terminal(candidate: dict[str, object]) -> None:
            evidence = candidate["evidence"]
            self.assertIsInstance(evidence, list)
            evidence.remove("foundation-selector:user-flow-analysis")

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "lost exact selector evidence",
        ):
            self._route_case_with_built_candidate_mutation(
                "experience-analysis",
                "experience-interaction-analysis",
                remove_terminal,
            )

        def relabel_sibling(candidate: dict[str, object]) -> None:
            candidate["layer3_skills"] = ["design-system-rules"]

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "fixed Layer 3 candidate differs from its request context",
        ):
            self._route_case_with_built_candidate_mutation(
                "experience-analysis",
                "experience-interaction-analysis",
                relabel_sibling,
            )

    def test_external_integration_member_alias_tampering_fails_closed(
        self,
    ) -> None:
        record = self._record_for_selector(
            self._authority("external-integration-member-alias"),
            "external-integration-analysis",
        )
        self.assertEqual(
            (
                "consumer-impact-analysis",
                "failure-contract-design",
            ),
            record.foundations,
        )

        consumer_alias = (
            "external-integration-consumer-impact-analysis"
        )
        failure_alias = (
            "external-integration-failure-contract-analysis"
        )

        without_consumer_binding = {
            alias_id: bindings
            for alias_id, bindings
            in ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS.items()
            if alias_id != consumer_alias
        }
        with mock.patch.object(
            ORACLE,
            "_FOUNDATION_ALIAS_SOURCE_BINDINGS",
            without_consumer_binding,
        ):
            with self.assertRaisesRegex(
                ORACLE.RoutingIntegrityError,
                "unknown Foundation route rule",
            ):
                self._route_case("external-integration-consumer-only")

        swapped_consumer_binding = dict(
            ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS
        )
        swapped_consumer_binding[consumer_alias] = (
            (
                ("user-flow-analysis",),
                "engineering-change-analysis",
                "ai-code-review-refactor",
            ),
        )
        with mock.patch.object(
            ORACLE,
            "_FOUNDATION_ALIAS_SOURCE_BINDINGS",
            swapped_consumer_binding,
        ):
            with self.assertRaisesRegex(
                ORACLE.RoutingIntegrityError,
                "undeclared selector owner binding",
            ):
                self._route_case("external-integration-consumer-only")

        def unknown_identity(candidate: dict[str, object]) -> None:
            candidate["candidate_id"] = "unknown-external-member"
            candidate["rule_id"] = "unknown-external-member"

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "unknown Foundation route rule",
        ):
            self._route_case_with_built_candidate_mutation(
                "external-integration-consumer-only",
                consumer_alias,
                unknown_identity,
            )

        def swap_owner(candidate: dict[str, object]) -> None:
            self._replace_foundation_route_binding(
                candidate,
                primary_skill="integration-change-builder",
                review_skill="ai-code-review-refactor",
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "undeclared selector owner binding",
        ):
            self._route_case_with_built_candidate_mutation(
                "external-integration-consumer-only",
                consumer_alias,
                swap_owner,
            )

        def relabel_sibling(candidate: dict[str, object]) -> None:
            candidate["layer3_skills"] = ["failure-contract-design"]

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "fixed Layer 3 candidate differs from its request context",
        ):
            self._route_case_with_built_candidate_mutation(
                "external-integration-consumer-only",
                consumer_alias,
                relabel_sibling,
            )

        def change_canonical_source_row(
            candidate: dict[str, object],
        ) -> None:
            rows = candidate["source_foundation_candidates"]
            self.assertIsInstance(rows, list)
            rows[0]["foundations"] = ["consumer-impact-analysis"]

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "did not resolve exact selector source rows",
        ):
            self._route_case_with_built_candidate_mutation(
                "external-integration-consumer-only",
                consumer_alias,
                change_canonical_source_row,
            )

        def remove_terminal(candidate: dict[str, object]) -> None:
            evidence = candidate["evidence"]
            self.assertIsInstance(evidence, list)
            evidence.remove(
                "foundation-selector:external-integration-analysis"
            )

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "lost exact selector evidence",
        ):
            self._route_case_with_built_candidate_mutation(
                "external-integration-failure-only",
                failure_alias,
                remove_terminal,
            )

    def test_r0_10q_review_risk_rejects_complete_other_family_scope(
        self,
    ) -> None:
        target = self._route_case(
            "t2c-preparation-reliability-risk"
        )["winner_trace"]["raw_candidates"]
        replacements = [
            candidate
            for candidate in target
            if candidate.get("candidate_id")
            == "review-reliability-risk"
        ]
        self.assertEqual(1, len(replacements))

        with self.assertRaisesRegex(
            ORACLE.RoutingIntegrityError,
            "classifier origin",
        ):
            self._route_case_with_enriched_candidate_replacement(
                "t2c-review-regression-security-risk",
                "review-security-risk",
                replacements[0],
            )

    def test_r0_10r_route_binding_maps_are_exact_and_unambiguous(
        self,
    ) -> None:
        observed_full_identities: set[
            tuple[str, str, str | None, str | None, str, str]
        ] = set()
        primary_by_scope: dict[
            tuple[str, str, str | None, str | None],
            str,
        ] = {}
        reviews_by_owner: dict[
            tuple[str, str, str | None, str | None, str],
            set[str],
        ] = {}
        route_specs_by_selector: dict[
            str,
            list[tuple[object, ...]],
        ] = {}
        for label, bindings_by_selector in (
            (
                "additional",
                ORACLE._FOUNDATION_SELECTOR_ADDITIONAL_OWNER_BINDINGS,
            ),
            ("dynamic", ORACLE._DYNAMIC_FOUNDATION_OWNER_BINDINGS),
        ):
            self.assertIsInstance(bindings_by_selector, dict)
            for selector_id, bindings in bindings_by_selector.items():
                self.assertIsInstance(selector_id, str)
                self.assertIsInstance(bindings, tuple)
                self.assertTrue(bindings)
                for binding in bindings:
                    self.assertIsInstance(binding, tuple)
                    self.assertEqual(
                        5,
                        len(binding),
                        f"{label} binding lacks exact route scope",
                    )
                    (
                        candidate_id,
                        rule_id,
                        routing_family,
                        primary_skill,
                        review_skill,
                    ) = binding
                    self.assertIsInstance(candidate_id, str)
                    self.assertTrue(
                        rule_id is None or isinstance(rule_id, str)
                    )
                    self.assertTrue(
                        routing_family is None
                        or isinstance(routing_family, str)
                    )
                    self.assertIsInstance(primary_skill, str)
                    self.assertIsInstance(review_skill, str)
                    self.assertTrue(primary_skill)
                    self.assertTrue(review_skill)
                    self.assertNotEqual("*", review_skill)
                    self.assertIn(
                        review_skill,
                        ORACLE._EXPECTED_REVIEW_TASK_SKILLS,
                    )
                    scope = (
                        selector_id,
                        candidate_id,
                        rule_id,
                        routing_family,
                    )
                    full_identity = (
                        *scope,
                        primary_skill,
                        review_skill,
                    )
                    self.assertNotIn(
                        full_identity,
                        observed_full_identities,
                        f"{label} route binding is duplicated",
                    )
                    observed_full_identities.add(full_identity)
                    if scope in primary_by_scope:
                        self.assertEqual(
                            primary_by_scope[scope],
                            primary_skill,
                            f"{label} route scope has a second primary",
                        )
                    else:
                        primary_by_scope[scope] = primary_skill
                    owner_identity = (*scope, primary_skill)
                    owner_reviews = reviews_by_owner.setdefault(
                        owner_identity,
                        set(),
                    )
                    self.assertNotIn(
                        review_skill,
                        owner_reviews,
                        f"{label} owner review is duplicated",
                    )
                    owner_reviews.add(review_skill)
                    route_specs_by_selector.setdefault(
                        selector_id,
                        [],
                    ).append(binding)

        alias_scopes: set[tuple[str, tuple[str, ...]]] = set()
        alias_bindings_by_id: dict[
            str,
            list[tuple[tuple[str, ...], str, str]],
        ] = {}
        for alias_id, bindings in (
            ORACLE._FOUNDATION_ALIAS_SOURCE_BINDINGS.items()
        ):
            self.assertIsInstance(alias_id, str)
            self.assertIsInstance(bindings, tuple)
            self.assertTrue(bindings)
            for binding in bindings:
                self.assertIsInstance(binding, tuple)
                self.assertEqual(
                    3,
                    len(binding),
                    "alias binding lacks exact sources and owner pair",
                )
                source_ids, primary_skill, review_skill = binding
                self.assertIsInstance(source_ids, tuple)
                self.assertTrue(source_ids)
                self.assertTrue(
                    all(isinstance(item, str) for item in source_ids)
                )
                self.assertIsInstance(primary_skill, str)
                self.assertIsInstance(review_skill, str)
                scope = (alias_id, source_ids)
                self.assertNotIn(
                    scope,
                    alias_scopes,
                    "alias source scope has multiple owner pairs",
                )
                alias_scopes.add(scope)
                alias_bindings_by_id.setdefault(alias_id, []).append(
                    binding
                )

        authority = self._authority("R0-10p")
        records_by_id = {
            record.selector_id: record
            for record in self._foundation_records(authority)
        }

        def candidate_for_spec(
            spec: tuple[object, ...],
        ) -> dict[str, object]:
            (
                candidate_id,
                rule_id,
                routing_family,
                primary_skill,
                review_skill,
            ) = spec
            evidence = []
            if (
                isinstance(candidate_id, str)
                and candidate_id.startswith("implementation-owner:")
            ):
                evidence.append(
                    ORACLE._IMPLEMENTATION_OWNER_FAMILY_EVIDENCE[
                        routing_family
                    ]
                )
            candidate = {
                "candidate_id": candidate_id,
                "rule_id": rule_id,
                "routing_family": routing_family,
                "primary_skill": primary_skill,
                "review_skill": review_skill,
                "evidence": evidence,
            }
            if candidate_id == "implementation-preparation":
                candidate["candidate_layer3_context"] = {
                    "kind": "preparation",
                    "risk": {"review_skill": review_skill},
                    "owners": [],
                }
            return candidate

        for selector_id, specs in route_specs_by_selector.items():
            record = records_by_id[selector_id]
            declared_specs = set(specs)
            record_pairs = {
                (owner.primary_skill, owner.review_skill)
                for owner in record.owner_bindings
            }
            for spec in specs:
                candidate = candidate_for_spec(spec)
                self.assertTrue(
                    ORACLE._foundation_route_binding_declared(
                        candidate,
                        [record],
                    )
                )
                exact_pair = (spec[-2], spec[-1])
                for alternate_pair in record_pairs - {exact_pair}:
                    mutated = copy.deepcopy(candidate)
                    (
                        mutated["primary_skill"],
                        mutated["review_skill"],
                    ) = alternate_pair
                    expected = (
                        spec[0],
                        spec[1],
                        spec[2],
                        *alternate_pair,
                    ) in declared_specs
                    self.assertEqual(
                        expected,
                        ORACLE._foundation_route_binding_declared(
                            mutated,
                            [record],
                        ),
                        f"{selector_id} alternate review pair did not match "
                        "the exact declared spec set",
                    )
                if str(spec[0]).startswith("implementation-owner:"):
                    for other in specs:
                        if (
                            other[:4] == spec[:4]
                            or not str(other[0]).startswith(
                                "implementation-owner:"
                            )
                        ):
                            continue
                        mutated = candidate_for_spec(other)
                        mutated["evidence"] = list(candidate["evidence"])
                        self.assertFalse(
                            ORACLE._foundation_route_binding_declared(
                                mutated,
                                [record],
                            ),
                            f"{selector_id} accepted another automatic "
                            "owner scope with the original family evidence",
                        )

        for record in records_by_id.values():
            if record.source.kind == "dynamic-helper-only":
                continue
            direct = record.owner_bindings[0]
            direct_pair = (
                direct.primary_skill,
                direct.review_skill,
            )
            candidate = {
                "candidate_id": record.selector_id,
                "rule_id": record.selector_id,
                "routing_family": None,
                "primary_skill": direct_pair[0],
                "review_skill": direct_pair[1],
            }
            self.assertTrue(
                ORACLE._foundation_route_binding_declared(
                    candidate,
                    [record],
                )
            )
            for alternate in {
                (owner.primary_skill, owner.review_skill)
                for owner in record.owner_bindings[1:]
            }:
                mutated = copy.deepcopy(candidate)
                (
                    mutated["primary_skill"],
                    mutated["review_skill"],
                ) = alternate
                self.assertFalse(
                    ORACLE._foundation_route_binding_declared(
                        mutated,
                        [record],
                    ),
                    f"canonical {record.selector_id} accepted another "
                    f"record pair {alternate!r}",
                )

        for alias_id, bindings in alias_bindings_by_id.items():
            for source_ids, primary_skill, review_skill in bindings:
                records = [
                    records_by_id[source_id]
                    for source_id in source_ids
                ]
                candidate = {
                    "candidate_id": alias_id,
                    "rule_id": alias_id,
                    "routing_family": None,
                    "primary_skill": primary_skill,
                    "review_skill": review_skill,
                    "layer3_skills": list(
                        getattr(
                            ORACLE,
                            "_FOUNDATION_ALIAS_MEMBER_SUBSETS",
                            {},
                        ).get(alias_id, ())
                    ),
                }
                self.assertTrue(
                    ORACLE._foundation_route_binding_declared(
                        candidate,
                        records,
                    )
                )
                common_pairs = set.intersection(
                    *(
                        {
                            (
                                owner.primary_skill,
                                owner.review_skill,
                            )
                            for owner in record.owner_bindings
                        }
                        for record in records
                    )
                )
                for alternate in common_pairs - {
                    (primary_skill, review_skill)
                }:
                    mutated = copy.deepcopy(candidate)
                    (
                        mutated["primary_skill"],
                        mutated["review_skill"],
                    ) = alternate
                    self.assertFalse(
                        ORACLE._foundation_route_binding_declared(
                            mutated,
                            records,
                        ),
                        f"alias {alias_id} accepted another common "
                        f"record pair {alternate!r}",
                    )

        repository_scope = (
            "implementation-owner:repository-tooling-change-builder",
            None,
            "repository-tooling",
            "repository-tooling-change-builder",
            "ai-code-review-refactor",
        )
        repository_candidate = candidate_for_spec(repository_scope)
        build_tool_record = records_by_id[
            "dynamic-foundation:build-tool-professional-usage"
        ]
        validation_record = records_by_id[
            "dynamic-foundation:targeted-validation-selection"
        ]
        backend_record = records_by_id[
            "dynamic-foundation:csharp-dotnet-professional-usage"
        ]
        self.assertFalse(
            ORACLE._foundation_route_binding_declared(
                repository_candidate,
                [build_tool_record, backend_record],
            ),
            "one exact source scope must not authorize a multi-record "
            "Foundation candidate",
        )
        self.assertTrue(
            ORACLE._foundation_route_binding_declared(
                repository_candidate,
                [build_tool_record, validation_record],
            ),
            "every source record authorizing the same exact route scope "
            "must admit the multi-record Foundation candidate",
        )

    def test_r0_10s_automatic_owner_bindings_cover_exact_helper_scopes(
        self,
    ) -> None:
        implementation_scopes = (
            (
                "dynamic",
                "dynamic-foundation:filesystem-process-safety",
                "installed-client",
                "installed-client-change-builder",
                "ai-code-review-refactor",
                "installed-application-surface",
            ),
            (
                "additional",
                "distributed-workflow-analysis",
                "data-middleware",
                "data-middleware-change-builder",
                "ai-code-review-refactor",
                "middleware-surface",
            ),
            (
                "additional",
                "backend-idempotency-analysis",
                "data-middleware",
                "data-middleware-change-builder",
                "ai-code-review-refactor",
                "middleware-surface",
            ),
            (
                "additional",
                "database-migration-analysis",
                "data-middleware",
                "data-middleware-change-builder",
                "ai-code-review-refactor",
                "middleware-surface",
            ),
            (
                "additional",
                "integration-handoff-artifact",
                "integration",
                "integration-change-builder",
                "ai-code-review-refactor",
                "integration-edge",
            ),
            (
                "additional",
                "external-integration-analysis",
                "integration",
                "integration-change-builder",
                "ai-code-review-refactor",
                "integration-edge",
            ),
            (
                "additional",
                "backend-idempotency-analysis",
                "integration",
                "integration-change-builder",
                "ai-code-review-refactor",
                "integration-edge",
            ),
            (
                "dynamic",
                "dynamic-foundation:targeted-validation-selection",
                "test-validation",
                "quality-test-gate",
                "ai-code-review-refactor",
                "behavior-proof-surface",
            ),
            (
                "additional",
                "cryptography-key-lifecycle",
                "logging",
                "logging-design-gate",
                "logging-design-gate",
                "diagnostic-record-surface",
            ),
        )
        maps = {
            "additional": (
                ORACLE._FOUNDATION_SELECTOR_ADDITIONAL_OWNER_BINDINGS
            ),
            "dynamic": ORACLE._DYNAMIC_FOUNDATION_OWNER_BINDINGS,
        }
        authority = self._authority("R0-10s")
        records_by_id = {
            record.selector_id: record
            for record in self._foundation_records(authority)
        }

        for (
            map_name,
            selector_id,
            family,
            primary,
            review,
            family_evidence,
        ) in implementation_scopes:
            with self.subTest(selector_id=selector_id, family=family):
                spec = (
                    f"implementation-owner:{primary}",
                    None,
                    family,
                    primary,
                    review,
                )
                self.assertIn(spec, maps[map_name].get(selector_id, ()))
                candidate = {
                    "candidate_id": spec[0],
                    "rule_id": None,
                    "routing_family": family,
                    "primary_skill": primary,
                    "review_skill": review,
                    "evidence": [family_evidence],
                }
                self.assertTrue(
                    ORACLE._foundation_route_binding_declared(
                        candidate,
                        [records_by_id[selector_id]],
                    )
                )

        middleware_spec = (
            "implementation-owner:data-middleware-change-builder",
            None,
            "data-middleware",
            "data-middleware-change-builder",
            "ai-code-review-refactor",
        )
        middleware_candidate = {
            "candidate_id": middleware_spec[0],
            "rule_id": None,
            "routing_family": "data-middleware",
            "primary_skill": middleware_spec[-2],
            "review_skill": middleware_spec[-1],
            "evidence": ["middleware-surface"],
        }
        middleware_records = [
            records_by_id["distributed-workflow-analysis"],
            records_by_id["backend-idempotency-analysis"],
        ]
        self.assertTrue(
            ORACLE._foundation_route_binding_declared(
                middleware_candidate,
                middleware_records,
            ),
            "every selector contributing to the aggregate middleware owner "
            "must admit the same exact scope",
        )
        for candidate, wrong_marker in (
            (middleware_candidate, "integration-edge"),
            (
                {
                    "candidate_id": (
                        "implementation-owner:integration-change-builder"
                    ),
                    "rule_id": None,
                    "routing_family": "integration",
                    "primary_skill": "integration-change-builder",
                    "review_skill": "ai-code-review-refactor",
                    "evidence": ["integration-edge"],
                },
                "middleware-surface",
            ),
        ):
            mutated = copy.deepcopy(candidate)
            mutated["evidence"] = [wrong_marker]
            selector_id = (
                "backend-idempotency-analysis"
                if candidate["routing_family"] == "integration"
                else "distributed-workflow-analysis"
            )
            self.assertFalse(
                ORACLE._foundation_route_binding_declared(
                    mutated,
                    [records_by_id[selector_id]],
                )
            )

    def test_r0_11_import_dag_is_capcov_to_oracle_to_validation(self) -> None:
        capcov_imports = _module_imports(CAPABILITY_COVERAGE_PATH)
        oracle_imports = _module_imports(ORACLE_PATH)
        validation_imports = _module_imports(VALIDATION_PATH)
        self.assertIn("deterministic_route_oracle", capcov_imports)
        self.assertIn("validation_utils", oracle_imports)
        self.assertTrue(
            {
                "deterministic_route_oracle",
                "capability_coverage",
            }.isdisjoint(validation_imports)
        )
        self.assertNotIn("capability_coverage", oracle_imports)

    def test_r0_12_factory_is_jit_side_effect_free_and_max_three(self) -> None:
        *_, authority_type, factory = self._authority_api("R0-12")
        eager_instances = [
            f"{module.__name__}.{name}"
            for module in (ORACLE, CAPABILITY_COVERAGE)
            for name, value in vars(module).items()
            if isinstance(value, authority_type)
        ]
        self.assertEqual([], eager_instances)
        forbidden_calls = {
            "route": mock.Mock(side_effect=AssertionError("route called")),
            "route_with_trace": mock.Mock(
                side_effect=AssertionError("route_with_trace called")
            ),
        }
        with (
            mock.patch.object(Path, "read_text") as read_text,
            mock.patch.object(Path, "read_bytes") as read_bytes,
            mock.patch.object(
                ORACLE,
                "route",
                forbidden_calls["route"],
            ),
            mock.patch.object(
                ORACLE,
                "route_with_trace",
                forbidden_calls["route_with_trace"],
            ),
        ):
            authority = factory(
                foundation_registry=copy.deepcopy(self.foundation),
                professional_registry=copy.deepcopy(self.professional),
            )
        read_text.assert_not_called()
        read_bytes.assert_not_called()
        forbidden_calls["route"].assert_not_called()
        forbidden_calls["route_with_trace"].assert_not_called()
        self.assertTrue(
            all(
                1 <= len(record.foundations) <= 3
                for record in authority.foundation_selectors
            )
        )
        factory_node = _function_node(
            ORACLE_PATH,
            "oracle_admission_authority",
        )
        forbidden_literals = {
            literal
            for literal in _literal_strings(factory_node)
            if any(
                token in literal.casefold()
                for token in (
                    "skill.md",
                    "references/",
                    "render",
                    "report",
                    "build",
                    "dispatch",
                )
            )
        }
        self.assertEqual(set(), forbidden_literals)

    def test_r0_13a_current_fixture_is_423_unique_control(self) -> None:
        rows = self.admission["cases"]
        ids = [row["id"] for row in rows]
        combinations = [
            (row["layer"], row["skill"], row["case_kind"])
            for row in rows
        ]
        self.assertNotEqual(411, len(rows))
        self.assertEqual(429, len(rows))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(combinations), len(set(combinations)))

    def test_r0_13b_current_fixture_is_authority_subset(self) -> None:
        expected = self._expected_combinations_from_sources()
        combinations = {
            (row["layer"], row["skill"], row["case_kind"])
            for row in self.admission["cases"]
        }
        self.assertEqual(set(), set(combinations) - expected)

    def test_r0_14_fixture_arithmetic_is_0_plus_0_plus_0(self) -> None:
        expected = self._expected_combinations_from_sources()
        fixture = {
            (row["layer"], row["skill"], row["case_kind"])
            for row in self.admission["cases"]
        }
        missing = expected - fixture
        self.assertNotEqual(WAVE1A_FOUNDATION_TRIPLES, missing)
        self.assertEqual(set(), missing)
        special_names = set(SPECIAL_SELECTORS)
        arithmetic = {
            "professional": sum(
                1 for layer, _, _ in missing if layer == "professional"
            ),
            "foundation-ordinary": sum(
                1
                for layer, skill, _ in missing
                if layer == "foundation" and skill not in special_names
            ),
            "foundation-special": sum(
                1
                for layer, skill, _ in missing
                if layer == "foundation" and skill in special_names
            ),
        }
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            arithmetic,
        )
        self.assertEqual(0, sum(arithmetic.values()))

        actual_a = {
            triple
            for triple in fixture
            if triple in PHASE2_A_FOUNDATION_TRIPLES
        }
        self.assertEqual(PHASE2_A_FOUNDATION_TRIPLES, actual_a)
        self.assertEqual(104, len(actual_a))

        expected_sequence = [
            ("foundation", skill, effect)
            for _group, _owner, _review, foundations in PHASE2_A_GROUPS
            for skill in foundations
            for effect in FOUNDATION_EFFECTS
        ]
        actual_sequence = [
            (row["layer"], row["skill"], row["case_kind"])
            for row in self.admission["cases"][
                PHASE2_A_PREDECESSOR_ROW_COUNT:
                PHASE2_A_PREDECESSOR_ROW_COUNT + len(expected_sequence)
            ]
        ]
        self.assertEqual(expected_sequence, actual_sequence)

        expected_wave1a_sequence = [
            ("foundation", skill, effect)
            for skill in WAVE1A_FOUNDATIONS
            for effect in FOUNDATION_EFFECTS
        ]
        actual_wave1a_sequence = [
            (row["layer"], row["skill"], row["case_kind"])
            for row in self.admission["cases"][-len(expected_wave1a_sequence):]
        ]
        self.assertEqual(expected_wave1a_sequence, actual_wave1a_sequence)

        predecessor = self.admission["cases"][
            :PHASE2_A_PREDECESSOR_ROW_COUNT
        ]
        predecessor_bytes = json.dumps(
            predecessor,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            PHASE2_A_PREDECESSOR_ROWS_SHA256,
            hashlib.sha256(predecessor_bytes).hexdigest(),
        )

        row_count = PHASE2_A_PREDECESSOR_ROW_COUNT
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in self.admission["cases"]
        }
        for group_id, owner, review, foundations in PHASE2_A_GROUPS:
            row_count += len(foundations) * len(FOUNDATION_EFFECTS)
            self.assertEqual(
                PHASE2_A_CUMULATIVE_ROW_COUNTS[group_id],
                row_count,
            )
            for skill in foundations:
                selected = rows_by_triple[
                    ("foundation", skill, "selected")
                ]
                self.assertEqual(
                    PHASE2_A_SELECTED_PRIMARY_OVERRIDES.get(skill, owner),
                    selected["expected"]["primary_skill"],
                )
                self.assertTrue(selected["expected"]["selected"])

        self.assertEqual(
            {
                "consumer-impact-analysis",
                "failure-contract-design",
                "idempotency-retry-design",
                "data-migration-design",
                "failure-diagnosis",
            },
            set(PHASE2_A_SELECTED_PRIMARY_OVERRIDES),
        )

    def test_r0_15_phase2_f01_professional_checkpoint_is_exact(
        self,
    ) -> None:
        r0_id = "R0-15-phase2-f01-professional-checkpoint"
        rows = self.admission["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in rows
        }
        missing_f01 = sorted(
            PHASE2_F01_PROFESSIONAL_TRIPLES - set(rows_by_triple)
        )
        if missing_f01:
            self.fail(
                f"[{r0_id}] expected missing_f01=[]; "
                f"actual_missing_count={len(missing_f01)}; "
                f"actual_missing={missing_f01!r}"
            )

        f01_skills = {
            skill
            for _layer, skill, _effect
            in PHASE2_F01_PROFESSIONAL_TRIPLES
        }
        actual_f01 = {
            triple
            for triple in rows_by_triple
            if triple[0] == "professional" and triple[1] in f01_skills
        }
        self.assertEqual(PHASE2_F01_PROFESSIONAL_TRIPLES, actual_f01)
        self.assertEqual(55, len(actual_f01))
        self.assertEqual(429, len(rows))
        self.assertEqual(429, len(rows_by_triple))

        expected = self._expected_combinations_from_sources()
        actual = set(rows_by_triple)
        missing = expected - actual
        special_names = set(SPECIAL_SELECTORS)
        self.assertEqual(set(), actual - expected)
        self.assertNotEqual(WAVE1A_FOUNDATION_TRIPLES, missing)
        self.assertEqual(set(), missing)
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation" and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation" and skill in special_names
                ),
            },
        )

        f01_rows = [
            rows_by_triple[triple]
            for triple in sorted(PHASE2_F01_PROFESSIONAL_TRIPLES)
        ]
        self.assertEqual(55, len({row["id"] for row in f01_rows}))
        self.assertEqual(55, len({row["prompt"] for row in f01_rows}))
        forbidden_prompt_labels = (
            "selected",
            "alternate owner",
            "alternate-owner",
            "direct task",
            "direct-task",
            "multitask",
            "multi-task",
            "true conflict",
            "true-conflict",
        )
        for row in f01_rows:
            with self.subTest(skill=row["skill"], effect=row["case_kind"]):
                normalized_prompt = " ".join(
                    row["prompt"].casefold().split()
                )
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )
                self.assertEqual(row["id"], row["main_execution"]["task_id"])
                self.assertEqual(
                    f"task:{row['id']}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                self.assertIs(
                    (
                        row["case_kind"] == "selected"
                        or (
                            row["skill"] == "engineering-change-analysis"
                            and row["case_kind"] == "multitask"
                        )
                    ),
                    row["expected"]["selected"],
                )

    def test_r0_16_phase2_f02_special_foundation_checkpoint_is_exact(
        self,
    ) -> None:
        r0_id = "R0-16-phase2-f02-special-foundation-checkpoint"
        rows = self.admission["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in rows
        }
        missing_f02 = sorted(
            PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES
            - set(rows_by_triple)
        )
        if missing_f02:
            self.fail(
                f"[{r0_id}] expected missing_f02=[]; "
                f"actual_missing_count={len(missing_f02)}; "
                f"actual_missing={missing_f02!r}"
            )

        special_names = set(SPECIAL_SELECTORS)
        actual_f02 = {
            triple
            for triple in rows_by_triple
            if triple[0] == "foundation"
            and triple[1] in special_names
        }
        self.assertEqual(
            PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES,
            actual_f02,
        )
        self.assertEqual(16, len(actual_f02))
        self.assertEqual(429, len(rows))
        self.assertEqual(429, len(rows_by_triple))

        expected = self._expected_combinations_from_sources()
        actual = set(rows_by_triple)
        missing = expected - actual
        self.assertEqual(set(), actual - expected)
        self.assertNotEqual(WAVE1A_FOUNDATION_TRIPLES, missing)
        self.assertEqual(set(), missing)
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation"
                    and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation"
                    and skill in special_names
                ),
            },
        )

        f02_rows = [
            rows_by_triple[triple]
            for triple in sorted(
                PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES
            )
        ]
        self.assertEqual(16, len({row["id"] for row in f02_rows}))
        self.assertEqual(16, len({row["prompt"] for row in f02_rows}))
        forbidden_prompt_labels = (
            "selected",
            "domain-owned",
            "domain owned",
            "adjacent",
            "simple",
        )
        expected_adjacent_primaries = {
            "architecture-tradeoff-analysis": (
                "architecture-impact-reviewer"
            ),
            "test-data-management": "quality-test-gate",
            "authentication-authorization": "security-privacy-gate",
        }
        for row in f02_rows:
            with self.subTest(skill=row["skill"], effect=row["case_kind"]):
                normalized_prompt = " ".join(
                    row["prompt"].casefold().split()
                )
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )
                self.assertEqual(row["id"], row["main_execution"]["task_id"])
                self.assertEqual(
                    f"task:{row['id']}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                self.assertIs(
                    row["case_kind"] == "selected",
                    row["expected"]["selected"],
                )
                if (
                    row["case_kind"] == "adjacent"
                    and row["skill"] in expected_adjacent_primaries
                ):
                    self.assertEqual(
                        expected_adjacent_primaries[row["skill"]],
                        row["expected"]["primary_skill"],
                    )

    def test_r0_17_phase2_f03_intake_domain_experience_checkpoint_is_exact(
        self,
    ) -> None:
        r0_id = "R0-17-phase2-f03-intake-domain-experience-checkpoint"
        rows = self.admission["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in rows
        }
        missing_f03 = sorted(
            PHASE2_F03_FOUNDATION_TRIPLES - set(rows_by_triple)
        )
        if missing_f03:
            self.fail(
                f"[{r0_id}] expected missing_f03=[]; "
                f"actual_missing_count={len(missing_f03)}; "
                f"actual_missing={missing_f03!r}"
            )

        actual_f03 = {
            triple
            for triple in rows_by_triple
            if triple[0] == "foundation"
            and triple[1] in PHASE2_F03_FOUNDATIONS
        }
        self.assertEqual(PHASE2_F03_FOUNDATION_TRIPLES, actual_f03)
        self.assertEqual(28, len(actual_f03))
        self.assertEqual(429, len(rows))
        self.assertEqual(429, len(rows_by_triple))
        self.assertEqual(
            {
                "professional": 105,
                "foundation": 276,
                "domain": 48,
            },
            {
                layer: sum(
                    1
                    for row in rows
                    if row["layer"] == layer
                )
                for layer in ("professional", "foundation", "domain")
            },
        )

        predecessor = rows[:PHASE2_F03_PREDECESSOR_ROW_COUNT]
        predecessor_bytes = json.dumps(
            predecessor,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            PHASE2_F03_PREDECESSOR_ROWS_SHA256,
            hashlib.sha256(predecessor_bytes).hexdigest(),
        )

        expected = self._expected_combinations_from_sources()
        actual = set(rows_by_triple)
        missing = expected - actual
        self.assertEqual(set(), actual - expected)
        self.assertNotEqual(WAVE1A_FOUNDATION_TRIPLES, missing)
        self.assertEqual(set(), missing)
        special_names = set(SPECIAL_SELECTORS)
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation"
                    and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation"
                    and skill in special_names
                ),
            },
        )

        old_ordinary = {
            triple
            for triple in actual
            if triple[0] == "foundation"
            and triple[1] not in special_names
            and triple[1] not in PHASE2_F03_FOUNDATIONS
            and triple[1] not in PHASE2_F04_FOUNDATIONS
            and triple[1] not in PHASE2_A_FOUNDATIONS
            and triple not in WAVE1A_FOUNDATION_TRIPLES
        }
        actual_wave1a = actual & WAVE1A_FOUNDATION_TRIPLES
        actual_f02 = {
            triple
            for triple in actual
            if triple[0] == "foundation"
            and triple[1] in special_names
        }
        actual_f01 = {
            triple
            for triple in actual
            if triple[0] == "professional"
            and triple in PHASE2_F01_PROFESSIONAL_TRIPLES
        }
        self.assertEqual(72, len(old_ordinary))
        self.assertEqual(WAVE1A_FOUNDATION_TRIPLES, actual_wave1a)
        self.assertEqual(
            PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES,
            actual_f02,
        )
        self.assertEqual(PHASE2_F01_PROFESSIONAL_TRIPLES, actual_f01)

        f03_rows = [
            rows_by_triple[triple]
            for triple in sorted(PHASE2_F03_FOUNDATION_TRIPLES)
        ]
        self.assertEqual(28, len({row["id"] for row in f03_rows}))
        self.assertEqual(28, len({row["prompt"] for row in f03_rows}))
        prefixes_by_effect = {
            effect: set()
            for effect in FOUNDATION_EFFECTS
        }
        forbidden_prompt_labels = (
            "selected",
            "domain-owned",
            "domain owned",
            "adjacent",
            "simple",
        )
        for row in f03_rows:
            with self.subTest(
                skill=row["skill"],
                effect=row["case_kind"],
            ):
                self.assertEqual(
                    (
                        "capcov-admission-foundation-"
                        f"{row['skill']}-{row['case_kind']}"
                    ),
                    row["id"],
                )
                self.assertEqual(
                    row["id"],
                    row["main_execution"]["task_id"],
                )
                self.assertEqual(
                    f"task:{row['id']}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                normalized_prompt = " ".join(
                    row["prompt"].casefold().split()
                )
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )
                self.assertIs(
                    row["case_kind"] == "selected",
                    row["expected"]["selected"],
                )
                prefixes_by_effect[row["case_kind"]].add(
                    " ".join(normalized_prompt.split()[:5])
                )
        self.assertTrue(
            all(
                len(prefixes) == len(PHASE2_F03_FOUNDATIONS)
                for prefixes in prefixes_by_effect.values()
            )
        )

    def test_r0_18_phase2_f04_structure_review_checkpoint_is_exact(
        self,
    ) -> None:
        r0_id = "R0-18-phase2-f04-structure-review-checkpoint"
        rows = self.admission["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in rows
        }
        missing_f04 = sorted(
            PHASE2_F04_FOUNDATION_TRIPLES - set(rows_by_triple)
        )
        if missing_f04:
            self.fail(
                f"[{r0_id}] expected missing_f04=[]; "
                f"actual_missing_count={len(missing_f04)}; "
                f"actual_missing={missing_f04!r}"
            )

        actual = set(rows_by_triple)
        actual_f04 = {
            triple
            for triple in actual
            if triple[0] == "foundation"
            and triple[1] in PHASE2_F04_FOUNDATIONS
        }
        self.assertEqual(PHASE2_F04_FOUNDATION_TRIPLES, actual_f04)
        self.assertEqual(44, len(actual_f04))
        self.assertEqual(429, len(rows))
        self.assertEqual(429, len(rows_by_triple))
        self.assertEqual(
            {
                "professional": 105,
                "foundation": 276,
                "domain": 48,
            },
            {
                layer: sum(
                    1
                    for row in rows
                    if row["layer"] == layer
                )
                for layer in ("professional", "foundation", "domain")
            },
        )

        predecessor = rows[:PHASE2_F04_PREDECESSOR_ROW_COUNT]
        predecessor_bytes = json.dumps(
            predecessor,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            PHASE2_F04_PREDECESSOR_ROWS_SHA256,
            hashlib.sha256(predecessor_bytes).hexdigest(),
        )

        expected = self._expected_combinations_from_sources()
        missing = expected - actual
        self.assertEqual(set(), actual - expected)
        self.assertNotEqual(WAVE1A_FOUNDATION_TRIPLES, missing)
        self.assertEqual(set(), missing)
        special_names = set(SPECIAL_SELECTORS)
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation"
                    and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing
                    if layer == "foundation"
                    and skill in special_names
                ),
            },
        )

        cohorts = {
            "professional": sum(
                1 for triple in actual if triple[0] == "professional"
            ),
            "special": sum(
                1
                for triple in actual
                if triple[0] == "foundation"
                and triple[1] in special_names
            ),
            "pre-f03-ordinary": sum(
                1
                for triple in actual
                if triple[0] == "foundation"
                and triple[1] not in special_names
                and triple[1] not in PHASE2_F03_FOUNDATIONS
                and triple[1] not in PHASE2_F04_FOUNDATIONS
                and triple[1] not in PHASE2_A_FOUNDATIONS
                and triple not in WAVE1A_FOUNDATION_TRIPLES
            ),
            "f03": len(
                {
                    triple
                    for triple in actual
                    if triple in PHASE2_F03_FOUNDATION_TRIPLES
                }
            ),
            "f04": len(actual_f04),
            "wave1a": len(actual & WAVE1A_FOUNDATION_TRIPLES),
            "domain": sum(
                1 for triple in actual if triple[0] == "domain"
            ),
        }
        self.assertEqual(
            {
                "professional": 105,
                "special": 16,
                "pre-f03-ordinary": 72,
                "f03": 28,
                "f04": 44,
                "wave1a": 12,
                "domain": 48,
            },
            cohorts,
        )

        f04_rows = [
            rows_by_triple[triple]
            for triple in sorted(PHASE2_F04_FOUNDATION_TRIPLES)
        ]
        self.assertEqual(44, len({row["id"] for row in f04_rows}))
        self.assertEqual(44, len({row["prompt"] for row in f04_rows}))
        forbidden_prompt_labels = (
            "selected",
            "domain-owned",
            "domain owned",
            "adjacent",
            "simple",
        )
        for row in f04_rows:
            with self.subTest(
                skill=row["skill"],
                effect=row["case_kind"],
            ):
                self.assertEqual(
                    (
                        "capcov-admission-foundation-"
                        f"{row['skill']}-{row['case_kind']}"
                    ),
                    row["id"],
                )
                self.assertEqual(
                    row["id"],
                    row["main_execution"]["task_id"],
                )
                self.assertEqual(
                    f"task:{row['id']}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                self.assertIs(
                    row["case_kind"] == "selected",
                    row["expected"]["selected"],
                )
                normalized_prompt = " ".join(
                    row["prompt"].casefold().split()
                )
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )

        self.assertEqual(
            PHASE2_F04_FOUNDATIONS,
            frozenset(PHASE2_F04_ADJACENT_FOUNDATIONS),
        )

    def test_r0_mutation_duplicate_selector_and_foundation_ids_fail(
        self,
    ) -> None:
        (
            _,
            _,
            record_type,
            authority_type,
            _,
        ) = self._authority_api("R0-M01")
        authority = self._authority("R0-M01")
        first = authority.foundation_selectors[0]
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            authority_type(
                contract=authority.contract,
                foundation_selectors=(
                    *authority.foundation_selectors,
                    first,
                ),
                primary_task_skills=authority.primary_task_skills,
                review_task_skills=authority.review_task_skills,
            )
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            record_type(
                selector_id=first.selector_id,
                foundations=(
                    first.foundations[0],
                    first.foundations[0],
                ),
                source=first.source,
                evidence_ids=first.evidence_ids,
                owner_bindings=first.owner_bindings,
            )
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            record_type(
                selector_id=first.selector_id,
                foundations=(),
                source=first.source,
                evidence_ids=first.evidence_ids,
                owner_bindings=first.owner_bindings,
            )

    def test_r0_mutation_unknown_non_product_and_reciprocity_fail(
        self,
    ) -> None:
        authority = self._authority("R0-M02")
        *_, factory = self._authority_api("R0-M02")
        target = authority.foundation_selectors[0].foundations[0]

        unknown = copy.deepcopy(self.foundation)
        unknown["foundation_skills"] = [
            row
            for row in unknown["foundation_skills"]
            if row["name"] != target
        ]
        with self.assertRaises(
            (ORACLE.RoutingIntegrityError, VALIDATION.ValidationProblem)
        ):
            factory(
                foundation_registry=unknown,
                professional_registry=copy.deepcopy(self.professional),
            )

        non_product = copy.deepcopy(self.foundation)
        next(
            row
            for row in non_product["foundation_skills"]
            if row["name"] == target
        )["delivery_scope"] = "authoring"
        with self.assertRaises(
            (ORACLE.RoutingIntegrityError, VALIDATION.ValidationProblem)
        ):
            factory(
                foundation_registry=non_product,
                professional_registry=copy.deepcopy(self.professional),
            )

        binding = authority.foundation_selectors[0].owner_bindings[0]
        reciprocal = copy.deepcopy(self.professional)
        owner = next(
            row
            for row in reciprocal["professional_skills"]
            if row["name"] == binding.primary_skill
        )
        owner["layer3_candidates"] = [
            name
            for name in owner.get("layer3_candidates", [])
            if name != target
        ]
        with self.assertRaises(
            (ORACLE.RoutingIntegrityError, VALIDATION.ValidationProblem)
        ):
            factory(
                foundation_registry=copy.deepcopy(self.foundation),
                professional_registry=reciprocal,
            )

    def test_r0_mutation_bad_source_binding_evidence_and_order_fail(
        self,
    ) -> None:
        (
            source_type,
            binding_type,
            record_type,
            authority_type,
            _,
        ) = self._authority_api("R0-M03")
        authority = self._authority("R0-M03")
        first = authority.foundation_selectors[0]
        mutations: tuple[
            tuple[str, Callable[[], object]],
            ...,
        ] = (
            (
                "raw-source-bypass",
                lambda: record_type(
                    selector_id=first.selector_id,
                    foundations=first.foundations,
                    source=source_type(
                        kind="raw-bypass",
                        symbol=first.source.symbol,
                        source_id=first.source.source_id,
                    ),
                    evidence_ids=first.evidence_ids,
                    owner_bindings=first.owner_bindings,
                ),
            ),
            (
                "helper-source-bypass",
                lambda: record_type(
                    selector_id=first.selector_id,
                    foundations=first.foundations,
                    source=source_type(
                        kind="dynamic-helper-only",
                        symbol="missing_foundation_selector_helper",
                        source_id=first.source.source_id,
                    ),
                    evidence_ids=first.evidence_ids,
                    owner_bindings=first.owner_bindings,
                ),
            ),
            (
                "lost-selector-id",
                lambda: record_type(
                    selector_id="",
                    foundations=first.foundations,
                    source=first.source,
                    evidence_ids=first.evidence_ids,
                    owner_bindings=first.owner_bindings,
                ),
            ),
            (
                "lost-evidence",
                lambda: record_type(
                    selector_id=first.selector_id,
                    foundations=first.foundations,
                    source=first.source,
                    evidence_ids=(),
                    owner_bindings=first.owner_bindings,
                ),
            ),
            (
                "duplicate-evidence",
                lambda: record_type(
                    selector_id=first.selector_id,
                    foundations=first.foundations,
                    source=first.source,
                    evidence_ids=(
                        first.evidence_ids[0],
                        first.evidence_ids[0],
                    ),
                    owner_bindings=first.owner_bindings,
                ),
            ),
            (
                "undeclared-final-owner",
                lambda: record_type(
                    selector_id=first.selector_id,
                    foundations=first.foundations,
                    source=first.source,
                    evidence_ids=first.evidence_ids,
                    owner_bindings=(
                        binding_type(
                            primary_skill="undeclared-final-owner",
                            review_skill="ai-code-review-refactor",
                        ),
                    ),
                ),
            ),
        )
        for label, mutation in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ORACLE.RoutingIntegrityError):
                    mutation()
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            authority_type(
                contract=authority.contract,
                foundation_selectors=tuple(
                    reversed(authority.foundation_selectors)
                ),
                primary_task_skills=authority.primary_task_skills,
                review_task_skills=authority.review_task_skills,
            )
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            authority_type(
                contract=authority.contract,
                foundation_selectors=authority.foundation_selectors[:-1],
                primary_task_skills=authority.primary_task_skills,
                review_task_skills=authority.review_task_skills,
            )

    def test_r0_mutation_matcher_omission_injection_and_deferred_fail(
        self,
    ) -> None:
        *_, factory = self._authority_api("R0-M04")
        canonical = copy.deepcopy(self.foundation)
        runtime_rows = [
            row
            for row in canonical["foundation_skills"]
            if isinstance(row.get("activation"), dict)
            and "runtime_matcher" in row["activation"]
        ]
        omitted = copy.deepcopy(canonical)
        omitted_target = runtime_rows[0]["name"]
        next(
            row
            for row in omitted["foundation_skills"]
            if row["name"] == omitted_target
        )["activation"].pop("runtime_matcher")
        with self.assertRaises(
            (ORACLE.RoutingIntegrityError, VALIDATION.ValidationProblem)
        ):
            factory(
                foundation_registry=omitted,
                professional_registry=copy.deepcopy(self.professional),
            )

        for target in (
            "architecture-enforcement-tooling",
            "repository-impact-inspection",
        ):
            injected = copy.deepcopy(canonical)
            target_row = next(
                row
                for row in injected["foundation_skills"]
                if row["name"] == target
            )
            target_row["activation"]["runtime_matcher"] = copy.deepcopy(
                runtime_rows[0]["activation"]["runtime_matcher"]
            )
            with self.subTest(target=target), self.assertRaises(
                (ORACLE.RoutingIntegrityError, VALIDATION.ValidationProblem)
            ):
                factory(
                    foundation_registry=injected,
                    professional_registry=copy.deepcopy(self.professional),
                )

    def test_r0_mutation_high_risk_primary_and_capcov_broadening_fail(
        self,
    ) -> None:
        *_, authority_type, _ = self._authority_api("R0-M05")
        authority = self._authority("R0-M05")
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            authority_type(
                contract=authority.contract,
                foundation_selectors=authority.foundation_selectors,
                primary_task_skills=tuple(
                    sorted(
                        {
                            *authority.primary_task_skills,
                            "high-risk-design-review",
                        }
                    )
                ),
                review_task_skills=authority.review_task_skills,
            )
        contract = CAPABILITY_COVERAGE._admission_case_contract(
            copy.deepcopy(self.professional),
            copy.deepcopy(self.foundation),
            copy.deepcopy(self.domain),
        )
        combinations = CAPABILITY_COVERAGE._admission_combinations(contract)
        self.assertEqual(
            self._expected_combinations_from_sources(),
            set(combinations),
        )

    def test_wave1a_foundation_consumers_are_complete_red(self) -> None:
        expected_used_by = {
            "technology-stack-selection": {
                "architecture-impact-reviewer",
                "high-risk-design-review",
            },
            "module-boundary-design": {
                "architecture-impact-reviewer",
                "high-risk-design-review",
            },
            "configuration-runtime-policy": {
                "ai-code-review-refactor",
                "backend-change-builder",
                "data-middleware-change-builder",
                "delivery-release-gate",
                "engineering-change-analysis",
                "frontend-change-builder",
                "installed-client-change-builder",
                "integration-change-builder",
                "platform-infrastructure-change-builder",
                "repository-tooling-change-builder",
            },
            "dependency-vulnerability-scanning": {
                "backend-change-builder",
                "data-middleware-change-builder",
                "engineering-change-analysis",
                "frontend-change-builder",
                "installed-client-change-builder",
                "integration-change-builder",
                "platform-infrastructure-change-builder",
                "repository-tooling-change-builder",
                "security-privacy-gate",
            },
        }
        mismatches: list[str] = []
        for foundation, expected in expected_used_by.items():
            actual = set(self.foundation_rows[foundation]["used_by"])
            if actual != expected:
                mismatches.append(
                    f"{foundation}: missing={sorted(expected - actual)!r}; "
                    f"unexpected={sorted(actual - expected)!r}"
                )
        self.assertEqual(
            [],
            mismatches,
            "Wave1A consumer authority is incomplete",
        )

    def test_wave1a_dev_only_sandbox_boundary_stays_closed(self) -> None:
        row = self.foundation_rows["agent-tool-permission-sandbox"]
        self.assertEqual([], row["used_by"])
        self.assertEqual("dev-only", row["delivery_scope"])
        inventory = _source_selector_inventory(self.foundation)
        routed_foundations = {
            foundation
            for foundations in inventory.values()
            for foundation in foundations
        }
        self.assertNotIn("agent-tool-permission-sandbox", routed_foundations)
        self.assertTrue(
            all(
                "agent-tool-permission-sandbox"
                not in professional["layer3_candidates"]
                for professional in self.professional_rows.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
