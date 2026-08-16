from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import re
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from capability_coverage import (
    _validate_evidence_projection,
    evaluate_admission_evidence,
    validate_capability_coverage,
)
import capability_coverage as CAPABILITY_COVERAGE
import deterministic_route_oracle as ROUTE_ORACLE
import validation_utils as VALIDATION_CONTRACTS
from validation_utils import ValidationProblem, load_yaml_file


ROUTING_SPEC = importlib.util.spec_from_file_location(
    "capcov_eval_routing",
    ROOT / "scripts" / "eval-routing.py",
)
assert ROUTING_SPEC is not None and ROUTING_SPEC.loader is not None
ROUTING = importlib.util.module_from_spec(ROUTING_SPEC)
sys.modules[ROUTING_SPEC.name] = ROUTING
ROUTING_SPEC.loader.exec_module(ROUTING)

BEHAVIOR_SPEC = importlib.util.spec_from_file_location(
    "capcov_eval_agent_behavior",
    ROOT / "scripts" / "eval-agent-behavior.py",
)
assert BEHAVIOR_SPEC is not None and BEHAVIOR_SPEC.loader is not None
BEHAVIOR = importlib.util.module_from_spec(BEHAVIOR_SPEC)
sys.modules[BEHAVIOR_SPEC.name] = BEHAVIOR
BEHAVIOR_SPEC.loader.exec_module(BEHAVIOR)


CAPABILITY_ROUTE_CASES = (
    ROOT / "evals" / "routing" / "capability-coverage-cases.yaml"
)
R0_ADMISSION_INVENTORY_PREIMAGE_SHA256 = (
    "5394d982c2b8086a5f7a4b83024e3fcd8846ed4b174c223fac1d684f0a54723f"
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
        for effect in (
            "selected",
            "domain-owned",
            "adjacent",
            "simple",
        )
    }
)
PHASE2_F03_PREDECESSOR_ROW_COUNT = 241
PHASE2_F03_PREDECESSOR_ROWS_SHA256 = (
    "cd965934eb9373f2d36a11e99bc7c251a1345ca25bea66c8c96567d2c8854473"
)
PHASE2_F03_SELECTED_CANDIDATE_IDS = {
    "acceptance-standard-definition": "acceptance-definition",
    "requirement-clarification": "ambiguous-intake",
    "business-rule-extraction": (
        "foundation-activation-business-rule-extraction"
    ),
    "state-machine-modeling": (
        "foundation-activation-state-machine-modeling"
    ),
    "design-system-rules": "experience-design-system-analysis",
    "interaction-state-modeling": "experience-interaction-analysis",
    "task-dag-decomposition": "accepted-brief-task-dag",
}
PHASE2_F03_SELECTED_TRIGGER_PHRASES = {
    "acceptance-standard-definition": ("observable acceptance",),
    "requirement-clarification": ("ambiguous",),
    "business-rule-extraction": (
        "business policies",
        "domain invariants",
    ),
    "state-machine-modeling": (
        "domain lifecycle states",
        "allowed transitions",
    ),
    "design-system-rules": (
        "user flow",
        "design tokens",
        "components",
        "spacing",
        "typography",
    ),
    "interaction-state-modeling": (
        "user flow",
        "loading",
        "error",
        "interaction states",
        "state transitions",
    ),
    "task-dag-decomposition": (
        "accepted engineering brief",
        "explicit task dag",
    ),
}
PHASE2_F03_ADJACENT_FOUNDATIONS = {
    "acceptance-standard-definition": ["requirement-clarification"],
    "requirement-clarification": ["acceptance-standard-definition"],
    "business-rule-extraction": ["state-machine-modeling"],
    "state-machine-modeling": ["business-rule-extraction"],
    "design-system-rules": ["interaction-state-modeling"],
    "interaction-state-modeling": ["design-system-rules"],
    "task-dag-decomposition": ["repository-context-map"],
}
PHASE2_F03_EXPECTED_PRIMARIES = {
    ("acceptance-standard-definition", "selected"): (
        "acceptance-criteria-builder"
    ),
    ("acceptance-standard-definition", "domain-owned"): (
        "installed-client-change-builder"
    ),
    ("acceptance-standard-definition", "adjacent"): (
        "change-intake-compiler"
    ),
    ("acceptance-standard-definition", "simple"): (
        "backend-change-builder"
    ),
    ("requirement-clarification", "selected"): "change-intake-compiler",
    ("requirement-clarification", "domain-owned"): (
        "installed-client-change-builder"
    ),
    ("requirement-clarification", "adjacent"): (
        "acceptance-criteria-builder"
    ),
    ("requirement-clarification", "simple"): "backend-change-builder",
    ("business-rule-extraction", "selected"): "domain-impact-modeler",
    ("business-rule-extraction", "domain-owned"): (
        "installed-client-change-builder"
    ),
    ("business-rule-extraction", "adjacent"): "domain-impact-modeler",
    ("business-rule-extraction", "simple"): "backend-change-builder",
    ("state-machine-modeling", "selected"): "domain-impact-modeler",
    ("state-machine-modeling", "domain-owned"): (
        "installed-client-change-builder"
    ),
    ("state-machine-modeling", "adjacent"): "domain-impact-modeler",
    ("state-machine-modeling", "simple"): "backend-change-builder",
    ("design-system-rules", "selected"): "experience-impact-modeler",
    ("design-system-rules", "domain-owned"): (
        "installed-client-change-builder"
    ),
    ("design-system-rules", "adjacent"): "experience-impact-modeler",
    ("design-system-rules", "simple"): "backend-change-builder",
    ("interaction-state-modeling", "selected"): (
        "experience-impact-modeler"
    ),
    ("interaction-state-modeling", "domain-owned"): (
        "platform-infrastructure-change-builder"
    ),
    ("interaction-state-modeling", "adjacent"): (
        "experience-impact-modeler"
    ),
    ("interaction-state-modeling", "simple"): "backend-change-builder",
    ("task-dag-decomposition", "selected"): "task-dag-planner",
    ("task-dag-decomposition", "domain-owned"): (
        "installed-client-change-builder"
    ),
    ("task-dag-decomposition", "adjacent"): (
        "engineering-change-analysis"
    ),
    ("task-dag-decomposition", "simple"): "backend-change-builder",
}
PHASE2_F03_TRIGGER_REMOVAL_PROMPTS = {
    "acceptance-standard-definition": (
        "Analyze a requested behavior whose success conditions are already "
        "approved."
    ),
    "requirement-clarification": (
        "Analyze a fully specified change with no open questions."
    ),
    "business-rule-extraction": (
        "Analyze an invoice data shape while policy and invariant "
        "definitions remain fixed."
    ),
    "state-machine-modeling": (
        "Analyze a domain record while lifecycle states and transitions "
        "remain unchanged."
    ),
    "design-system-rules": (
        "Analyze a user flow report that merely lists design tokens and "
        "components; no design-system decision is requested and no token "
        "or component behavior changes."
    ),
    "interaction-state-modeling": (
        "Analyze a user flow glossary report that merely mentions "
        "interaction states; do not decide or change any state or "
        "transition behavior."
    ),
    "task-dag-decomposition": (
        "Analyze several dependent work items before any Engineering Brief "
        "exists."
    ),
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
        for effect in (
            "selected",
            "domain-owned",
            "adjacent",
            "simple",
        )
    }
)
PHASE2_F04_PREDECESSOR_ROW_COUNT = 269
PHASE2_F04_PREDECESSOR_ROWS_SHA256 = (
    "fc87d0b7fde7632aa6e4cead664a538c21a7f057b2cff3d43c6e5a9cc68dac43"
)
PHASE2_F04_SELECTED_ROUTES = {
    "code-clarity-maintainability": (
        "ai-code-review-refactor",
        ["code-clarity-maintainability"],
        "review-generic",
    ),
    "code-review": (
        "ai-code-review-refactor",
        ["code-review"],
        "review-generic",
    ),
    "concurrency-control": (
        "engineering-change-analysis",
        [
            "concurrency-control",
            "degradation-circuit-breaking",
            "observability",
        ],
        "cache-stampede-reliability-controls",
    ),
    "design-pattern-selection": (
        "architecture-impact-reviewer",
        ["design-pattern-selection"],
        "design-pattern-analysis",
    ),
    "domain-object-identification": (
        "domain-impact-modeler",
        ["domain-object-identification"],
        "domain-object-analysis",
    ),
    "implementation-structure-design": (
        "architecture-impact-reviewer",
        ["implementation-structure-design"],
        "owner-internal-structure-analysis",
    ),
    "minimal-correct-implementation": (
        "engineering-change-analysis",
        ["minimal-correct-implementation"],
        "minimality-analysis",
    ),
    "module-boundary-design": (
        "architecture-impact-reviewer",
        ["module-boundary-design"],
        "module-boundary-analysis",
    ),
    "refactoring": (
        "engineering-change-analysis",
        ["refactoring"],
        "refactor-fixed-destination",
    ),
    "repository-context-map": (
        "engineering-change-analysis",
        ["repository-context-map"],
        "critical-unknown",
    ),
    "package-dependency-management": (
        "engineering-change-analysis",
        ["package-dependency-management"],
        "package-dependency-analysis",
    ),
}
PHASE2_F04_DOMAIN_PRIMARIES = {
    "code-clarity-maintainability": "installed-client-change-builder",
    "code-review": "installed-client-change-builder",
    "concurrency-control": "installed-client-change-builder",
    "design-pattern-selection": "installed-client-change-builder",
    "domain-object-identification": "installed-client-change-builder",
    "implementation-structure-design": (
        "platform-infrastructure-change-builder"
    ),
    "minimal-correct-implementation": "installed-client-change-builder",
    "module-boundary-design": "installed-client-change-builder",
    "refactoring": "installed-client-change-builder",
    "repository-context-map": "installed-client-change-builder",
    "package-dependency-management": "installed-client-change-builder",
}
PHASE2_F04_ADJACENT_ROUTES = {
    "code-clarity-maintainability": (
        "ai-code-review-refactor",
        ["code-review"],
    ),
    "code-review": (
        "ai-code-review-refactor",
        ["code-clarity-maintainability"],
    ),
    "concurrency-control": (
        "architecture-impact-reviewer",
        ["design-pattern-selection"],
    ),
    "design-pattern-selection": (
        "engineering-change-analysis",
        [
            "concurrency-control",
            "degradation-circuit-breaking",
            "observability",
        ],
    ),
    "domain-object-identification": (
        "domain-impact-modeler",
        ["business-rule-extraction", "state-machine-modeling"],
    ),
    "implementation-structure-design": (
        "architecture-impact-reviewer",
        ["module-boundary-design"],
    ),
    "minimal-correct-implementation": (
        "engineering-change-analysis",
        ["refactoring"],
    ),
    "module-boundary-design": (
        "architecture-impact-reviewer",
        ["implementation-structure-design"],
    ),
    "refactoring": (
        "engineering-change-analysis",
        ["minimal-correct-implementation"],
    ),
    "repository-context-map": (
        "engineering-change-analysis",
        ["package-dependency-management"],
    ),
    "package-dependency-management": (
        "engineering-change-analysis",
        ["repository-context-map"],
    ),
}
PHASE2_F04_TRIGGER_REMOVAL_PROMPTS = {
    "code-clarity-maintainability": (
        "Review the actual diff for correctness; no readability or naming "
        "change is in scope."
    ),
    "code-review": (
        "Implement the accepted backend invoice footer calculation change "
        "after review scope was fixed."
    ),
    "concurrency-control": (
        "Analyze a cache efficiency issue for duplicate reads after request "
        "coordination is fixed."
    ),
    "design-pattern-selection": (
        "Analyze backend provider code after substitution, lifecycle, and "
        "extension choices were fixed; no pattern decision remains."
    ),
    "domain-object-identification": (
        "With an accepted Engineering Brief, analyze only DTO, relational "
        "table, and UI label mapping; domain identity, lifecycle, aggregate, "
        "invariant, and writer authority remain unchanged."
    ),
    "implementation-structure-design": (
        "Analyze the accepted PaymentsService helper change after "
        "owner-private reuse and deliberate separation were fixed."
    ),
    "minimal-correct-implementation": (
        "Analyze the accepted response wrapper after its necessity and "
        "implementation were fixed."
    ),
    "module-boundary-design": (
        "Analyze work inside PaymentsService; module ownership, exports, and "
        "dependency edges remain unchanged."
    ),
    "refactoring": (
        "Analyze a proposed code move before its destination owner and final "
        "placement are decided."
    ),
    "repository-context-map": (
        "Implement an accepted repository-owned generator source change; "
        "the template, generator, derived artifact, committed policy, and "
        "freshness check are known."
    ),
    "package-dependency-management": (
        "Analyze use of an existing standard-library capability; no package "
        "installation or supply-chain decision is requested."
    ),
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
PHASE2_A_CASES = {
    ('consumer-impact-analysis', 'selected'): ('A01', 'Analyze an external integration downstream consumer compatibility change; retryable versus terminal outcomes and timeout cancellation meaning remain unchanged.', 'engineering-change-analysis', 'ai-code-review-refactor', ('consumer-impact-analysis',), 'external-integration-consumer-impact-analysis', ('external-integration-analysis',)),
    ('consumer-impact-analysis', 'domain-owned'): ('A01', 'Implement the accepted Android app foreground service and background work scheduling behavior for the catalog client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('consumer-impact-analysis', 'adjacent'): ('A01', 'With an accepted Engineering Brief, analyze only the provider integration handoff artifact.', 'integration-change-builder', 'ai-code-review-refactor', ('contract-testing',), 'integration-handoff-artifact', ()),
    ('consumer-impact-analysis', 'simple'): ('A01', 'Implement an accepted backend invoice label capitalization change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('failure-contract-design', 'selected'): ('A01', 'Analyze an external integration retryable versus terminal outcome and timeout cancellation meaning change; downstream consumer compatibility remains unchanged.', 'engineering-change-analysis', 'ai-code-review-refactor', ('failure-contract-design',), 'external-integration-failure-contract-analysis', ('external-integration-analysis',)),
    ('failure-contract-design', 'domain-owned'): ('A01', 'Implement the accepted iOS scene and background task expiration behavior for the calendar client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('failure-contract-design', 'adjacent'): ('A01', 'With an accepted Engineering Brief, analyze only the consumer integration handoff artifact.', 'integration-change-builder', 'ai-code-review-refactor', ('contract-testing',), 'integration-handoff-artifact', ()),
    ('failure-contract-design', 'simple'): ('A01', 'Implement an accepted backend receipt line ordering change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('degradation-circuit-breaking', 'selected'): ('A02', 'Review a reliability-only failure with no abuse or privacy risk, including outage degradation and recovery behavior.', 'reliability-observability-gate', 'reliability-observability-gate', ('degradation-circuit-breaking', 'observability', 'backup-recovery'), 'review-reliability-risk', ('security-anti-reliability-only',)),
    ('degradation-circuit-breaking', 'domain-owned'): ('A02', 'Implement the accepted macOS AppKit app window state behavior for the photo client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('macos-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('degradation-circuit-breaking', 'adjacent'): ('A02', 'Implement structured redacted logs for a field-only change with no reliability decision.', 'logging-design-gate', 'logging-design-gate', ('logging-error-handling',), 'implementation-owner:logging-design-gate', ()),
    ('degradation-circuit-breaking', 'simple'): ('A02', 'Implement an accepted backend health response wording change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('web-security', 'selected'): ('A03', 'Analyze an SSRF URL fetch threat for an authenticated service account, with no authorization handoff or policy change.', 'security-privacy-gate', 'security-privacy-gate', ('threat-modeling', 'web-security'), 'ssrf-threat-professional-precedence', ('ssrf-url-fetch-analysis',)),
    ('web-security', 'domain-owned'): ('A03', 'Implement an accepted Windows packaged desktop application protocol-handler change for the media client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('windows-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('web-security', 'adjacent'): ('A03', 'Analyze a credential or session lifecycle behavior change that affects token issuance, transport, storage, renewal, privilege change, rotation, revocation, logout, recovery, authorization, disclosure, or replay handling for a workforce login.', 'security-privacy-gate', 'security-privacy-gate', ('authentication-security',), 'security-credential-session-lifecycle', ()),
    ('web-security', 'simple'): ('A03', 'Implement an accepted backend decimal formatting change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('contract-testing', 'selected'): ('A04', 'With an accepted Engineering Brief, analyze only the integration handoff artifact.', 'integration-change-builder', 'ai-code-review-refactor', ('contract-testing',), 'integration-handoff-artifact', ('integration-handoff-artifact',)),
    ('contract-testing', 'domain-owned'): ('A04', 'Implement the accepted Android app foreground service and background work scheduling behavior for the travel client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('contract-testing', 'adjacent'): ('A04', 'Implement backend retry idempotency for duplicated invoice jobs.', 'engineering-change-analysis', 'ai-code-review-refactor', ('idempotency-retry-design',), 'backend-idempotency-analysis', ()),
    ('contract-testing', 'simple'): ('A04', 'Implement an accepted backend notification punctuation change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('idempotency-retry-design', 'selected'): ('A04', 'Implement backend retry idempotency for duplicate job delivery.', 'engineering-change-analysis', 'ai-code-review-refactor', ('idempotency-retry-design',), 'backend-idempotency-analysis', ('backend-idempotency-analysis',)),
    ('idempotency-retry-design', 'domain-owned'): ('A04', 'Implement the accepted iOS scene and background task expiration behavior for the notes client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('idempotency-retry-design', 'adjacent'): ('A04', 'With an accepted Engineering Brief, analyze only the deployment integration handoff artifact.', 'integration-change-builder', 'ai-code-review-refactor', ('contract-testing',), 'integration-handoff-artifact', ()),
    ('idempotency-retry-design', 'simple'): ('A04', 'Implement an accepted backend report title change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('observability', 'selected'): ('A05', 'Review outage degradation SLO metrics and recovery behavior.', 'reliability-observability-gate', 'reliability-observability-gate', ('degradation-circuit-breaking', 'observability', 'backup-recovery'), 'review-reliability-risk', ('security-anti-reliability-only',)),
    ('observability', 'domain-owned'): ('A05', 'Implement the accepted macOS AppKit app window state behavior for the drawing client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('macos-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('observability', 'adjacent'): ('A05', 'Implement structured redacted logs for an audit correlation field with no SLO or recovery decision.', 'logging-design-gate', 'logging-design-gate', ('logging-error-handling',), 'implementation-owner:logging-design-gate', ()),
    ('observability', 'simple'): ('A05', 'Implement an accepted backend unit conversion calculation change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('backup-recovery', 'selected'): ('A05', 'Review the actual diff for an SLO recovery change with material outage recovery risk.', 'reliability-observability-gate', 'reliability-observability-gate', ('degradation-circuit-breaking', 'observability', 'backup-recovery'), 'review-reliability-risk', ('dynamic-foundation:backup-recovery',)),
    ('backup-recovery', 'domain-owned'): ('A05', 'Implement an accepted Windows packaged desktop application protocol-handler change for the planning client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('windows-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('backup-recovery', 'adjacent'): ('A05', 'Review a production rollout with compatibility stop signals while state restore behavior remains unchanged.', 'delivery-release-gate', 'delivery-release-gate', ('release-rollback', 'version-compatibility'), 'review-release-risk', ()),
    ('backup-recovery', 'simple'): ('A05', 'Implement an accepted backend invoice footer change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('permission-boundary-modeling', 'selected'): ('A06', 'Analyze tenant authorization and object permission security.', 'security-privacy-gate', 'security-privacy-gate', ('permission-boundary-modeling', 'threat-modeling'), 'generic-security-risk', ('tenant-isolation-security',)),
    ('permission-boundary-modeling', 'domain-owned'): ('A06', 'Implement the accepted Android app foreground service and background work scheduling behavior for the weather client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('permission-boundary-modeling', 'adjacent'): ('A06', 'Analyze a credential or session lifecycle behavior change that affects token issuance, transport, storage, renewal, privilege change, rotation, revocation, logout, recovery, authorization, disclosure, or replay handling for a support login.', 'security-privacy-gate', 'security-privacy-gate', ('authentication-security',), 'security-credential-session-lifecycle', ()),
    ('permission-boundary-modeling', 'simple'): ('A06', 'Implement an accepted backend locale display-name change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('threat-modeling', 'selected'): ('A06', 'Analyze tenant authorization security boundaries.', 'security-privacy-gate', 'security-privacy-gate', ('permission-boundary-modeling', 'threat-modeling'), 'generic-security-risk', ('ssrf-url-fetch-analysis',)),
    ('threat-modeling', 'domain-owned'): ('A06', 'Implement the accepted iOS scene and background task expiration behavior for the reading client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('threat-modeling', 'adjacent'): ('A06', 'Analyze a cryptographic key lifecycle decision for nonce rotation and destruction; no reachable abuse-path decision changes.', 'security-privacy-gate', 'security-privacy-gate', ('secret-configuration-security', 'cryptography-key-lifecycle'), 'cryptography-key-lifecycle', ()),
    ('threat-modeling', 'simple'): ('A06', 'Implement an accepted backend category label change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('authentication-security', 'selected'): ('A06', 'Analyze a credential or session lifecycle behavior change that affects token issuance, transport, storage, renewal, privilege change, rotation, revocation, logout, recovery, authorization, disclosure, or replay handling.', 'security-privacy-gate', 'security-privacy-gate', ('authentication-security',), 'security-credential-session-lifecycle', ('security-credential-session-lifecycle',)),
    ('authentication-security', 'domain-owned'): ('A06', 'Implement the accepted macOS AppKit app window state behavior for the music client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('macos-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('authentication-security', 'adjacent'): ('A06', 'Analyze tenant authorization and object permission enforcement; credential lifecycle behavior remains unchanged.', 'security-privacy-gate', 'security-privacy-gate', ('permission-boundary-modeling', 'threat-modeling'), 'generic-security-risk', ()),
    ('authentication-security', 'simple'): ('A06', 'Implement an accepted backend tax-description change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('secret-configuration-security', 'selected'): ('A06', 'Analyze a cryptographic construction and key lifecycle decision for nonce, ciphertext envelope, rotation, recovery, and destruction.', 'security-privacy-gate', 'security-privacy-gate', ('secret-configuration-security', 'cryptography-key-lifecycle'), 'cryptography-key-lifecycle', ('cryptography-key-lifecycle',)),
    ('secret-configuration-security', 'domain-owned'): ('A06', 'Implement an accepted Windows packaged desktop application protocol-handler change for the map client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('windows-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('secret-configuration-security', 'adjacent'): ('A06', 'Analyze a credential or session lifecycle behavior change that affects token issuance, transport, storage, renewal, privilege change, rotation, revocation, logout, recovery, authorization, disclosure, or replay handling for an operator login.', 'security-privacy-gate', 'security-privacy-gate', ('authentication-security',), 'security-credential-session-lifecycle', ()),
    ('secret-configuration-security', 'simple'): ('A06', 'Implement an accepted backend status-text change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('api-contract-design', 'selected'): ('A07', 'With an accepted Engineering Brief, analyze an input shape change with no security sink.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('api-contract-design',), 'security-anti-input-shape', ('security-anti-input-shape',)),
    ('api-contract-design', 'domain-owned'): ('A07', 'Implement the accepted Android app foreground service and background work scheduling behavior for the fitness client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('api-contract-design', 'adjacent'): ('A07', 'With an accepted Engineering Brief, analyze only DTO, database record, and UI label mapping with no input-shape decision.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('model-boundary-mapping',), 'dto-model-boundary-analysis', ()),
    ('api-contract-design', 'simple'): ('A07', 'Implement an accepted backend internal helper rename.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('model-boundary-mapping', 'selected'): ('A07', 'With an accepted Engineering Brief, analyze only DTO, relational table, and UI label mapping; there is no domain identity, lifecycle, aggregate, invariant, or writer-authority decision.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('model-boundary-mapping',), 'dto-model-boundary-analysis', ('dto-model-boundary-analysis',)),
    ('model-boundary-mapping', 'domain-owned'): ('A07', 'Implement the accepted iOS scene and background task expiration behavior for the recipe client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('model-boundary-mapping', 'adjacent'): ('A07', 'With an accepted Engineering Brief, analyze only a distributable SDK public contract; mapper placement remains fixed.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('sdk-library-contract-design',), 'sdk-contract-analysis', ()),
    ('model-boundary-mapping', 'simple'): ('A07', 'Implement an accepted backend comment spelling correction.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('sdk-library-contract-design', 'selected'): ('A07', 'With an accepted Engineering Brief, analyze only a distributable SDK public contract and compatibility change; owner-private reuse placement is fixed.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('sdk-library-contract-design',), 'sdk-contract-analysis', ('sdk-contract-analysis',)),
    ('sdk-library-contract-design', 'domain-owned'): ('A07', 'Implement the accepted macOS AppKit app window state behavior for the writing client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('macos-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('sdk-library-contract-design', 'adjacent'): ('A07', 'With an accepted Engineering Brief, analyze an input shape change with no security sink or library export change.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('api-contract-design',), 'security-anti-input-shape', ()),
    ('sdk-library-contract-design', 'simple'): ('A07', 'Implement an accepted backend private constant rename.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('version-compatibility', 'selected'): ('A08', 'Review a production rollout with compatibility stop signals and rollback.', 'delivery-release-gate', 'delivery-release-gate', ('release-rollback', 'version-compatibility'), 'review-release-risk', ('production-release-decision',)),
    ('version-compatibility', 'domain-owned'): ('A08', 'Implement an accepted Windows packaged desktop application protocol-handler change for the mail client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('windows-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('version-compatibility', 'adjacent'): ('A08', 'With an accepted Engineering Brief, analyze only the data consistency and recovery artifact; release versions are fixed.', 'data-middleware-change-builder', 'quality-test-gate', ('transaction-consistency',), 'data-consistency-artifact', ()),
    ('version-compatibility', 'simple'): ('A08', 'Implement an accepted backend metric description change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('data-migration-design', 'selected'): ('A08', 'Plan a database migration with backfill coexistence and rollback.', 'engineering-change-analysis', 'delivery-release-gate', ('data-migration-design', 'transaction-consistency', 'release-rollback'), 'database-migration-coexistence-rollback', ('database-migration-analysis',)),
    ('data-migration-design', 'domain-owned'): ('A08', 'Implement the accepted Android app foreground service and background work scheduling behavior for the budget client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('data-migration-design', 'adjacent'): ('A08', 'Review the production rollout decision for compatibility stop signals and rollback; no data conversion is required.', 'delivery-release-gate', 'delivery-release-gate', ('release-rollback', 'version-compatibility'), 'review-release-risk', ()),
    ('data-migration-design', 'simple'): ('A08', 'Implement an accepted backend internal test-name change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('release-rollback', 'selected'): ('A08', 'Review the production rollout decision for a material production apply and release rollback risk.', 'delivery-release-gate', 'delivery-release-gate', ('release-rollback', 'version-compatibility'), 'review-release-risk', ('production-release-decision',)),
    ('release-rollback', 'domain-owned'): ('A08', 'Implement the accepted iOS scene and background task expiration behavior for the podcast client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('release-rollback', 'adjacent'): ('A08', 'With an accepted Engineering Brief, analyze only the data consistency and recovery artifact for the partner snapshot.', 'data-middleware-change-builder', 'quality-test-gate', ('transaction-consistency',), 'data-consistency-artifact', ()),
    ('release-rollback', 'simple'): ('A08', 'Implement an accepted backend private error-message correction.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('build-tool-professional-usage', 'selected'): ('A09', 'Implement an accepted repository-owned generator source change.', 'repository-tooling-change-builder', 'ai-code-review-refactor', ('build-tool-professional-usage', 'targeted-validation-selection'), 'implementation-owner:repository-tooling-change-builder', ('dynamic-foundation:build-tool-professional-usage',)),
    ('build-tool-professional-usage', 'domain-owned'): ('A09', 'Implement the accepted macOS AppKit app window state behavior for the video client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('macos-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('build-tool-professional-usage', 'adjacent'): ('A09', 'Select regression tests and validate final changed service paths; repository generation remains unchanged.', 'quality-test-gate', 'ai-code-review-refactor', ('regression-testing',), 'implementation-owner:quality-test-gate', ()),
    ('build-tool-professional-usage', 'simple'): ('A09', 'Implement an accepted backend currency symbol display change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('targeted-validation-selection', 'selected'): ('A09', 'Implement an accepted repository-owned generator source change. The editable template, generator, derived artifact, committed policy, and freshness check are known. The owner-private generator method and file placement were already fixed.', 'repository-tooling-change-builder', 'ai-code-review-refactor', ('build-tool-professional-usage', 'targeted-validation-selection'), 'implementation-owner:repository-tooling-change-builder', ('dynamic-foundation:targeted-validation-selection',)),
    ('targeted-validation-selection', 'domain-owned'): ('A09', 'Implement an accepted Windows packaged desktop application protocol-handler change for the chat client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('windows-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('targeted-validation-selection', 'adjacent'): ('A09', 'Implement a local frontend component state fix; repository test entrypoints remain fixed.', 'frontend-change-builder', 'ai-code-review-refactor', ('state-management-design',), 'implementation-owner:frontend-change-builder', ()),
    ('targeted-validation-selection', 'simple'): ('A09', 'Implement an accepted backend address-line formatting change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('state-management-design', 'selected'): ('A10', 'Implement a local frontend component state fix; shared installed client behavior remains unchanged because a framework name has no repository build release or published-artifact target evidence.', 'frontend-change-builder', 'ai-code-review-refactor', ('state-management-design',), 'implementation-owner:frontend-change-builder', ('dynamic-foundation:state-management-design',)),
    ('state-management-design', 'domain-owned'): ('A10', 'Implement the accepted Android app foreground service and background work scheduling behavior for the banking client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('state-management-design', 'adjacent'): ('A10', 'Select regression tests and validate the final changed paths; Windows service lifecycle behavior remains unchanged for the accepted backend repair.', 'quality-test-gate', 'ai-code-review-refactor', ('regression-testing',), 'implementation-owner:quality-test-gate', ()),
    ('state-management-design', 'simple'): ('A10', 'Implement an accepted backend product label change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('regression-testing', 'selected'): ('A11', 'Select regression tests and validate the final changed paths; Windows service lifecycle behavior remains unchanged.', 'quality-test-gate', 'ai-code-review-refactor', ('regression-testing',), 'implementation-owner:quality-test-gate', ('dynamic-foundation:regression-testing',)),
    ('regression-testing', 'domain-owned'): ('A11', 'Implement the accepted iOS scene and background task expiration behavior for the transit client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('regression-testing', 'adjacent'): ('A11', 'Implement a local frontend component state fix; recurrence behavior is not part of the change.', 'frontend-change-builder', 'ai-code-review-refactor', ('state-management-design',), 'implementation-owner:frontend-change-builder', ()),
    ('regression-testing', 'simple'): ('A11', 'Implement an accepted backend receipt header change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('failure-diagnosis', 'selected'): ('A12', 'Diagnose the root cause of a failing background worker from logs tests and source evidence.', 'engineering-change-analysis', 'reliability-observability-gate', ('failure-diagnosis',), 'failure-diagnosis-analysis', ('incident-response-coordination',)),
    ('failure-diagnosis', 'domain-owned'): ('A12', 'Implement the accepted macOS AppKit app window state behavior for the weather-station client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('macos-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('failure-diagnosis', 'adjacent'): ('A12', 'Implement structured redacted logs with correlation fields; the failure cause is already established.', 'logging-design-gate', 'logging-design-gate', ('logging-error-handling',), 'implementation-owner:logging-design-gate', ()),
    ('failure-diagnosis', 'simple'): ('A12', 'Implement an accepted backend timestamp display-format change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('logging-error-handling', 'selected'): ('A13', 'Implement structured redacted logs with correlation fields; macOS installed application lifecycle behavior remains unchanged.', 'logging-design-gate', 'logging-design-gate', ('logging-error-handling',), 'implementation-owner:logging-design-gate', ('dynamic-foundation:logging-error-handling',)),
    ('logging-error-handling', 'domain-owned'): ('A13', 'Implement an accepted Windows packaged desktop application protocol-handler change for the library client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('windows-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('logging-error-handling', 'adjacent'): ('A13', 'Select regression tests and validate the final changed paths; Windows service lifecycle behavior remains unchanged for the accepted worker repair.', 'quality-test-gate', 'ai-code-review-refactor', ('regression-testing',), 'implementation-owner:quality-test-gate', ()),
    ('logging-error-handling', 'simple'): ('A13', 'Implement an accepted backend unit abbreviation change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('transaction-consistency', 'selected'): ('A14', 'With an accepted Engineering Brief, analyze only the data consistency and recovery artifact.', 'data-middleware-change-builder', 'quality-test-gate', ('transaction-consistency',), 'data-consistency-artifact', ('distributed-workflow-analysis',)),
    ('transaction-consistency', 'domain-owned'): ('A14', 'Implement the accepted Android app foreground service and background work scheduling behavior for the shopping client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('android-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('transaction-consistency', 'adjacent'): ('A14', 'With an accepted Engineering Brief, analyze an input shape change with no security sink for the partner request.', 'data-api-contract-changer', 'architecture-impact-reviewer', ('api-contract-design',), 'security-anti-input-shape', ()),
    ('transaction-consistency', 'simple'): ('A14', 'Implement an accepted backend region-name display change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
    ('documentation-generation', 'selected'): ('A15', 'Update public migration documentation and validate examples; Linux graphical desktop session and D-Bus behavior remain unchanged.', 'change-documentation-gate', 'change-documentation-gate', ('documentation-generation',), 'migration-documentation', ('security-anti-scanner-report',)),
    ('documentation-generation', 'domain-owned'): ('A15', 'Implement the accepted iOS scene and background task expiration behavior for the language client.', 'installed-client-change-builder', 'ai-code-review-refactor', ('ios-ipados-platform-extension',), 'implementation-owner:installed-client-change-builder', ()),
    ('documentation-generation', 'adjacent'): ('A15', 'Implement a local frontend component state fix; audience-facing documentation remains unchanged.', 'frontend-change-builder', 'ai-code-review-refactor', ('state-management-design',), 'implementation-owner:frontend-change-builder', ()),
    ('documentation-generation', 'simple'): ('A15', 'Implement an accepted backend invoice note wording change.', 'backend-change-builder', 'ai-code-review-refactor', (), 'implementation-owner:backend-change-builder', ()),
}
PHASE2_A_FOUNDATIONS = frozenset(
    skill
    for _group, _owner, _review, foundations in PHASE2_A_GROUPS
    for skill in foundations
)
PHASE2_A_FOUNDATION_TRIPLES = frozenset(
    {
        ("foundation", skill, effect)
        for skill in PHASE2_A_FOUNDATIONS
        for effect in (
            "selected",
            "domain-owned",
            "adjacent",
            "simple",
        )
    }
)
PHASE2_A_PREDECESSOR_ROW_COUNT = 313
PHASE2_A_PREDECESSOR_ROWS_SHA256 = (
    "d3f44baa2d9b98f2712900ca5d5ef54b4a762544ddcc4549cbdeeca4368e4b72"
)
PHASE2_A_SELECTED_PRIMARY_OVERRIDES = {'consumer-impact-analysis': 'engineering-change-analysis',
 'failure-contract-design': 'engineering-change-analysis',
 'idempotency-retry-design': 'engineering-change-analysis',
 'data-migration-design': 'engineering-change-analysis',
 'failure-diagnosis': 'engineering-change-analysis'}
PHASE2_F02_SPECIAL_SELECTOR_IDS = {
    "architecture-tradeoff-analysis": "explicit-architecture-tradeoff",
    "test-data-management": "explicit-test-data-analysis",
    "authentication-authorization": (
        "explicit-authentication-authorization-analysis"
    ),
    "repeat-failure-analysis": "review-repeat-failure",
}
PHASE2_F02_TARGET_PROMPT_MARKERS = {
    "architecture-tradeoff-analysis": (
        "architecture",
        "module boundary",
        "topology",
    ),
    "test-data-management": (
        "test data",
        "fixture",
        "cleanup",
    ),
    "authentication-authorization": (
        "authentication",
        "authorization",
        "sign-in",
    ),
    "repeat-failure-analysis": (
        "repair",
        "validator",
        "failure",
    ),
}
PHASE2_F02_ANTI_TRIGGER_PROMPTS = {
    "architecture-tradeoff-analysis": (
        "Implement the accepted backend calculation after the architecture "
        "topology and module boundaries were fixed; no tradeoff decision "
        "remains."
    ),
    "test-data-management": (
        "Change the accepted backend calculation while fixture creation, "
        "test data lifetime, isolation, and cleanup remain unchanged."
    ),
    "authentication-authorization": (
        "Implement an accepted backend invoice total after authentication "
        "succeeds; no "
        "authorization handoff or policy decision is requested."
    ),
    "repeat-failure-analysis": (
        "Implement an accepted backend pricing rule after the first "
        "validator failure; no repair path or cause has repeated."
    ),
}
PHASE2_F01_MULTITASK_PROMPT_MARKERS = {
    "change-documentation-gate": "documentation",
    "data-api-contract-changer": "api compatibility",
    "data-middleware-change-builder": "data consistency",
    "delivery-release-gate": "release rollback",
    "domain-impact-modeler": "domain invariant",
    "engineering-artifact-review": "brief review",
    "engineering-change-analysis": "repository ownership analysis",
    "experience-impact-modeler": "interaction acceptance",
    "integration-change-builder": "integration handoff",
    "logging-design-gate": "logging redaction",
    "reliability-observability-gate": "resilience acceptance",
    "security-privacy-gate": "risk-assessment acceptance",
    "task-dag-planner": "task dependency plan",
}
PHASE2_F01_CONFLICT_NEGATIVE_PROMPTS = {
    "data-middleware-change-builder": (
        "Implement an accepted database cache behavior change."
    ),
    "integration-change-builder": (
        "Implement an accepted external integration behavior change."
    ),
    "logging-design-gate": (
        "Implement an accepted structured logging redaction change."
    ),
}
LEGACY_ROUTE_CASE_IDS = {
    "capcov-route-react-web-owner",
    "capcov-route-pwa-only-owner",
    "capcov-route-android-owner",
    "capcov-route-ios-owner",
    "capcov-route-windows-owner",
    "capcov-route-macos-owner",
    "capcov-route-linux-desktop-owner",
    "capcov-route-flutter-android-ios",
    "capcov-route-electron-windows",
    "capcov-route-cross-alone-rejected",
    "capcov-route-backend-no-installed-client",
    "capcov-route-kotlin-backend-no-android",
    "capcov-route-terraform-source",
    "capcov-route-terraform-apply",
    "capcov-removed-mobile-skill-id-unsupported",
    "capcov-unknown-installed-client-target-analysis",
}
NATURAL_CLIENT_ROUTE_CASE_IDS = {
    "capcov-natural-android-screen-state",
    "capcov-natural-android-foreground-background",
    "capcov-natural-ios-swiftui-view-state",
    "capcov-natural-ios-scene-background-task",
    "capcov-natural-windows-packaged-desktop-app",
    "capcov-natural-macos-appkit-app",
    "capcov-natural-linux-graphical-desktop-app",
    "capcov-natural-flutter-android-ios",
    "capcov-natural-electron-windows",
    "capcov-natural-kotlin-backend",
    "capcov-natural-swift-linux-backend",
    "capcov-natural-csharp-linux-backend",
    "capcov-natural-cpp-linux-server",
    "capcov-natural-dart-backend",
    "capcov-natural-cross-target-unknown",
    "capcov-natural-pwa-web-only",
    "capcov-natural-android-store-rollout",
}
NEIGHBOR_CLIENT_ROUTE_CASE_IDS = {
    "capcov-neighbor-android-app-state-backend-payload",
    "capcov-neighbor-ios-app-state-backend-payload",
    "capcov-neighbor-macos-swiftui-window",
    "capcov-neighbor-android-compose-view",
    "capcov-neighbor-windows-wpf-window",
    "capcov-neighbor-windows-winui-view",
}
DOCUMENTATION_ORDER_NEGATIVE_ROUTE_CASE_IDS = {
    "capcov-docs-order-android-compose",
    "capcov-docs-order-leading-only-android-compose-analyze",
    "capcov-docs-order-leading-only-android-compose-inspect",
    "capcov-docs-order-leading-only-android-compose-review",
    "capcov-docs-order-macos-swiftui",
    "capcov-docs-order-windows-wpf",
    "capcov-docs-order-windows-winui",
}
ANDROID_ACCESSIBILITY_ROUTE_CASE_IDS = {
    "capcov-route-android-accessibility-owner",
    "capcov-route-android-compose-semantics",
    "capcov-route-android-dpad-navigation",
    "capcov-route-android-pointer-alternative",
    "capcov-route-flutter-android-accessibility",
    "capcov-route-react-native-android-accessibility",
    "capcov-route-android-accessibility-review",
    "capcov-route-flutter-android-ios-accessibility-overflow",
    "capcov-route-android-accessibility-api-name-negative",
    "capcov-route-android-talkback-constant-rename-negative",
    "capcov-route-backend-json-dynamic-type-negative",
    "capcov-route-backend-kotlin-accessibility-field-negative",
    "capcov-route-backend-accessibility-diff-field-negative",
    "capcov-route-ios-lifecycle-no-android-accessibility",
    "capcov-route-android-accessibility-docs-negative",
    "capcov-route-cross-platform-accessibility-target-unknown",
}
ROUTE_CASE_IDS = (
    LEGACY_ROUTE_CASE_IDS
    | NATURAL_CLIENT_ROUTE_CASE_IDS
    | NEIGHBOR_CLIENT_ROUTE_CASE_IDS
    | DOCUMENTATION_ORDER_NEGATIVE_ROUTE_CASE_IDS
    | ANDROID_ACCESSIBILITY_ROUTE_CASE_IDS
)


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
            "l2_eligibility": [],
            "obligations": ["high-risk pre-implementation evidence"],
            "unresolved": [],
            "edit_status": "allowed",
        },
    }


def _route(
    prompt: str,
    *,
    task_id: str,
    **kwargs: object,
) -> dict[str, object]:
    decision = ROUTE_ORACLE.route(
        prompt,
        main_execution=_main_execution(task_id),
        **kwargs,
    )
    result = decision["route_result"]
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }


def _trace(
    prompt: str,
    *,
    task_id: str,
    **kwargs: object,
) -> dict[str, object]:
    return ROUTE_ORACLE.route_with_trace(
        prompt,
        main_execution=_main_execution(task_id),
        **kwargs,
    )


def _admission_registries() -> tuple[dict, dict, dict]:
    return (
        load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
        load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
        load_yaml_file(ROOT / "src/registry/domain-skills.yaml"),
    )


def _admission_observation(
    *,
    layer: str,
    skill: str,
    case_kind: str,
) -> dict[str, object]:
    rows = load_yaml_file(
        ROOT / "evals/capability-coverage/admission-cases.yaml"
    )["cases"]
    row = next(
        item
        for item in rows
        if item["layer"] == layer
        and item["skill"] == skill
        and item["case_kind"] == case_kind
    )
    observed = ROUTE_ORACLE.route_with_trace(
        row["prompt"],
        main_execution=row["main_execution"],
    )
    return {
        "main_execution": copy.deepcopy(row["main_execution"]),
        "route_decision": observed["route_decision"],
        "winner_trace": observed["winner_trace"],
    }


def _classify_t4b_admission_effect(
    *,
    case_id: str,
    layer: str,
    skill: str,
    declared_case_kind: str,
    observation: dict[str, object],
    registries: tuple[dict, dict, dict] | None = None,
) -> dict[str, object]:
    classifier = getattr(
        CAPABILITY_COVERAGE,
        "_classify_admission_effect",
        None,
    )
    if not callable(classifier):
        raise AssertionError(
            f"[{case_id}] expected callable=_classify_admission_effect; "
            "actual=missing"
        )
    professional, foundation, domain = (
        _admission_registries() if registries is None else registries
    )
    result = classifier(
        layer=layer,
        skill=skill,
        declared_case_kind=declared_case_kind,
        main_execution=observation["main_execution"],
        route_decision=observation["route_decision"],
        winner_trace=observation["winner_trace"],
        professional_registry=professional,
        foundation_registry=foundation,
        domain_registry=domain,
    )
    if (
        not isinstance(result, dict)
        or set(result) != {"computed_effect", "errors"}
        or not isinstance(result.get("errors"), list)
    ):
        raise AssertionError(
            f"[{case_id}] expected classifier result fields="
            "['computed_effect','errors']; "
            f"actual={result!r}"
        )
    return result


def _t4b_admission_integrity_errors(
    *,
    case_id: str,
    observation: dict[str, object],
) -> list[str]:
    validator = getattr(
        CAPABILITY_COVERAGE,
        "_admission_route_integrity_errors",
        None,
    )
    if not callable(validator):
        raise AssertionError(
            f"[{case_id}] expected callable="
            "_admission_route_integrity_errors; actual=missing"
        )
    errors = validator(
        main_execution=observation["main_execution"],
        route_decision=observation["route_decision"],
        winner_trace=observation["winner_trace"],
    )
    if not isinstance(errors, list) or not all(
        isinstance(item, str) and item for item in errors
    ):
        raise AssertionError(
            f"[{case_id}] expected integrity errors=list[str]; "
            f"actual={errors!r}"
        )
    return errors


MATRIX_CONSUMERS = {
    "capcov-matrix-consumer-professionalism-regression": (
        "validate-professionalism-regression.py",
        "capcov_validate_professionalism_regression",
    ),
    "capcov-matrix-consumer-eval-routing": (
        "eval-routing.py",
        "capcov_eval_routing_consumer",
    ),
    "capcov-matrix-consumer-validate-skills": (
        "validate-skills.py",
        "capcov_validate_skills",
    ),
    "capcov-matrix-consumer-validate-capabilities": (
        "validate-capabilities.py",
        "capcov_validate_capabilities",
    ),
}


def _load_matrix_consumers() -> dict[str, object]:
    loaded: dict[str, object] = {}
    for case_id, (script_name, module_name) in MATRIX_CONSUMERS.items():
        spec = importlib.util.spec_from_file_location(
            module_name,
            ROOT / "scripts" / script_name,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        loaded[case_id] = module
    return loaded


def _write_yaml_mapping(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in payload.items()
        )
        + "\n",
        encoding="utf-8",
    )


def _minimal_valid_matrix() -> dict[str, object]:
    required_space = {
        "engineering_tasks": ["web implementation"],
        "platforms": ["Web browser"],
        "language_runtimes": ["TypeScript"],
        "cross_cutting_risks": ["accessibility"],
        "product_domains": ["AI product"],
        "routing_combinations": ["route-react-web"],
    }
    base_entry = {
        "surface": "bounded test surface",
        "task_type": "bounded test task",
        "language_runtime": [],
        "cross_cutting_risks": [],
        "expected_professional_owner": "frontend-change-builder",
        "expected_domain_extensions": [],
        "expected_foundation_skills": [],
        "coverage_status": "partial",
        "disposition": "retain-partial",
        "reason": "Gap: this minimal fixture retains bounded path context only.",
        "evidence_fixtures": [
            "evals/routing/capability-coverage-cases.yaml"
        ],
    }
    entries = [
        base_entry
        | {
            "id": "engineering-web-implementation",
            "axis": "engineering-task",
            "task_type": "web implementation",
        },
        base_entry
        | {
            "id": "platform-web-browser",
            "axis": "platform",
            "surface": "Web browser",
        },
        base_entry
        | {
            "id": "language-typescript",
            "axis": "language-runtime",
            "language_runtime": ["TypeScript"],
        },
        base_entry
        | {
            "id": "risk-accessibility",
            "axis": "cross-cutting-risk",
            "cross_cutting_risks": ["accessibility"],
        },
        base_entry
        | {
            "id": "domain-ai-product",
            "axis": "product-domain",
            "surface": "AI product",
        },
        base_entry
        | {
            "id": "route-react-web",
            "axis": "routing-combination",
        },
    ]
    return {
        "schema_version": 1,
        "kind": "changeforge.capability_coverage_matrix",
        "required_space": required_space,
        "entries": entries,
    }


def _set_first_entry_covered(
    matrix: dict[str, object],
    evidence_fixtures: list[str],
) -> None:
    entry = matrix["entries"][0]
    entry["coverage_status"] = "covered"
    entry["disposition"] = "retain-existing"
    entry["reason"] = "Current exact behavioral evidence covers this value."
    entry["evidence_fixtures"] = evidence_fixtures


def _write_matrix_fixture(
    root: Path,
    payload: dict[str, object],
    *,
    name: str,
) -> Path:
    evidence = (
        root
        / "evals"
        / "routing"
        / "capability-coverage-cases.yaml"
    )
    if not evidence.exists():
        _write_yaml_mapping(
            evidence,
            {"schema_version": 1, "cases": []},
        )
    matrix_path = root / name
    _write_yaml_mapping(matrix_path, payload)
    return matrix_path


class CapabilityCoverageRedTests(unittest.TestCase):
    maxDiff = None

    def test_new_professional_route_boundaries_do_not_overlap(self) -> None:
        cases = {
            "repository-positive": (
                "Implement an accepted repository-owned generator source change.",
                "repository-tooling-change-builder",
            ),
            "repository-adjacent": (
                "Implement an accepted Terraform module source change.",
                "platform-infrastructure-change-builder",
            ),
            "incident-positive": (
                "Coordinate an active multi-responder incident with command, "
                "mitigation, communications, and handoff.",
                "incident-response-coordinator",
            ),
            "incident-adjacent": (
                "Analyze an SLO degradation and resilience design with no "
                "active incident command.",
                "reliability-observability-gate",
            ),
        }
        actual = {
            label: _route(prompt, task_id=self._testMethodName)["primary_skill"]
            for label, (prompt, _expected) in cases.items()
        }
        self.assertEqual(
            {label: expected for label, (_prompt, expected) in cases.items()},
            actual,
        )
        self.assertNotEqual(
            actual["repository-positive"],
            actual["incident-positive"],
        )

    def test_phase_two_foundation_route_families_and_boundaries(self) -> None:
        expected_selected = {
            "filesystem-backend": (
                "Implement a backend service change that atomically replaces a local "
                "file and spawns a child process with bounded cancellation.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-installed-client": (
                "Implement an accepted Windows installed-client change that replaces "
                "a local settings file under a trusted path.",
                "installed-client-change-builder",
                "filesystem-process-safety",
            ),
            "node-process-signal-child": (
                "Implement Node.js backend process signal and child-process shutdown behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-timer-cancellation": (
                "Implement Node.js backend timer and AbortSignal cancellation behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-module-flags": (
                "Implement Node.js backend ESM module entrypoint and runtime flag behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-resource-worker": (
                "Implement Node.js backend active-resource and Worker thread ownership behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-streams": (
                "Implement Node.js backend stream pipeline backpressure behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-buffer": (
                "Implement Node.js backend Buffer encoding and alias ownership behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-event-loop": (
                "Implement Node.js backend event loop and process.nextTick fairness behavior.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "workflow-compensation": (
                "Analyze compensation after independently committed service effects.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-reconciliation": (
                "Analyze reconciliation of desired workflow state against participant facts.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-repair": (
                "Analyze authorized repair of stuck cross-service workflow state.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-evolution": (
                "Analyze active-workflow definition evolution across independently committed participants.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "audit-analysis": (
                "Analyze audit evidence integrity for missing-record detection and "
                "tamper verification.",
                "security-privacy-gate",
                "audit-evidence-integrity",
            ),
            "audit-implementation": (
                "Implement audit evidence integrity for protected audit storage and export.",
                "logging-design-gate",
                "audit-evidence-integrity",
            ),
        }
        for case_id, (prompt, owner, foundation) in expected_selected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertIn(foundation, actual["layer3_skills"])
                self.assertLessEqual(len(actual["layer3_skills"]), 3)
                if foundation == "audit-evidence-integrity":
                    self.assertNotIn("observability", actual["layer3_skills"])

        expected_rejected = {
            "filesystem-repository-no-effect": (
                "Implement an accepted repository-owned generator source change "
                "with no local file mutation or child-process behavior.",
                "repository-tooling-change-builder",
                "filesystem-process-safety",
            ),
            "node-typescript-only": (
                "Implement a Node.js backend TypeScript-only type change with runtime behavior unchanged.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-browser": (
                "Implement a React web browser component using streams with no Node.js runtime behavior.",
                "frontend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-build-package": (
                "Implement a Node.js backend package manifest and build graph change; runtime behavior is unchanged.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-business-rule": (
                "Implement a Node.js backend business rule with no runtime or core-library behavior change.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-runtime-unchanged": (
                "Implement a Node.js backend endpoint; runtime semantics unchanged.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "workflow-atomic": (
                "With an accepted Engineering Brief, analyze only the data consistency "
                "and recovery artifact for one atomic database transaction with no "
                "independently committed service effects.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-local-retry": (
                "Analyze local retry idempotency with no cross-service workflow state.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "workflow-schema-only": (
                "Analyze a workflow message schema-only compatibility change with no runtime state transition.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "workflow-engine-mechanics": (
                "Implement workflow engine scheduler mechanics with no participant business effects.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "tenant-saas-lifecycle": (
                "Analyze SaaS tenant provisioning, subscription billing, entitlements, "
                "and customization lifecycle with no isolation mechanism change.",
                "engineering-change-analysis",
                "tenant-isolation",
            ),
        }
        for case_id, (prompt, owner, foundation) in expected_rejected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertNotIn(foundation, actual["layer3_skills"])
                self.assertLessEqual(len(actual["layer3_skills"]), 3)

    def test_phase_two_foundation_antitriggers_are_independent(self) -> None:
        rejected = {
            "filesystem-registry-original": (
                "Implement a backend service atomic file replacement with no local "
                "filesystem mutation path-authority or child-process contract changes.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-root-original": (
                "Implement a backend service local file change. No task-local "
                "filesystem or child-process safety decision changes.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-positive-token-no-change": (
                "Implement a backend service that atomically replaces a local file, "
                "but no task-local filesystem or child-process safety decision changes.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "node-typescript-stream": (
                "Implement a Node.js backend TypeScript-only stream interface.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-browser-only": (
                "Implement a Node.js backend adapter for a browser-only stream interface.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-build-package-module-config": (
                "Implement a Node.js backend build-policy and package-policy module "
                "export config-only change.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-business-process-state": (
                "Implement a Node.js backend business-rule process-state calculation only.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-registry-original": (
                "Implement a Node.js backend stream endpoint; Node.js runtime and "
                "core-library behavior remains unchanged.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "workflow-atomic-compensation": (
                "Analyze distributed workflow participant compensation inside one "
                "atomic transaction.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "workflow-local-retry-compensation": (
                "Analyze cross-service workflow compensation as local retry only.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "workflow-schema-reconciliation": (
                "Analyze distributed workflow reconciliation for a schema-only message change.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "workflow-engine-repair": (
                "Analyze active-workflow repair for engine mechanics only.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
            "workflow-registry-original": (
                "Analyze distributed workflow compensation with no independently "
                "committed participant effect or durable workflow state changes.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in rejected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertNotIn(foundation, actual["layer3_skills"])
                self.assertLessEqual(len(actual["layer3_skills"]), 3)

    def test_phase_two_r02_normalization_mixed_and_negated_boundaries(self) -> None:
        rejected = {
            "filesystem-spaced-punctuated-registry-clause": (
                "Implement an accepted repository-owned generator source change that "
                "atomically replaces a local file; no local filesystem mutation, "
                "path authority, or child process contract changes.",
                "repository-tooling-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-spaced-root-clause": (
                "Implement an accepted repository-owned generator source change with "
                "an atomic file operation, but no task local filesystem or child "
                "process safety decision changes.",
                "repository-tooling-change-builder",
                "filesystem-process-safety",
            ),
            "workflow-local-retry-equivalent": (
                "Analyze cross-service workflow compensation limited to local retry.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in rejected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertNotIn(foundation, actual["layer3_skills"])

        ambiguous_prompt = (
            "Implement an accepted repository-owned generator source change "
            "for an unknown local path whose filesystem behavior remains "
            "unchanged."
        )
        normalized = " ".join(ambiguous_prompt.casefold().split())
        ambiguous_facts = ROUTE_ORACLE._routing_boundary_fact_snapshots(
            normalized,
            parsed=ROUTE_ORACLE._parse_normalized_task_request(normalized),
        )
        self.assertEqual(1, len(ambiguous_facts))
        self.assertEqual("unknown", ambiguous_facts[0].path_mutation)
        self.assertEqual("ambiguous", ambiguous_facts[0].filesystem_behavior)
        ambiguous_route = _route(
            ambiguous_prompt,
            task_id=f"{self._testMethodName}:unknown-path",
        )
        self.assertEqual("analyzed", ambiguous_route["path"])
        self.assertEqual(
            "engineering-change-analysis",
            ambiguous_route["primary_skill"],
        )
        ambiguous_trace = _trace(
            ambiguous_prompt,
            task_id=f"{self._testMethodName}:unknown-path-trace",
        )
        self.assertEqual(
            "critical-unknown",
            ambiguous_trace["winner_trace"]["selected_candidate"][
                "candidate_id"
            ],
        )
        self.assertIn(
            "critical-verification-unknown",
            ambiguous_trace["winner_trace"]["selected_candidate"][
                "evidence"
            ],
        )

        registration_prompts = (
            "Implement the accepted repository CLI so --add-dir registers a "
            "user-owned skills directory for the same OS user while "
            "child-process behavior remains unchanged.",
            "Implement the accepted repository CLI with child-process behavior "
            "unchanged while --add-dir registers a user-owned skills directory "
            "for the same OS user.",
        )
        registration_routes = []
        for order, prompt in enumerate(registration_prompts):
            with self.subTest(registration_order=order):
                actual = _route(
                    prompt,
                    task_id=f"{self._testMethodName}:registration:{order}",
                )
                registration_routes.append(actual)
                self.assertEqual(
                    "repository-tooling-change-builder",
                    actual["primary_skill"],
                )
                self.assertIn(
                    "filesystem-process-safety",
                    actual["layer3_skills"],
                )
                self.assertNotEqual(
                    "security-privacy-gate",
                    actual["primary_skill"],
                )
                self.assertNotEqual(
                    "security-privacy-gate",
                    actual["review_skill"],
                )
        self.assertEqual(registration_routes[0], registration_routes[1])

        aggregate_only = _route(
            "Implement an accepted repository-owned generator source change "
            "while child-process behavior remains unchanged.",
            task_id=f"{self._testMethodName}:aggregate-only",
        )
        self.assertEqual(
            "repository-tooling-change-builder",
            aggregate_only["primary_skill"],
        )
        self.assertNotIn(
            "filesystem-process-safety",
            aggregate_only["layer3_skills"],
        )

        selected = {
            "node-package-metadata-with-runtime": (
                "Implement a Node.js backend ESM runtime flag change plus "
                "package-policy metadata.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-business-rule-with-runtime": (
                "Implement a Node.js backend process-signal shutdown behavior plus "
                "a business-rule update.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "workflow-negated-schema-only": (
                "Analyze distributed workflow reconciliation; this is not a "
                "schema-only change.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-negated-local-retry-only": (
                "Analyze cross-service workflow compensation; this is not a local "
                "retry only.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in selected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertIn(foundation, actual["layer3_skills"])
                self.assertLessEqual(len(actual["layer3_skills"]), 3)

    def test_phase_two_r02_clause_level_effect_classification(self) -> None:
        rejected = {
            "filesystem-slash-both-unchanged": (
                "Implement an accepted repository-owned generator source change with "
                "an atomic file token, but no task-local filesystem / child-process "
                "safety decision changes.",
                "repository-tooling-change-builder",
                "filesystem-process-safety",
            ),
            "workflow-local-retry-participant-facts": (
                "Analyze local retry compensation against participant facts.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in rejected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertNotIn(foundation, actual["layer3_skills"])

        selected = {
            "filesystem-child-changed-filesystem-unchanged": (
                "Implement an accepted repository-owned generator source change with "
                "a child-process contract change; there is no local filesystem "
                "mutation, and path authority remains unchanged.",
                "repository-tooling-change-builder",
                "filesystem-process-safety",
            ),
            "node-esm-package-mixed": (
                "Implement a Node.js backend ESM module export change plus "
                "package-policy metadata.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-child-stdio-business-mixed": (
                "Implement a Node.js backend child-process stdio shutdown change plus "
                "a business-rule update.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-worker-resource-package-mixed": (
                "Implement a Node.js backend Worker resource lifecycle change plus "
                "package-policy metadata.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "workflow-not-merely-schema-only": (
                "Analyze distributed workflow reconciliation; this is not merely a "
                "schema-only change.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-not-just-schema-only": (
                "Analyze distributed workflow reconciliation; this is not just "
                "schema-only work.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-not-limited-local-retry": (
                "Analyze cross-service workflow compensation; this is not limited to "
                "local retry only.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in selected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertIn(foundation, actual["layer3_skills"])
                self.assertLessEqual(len(actual["layer3_skills"]), 3)

    def test_phase_two_r02_scoped_effect_reviewer_cases(self) -> None:
        selected = {
            "filesystem-child-only": (
                "Implement a backend service child process contract change and no "
                "local filesystem mutation or path authority change.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-path-only": (
                "Implement path-containment behavior change while child-process "
                "behavior remains unchanged.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-durability-only": (
                "Implement filesystem durability behavior change without "
                "child-process work.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-timeout-only": (
                "Implement subprocess timeout behavior change without local file "
                "changes.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "filesystem-slash-mixed": (
                "Implement path-containment change / child-process behavior remains "
                "unchanged.",
                "backend-change-builder",
                "filesystem-process-safety",
            ),
            "workflow-negated-limited-retry": (
                "Analyze cross-service workflow compensation; this is not limited "
                "to local retry.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-negated-engine-only": (
                "Analyze distributed workflow repair; not merely engine mechanics "
                "only.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-negated-scheduler-only": (
                "Analyze active-workflow evolution; not just workflow engine "
                "scheduler mechanics.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-schema-adjacent": (
                "Analyze distributed workflow compensation plus a schema-only API "
                "update.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
            "workflow-engine-adjacent": (
                "Analyze cross-service reconciliation plus workflow-engine "
                "scheduler mechanics.",
                "data-middleware-change-builder",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in selected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertIn(foundation, actual["layer3_skills"])

        rejected = {
            "node-typescript-worker-adjacent": (
                "Implement a Node.js backend TypeScript-only Worker interface "
                "behavior change.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-browser-worker-adjacent": (
                "Implement a Node.js backend browser-only Worker lifecycle API "
                "change.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-package-esm-adjacent": (
                "Implement a Node.js backend package-policy ESM export metadata only.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "node-business-worker-adjacent": (
                "Implement a Node.js backend business-rule Worker allocation state "
                "only.",
                "backend-change-builder",
                "nodejs-runtime-professional-usage",
            ),
            "workflow-restricted-local-retry": (
                "Analyze cross-service workflow compensation restricted to local "
                "retries.",
                "engineering-change-analysis",
                "distributed-workflow-consistency",
            ),
        }
        for case_id, (prompt, owner, foundation) in rejected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(owner, actual["primary_skill"])
                self.assertNotIn(foundation, actual["layer3_skills"])

    def test_phase_two_r02_node_families_keep_changed_with_adjacent_scope(
        self,
    ) -> None:
        prompts = {
            "process-child-signal": (
                "Implement a Node.js backend child-process stdio shutdown behavior "
                "plus a business-rule update."
            ),
            "timer-cancellation": (
                "Implement a Node.js backend AbortSignal timer cancellation behavior "
                "plus a TypeScript type update."
            ),
            "module-runtime": (
                "Implement a Node.js backend ESM runtime flag behavior change plus "
                "package-policy metadata."
            ),
            "worker-resource": (
                "Implement a Node.js backend Worker resource ownership lifecycle "
                "change plus package-policy metadata."
            ),
            "stream-backpressure": (
                "Implement a Node.js backend stream backpressure completion behavior "
                "plus a business-rule update."
            ),
            "buffer-binary": (
                "Implement a Node.js backend Buffer encoding alias behavior change "
                "plus package-policy metadata."
            ),
            "event-loop-context": (
                "Implement a Node.js backend event-loop async-context fairness "
                "behavior change plus a business-rule update."
            ),
        }
        for family, prompt in prompts.items():
            with self.subTest(family=family):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual("backend-change-builder", actual["primary_skill"])
                self.assertIn(
                    "nodejs-runtime-professional-usage",
                    actual["layer3_skills"],
                )

    def test_phase_two_r02_node_policy_only_closed_grammar(self) -> None:
        rejected = {
            "package-esm-metadata": (
                "Implement a Node.js backend package-policy ESM export metadata "
                "change only."
            ),
            "build-commonjs-config": (
                "Implement a Node.js backend build-policy CommonJS export config "
                "change only."
            ),
            "package-entrypoint-manifest": (
                "Implement a Node.js backend package-policy entrypoint manifest "
                "change only."
            ),
        }
        for case_id, prompt in rejected.items():
            with self.subTest(case_id=case_id):
                records = ROUTE_ORACLE._node_runtime_effect_records(prompt)
                self.assertEqual(
                    ROUTE_ORACLE.EFFECT_ADJACENT_ONLY,
                    dict(ROUTE_ORACLE._effect_family_states(records))[
                        "module-runtime"
                    ],
                )
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual("backend-change-builder", actual["primary_skill"])
                self.assertNotIn(
                    "nodejs-runtime-professional-usage",
                    actual["layer3_skills"],
                )

        selected = {
            "esm-independent": (
                "Implement a Node.js backend ESM runtime resolution behavior change "
                "plus package-policy metadata update."
            ),
            "commonjs-independent": (
                "Implement a Node.js backend CommonJS runtime resolution behavior "
                "change plus build-policy config update."
            ),
            "entrypoint-independent": (
                "Implement a Node.js backend entrypoint runtime behavior change plus "
                "package-policy manifest update."
            ),
            "esm-same-scope": (
                "Implement a Node.js backend package-policy ESM runtime resolution "
                "behavior change with metadata change only."
            ),
            "commonjs-same-scope": (
                "Implement a Node.js backend build-policy CommonJS runtime behavior "
                "change with config change only."
            ),
            "entrypoint-same-scope": (
                "Implement a Node.js backend package-policy entrypoint runtime "
                "behavior change with manifest change only."
            ),
        }
        for case_id, prompt in selected.items():
            with self.subTest(case_id=case_id):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual("backend-change-builder", actual["primary_skill"])
                self.assertIn(
                    "nodejs-runtime-professional-usage",
                    actual["layer3_skills"],
                )

    def test_phase_two_r02_same_family_ambiguity_falls_back(self) -> None:
        prompts = {
            "filesystem-path": (
                "Implement a backend service path-containment behavior both changes "
                "and remains unchanged."
            ),
            "node-stream": (
                "Implement a Node.js backend stream backpressure behavior both "
                "changes and remains unchanged."
            ),
            "workflow-compensation": (
                "Analyze cross-service workflow compensation effect both changes and "
                "remains unchanged."
            ),
        }
        expected = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for family, prompt in prompts.items():
            with self.subTest(family=family):
                self.assertEqual(expected, _route(prompt, task_id=self._testMethodName))
                if family == "node-stream":
                    traced = _trace(prompt, task_id=self._testMethodName)
                    self.assertEqual(
                        "critical-unknown",
                        traced["winner_trace"]["selected_candidate"][
                            "candidate_id"
                        ],
                    )

    def test_phase_two_r02_scoped_effect_record_decision_table(self) -> None:
        self.assertEqual(
            (
                (0, "child process contract change"),
                (1, "no local filesystem mutation"),
                (2, "no path authority change"),
            ),
            ROUTE_ORACLE._bounded_effect_scopes(
                "Child-process contract change and no local filesystem mutation "
                "or path authority change."
            ),
        )

        filesystem_prompts = {
            "create": "local file create behavior change",
            "replace": "local file replacement behavior change",
            "durability": "filesystem durability behavior change",
            "protection": "file protection behavior change",
            "path": "path containment behavior change",
            "link": "filesystem link behavior change",
            "cleanup": "temporary file cleanup behavior change",
        }
        for decision, prompt in filesystem_prompts.items():
            with self.subTest(filesystem_decision=decision):
                records = ROUTE_ORACLE._filesystem_process_effect_records(prompt)
                self.assertEqual(
                    ROUTE_ORACLE.EFFECT_CHANGED,
                    dict(ROUTE_ORACLE._effect_family_states(records))[
                        "filesystem-path"
                    ],
                )

        process_prompts = {
            "executable": "child-process executable selection change",
            "argv": "child-process argv behavior change",
            "environment": "child-process environment behavior change",
            "cwd": "subprocess cwd behavior change",
            "stdio": "child-process stdio behavior change",
            "exit": "subprocess exit behavior change",
            "timeout": "subprocess timeout behavior change",
            "cancel": "subprocess cancellation behavior change",
            "descendant": "child-process descendant behavior change",
            "result": "subprocess result behavior change",
            "lifecycle": "subprocess lifecycle behavior change",
            "behavior": "child-process behavior change",
            "contract": "child-process contract change",
        }
        for decision, prompt in process_prompts.items():
            with self.subTest(process_decision=decision):
                records = ROUTE_ORACLE._filesystem_process_effect_records(prompt)
                self.assertEqual(
                    ROUTE_ORACLE.EFFECT_CHANGED,
                    dict(ROUTE_ORACLE._effect_family_states(records))[
                        "child-process"
                    ],
                )

        node_prompts = {
            "process-child-signal": (
                "Node.js child-process stdio shutdown behavior plus business-rule "
                "metadata."
            ),
            "timer-cancellation": (
                "Node.js AbortSignal timer cancellation behavior plus TypeScript "
                "metadata."
            ),
            "module-runtime": (
                "Node.js ESM runtime flag behavior change plus package metadata."
            ),
            "worker-resource": (
                "Node.js Worker resource lifecycle change plus package metadata."
            ),
            "stream-backpressure": (
                "Node.js stream backpressure completion behavior plus business "
                "metadata."
            ),
            "buffer-binary": (
                "Node.js Buffer encoding alias behavior change plus package metadata."
            ),
            "event-loop-context": (
                "Node.js event-loop async-context fairness behavior change plus "
                "business metadata."
            ),
        }
        for family, prompt in node_prompts.items():
            with self.subTest(node_family=family):
                states = dict(
                    ROUTE_ORACLE._effect_family_states(
                        ROUTE_ORACLE._node_runtime_effect_records(prompt)
                    )
                )
                self.assertEqual(ROUTE_ORACLE.EFFECT_CHANGED, states[family])

        node_adjacent = {
            "worker-typescript": (
                "worker-resource",
                "Node.js TypeScript-only Worker interface behavior change.",
            ),
            "worker-browser": (
                "worker-resource",
                "Node.js browser-only Worker lifecycle API change.",
            ),
            "module-package": (
                "module-runtime",
                "Node.js package-policy ESM export metadata only.",
            ),
            "worker-business": (
                "worker-resource",
                "Node.js business-rule Worker allocation state only.",
            ),
        }
        for case_id, (family, prompt) in node_adjacent.items():
            with self.subTest(node_adjacent=case_id):
                states = dict(
                    ROUTE_ORACLE._effect_family_states(
                        ROUTE_ORACLE._node_runtime_effect_records(prompt)
                    )
                )
                self.assertEqual(ROUTE_ORACLE.EFFECT_ADJACENT_ONLY, states[family])

        unchanged_states = dict(
            ROUTE_ORACLE._effect_family_states(
                ROUTE_ORACLE._node_runtime_effect_records(
                    "Node.js runtime and core-library behavior remains unchanged."
                )
            )
        )
        self.assertEqual(7, len(unchanged_states))
        self.assertEqual(
            {ROUTE_ORACLE.EFFECT_UNCHANGED},
            set(unchanged_states.values()),
        )

        distributed_cases = {
            "changed": (
                ROUTE_ORACLE.EFFECT_CHANGED,
                "cross-service workflow compensation",
            ),
            "limited": (
                ROUTE_ORACLE.EFFECT_ADJACENT_ONLY,
                "cross-service workflow compensation restricted to local retries",
            ),
            "local-only": (
                ROUTE_ORACLE.EFFECT_ADJACENT_ONLY,
                "local retry compensation against participant facts",
            ),
            "negated-limit": (
                ROUTE_ORACLE.EFFECT_CHANGED,
                "cross-service workflow compensation not limited to local retry",
            ),
        }
        for case_id, (expected, prompt) in distributed_cases.items():
            with self.subTest(distributed=case_id):
                records = ROUTE_ORACLE._distributed_workflow_effect_records(prompt)
                self.assertEqual(
                    expected,
                    dict(ROUTE_ORACLE._effect_family_states(records))[
                        "distributed-workflow"
                    ],
                )

        self.assertEqual(
            (("example", ROUTE_ORACLE.EFFECT_AMBIGUOUS),),
            ROUTE_ORACLE._effect_family_states(
                (
                    ("example", ROUTE_ORACLE.EFFECT_CHANGED, 7),
                    ("example", ROUTE_ORACLE.EFFECT_UNCHANGED, 7),
                )
            ),
        )
        self.assertEqual(
            (("example", ROUTE_ORACLE.EFFECT_CHANGED),),
            ROUTE_ORACLE._effect_family_states(
                (
                    ("example", ROUTE_ORACLE.EFFECT_CHANGED, 7),
                    ("example", ROUTE_ORACLE.EFFECT_UNCHANGED, 8),
                )
            ),
        )

    def test_backend_companion_overflow_falls_back_without_truncation(self) -> None:
        prompt = (
            "Implement a Node.js backend service stream pipeline that atomically "
            "replaces a local file and includes Kotlin coroutine code plus C# "
            "CancellationToken async disposal behavior."
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            _route(prompt, task_id=self._testMethodName),
        )
        traced = _trace(prompt, task_id=self._testMethodName)
        selected = traced["winner_trace"]["selected_candidate"]
        self.assertEqual("foundation-layer3-overflow", selected["candidate_id"])
        self.assertEqual(
            ["foundation-layer3-overflow"],
            selected["evidence"],
        )
        self.assertEqual(
            sorted(
                [
                    "nodejs-runtime-professional-usage",
                    "filesystem-process-safety",
                    "kotlin-professional-usage",
                    "csharp-dotnet-professional-usage",
                ]
            ),
            selected["eligible_layer3_skills"],
        )
        self.assertEqual(
            4,
            len(selected["eligible_layer3_skills"]),
        )

        routing = load_yaml_file(ROOT / "evals/routing/cases.yaml")
        cases = routing.get("cases") if isinstance(routing, dict) else None
        self.assertIsInstance(cases, list)
        for case in cases:
            with self.subTest(case_id=case.get("id")):
                actual = _route(
                    str(case.get("prompt", "")),
                    task_id=str(case.get("id")),
                )
                self.assertLessEqual(len(actual["layer3_skills"]), 3)

        invalid_overflow_sets = {
            "corrupt": [None, "filesystem-process-safety"],
            "duplicate": [
                "nodejs-runtime-professional-usage",
                "filesystem-process-safety",
                "kotlin-professional-usage",
                "kotlin-professional-usage",
            ],
            "stale": [
                "nodejs-runtime-professional-usage",
                "filesystem-process-safety",
                "kotlin-professional-usage",
                "stale-foundation-layer3",
            ],
            "unauthorized": [
                "nodejs-runtime-professional-usage",
                "filesystem-process-safety",
                "kotlin-professional-usage",
                "web-platform-professional-usage",
            ],
        }
        for case_id, layer3 in invalid_overflow_sets.items():
            with self.subTest(integrity_mutation=case_id):
                with mock.patch.object(
                    ROUTE_ORACLE,
                    "_implementation_owner_layer3",
                    return_value=layer3,
                ), self.assertRaises(
                    ROUTE_ORACLE.RoutingIntegrityError
                ):
                    ROUTE_ORACLE.route(
                        "Implement an accepted backend service behavior change.",
                        main_execution=_main_execution(
                            f"{self._testMethodName}:{case_id}"
                        ),
                    )

    def test_node_raw_token_without_closed_family_effect_does_not_load(
        self,
    ) -> None:
        observed = _route(
            "Implement a Node.js backend endpoint with a raw runtime token label.",
            task_id=self._testMethodName,
        )
        self.assertEqual(
            "backend-change-builder",
            observed["primary_skill"],
        )
        self.assertNotIn(
            "nodejs-runtime-professional-usage",
            observed["layer3_skills"],
        )

    def test_actual_diff_review_intent_precedes_semantic_analysis(self) -> None:
        prompts = {
            "tenant": (
                "Review the actual diff for tenant isolation across storage, cache, "
                "queue, and administrative paths."
            ),
            "cryptography": (
                "Review the actual diff for a cryptographic construction and key "
                "lifecycle nonce policy change."
            ),
            "audit": (
                "Review the actual diff for audit evidence integrity and tamper "
                "verification changes."
            ),
        }
        generic_expected = {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "ai-code-review-refactor",
            "layer3_skills": ["code-review"],
            "review_skill": "ai-code-review-refactor",
        }
        for case_id, prompt in prompts.items():
            with self.subTest(case_id=case_id):
                expected = (
                    {
                        "path": "direct",
                        "profile": "review-agent",
                        "primary_skill": "security-privacy-gate",
                        "layer3_skills": ["audit-evidence-integrity"],
                        "review_skill": "security-privacy-gate",
                    }
                    if case_id == "audit"
                    else generic_expected
                )
                self.assertEqual(expected, _route(prompt, task_id=self._testMethodName))

        tenant_boundary = _route(
            "Review the actual diff for an existing reachable tenant "
            "authorization boundary with object permission enforcement and "
            "tenant isolation changes.",
            task_id=self._testMethodName,
        )
        self.assertEqual(
            {
                "path": "direct",
                "profile": "review-agent",
                "primary_skill": "security-privacy-gate",
                "layer3_skills": [
                    "permission-boundary-modeling",
                    "threat-modeling",
                    "tenant-isolation",
                ],
                "review_skill": "security-privacy-gate",
            },
            tenant_boundary,
        )

    def test_capability_matrix_is_required_and_covers_the_declared_space(self) -> None:
        case_id = "capcov-matrix-required"
        matrix_path = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        if not matrix_path.is_file():
            self.fail(
                f"[{case_id}] expected file=evals/capability-coverage/matrix.yaml; "
                "actual=missing"
            )
        matrix = load_yaml_file(matrix_path)
        entries = matrix.get("entries") if isinstance(matrix, dict) else None
        errors: list[str] = []
        if not isinstance(entries, list):
            errors.append(f"[{case_id}] expected entries=list; actual={type(entries).__name__}")
        else:
            required_fields = {
                "surface",
                "task_type",
                "language_runtime",
                "cross_cutting_risks",
                "expected_professional_owner",
                "expected_domain_extensions",
                "expected_foundation_skills",
                "coverage_status",
                "evidence_fixtures",
            }
            allowed_status = {
                "covered",
                "partial",
                "missing",
                "intentionally-unsupported",
            }
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    errors.append(
                        f"[{case_id}] expected entries[{index}]=mapping; "
                        f"actual={type(entry).__name__}"
                    )
                    continue
                missing = sorted(required_fields - set(entry))
                if missing:
                    errors.append(
                        f"[{case_id}] expected entries[{index}].fields="
                        f"{json.dumps(sorted(required_fields))}; actual=missing:{','.join(missing)}"
                    )
                status = entry.get("coverage_status")
                if status not in allowed_status:
                    errors.append(
                        f"[{case_id}] expected entries[{index}].coverage_status="
                        f"{json.dumps(sorted(allowed_status))}; actual={json.dumps(status)}"
                    )
                if status == "intentionally-unsupported" and not str(
                    entry.get("reason", "")
                ).strip():
                    errors.append(
                        f"[{case_id}] expected entries[{index}].reason=non-empty; "
                        "actual=missing"
                    )
                if status == "missing" and not str(
                    entry.get("disposition", "")
                ).strip():
                    errors.append(
                        f"[{case_id}] expected entries[{index}].disposition="
                        "non-empty; actual=missing"
                    )
                evidence = entry.get("evidence_fixtures")
                if not isinstance(evidence, list) or not evidence:
                    errors.append(
                        f"[{case_id}] expected entries[{index}].evidence_fixtures="
                        "non-empty-list; actual=missing-or-empty"
                    )

            def flattened(field: str) -> set[str]:
                values: set[str] = set()
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    raw = entry.get(field)
                    if isinstance(raw, list):
                        values.update(str(item).strip() for item in raw)
                    elif isinstance(raw, str):
                        values.add(raw.strip())
                return values

            required_tasks = {
                "requirement intake",
                "repository analysis",
                "diagnosis",
                "architecture design",
                "task planning",
                "web implementation",
                "installed client implementation",
                "backend implementation",
                "data platform implementation",
                "infrastructure implementation",
                "integration implementation",
                "developer tooling implementation",
                "testing",
                "security review",
                "reliability review",
                "implementation review",
                "release",
                "rollback",
                "incident response",
                "documentation",
            }
            required_surfaces = {
                "Web browser",
                "PWA",
                "Android",
                "Android TV",
                "Wear OS",
                "Android Automotive",
                "iOS",
                "iPadOS",
                "watchOS",
                "tvOS",
                "visionOS",
                "macOS",
                "Mac Catalyst",
                "Windows desktop",
                "Windows service",
                "Linux desktop",
                "Linux server",
                "CLI",
                "TUI",
                "daemon",
                "container",
                "Kubernetes",
                "cloud platform",
                "serverless",
                "edge runtime",
                "browser extension",
                "embedded device",
                "firmware",
                "RTOS",
                "kernel",
                "driver",
                "cross-platform client",
                "AI product",
                "machine learning system",
                "big data",
                "SaaS",
                "multitenancy",
                "payments",
                "trading",
                "commerce",
                "marketplace",
                "Web3",
                "enterprise identity",
                "collaboration",
                "realtime communication",
                "media processing",
                "gaming",
                "XR",
                "IoT",
                "embedded",
                "automotive",
                "industrial automation",
                "healthcare",
                "telecom",
                "geospatial",
            }
            required_languages = {
                "C",
                "C++",
                "Rust",
                "Go",
                "Java",
                "JVM",
                "Kotlin",
                "Swift",
                "Objective-C",
                "C#",
                ".NET",
                "JavaScript",
                "TypeScript",
                "Node.js",
                "Python",
                "Shell",
                "PowerShell",
                "SQL",
                "Dart",
                "PHP",
                "Ruby",
                "Scala",
            }
            required_risks = {
                "lifecycle",
                "process termination",
                "state restoration",
                "offline behavior",
                "sync conflict",
                "accessibility",
                "privacy",
                "local data security",
                "permissions",
                "authentication",
                "authorization",
                "tenant isolation",
                "cryptography",
                "key lifecycle",
                "audit evidence",
                "concurrency",
                "distributed consistency",
                "retry",
                "idempotency",
                "migration",
                "backward compatibility",
                "packaging",
                "signing",
                "installation",
                "update",
                "rollback",
                "performance",
                "capacity",
                "resilience",
                "observability",
                "testing",
                "release",
                "infrastructure as code",
            }
            for field, required in (
                ("task_type", required_tasks),
                ("surface", required_surfaces),
                ("language_runtime", required_languages),
                ("cross_cutting_risks", required_risks),
            ):
                missing_values = sorted(required - flattened(field))
                if missing_values:
                    errors.append(
                        f"[{case_id}] expected {field}.coverage="
                        f"{json.dumps(sorted(required), ensure_ascii=False)}; "
                        f"actual=missing:{json.dumps(missing_values, ensure_ascii=False)}"
                    )
        if errors:
            self.fail("\n".join(errors))

    def test_t16_matrix_inventory_status_language_and_phase_two_contract(
        self,
    ) -> None:
        case_id = "capcov-t16-matrix-inventory-contract"
        matrix = load_yaml_file(
            ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        )
        entries = matrix.get("entries") if isinstance(matrix, dict) else None
        if not isinstance(entries, list):
            self.fail(
                f"[{case_id}] expected entries=list; "
                f"actual={type(entries).__name__}"
            )
        rows = [entry for entry in entries if isinstance(entry, dict)]
        ids = [entry.get("id") for entry in rows]
        by_id = {
            entry["id"]: entry
            for entry in rows
            if isinstance(entry.get("id"), str)
        }
        errors: list[str] = []
        if len(entries) != 125:
            errors.append(
                f"[{case_id}] expected entry_count=125; actual={len(entries)}"
            )
        if len(rows) != len(entries):
            errors.append(
                f"[{case_id}] expected every_entry=mapping; "
                f"actual mappings={len(rows)}"
            )
        if len(ids) != len(set(ids)):
            duplicates = sorted(
                str(item) for item in set(ids) if ids.count(item) > 1
            )
            errors.append(
                f"[{case_id}] expected unique_entry_ids=124; "
                f"actual duplicates={json.dumps(duplicates)}"
            )

        expected_status_counts = {
            "covered": 81,
            "partial": 39,
            "missing": 0,
            "intentionally-unsupported": 5,
        }
        actual_status_counts = {
            status: sum(
                entry.get("coverage_status") == status for entry in rows
            )
            for status in expected_status_counts
        }
        if actual_status_counts != expected_status_counts:
            errors.append(
                f"[{case_id}] expected status_counts="
                f"{json.dumps(expected_status_counts, sort_keys=True)}; "
                f"actual={json.dumps(actual_status_counts, sort_keys=True)}"
            )

        required_space = (
            matrix.get("required_space") if isinstance(matrix, dict) else None
        )
        if not isinstance(required_space, dict):
            errors.append(
                f"[{case_id}] expected required_space=mapping; "
                f"actual={type(required_space).__name__}"
            )
        else:
            projection_contract = {
                "engineering_tasks": (
                    "engineering-task",
                    "task_type",
                    20,
                ),
                "platforms": ("platform", "surface", 32),
                "language_runtimes": (
                    "language-runtime",
                    "language_runtime",
                    22,
                ),
                "cross_cutting_risks": (
                    "cross-cutting-risk",
                    "cross_cutting_risks",
                    33,
                ),
                "product_domains": ("product-domain", "surface", 23),
                "routing_combinations": (
                    "routing-combination",
                    "id",
                    20,
                ),
            }
            if set(required_space) != set(projection_contract):
                errors.append(
                    f"[{case_id}] expected required_space.fields="
                    f"{json.dumps(sorted(projection_contract))}; "
                    f"actual={json.dumps(sorted(required_space))}"
                )
            for field, (
                axis,
                entry_field,
                expected_count,
            ) in projection_contract.items():
                declared = required_space.get(field)
                if not isinstance(declared, list):
                    errors.append(
                        f"[{case_id}] expected required_space.{field}=list; "
                        f"actual={type(declared).__name__}"
                    )
                    continue
                projected: list[object] = []
                for entry in rows:
                    if entry.get("axis") != axis:
                        continue
                    value = entry.get(entry_field)
                    if isinstance(value, list):
                        projected.extend(value)
                    else:
                        projected.append(value)
                if len(declared) != expected_count:
                    errors.append(
                        f"[{case_id}] expected required_space.{field}.count="
                        f"{expected_count}; actual={len(declared)}"
                    )
                if len(declared) != len(set(declared)):
                    errors.append(
                        f"[{case_id}] expected required_space.{field}=unique; "
                        f"actual={json.dumps(declared, ensure_ascii=False)}"
                    )
                if set(declared) != set(projected):
                    errors.append(
                        f"[{case_id}] expected required_space.{field}="
                        "exact-entry-projection; "
                        f"actual declared_only="
                        f"{json.dumps(sorted(set(declared) - set(projected)), ensure_ascii=False)} "
                        f"entry_only="
                        f"{json.dumps(sorted(set(projected) - set(declared)), ensure_ascii=False)}"
                    )
            expected_route_rows = [
                "route-react-web",
                "route-android-installed-client",
                "route-android-installed-client-accessibility",
                "route-ios-installed-client",
                "route-windows-installed-client",
                "route-macos-installed-client",
                "route-linux-installed-client",
                "route-flutter-android-ios",
                "route-electron-windows",
                "route-terraform-source",
                "route-terraform-production-apply",
                "route-ordinary-android-no-mobile-bridge",
                "route-ordinary-ios-no-mobile-bridge",
                "route-cross-platform-alone-rejected",
                "route-unknown-target-analysis-first",
                "route-web-installed-zero-conflict",
                "route-backend-installed-zero-conflict",
                "route-infrastructure-release-zero-conflict",
                "route-platform-professional-zero-conflict",
                "route-language-domain-zero-conflict",
            ]
            if required_space.get("routing_combinations") != expected_route_rows:
                errors.append(
                    f"[{case_id}] expected required_space.routing_combinations="
                    f"{json.dumps(expected_route_rows)}; "
                    f"actual={json.dumps(required_space.get('routing_combinations'))}"
                )

        retired_id = "language-kotlin-swift-csharp-dotnet-powershell"
        if retired_id in by_id:
            errors.append(
                f"[{case_id}] expected retired_id={retired_id}=absent; "
                "actual=present"
            )
        language_contract = {
            "language-kotlin": {
                "language_runtime": ["Kotlin"],
                "expected_professional_owner": "backend-change-builder",
                "expected_foundation_skills": [
                    "kotlin-professional-usage"
                ],
            },
            "language-swift": {
                "language_runtime": ["Swift"],
                "expected_professional_owner": (
                    "installed-client-change-builder"
                ),
                "expected_foundation_skills": [
                    "swift-professional-usage"
                ],
            },
            "language-csharp-dotnet": {
                "language_runtime": ["C#", ".NET"],
                "expected_professional_owner": "backend-change-builder",
                "expected_foundation_skills": [
                    "csharp-dotnet-professional-usage"
                ],
            },
            "language-powershell": {
                "language_runtime": ["PowerShell"],
                "expected_professional_owner": (
                    "platform-infrastructure-change-builder"
                ),
                "expected_foundation_skills": [
                    "powershell-professional-usage"
                ],
            },
        }
        for entry_id, expected in language_contract.items():
            entry = by_id.get(entry_id)
            if entry is None:
                errors.append(
                    f"[{case_id}] expected {entry_id}=present; actual=missing"
                )
                continue
            expected_fields = expected | {
                "axis": "language-runtime",
                "expected_domain_extensions": [],
                "coverage_status": "covered",
                "disposition": "retain-existing",
            }
            for field, expected_value in expected_fields.items():
                if entry.get(field) != expected_value:
                    errors.append(
                        f"[{case_id}] expected {entry_id}.{field}="
                        f"{json.dumps(expected_value)}; "
                        f"actual={json.dumps(entry.get(field))}"
                    )

        partial_rows = [
            entry
            for entry in rows
            if entry.get("coverage_status") == "partial"
        ]
        invalid_partial = {
            str(entry.get("id")): {
                "disposition": entry.get("disposition"),
                "reason": entry.get("reason"),
            }
            for entry in partial_rows
            if entry.get("disposition") != "retain-partial"
            or not str(entry.get("reason", "")).startswith("Gap:")
        }
        partial_reasons = [str(entry.get("reason", "")) for entry in partial_rows]
        if len(partial_rows) != 39 or invalid_partial:
            errors.append(
                f"[{case_id}] expected partial_rows=39 with explicit "
                "terminal retain-partial Gap treatment; "
                f"actual count={len(partial_rows)} invalid="
                f"{json.dumps(invalid_partial, sort_keys=True)}"
            )
        if len(partial_reasons) != len(set(partial_reasons)):
            errors.append(
                f"[{case_id}] expected every partial reason to be distinct; "
                f"actual={json.dumps(partial_reasons)}"
            )
        transitional_dispositions = sorted(
            str(entry.get("id"))
            for entry in rows
            if entry.get("disposition") == "evaluate-phase-2"
        )
        if transitional_dispositions:
            errors.append(
                f"[{case_id}] expected evaluate-phase-2 disposition to be absent; "
                f"actual={json.dumps(transitional_dispositions)}"
            )
        if errors:
            self.fail("\n".join(errors))

    def test_t16_matrix_composition_and_stale_reason_contract(self) -> None:
        case_id = "capcov-t16-matrix-composition-contract"
        matrix = load_yaml_file(
            ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        )
        entries = matrix.get("entries") if isinstance(matrix, dict) else None
        if not isinstance(entries, list):
            self.fail(
                f"[{case_id}] expected entries=list; "
                f"actual={type(entries).__name__}"
            )
        by_id = {
            entry.get("id"): entry
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("id"), str)
        }
        errors: list[str] = []
        over_limit: dict[str, int] = {}
        for entry_id, entry in by_id.items():
            domains = entry.get("expected_domain_extensions")
            foundations = entry.get("expected_foundation_skills")
            if isinstance(domains, list) and isinstance(foundations, list):
                total = len(domains) + len(foundations)
                if total > 3:
                    over_limit[entry_id] = total
        if over_limit:
            errors.append(
                f"[{case_id}] expected every_entry.expected_layer3_count<=3; "
                f"actual={json.dumps(over_limit, sort_keys=True)}"
            )
        with tempfile.TemporaryDirectory(
            prefix="capcov-t16-layer3-budget-"
        ) as raw:
            temp_root = Path(raw)
            over_budget_matrix = _minimal_valid_matrix()
            over_budget_matrix["entries"][0][
                "expected_domain_extensions"
            ] = ["android-platform-extension", "ios-ipados-platform-extension"]
            over_budget_matrix["entries"][0][
                "expected_foundation_skills"
            ] = ["client-lifecycle-state-restoration", "client-application-testing"]
            over_budget_path = _write_matrix_fixture(
                temp_root,
                over_budget_matrix,
                name="over-budget.yaml",
            )
            first_errors = validate_capability_coverage(
                over_budget_path,
                root=temp_root,
            )
            second_errors = validate_capability_coverage(
                over_budget_path,
                root=temp_root,
            )
            folded_errors = " ".join(first_errors).casefold()
            if (
                first_errors != second_errors
                or "entries[0]" not in folded_errors
                or "at most 3" not in folded_errors
                or "total=4" not in folded_errors
            ):
                errors.append(
                    f"[{case_id}] expected deterministic validator rejection "
                    "for one four-Skill JIT projection; "
                    f"actual={json.dumps([first_errors, second_errors])}"
                )

            transitional_matrix = _minimal_valid_matrix()
            transitional_matrix["entries"][0][
                "disposition"
            ] = "evaluate-phase-2"
            transitional_path = _write_matrix_fixture(
                temp_root,
                transitional_matrix,
                name="transitional-disposition.yaml",
            )
            transitional_errors = validate_capability_coverage(
                transitional_path,
                root=temp_root,
            )
            if (
                not transitional_errors
                or "disposition" not in " ".join(transitional_errors).casefold()
                or "retain-partial" not in " ".join(transitional_errors)
            ):
                errors.append(
                    f"[{case_id}] expected evaluate-phase-2 disposition to fail closed; "
                    f"actual={json.dumps(transitional_errors)}"
                )

            admission_matrix = _minimal_valid_matrix()
            admission_id = (
                "capcov-admission-foundation-accessibility-decision"
            )
            _set_first_entry_covered(admission_matrix, [admission_id])
            admission_path = _write_matrix_fixture(
                temp_root,
                admission_matrix,
                name="admission-evidence.yaml",
            )
            admission_catalog = {
                admission_id: (
                    "evals/capability-coverage/admission-cases.yaml:cases[64]",
                ),
            }
            admission_errors = validate_capability_coverage(
                admission_path,
                root=ROOT,
                evidence_ids=admission_catalog,
                passing_evidence_ids=set(),
            )
            if admission_errors != []:
                errors.append(
                    f"[{case_id}] expected current passing admission evidence "
                    "to be accepted by the authoritative admission evaluator; "
                    f"actual={json.dumps(admission_errors)}"
                )

            forged_id = "capcov-admission-forged-not-in-fixture"
            forged_matrix = _minimal_valid_matrix()
            _set_first_entry_covered(forged_matrix, [forged_id])
            forged_path = _write_matrix_fixture(
                temp_root,
                forged_matrix,
                name="forged-admission-evidence.yaml",
            )
            forged_errors = validate_capability_coverage(
                forged_path,
                root=ROOT,
                evidence_ids={
                    forged_id: (
                        "evals/capability-coverage/admission-cases.yaml:"
                        "cases[999]",
                    ),
                },
                passing_evidence_ids=set(),
            )
            if (
                not forged_errors
                or forged_id not in " ".join(forged_errors)
                or "not passing" not in " ".join(forged_errors).casefold()
            ):
                errors.append(
                    f"[{case_id}] expected forged admission evidence to fail "
                    "closed against the fixture/evaluator closed set; "
                    f"actual={json.dumps(forged_errors)}"
                )

            route_id = "capcov-route-react-web-owner"
            route_matrix = _minimal_valid_matrix()
            _set_first_entry_covered(route_matrix, [route_id])
            route_path = _write_matrix_fixture(
                temp_root,
                route_matrix,
                name="non-passing-route-evidence.yaml",
            )
            route_errors = validate_capability_coverage(
                route_path,
                root=ROOT,
                evidence_ids={
                    route_id: (
                        "evals/routing/capability-coverage-cases.yaml:cases[0]",
                    ),
                },
                passing_evidence_ids=set(),
            )
            if (
                not route_errors
                or route_id not in " ".join(route_errors)
                or "not passing" not in " ".join(route_errors).casefold()
            ):
                errors.append(
                    f"[{case_id}] expected non-passing route evidence to fail "
                    "closed against current route results; "
                    f"actual={json.dumps(route_errors)}"
                )

        row_contract = {
            "task-installed-client-implementation": {
                "expected_domain_extensions": [],
            },
            "task-infrastructure-implementation": {
                "expected_domain_extensions": [],
            },
            "risk-infrastructure-as-code": {
                "expected_domain_extensions": [],
            },
            "risk-client-local-data-security": {
                "expected_domain_extensions": [],
            },
            "platform-pwa": {
                "expected_domain_extensions": [],
                "expected_foundation_skills": [
                    "web-platform-professional-usage"
                ],
            },
            "platform-mac-catalyst": {
                "expected_domain_extensions": [
                    "macos-platform-extension"
                ],
                "expected_foundation_skills": [
                    "swift-professional-usage"
                ],
            },
            "risk-accessibility": {
                "expected_professional_owner": "frontend-change-builder",
                "expected_domain_extensions": [],
                "expected_foundation_skills": [
                    "accessibility-inclusive-design"
                ],
                "evidence_fixtures": [
                    "capcov-admission-foundation-accessibility-decision"
                ],
            },
        }
        for entry_id, expected_fields in row_contract.items():
            entry = by_id.get(entry_id)
            if entry is None:
                errors.append(
                    f"[{case_id}] expected {entry_id}=present; actual=missing"
                )
                continue
            for field, expected_value in expected_fields.items():
                if entry.get(field) != expected_value:
                    errors.append(
                        f"[{case_id}] expected {entry_id}.{field}="
                        f"{json.dumps(expected_value)}; "
                        f"actual={json.dumps(entry.get(field))}"
                    )

        container_reason = str(
            by_id.get("platform-container", {}).get("reason", "")
        ).casefold()
        if (
            any(
                token not in container_reason
                for token in ("source", "runtime", "owner")
            )
            or not any(
                state in container_reason
                for state in (
                    "unstable",
                    "not stable",
                    "lacks a stable",
                    "not yet stable",
                )
            )
            or "await the infrastructure builder" in container_reason
        ):
            errors.append(
                f"[{case_id}] expected platform-container.reason to name "
                "the remaining unstable source/runtime owner without the "
                "obsolete infrastructure-builder gap; "
                f"actual={json.dumps(container_reason)}"
            )

        packaging_reason = str(
            by_id.get("risk-packaging-distribution", {}).get("reason", "")
        ).casefold()
        required_packaging_terms = {
            "android",
            "ios",
            "ipados",
            "windows",
            "macos",
            "linux",
            "domain",
            "package",
            "sign",
            "repair",
            "uninstall",
            "store",
            "direct-update",
        }
        missing_packaging_terms = sorted(
            token
            for token in required_packaging_terms
            if token not in packaging_reason
        )
        if (
            missing_packaging_terms
            or "depends on phase-one platform extensions" in packaging_reason
        ):
            errors.append(
                f"[{case_id}] expected risk-packaging-distribution.reason "
                "to retain the special-platform/end-to-end gap after naming "
                "the five existing platform Domains; "
                f"actual missing={json.dumps(missing_packaging_terms)} "
                f"reason={json.dumps(packaging_reason)}"
            )
        stale_reason_tokens = (
            "planned base",
            "need phase-two",
            "phase-two evaluation",
            "phase-two evidence",
        )
        stale_reasons = {
            entry_id: entry.get("reason")
            for entry_id, entry in by_id.items()
            if entry.get("coverage_status") == "partial"
            and any(
                token in str(entry.get("reason", "")).casefold()
                for token in stale_reason_tokens
            )
        }
        if stale_reasons:
            errors.append(
                f"[{case_id}] expected terminal partial reasons without transitional wording; "
                f"actual={json.dumps(stale_reasons, sort_keys=True)}"
            )
        terminal_reason_contract = {
            "platform-android-tv": (
                "tv-specific",
                "platform contract",
                "evidence boundary",
            ),
            "platform-serverless": (
                "unresolved provider-semantics contract",
            ),
            "platform-edge-runtime": (
                "unresolved edge execution contract",
            ),
            "domain-commerce": (
                "unadmitted commerce-domain contract",
            ),
        }
        for entry_id, required_phrases in terminal_reason_contract.items():
            reason = str(by_id.get(entry_id, {}).get("reason", "")).casefold()
            missing = [
                phrase for phrase in required_phrases if phrase not in reason
            ]
            if missing:
                errors.append(
                    f"[{case_id}] expected {entry_id}.reason terminal contract "
                    f"phrases={json.dumps(required_phrases)}; "
                    f"actual missing={json.dumps(missing)} reason={json.dumps(reason)}"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_t16_unsupported_rows_use_exact_quoted_gap_contract(self) -> None:
        case_id = "capcov-t16-unsupported-gap-contract"
        matrix_path = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        matrix_text = matrix_path.read_text(encoding="utf-8")
        matrix = load_yaml_file(matrix_path)
        entries = matrix.get("entries") if isinstance(matrix, dict) else None
        if not isinstance(entries, list):
            self.fail(
                f"[{case_id}] expected entries=list; "
                f"actual={type(entries).__name__}"
            )
        unsupported = {
            str(entry.get("id")): entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("coverage_status") == "intentionally-unsupported"
        }
        expected_ids = {
            "domain-automotive",
            "domain-industrial-automation",
            "domain-healthcare",
            "domain-telecom",
            "domain-geospatial",
        }
        errors: list[str] = []
        if set(unsupported) != expected_ids:
            errors.append(
                f"[{case_id}] expected unsupported_ids="
                f"{json.dumps(sorted(expected_ids))}; "
                f"actual={json.dumps(sorted(unsupported))}"
            )
        quoted_gap_pattern = re.compile(
            r"evidence_fixtures:\s*\[\s*"
            r"([\"'])gap:official-primary-source\1\s*,\s*"
            r"([\"'])gap:qualified-reviewer\2\s*\]"
        )
        for entry_id in sorted(expected_ids):
            entry = unsupported.get(entry_id)
            if entry is None:
                continue
            if entry.get("expected_professional_owner") is not None:
                errors.append(
                    f"[{case_id}] expected {entry_id}.owner=null; "
                    f"actual={json.dumps(entry.get('expected_professional_owner'))}"
                )
            for field in (
                "expected_domain_extensions",
                "expected_foundation_skills",
            ):
                if entry.get(field) != []:
                    errors.append(
                        f"[{case_id}] expected {entry_id}.{field}=[]; "
                        f"actual={json.dumps(entry.get(field))}"
                    )
            expected_gaps = [
                "gap:official-primary-source",
                "gap:qualified-reviewer",
            ]
            if entry.get("evidence_fixtures") != expected_gaps:
                errors.append(
                    f"[{case_id}] expected {entry_id}.evidence_fixtures="
                    f"{json.dumps(expected_gaps)}; "
                    f"actual={json.dumps(entry.get('evidence_fixtures'))}"
                )
            reason = " ".join(
                str(entry.get("reason", "")).casefold().split()
            )
            source_gap = re.search(
                r"reliable official or primary source contract evidence "
                r"is (?:missing|unavailable)",
                reason,
            )
            reviewer_gap = re.search(
                r"qualified(?: [a-z]+)* reviewer evidence "
                r"is (?:missing|unavailable)",
                reason,
            )
            if source_gap is None or reviewer_gap is None:
                errors.append(
                    f"[{case_id}] expected {entry_id}.reason to name both "
                    "primary-source and qualified-reviewer gaps; "
                    f"actual={json.dumps(entry.get('reason'))}"
                )

            marker = f"  - id: {entry_id}\n"
            start = matrix_text.find(marker)
            end = (
                matrix_text.find("\n  - id: ", start + len(marker))
                if start >= 0
                else -1
            )
            block = (
                matrix_text[start:]
                if start >= 0 and end < 0
                else matrix_text[start:end]
                if start >= 0
                else ""
            )
            if quoted_gap_pattern.search(block) is None:
                errors.append(
                    f"[{case_id}] expected {entry_id}.gap_tokens="
                    "explicitly-quoted-exact-strings; actual=unquoted-or-missing"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_t16_capability_routes_and_conflict_evidence_are_closed(
        self,
    ) -> None:
        case_id = "capcov-t16-route-evidence-contract"
        route_document = load_yaml_file(CAPABILITY_ROUTE_CASES)
        cases = (
            route_document.get("cases")
            if isinstance(route_document, dict)
            else None
        )
        if not isinstance(cases, list):
            self.fail(
                f"[{case_id}] expected route_cases=list; "
                f"actual={type(cases).__name__}"
            )
        route_rows = [case for case in cases if isinstance(case, dict)]
        route_ids = [case.get("id") for case in route_rows]
        expected_route_ids = ROUTE_CASE_IDS
        errors: list[str] = []
        if len(cases) != 62 or set(route_ids) != expected_route_ids:
            errors.append(
                f"[{case_id}] expected route_count=62 ids="
                f"{json.dumps(sorted(expected_route_ids))}; "
                f"actual count={len(cases)} ids="
                f"{json.dumps(sorted(str(item) for item in route_ids))}"
            )
        if len(route_ids) != len(set(route_ids)):
            errors.append(
                f"[{case_id}] expected route_ids=unique; "
                f"actual unique_count={len(set(route_ids))}"
            )
        route_by_id = {
            case["id"]: case
            for case in route_rows
            if isinstance(case.get("id"), str)
        }
        new_route_contract = {
            "capcov-route-backend-no-installed-client": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "backend-change-builder",
                "layer3_skills": [],
                "review_skill": "ai-code-review-refactor",
            },
            "capcov-route-kotlin-backend-no-android": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "backend-change-builder",
                "layer3_skills": ["kotlin-professional-usage"],
                "review_skill": "ai-code-review-refactor",
            },
        }
        new_route_exclusions = {
            "capcov-route-backend-no-installed-client": [
                "installed-client-change-builder",
                "android-platform-extension",
                "ios-ipados-platform-extension",
                "windows-platform-extension",
                "macos-platform-extension",
                "linux-desktop-platform-extension",
                "cross-platform-client-extension",
            ],
            "capcov-route-kotlin-backend-no-android": [
                "installed-client-change-builder",
                "android-platform-extension",
            ],
        }
        for route_id, expected in new_route_contract.items():
            route = route_by_id.get(route_id)
            if route is None:
                errors.append(
                    f"[{case_id}] expected route={route_id}=present; "
                    "actual=missing"
                )
                continue
            if route.get("expected") != expected:
                errors.append(
                    f"[{case_id}] expected {route_id}.expected="
                    f"{json.dumps(expected, sort_keys=True)}; "
                    f"actual={json.dumps(route.get('expected'), sort_keys=True)}"
                )
            expected_exclusions = new_route_exclusions[route_id]
            if route.get("excluded_skills") != expected_exclusions:
                errors.append(
                    f"[{case_id}] expected {route_id}.excluded_skills="
                    f"{json.dumps(expected_exclusions)}; "
                    f"actual={json.dumps(route.get('excluded_skills'))}"
                )
        exclusion_extensions = {
            "capcov-route-react-web-owner": [
                "installed-client-change-builder",
            ],
            "capcov-route-terraform-source": [
                "delivery-release-gate",
            ],
        }
        for route_id, expected_exclusions in exclusion_extensions.items():
            actual_exclusions = route_by_id.get(route_id, {}).get(
                "excluded_skills"
            )
            if actual_exclusions != expected_exclusions:
                errors.append(
                    f"[{case_id}] expected {route_id}.excluded_skills="
                    f"{json.dumps(expected_exclusions)}; "
                    f"actual={json.dumps(actual_exclusions)}"
                )

        route_report = ROUTING.evaluate_routes(
            cases_path=CAPABILITY_ROUTE_CASES,
            _validate_capability_matrix=False,
        )
        evaluated_by_id = {
            item["id"]: item
            for item in route_report.get("results", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        if (
            route_report.get("case_count") != 62
            or len(route_report.get("results", [])) != 62
            or route_report.get("candidate_coverage") != "full"
            or route_report.get("route_once") != "proven"
        ):
            errors.append(
                f"[{case_id}] expected evaluated_routes=62 with healthy harness; "
                f"actual={json.dumps({key: route_report.get(key) for key in ('case_count', 'candidate_coverage', 'route_once')}, sort_keys=True)}"
            )
        for route_id in sorted(new_route_contract):
            result = evaluated_by_id.get(route_id)
            if (
                not isinstance(result, dict)
                or result.get("actual") != new_route_contract[route_id]
                or result.get("positive_passed") is not True
                or result.get("negative_passed") is not True
                or result.get("passed") is not True
            ):
                errors.append(
                    f"[{case_id}] expected {route_id}=behavioral-pass; "
                    f"actual={json.dumps(result, sort_keys=True)}"
                )

        matrix = load_yaml_file(
            ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        )
        entries = matrix.get("entries") if isinstance(matrix, dict) else []
        matrix_by_id = {
            entry.get("id"): entry
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("id"), str)
        }
        conflict_contract = {
            "route-web-installed-zero-conflict": {
                "expected_professional_owner": "frontend-change-builder",
                "expected_domain_extensions": [],
                "expected_foundation_skills": [
                    "web-platform-professional-usage"
                ],
                "evidence_fixtures": ["capcov-route-react-web-owner"],
            },
            "route-backend-installed-zero-conflict": {
                "expected_professional_owner": "backend-change-builder",
                "expected_domain_extensions": [],
                "expected_foundation_skills": [],
                "evidence_fixtures": [
                    "capcov-route-backend-no-installed-client"
                ],
            },
            "route-infrastructure-release-zero-conflict": {
                "expected_professional_owner": (
                    "platform-infrastructure-change-builder"
                ),
                "expected_domain_extensions": [],
                "expected_foundation_skills": [
                    "infrastructure-as-code-safety"
                ],
                "evidence_fixtures": ["capcov-route-terraform-source"],
            },
            "route-platform-professional-zero-conflict": {
                "expected_professional_owner": (
                    "installed-client-change-builder"
                ),
                "expected_domain_extensions": [
                    "android-platform-extension"
                ],
                "expected_foundation_skills": [],
                "evidence_fixtures": ["capcov-route-android-owner"],
            },
            "route-language-domain-zero-conflict": {
                "expected_professional_owner": "backend-change-builder",
                "expected_domain_extensions": [],
                "expected_foundation_skills": [
                    "kotlin-professional-usage"
                ],
                "evidence_fixtures": [
                    "capcov-route-kotlin-backend-no-android"
                ],
            },
        }
        for entry_id, expected_fields in conflict_contract.items():
            entry = matrix_by_id.get(entry_id)
            if entry is None:
                errors.append(
                    f"[{case_id}] expected matrix_entry={entry_id}=present; "
                    "actual=missing"
                )
                continue
            for field, expected_value in expected_fields.items():
                actual_value = entry.get(field)
                if actual_value != expected_value:
                    errors.append(
                        f"[{case_id}] expected {entry_id}.{field}="
                        f"{json.dumps(expected_value)}; "
                        f"actual={json.dumps(actual_value)}"
                    )
            evidence = entry.get("evidence_fixtures")
            if isinstance(evidence, list) and any(
                str(item).startswith("capcov-admission-")
                for item in evidence
            ):
                errors.append(
                    f"[{case_id}] expected {entry_id}.evidence_family="
                    "capability-route; actual=admission"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_nonrouting_covered_evidence_requires_owner_bound_layer3_union(
        self,
    ) -> None:
        entry = {
            "id": "task-owner-bound-layer3",
            "axis": "engineering-task",
            "coverage_status": "covered",
            "expected_professional_owner": "installed-client-change-builder",
            "expected_domain_extensions": ["android-platform-extension"],
            "expected_foundation_skills": [
                "accessibility-inclusive-design",
                "client-application-testing",
            ],
            "evidence_fixtures": [
                "capcov-owner-selected-testing",
                "capcov-other-owner-selected-accessibility",
            ],
        }
        evidence_claims = {
            "capcov-owner-selected-testing": {
                "source": "evals/routing/capability-coverage-cases.yaml",
                "expected_professional_owner": (
                    "installed-client-change-builder"
                ),
                "expected_layer3_skills": ["client-application-testing"],
            },
            "capcov-other-owner-selected-accessibility": {
                "source": "evals/routing/capability-coverage-cases.yaml",
                "expected_professional_owner": "frontend-change-builder",
                "expected_layer3_skills": ["accessibility-inclusive-design"],
            },
        }
        errors: list[str] = []
        _validate_evidence_projection(
            [entry],
            root=ROOT,
            evidence_ids=set(evidence_claims),
            passing_exact_ids=set(evidence_claims),
            evidence_claims=evidence_claims,
            errors=errors,
        )
        self.assertEqual(
            [
                "task-owner-bound-layer3: covered evidence owner-bound "
                "passing Layer 3 union is missing declared Skill(s) "
                "['android-platform-extension', "
                "'accessibility-inclusive-design']; "
                "owner='installed-client-change-builder'; fixture claims="
                "[{'fixture': 'capcov-owner-selected-testing', "
                "'owner': 'installed-client-change-builder', "
                "'layer3': ['client-application-testing']}]"
            ],
            errors,
        )

    def test_covered_rows_require_exact_passing_behavioral_ids(self) -> None:
        case_id = "capcov-covered-exact-passing-evidence"
        matrix_path = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        matrix = load_yaml_file(matrix_path)
        entries = matrix.get("entries") if isinstance(matrix, dict) else None
        if not isinstance(entries, list):
            self.fail(
                f"[{case_id}] expected entries=list; "
                f"actual={type(entries).__name__}"
            )
        covered_paths = {
            str(entry.get("id")): entry.get("evidence_fixtures")
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("coverage_status") == "covered"
            and any(
                isinstance(item, str)
                and (
                    "/" in item
                    or Path(item).suffix in {".yaml", ".json"}
                )
                for item in entry.get("evidence_fixtures", [])
            )
        }
        errors: list[str] = []
        if covered_paths:
            errors.append(
                f"[{case_id}] expected covered_path_evidence=0; "
                f"actual={json.dumps(covered_paths, sort_keys=True)}"
            )
        source_ids = {
            "canonical": {
                str(row.get("id"))
                for row in load_yaml_file(
                    ROOT / "evals" / "routing" / "cases.yaml"
                )["cases"]
            },
            "admission": {
                str(row.get("id"))
                for row in load_yaml_file(
                    ROOT
                    / "evals"
                    / "capability-coverage"
                    / "admission-cases.yaml"
                )["cases"]
            },
            "capability": {
                str(row.get("id"))
                for row in load_yaml_file(CAPABILITY_ROUTE_CASES)["cases"]
            },
        }
        source_row_counts = {source: 0 for source in source_ids}
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or entry.get("coverage_status") != "covered"
            ):
                continue
            row_sources: set[str] = set()
            for fixture_id in entry.get("evidence_fixtures", []):
                matching_sources = [
                    source
                    for source, ids in source_ids.items()
                    if fixture_id in ids
                ]
                if len(matching_sources) != 1:
                    errors.append(
                        f"[{case_id}] expected {entry.get('id')} fixture "
                        f"{fixture_id!r} to belong to exactly one current "
                        "behavioral source; actual sources="
                        f"{json.dumps(matching_sources)}"
                    )
                    continue
                row_sources.add(matching_sources[0])
            for source in row_sources:
                source_row_counts[source] += 1
        expected_source_row_counts = {
            "canonical": 35,
            "admission": 30,
            "capability": 21,
        }
        if source_row_counts != expected_source_row_counts:
            errors.append(
                f"[{case_id}] expected evidence_source_row_counts="
                f"{json.dumps(expected_source_row_counts, sort_keys=True)}; "
                f"actual={json.dumps(source_row_counts, sort_keys=True)}"
            )

        with tempfile.TemporaryDirectory(
            prefix="capcov-covered-exact-evidence-"
        ) as raw:
            temp_root = Path(raw)
            path_matrix = _minimal_valid_matrix()
            _set_first_entry_covered(
                path_matrix,
                ["evals/routing/capability-coverage-cases.yaml"],
            )
            path_matrix_path = _write_matrix_fixture(
                temp_root,
                path_matrix,
                name="covered-path.yaml",
            )
            path_errors = validate_capability_coverage(
                path_matrix_path,
                root=temp_root,
                evidence_ids={},
                passing_evidence_ids=set(),
            )
            if (
                not path_errors
                or "covered" not in " ".join(path_errors).casefold()
                or "exact" not in " ".join(path_errors).casefold()
            ):
                errors.append(
                    f"[{case_id}] expected existing covered file path to "
                    "fail without an exact passing case ID; "
                    f"actual={json.dumps(path_errors)}"
                )

            forged_id = "capcov-route-forged-exact-id"
            forged_matrix = _minimal_valid_matrix()
            _set_first_entry_covered(forged_matrix, [forged_id])
            forged_path = _write_matrix_fixture(
                temp_root,
                forged_matrix,
                name="covered-forged-id.yaml",
            )
            forged_errors = validate_capability_coverage(
                forged_path,
                root=temp_root,
                evidence_ids={},
                passing_evidence_ids=set(),
            )
            if (
                not forged_errors
                or forged_id not in " ".join(forged_errors)
                or "stale" not in " ".join(forged_errors).casefold()
            ):
                errors.append(
                    f"[{case_id}] expected forged exact ID to fail closed; "
                    f"actual={json.dumps(forged_errors)}"
                )

            nonpassing_id = "capcov-route-react-web-owner"
            nonpassing_matrix = _minimal_valid_matrix()
            _set_first_entry_covered(
                nonpassing_matrix,
                [nonpassing_id],
            )
            nonpassing_path = _write_matrix_fixture(
                temp_root,
                nonpassing_matrix,
                name="covered-nonpassing-id.yaml",
            )
            nonpassing_errors = validate_capability_coverage(
                nonpassing_path,
                root=temp_root,
                evidence_ids={
                    nonpassing_id: (
                        "evals/routing/capability-coverage-cases.yaml:cases[0]",
                    )
                },
                passing_evidence_ids=set(),
            )
            if (
                not nonpassing_errors
                or nonpassing_id not in " ".join(nonpassing_errors)
                or "not passing" not in " ".join(nonpassing_errors).casefold()
            ):
                errors.append(
                    f"[{case_id}] expected known non-passing exact ID to "
                    f"fail closed; actual={json.dumps(nonpassing_errors)}"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_admission_evidence_enforces_authoritative_closed_contract(
        self,
    ) -> None:
        case_id = "capcov-admission-authoritative-closed-contract"
        valid = load_yaml_file(
            ROOT / "evals" / "capability-coverage" / "admission-cases.yaml"
        )
        professional = load_yaml_file(
            ROOT / "src" / "registry" / "professional-skills.yaml"
        )
        foundation = load_yaml_file(
            ROOT / "src" / "registry" / "foundation-skills.yaml"
        )
        domain = load_yaml_file(
            ROOT / "src" / "registry" / "domain-skills.yaml"
        )
        scenarios: dict[str, tuple[dict[str, object], tuple[str, ...]]] = {}

        duplicate_row = copy.deepcopy(valid)
        duplicate_row["cases"].append(
            copy.deepcopy(duplicate_row["cases"][0])
        )
        scenarios["duplicate-row"] = (
            duplicate_row,
            ("duplicate", "unique"),
        )

        duplicate = copy.deepcopy(valid)
        duplicate["cases"][-1] = copy.deepcopy(duplicate["cases"][0])
        scenarios["duplicate-id"] = (
            duplicate,
            ("duplicate", "unique"),
        )

        malformed = copy.deepcopy(valid)
        malformed["cases"][0] = "not-a-mapping"
        scenarios["malformed-row"] = (malformed, ("mapping",))

        wrong_schema = copy.deepcopy(valid)
        wrong_schema["schema_version"] = 2
        scenarios["wrong-schema"] = (wrong_schema, ("schema_version",))

        wrong_kind = copy.deepcopy(valid)
        wrong_kind["kind"] = "changeforge.wrong_admission_kind"
        scenarios["wrong-kind"] = (wrong_kind, ("kind",))

        wrong_fields = copy.deepcopy(valid)
        wrong_fields["cases"][0]["unexpected"] = True
        scenarios["wrong-row-fields"] = (wrong_fields, ("fields",))

        wrong_expected_fields = copy.deepcopy(valid)
        wrong_expected_fields["cases"][0]["expected"]["unexpected"] = True
        scenarios["wrong-expected-fields"] = (
            wrong_expected_fields,
            ("expected fields",),
        )

        wrong_case_kind = copy.deepcopy(valid)
        wrong_case_kind["cases"][0]["case_kind"] = "unexpected-kind"
        scenarios["wrong-case-kind"] = (
            wrong_case_kind,
            ("case_kind",),
        )

        with tempfile.TemporaryDirectory(
            prefix="capcov-admission-closed-contract-"
        ) as raw:
            temp_root = Path(raw)
            fixture_path = (
                temp_root
                / "evals"
                / "capability-coverage"
                / "admission-cases.yaml"
            )
            errors: list[str] = []
            for label, (payload, required_tokens) in scenarios.items():
                _write_yaml_mapping(fixture_path, payload)
                with mock.patch(
                    "capability_coverage.route_with_trace"
                ) as route_mock:
                    passing, actual_errors = evaluate_admission_evidence(
                        root=temp_root,
                        professional_registry=professional,
                        foundation_registry=foundation,
                        domain_registry=domain,
                    )
                folded = " ".join(actual_errors).casefold()
                if (
                    not actual_errors
                    or not any(token in folded for token in required_tokens)
                    or passing
                    or route_mock.called
                ):
                    errors.append(
                        f"[{case_id}] expected {label}=rejected-before-routing "
                        f"with signal={json.dumps(required_tokens)} and "
                        "passing_ids=[]; "
                        f"actual errors={json.dumps(actual_errors)} "
                        f"passing_count={len(passing)} "
                        f"route_called={route_mock.called}"
                    )
        if errors:
            self.fail("\n".join(errors))

    def test_each_named_consumer_executes_matrix_validation_in_process(self) -> None:
        loaded = _load_matrix_consumers()
        errors: list[str] = []
        for case_id, module in loaded.items():
            validator = getattr(
                module,
                "validate_capability_coverage_matrix",
                None,
            )
            if validator is None:
                errors.append(
                    f"[{case_id}] expected callable="
                    "validate_capability_coverage_matrix; actual=missing"
                )
            elif not callable(validator):
                errors.append(
                    f"[{case_id}] expected callable="
                    "validate_capability_coverage_matrix; actual=non-callable"
                )
        if errors:
            self.fail("\n".join(errors))

        with tempfile.TemporaryDirectory(prefix="capcov-matrix-consumers-") as raw:
            temp_root = Path(raw)
            evidence = (
                temp_root
                / "evals"
                / "routing"
                / "capability-coverage-cases.yaml"
            )
            evidence.parent.mkdir(parents=True)
            evidence.write_text("---\nschema_version: 1\ncases: []\n", encoding="utf-8")
            valid_matrix = _minimal_valid_matrix()
            required_space = valid_matrix["required_space"]
            valid_entries = valid_matrix["entries"]
            schema_entries = copy.deepcopy(valid_entries)
            schema_entries[0] = {
                key: value
                for key, value in schema_entries[0].items()
                if key != "task_type"
            }
            status_entries = copy.deepcopy(valid_entries)
            status_entries[0]["coverage_status"] = "unsupported"
            evidence_entries = copy.deepcopy(valid_entries)
            evidence_entries[0]["evidence_fixtures"] = [
                "evals/routing/does-not-exist.yaml"
            ]
            fixtures = {
                "valid": valid_matrix,
                "schema": {
                    "schema_version": 1,
                    "kind": "changeforge.capability_coverage_matrix",
                    "required_space": required_space,
                    "entries": schema_entries,
                },
                "status": {
                    "schema_version": 1,
                    "kind": "changeforge.capability_coverage_matrix",
                    "required_space": required_space,
                    "entries": status_entries,
                },
                "evidence": {
                    "schema_version": 1,
                    "kind": "changeforge.capability_coverage_matrix",
                    "required_space": required_space,
                    "entries": evidence_entries,
                },
            }
            fixture_paths: dict[str, Path] = {}
            for name, payload in fixtures.items():
                path = temp_root / f"{name}.yaml"
                _write_yaml_mapping(path, payload)
                fixture_paths[name] = path
            parse_path = temp_root / "parse.yaml"
            parse_path.write_text("entries: [\n", encoding="utf-8")
            fixture_paths["parse"] = parse_path

            for case_id, module in loaded.items():
                validator = getattr(
                    module,
                    "validate_capability_coverage_matrix",
                )
                valid_errors = validator(
                    fixture_paths["valid"],
                    root=temp_root,
                )
                if valid_errors != []:
                    errors.append(
                        f"[{case_id}] expected valid_errors=[]; "
                        f"actual={json.dumps(valid_errors)}"
                    )
                for category, required_tokens in (
                    ("parse", ("yaml", "parse")),
                    ("schema", ("task_type",)),
                    ("status", ("coverage_status",)),
                    (
                        "evidence",
                        ("evidence_fixtures", "does-not-exist.yaml"),
                    ),
                ):
                    actual_errors = validator(
                        fixture_paths[category],
                        root=temp_root,
                    )
                    folded = " ".join(str(item) for item in actual_errors).casefold()
                    if (
                        not isinstance(actual_errors, list)
                        or not actual_errors
                        or not any(token in folded for token in required_tokens)
                    ):
                        errors.append(
                            f"[{case_id}] expected {category}_errors="
                            f"{json.dumps(required_tokens)}; "
                            f"actual={json.dumps(actual_errors)}"
                        )

            sentinel = "capcov matrix sentinel"
            professionalism = loaded[
                "capcov-matrix-consumer-professionalism-regression"
            ]
            with mock.patch.object(
                professionalism,
                "validate_capability_coverage_matrix",
                return_value=[sentinel],
            ) as validator_spy:
                report = json.loads(
                    (
                        ROOT / "reports" / "professional-coverage-matrix.json"
                    ).read_text(encoding="utf-8")
                )
                with self.assertRaisesRegex(ValueError, sentinel):
                    professionalism._coverage_gate_summary(
                        report,
                        professionalism.DEFAULT_RELEASE_REVIEW_CONFIG,
                    )
                if validator_spy.call_count != 1:
                    errors.append(
                        "[capcov-matrix-consumer-professionalism-regression] "
                        "expected entrypoint_matrix_calls=1; "
                        f"actual={validator_spy.call_count}"
                    )

            routing = loaded["capcov-matrix-consumer-eval-routing"]
            with mock.patch.object(
                routing,
                "validate_capability_coverage_matrix",
                return_value=[sentinel],
            ) as validator_spy:
                report = routing.evaluate_routes(
                    cases_path=ROOT / "evals" / "routing" / "cases.yaml"
                )
                if validator_spy.call_count != 1:
                    errors.append(
                        "[capcov-matrix-consumer-eval-routing] expected "
                        "entrypoint_matrix_calls=1; "
                        f"actual={validator_spy.call_count}"
                    )
                if sentinel not in report.get("errors", []):
                    errors.append(
                        "[capcov-matrix-consumer-eval-routing] expected "
                        "sentinel_consumed=true; actual=false"
                    )

            for case_id in (
                "capcov-matrix-consumer-validate-skills",
                "capcov-matrix-consumer-validate-capabilities",
            ):
                module = loaded[case_id]
                with mock.patch.object(
                    module,
                    "validate_capability_coverage_matrix",
                    return_value=[sentinel],
                ) as validator_spy, mock.patch.object(
                    module,
                    "fail_many",
                    return_value=1,
                ) as fail_spy:
                    module.main()
                    if validator_spy.call_count != 1:
                        errors.append(
                            f"[{case_id}] expected entrypoint_matrix_calls=1; "
                            f"actual={validator_spy.call_count}"
                        )
                    consumed = (
                        fail_spy.call_count == 1
                        and sentinel in fail_spy.call_args.args[1]
                    )
                    if not consumed:
                        errors.append(
                            f"[{case_id}] expected sentinel_consumed=true; "
                            "actual=false"
                        )
        if errors:
            self.fail("\n".join(errors))

    def test_matrix_schema_version_requires_exact_int_in_all_consumers(
        self,
    ) -> None:
        case_id = "capcov-matrix-schema-version-exact-int"
        loaded = _load_matrix_consumers()
        with tempfile.TemporaryDirectory(
            prefix="capcov-schema-version-"
        ) as raw:
            temp_root = Path(raw)
            valid = _minimal_valid_matrix()
            valid_path = _write_matrix_fixture(
                temp_root,
                valid,
                name="valid.yaml",
            )
            boolean = copy.deepcopy(valid)
            boolean["schema_version"] = True
            boolean_path = _write_matrix_fixture(
                temp_root,
                boolean,
                name="boolean.yaml",
            )
            errors: list[str] = []
            for consumer_id, module in loaded.items():
                validator = getattr(
                    module,
                    "validate_capability_coverage_matrix",
                )
                control_errors = validator(valid_path, root=temp_root)
                if control_errors != []:
                    errors.append(
                        f"[{case_id}] expected {consumer_id}.control_errors=[]; "
                        f"actual={json.dumps(control_errors)}"
                    )
                    continue
                actual_errors = validator(boolean_path, root=temp_root)
                folded = " ".join(actual_errors).casefold()
                has_exact_type_signal = (
                    "schema_version" in folded
                    and re.search(r"\b(?:int|integer)\b", folded) is not None
                )
                if not actual_errors or not has_exact_type_signal:
                    errors.append(
                        f"[{case_id}] expected {consumer_id} to reject "
                        "schema_version=true as non-int; "
                        f"actual={json.dumps(actual_errors)}"
                    )
        if errors:
            self.fail("\n".join(errors))

    def test_matrix_evidence_paths_stay_inside_repository_root(self) -> None:
        case_id = "capcov-matrix-evidence-path-boundary"
        with tempfile.TemporaryDirectory(
            prefix="capcov-evidence-boundary-"
        ) as raw:
            temp_parent = Path(raw)
            temp_root = temp_parent / "repository"
            valid = _minimal_valid_matrix()
            valid_path = _write_matrix_fixture(
                temp_root,
                valid,
                name="valid.yaml",
            )
            control_errors = validate_capability_coverage(
                valid_path,
                root=temp_root,
            )
            if control_errors != []:
                self.fail(
                    f"[{case_id}] expected control_errors=[]; "
                    f"actual={json.dumps(control_errors)}"
                )

            outside = temp_parent / "outside-evidence.yaml"
            _write_yaml_mapping(
                outside,
                {"schema_version": 1, "cases": []},
            )
            link = (
                temp_root
                / "evals"
                / "routing"
                / "outside-link.yaml"
            )
            link.symlink_to(outside)
            existing_inside = (
                temp_root
                / "evals"
                / "routing"
                / "capability-coverage-cases.yaml"
            )
            mutations = {
                "absolute": str(existing_inside),
                "parent-traversal": "../outside-evidence.yaml",
                "symlink-escape": "evals/routing/outside-link.yaml",
            }
            errors: list[str] = []
            for label, evidence_value in mutations.items():
                mutated = copy.deepcopy(valid)
                mutated["entries"][0]["evidence_fixtures"] = [
                    evidence_value
                ]
                mutated_path = _write_matrix_fixture(
                    temp_root,
                    mutated,
                    name=f"{label}.yaml",
                )
                actual_errors = validate_capability_coverage(
                    mutated_path,
                    root=temp_root,
                )
                if not actual_errors:
                    errors.append(
                        f"[{case_id}] expected {label}=rejected; "
                        f"actual={json.dumps(actual_errors)}"
                    )
        if errors:
            self.fail("\n".join(errors))

    def test_matrix_unsupported_reason_requires_affirmative_gaps(self) -> None:
        case_id = "capcov-matrix-unsupported-gap-affirmation"
        loaded = _load_matrix_consumers()
        with tempfile.TemporaryDirectory(
            prefix="capcov-unsupported-reason-"
        ) as raw:
            temp_root = Path(raw)
            affirmative = _minimal_valid_matrix()
            entry = affirmative["entries"][0]
            entry.update(
                {
                    "expected_professional_owner": None,
                    "expected_domain_extensions": [],
                    "expected_foundation_skills": [],
                    "coverage_status": "intentionally-unsupported",
                    "disposition": "do-not-support",
                    "reason": (
                        "Reliable official or primary source contract evidence "
                        "is unavailable, and qualified reviewer evidence is "
                        "unavailable."
                    ),
                    "evidence_fixtures": [
                        "gap:official-primary-source",
                        "gap:qualified-reviewer",
                    ],
                }
            )
            affirmative_path = _write_matrix_fixture(
                temp_root,
                affirmative,
                name="affirmative.yaml",
            )
            errors: list[str] = []
            for consumer_id, module in loaded.items():
                validator = getattr(
                    module,
                    "validate_capability_coverage_matrix",
                )
                control_errors = validator(
                    affirmative_path,
                    root=temp_root,
                )
                if control_errors != []:
                    errors.append(
                        f"[{case_id}] expected {consumer_id}."
                        "affirmative_control_errors=[]; "
                        f"actual={json.dumps(control_errors)}"
                    )

            evidence_cases = {
                "zero-canonical": ["gap:"],
                "only-source": ["gap:official-primary-source"],
                "only-reviewer": ["gap:qualified-reviewer"],
                "arbitrary": ["gap:bounded-unsupported-proof"],
                "source-plus-arbitrary": [
                    "gap:official-primary-source",
                    "gap:bounded-unsupported-proof",
                ],
                "reviewer-plus-arbitrary": [
                    "gap:qualified-reviewer",
                    "gap:bounded-unsupported-proof",
                ],
            }
            reason_cases = {
                "no": (
                    "No reliable official primary source evidence is unavailable, "
                    "and no qualified reviewer evidence is unavailable."
                ),
                "not": (
                    "Reliable official primary source evidence is not unavailable, "
                    "and qualified reviewer evidence is not unavailable."
                ),
                "without": (
                    "Reliable official primary source evidence exists without a "
                    "missing source contract, and qualified reviewer evidence "
                    "exists without missing reviewer evidence."
                ),
                "available": (
                    "Reliable official primary source evidence is available, and "
                    "qualified reviewer evidence is available."
                ),
                "unavailable-negated": (
                    "The term unavailable does not describe reliable official "
                    "primary source evidence, and unavailable does not describe "
                    "qualified reviewer evidence."
                ),
                "qualified-no-reviewer": (
                    "Reliable official or primary source contract evidence is "
                    "unavailable, and qualified no reviewer evidence is unavailable."
                ),
                "qualified-not-reviewer": (
                    "Reliable official or primary source contract evidence is "
                    "unavailable, and qualified not reviewer evidence is unavailable."
                ),
                "qualified-without-reviewer": (
                    "Reliable official or primary source contract evidence is "
                    "unavailable, and qualified without reviewer evidence is "
                    "unavailable."
                ),
                "qualified-available-reviewer": (
                    "Reliable official or primary source contract evidence is "
                    "unavailable, and qualified available reviewer evidence is "
                    "unavailable."
                ),
            }
            invalid_paths: dict[str, Path] = {}
            for label, evidence_fixtures in evidence_cases.items():
                mutated = copy.deepcopy(affirmative)
                mutated["entries"][0]["evidence_fixtures"] = evidence_fixtures
                invalid_paths[f"evidence-{label}"] = _write_matrix_fixture(
                    temp_root,
                    mutated,
                    name=f"evidence-{label}.yaml",
                )
            for label, reason in reason_cases.items():
                mutated = copy.deepcopy(affirmative)
                mutated["entries"][0]["reason"] = reason
                invalid_paths[f"reason-{label}"] = _write_matrix_fixture(
                    temp_root,
                    mutated,
                    name=f"reason-{label}.yaml",
                )

            for label, path in invalid_paths.items():
                for consumer_id, module in loaded.items():
                    validator = getattr(
                        module,
                        "validate_capability_coverage_matrix",
                    )
                    actual_errors = validator(path, root=temp_root)
                    if not actual_errors:
                        errors.append(
                            f"[{case_id}] expected {label}.{consumer_id}="
                            "rejected; actual=[]"
                        )
        if errors:
            self.fail("\n".join(errors))

    def test_matrix_fixture_ids_are_globally_unique_and_deterministic(
        self,
    ) -> None:
        case_id = "capcov-matrix-fixture-id-uniqueness"
        loaded = _load_matrix_consumers()
        with tempfile.TemporaryDirectory(
            prefix="capcov-fixture-ids-"
        ) as raw:
            temp_root = Path(raw)
            matrix_path = _write_matrix_fixture(
                temp_root,
                _minimal_valid_matrix(),
                name="matrix.yaml",
            )
            admission_path = (
                temp_root
                / "evals"
                / "capability-coverage"
                / "admission-cases.yaml"
            )
            routing_path = (
                temp_root
                / "evals"
                / "routing"
                / "capability-coverage-cases.yaml"
            )

            def write_documents(
                admission_ids: list[str],
                routing_ids: list[str],
            ) -> None:
                _write_yaml_mapping(
                    admission_path,
                    {
                        "schema_version": 1,
                        "kind": "changeforge.capability_admission_cases",
                        "cases": [{"id": item} for item in admission_ids],
                    },
                )
                _write_yaml_mapping(
                    routing_path,
                    {
                        "schema_version": 1,
                        "kind": "changeforge.routing_cases",
                        "cases": [{"id": item} for item in routing_ids],
                    },
                )

            write_documents(
                ["capcov-unique-admission"],
                ["capcov-unique-routing"],
            )
            for consumer_id, module in loaded.items():
                control_errors = getattr(
                    module,
                    "validate_capability_coverage_matrix",
                )(matrix_path, root=temp_root)
                if control_errors != []:
                    self.fail(
                        f"[{case_id}] expected {consumer_id}.control_errors=[]; "
                        f"actual={json.dumps(control_errors)}"
                    )

            scenarios = {
                "within-admission": (
                    ["capcov-duplicate-admission", "capcov-duplicate-admission"],
                    ["capcov-unique-routing"],
                    "capcov-duplicate-admission",
                ),
                "within-routing": (
                    ["capcov-unique-admission"],
                    ["capcov-duplicate-routing", "capcov-duplicate-routing"],
                    "capcov-duplicate-routing",
                ),
                "cross-document": (
                    ["capcov-duplicate-cross-document"],
                    ["capcov-duplicate-cross-document"],
                    "capcov-duplicate-cross-document",
                ),
            }
            errors: list[str] = []
            for label, (
                admission_ids,
                routing_ids,
                duplicate_id,
            ) in scenarios.items():
                write_documents(admission_ids, routing_ids)
                for consumer_id, module in loaded.items():
                    validator = getattr(
                        module,
                        "validate_capability_coverage_matrix",
                    )
                    first = validator(matrix_path, root=temp_root)
                    second = validator(matrix_path, root=temp_root)
                    folded = " ".join(first).casefold()
                    duplicate_signal = (
                        duplicate_id in folded
                        and any(
                            token in folded
                            for token in ("duplicate", "unique")
                        )
                    )
                    if first != second:
                        errors.append(
                            f"[{case_id}] expected {label}.{consumer_id}="
                            "deterministic; "
                            f"actual={json.dumps([first, second])}"
                        )
                    if not first or not duplicate_signal:
                        errors.append(
                            f"[{case_id}] expected {label}.{consumer_id} "
                            f"duplicate={duplicate_id}; "
                            f"actual={json.dumps(first)}"
                        )
        if errors:
            self.fail("\n".join(errors))

    def test_matrix_cross_platform_unknown_target_is_analysis_first(
        self,
    ) -> None:
        case_id = "capcov-matrix-cross-platform-target-boundary"
        matrix = load_yaml_file(
            ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        )
        entries = matrix.get("entries") if isinstance(matrix, dict) else None
        if not isinstance(entries, list):
            self.fail(
                f"[{case_id}] expected entries=list; "
                f"actual={type(entries).__name__}"
            )
        by_id = {
            entry.get("id"): entry
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("id"), str)
        }
        errors: list[str] = []
        analysis_first = (
            "platform-cross-platform-client",
            "route-cross-platform-alone-rejected",
            "route-unknown-target-analysis-first",
        )
        for entry_id in analysis_first:
            entry = by_id.get(entry_id)
            if entry is None:
                errors.append(
                    f"[{case_id}] expected {entry_id}=present; actual=missing"
                )
                continue
            if entry.get("expected_professional_owner") != (
                "engineering-change-analysis"
            ):
                errors.append(
                    f"[{case_id}] expected {entry_id}.owner="
                    "engineering-change-analysis; "
                    f"actual={json.dumps(entry.get('expected_professional_owner'))}"
                )
            if entry.get("expected_domain_extensions") != []:
                errors.append(
                    f"[{case_id}] expected {entry_id}.domains=[]; "
                    f"actual={json.dumps(entry.get('expected_domain_extensions'))}"
                )

        concrete = {
            "route-flutter-android-ios": [
                "cross-platform-client-extension",
                "android-platform-extension",
                "ios-ipados-platform-extension",
            ],
            "route-electron-windows": [
                "cross-platform-client-extension",
                "windows-platform-extension",
            ],
        }
        for entry_id, expected_domains in concrete.items():
            entry = by_id.get(entry_id)
            actual_domains = (
                entry.get("expected_domain_extensions")
                if isinstance(entry, dict)
                else None
            )
            if actual_domains != expected_domains:
                errors.append(
                    f"[{case_id}] expected {entry_id}.domains="
                    f"{json.dumps(expected_domains)}; "
                    f"actual={json.dumps(actual_domains)}"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_mobile_removal_source_inventory_and_profile_counts(self) -> None:
        case_id = "capcov-mobile-remove-source-inventory"
        registry_contract = {
            "control-skills.yaml": ("control_skills", 1),
            "professional-skills.yaml": ("professional_skills", 26),
            "foundation-skills.yaml": ("foundation_skills", 150),
            "domain-skills.yaml": ("domain_skills", 13),
        }
        entries_by_layer: dict[str, list[dict[str, object]]] = {}
        errors: list[str] = []
        for file_name, (key, expected_count) in registry_contract.items():
            data = load_yaml_file(ROOT / "src" / "registry" / file_name)
            raw_entries = data.get(key) if isinstance(data, dict) else None
            entries = (
                [entry for entry in raw_entries if isinstance(entry, dict)]
                if isinstance(raw_entries, list)
                else []
            )
            entries_by_layer[key] = entries
            if len(entries) != expected_count:
                errors.append(
                    f"[{case_id}] expected {key}.count={expected_count}; "
                    f"actual={len(entries)}"
                )

        layer_counts = {
            key: len(entries)
            for key, entries in entries_by_layer.items()
        }
        total = sum(layer_counts.values())
        non_control = total - layer_counts.get("control_skills", 0)
        if (total, non_control) != (190, 189):
            errors.append(
                f"[{case_id}] expected source_inventory="
                "190-total/189-non-control; "
                f"actual={total}-total/{non_control}-non-control"
            )

        domain_entries = entries_by_layer.get("domain_skills", [])
        domain_names = {
            str(entry.get("name"))
            for entry in domain_entries
            if isinstance(entry.get("name"), str)
        }
        domain_paths = {
            str(entry.get("path"))
            for entry in domain_entries
            if isinstance(entry.get("path"), str)
        }
        physical_domain_paths = {
            skill.parent.relative_to(ROOT).as_posix()
            for skill in (ROOT / "src" / "domain-extensions").glob(
                "*/SKILL.md"
            )
        }
        if len(physical_domain_paths) != 13:
            errors.append(
                f"[{case_id}] expected physical_domain_count=13; "
                f"actual={len(physical_domain_paths)}"
            )
        if domain_paths != physical_domain_paths:
            errors.append(
                f"[{case_id}] expected registry_paths=physical_domain_paths; "
                "actual="
                f"{json.dumps({'registry_only': sorted(domain_paths - physical_domain_paths), 'physical_only': sorted(physical_domain_paths - domain_paths)}, sort_keys=True)}"
            )

        foundation_names = {
            str(entry.get("name"))
            for entry in entries_by_layer.get("foundation_skills", [])
            if isinstance(entry.get("name"), str)
        }
        layer3_catalog = foundation_names | domain_names
        if len(layer3_catalog) != 163:
            errors.append(
                f"[{case_id}] expected layer3_catalog_count=163; "
                f"actual={len(layer3_catalog)}"
            )

        expected_top_level = {
            "recommended": 27,
            "full": 40,
            "dev": 190,
        }
        if VALIDATION_CONTRACTS.EXPECTED_PROFILE_TOP_LEVEL_COUNTS != (
            expected_top_level
        ):
            errors.append(
                f"[{case_id}] expected profile_top_level_counts="
                f"{json.dumps(expected_top_level, sort_keys=True)}; "
                "actual="
                f"{json.dumps(VALIDATION_CONTRACTS.EXPECTED_PROFILE_TOP_LEVEL_COUNTS, sort_keys=True)}"
            )
        expected_delivery = {
            "recommended": {
                "top_level_skill": 27,
                "targeted_reference": 154,
                "routing_index_only": 9,
            },
            "full": {
                "top_level_skill": 40,
                "targeted_reference": 141,
                "routing_index_only": 9,
            },
            "dev": {
                "top_level_skill": 190,
                "targeted_reference": 0,
                "routing_index_only": 0,
            },
        }
        if VALIDATION_CONTRACTS.EXPECTED_PROFILE_DELIVERY_MODE_COUNTS != (
            expected_delivery
        ):
            errors.append(
                f"[{case_id}] expected profile_delivery_counts="
                f"{json.dumps(expected_delivery, sort_keys=True)}; "
                "actual="
                f"{json.dumps(VALIDATION_CONTRACTS.EXPECTED_PROFILE_DELIVERY_MODE_COUNTS, sort_keys=True)}"
            )
        if errors:
            self.fail("\n".join(errors))

    def test_mobile_removal_eliminates_compatibility_routing_contracts(
        self,
    ) -> None:
        case_id = "capcov-mobile-remove-routing-contract"
        active_contracts = {
            "src/registry/domain-skills.yaml": (
                "explicit-only-compatibility",
                "replacement_targets",
            ),
            "scripts/validation_utils.py": (
                "DOMAIN_COMPATIBILITY_ROUTING_MODE",
                "explicit-only-compatibility",
                "replacement_targets",
                "compatibility_exact_id_covered",
                "compatibility_legacy_config_covered",
                "compatibility_successor_redirect_covered",
                "compatibility_bridge_excluded_covered",
                "compatibility_ordinary_negative_covered",
            ),
            "scripts/deterministic_route_oracle.py": (
                "MOBILE_COMPATIBILITY_BRIDGE",
                "DOMAIN_COMPATIBILITY_ROUTING_MODE",
                "DOMAIN_COMPATIBILITY_ROUTE_SPECS",
                "_compatibility_resolution",
                "replacement_targets",
                "routing_input",
                "include_compatibility",
            ),
            "scripts/eval-routing.py": (
                "routing_input",
                "compatibility_expectation",
                "compatibility_resolution",
            ),
            "scripts/capability_coverage.py": (
                "routing_input",
                "compatibility_expectation",
            ),
            "scripts/eval-skill-professionalism.py": (
                "compatibility_resolution",
                "capcov-legacy-config-mobile-",
            ),
            "scripts/validate-skill-routing.py": (
                "DOMAIN_COMPATIBILITY_ROUTING_MODE",
            ),
            "evals/routing/capability-coverage-cases.yaml": (
                "routing_input:",
                "compatibility_expectation:",
                "explicit-only-compatibility",
                "replacement_targets",
                "legacy-config",
            ),
        }
        errors: list[str] = []
        for relative, forbidden_markers in active_contracts.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            present = [
                marker for marker in forbidden_markers if marker in text
            ]
            if present:
                errors.append(
                    f"[{case_id}] expected {relative}.compatibility_markers="
                    "absent; "
                    f"actual={json.dumps(present)}"
                )

        if VALIDATION_CONTRACTS.DOMAIN_ROUTING_MODES != frozenset(
            {"modifier-only"}
        ):
            errors.append(
                f"[{case_id}] expected domain_routing_modes=['modifier-only']; "
                "actual="
                f"{json.dumps(sorted(VALIDATION_CONTRACTS.DOMAIN_ROUTING_MODES))}"
            )
        for module, names in (
            (
                VALIDATION_CONTRACTS,
                ("DOMAIN_COMPATIBILITY_ROUTING_MODE",),
            ),
            (
                ROUTE_ORACLE,
                (
                    "MOBILE_COMPATIBILITY_BRIDGE",
                    "DOMAIN_COMPATIBILITY_ROUTE_SPECS",
                    "_compatibility_resolution",
                ),
            ),
        ):
            present = [name for name in names if hasattr(module, name)]
            if present:
                errors.append(
                    f"[{case_id}] expected {module.__name__}.compatibility_api="
                    f"absent; actual={json.dumps(present)}"
                )
        route_parameters = set(inspect.signature(ROUTING.route).parameters)
        forbidden_parameters = sorted(
            route_parameters & {"routing_input", "include_compatibility"}
        )
        if forbidden_parameters:
            errors.append(
                f"[{case_id}] expected route.compatibility_parameters=absent; "
                f"actual={json.dumps(forbidden_parameters)}"
            )
        if errors:
            self.fail("\n".join(errors))

    def test_mobile_removal_route_closed_set_and_successors(self) -> None:
        case_id = "capcov-mobile-remove-route-closed-set"
        expected_route_ids = ROUTE_CASE_IDS
        route_document = load_yaml_file(CAPABILITY_ROUTE_CASES)
        cases = (
            route_document.get("cases")
            if isinstance(route_document, dict)
            else None
        )
        if not isinstance(cases, list):
            self.fail(
                f"[{case_id}] expected cases=list; "
                f"actual={type(cases).__name__}"
            )
        rows = [
            row
            for row in cases
            if isinstance(row, dict)
            and isinstance(row.get("id"), str)
        ]
        route_by_id = {str(row["id"]): row for row in rows}
        actual_route_ids = set(route_by_id)
        errors: list[str] = []
        if len(rows) != 62 or actual_route_ids != expected_route_ids:
            errors.append(
                f"[{case_id}] expected route_count=62 ids="
                f"{json.dumps(sorted(expected_route_ids))}; "
                f"actual count={len(rows)} ids="
                f"{json.dumps(sorted(actual_route_ids))}"
            )

        analysis_expected = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        transformed_contract = {
            "capcov-removed-mobile-skill-id-unsupported": {
                "expected": analysis_expected,
            },
            "capcov-unknown-installed-client-target-analysis": {
                "expected": analysis_expected,
            },
        }
        for route_id, expected_contract in transformed_contract.items():
            row = route_by_id.get(route_id)
            if row is None:
                errors.append(
                    f"[{case_id}] expected {route_id}=present; actual=missing"
                )
                continue
            if row.get("expected") != expected_contract["expected"]:
                errors.append(
                    f"[{case_id}] expected {route_id}.expected="
                    f"{json.dumps(expected_contract['expected'], sort_keys=True)}; "
                    f"actual={json.dumps(row.get('expected'), sort_keys=True)}"
                )
            forbidden_fields = sorted(
                set(row) & {"routing_input", "compatibility_expectation"}
            )
            if forbidden_fields:
                errors.append(
                    f"[{case_id}] expected {route_id}.legacy_fields=absent; "
                    f"actual={json.dumps(forbidden_fields)}"
                )

        successor_contract = {
            "capcov-route-android-owner": [
                "android-platform-extension"
            ],
            "capcov-route-ios-owner": [
                "ios-ipados-platform-extension"
            ],
            "capcov-route-flutter-android-ios": [
                "cross-platform-client-extension",
                "android-platform-extension",
                "ios-ipados-platform-extension",
            ],
            "capcov-route-electron-windows": [
                "cross-platform-client-extension",
                "windows-platform-extension",
            ],
        }
        for route_id, expected_domains in successor_contract.items():
            row = route_by_id.get(route_id)
            actual_domains = (
                row.get("expected", {}).get("layer3_skills")
                if isinstance(row, dict)
                and isinstance(row.get("expected"), dict)
                else None
            )
            if actual_domains != expected_domains:
                errors.append(
                    f"[{case_id}] expected {route_id}.successor_domains="
                    f"{json.dumps(expected_domains)}; "
                    f"actual={json.dumps(actual_domains)}"
                )

        route_report = ROUTING.evaluate_routes(
            cases_path=CAPABILITY_ROUTE_CASES,
            _validate_capability_matrix=False,
        )
        if (
            route_report.get("case_count") != 62
            or len(route_report.get("results", [])) != 62
            or route_report.get("candidate_coverage") != "full"
            or route_report.get("route_once") != "proven"
        ):
            errors.append(
                f"[{case_id}] expected evaluated_routes=62 with healthy harness; "
                "actual="
                f"{json.dumps({key: route_report.get(key) for key in ('case_count', 'candidate_coverage', 'route_once')}, sort_keys=True)}"
            )

        domain_names = {
            str(entry.get("name"))
            for entry in load_yaml_file(
                ROOT / "src" / "registry" / "domain-skills.yaml"
            ).get("domain_skills", [])
            if isinstance(entry, dict)
            and isinstance(entry.get("name"), str)
        }
        for route_id in transformed_contract:
            fixture = route_by_id[route_id]
            actual = ROUTING.route(
                str(fixture["prompt"]),
                main_execution=fixture["main_execution"],
            )
            if actual != analysis_expected:
                errors.append(
                    f"[{case_id}] expected {route_id}.actual="
                    f"{json.dumps(analysis_expected, sort_keys=True)}; "
                    f"actual={json.dumps(actual, sort_keys=True)}"
                )
                continue
            selected_domains = sorted(
                set(actual.get("layer3_skills", [])) & domain_names
            )
            if selected_domains:
                errors.append(
                    f"[{case_id}] expected {route_id}.selected_domains=[]; "
                    f"actual={json.dumps(selected_domains)}"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_mobile_removal_preserves_canonical_matrix_and_admission_counts(
        self,
    ) -> None:
        case_id = "capcov-mobile-remove-stable-evidence-counts"
        errors: list[str] = []
        canonical = ROUTING.evaluate_routes()
        canonical_summary = {
            "status": canonical.get("status"),
            "case_count": canonical.get("case_count"),
            "passed_count": canonical.get("passed_count"),
        }
        canonical_cases = load_yaml_file(ROUTING.CASES)["cases"]
        expected_canonical = {
            "status": "pass",
            "case_count": len(canonical_cases),
            "passed_count": len(canonical_cases),
        }
        if canonical_summary != expected_canonical:
            errors.append(
                f"[{case_id}] expected canonical_routes="
                f"{json.dumps(expected_canonical, sort_keys=True)}; "
                f"actual={json.dumps(canonical_summary, sort_keys=True)}"
            )
        canonical_errors = canonical.get("errors")
        if canonical_errors != []:
            errors.append(
                f"[{case_id}] expected canonical_errors=[]; actual="
                f"{json.dumps(canonical_errors, sort_keys=True)}"
            )

        admission = load_yaml_file(
            ROOT
            / "evals"
            / "capability-coverage"
            / "admission-cases.yaml"
        )
        admission_cases = (
            admission.get("cases")
            if isinstance(admission, dict)
            else None
        )
        admission_ids = {
            str(row.get("id"))
            for row in admission_cases or []
            if isinstance(row, dict)
            and isinstance(row.get("id"), str)
        }
        admission_combinations = {
            (row.get("layer"), row.get("skill"), row.get("case_kind"))
            for row in admission_cases or []
            if isinstance(row, dict)
        }
        if (
            not isinstance(admission_cases, list)
            or len(admission_ids) != len(admission_cases or [])
            or len(admission_combinations) != len(admission_cases or [])
            or not admission_combinations
            <= CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
        ):
            errors.append(
                f"[{case_id}] expected admissions=unique-registry-derived-"
                "subset; "
                "actual="
                f"{json.dumps({'row_count': len(admission_cases or []), 'unique_id_count': len(admission_ids), 'unique_obligation_count': len(admission_combinations), 'extra': sorted(admission_combinations - CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS)}, sort_keys=True)}"
            )

        matrix = load_yaml_file(
            ROOT / "evals" / "capability-coverage" / "matrix.yaml"
        )
        matrix_entries = (
            matrix.get("entries") if isinstance(matrix, dict) else None
        )
        statuses: dict[str, int] = {}
        for entry in matrix_entries or []:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("coverage_status"))
            statuses[status] = statuses.get(status, 0) + 1
        expected_statuses = {
            "covered": 81,
            "partial": 39,
            "missing": 0,
            "intentionally-unsupported": 5,
        }
        actual_statuses = {
            key: statuses.get(key, 0)
            for key in expected_statuses
        }
        if (
            not isinstance(matrix_entries, list)
            or len(matrix_entries) != 125
            or actual_statuses != expected_statuses
        ):
            errors.append(
                f"[{case_id}] expected matrix=125/"
                f"{json.dumps(expected_statuses, sort_keys=True)}; "
                "actual="
                f"{json.dumps({'row_count': len(matrix_entries or []), 'statuses': actual_statuses}, sort_keys=True)}"
            )
        if errors:
            self.fail("\n".join(errors))

    def test_domain_registry_v6_requires_modifier_only_routing_mode(self) -> None:
        case_id = "capcov-domain-schema-v6-mode-required"
        data = load_yaml_file(ROOT / "src" / "registry" / "domain-skills.yaml")
        actual_version = data.get("schema_version") if isinstance(data, dict) else None
        if type(actual_version) is not int or actual_version != 6:
            self.fail(
                f"[{case_id}] expected schema_version=exact-int-6; "
                f"actual={json.dumps(actual_version)}"
            )
        errors: list[str] = []
        for entry in data.get("domain_skills", []):
            name = entry.get("name")
            actual_mode = entry.get("routing_mode")
            if actual_mode != "modifier-only":
                errors.append(
                    f"[{case_id}] expected routing_mode.{name}=modifier-only; "
                    f"actual={json.dumps(actual_mode)}"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_canonical_routing_report_has_completed_mobile_successor_migration(
        self,
    ) -> None:
        report = ROUTING.evaluate_routes()
        failed = {
            item["id"]
            for item in report["results"]
            if item.get("passed") is not True
        }
        canonical_cases = load_yaml_file(ROUTING.CASES)["cases"]
        self.assertEqual(6, report["schema_version"])
        self.assertEqual("pass", report["status"])
        self.assertEqual([], report["errors"])
        self.assertEqual(len(canonical_cases), report["case_count"])
        self.assertEqual(len(canonical_cases), report["passed_count"])
        self.assertEqual(set(), failed)
        self.assertTrue(
            all(item.get("negative_passed") is True for item in report["results"])
        )
        self.assertEqual(69, report["negative_case_count"])
        self.assertEqual(44, report["domain_family_case_count"])
        self.assertEqual(26, report["domain_anti_case_count"])
        self.assertEqual(13, report["domain_transition_case_count"])
        self.assertEqual(14, report["domain_unchanged_case_count"])
        self.assertEqual(3, report["max_layer3_per_case"])
        self.assertEqual("full", report["candidate_coverage"])
        self.assertEqual("proven", report["route_once"])
        self.assertEqual(0, report["legacy_route_count"])
        self.assertTrue(
            all(
                isinstance(item.get("route_decision"), dict)
                for item in report["results"]
            )
        )
        prompt = "Implement an accepted backend service behavior change."
        with self.assertRaises(TypeError):
            ROUTE_ORACLE.route(prompt)
        with self.assertRaises(TypeError):
            ROUTE_ORACLE.route_with_trace(prompt)
        with self.assertRaises(TypeError):
            ROUTING.route(prompt)

    def test_phase_two_natural_client_domain_routes_are_exact(self) -> None:
        case_id = "capcov-natural-client-domain-exact-routes"
        document = load_yaml_file(CAPABILITY_ROUTE_CASES)
        self.assertEqual({"schema_version", "cases"}, set(document))
        self.assertEqual(1, document["schema_version"])
        cases = document["cases"]
        self.assertIsInstance(cases, list)
        rows = {
            row["id"]: row
            for row in cases
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        self.assertEqual(62, len(cases))
        self.assertEqual(62, len(rows))
        self.assertEqual(ROUTE_CASE_IDS, set(rows))
        self.assertEqual(
            NATURAL_CLIENT_ROUTE_CASE_IDS
            | NEIGHBOR_CLIENT_ROUTE_CASE_IDS
            | DOCUMENTATION_ORDER_NEGATIVE_ROUTE_CASE_IDS,
            set(rows) - LEGACY_ROUTE_CASE_IDS - ANDROID_ACCESSIBILITY_ROUTE_CASE_IDS,
        )

        report = ROUTING.evaluate_routes(
            cases_path=CAPABILITY_ROUTE_CASES,
            _validate_capability_matrix=False,
        )
        self.assertEqual(6, report["schema_version"])
        self.assertEqual(62, report["case_count"])
        self.assertEqual(62, len(report["results"]))
        self.assertEqual("full", report["candidate_coverage"])
        self.assertEqual("proven", report["route_once"])
        self.assertLessEqual(report["max_layer3_per_case"], 3)
        results = {
            result["id"]: result
            for result in report["results"]
            if isinstance(result, dict) and isinstance(result.get("id"), str)
        }
        self.assertEqual(ROUTE_CASE_IDS, set(results))

        harness_errors: list[str] = []
        route_mismatches: list[str] = []
        allowed_route_error_prefixes = tuple(
            prefix
            for target_id in (
                NATURAL_CLIENT_ROUTE_CASE_IDS
                | NEIGHBOR_CLIENT_ROUTE_CASE_IDS
                | DOCUMENTATION_ORDER_NEGATIVE_ROUTE_CASE_IDS
            )
            for prefix in (
                f"{target_id}: expected ",
                f"{target_id}: actual route selected explicitly excluded Skill(s): ",
            )
        )
        for error in report["errors"]:
            if not (
                isinstance(error, str)
                and error.startswith(allowed_route_error_prefixes)
            ):
                harness_errors.append(
                    f"[{case_id}] unexpected evaluator error={error!r}"
                )

        for target_id in sorted(
            NATURAL_CLIENT_ROUTE_CASE_IDS
            | DOCUMENTATION_ORDER_NEGATIVE_ROUTE_CASE_IDS
        ):
            fixture = rows[target_id]
            result = results[target_id]
            expected = fixture["expected"]
            actual = result.get("actual")
            decision = result.get("route_decision")
            trace = result.get("winner_trace")
            if (
                not isinstance(actual, dict)
                or not isinstance(decision, dict)
                or not isinstance(trace, dict)
            ):
                harness_errors.append(
                    f"[{target_id}] expected complete route result; "
                    f"actual={json.dumps(result, sort_keys=True)}"
                )
                continue
            route_result = decision.get("route_result")
            selected = trace.get("selected_candidate")
            if not isinstance(route_result, dict) or not isinstance(
                selected,
                dict,
            ):
                harness_errors.append(
                    f"[{target_id}] expected complete envelope and winner; "
                    f"actual={json.dumps({'route_result': route_result, 'selected': selected}, sort_keys=True)}"
                )
                continue
            expected_route_result = {
                "start_profile": expected["profile"],
                "primary_skill": expected["primary_skill"],
                "layer3_skills": expected["layer3_skills"],
                "review_skill": expected["review_skill"],
                "execution_level": "L4",
                "level_basis": fixture["main_execution"]["level_basis"],
            }
            if decision.get("path") != actual["path"]:
                harness_errors.append(
                    f"[{target_id}] route_decision.path does not project actual.path"
                )
            actual_route_result = {
                key: route_result.get(key)
                for key in expected_route_result
            }
            if actual_route_result != (
                expected_route_result
                if actual == expected
                else {
                    "start_profile": actual["profile"],
                    "primary_skill": actual["primary_skill"],
                    "layer3_skills": actual["layer3_skills"],
                    "review_skill": actual["review_skill"],
                    "execution_level": "L4",
                    "level_basis": fixture["main_execution"]["level_basis"],
                }
            ):
                harness_errors.append(
                    f"[{target_id}] route envelope projection is inconsistent; "
                    f"actual={json.dumps(actual_route_result, sort_keys=True)}"
                )
            if (
                decision.get("main_execution_provenance")
                != fixture["main_execution"]
                or decision.get("route_once") is not True
                or trace.get("candidate_coverage") != "full"
                or trace.get("route_once") != "proven"
            ):
                harness_errors.append(
                    f"[{target_id}] expected L4 provenance and route-once proof"
                )
            if len(actual.get("layer3_skills", [])) > 3:
                harness_errors.append(
                    f"[{target_id}] actual Layer 3 exceeds budget: "
                    f"{actual['layer3_skills']!r}"
                )
            if actual != expected:
                route_mismatches.append(
                    f"[{target_id}] expected={json.dumps(expected, sort_keys=True)}; "
                    f"actual={json.dumps(actual, sort_keys=True)}; "
                    f"rule={trace.get('rule_id')!r}; "
                    f"selected={selected.get('candidate_id')!r}"
                )

        if harness_errors:
            self.fail("\n".join(harness_errors))
        if route_mismatches:
            self.fail("\n".join(route_mismatches))

    def test_phase_two_neighbor_client_domain_routes_are_exact(self) -> None:
        case_id = "capcov-neighbor-client-domain-exact-routes"
        document = load_yaml_file(CAPABILITY_ROUTE_CASES)
        self.assertEqual({"schema_version", "cases"}, set(document))
        self.assertEqual(1, document["schema_version"])
        cases = document["cases"]
        rows = {
            row["id"]: row
            for row in cases
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        self.assertEqual(62, len(cases))
        self.assertEqual(62, len(rows))
        self.assertEqual(ROUTE_CASE_IDS, set(rows))
        self.assertEqual(
            NEIGHBOR_CLIENT_ROUTE_CASE_IDS,
            {
                target_id
                for target_id in rows
                if target_id.startswith("capcov-neighbor-")
            },
        )

        report = ROUTING.evaluate_routes(
            cases_path=CAPABILITY_ROUTE_CASES,
            _validate_capability_matrix=False,
        )
        self.assertEqual(6, report["schema_version"])
        self.assertEqual(62, report["case_count"])
        self.assertEqual(62, len(report["results"]))
        self.assertEqual("full", report["candidate_coverage"])
        self.assertEqual("proven", report["route_once"])
        self.assertLessEqual(report["max_layer3_per_case"], 3)
        results = {
            result["id"]: result
            for result in report["results"]
            if isinstance(result, dict) and isinstance(result.get("id"), str)
        }
        self.assertEqual(ROUTE_CASE_IDS, set(results))

        allowed_route_error_prefixes = tuple(
            prefix
            for target_id in (
                NATURAL_CLIENT_ROUTE_CASE_IDS
                | NEIGHBOR_CLIENT_ROUTE_CASE_IDS
                | DOCUMENTATION_ORDER_NEGATIVE_ROUTE_CASE_IDS
            )
            for prefix in (
                f"{target_id}: expected ",
                f"{target_id}: actual route selected explicitly excluded Skill(s): ",
            )
        )
        harness_errors = [
            f"[{case_id}] unexpected evaluator error={error!r}"
            for error in report["errors"]
            if not (
                isinstance(error, str)
                and error.startswith(allowed_route_error_prefixes)
            )
        ]
        route_mismatches: list[str] = []
        for target_id in sorted(NEIGHBOR_CLIENT_ROUTE_CASE_IDS):
            fixture = rows[target_id]
            expected = fixture["expected"]
            result = results[target_id]
            actual = result.get("actual")
            decision = result.get("route_decision")
            trace = result.get("winner_trace")
            if (
                not isinstance(actual, dict)
                or not isinstance(decision, dict)
                or not isinstance(trace, dict)
            ):
                harness_errors.append(
                    f"[{target_id}] expected complete route result; "
                    f"actual={json.dumps(result, sort_keys=True)}"
                )
                continue
            route_result = decision.get("route_result")
            selected = trace.get("selected_candidate")
            if not isinstance(route_result, dict) or not isinstance(
                selected,
                dict,
            ):
                harness_errors.append(
                    f"[{target_id}] expected complete envelope and winner; "
                    f"actual={json.dumps({'route_result': route_result, 'selected': selected}, sort_keys=True)}"
                )
                continue
            expected_projection = {
                "start_profile": actual["profile"],
                "primary_skill": actual["primary_skill"],
                "layer3_skills": actual["layer3_skills"],
                "review_skill": actual["review_skill"],
                "execution_level": "L4",
                "level_basis": fixture["main_execution"]["level_basis"],
            }
            actual_projection = {
                key: route_result.get(key)
                for key in expected_projection
            }
            if (
                decision.get("path") != actual["path"]
                or actual_projection != expected_projection
                or decision.get("main_execution_provenance")
                != fixture["main_execution"]
                or decision.get("route_once") is not True
                or trace.get("candidate_coverage") != "full"
                or trace.get("route_once") != "proven"
                or len(actual.get("layer3_skills", [])) > 3
            ):
                harness_errors.append(
                    f"[{target_id}] expected consistent L4 route envelope, "
                    "route-once proof, and Layer 3 budget; "
                    f"actual={json.dumps({'decision_path': decision.get('path'), 'route_result': actual_projection, 'trace': trace}, sort_keys=True)}"
                )
                continue
            if actual != expected:
                route_mismatches.append(
                    f"[{target_id}] mismatch=route; "
                    f"expected={json.dumps(expected, sort_keys=True)}; "
                    f"actual={json.dumps(actual, sort_keys=True)}; "
                    f"candidate={selected.get('candidate_id')!r}; "
                    f"rule={trace.get('rule_id')!r}"
                )

        if harness_errors:
            self.fail("\n".join(harness_errors))
        if route_mismatches:
            self.fail("\n".join(route_mismatches))

    def test_phase_one_routes_match_one_owner_and_ordered_domain_contract(self) -> None:
        report = ROUTING.evaluate_routes(
            cases_path=CAPABILITY_ROUTE_CASES,
            _validate_capability_matrix=False,
        )
        results = {item["id"]: item for item in report["results"]}
        errors: list[str] = []
        for case_id in sorted(LEGACY_ROUTE_CASE_IDS):
            item = results.get(case_id)
            if item is None:
                errors.append(f"[{case_id}] expected fixture=present; actual=missing")
                continue
            expected = item["expected"]
            actual = item["actual"]
            for field in (
                "path",
                "profile",
                "primary_skill",
                "layer3_skills",
                "review_skill",
            ):
                if actual.get(field) != expected.get(field):
                    errors.append(
                        f"[{case_id}] expected {field}="
                        f"{json.dumps(expected.get(field), separators=(',', ':'))}; "
                        f"actual={json.dumps(actual.get(field), separators=(',', ':'))}"
                    )
            if len(actual.get("layer3_skills", [])) > 3:
                errors.append(
                    f"[{case_id}] expected layer3_count<=3; "
                    f"actual={len(actual.get('layer3_skills', []))}"
                )
        if errors:
            self.fail("\n".join(errors))

    def test_removed_skill_id_is_unsupported_without_redirect(self) -> None:
        cases = load_yaml_file(CAPABILITY_ROUTE_CASES)["cases"]
        row = next(
            case
            for case in cases
            if case["id"] == "capcov-removed-mobile-skill-id-unsupported"
        )
        actual = ROUTING.route(
            row["prompt"],
            main_execution=row["main_execution"],
        )
        self.assertEqual(row["expected"], actual)
        self.assertEqual(
            {
                "path",
                "profile",
                "primary_skill",
                "layer3_skills",
                "review_skill",
            },
            set(actual),
        )
        domain_names = {
            entry["name"]
            for entry in load_yaml_file(
                ROOT / "src" / "registry" / "domain-skills.yaml"
            )["domain_skills"]
        }
        self.assertEqual(set(), set(actual["layer3_skills"]) & domain_names)

    def test_admission_cases_are_explicit_registered_and_jit_routable(self) -> None:
        fixture_path = (
            ROOT / "evals" / "capability-coverage" / "admission-cases.yaml"
        )
        data = load_yaml_file(fixture_path)
        contract_id = "capcov-admission-fixture-contract"
        contract_errors: list[str] = []
        if not isinstance(data, dict):
            self.fail(
                f"[{contract_id}] expected document=mapping; "
                f"actual={type(data).__name__}"
            )
        if data.get("schema_version") != 1:
            contract_errors.append(
                f"[{contract_id}] expected schema_version=1; "
                f"actual={json.dumps(data.get('schema_version'))}"
            )
        if data.get("kind") != "changeforge.capability_admission_cases":
            contract_errors.append(
                f"[{contract_id}] expected kind="
                "changeforge.capability_admission_cases; "
                f"actual={json.dumps(data.get('kind'))}"
            )
        cases = data.get("cases")
        if not isinstance(cases, list):
            self.fail(
                f"[{contract_id}] expected cases=list; "
                f"actual={type(cases).__name__}"
            )
        if not all(isinstance(row, dict) for row in cases):
            bad_types = [
                type(row).__name__
                for row in cases
                if not isinstance(row, dict)
            ]
            contract_errors.append(
                f"[{contract_id}] expected rows=mappings; "
                f"actual={json.dumps(bad_types)}"
            )
        rows = [row for row in cases if isinstance(row, dict)]
        ids = [row.get("id") for row in rows]
        if len(ids) != len(set(ids)):
            contract_errors.append(
                f"[{contract_id}] expected unique_ids={len(ids)}; "
                f"actual={len(set(ids))}"
            )
        row_fields = {
            "id",
            "layer",
            "skill",
            "case_kind",
            "prompt",
            "expected",
            "main_execution",
        }
        expected_fields = {"selected", "primary_skill"}
        triples: list[tuple[object, object, object]] = []
        id_pattern = re.compile(
            r"^capcov-admission-[a-z0-9]+(?:-[a-z0-9]+)*$"
        )
        for index, row in enumerate(rows):
            row_id = (
                row.get("id")
                if isinstance(row.get("id"), str) and row.get("id")
                else f"{contract_id}-row-{index}"
            )
            if set(row) != row_fields:
                contract_errors.append(
                    f"[{row_id}] expected row_fields="
                    f"{json.dumps(sorted(row_fields))}; "
                    f"actual={json.dumps(sorted(row))}"
                )
            for field in ("id", "layer", "skill", "case_kind", "prompt"):
                value = row.get(field)
                if not isinstance(value, str) or not value.strip():
                    contract_errors.append(
                        f"[{row_id}] expected {field}=non-blank-string; "
                        f"actual={json.dumps(value)}"
                    )
            main_errors = VALIDATION_CONTRACTS.validate_main_execution(
                row.get("main_execution")
            )
            if main_errors:
                contract_errors.extend(
                    f"[{row_id}] {error}"
                    for error in main_errors
                )
            if (
                not isinstance(row.get("id"), str)
                or id_pattern.fullmatch(row["id"]) is None
            ):
                contract_errors.append(
                    f"[{row_id}] expected id=closed-lower-kebab; "
                    f"actual={json.dumps(row.get('id'))}"
                )
            expected = row.get("expected")
            if not isinstance(expected, dict):
                contract_errors.append(
                    f"[{row_id}] expected expected=mapping; "
                    f"actual={type(expected).__name__}"
                )
            else:
                if set(expected) != expected_fields:
                    contract_errors.append(
                        f"[{row_id}] expected expected_fields="
                        f"{json.dumps(sorted(expected_fields))}; "
                        f"actual={json.dumps(sorted(expected))}"
                    )
                if type(expected.get("selected")) is not bool:
                    contract_errors.append(
                        f"[{row_id}] expected selected=boolean; "
                        f"actual={json.dumps(expected.get('selected'))}"
                    )
                if not isinstance(
                    expected.get("primary_skill"),
                    str,
                ) or not expected["primary_skill"].strip():
                    contract_errors.append(
                        f"[{row_id}] expected primary_skill="
                        "non-blank-string; "
                        f"actual={json.dumps(expected.get('primary_skill'))}"
                    )
            triples.append(
                (
                    row.get("layer"),
                    row.get("skill"),
                    row.get("case_kind"),
                )
            )
        if len(triples) != len(set(triples)):
            contract_errors.append(
                f"[{contract_id}] expected unique_layer_skill_case_kind="
                f"{len(triples)}; "
                f"actual={len(set(triples))}"
            )
        unexpected_combinations = sorted(
            set(triples)
            - CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
        )
        if unexpected_combinations:
            contract_errors.append(
                f"[{contract_id}] expected combinations=registry-derived-"
                f"subset; actual extra={unexpected_combinations!r}"
            )
        if contract_errors:
            self.fail("\n".join(contract_errors))

        professional_data = load_yaml_file(
            ROOT / "src" / "registry" / "professional-skills.yaml"
        )
        domain_data = load_yaml_file(ROOT / "src" / "registry" / "domain-skills.yaml")
        foundation_data = load_yaml_file(
            ROOT / "src" / "registry" / "foundation-skills.yaml"
        )
        passing_ids, errors = evaluate_admission_evidence(
            root=ROOT,
            professional_registry=professional_data,
            foundation_registry=foundation_data,
            domain_registry=domain_data,
        )
        non_inventory_errors = [
            error
            for error in errors
            if not error.startswith(
                "capability admission evidence: missing obligations="
            )
        ]
        if non_inventory_errors or passing_ids != set(ids):
            missing_passing = sorted(set(ids) - passing_ids)
            self.fail(
                "\n".join(
                    [
                        *non_inventory_errors,
                        f"[{contract_id}] expected passing_ids=current-valid-"
                        "rows; "
                        f"actual missing={json.dumps(missing_passing)}",
                    ]
                )
            )

    def test_t4b_v2_admission_inventory_is_registry_derived(self) -> None:
        case_id = "capcov-r0-authority-derived-inventory"
        professional, foundation, domain = _admission_registries()
        factory = getattr(
            ROUTE_ORACLE,
            "oracle_admission_authority",
            None,
        )
        if not callable(factory):
            self.fail(
                f"[{case_id}-missing-authority-api] expected callable="
                "deterministic_route_oracle.oracle_admission_authority; "
                "actual=missing; capability_test_preimage_sha256="
                f"{R0_ADMISSION_INVENTORY_PREIMAGE_SHA256}"
            )
        authority = factory(
            foundation_registry=copy.deepcopy(foundation),
            professional_registry=copy.deepcopy(professional),
        )
        professional_names = set(authority.primary_task_skills)
        foundation_names = {
            skill
            for selector in authority.foundation_selectors
            for skill in selector.foundations
        }
        domain_names = {
            row["name"] for row in domain["domain_skills"]
        }
        current_domain_names = {
            candidate
            for row in professional["professional_skills"]
            if row.get("routing_family")
            in {"installed-client", "platform-infrastructure"}
            for candidate in row.get("layer3_candidates", [])
            if candidate in domain_names
        }
        self.assertEqual(24, len(professional_names))
        self.assertEqual(69, len(foundation_names))
        self.assertEqual(13, len(domain_names))

        expected_precedence = {
            "professional": (
                "true-conflict",
                "multitask",
                "direct-task",
                "selected",
                "alternate-owner",
            ),
            "foundation": (
                "selected",
                "domain-owned",
                "adjacent",
                "simple",
            ),
            "domain": ("selected", "not-selected"),
        }
        expected_case_kinds = {
            "professional": expected_precedence["professional"],
            "foundation": expected_precedence["foundation"],
            "domain": (
                "explicit",
                "unknown",
                "non-target",
                "cross-platform",
                "language-negative",
                "release-framework-mismatch",
            ),
        }
        expected_names = {
            "professional": professional_names,
            "foundation": foundation_names,
            "domain": current_domain_names,
        }
        self.assertEqual(
            1,
            CAPABILITY_COVERAGE.ADMISSION_SCHEMA_VERSION,
            f"[{case_id}] expected schema_version=1 to remain unchanged",
        )
        errors: list[str] = []
        actual_precedence = getattr(
            CAPABILITY_COVERAGE,
            "ADMISSION_EFFECT_PRECEDENCE",
            None,
        )
        if actual_precedence != expected_precedence:
            errors.append(
                f"[{case_id}] expected effect_precedence="
                f"{expected_precedence!r}; actual={actual_precedence!r}"
            )

        contract = CAPABILITY_COVERAGE.ADMISSION_CASE_CONTRACT
        for layer in ("professional", "foundation", "domain"):
            layer_contract = contract.get(layer)
            actual_names = (
                set(layer_contract.get("skill_prefixes", {}))
                if isinstance(layer_contract, dict)
                else set()
            )
            actual_effects = (
                tuple(layer_contract.get("case_kinds", ()))
                if isinstance(layer_contract, dict)
                else ()
            )
            if actual_names != expected_names[layer]:
                missing_names = expected_names[layer] - actual_names
                extra_names = actual_names - expected_names[layer]
                errors.append(
                    f"[{case_id}] expected {layer}_skills="
                    f"registry-derived-count-{len(expected_names[layer])}; "
                    f"actual_count={len(actual_names)}; "
                    f"missing_count={len(missing_names)}; "
                    f"extra_count={len(extra_names)}"
                )
            if actual_effects != expected_case_kinds[layer]:
                errors.append(
                    f"[{case_id}] expected {layer}_effects="
                    f"{expected_case_kinds[layer]!r}; "
                    f"actual={actual_effects!r}"
                )

        professional_rows = {
            row["name"]: row
            for row in professional["professional_skills"]
            if row["name"] in professional_names
        }
        expected_combinations = {
            (
                "professional",
                skill,
                effect,
            )
            for skill, row in professional_rows.items()
            for effect in (
                expected_precedence["professional"]
                if isinstance(row.get("routing_family"), str)
                and row.get("routing_family")
                else tuple(
                    item
                    for item in expected_precedence["professional"]
                    if item != "true-conflict"
                )
            )
        }
        expected_combinations.update(
            {
                ("foundation", skill, effect)
                for skill in foundation_names
                for effect in expected_precedence["foundation"]
            }
        )
        expected_combinations.update(
            {
                ("domain", skill, case_kind)
                for skill in current_domain_names
                for case_kind in expected_case_kinds["domain"]
            }
        )
        if (
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            != expected_combinations
        ):
            errors.append(
                f"[{case_id}] expected combinations=registry-derived "
                "Skill/effect product; actual=mismatch"
            )
        expected_counts = {
            layer: sum(
                1
                for candidate_layer, _skill, _effect
                in expected_combinations
                if candidate_layer == layer
            )
            for layer in ("professional", "foundation", "domain")
        }
        if expected_counts != {
            "professional": 105,
            "foundation": 276,
            "domain": 48,
        }:
            errors.append(
                f"[{case_id}] expected obligation_counts="
                "{'professional': 105, 'foundation': 276, 'domain': 48}; "
                f"actual={expected_counts!r}"
            )
        fixture = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )
        fixture_rows = fixture["cases"]
        actual_combinations = {
            (row["layer"], row["skill"], row["case_kind"])
            for row in fixture_rows
        }
        missing_obligations = sorted(
            expected_combinations - actual_combinations
        )
        extra_obligations = sorted(
            actual_combinations - expected_combinations
        )
        if extra_obligations:
            errors.append(
                f"[{case_id}] expected extra_obligations=[]; "
                f"actual={extra_obligations!r}"
            )
        special_foundations = {
            "architecture-tradeoff-analysis",
            "test-data-management",
            "authentication-authorization",
            "repeat-failure-analysis",
        }
        missing_arithmetic = {
            "professional": sum(
                1
                for layer, _skill, _effect in missing_obligations
                if layer == "professional"
            ),
            "foundation-ordinary": sum(
                1
                for layer, skill, _effect in missing_obligations
                if layer == "foundation"
                and skill not in special_foundations
            ),
            "foundation-special": sum(
                1
                for layer, skill, _effect in missing_obligations
                if layer == "foundation"
                and skill in special_foundations
            ),
        }
        if len(fixture_rows) != 429 or len(actual_combinations) != 429:
            errors.append(
                f"[{case_id}] expected current_fixture_rows=429 unique; "
                f"actual rows={len(fixture_rows)} "
                f"unique={len(actual_combinations)}"
            )
        if len(expected_combinations) != 429:
            errors.append(
                f"[{case_id}] expected obligation_target=429; "
                f"actual={len(expected_combinations)}"
            )
        if len(missing_obligations) != 0:
            errors.append(
                f"[{case_id}] expected missing_obligations=0; "
                f"actual_count={len(missing_obligations)}"
            )
        if missing_arithmetic != {
            "professional": 0,
            "foundation-ordinary": 0,
            "foundation-special": 0,
        }:
            errors.append(
                f"[{case_id}] expected missing_arithmetic="
                "{'professional': 0, 'foundation-ordinary': 0, "
                "'foundation-special': 0}; "
                f"actual={missing_arithmetic!r}"
            )
        if errors:
            self.fail("\n".join(errors))

    def test_phase2_f01_professional_rows_are_exact_and_anti_labeled(
        self,
    ) -> None:
        case_id = "capcov-phase2-f01-professional-checkpoint"
        fixture_rows = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in fixture_rows
        }
        missing_f01 = sorted(
            PHASE2_F01_PROFESSIONAL_TRIPLES - set(rows_by_triple)
        )
        if missing_f01:
            self.fail(
                f"[{case_id}] expected missing_f01=[]; "
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

        actual_combinations = set(rows_by_triple)
        missing_obligations = (
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            - actual_combinations
        )
        self.assertEqual(429, len(fixture_rows))
        self.assertEqual(429, len(actual_combinations))
        self.assertEqual(set(), actual_combinations - (
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
        ))
        self.assertEqual(0, len(missing_obligations))
        special_foundations = {
            "architecture-tradeoff-analysis",
            "test-data-management",
            "authentication-authorization",
            "repeat-failure-analysis",
        }
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing_obligations
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill not in special_foundations
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill in special_foundations
                ),
            },
        )

        f01_rows = [
            rows_by_triple[triple]
            for triple in sorted(PHASE2_F01_PROFESSIONAL_TRIPLES)
        ]
        prompts = [row["prompt"] for row in f01_rows]
        self.assertEqual(55, len(set(prompts)))
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
        professional, foundation, domain = _admission_registries()
        for row in f01_rows:
            skill = row["skill"]
            case_kind = row["case_kind"]
            row_id = row["id"]
            prompt = row["prompt"]
            with self.subTest(skill=skill, effect=case_kind):
                normalized_prompt = " ".join(prompt.casefold().split())
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )
                self.assertEqual(row_id, row["main_execution"]["task_id"])
                self.assertEqual(
                    f"task:{row_id}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                expected_selected = (
                    case_kind == "selected"
                    or (
                        skill == "engineering-change-analysis"
                        and case_kind == "multitask"
                    )
                )
                self.assertIs(
                    expected_selected,
                    row["expected"]["selected"],
                )

                observed = ROUTE_ORACLE.route_with_trace(
                    prompt,
                    main_execution=row["main_execution"],
                    domain_registry=domain,
                )
                observation = {
                    "main_execution": row["main_execution"],
                    "route_decision": observed["route_decision"],
                    "winner_trace": observed["winner_trace"],
                }
                route_decision = observed["route_decision"]
                route_result = route_decision["route_result"]
                winner_trace = observed["winner_trace"]
                selected = winner_trace["selected_candidate"]
                self.assertEqual(
                    row["expected"]["primary_skill"],
                    route_result["primary_skill"],
                )
                self.assertIs(
                    row["expected"]["selected"],
                    route_result["primary_skill"] == skill,
                )
                classification = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill=skill,
                    declared_case_kind=case_kind,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(
                    case_kind,
                    classification["computed_effect"],
                )
                self.assertEqual([], classification["errors"])

                wrong_kind = (
                    "selected"
                    if case_kind != "selected"
                    else "alternate-owner"
                )
                relabeled = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill=skill,
                    declared_case_kind=wrong_kind,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(case_kind, relabeled["computed_effect"])
                self.assertEqual(
                    [
                        f"declared case_kind {wrong_kind!r} does not match "
                        f"computed effect {case_kind!r}"
                    ],
                    relabeled["errors"],
                )

                if case_kind == "direct-task":
                    self.assertEqual("direct", route_decision["path"])
                    self.assertEqual(
                        "task-agent",
                        route_result["start_profile"],
                    )
                    self.assertNotEqual(skill, route_result["primary_skill"])
                    self.assertNotEqual(skill, route_result["review_skill"])
                    self.assertNotIn(skill, route_result["layer3_skills"])
                elif case_kind == "multitask":
                    self.assertEqual(
                        "merged-route-candidate",
                        selected["candidate_id"],
                    )
                    self.assertEqual(
                        ["multiple-dependent-tasks"],
                        selected["evidence"],
                    )
                    self.assertEqual(
                        [
                            "dependent-task-analysis-early",
                            "dependent-task-analysis-fallback",
                        ],
                        selected["source_candidate_ids"],
                    )
                    self.assertIn(
                        PHASE2_F01_MULTITASK_PROMPT_MARKERS[skill],
                        normalized_prompt,
                    )
                elif case_kind == "alternate-owner":
                    self.assertNotEqual(
                        ["multiple-dependent-tasks"],
                        selected.get("evidence"),
                    )
                    self.assertFalse(
                        {
                            "dependent-task-analysis-early",
                            "dependent-task-analysis-fallback",
                        }.intersection(
                            selected.get("source_candidate_ids", [])
                        )
                    )
                elif case_kind == "true-conflict":
                    self.assertEqual(
                        "implementation-owner-conflict",
                        selected["candidate_id"],
                    )
                    automatic = [
                        candidate
                        for candidate in winner_trace["raw_candidates"]
                        if candidate.get("candidate_type")
                        == "automatic-implementation-owner"
                    ]
                    self.assertEqual(2, len(automatic))
                    self.assertIn(
                        skill,
                        {
                            candidate["primary_skill"]
                            for candidate in automatic
                        },
                    )
                    negative = ROUTE_ORACLE.route_with_trace(
                        PHASE2_F01_CONFLICT_NEGATIVE_PROMPTS[skill],
                        main_execution=_main_execution(
                            f"{case_id}-{skill}-single-owner"
                        ),
                        domain_registry=domain,
                    )
                    self.assertNotEqual(
                        "implementation-owner-conflict",
                        negative["winner_trace"]["selected_candidate"][
                            "candidate_id"
                        ],
                    )

                if (
                    skill == "engineering-artifact-review"
                    and case_kind == "selected"
                ):
                    self.assertEqual("direct", route_decision["path"])
                    self.assertEqual(
                        "review-agent",
                        route_result["start_profile"],
                    )
                    self.assertEqual(
                        "engineering-artifact-review",
                        selected["candidate_id"],
                    )
                    self.assertIn("no actual diff", normalized_prompt)
                if skill == "task-dag-planner" and case_kind == "selected":
                    self.assertEqual("analyzed", route_decision["path"])
                    self.assertEqual(
                        "engineering-artifact-review",
                        route_result["review_skill"],
                    )

    def test_phase2_f02_special_foundation_rows_are_exact_and_anti_triggered(
        self,
    ) -> None:
        case_id = "capcov-phase2-f02-special-foundation-checkpoint"
        fixture_rows = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in fixture_rows
        }
        missing_f02 = sorted(
            PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES - set(rows_by_triple)
        )
        if missing_f02:
            self.fail(
                f"[{case_id}] expected missing_f02=[]; "
                f"actual_missing_count={len(missing_f02)}; "
                f"actual_missing={missing_f02!r}"
            )

        special_names = set(PHASE2_F02_SPECIAL_SELECTOR_IDS)
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

        actual_combinations = set(rows_by_triple)
        missing_obligations = (
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            - actual_combinations
        )
        self.assertEqual(429, len(fixture_rows))
        self.assertEqual(429, len(actual_combinations))
        self.assertEqual(
            set(),
            actual_combinations
            - CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS,
        )
        self.assertEqual(0, len(missing_obligations))
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing_obligations
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing_obligations
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
        prefixes_by_effect: dict[str, set[str]] = {
            effect: set()
            for effect in (
                "selected",
                "domain-owned",
                "adjacent",
                "simple",
            )
        }
        professional, foundation, domain = _admission_registries()
        expected_selected_ids = {
            **PHASE2_F02_SPECIAL_SELECTOR_IDS,
            "repeat-failure-analysis": "review-generic",
        }
        expected_adjacent_primaries = {
            "architecture-tradeoff-analysis": (
                "architecture-impact-reviewer"
            ),
            "test-data-management": "quality-test-gate",
            "authentication-authorization": "security-privacy-gate",
        }
        selected_trigger_phrases = {
            "architecture-tradeoff-analysis": (
                "explicit architecture tradeoff",
            ),
            "test-data-management": (
                "explicit test-data decision",
            ),
            "authentication-authorization": (
                "explicit authentication and authorization handoff decision",
            ),
            "repeat-failure-analysis": (
                "review the actual diff",
                "same repair path",
                "cause",
                "validator",
                "failed twice",
            ),
        }

        for row in f02_rows:
            skill = row["skill"]
            effect = row["case_kind"]
            task_id = row["main_execution"]["task_id"]
            normalized_prompt = " ".join(
                row["prompt"].casefold().split()
            )
            with self.subTest(skill=skill, effect=effect):
                self.assertEqual(
                    (
                        "capcov-admission-foundation-"
                        f"{skill}-{effect}"
                    ),
                    row["id"],
                )
                self.assertEqual(row["id"], task_id)
                self.assertEqual(
                    f"task:{task_id}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    ),
                    normalized_prompt,
                )
                self.assertTrue(
                    any(
                        marker in normalized_prompt
                        for marker in (
                            PHASE2_F02_TARGET_PROMPT_MARKERS[skill]
                        )
                    ),
                    normalized_prompt,
                )
                prefixes_by_effect[effect].add(
                    " ".join(normalized_prompt.split()[:5])
                )

                observed = ROUTE_ORACLE.route_with_trace(
                    row["prompt"],
                    main_execution=row["main_execution"],
                    domain_registry=domain,
                )
                route_decision = observed["route_decision"]
                route_result = route_decision["route_result"]
                winner_trace = observed["winner_trace"]
                selected = winner_trace["selected_candidate"]
                self.assertEqual(
                    row["expected"]["primary_skill"],
                    route_result["primary_skill"],
                )
                self.assertIs(
                    row["expected"]["selected"],
                    skill in route_result["layer3_skills"],
                )
                if effect == "adjacent" and skill in expected_adjacent_primaries:
                    self.assertEqual(
                        expected_adjacent_primaries[skill],
                        row["expected"]["primary_skill"],
                    )
                    self.assertEqual(
                        expected_adjacent_primaries[skill],
                        route_result["primary_skill"],
                    )
                observation = {
                    "main_execution": copy.deepcopy(
                        row["main_execution"]
                    ),
                    "route_decision": route_decision,
                    "winner_trace": winner_trace,
                }
                classified = _classify_t4b_admission_effect(
                    case_id=row["id"],
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=effect,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(
                    {"computed_effect": effect, "errors": []},
                    classified,
                )
                wrong_effect = next(
                    candidate
                    for candidate in (
                        "selected",
                        "domain-owned",
                        "adjacent",
                        "simple",
                    )
                    if candidate != effect
                )
                relabeled = _classify_t4b_admission_effect(
                    case_id=f"{row['id']}-relabeled",
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=wrong_effect,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(effect, relabeled["computed_effect"])
                self.assertEqual(
                    [
                        f"declared case_kind {wrong_effect!r} does not "
                        f"match computed effect {effect!r}"
                    ],
                    relabeled["errors"],
                )

                if effect == "selected":
                    selector_id = PHASE2_F02_SPECIAL_SELECTOR_IDS[skill]
                    self.assertTrue(
                        all(
                            phrase in normalized_prompt
                            for phrase in selected_trigger_phrases[skill]
                        )
                    )
                    self.assertEqual(
                        expected_selected_ids[skill],
                        selected["candidate_id"],
                    )
                    raw_matches = [
                        candidate
                        for candidate in winner_trace["raw_candidates"]
                        if candidate.get("candidate_id") == selector_id
                    ]
                    self.assertEqual(1, len(raw_matches))
                    self.assertEqual(
                        [skill],
                        raw_matches[0]["layer3_skills"],
                    )
                    source_rows = selected[
                        "source_foundation_candidates"
                    ]
                    self.assertEqual(
                        [
                            {
                                "candidate_id": selector_id,
                                "foundations": [skill],
                                "evidence": raw_matches[0]["evidence"],
                                "owner_binding": {
                                    "primary_skill": route_result[
                                        "primary_skill"
                                    ],
                                    "review_skill": route_result[
                                        "review_skill"
                                    ],
                                },
                            }
                        ],
                        source_rows,
                    )
                    self.assertEqual(
                        f"foundation-selector:{selector_id}",
                        raw_matches[0]["evidence"][-1],
                    )

        for effect, prefixes in prefixes_by_effect.items():
            with self.subTest(effect=effect, prompt_template_prefixes=True):
                self.assertEqual(4, len(prefixes))

        for skill, prompt in PHASE2_F02_ANTI_TRIGGER_PROMPTS.items():
            with self.subTest(skill=skill, trigger_removed=True):
                task_id = f"{case_id}-{skill}-trigger-removed"
                observed = ROUTE_ORACLE.route_with_trace(
                    prompt,
                    main_execution=_main_execution(task_id),
                    domain_registry=domain,
                )
                route_result = observed["route_decision"][
                    "route_result"
                ]
                winner_trace = observed["winner_trace"]
                self.assertNotIn(skill, route_result["layer3_skills"])
                selector_id = PHASE2_F02_SPECIAL_SELECTOR_IDS[skill]
                self.assertNotIn(
                    selector_id,
                    {
                        candidate["candidate_id"]
                        for candidate in winner_trace["raw_candidates"]
                    },
                )
                negative_observation = {
                    "main_execution": _main_execution(task_id),
                    "route_decision": observed["route_decision"],
                    "winner_trace": winner_trace,
                }
                negative = _classify_t4b_admission_effect(
                    case_id=task_id,
                    layer="foundation",
                    skill=skill,
                    declared_case_kind="selected",
                    observation=negative_observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual("simple", negative["computed_effect"])
                self.assertEqual(
                    [
                        "declared case_kind 'selected' does not match "
                        "computed effect 'simple'"
                    ],
                    negative["errors"],
                )

    def test_phase2_f03_intake_domain_experience_rows_are_exact_and_live(
        self,
    ) -> None:
        case_id = "capcov-phase2-f03-intake-domain-experience-checkpoint"
        fixture_rows = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in fixture_rows
        }
        missing_f03 = sorted(
            PHASE2_F03_FOUNDATION_TRIPLES - set(rows_by_triple)
        )
        if missing_f03:
            self.fail(
                f"[{case_id}] expected missing_f03=[]; "
                f"actual_missing_count={len(missing_f03)}; "
                f"actual_missing={missing_f03!r}"
            )

        actual_combinations = set(rows_by_triple)
        actual_f03 = {
            triple
            for triple in actual_combinations
            if triple[0] == "foundation"
            and triple[1] in PHASE2_F03_FOUNDATIONS
        }
        self.assertEqual(PHASE2_F03_FOUNDATION_TRIPLES, actual_f03)
        self.assertEqual(28, len(actual_f03))
        self.assertEqual(429, len(fixture_rows))
        self.assertEqual(429, len(actual_combinations))

        predecessor = fixture_rows[:PHASE2_F03_PREDECESSOR_ROW_COUNT]
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

        missing_obligations = (
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            - actual_combinations
        )
        self.assertEqual(
            set(),
            actual_combinations
            - CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS,
        )
        self.assertEqual(0, len(missing_obligations))
        special_names = set(PHASE2_F02_SPECIAL_SELECTOR_IDS)
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing_obligations
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill in special_names
                ),
            },
        )

        old_ordinary = {
            triple
            for triple in actual_combinations
            if triple[0] == "foundation"
            and triple[1] not in special_names
            and triple[1] not in PHASE2_F03_FOUNDATIONS
            and triple[1] not in PHASE2_F04_FOUNDATIONS
            and triple[1] not in PHASE2_A_FOUNDATIONS
        }
        actual_f02 = {
            triple
            for triple in actual_combinations
            if triple[0] == "foundation"
            and triple[1] in special_names
        }
        actual_f01 = {
            triple
            for triple in actual_combinations
            if triple in PHASE2_F01_PROFESSIONAL_TRIPLES
        }
        self.assertEqual(84, len(old_ordinary))
        self.assertEqual(
            PHASE2_F02_SPECIAL_FOUNDATION_TRIPLES,
            actual_f02,
        )
        self.assertEqual(PHASE2_F01_PROFESSIONAL_TRIPLES, actual_f01)
        self.assertEqual(
            48,
            sum(
                1
                for triple in actual_combinations
                if triple[0] == "domain"
            ),
        )

        f03_rows = [
            rows_by_triple[triple]
            for triple in sorted(PHASE2_F03_FOUNDATION_TRIPLES)
        ]
        self.assertEqual(28, len({row["id"] for row in f03_rows}))
        self.assertEqual(28, len({row["prompt"] for row in f03_rows}))
        prefixes_by_effect = {
            effect: set()
            for effect in (
                "selected",
                "domain-owned",
                "adjacent",
                "simple",
            )
        }
        professional, foundation, domain = _admission_registries()
        domain_names = {
            row["name"] for row in domain["domain_skills"]
        }
        forbidden_prompt_labels = (
            "selected",
            "domain-owned",
            "domain owned",
            "adjacent",
            "simple",
        )
        for row in f03_rows:
            skill = row["skill"]
            effect = row["case_kind"]
            normalized_prompt = " ".join(
                row["prompt"].casefold().split()
            )
            with self.subTest(skill=skill, effect=effect):
                self.assertEqual(
                    (
                        "capcov-admission-foundation-"
                        f"{skill}-{effect}"
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
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )
                prefixes_by_effect[effect].add(
                    " ".join(normalized_prompt.split()[:5])
                )

                observed = ROUTE_ORACLE.route_with_trace(
                    row["prompt"],
                    main_execution=row["main_execution"],
                    domain_registry=domain,
                )
                route_decision = observed["route_decision"]
                route_result = route_decision["route_result"]
                winner_trace = observed["winner_trace"]
                selected = winner_trace["selected_candidate"]
                self.assertEqual(
                    PHASE2_F03_EXPECTED_PRIMARIES[(skill, effect)],
                    row["expected"]["primary_skill"],
                )
                self.assertEqual(
                    row["expected"]["primary_skill"],
                    route_result["primary_skill"],
                )
                self.assertIs(
                    row["expected"]["selected"],
                    skill in route_result["layer3_skills"],
                )

                if effect == "selected":
                    self.assertEqual(
                        [skill],
                        route_result["layer3_skills"],
                    )
                    self.assertEqual(
                        PHASE2_F03_SELECTED_CANDIDATE_IDS[skill],
                        selected["candidate_id"],
                    )
                    self.assertTrue(
                        all(
                            phrase in normalized_prompt
                            for phrase in (
                                PHASE2_F03_SELECTED_TRIGGER_PHRASES[skill]
                            )
                        )
                    )
                elif effect == "domain-owned":
                    self.assertNotIn(
                        skill,
                        route_result["layer3_skills"],
                    )
                    self.assertTrue(
                        set(route_result["layer3_skills"])
                        & domain_names
                    )
                elif effect == "adjacent":
                    self.assertEqual(
                        PHASE2_F03_ADJACENT_FOUNDATIONS[skill],
                        route_result["layer3_skills"],
                    )
                else:
                    self.assertEqual([], route_result["layer3_skills"])

                observation = {
                    "main_execution": copy.deepcopy(
                        row["main_execution"]
                    ),
                    "route_decision": route_decision,
                    "winner_trace": winner_trace,
                }
                classified = _classify_t4b_admission_effect(
                    case_id=row["id"],
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=effect,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(
                    {"computed_effect": effect, "errors": []},
                    classified,
                )
                wrong_effect = next(
                    candidate
                    for candidate in (
                        "selected",
                        "domain-owned",
                        "adjacent",
                        "simple",
                    )
                    if candidate != effect
                )
                relabeled = _classify_t4b_admission_effect(
                    case_id=f"{row['id']}-relabeled",
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=wrong_effect,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(effect, relabeled["computed_effect"])
                self.assertEqual(
                    [
                        f"declared case_kind {wrong_effect!r} does not "
                        f"match computed effect {effect!r}"
                    ],
                    relabeled["errors"],
                )

        self.assertTrue(
            all(
                len(prefixes) == len(PHASE2_F03_FOUNDATIONS)
                for prefixes in prefixes_by_effect.values()
            )
        )

        for skill, prompt in PHASE2_F03_TRIGGER_REMOVAL_PROMPTS.items():
            with self.subTest(skill=skill, trigger_removed=True):
                task_id = f"{case_id}-{skill}-trigger-removed"
                observed = ROUTE_ORACLE.route_with_trace(
                    prompt,
                    main_execution=_main_execution(task_id),
                    domain_registry=domain,
                )
                route_result = observed["route_decision"][
                    "route_result"
                ]
                raw_ids = {
                    candidate["candidate_id"]
                    for candidate in observed["winner_trace"][
                        "raw_candidates"
                    ]
                }
                self.assertNotIn(skill, route_result["layer3_skills"])
                self.assertNotIn(
                    PHASE2_F03_SELECTED_CANDIDATE_IDS[skill],
                    raw_ids,
                )

    def test_phase2_f04_structure_review_rows_are_exact_and_live(
        self,
    ) -> None:
        case_id = "capcov-phase2-f04-structure-review-checkpoint"
        fixture_rows = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in fixture_rows
        }
        missing_f04 = sorted(
            PHASE2_F04_FOUNDATION_TRIPLES - set(rows_by_triple)
        )
        if missing_f04:
            self.fail(
                f"[{case_id}] expected missing_f04=[]; "
                f"actual_missing_count={len(missing_f04)}; "
                f"actual_missing={missing_f04!r}"
            )

        actual_combinations = set(rows_by_triple)
        actual_f04 = {
            triple
            for triple in actual_combinations
            if triple[0] == "foundation"
            and triple[1] in PHASE2_F04_FOUNDATIONS
        }
        self.assertEqual(PHASE2_F04_FOUNDATION_TRIPLES, actual_f04)
        self.assertEqual(44, len(actual_f04))
        self.assertEqual(429, len(fixture_rows))
        self.assertEqual(429, len(actual_combinations))

        predecessor = fixture_rows[:PHASE2_F04_PREDECESSOR_ROW_COUNT]
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

        missing_obligations = (
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            - actual_combinations
        )
        self.assertEqual(
            set(),
            actual_combinations
            - CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS,
        )
        self.assertEqual(0, len(missing_obligations))
        special_names = set(PHASE2_F02_SPECIAL_SELECTOR_IDS)
        self.assertEqual(
            {
                "professional": 0,
                "foundation-ordinary": 0,
                "foundation-special": 0,
            },
            {
                "professional": sum(
                    1
                    for layer, _skill, _effect in missing_obligations
                    if layer == "professional"
                ),
                "foundation-ordinary": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill not in special_names
                ),
                "foundation-special": sum(
                    1
                    for layer, skill, _effect in missing_obligations
                    if layer == "foundation"
                    and skill in special_names
                ),
            },
        )
        self.assertEqual(
            {
                "professional": 105,
                "special": 16,
                "pre-f03-ordinary": 84,
                "f03": 28,
                "f04": 44,
                "domain": 48,
            },
            {
                "professional": sum(
                    1
                    for triple in actual_combinations
                    if triple[0] == "professional"
                ),
                "special": sum(
                    1
                    for triple in actual_combinations
                    if triple[0] == "foundation"
                    and triple[1] in special_names
                ),
                "pre-f03-ordinary": sum(
                    1
                    for triple in actual_combinations
                    if triple[0] == "foundation"
                    and triple[1] not in special_names
                    and triple[1] not in PHASE2_F03_FOUNDATIONS
                    and triple[1] not in PHASE2_F04_FOUNDATIONS
                    and triple[1] not in PHASE2_A_FOUNDATIONS
                ),
                "f03": sum(
                    1
                    for triple in actual_combinations
                    if triple in PHASE2_F03_FOUNDATION_TRIPLES
                ),
                "f04": len(actual_f04),
                "domain": sum(
                    1
                    for triple in actual_combinations
                    if triple[0] == "domain"
                ),
            },
        )

        f04_rows = [
            rows_by_triple[triple]
            for triple in sorted(PHASE2_F04_FOUNDATION_TRIPLES)
        ]
        self.assertEqual(44, len({row["id"] for row in f04_rows}))
        self.assertEqual(44, len({row["prompt"] for row in f04_rows}))
        professional, foundation, domain = _admission_registries()
        domain_names = {
            row["name"] for row in domain["domain_skills"]
        }
        forbidden_prompt_labels = (
            "selected",
            "domain-owned",
            "domain owned",
            "adjacent",
            "simple",
        )
        for row in f04_rows:
            skill = row["skill"]
            effect = row["case_kind"]
            normalized_prompt = " ".join(
                row["prompt"].casefold().split()
            )
            with self.subTest(skill=skill, effect=effect):
                self.assertEqual(
                    (
                        "capcov-admission-foundation-"
                        f"{skill}-{effect}"
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
                self.assertFalse(
                    any(
                        label in normalized_prompt
                        for label in forbidden_prompt_labels
                    )
                )

                observed = ROUTE_ORACLE.route_with_trace(
                    row["prompt"],
                    main_execution=row["main_execution"],
                    domain_registry=domain,
                )
                route_decision = observed["route_decision"]
                route_result = route_decision["route_result"]
                winner_trace = observed["winner_trace"]
                selected = winner_trace["selected_candidate"]
                self.assertEqual(
                    row["expected"]["primary_skill"],
                    route_result["primary_skill"],
                )
                self.assertIs(
                    row["expected"]["selected"],
                    skill in route_result["layer3_skills"],
                )

                if effect == "selected":
                    (
                        expected_primary,
                        expected_layer3,
                        expected_candidate,
                    ) = PHASE2_F04_SELECTED_ROUTES[skill]
                    self.assertEqual(
                        expected_primary,
                        row["expected"]["primary_skill"],
                    )
                    self.assertEqual(
                        expected_layer3,
                        route_result["layer3_skills"],
                    )
                    self.assertEqual(
                        expected_candidate,
                        selected["candidate_id"],
                    )
                elif effect == "domain-owned":
                    self.assertEqual(
                        PHASE2_F04_DOMAIN_PRIMARIES[skill],
                        row["expected"]["primary_skill"],
                    )
                    self.assertNotIn(
                        skill,
                        route_result["layer3_skills"],
                    )
                    self.assertTrue(
                        set(route_result["layer3_skills"])
                        & domain_names
                    )
                elif effect == "adjacent":
                    (
                        expected_primary,
                        expected_layer3,
                    ) = PHASE2_F04_ADJACENT_ROUTES[skill]
                    self.assertEqual(
                        expected_primary,
                        row["expected"]["primary_skill"],
                    )
                    self.assertEqual(
                        expected_layer3,
                        route_result["layer3_skills"],
                    )
                else:
                    self.assertEqual(
                        "backend-change-builder",
                        row["expected"]["primary_skill"],
                    )
                    self.assertEqual([], route_result["layer3_skills"])

                observation = {
                    "main_execution": copy.deepcopy(
                        row["main_execution"]
                    ),
                    "route_decision": route_decision,
                    "winner_trace": winner_trace,
                }
                classified = _classify_t4b_admission_effect(
                    case_id=row["id"],
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=effect,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(
                    {"computed_effect": effect, "errors": []},
                    classified,
                )
                wrong_effect = next(
                    candidate
                    for candidate in (
                        "selected",
                        "domain-owned",
                        "adjacent",
                        "simple",
                    )
                    if candidate != effect
                )
                relabeled = _classify_t4b_admission_effect(
                    case_id=f"{row['id']}-relabeled",
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=wrong_effect,
                    observation=observation,
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(effect, relabeled["computed_effect"])
                self.assertEqual(
                    [
                        f"declared case_kind {wrong_effect!r} does not "
                        f"match computed effect {effect!r}"
                    ],
                    relabeled["errors"],
                )

        for skill, prompt in PHASE2_F04_TRIGGER_REMOVAL_PROMPTS.items():
            with self.subTest(skill=skill, trigger_removed=True):
                task_id = f"{case_id}-{skill}-trigger-removed"
                observed = ROUTE_ORACLE.route_with_trace(
                    prompt,
                    main_execution=_main_execution(task_id),
                    domain_registry=domain,
                )
                route_decision = observed["route_decision"]
                route_result = route_decision["route_result"]
                self.assertNotIn(skill, route_result["layer3_skills"])
                negative = _classify_t4b_admission_effect(
                    case_id=task_id,
                    layer="foundation",
                    skill=skill,
                    declared_case_kind="selected",
                    observation={
                        "main_execution": _main_execution(task_id),
                        "route_decision": route_decision,
                        "winner_trace": observed["winner_trace"],
                    },
                    registries=(professional, foundation, domain),
                )
                self.assertNotEqual(
                    "selected",
                    negative["computed_effect"],
                )
                self.assertEqual(
                    [
                        "declared case_kind 'selected' does not match "
                        f"computed effect {negative['computed_effect']!r}"
                    ],
                    negative["errors"],
                )

    def test_repair10_a_batch_admission_rows_are_exact_and_live(
        self,
    ) -> None:
        case_id = "capcov-repair10-a-batch-admission-checkpoint"
        fixture_rows = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )["cases"]
        rows_by_triple = {
            (row["layer"], row["skill"], row["case_kind"]): row
            for row in fixture_rows
        }
        actual_combinations = set(rows_by_triple)
        actual_a = {
            triple
            for triple in actual_combinations
            if triple in PHASE2_A_FOUNDATION_TRIPLES
        }
        self.assertEqual(429, len(fixture_rows))
        self.assertEqual(429, len(actual_combinations))
        self.assertEqual(PHASE2_A_FOUNDATION_TRIPLES, actual_a)
        self.assertEqual(104, len(actual_a))
        self.assertEqual(
            CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS,
            actual_combinations,
        )
        self.assertEqual(
            {
                "professional": 105,
                "foundation": 276,
                "domain": 48,
            },
            {
                layer: sum(
                    1
                    for row in fixture_rows
                    if row["layer"] == layer
                )
                for layer in ("professional", "foundation", "domain")
            },
        )

        predecessor = fixture_rows[:PHASE2_A_PREDECESSOR_ROW_COUNT]
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
        expected_sequence = [
            ("foundation", skill, effect)
            for _group, _owner, _review, foundations in PHASE2_A_GROUPS
            for skill in foundations
            for effect in (
                "selected",
                "domain-owned",
                "adjacent",
                "simple",
            )
        ]
        current_sequence = [
            *expected_sequence,
            *(
                ("foundation", skill, effect)
                for skill in (
                    "configuration-runtime-policy",
                    "dependency-vulnerability-scanning",
                    "technology-stack-selection",
                )
                for effect in (
                    "selected",
                    "domain-owned",
                    "adjacent",
                    "simple",
                )
            ),
        ]
        self.assertEqual(
            current_sequence,
            [
                (row["layer"], row["skill"], row["case_kind"])
                for row in fixture_rows[PHASE2_A_PREDECESSOR_ROW_COUNT:]
            ],
        )

        professional, foundation, domain = _admission_registries()
        domain_names = {
            row["name"] for row in domain["domain_skills"]
        }
        group_routes = {
            skill: (owner, review)
            for _group, owner, review, foundations in PHASE2_A_GROUPS
            for skill in foundations
        }
        forbidden_prompt_labels = (
            "selected",
            "domain-owned",
            "domain owned",
            "adjacent",
            "simple",
        )
        for triple in expected_sequence:
            _layer, skill, effect = triple
            (
                expected_group,
                expected_prompt,
                expected_primary,
                expected_review,
                expected_layer3,
                expected_winner,
                expected_target_source_ids,
            ) = PHASE2_A_CASES[(skill, effect)]
            row = rows_by_triple[triple]
            with self.subTest(skill=skill, effect=effect):
                self.assertEqual(expected_group, next(
                    group_id
                    for group_id, _owner, _review, foundations
                    in PHASE2_A_GROUPS
                    if skill in foundations
                ))
                self.assertEqual(expected_prompt, row["prompt"])
                self.assertEqual(
                    (
                        "capcov-admission-foundation-"
                        f"{skill}-{effect}"
                    ),
                    row["id"],
                )
                self.assertEqual(row["id"], row["main_execution"]["task_id"])
                self.assertEqual(
                    f"task:{row['id']}:routing-api",
                    row["main_execution"]["level_basis"][
                        "trigger_evaluations"
                    ][0]["source_anchor"],
                )
                self.assertFalse(
                    any(
                        label in " ".join(
                            row["prompt"].casefold().split()
                        )
                        for label in forbidden_prompt_labels
                    )
                )
                self.assertEqual(
                    expected_primary,
                    row["expected"]["primary_skill"],
                )
                self.assertIs(
                    effect == "selected",
                    row["expected"]["selected"],
                )

                observed = ROUTE_ORACLE.route_with_trace(
                    row["prompt"],
                    main_execution=row["main_execution"],
                    domain_registry=domain,
                )
                route_decision = observed["route_decision"]
                route_result = route_decision["route_result"]
                winner_trace = observed["winner_trace"]
                selected = winner_trace["selected_candidate"]
                self.assertEqual(
                    expected_primary,
                    route_result["primary_skill"],
                )
                self.assertEqual(
                    expected_review,
                    route_result["review_skill"],
                )
                self.assertEqual(
                    list(expected_layer3),
                    route_result["layer3_skills"],
                )
                self.assertEqual(
                    expected_winner,
                    selected["candidate_id"],
                )
                target_sources = [
                    source
                    for source in selected.get(
                        "source_foundation_candidates",
                        [],
                    )
                    if skill in source["foundations"]
                ]
                self.assertEqual(
                    list(expected_target_source_ids),
                    [
                        source["candidate_id"]
                        for source in target_sources
                    ],
                )
                for source in target_sources:
                    self.assertEqual(
                        {
                            "primary_skill": route_result["primary_skill"],
                            "review_skill": route_result["review_skill"],
                        },
                        source["owner_binding"],
                    )
                    self.assertTrue(
                        source["evidence"][-1].startswith(
                            "foundation-selector:"
                        )
                    )
                self.assertIs(
                    effect == "selected",
                    skill in route_result["layer3_skills"],
                )
                self.assertIs(
                    effect == "selected",
                    bool(target_sources),
                )
                if effect == "domain-owned":
                    self.assertTrue(
                        set(route_result["layer3_skills"])
                        & domain_names
                    )
                elif effect == "adjacent":
                    self.assertTrue(route_result["layer3_skills"])
                    self.assertTrue(
                        set(route_result["layer3_skills"])
                        & PHASE2_A_FOUNDATIONS
                        or set(route_result["layer3_skills"])
                        - domain_names
                    )
                elif effect == "simple":
                    self.assertEqual([], route_result["layer3_skills"])

                classified = _classify_t4b_admission_effect(
                    case_id=row["id"],
                    layer="foundation",
                    skill=skill,
                    declared_case_kind=effect,
                    observation={
                        "main_execution": copy.deepcopy(
                            row["main_execution"]
                        ),
                        "route_decision": route_decision,
                        "winner_trace": winner_trace,
                    },
                    registries=(professional, foundation, domain),
                )
                self.assertEqual(
                    {"computed_effect": effect, "errors": []},
                    classified,
                )

                if effect == "selected":
                    owner, review = group_routes[skill]
                    self.assertEqual(
                        PHASE2_A_SELECTED_PRIMARY_OVERRIDES.get(
                            skill,
                            owner,
                        ),
                        route_result["primary_skill"],
                    )
                    self.assertEqual(
                        review,
                        route_result["review_skill"],
                    )

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

    def test_t4b_v2_effect_precedence_and_case_kind_is_declarative(
        self,
    ) -> None:
        case_id = "capcov-t4b-v2-effect-precedence-declarative-kind"
        if not callable(
            getattr(CAPABILITY_COVERAGE, "_classify_admission_effect", None)
        ):
            self.fail(
                f"[{case_id}] expected callable=_classify_admission_effect; "
                "actual=missing"
            )
        true_conflict = {
            "main_execution": _main_execution(
                "capcov-t4b-v2-effect-precedence-conflict"
            )
        }
        true_conflict.update(
            _trace(
                "Implement an accepted repository-owned generator and "
                "Android installed-client behavior change.",
                task_id="capcov-t4b-v2-effect-precedence-conflict",
            )
        )
        professional_cases = {
            "true-conflict": true_conflict,
            "multitask": _admission_observation(
                layer="professional",
                skill="installed-client-change-builder",
                case_kind="multitask",
            ),
            "direct-task": _admission_observation(
                layer="professional",
                skill="installed-client-change-builder",
                case_kind="direct-task",
            ),
            "selected": _admission_observation(
                layer="professional",
                skill="installed-client-change-builder",
                case_kind="selected",
            ),
            "alternate-owner": _admission_observation(
                layer="professional",
                skill="installed-client-change-builder",
                case_kind="alternate-owner",
            ),
        }
        for expected_effect, observation in professional_cases.items():
            with self.subTest(layer="professional", effect=expected_effect):
                result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill="installed-client-change-builder",
                    declared_case_kind=expected_effect,
                    observation=observation,
                )
                self.assertEqual(expected_effect, result["computed_effect"])
                self.assertEqual([], result["errors"])

        foundation_cases = {
            "selected": "selected",
            "domain-owned": "domain-owned",
            "adjacent": "adjacent",
            "simple": "simple",
        }
        for expected_effect, source_kind in foundation_cases.items():
            with self.subTest(layer="foundation", effect=expected_effect):
                observation = _admission_observation(
                    layer="foundation",
                    skill="client-lifecycle-state-restoration",
                    case_kind=source_kind,
                )
                result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="foundation",
                    skill="client-lifecycle-state-restoration",
                    declared_case_kind=expected_effect,
                    observation=observation,
                )
                self.assertEqual(expected_effect, result["computed_effect"])
                self.assertEqual([], result["errors"])

        selected_observation = professional_cases["selected"]
        relabeled = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="installed-client-change-builder",
            declared_case_kind="alternate-owner",
            observation=selected_observation,
        )
        self.assertEqual("selected", relabeled["computed_effect"])
        self.assertEqual(
            [
                "declared case_kind 'alternate-owner' does not match "
                "computed effect 'selected'"
            ],
            relabeled["errors"],
        )

    def test_t4b_v2_strict_multitask_precedes_selected_owner(
        self,
    ) -> None:
        case_id = "capcov-t4b-v2-strict-multitask-precedes-selected"

        def observation(
            label: str,
            prompt: str,
        ) -> dict[str, object]:
            task_id = f"{case_id}-{label}"
            actual = {"main_execution": _main_execution(task_id)}
            actual.update(_trace(prompt, task_id=task_id))
            return actual

        ordinary = observation(
            "ordinary",
            "Using repository source evidence, explain which module owns "
            "this change; acceptance is already measurable and unchanged.",
        )
        ordinary_result = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="engineering-change-analysis",
            declared_case_kind="selected",
            observation=ordinary,
        )
        self.assertEqual("selected", ordinary_result["computed_effect"])
        self.assertEqual([], ordinary_result["errors"])

        generic_multiple = observation(
            "generic-multiple",
            "Analyze multiple tasks for one repository-owned change with no "
            "dependent task decomposition.",
        )
        generic_result = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="engineering-change-analysis",
            declared_case_kind="selected",
            observation=generic_multiple,
        )
        self.assertEqual("selected", generic_result["computed_effect"])
        self.assertEqual([], generic_result["errors"])
        generic_relabel = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="engineering-change-analysis",
            declared_case_kind="multitask",
            observation=generic_multiple,
        )
        self.assertEqual("selected", generic_relabel["computed_effect"])
        self.assertEqual(
            [
                "declared case_kind 'multitask' does not match computed "
                "effect 'selected'"
            ],
            generic_relabel["errors"],
        )

        strict_multitask = observation(
            "strict",
            "Plan multiple dependent tasks for an Android screen and a "
            "backend API change.",
        )
        selected = strict_multitask["winner_trace"]["selected_candidate"]
        self.assertEqual("merged-route-candidate", selected["candidate_id"])
        self.assertEqual(
            ["multiple-dependent-tasks"],
            selected["evidence"],
        )
        self.assertEqual(
            [
                "dependent-task-analysis-early",
                "dependent-task-analysis-fallback",
            ],
            selected["source_candidate_ids"],
        )
        strict_result = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="engineering-change-analysis",
            declared_case_kind="multitask",
            observation=strict_multitask,
        )
        self.assertEqual("multitask", strict_result["computed_effect"])
        self.assertEqual([], strict_result["errors"])

    def test_t4b_g2_professional_effects_follow_actual_route_semantics(
        self,
    ) -> None:
        case_id = "capcov-t4b-g2-professional-effect-semantics"

        def observation(
            label: str,
            prompt: str,
        ) -> dict[str, object]:
            task_id = f"{case_id}-{label}"
            actual = {"main_execution": _main_execution(task_id)}
            actual.update(_trace(prompt, task_id=task_id))
            return actual

        def assert_target_absent(
            actual: dict[str, object],
            target: str,
        ) -> None:
            route_result = actual["route_decision"]["route_result"]
            self.assertNotEqual(target, route_result["primary_skill"])
            self.assertNotEqual(target, route_result["review_skill"])
            self.assertNotIn(target, route_result["layer3_skills"])

        review_selected = observation(
            "review-selected",
            "Analyze release and rollback risk for high-risk multiple tasks "
            "after the architecture, module boundaries, and dependency graph "
            "are accepted and fixed.",
        )
        selected_result = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="high-risk-design-review",
            declared_case_kind="selected",
            observation=review_selected,
        )
        self.assertEqual("selected", selected_result["computed_effect"])
        self.assertEqual([], selected_result["errors"])

        automatic_direct = observation(
            "automatic-direct",
            "Implement an accepted backend service business-rule change.",
        )
        self.assertEqual(
            "automatic-implementation-owner",
            automatic_direct["winner_trace"]["selected_candidate"][
                "candidate_type"
            ],
        )
        assert_target_absent(
            automatic_direct,
            "change-documentation-gate",
        )
        direct_result = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="change-documentation-gate",
            declared_case_kind="direct-task",
            observation=automatic_direct,
        )
        self.assertEqual("direct-task", direct_result["computed_effect"])
        self.assertEqual([], direct_result["errors"])

        documentation_merge = observation(
            "documentation-merge",
            "Update migration documentation without changing runtime "
            "behavior.",
        )
        self.assertEqual(
            "merged-route",
            documentation_merge["winner_trace"]["selected_candidate"][
                "candidate_type"
            ],
        )
        documentation_selected = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="change-documentation-gate",
            declared_case_kind="selected",
            observation=documentation_merge,
        )
        self.assertEqual(
            "selected",
            documentation_selected["computed_effect"],
        )
        self.assertEqual([], documentation_selected["errors"])
        assert_target_absent(
            documentation_merge,
            "high-risk-design-review",
        )
        documentation_direct = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="high-risk-design-review",
            declared_case_kind="direct-task",
            observation=documentation_merge,
        )
        self.assertEqual(
            "direct-task",
            documentation_direct["computed_effect"],
        )
        self.assertEqual([], documentation_direct["errors"])

        dependent_tasks = observation(
            "dependent-tasks",
            "Plan multiple dependent tasks for an Android screen and a "
            "backend API change.",
        )
        self.assertEqual(
            [
                "dependent-task-analysis-early",
                "dependent-task-analysis-fallback",
            ],
            dependent_tasks["winner_trace"]["selected_candidate"][
                "source_candidate_ids"
            ],
        )
        assert_target_absent(
            dependent_tasks,
            "change-documentation-gate",
        )
        dependent_result = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="change-documentation-gate",
            declared_case_kind="multitask",
            observation=dependent_tasks,
        )
        self.assertEqual("multitask", dependent_result["computed_effect"])
        self.assertEqual([], dependent_result["errors"])

        accepted_task_dag = observation(
            "accepted-task-dag",
            "Using the accepted Engineering Brief, produce the explicit "
            "Task DAG and review boundaries.",
        )
        self.assertEqual(
            "accepted-brief-task-dag",
            accepted_task_dag["winner_trace"]["selected_candidate"][
                "candidate_id"
            ],
        )
        for target in (
            "engineering-change-analysis",
            "ai-code-review-refactor",
        ):
            with self.subTest(multitask_target=target):
                assert_target_absent(accepted_task_dag, target)
                task_dag_result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill=target,
                    declared_case_kind="multitask",
                    observation=accepted_task_dag,
                )
                self.assertEqual(
                    "multitask",
                    task_dag_result["computed_effect"],
                )
                self.assertEqual([], task_dag_result["errors"])

        multitask_mutations: list[
            tuple[str, dict[str, object], str]
        ] = []
        dependent_duplicate = copy.deepcopy(dependent_tasks)
        dependent_duplicate["winner_trace"]["raw_candidates"].append(
            copy.deepcopy(
                dependent_duplicate["winner_trace"]["raw_candidates"][0]
            )
        )
        multitask_mutations.append(
            (
                "dependent-duplicate-raw",
                dependent_duplicate,
                "change-documentation-gate",
            )
        )
        dependent_extra = copy.deepcopy(dependent_tasks)
        extra_candidate = copy.deepcopy(
            dependent_extra["winner_trace"]["raw_candidates"][0]
        )
        extra_candidate["candidate_id"] = "dependent-task-analysis-extra"
        extra_candidate["rule_id"] = "dependent-task-analysis-extra"
        dependent_extra["winner_trace"]["raw_candidates"].append(
            extra_candidate
        )
        multitask_mutations.append(
            (
                "dependent-extra-raw",
                dependent_extra,
                "change-documentation-gate",
            )
        )
        dependent_precedence = copy.deepcopy(dependent_tasks)
        dependent_precedence["winner_trace"]["raw_candidates"][0][
            "precedence"
        ] += 1
        multitask_mutations.append(
            (
                "dependent-forged-precedence",
                dependent_precedence,
                "change-documentation-gate",
            )
        )
        accepted_rule = copy.deepcopy(accepted_task_dag)
        accepted_rule["winner_trace"]["raw_candidates"][0]["rule_id"] = (
            "forged-accepted-task-dag"
        )
        multitask_mutations.append(
            (
                "accepted-forged-raw-rule",
                accepted_rule,
                "engineering-change-analysis",
            )
        )
        accepted_precedence = copy.deepcopy(accepted_task_dag)
        accepted_precedence["winner_trace"]["raw_candidates"][0][
            "precedence"
        ] += 1
        multitask_mutations.append(
            (
                "accepted-forged-raw-precedence",
                accepted_precedence,
                "engineering-change-analysis",
            )
        )
        selected_raw_mismatch = copy.deepcopy(dependent_tasks)
        selected_raw_mismatch["winner_trace"]["selected_candidate"][
            "stage"
        ] = "forged-planning-stage"
        multitask_mutations.append(
            (
                "dependent-selected-raw-mismatch",
                selected_raw_mismatch,
                "change-documentation-gate",
            )
        )
        for label, mutated, target in multitask_mutations:
            with self.subTest(multitask_mutation=label):
                mutation_result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill=target,
                    declared_case_kind="multitask",
                    observation=mutated,
                )
                self.assertNotEqual(
                    "multitask",
                    mutation_result["computed_effect"],
                )
                self.assertTrue(mutation_result["errors"])

    def test_t4b_g2_accepted_brief_selector_enriched_trace_is_exact(
        self,
    ) -> None:
        case_id = "capcov-t4b-g2-accepted-brief-selector-enriched"
        task_id = f"{case_id}-task"
        observation = {
            "main_execution": _main_execution(task_id),
        }
        observation.update(
            _trace(
                "Using the accepted Engineering Brief, produce the explicit "
                "Task DAG and review boundaries.",
                task_id=task_id,
            )
        )
        decision = observation["route_decision"]
        trace = observation["winner_trace"]
        canonical_source = {
            "candidate_id": "accepted-brief-task-dag",
            "foundations": ["task-dag-decomposition"],
            "evidence": [
                "accepted-engineering-brief",
                "explicit-task-dag",
                "foundation-selector:accepted-brief-task-dag",
            ],
            "owner_binding": {
                "primary_skill": "task-dag-planner",
                "review_skill": "engineering-artifact-review",
            },
        }
        canonical_raw = {
            "candidate_id": "accepted-brief-task-dag",
            "candidate_type": "explicit-route",
            "candidate_layer3_context": {
                "kind": "fixed",
                "domain_requests": [],
                "foundation_requests": ["task-dag-decomposition"],
            },
            "eligible_domain_layer3_skills": [],
            "eligible_foundation_layer3_skills": [
                "task-dag-decomposition"
            ],
            "eligible_layer3_skills": ["task-dag-decomposition"],
            "evidence": [
                "accepted-engineering-brief",
                "explicit-task-dag",
                "foundation-selector:accepted-brief-task-dag",
            ],
            "layer3_overflow": False,
            "layer3_skills": ["task-dag-decomposition"],
            "path": "analyzed",
            "precedence": 5,
            "precedence_class": "analysis-artifact",
            "primary_skill": "task-dag-planner",
            "profile": "analysis-agent",
            "reserved_domain_capacity": 0,
            "review_skill": "engineering-artifact-review",
            "rule_id": "accepted-brief-task-dag",
            "semantic_atoms": [],
            "source_foundation_candidates": [canonical_source],
            "stage": "planning",
        }
        canonical_selected = {
            **canonical_raw,
            "reason": "highest-semantic-precedence",
            "source_candidate_ids": ["accepted-brief-task-dag"],
        }
        self.assertEqual([canonical_raw], trace["raw_candidates"])
        self.assertEqual(canonical_selected, trace["selected_candidate"])
        self.assertEqual(
            ["task-dag-decomposition"],
            decision["route_result"]["layer3_skills"],
        )

        assessment = getattr(
            CAPABILITY_COVERAGE,
            "_admission_multitask_trace_assessment",
            None,
        )
        if not callable(assessment):
            self.fail(
                f"[{case_id}] expected callable="
                "_admission_multitask_trace_assessment; actual=missing"
            )

        def assess(
            current: dict[str, object],
        ) -> tuple[bool, list[str]]:
            return assessment(
                route_decision=current["route_decision"],
                winner_trace=current["winner_trace"],
                owner_authorized_domains=set(),
            )

        self.assertEqual((True, []), assess(observation))
        for target in (
            "engineering-change-analysis",
            "ai-code-review-refactor",
        ):
            with self.subTest(canonical_target=target):
                result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill=target,
                    declared_case_kind="multitask",
                    observation=observation,
                )
                self.assertEqual("multitask", result["computed_effect"])
                self.assertEqual([], result["errors"])

        raw_error = (
            "accepted-Brief multitask raw trace must exactly equal the "
            "single canonical planner candidate"
        )
        selected_error = (
            "accepted-Brief multitask selected trace must exactly bind the "
            "canonical raw planner candidate"
        )

        def assert_rejected(
            *,
            label: str,
            current: dict[str, object],
            expected_error: str,
        ) -> None:
            with self.subTest(mutation=label):
                valid, errors = assess(current)
                self.assertFalse(valid)
                self.assertIn(expected_error, errors)

        raw_selector = copy.deepcopy(observation)
        raw_selector["winner_trace"]["raw_candidates"][0]["evidence"][-1] = (
            "foundation-selector:forged"
        )
        assert_rejected(
            label="raw-selector-terminal",
            current=raw_selector,
            expected_error=raw_error,
        )

        selected_selector = copy.deepcopy(observation)
        selected_selector["winner_trace"]["selected_candidate"]["evidence"][
            -1
        ] = "foundation-selector:forged"
        assert_rejected(
            label="selected-selector-terminal",
            current=selected_selector,
            expected_error=selected_error,
        )

        raw_semantic_atoms = copy.deepcopy(observation)
        raw_semantic_atoms["winner_trace"]["raw_candidates"][0][
            "semantic_atoms"
        ] = ["forged-semantic-atom"]
        assert_rejected(
            label="raw-semantic-atoms",
            current=raw_semantic_atoms,
            expected_error=raw_error,
        )

        selected_semantic_atoms = copy.deepcopy(observation)
        selected_semantic_atoms["winner_trace"]["selected_candidate"][
            "semantic_atoms"
        ] = ["forged-semantic-atom"]
        assert_rejected(
            label="selected-semantic-atoms",
            current=selected_semantic_atoms,
            expected_error=selected_error,
        )

        raw_source = copy.deepcopy(observation)
        raw_source["winner_trace"]["raw_candidates"][0][
            "source_foundation_candidates"
        ][0]["candidate_id"] = "forged-selector"
        assert_rejected(
            label="raw-source-foundation-candidate",
            current=raw_source,
            expected_error=raw_error,
        )

        selected_source = copy.deepcopy(observation)
        selected_source["winner_trace"]["selected_candidate"][
            "source_foundation_candidates"
        ][0]["owner_binding"]["review_skill"] = "ai-code-review-refactor"
        assert_rejected(
            label="selected-source-foundation-candidate",
            current=selected_source,
            expected_error=selected_error,
        )

        selected_divergence = copy.deepcopy(observation)
        selected_divergence["winner_trace"]["selected_candidate"]["stage"] = (
            "forged-stage"
        )
        assert_rejected(
            label="raw-selected-divergence",
            current=selected_divergence,
            expected_error=selected_error,
        )

        for surface, expected_error in (
            ("raw", raw_error),
            ("selected", selected_error),
        ):
            surplus = copy.deepcopy(observation)
            candidate = (
                surplus["winner_trace"]["raw_candidates"][0]
                if surface == "raw"
                else surplus["winner_trace"]["selected_candidate"]
            )
            candidate["surplus"] = "forged"
            assert_rejected(
                label=f"{surface}-surplus-field",
                current=surplus,
                expected_error=expected_error,
            )

    def test_t4b_g2_multitask_trace_layer3_binding_is_exact(self) -> None:
        case_id = "capcov-t4b-g2-multitask-layer3-binding"
        fixture_expectations = {
            "capcov-admission-prof-installed-client-multitask": [
                "android-platform-extension"
            ],
            "capcov-admission-prof-platform-infrastructure-multitask": [],
            "capcov-admission-prof-repository-tooling-multitask": [],
            "capcov-admission-prof-incident-response-multitask": [],
        }
        fixture_rows = {
            row["id"]: row
            for row in load_yaml_file(
                ROOT / "evals/capability-coverage/admission-cases.yaml"
            )["cases"]
            if row.get("id") in fixture_expectations
        }
        self.assertEqual(set(fixture_expectations), set(fixture_rows))
        source_candidate_ids = [
            "dependent-task-analysis-early",
            "dependent-task-analysis-fallback",
        ]
        expected_layer3_fields = (
            "eligible_foundation_layer3_skills",
            "eligible_domain_layer3_skills",
            "eligible_layer3_skills",
            "reserved_domain_capacity",
            "layer3_overflow",
        )
        self.assertEqual(
            expected_layer3_fields,
            ROUTE_ORACLE.ROUTE_CANDIDATE_LAYER3_FIELDS,
        )
        projection_fields = (
            "candidate_layer3_context",
            *expected_layer3_fields,
            "layer3_skills",
        )
        fixture_observations: dict[str, dict[str, object]] = {}
        for fixture_id, expected_layer3 in fixture_expectations.items():
            with self.subTest(positive_fixture=fixture_id):
                row = fixture_rows[fixture_id]
                observed = ROUTE_ORACLE.route_with_trace(
                    row["prompt"],
                    main_execution=row["main_execution"],
                )
                current = {
                    "main_execution": copy.deepcopy(row["main_execution"]),
                    "route_decision": observed["route_decision"],
                    "winner_trace": observed["winner_trace"],
                }
                fixture_observations[fixture_id] = current
                decision = current["route_decision"]
                trace = current["winner_trace"]
                raw_candidates = trace["raw_candidates"]
                selected = trace["selected_candidate"]
                authority_layer3 = [
                    candidate["skill"]
                    for candidate in decision["selection_evidence"][
                        "layer3_candidates"
                    ]
                    if candidate["eligible"] is True
                ]
                self.assertEqual(expected_layer3, authority_layer3)
                self.assertEqual(
                    expected_layer3,
                    decision["route_result"]["layer3_skills"],
                )
                self.assertEqual(
                    source_candidate_ids,
                    [
                        candidate["candidate_id"]
                        for candidate in raw_candidates
                    ],
                )
                self.assertEqual(
                    source_candidate_ids,
                    selected["source_candidate_ids"],
                )
                expected_context = {
                    "kind": "fixed",
                    "domain_requests": expected_layer3,
                    "foundation_requests": [],
                }
                for candidate in [*raw_candidates, selected]:
                    self.assertEqual(
                        expected_context,
                        candidate["candidate_layer3_context"],
                    )
                    self.assertEqual(
                        [],
                        candidate["eligible_foundation_layer3_skills"],
                    )
                    self.assertEqual(
                        expected_layer3,
                        candidate["eligible_domain_layer3_skills"],
                    )
                    self.assertEqual(
                        expected_layer3,
                        candidate["eligible_layer3_skills"],
                    )
                    self.assertEqual(
                        len(expected_layer3),
                        candidate["reserved_domain_capacity"],
                    )
                    self.assertIs(
                        False,
                        candidate["layer3_overflow"],
                    )
                    self.assertEqual(
                        expected_layer3,
                        candidate["layer3_skills"],
                    )
                result = _classify_t4b_admission_effect(
                    case_id=fixture_id,
                    layer=row["layer"],
                    skill=row["skill"],
                    declared_case_kind=row["case_kind"],
                    observation=current,
                )
                self.assertEqual("multitask", result["computed_effect"])
                self.assertEqual([], result["errors"])

        dependent_tasks = fixture_observations[
            "capcov-admission-prof-installed-client-multitask"
        ]
        accepted_task_id = f"{case_id}-accepted-task-dag"
        accepted_task_dag = {
            "main_execution": _main_execution(accepted_task_id)
        }
        accepted_task_dag.update(
            _trace(
                "Using the accepted Engineering Brief, produce the explicit "
                "Task DAG and review boundaries.",
                task_id=accepted_task_id,
            )
        )
        accepted_trace = accepted_task_dag["winner_trace"]
        self.assertEqual(1, len(accepted_trace["raw_candidates"]))
        self.assertEqual(
            ["task-dag-decomposition"],
            accepted_trace["raw_candidates"][0]["layer3_skills"],
        )
        self.assertEqual(
            ["task-dag-decomposition"],
            accepted_trace["selected_candidate"]["layer3_skills"],
        )
        with self.subTest(positive_fixture="accepted-brief-task-dag"):
            accepted_result = _classify_t4b_admission_effect(
                case_id=case_id,
                layer="professional",
                skill="engineering-change-analysis",
                declared_case_kind="multitask",
                observation=accepted_task_dag,
            )
            self.assertEqual("multitask", accepted_result["computed_effect"])
            self.assertEqual([], accepted_result["errors"])

        def assert_multitask_rejected(
            *,
            label: str,
            mutated: dict[str, object],
            target: str,
            registries: tuple[dict, dict, dict] | None = None,
        ) -> None:
            with self.subTest(multitask_layer3_mutation=label):
                mutation_result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill=target,
                    declared_case_kind="multitask",
                    observation=mutated,
                    registries=registries,
                )
                self.assertNotEqual(
                    "multitask",
                    mutation_result["computed_effect"],
                )
                self.assertTrue(mutation_result["errors"])

        def changed_projection_value(
            field: str,
            current: object,
        ) -> object:
            if field == "candidate_layer3_context":
                assert isinstance(current, dict)
                changed = copy.deepcopy(current)
                changed["foundation_requests"] = [
                    *changed["foundation_requests"],
                    "release-rollback",
                ]
                return changed
            if field == "reserved_domain_capacity":
                assert isinstance(current, int)
                return current + 1
            if field == "layer3_overflow":
                assert isinstance(current, bool)
                return not current
            assert isinstance(current, list)
            addition = (
                "cloud-platform-extension"
                if field == "eligible_domain_layer3_skills"
                else "release-rollback"
            )
            return [*current, addition]

        for surface in ("raw", "selected"):
            for field in projection_fields:
                mutated = copy.deepcopy(dependent_tasks)
                candidate = (
                    mutated["winner_trace"]["raw_candidates"][0]
                    if surface == "raw"
                    else mutated["winner_trace"]["selected_candidate"]
                )
                candidate[field] = changed_projection_value(
                    field,
                    candidate[field],
                )
                assert_multitask_rejected(
                    label=(
                        "capcov-admission-prof-installed-client-multitask-"
                        f"{surface}-{field}"
                    ),
                    mutated=mutated,
                    target="installed-client-change-builder",
                )

        for surface in ("raw", "selected"):
            for field in projection_fields:
                mutated = copy.deepcopy(accepted_task_dag)
                candidate = (
                    mutated["winner_trace"]["raw_candidates"][0]
                    if surface == "raw"
                    else mutated["winner_trace"]["selected_candidate"]
                )
                del candidate[field]
                assert_multitask_rejected(
                    label=f"accepted-brief-{surface}-missing-{field}",
                    mutated=mutated,
                    target="engineering-change-analysis",
                )

        for label, source_ids in (
            (
                "source-candidate-ids-reordered",
                list(reversed(source_candidate_ids)),
            ),
            (
                "source-candidate-ids-duplicated",
                [source_candidate_ids[0], source_candidate_ids[0]],
            ),
        ):
            mutated = copy.deepcopy(dependent_tasks)
            mutated["winner_trace"]["selected_candidate"][
                "source_candidate_ids"
            ] = source_ids
            assert_multitask_rejected(
                label=label,
                mutated=mutated,
                target="installed-client-change-builder",
            )

        for surface in ("raw", "selected"):
            mutated = copy.deepcopy(dependent_tasks)
            candidate = (
                mutated["winner_trace"]["raw_candidates"][0]
                if surface == "raw"
                else mutated["winner_trace"]["selected_candidate"]
            )
            candidate["surplus"] = "forged"
            assert_multitask_rejected(
                label=f"{surface}-full-dict-surplus",
                mutated=mutated,
                target="installed-client-change-builder",
            )

        forged_domain = "unregistered-domain-extension"
        coupled_forgery = copy.deepcopy(
            fixture_observations[
                "capcov-admission-prof-repository-tooling-multitask"
            ]
        )
        forged_layer3_projection = {
            "candidate_layer3_context": {
                "kind": "fixed",
                "domain_requests": [forged_domain],
                "foundation_requests": [],
            },
            "eligible_foundation_layer3_skills": [],
            "eligible_domain_layer3_skills": [forged_domain],
            "eligible_layer3_skills": [forged_domain],
            "reserved_domain_capacity": 1,
            "layer3_overflow": False,
            "layer3_skills": [forged_domain],
        }
        coupled_forgery["route_decision"]["route_result"][
            "layer3_skills"
        ] = [forged_domain]
        selection_candidates = coupled_forgery["route_decision"][
            "selection_evidence"
        ]["layer3_candidates"]
        selection_candidates.insert(
            0,
            {
                "skill": forged_domain,
                "eligible": True,
                "evidence_ids": copy.deepcopy(
                    selection_candidates[0]["evidence_ids"]
                ),
                "rejection_reasons": [],
            },
        )
        for candidate in [
            *coupled_forgery["winner_trace"]["raw_candidates"],
            coupled_forgery["winner_trace"]["selected_candidate"],
        ]:
            candidate.update(copy.deepcopy(forged_layer3_projection))
        assert_multitask_rejected(
            label="coupled-unregistered-domain-route-trace-forgery",
            mutated=coupled_forgery,
            target="repository-tooling-change-builder",
        )

        professional, foundation, domain = _admission_registries()
        disagreeing_domain = copy.deepcopy(domain)
        android_row = next(
            row
            for row in disagreeing_domain["domain_skills"]
            if row["name"] == "android-platform-extension"
        )
        android_row["used_by"] = [
            owner
            for owner in android_row["used_by"]
            if owner != "engineering-change-analysis"
        ]
        assert_multitask_rejected(
            label="android-domain-professional-registry-disagreement",
            mutated=copy.deepcopy(dependent_tasks),
            target="installed-client-change-builder",
            registries=(professional, foundation, disagreeing_domain),
        )

    def test_t4b_v2_true_conflict_requires_exact_policy_evidence(
        self,
    ) -> None:
        case_id = "capcov-t4b-v2-strict-true-conflict"
        task_id = "capcov-t4b-v2-strict-true-conflict"
        observation = {
            "main_execution": _main_execution(task_id),
        }
        observation.update(
            _trace(
                "Implement an accepted repository-owned generator and "
                "Android installed-client behavior change.",
                task_id=task_id,
            )
        )
        decision = observation["route_decision"]
        trace = observation["winner_trace"]
        selected = trace["selected_candidate"]
        self.assertEqual(
            {
                "candidate_id": "implementation-owner-conflict",
                "candidate_type": "derived-conflict",
                "reason": "implementation-owner-conflict",
                "evidence": [
                    "installed-client:installed-client-change-builder",
                    "repository-tooling:repository-tooling-change-builder",
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
                    "candidate_id",
                    "candidate_type",
                    "reason",
                    "evidence",
                    "path",
                    "profile",
                    "primary_skill",
                    "layer3_skills",
                    "review_skill",
                )
            },
        )
        automatic = [
            candidate
            for candidate in trace["raw_candidates"]
            if candidate["candidate_type"]
            == "automatic-implementation-owner"
        ]
        self.assertEqual(2, len(automatic))
        self.assertEqual(
            1,
            len({candidate["precedence"] for candidate in automatic}),
        )
        self.assertEqual(
            [
                {
                    "candidate_id": (
                        "implementation-owner:"
                        "installed-client-change-builder"
                    ),
                    "evidence": [
                        "effect-changed",
                        "explicit-implementation-action",
                        "installed-application-surface",
                    ],
                    "reason": "ambiguous-implementation-owner",
                },
                {
                    "candidate_id": (
                        "implementation-owner:"
                        "repository-tooling-change-builder"
                    ),
                    "evidence": [
                        "effect-changed",
                        "explicit-implementation-action",
                        "repository-developer-tool",
                        "dynamic-helper:_implementation_owner_layer3",
                        (
                            "foundation-selector:dynamic-foundation:"
                            "build-tool-professional-usage"
                        ),
                        (
                            "foundation-selector:dynamic-foundation:"
                            "targeted-validation-selection"
                        ),
                    ],
                    "reason": "ambiguous-implementation-owner",
                },
            ],
            [
                {
                    "candidate_id": candidate["candidate_id"],
                    "evidence": candidate["evidence"],
                    "reason": candidate["reason"],
                }
                for candidate in trace["excluded_candidates"]
            ],
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "start_profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                "path": decision["path"],
                "start_profile": decision["route_result"][
                    "start_profile"
                ],
                "primary_skill": decision["route_result"][
                    "primary_skill"
                ],
                "layer3_skills": decision["route_result"][
                    "layer3_skills"
                ],
                "review_skill": decision["route_result"]["review_skill"],
            },
        )
        if not callable(
            getattr(CAPABILITY_COVERAGE, "_classify_admission_effect", None)
        ):
            self.fail(
                f"[{case_id}] expected callable=_classify_admission_effect; "
                "actual=missing"
            )

        valid = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="installed-client-change-builder",
            declared_case_kind="true-conflict",
            observation=observation,
        )
        self.assertEqual("true-conflict", valid["computed_effect"])
        self.assertEqual([], valid["errors"])

        mutations: dict[str, dict[str, object]] = {}
        for label, field, value in (
            ("id", "candidate_id", "critical-unknown"),
            ("type", "candidate_type", "converted-cohort"),
            ("reason", "reason", "highest-semantic-precedence"),
            ("evidence", "evidence", ["forged-conflict-evidence"]),
        ):
            mutated = copy.deepcopy(observation)
            mutated["winner_trace"]["selected_candidate"][field] = value
            mutations[label] = mutated
        for label, decision_path, trace_path, value in (
            (
                "policy-path",
                ("route_decision", "path"),
                ("winner_trace", "selected_candidate", "path"),
                "direct",
            ),
            (
                "policy-profile",
                ("route_decision", "route_result", "start_profile"),
                ("winner_trace", "selected_candidate", "profile"),
                "task-agent",
            ),
            (
                "policy-primary",
                ("route_decision", "route_result", "primary_skill"),
                ("winner_trace", "selected_candidate", "primary_skill"),
                "backend-change-builder",
            ),
            (
                "policy-layer3",
                ("route_decision", "route_result", "layer3_skills"),
                ("winner_trace", "selected_candidate", "layer3_skills"),
                [],
            ),
            (
                "policy-review",
                ("route_decision", "route_result", "review_skill"),
                ("winner_trace", "selected_candidate", "review_skill"),
                "ai-code-review-refactor",
            ),
        ):
            mutated = copy.deepcopy(observation)
            for path in (decision_path, trace_path):
                target = mutated
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
            mutations[label] = mutated
        unequal_precedence = copy.deepcopy(observation)
        unequal_precedence["winner_trace"]["raw_candidates"][1][
            "precedence"
        ] += 1
        mutations["same-highest-precedence"] = unequal_precedence
        missing_participant = copy.deepcopy(observation)
        missing_participant["winner_trace"]["raw_candidates"].pop()
        mutations["two-automatic-participants"] = missing_participant
        participant_type = copy.deepcopy(observation)
        participant_type["winner_trace"]["raw_candidates"][0][
            "candidate_type"
        ] = "explicit-route"
        mutations["automatic-participant-type"] = participant_type
        participant_evidence = copy.deepcopy(observation)
        participant_evidence["winner_trace"]["raw_candidates"][0][
            "evidence"
        ] = ["forged-participant-evidence"]
        mutations["automatic-participant-evidence"] = participant_evidence
        duplicate_participants = copy.deepcopy(observation)
        duplicate_participant = copy.deepcopy(
            duplicate_participants["winner_trace"]["raw_candidates"][0]
        )
        duplicate_participants["winner_trace"]["raw_candidates"] = [
            copy.deepcopy(duplicate_participant),
            copy.deepcopy(duplicate_participant),
        ]
        duplicate_identity = (
            f"{duplicate_participant['routing_family']}:"
            f"{duplicate_participant['primary_skill']}"
        )
        duplicate_participants["winner_trace"]["selected_candidate"][
            "evidence"
        ] = [duplicate_identity, duplicate_identity]
        duplicate_participants["winner_trace"]["excluded_candidates"] = [
            {
                **copy.deepcopy(duplicate_participant),
                "reason": "ambiguous-implementation-owner",
            },
            {
                **copy.deepcopy(duplicate_participant),
                "reason": "ambiguous-implementation-owner",
            },
        ]
        duplicate_integrity_errors = _t4b_admission_integrity_errors(
            case_id=case_id,
            observation=duplicate_participants,
        )
        self.assertTrue(
            duplicate_integrity_errors,
            "duplicate conflict participants must fail route integrity",
        )
        mutations["distinct-canonical-participants"] = (
            duplicate_participants
        )
        missing_exclusion = copy.deepcopy(observation)
        missing_exclusion["winner_trace"]["excluded_candidates"].pop()
        mutations["exact-exclusions"] = missing_exclusion
        for label, field, value in (
            ("exclusion-id", "candidate_id", "forged-exclusion"),
            (
                "exclusion-reason",
                "reason",
                "not-selected-by-primary-route-precedence",
            ),
            (
                "exclusion-evidence",
                "evidence",
                ["forged-exclusion-evidence"],
            ),
        ):
            mutated = copy.deepcopy(observation)
            mutated["winner_trace"]["excluded_candidates"][0][field] = value
            mutations[label] = mutated
        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill="installed-client-change-builder",
                    declared_case_kind="true-conflict",
                    observation=mutated,
                )
                self.assertNotEqual(
                    "true-conflict",
                    result["computed_effect"],
                )
                self.assertTrue(result["errors"])

        lower_precedence_target = _classify_t4b_admission_effect(
            case_id=case_id,
            layer="professional",
            skill="change-documentation-gate",
            declared_case_kind="true-conflict",
            observation=observation,
        )
        self.assertNotEqual(
            "true-conflict",
            lower_precedence_target["computed_effect"],
        )
        self.assertTrue(lower_precedence_target["errors"])

    def test_t4b_v2_route_integrity_mutations_do_not_count_obligations(
        self,
    ) -> None:
        case_id = "capcov-t4b-v2-route-integrity"
        if not callable(
            getattr(
                CAPABILITY_COVERAGE,
                "_admission_route_integrity_errors",
                None,
            )
        ):
            self.fail(
                f"[{case_id}] expected callable="
                "_admission_route_integrity_errors; actual=missing"
            )
        observation = _admission_observation(
            layer="professional",
            skill="installed-client-change-builder",
            case_kind="selected",
        )
        self.assertEqual(
            [],
            _t4b_admission_integrity_errors(
                case_id=case_id,
                observation=observation,
            ),
        )

        mutations: dict[str, dict[str, object]] = {}
        provenance = copy.deepcopy(observation)
        provenance["route_decision"]["main_execution_provenance"][
            "task_id"
        ] = "forged-task"
        mutations["provenance-deep-equality"] = provenance
        execution_level = copy.deepcopy(observation)
        execution_level["route_decision"]["route_result"][
            "execution_level"
        ] = "L3"
        mutations["execution-level"] = execution_level
        level_basis = copy.deepcopy(observation)
        level_basis["route_decision"]["route_result"]["level_basis"][
            "edit_status"
        ] = "blocked"
        mutations["level-basis"] = level_basis
        review_equality = copy.deepcopy(observation)
        review_equality["winner_trace"]["selected_candidate"][
            "review_skill"
        ] = "security-privacy-gate"
        mutations["review-equality"] = review_equality
        decision_route_once = copy.deepcopy(observation)
        decision_route_once["route_decision"]["route_once"] = False
        mutations["decision-route-once"] = decision_route_once
        trace_route_once = copy.deepcopy(observation)
        trace_route_once["winner_trace"]["route_once"] = "unproven"
        mutations["trace-route-once"] = trace_route_once
        candidate_coverage = copy.deepcopy(observation)
        candidate_coverage["winner_trace"]["candidate_coverage"] = (
            "partial"
        )
        mutations["candidate-coverage"] = candidate_coverage

        projection_mutations = {
            "path": (
                ("route_decision", "path"),
                "analyzed",
            ),
            "profile": (
                ("route_decision", "route_result", "start_profile"),
                "analysis-agent",
            ),
            "primary_skill": (
                ("route_decision", "route_result", "primary_skill"),
                "backend-change-builder",
            ),
            "layer3_skills": (
                ("route_decision", "route_result", "layer3_skills"),
                ["repository-context-map"],
            ),
            "review_skill": (
                ("route_decision", "route_result", "review_skill"),
                "security-privacy-gate",
            ),
        }
        for field, (path, value) in projection_mutations.items():
            mutated = copy.deepcopy(observation)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            mutations[f"projection-{field}"] = mutated

        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                errors = _t4b_admission_integrity_errors(
                    case_id=case_id,
                    observation=mutated,
                )
                self.assertTrue(errors)
                result = _classify_t4b_admission_effect(
                    case_id=case_id,
                    layer="professional",
                    skill="installed-client-change-builder",
                    declared_case_kind="selected",
                    observation=mutated,
                )
                self.assertIsNone(result["computed_effect"])
                self.assertTrue(result["errors"])

    def test_unknown_cross_platform_target_requires_repository_first_behavior(self) -> None:
        sample_path = (
            ROOT
            / "evals"
            / "agent-behavior"
            / "professional-samples"
            / "client"
            / "capcov-cross-target-unknown.yaml"
        )
        sample = load_yaml_file(sample_path)
        professional, layer3 = BEHAVIOR._registries()
        result = BEHAVIOR._score(sample_path, sample, professional, layer3)
        errors: list[str] = []
        if result.scores["route_once"] != 1.0:
            errors.append(
                "[capcov-behavior-cross-target-unknown] expected route_once=1.0; "
                f"actual={result.scores['route_once']:.1f}"
            )
        if result.scores["obligation_coverage"] != 1.0:
            errors.append(
                "[capcov-behavior-cross-target-unknown] expected "
                "obligation_coverage=1.0; "
                f"actual={result.scores['obligation_coverage']:.1f}"
            )
        if result.scores["forbidden_behavior_absence"] != 1.0:
            errors.append(
                "[capcov-behavior-cross-target-unknown] expected "
                "forbidden_behavior_absence=1.0; "
                f"actual={result.scores['forbidden_behavior_absence']:.1f}"
            )
        if errors:
            self.fail("\n".join(errors))


if __name__ == "__main__":
    unittest.main()
