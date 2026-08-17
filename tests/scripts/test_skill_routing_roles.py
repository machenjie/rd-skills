from __future__ import annotations

import importlib.util
import copy
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from fixture_capsule_contract import (
    CONTRACT_VERSION,
    canonical_capsule_sha256,
    validate_and_render_fixture_capsule,
)
from deterministic_route_oracle import (
    ALL_DOMAIN_ROUTE_SPECS,
    DOMAIN_ROUTE_SPECS,
    RoutingIntegrityError,
    _domain_clauses,
    compose_domain_extensions,
    domain_route_family,
    domain_route_families,
    domain_route_specs,
    route as canonical_route,
)
from validation_utils import ValidationProblem, load_yaml_file


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


def _route(prompt: str, *, task_id: str) -> dict[str, object]:
    decision = canonical_route(
        prompt,
        main_execution=_main_execution(task_id),
    )
    result = decision["route_result"]
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }


def _load(script: str, module_name: str):
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "scripts" / script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SkillRoutingRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.routing = _load("validate-skill-routing.py", "validate_skill_routing")
        cls.trajectory = _load("eval-agent-lightweight.py", "eval_agent_lightweight")

    def test_structure_responsibility_routes_use_semantic_forces_and_negation(self) -> None:
        cases = {
            "explicit-architecture-tradeoff": (
                "Analyze an explicit architecture tradeoff between two feasible module "
                "topologies; ownership and dependency boundaries are already established.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["architecture-tradeoff-analysis"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "explicit-test-data-analysis": (
                "Analyze an explicit test-data decision for deterministic fixtures, isolation, "
                "cleanup, and sensitive-data controls.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "quality-test-gate",
                    "layer3_skills": ["test-data-management"],
                    "review_skill": "quality-test-gate",
                },
            ),
            "explicit-authentication-authorization-analysis": (
                "Analyze an explicit authentication and authorization handoff decision for "
                "subject authority, provenance, propagation, and downstream freshness.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "security-privacy-gate",
                    "layer3_skills": ["authentication-authorization"],
                    "review_skill": "security-privacy-gate",
                },
            ),
            "explicit-test-strategy-analysis": (
                "Analyze which proof portfolio should cover several material failure "
                "mechanisms. Select the test levels, observable failure oracles, and "
                "justified omissions because no single command has been fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "quality-test-gate",
                    "layer3_skills": ["test-strategy"],
                    "review_skill": "quality-test-gate",
                },
            ),
            "owner-internal-placement": (
                "Implement a backend service change by deciding whether an owner-private "
                "helper stays as a method, private class, or same-file function; module "
                "ownership, exports, and public API remain unchanged.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "known-generator-authority": (
                "Implement an accepted repository-owned generator source change. The editable "
                "template, generator, derived artifact, committed policy, and freshness check "
                "are known. The owner-private generator method and file placement were already "
                "fixed.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "repository-tooling-change-builder",
                    "layer3_skills": [
                        "build-tool-professional-usage",
                        "targeted-validation-selection",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "resolved-backend-placement": (
                "Implement an accepted backend service change. The owner-private helper was "
                "already selected as a same-file function, and its placement is fixed.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "business-predicate-not-placement": (
                "Implement the owner-private helper as a same-file function that determines "
                "whether an order is eligible.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "runtime-selection-not-placement": (
                "Implement the owner-private helper as a same-file function that selects a "
                "retry strategy.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "runtime-delay-not-placement": (
                "Implement the owner-private helper as a same-file function that determines "
                "retry delay.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "put-selected-file-placement": (
                "Put the private helper into the already selected same file.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "move-selected-file-placement": (
                "Move the private helper into the already selected same file.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "place-invariant-method": (
                "Place the invariant method inside the accepted owner.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "actual-diff-private-move": (
                "Review the actual diff where a duplicate owner-private helper was consolidated "
                "and a private class moved inside the same module with behavior preserved.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": [
                        "implementation-structure-design",
                        "refactoring",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "domain-object-classification": (
                "Analyze whether Order is an entity, Money is an immutable value with "
                "replacement semantics, and Order is the aggregate update and invariant entry "
                "point; identify lifecycle and writer authority.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "domain-impact-modeler",
                    "layer3_skills": ["domain-object-identification"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "windows-domain-object-analysis": (
                "Analyze a Windows MSIX protocol-handler change whose application identity "
                "controls registration; identify domain object identity and writer authority.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "domain-impact-modeler",
                    "layer3_skills": [
                        "windows-platform-extension",
                        "domain-object-identification",
                    ],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "windows-packaged-desktop-implementation": (
                "Implement a Windows packaged desktop application protocol handler whose "
                "application identity controls registration.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "installed-client-change-builder",
                    "layer3_skills": ["windows-platform-extension"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "real-pattern-force": (
                "Implement backend provider variants with a current substitution contract plus "
                "singleton initialization, synchronization, reset, teardown, and concurrent "
                "caller ownership.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [
                        "design-pattern-selection",
                        "concurrency-control",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "pattern-analysis": (
                "Analyze whether backend provider variants have a current substitution "
                "contract, lifecycle, and extension force that justify a design pattern.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["design-pattern-selection"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "known-generator-pattern": (
                "Implement an accepted repository-owned generator source change. The editable "
                "template, derived artifact, committed policy, and freshness check are known; "
                "choose a pattern for provider variants with a current substitution contract.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "repository-tooling-change-builder",
                    "layer3_skills": [
                        "build-tool-professional-usage",
                        "design-pattern-selection",
                        "targeted-validation-selection",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "actual-diff-pattern": (
                "Review the actual diff that implements backend provider variants with a "
                "current substitution contract, lifecycle, and extension force.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": ["design-pattern-selection"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "actual-diff-domain-object": (
                "Review the actual diff that classifies Order as an entity and aggregate root, "
                "Money as an immutable value object, and Order as the writer authority.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": ["domain-object-identification"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "minimal-delete-list": (
                "Review the actual diff's complexity delete list and a new pass-through wrapper "
                "that has no current variation, lifecycle, protocol, or extension force.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": ["minimal-correct-implementation"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "minimal-analysis": (
                "Analyze whether a new pass-through wrapper is needed for accepted behavior; "
                "it has no current variation, lifecycle, protocol, or extension force.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["minimal-correct-implementation"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "minimal-backend": (
                "Implement accepted backend service behavior while deciding whether a new "
                "pass-through wrapper is needed; it has no current variation, lifecycle, "
                "protocol, or extension force.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": ["minimal-correct-implementation"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "minimal-generator": (
                "Implement an accepted repository-owned generator source change. The editable "
                "template, derived artifact, committed policy, and freshness check are known; "
                "decide whether a new pass-through wrapper is needed with no current variation, "
                "lifecycle, protocol, or extension force.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "repository-tooling-change-builder",
                    "layer3_skills": [
                        "build-tool-professional-usage",
                        "minimal-correct-implementation",
                        "targeted-validation-selection",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "classification-plus-method-placement": (
                "Implement the backend order rule after classifying entity, immutable value "
                "object, aggregate root, and writer authority, then place the invariant method "
                "inside the accepted owner without changing module exports.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [
                        "domain-object-identification",
                        "implementation-structure-design",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "ef-mapping-domain-facts-unchanged": (
                "Implement EF entity, relational table, and DTO mapping in the backend; domain "
                "identity, lifecycle, aggregate, invariant, and writer authority remain "
                "unchanged.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "deliberate-separate-owner-implementations": (
                "Implement within one accepted backend owner and deliberately keep separate "
                "implementations because their failure behavior, lifecycle, and evolution "
                "differ; module exports remain unchanged.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "unknown-generated-authority": (
                "Implement a repository-owned generator change, but it is unknown whether the "
                "template, generated file, or checked-in artifact is authoritative.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "cross-module-public-edge": (
                "Analyze a cross-module public export and dependency edge change; method and "
                "file placement inside each owner is already fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["module-boundary-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-structure-analysis": (
                "The accepted owner is PaymentsService. Analyze because owner-internal "
                "implementation structure reuse or deliberate separation remains unresolved.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-structure-analysis-reversed": (
                "Analyze because owner-internal implementation structure reuse or deliberate "
                "separation remains unresolved. The accepted owner is PaymentsService.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-structure-reviewer-a": (
                "The established owner is PaymentsService. Analyze the unresolved owner-private "
                "implementation structure choice between reusing the existing helper and "
                "retaining a deliberately separate implementation.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-structure-reviewer-b": (
                "For the known owner BillingService, analyze an undecided owner-internal "
                "implementation structure tradeoff: keep an intentionally separate private "
                "implementation or reuse the compatible serializer.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-structure-reviewer-c": (
                "Analyze the owner-private implementation structure alternatives: retain a "
                "deliberately separate copy or reuse the current validator. That structure "
                "decision remains unresolved. The owner is accepted.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-structure-source-order": (
                "The owner is known. The owner-internal implementation structure decision is "
                "unresolved: reuse the current mapper or keep a deliberately separate "
                "implementation. Analyze it.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-with-public-boundary-unknown": (
                "The established owner is PaymentsService. Analyze the unresolved owner-private "
                "implementation structure choice between reusing the existing helper and "
                "retaining a deliberately separate implementation. The cross-module public "
                "export change remains unresolved.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "owner-internal-with-dependency-boundary-unknown-first": (
                "The dependency edge change remains undecided. The established owner is "
                "PaymentsService. Analyze the unresolved owner-private implementation structure "
                "choice between reusing the existing helper and retaining a deliberately "
                "separate implementation.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "standalone-cross-module-boundary-unknown": (
                "Analyze a cross-module public export change that remains unresolved.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "fixed-owner-internal-structure": (
                "The accepted owner is PaymentsService. Analyze owner-internal implementation "
                "structure; reuse and deliberate separation are already fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "fixed-placement-refactor": (
                "Review the actual diff for a behavior-preserving move whose owner and final "
                "placement were already accepted.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": ["refactoring"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "fixed-placement-refactor-analysis": (
                "Analyze a behavior-preserving move whose destination owner and final placement "
                "are already fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["refactoring"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "unresolved-placement-is-not-refactoring": (
                "Analyze a behavior-preserving move whose destination owner and final placement "
                "are unresolved.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "guard-naming-only": (
                "Review the actual diff for guard-clause readability and local naming only; "
                "placement, behavior, ownership, and public surface remain unchanged.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": ["code-clarity-maintainability"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "dto-table-ui-not-domain": (
                "With an accepted Engineering Brief, analyze only DTO, relational table, and UI "
                "label mapping; there is no domain identity, lifecycle, aggregate, invariant, or "
                "writer-authority decision.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "data-api-contract-changer",
                    "layer3_skills": ["model-boundary-mapping"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "pattern-word-comment-only": (
                "Update a source comment that mentions the provider pattern; runtime behavior, "
                "variation, lifecycle, protocol, concurrency, and extension forces are unchanged.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "change-documentation-gate",
                    "layer3_skills": ["documentation-generation"],
                    "review_skill": "change-documentation-gate",
                },
            ),
            "documentation-only-module-wording": (
                "Update documentation wording for module ownership and dependency direction; "
                "runtime behavior and architecture remain unchanged.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "change-documentation-gate",
                    "layer3_skills": ["documentation-generation"],
                    "review_skill": "change-documentation-gate",
                },
            ),
            "documentation-with-runtime-architecture-change": (
                "Update documentation wording for module ownership and dependency direction, "
                "and change runtime behavior and architecture.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["module-boundary-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "unchanged-module-and-api": (
                "Implement an owner-private backend helper placement. Module ownership remains "
                "unchanged and there is no public API change.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "mixed-placement-open-first": (
                "Implement an accepted backend service change. The owner-private alpha helper "
                "placement has a method option and remains to be selected. The owner-private "
                "beta helper placement is already fixed as a same-file function.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "mixed-placement-fixed-first": (
                "Implement an accepted backend service change. The owner-private beta helper "
                "placement is already fixed as a same-file function. The owner-private alpha "
                "helper placement has a method option and remains to be selected.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "contradictory-placement-decision": (
                "Implement an accepted backend service change. Choose between a method and a "
                "private class for the owner-private helper placement, although that placement "
                "is already fixed as a same-file function.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "filesystem-safety": (
                "Implement a backend utility that atomically replaces a local file while "
                "checking path containment and symlink behavior; no object placement decision "
                "changes.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": ["filesystem-process-safety"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "sdk-contract": (
                "With an accepted Engineering Brief, analyze only a distributable SDK public "
                "contract and compatibility change; owner-private reuse placement is fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "data-api-contract-changer",
                    "layer3_skills": ["sdk-library-contract-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "package-supply-chain": (
                "Analyze whether to install a new package because of a current capability gap, "
                "including version, license, vulnerability, and supply-chain ownership; local "
                "reuse placement is fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["package-dependency-management"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
        }
        for label, (prompt, expected) in cases.items():
            with self.subTest(label=label):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(expected, actual)
                if label == "package-supply-chain":
                    self.assertNotIn(
                        "dependency-vulnerability-scanning",
                        actual["layer3_skills"],
                    )

        unrelated_predicates = {
            "business-whether": "The service determines whether an order is eligible",
            "runtime-selects": "The runtime selects a retry strategy",
            "runtime-determines": "The runtime determines retry delay",
        }
        placement_owners = {
            "backend": (
                "Implement an accepted backend service change. ",
                "The owner-private helper placement was already selected as a "
                "same-file function",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "repository-tooling": (
                "Implement an accepted repository-owned generator source change. The editable "
                "template, generator, derived artifact, committed policy, and freshness check "
                "are known. ",
                "The owner-private method placement was already selected as a "
                "same-file function",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "repository-tooling-change-builder",
                    "layer3_skills": [
                        "build-tool-professional-usage",
                        "targeted-validation-selection",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
        }
        for owner_kind, (prefix, fixed_placement, expected) in (
            placement_owners.items()
        ):
            for predicate_kind, predicate in unrelated_predicates.items():
                for order, clauses in (
                    (
                        "predicate-first",
                        (predicate, fixed_placement),
                    ),
                    (
                        "placement-first",
                        (fixed_placement, predicate),
                    ),
                ):
                    with self.subTest(
                        owner_kind=owner_kind,
                        predicate_kind=predicate_kind,
                        clause_order=order,
                    ):
                        prompt = f"{prefix}{clauses[0]}, and {clauses[1].lower()}."
                        actual = _route(
                            prompt,
                            task_id=(
                                f"{self._testMethodName}-{owner_kind}-"
                                f"{predicate_kind}-{order}"
                            ),
                        )
                        self.assertEqual(expected, actual)

        placement_selection_phrases = {
            "decide": "decide between a private helper method and same-file function placement",
            "deciding-whether": "deciding whether the private helper placement is a method or same-file function",
            "choose": "choose between a private helper method and same-file function placement",
            "select": "select a private helper method or same-file function placement",
            "determine": "determine the private helper method or same-file function placement",
            "whether": "whether the private helper placement is a method or same-file function must be established",
            "between": "the private helper placement is between a method and a same-file function",
            "one-of": "the private helper placement must be one of a method or a same-file function",
            "alternative": "the private helper placement has method and same-file function alternatives",
            "option": "the private helper placement has a method option and a same-file function option",
        }
        unresolved_expected = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for owner_kind, stem in (
            ("backend", "Implement an accepted backend service change while "),
            (
                "repository",
                "Implement an accepted repository-owned generator source change. The editable "
                "template, generator, derived artifact, committed policy, and freshness check "
                "are known while ",
            ),
        ):
            for cue, phrase in placement_selection_phrases.items():
                with self.subTest(owner_kind=owner_kind, placement_cue=cue):
                    decision = canonical_route(
                        f"{stem}{phrase}.",
                        main_execution=_main_execution(
                            f"{self._testMethodName}-{owner_kind}-{cue}"
                        ),
                    )
                    result = decision["route_result"]
                    actual = {
                        "path": decision["path"],
                        "profile": result["start_profile"],
                        "primary_skill": result["primary_skill"],
                        "layer3_skills": result["layer3_skills"],
                        "review_skill": result["review_skill"],
                    }
                    self.assertEqual(unresolved_expected, actual)
                    self.assertIsNone(result["execution_level"])
                    self.assertIsNone(result["level_basis"])
                    self.assertIsNone(
                        decision["main_execution_provenance"]
                    )

        resolved_placement_phrases = {
            "past": "was previously selected as a same-file function",
            "resolved": "is resolved as a same-file function",
            "accepted": "was accepted as a same-file function",
            "fixed": "is fixed as a same-file function",
        }
        for status, phrase in resolved_placement_phrases.items():
            with self.subTest(resolved_placement=status):
                actual = _route(
                    "Implement an accepted backend service change. The owner-private helper "
                    f"placement {phrase}.",
                    task_id=f"{self._testMethodName}-resolved-{status}",
                )
                self.assertEqual("direct", actual["path"])
                self.assertEqual("task-agent", actual["profile"])
                self.assertEqual("backend-change-builder", actual["primary_skill"])

    def test_owner_placement_finite_grammar_metamorphic_contract(self) -> None:
        analyzed = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        backend_direct = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "backend-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        }
        backend_structure = {
            **backend_direct,
            "layer3_skills": ["implementation-structure-design"],
        }
        tooling_direct = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "repository-tooling-change-builder",
            "layer3_skills": [
                "build-tool-professional-usage",
                "targeted-validation-selection",
            ],
            "review_skill": "ai-code-review-refactor",
        }
        tooling_structure = {
            **tooling_direct,
            "layer3_skills": [
                "build-tool-professional-usage",
                "implementation-structure-design",
                "targeted-validation-selection",
            ],
        }
        owner_contexts = {
            "backend": (
                "Implement an accepted backend service change. ",
                "the owner-private helper placement",
                backend_direct,
                backend_structure,
                "the private helper",
            ),
            "repository-tooling": (
                "Implement an accepted repository-owned generator source change. The editable "
                "template, generator, derived artifact, committed policy, and freshness check "
                "are known. ",
                "the owner-private method placement",
                tooling_direct,
                tooling_structure,
                "the owner-private generator method",
            ),
        }
        open_forms = {
            "if": "decide if {subject} should stay as a method or same-file function",
            "whether": "decide whether {subject} should stay as a method or same-file function",
            "which": "establish which location {subject} should use",
            "where": "determine where {subject} should stay",
            "between": "choose between a method and same-file function for {subject}",
            "one-of": "establish whether {subject} should be one of a method or same-file function",
            "to-keep": "decide whether to keep {subject} as a method or same-file function",
            "alternative": "{subject} has method and same-file function alternatives",
            "option": "{subject} has a method option and same-file function option",
            "choice": "{subject} has a choice between a method and same-file function",
            "tradeoff": "{subject} has a method-versus-function tradeoff",
        }
        for owner, (prefix, subject, _direct, _structure, _object) in (
            owner_contexts.items()
        ):
            for operator, template in open_forms.items():
                with self.subTest(owner=owner, open_operator=operator):
                    self.assertEqual(
                        analyzed,
                        _route(
                            f"{prefix}{template.format(subject=subject)}.",
                            task_id=f"{self._testMethodName}-{owner}-open-{operator}",
                        ),
                    )

        destination_forms = {
            "to": "to the already selected same file",
            "in": "in the already selected same file",
            "within": "within the already selected same file",
            "inside": "inside the already selected same file",
            "into": "into the already selected same file",
            "as": "as the already selected same-file function",
        }
        for owner, (prefix, _subject, _direct, structure, object_name) in (
            owner_contexts.items()
        ):
            for relation, destination in destination_forms.items():
                with self.subTest(owner=owner, destination_relation=relation):
                    self.assertEqual(
                        structure,
                        _route(
                            f"{prefix}Move {object_name} {destination}.",
                            task_id=(
                                f"{self._testMethodName}-{owner}-destination-"
                                f"{relation}"
                            ),
                        ),
                    )

        resolution_predicates = (
            "fixed",
            "resolved",
            "accepted",
            "selected",
            "decided",
            "chosen",
            "determined",
            "known",
        )
        for owner, (prefix, subject, direct, _structure, _object) in (
            owner_contexts.items()
        ):
            for predicate in resolution_predicates:
                with self.subTest(owner=owner, resolution=predicate):
                    self.assertEqual(
                        direct,
                        _route(
                            f"{prefix}{subject.capitalize()} is already {predicate} "
                            "as a same-file function.",
                            task_id=(
                                f"{self._testMethodName}-{owner}-resolution-"
                                f"{predicate}"
                            ),
                        ),
                    )

        for owner, (prefix, subject, direct, _structure, _object) in (
            owner_contexts.items()
        ):
            fixed = f"{subject.capitalize()} was already selected as a same-file function"
            predicate = "The runtime selects a retry strategy"
            for order, clauses in (
                ("predicate-first", (predicate, fixed)),
                ("placement-first", (fixed, predicate)),
            ):
                with self.subTest(owner=owner, unrelated_predicate_order=order):
                    self.assertEqual(
                        direct,
                        _route(
                            f"{prefix}{clauses[0]}, and {clauses[1].lower()}.",
                            task_id=(
                                f"{self._testMethodName}-{owner}-unrelated-{order}"
                            ),
                        ),
                    )

        boundary_cases = {
            "independent-mixed-decisions": (
                "Implement an accepted backend service change. The owner-private alpha helper "
                "placement has a method option and remains to be selected. The owner-private "
                "beta helper placement is fixed as a same-file function.",
                analyzed,
            ),
            "mutation-unchanged-conflict": (
                "Implement an accepted backend service change. Move the owner-private alpha "
                "helper into the selected same file, but the owner-private alpha helper "
                "placement remains unchanged.",
                analyzed,
            ),
            "incompatible-destinations": (
                "Implement an accepted backend service change. Move the owner-private alpha "
                "helper into the selected same file and place the owner-private alpha helper "
                "inside the selected private class.",
                analyzed,
            ),
            "open-resolution-conflict": (
                "Implement an accepted backend service change. Choose between a method and a "
                "private class for the owner-private alpha helper placement, although that "
                "placement is fixed as a same-file function.",
                analyzed,
            ),
            "relative-runtime-function-homonym": (
                "Implement the owner-private helper as a same-file function that selects "
                "which function handles retry.",
                backend_direct,
            ),
            "fixed-then-runtime-homonym": (
                "Implement the backend change with the owner-private helper placement already "
                "fixed as a same-file function, and let runtime determine whether a method is "
                "eligible.",
                backend_direct,
            ),
            "tooling-fixed-then-function-homonym": (
                "Implement the repository generator change with its owner-private placement "
                "already fixed as a same-file function, and let runtime select which function "
                "handles retry.",
                tooling_direct,
            ),
            "named-generic-anaphora": (
                "Implement the backend change with the alpha helper placement already selected "
                "as a same-file function and the owner-private helper placement fixed as a "
                "method; that placement is fixed as a same-file function.",
                analyzed,
            ),
            "generic-named-anaphora": (
                "Implement the backend change with the owner-private helper placement fixed as "
                "a method and the alpha helper placement already selected as a same-file "
                "function; that placement is fixed as a same-file function.",
                analyzed,
            ),
            "same-named-repeat-anaphora": (
                "Implement the backend change with the alpha helper placement already selected "
                "as a same-file function and the alpha helper placement already fixed as the "
                "same-file function; that placement is fixed as the same-file function.",
                backend_direct,
            ),
            "unique-generic-anaphora": (
                "Implement the backend change with the owner-private helper placement fixed as "
                "a method; that placement is fixed as a method.",
                backend_direct,
            ),
            "unique-anaphora": (
                "Implement an accepted backend service change. Move the owner-private alpha "
                "helper into the selected same file. That placement is already selected as a "
                "same-file function.",
                backend_structure,
            ),
            "missing-anaphora": (
                "Implement an accepted backend service change. That placement is fixed as a "
                "same-file function.",
                analyzed,
            ),
            "multiple-anaphora": (
                "Implement an accepted backend service change. The owner-private alpha helper "
                "placement is fixed as a method and the owner-private beta helper placement is "
                "fixed as a same-file function. That placement is fixed as a same-file "
                "function.",
                analyzed,
            ),
            "named-generic-anaphora-ambiguous-mutation": (
                "Implement an accepted backend service change. Move the owner-private alpha "
                "helper into the selected same file and the owner-private helper placement is "
                "fixed as a method. That placement is fixed as a same-file function.",
                analyzed,
            ),
            "underspecified": (
                "Implement an owner-private backend helper placement. Module ownership and "
                "public API remain unchanged.",
                analyzed,
            ),
            "fixed-refactor": (
                "Review the actual diff for a behavior-preserving move whose owner and final "
                "placement were already accepted.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": ["refactoring"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "actual-mutation-review": (
                "Review the actual diff where a duplicate owner-private helper was consolidated "
                "and a private class moved inside the same module with behavior preserved.",
                {
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": [
                        "implementation-structure-design",
                        "refactoring",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
        }
        for label, (prompt, expected) in boundary_cases.items():
            with self.subTest(boundary=label):
                self.assertEqual(
                    expected,
                    _route(
                        prompt,
                        task_id=f"{self._testMethodName}-boundary-{label}",
                    ),
                )

    def test_owner_placement_requested_action_ssot_contract(self) -> None:
        backend_direct = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "backend-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        }
        backend_structure = {
            **backend_direct,
            "layer3_skills": ["implementation-structure-design"],
        }
        tooling_direct = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "repository-tooling-change-builder",
            "layer3_skills": [
                "build-tool-professional-usage",
                "targeted-validation-selection",
            ],
            "review_skill": "ai-code-review-refactor",
        }
        repository_first = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        actual_diff_review = {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "ai-code-review-refactor",
            "layer3_skills": [
                "implementation-structure-design",
                "refactoring",
            ],
            "review_skill": "ai-code-review-refactor",
        }
        cases = {
            "relative-business-method": (
                "Implement the owner-private helper as a same-file function that determines "
                "whether a method is eligible.",
                backend_direct,
            ),
            "backend-bounded-runtime-function": (
                "Implement the backend change with the owner-private helper placement already "
                "fixed as a same-file function, and let runtime select which function handles "
                "retry.",
                backend_direct,
            ),
            "tooling-bounded-runtime-function": (
                "Implement the repository generator change with its owner-private placement "
                "already fixed as a same-file function, and let runtime select which function "
                "handles retry.",
                tooling_direct,
            ),
            "passive-move": (
                "The private helper was moved inside the accepted owner.",
                repository_first,
            ),
            "imperative-move": (
                "Move the private helper inside the accepted owner.",
                backend_structure,
            ),
            "actual-diff-passive-review": (
                "Review the actual diff where the private helper was moved inside the accepted "
                "owner and the duplicate helper was removed.",
                actual_diff_review,
            ),
            "fixed-declaration": (
                "The helper placement is fixed as a function.",
                repository_first,
            ),
            "explicit-implement-fixed": (
                "Implement the backend change. The helper placement is fixed as a function.",
                backend_direct,
            ),
        }
        for label, (prompt, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    expected,
                    _route(
                        prompt,
                        task_id=f"{self._testMethodName}-{label}",
                    ),
                )

    def test_owner_placement_compound_subject_is_not_requested_mutation(self) -> None:
        from deterministic_route_oracle import _owner_placement_decisions

        decisions = _owner_placement_decisions(
            "Reuse placement is fixed."
        )
        self.assertEqual(1, len(decisions))
        self.assertEqual("unchanged", decisions[0].polarity)
        self.assertEqual(
            ["resolution"],
            [fact.predicate_class for fact in decisions[0].facts],
        )
        self.assertFalse(
            any(fact.requested_action for fact in decisions[0].facts)
        )

        repository_first = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        package_analysis = {
            **repository_first,
            "layer3_skills": ["package-dependency-management"],
        }
        backend_structure = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "backend-change-builder",
            "layer3_skills": ["implementation-structure-design"],
            "review_skill": "ai-code-review-refactor",
        }
        cases = {
            "compound-declaration": (
                "Analyze the repository package. The reuse placement is fixed.",
                repository_first,
            ),
            "admission-compound-declaration": (
                "Analyze whether to install a new package for a current capability gap, "
                "including version, license, vulnerability, and supply-chain ownership; "
                "reuse placement is fixed.",
                package_analysis,
            ),
            "imperative-reuse": (
                "Reuse the private helper inside the accepted owner.",
                backend_structure,
            ),
            "imperative-move": (
                "Move the private helper inside the accepted owner.",
                backend_structure,
            ),
            "open-reuse-separation-analysis": (
                "The established owner is PaymentsService. Analyze the unresolved owner-private "
                "implementation structure choice between reusing the existing helper and "
                "retaining a deliberately separate implementation.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["implementation-structure-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
        }
        for label, (prompt, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    expected,
                    _route(
                        prompt,
                        task_id=f"{self._testMethodName}-{label}",
                    ),
                )

    def test_experience_analysis_routes_declared_member_subsets_only(
        self,
    ) -> None:
        experience_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "experience-impact-modeler",
            "review_skill": "ai-code-review-refactor",
        }
        cases = {
            "interaction-only": (
                "Analyze a user flow's loading and error interaction states "
                "and state transitions; no design token or component "
                "decision is requested.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "design-only": (
                "Analyze a user flow's design tokens, components, spacing, "
                "and typography; no interaction state or transition decision "
                "is requested.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "combined": (
                "Analyze a user flow's loading and error interaction states "
                "and transitions together with design tokens, components, "
                "spacing, and typography.",
                {
                    **experience_route,
                    "layer3_skills": [
                        "interaction-state-modeling",
                        "design-system-rules",
                    ],
                },
            ),
            "interaction-with-design-unchanged": (
                "Analyze a user flow's loading and error states and "
                "transitions; design tokens, components, spacing, and "
                "typography remain unchanged.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "design-with-interaction-unchanged": (
                "Analyze a user flow's design tokens, components, spacing, "
                "and typography; interaction states and transitions remain "
                "unchanged.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "interaction-mention-only": (
                "Analyze a user flow glossary report that merely mentions "
                "interaction states; do not decide or change any state or "
                "transition behavior.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "design-mention-only": (
                "Analyze a user flow report that merely lists design tokens "
                "and components; no design-system decision is requested and "
                "no token or component behavior changes.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "interaction-full-vocabulary-reference-only": (
                "Analyze a user flow report that lists loading and error "
                "states, state transitions, and recovery for documentation/"
                "reference only.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "interaction-full-vocabulary-decision": (
                "Analyze a user flow report that lists loading and error "
                "states, state transitions, and recovery for documentation/"
                "reference only, and explicitly decide, model, and change "
                "those state transitions and recovery.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "design-full-vocabulary-reference-only": (
                "Analyze a user flow report that lists design tokens, "
                "components, spacing, typography, and variants for "
                "documentation/reference only.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "design-full-vocabulary-decision": (
                "Analyze a user flow report that lists design tokens, "
                "components, spacing, typography, and variants for "
                "documentation/reference only, and explicitly choose, "
                "define, and apply a design-system token and component "
                "variant decision.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "interaction-unrelated-subject-unchanged": (
                "Analyze the checkout user flow's decision to model loading "
                "state transitions and error recovery; the legacy onboarding "
                "interaction state remains unchanged.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "design-unrelated-subject-unchanged": (
                "Analyze the checkout user flow's design-system decision to "
                "define design tokens, components, spacing, typography, and "
                "variants; the legacy marketing component remains unchanged.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "interaction-target-subject-unchanged": (
                "Analyze the checkout user flow's loading and error "
                "interaction states and state transitions that remain "
                "unchanged.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "design-target-subject-unchanged": (
                "Analyze the checkout user flow's design tokens, components, "
                "spacing, and typography that remain unchanged.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "interaction-coordinated-child-conjunction": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and change that user flow's loading and "
                "error transitions.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "design-coordinated-child-conjunction": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and change that user flow's design tokens "
                "and component variant decision.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "interaction-coordinated-child-update": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and update that user flow's loading and "
                "error transitions.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "interaction-coordinated-child-update-negative": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and do not update that user flow's loading "
                "and error transitions.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "interaction-coordinated-child-implement": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and implement that user flow's loading and "
                "error transitions.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "interaction-coordinated-child-implement-negative": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and do not implement that user flow's "
                "loading and error transitions.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "interaction-coordinated-child-fix": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and fix that user flow's loading and error "
                "transitions.",
                {
                    **experience_route,
                    "layer3_skills": ["interaction-state-modeling"],
                },
            ),
            "interaction-coordinated-child-fix-unchanged": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and fix that user flow's loading and error "
                "transitions that remain unchanged.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "design-coordinated-child-update": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and update that user flow's design tokens "
                "and component variants.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "design-coordinated-child-update-negative": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and do not update that user flow's design "
                "tokens and component variants.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "design-coordinated-child-implement": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and implement that user flow's design tokens "
                "and component variants.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "design-coordinated-child-implement-negative": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and do not implement that user flow's design "
                "tokens and component variants.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "design-coordinated-child-fix": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and fix that user flow's design tokens and "
                "component variants.",
                {
                    **experience_route,
                    "layer3_skills": ["design-system-rules"],
                },
            ),
            "design-coordinated-child-fix-unchanged": (
                "Analyze the checkout user flow report for documentation/"
                "reference only, and fix that user flow's design tokens and "
                "component variants that remain unchanged.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "generic-user-flow": (
                "Analyze a user flow.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
        }
        observed = {
            label: _route(
                prompt,
                task_id=f"{self._testMethodName}:{label}",
            )
            for label, (prompt, _expected) in cases.items()
        }
        expected = {
            label: route
            for label, (_prompt, route) in cases.items()
        }
        self.assertEqual(
            expected,
            observed,
            "experience routing must project only the declared member "
            "subset; a generic user-flow label is insufficient",
        )

    def test_external_integration_analysis_routes_exact_changed_members(
        self,
    ) -> None:
        external_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "review_skill": "ai-code-review-refactor",
        }
        reliability_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "reliability-observability-gate",
            "layer3_skills": [
                "degradation-circuit-breaking",
                "observability",
            ],
            "review_skill": "reliability-observability-gate",
        }
        fail_closed_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        cases = {
            "consumer-only": (
                "Analyze an external integration downstream consumer "
                "compatibility change; retryable versus terminal outcomes "
                "and timeout cancellation meaning remain unchanged.",
                {
                    **external_route,
                    "layer3_skills": ["consumer-impact-analysis"],
                },
            ),
            "failure-only": (
                "Analyze an external integration retryable versus terminal "
                "outcome and timeout cancellation meaning change; downstream "
                "consumer compatibility remains unchanged.",
                {
                    **external_route,
                    "layer3_skills": ["failure-contract-design"],
                },
            ),
            "combined": (
                "Implement an external integration timeout and contract "
                "change.",
                {
                    **external_route,
                    "layer3_skills": [
                        "consumer-impact-analysis",
                        "failure-contract-design",
                    ],
                },
            ),
            "both-unchanged": (
                "Analyze an external integration where downstream consumer "
                "compatibility remains unchanged; timeout and cancellation "
                "meaning remain unchanged.",
                fail_closed_route,
            ),
            "negated": (
                "Analyze an external integration without a downstream "
                "consumer compatibility or failure contract change.",
                fail_closed_route,
            ),
            "ambiguous-subject": (
                "Analyze an external integration whose provider subject is "
                "ambiguous; downstream consumer compatibility changes.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "change-intake-compiler",
                    "layer3_skills": ["requirement-clarification"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "unknown-owner": (
                "Analyze an external integration whose contract owner is "
                "unknown; downstream consumer compatibility changes.",
                fail_closed_route,
            ),
            "adjacent-reference": (
                "Analyze a reference to an external integration consumer "
                "contract; consumer behavior remains unchanged.",
                fail_closed_route,
            ),
            "timeout-meaning": (
                "Analyze an external integration timeout classification "
                "meaning change; downstream consumer behavior remains "
                "unchanged.",
                {
                    **external_route,
                    "layer3_skills": ["failure-contract-design"],
                },
            ),
            "safe-error-representation": (
                "Analyze an external integration safe error representation "
                "change; downstream consumer behavior remains unchanged.",
                {
                    **external_route,
                    "layer3_skills": ["failure-contract-design"],
                },
            ),
            "retry-mechanics": (
                "Analyze an external integration retry attempts and backoff "
                "budget change; consumer and failure contract semantics "
                "remain unchanged.",
                reliability_route,
            ),
            "fallback-degradation-mechanics": (
                "Analyze an external integration fallback and degradation "
                "mechanics change; consumer and failure contract semantics "
                "remain unchanged.",
                reliability_route,
            ),
            "unrelated-reliability-conflict": (
                "Analyze an external integration downstream consumer "
                "compatibility change; an unrelated service outage "
                "degradation behavior changes.",
                fail_closed_route,
            ),
        }
        observed = {
            label: _route(
                prompt,
                task_id=f"{self._testMethodName}:{label}",
            )
            for label, (prompt, _expected) in cases.items()
        }
        expected = {
            label: route
            for label, (_prompt, route) in cases.items()
        }
        self.assertEqual(expected, observed)

    def test_analysis_specialist_precedence_is_semantic_and_action_bounded(
        self,
    ) -> None:
        specialist_cases = {
            "module-boundary-ownership-change": (
                "Analyze a module boundary ownership change for the architecture, "
                "with one topology already chosen and no tradeoff decision.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["module-boundary-design"],
                    "review_skill": "architecture-impact-reviewer",
                },
            ),
            "proof-portfolio-level-oracle-selection": (
                "Analyze which proof portfolio should cover several failure "
                "mechanisms and choose test levels and failure oracles; test data "
                "fixtures and cleanup are already fixed.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "quality-test-gate",
                    "layer3_skills": ["test-strategy"],
                    "review_skill": "quality-test-gate",
                },
            ),
            "ssrf-url-fetch-threat-analysis": (
                "Analyze an SSRF URL fetch threat for an authenticated service "
                "account, with no authorization handoff or policy change.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "security-privacy-gate",
                    "layer3_skills": ["threat-modeling", "web-security"],
                    "review_skill": "security-privacy-gate",
                },
            ),
        }
        for label, (prompt, expected) in specialist_cases.items():
            with self.subTest(label=label, boundary="specialist-positive"):
                self.assertEqual(
                    expected,
                    _route(prompt, task_id=f"{self._testMethodName}:{label}"),
                )

        generic_eca = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        keyword_only_cases = {
            "module-keywords": (
                "Update documentation wording that mentions a module boundary "
                "ownership change; runtime behavior and architecture remain "
                "unchanged."
            ),
            "test-strategy-keywords": (
                "Summarize the existing proof portfolio, test levels, and failure "
                "oracles; all choices are already fixed and no selection is "
                "requested."
            ),
            "ssrf-keywords": (
                "Summarize SSRF URL fetch threat terminology without analyzing an "
                "abuse path, control placement, or security behavior."
            ),
        }
        for label, prompt in keyword_only_cases.items():
            with self.subTest(label=label, boundary="keyword-only"):
                self.assertEqual(
                    generic_eca,
                    _route(prompt, task_id=f"{self._testMethodName}:{label}"),
                )

        generic_analysis_cases = {
            "module-context": (
                "Analyze an internal helper with module boundary ownership change "
                "as historical context; module ownership and dependency edges "
                "remain unchanged.",
                generic_eca,
            ),
            "fixed-proof-portfolio": (
                "Analyze the current proof portfolio report where test levels and "
                "failure oracles are already fixed; no portfolio selection is "
                "requested.",
                generic_eca,
            ),
            "ssrf-boundary": (
                "Analyze an SSRF-prone server-side URL fetch boundary including "
                "canonicalization DNS redirects and private-network denial.",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["threat-modeling", "web-security"],
                    "review_skill": "security-privacy-gate",
                },
            ),
        }
        for label, (prompt, expected) in generic_analysis_cases.items():
            with self.subTest(label=label, boundary="generic-analysis"):
                self.assertEqual(
                    expected,
                    _route(prompt, task_id=f"{self._testMethodName}:{label}"),
                )

        direct_cases = {
            "module-implementation": (
                "Implement an accepted backend service change; module ownership "
                "and dependency edges remain unchanged.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "test-implementation": (
                "Implement accepted regression tests using fixed test levels and "
                "failure oracles.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "quality-test-gate",
                    "layer3_skills": ["regression-testing"],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
            "ssrf-implementation": (
                "Implement an accepted backend URL fetch control for SSRF denial "
                "and redirect validation.",
                {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            ),
        }
        for label, (prompt, expected) in direct_cases.items():
            with self.subTest(label=label, boundary="direct-implementation"):
                self.assertEqual(
                    expected,
                    _route(prompt, task_id=f"{self._testMethodName}:{label}"),
                )

    def test_plain_scenario_output_wording_does_not_trigger_scenario_routing(
        self,
    ) -> None:
        prompt = (
            "Update migration documentation without changing runtime behavior; "
            "mention a primary scenario with trigger, pre-state, decision, and "
            "observable postcondition."
        )
        self.assertEqual(
            {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "change-documentation-gate",
                "layer3_skills": ["documentation-generation"],
                "review_skill": "change-documentation-gate",
            },
            _route(prompt, task_id=self._testMethodName),
        )

    def test_windows_domain_object_analysis_honors_implementation_polarity(
        self,
    ) -> None:
        analysis = (
            "Analyze a Windows MSIX protocol-handler change whose application identity "
            "controls registration; identify domain object identity and writer authority"
        )
        expected_analysis = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "domain-impact-modeler",
            "layer3_skills": [
                "windows-platform-extension",
                "domain-object-identification",
            ],
            "review_skill": "architecture-impact-reviewer",
        }
        mismatches: list[str] = []
        expected_domain_matches = [
            (
                "windows-platform-extension",
                "application-identity-authority",
            )
        ]
        for clause in (
            "before implementation",
            "without implementation",
            "do not implement it",
            "implementation is out of scope",
        ):
            with self.subTest(clause=clause):
                prompt = f"{analysis}; {clause}."
                actual_domain_matches = domain_route_families(prompt)
                if actual_domain_matches != expected_domain_matches:
                    mismatches.append(
                        f"[clause={clause!r}] mismatch=domain-relevance; "
                        f"expected={expected_domain_matches!r}; "
                        f"actual={actual_domain_matches!r}"
                    )
                actual_route = _route(
                    prompt,
                    task_id=f"{self._testMethodName}:{clause}",
                )
                if actual_route != expected_analysis:
                    mismatches.append(
                        f"[clause={clause!r}] mismatch=final-route; "
                        f"expected={expected_analysis!r}; "
                        f"actual={actual_route!r}"
                    )

        expected_implementation = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "installed-client-change-builder",
            "layer3_skills": ["windows-platform-extension"],
            "review_skill": "ai-code-review-refactor",
        }
        implementation_suffix = (
            "an accepted Windows packaged desktop application protocol-handler change "
            "whose application identity controls registration"
        )
        implementation_clauses = (
            f"Implement {implementation_suffix}",
            f"For the accepted task, implement {implementation_suffix}",
            f"We must implement {implementation_suffix}",
            f"Please implement {implementation_suffix}",
            f"The accepted task is to implement {implementation_suffix}",
        )
        for implementation in implementation_clauses:
            for prompt in (
                f"{analysis}. {implementation}.",
                f"{implementation}. {analysis}.",
            ):
                with self.subTest(prompt=prompt):
                    actual_route = _route(
                        prompt,
                        task_id=self._testMethodName,
                    )
                    if actual_route != expected_implementation:
                        mismatches.append(
                            f"[prompt={prompt!r}] "
                            "mismatch=implementation-final-route; "
                            f"expected={expected_implementation!r}; "
                            f"actual={actual_route!r}"
                        )

        contradictory = (
            f"{analysis}. We must implement {implementation_suffix} despite an "
            "instruction that we must not implement it."
        )
        expected_contradictory = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": [
                "windows-platform-extension",
                "repository-context-map",
            ],
            "review_skill": "architecture-impact-reviewer",
        }
        actual_contradictory = _route(
            contradictory,
            task_id=f"{self._testMethodName}:contradictory",
        )
        if actual_contradictory != expected_contradictory:
            mismatches.append(
                "[clause='contradictory'] mismatch=final-route; "
                f"expected={expected_contradictory!r}; "
                f"actual={actual_contradictory!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_analysis_only_routes_ignore_negated_implementation_keywords(
        self,
    ) -> None:
        cases = {
            "node-business-rule": (
                "Analyze a Node.js backend business rule with no runtime or "
                "core-library behavior change",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
                (
                    "Implement a Node.js backend business rule with no runtime "
                    "or core-library behavior change.",
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "backend-change-builder",
                        "layer3_skills": [],
                        "review_skill": "ai-code-review-refactor",
                    },
                ),
            ),
            "filesystem-safety": (
                "Analyze a backend utility that atomically replaces a local file "
                "while checking path containment and symlink behavior",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                },
                (
                    "Implement a backend utility that atomically replaces a local "
                    "file while checking path containment and symlink behavior.",
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "backend-change-builder",
                        "layer3_skills": ["filesystem-process-safety"],
                        "review_skill": "ai-code-review-refactor",
                    },
                ),
            ),
            "design-pattern": (
                "Analyze whether backend provider variants have a current "
                "substitution contract, lifecycle, and extension force that "
                "justify a design pattern",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "architecture-impact-reviewer",
                    "layer3_skills": ["design-pattern-selection"],
                    "review_skill": "architecture-impact-reviewer",
                },
                (
                    "Implement backend provider variants with a current "
                    "substitution contract, lifecycle, and extension force.",
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "backend-change-builder",
                        "layer3_skills": ["design-pattern-selection"],
                        "review_skill": "ai-code-review-refactor",
                    },
                ),
            ),
            "minimality": (
                "Analyze whether a new pass-through wrapper is needed for "
                "accepted behavior; it has no current variation, lifecycle, "
                "protocol, or extension force",
                {
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["minimal-correct-implementation"],
                    "review_skill": "architecture-impact-reviewer",
                },
                (
                    "Implement accepted backend behavior while deciding whether "
                    "a new pass-through wrapper is needed; it has no current "
                    "variation, lifecycle, protocol, or extension force.",
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "backend-change-builder",
                        "layer3_skills": ["minimal-correct-implementation"],
                        "review_skill": "ai-code-review-refactor",
                    },
                ),
            ),
        }
        for label, (analysis, expected_analysis, contrast) in cases.items():
            for prompt in (
                f"{analysis}; do not implement it.",
                f"Do not implement it. {analysis}.",
            ):
                with self.subTest(label=label, prompt=prompt):
                    self.assertEqual(
                        expected_analysis,
                        _route(prompt, task_id=f"{self._testMethodName}:{label}"),
                    )
            positive_prompt, expected_positive = contrast
            with self.subTest(label=label, contrast="positive"):
                self.assertEqual(
                    expected_positive,
                    _route(
                        positive_prompt,
                        task_id=f"{self._testMethodName}:{label}:positive",
                    ),
                )

    def test_audit_integrity_action_polarity_is_clause_local(self) -> None:
        expected_analysis = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": ["audit-evidence-integrity"],
            "review_skill": "security-privacy-gate",
        }
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
                    self.assertEqual(
                        expected_analysis,
                        _route(
                            prompt,
                            task_id=f"{self._testMethodName}:{action}:negative",
                        ),
                    )
        for prompt in (
            analysis,
            (
                "Do not implement audit evidence integrity for protected audit "
                "storage and export."
            ),
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    expected_analysis,
                    _route(prompt, task_id=f"{self._testMethodName}:analysis"),
                )

        expected_implementation = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "logging-design-gate",
            "layer3_skills": ["audit-evidence-integrity"],
            "review_skill": "logging-design-gate",
        }
        for prompt in (
            (
                "Update audit evidence integrity for protected audit storage "
                "and export."
            ),
            (
                "Change audit evidence integrity for protected audit storage "
                "and export."
            ),
            (
                "Implement audit evidence integrity for protected audit storage "
                "and export."
            ),
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    expected_implementation,
                    _route(
                        prompt,
                        task_id=f"{self._testMethodName}:implementation",
                    ),
                )

        contradictory = (
            "Change audit evidence integrity for protected audit storage despite "
            "an instruction that we must not change audit evidence integrity."
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            _route(
                contradictory,
                task_id=f"{self._testMethodName}:contradictory",
            ),
        )

    def test_layer3_cell_accepts_exact_names_or_none(self) -> None:
        self.assertEqual(([], None), self.routing.parse_layer3_cell("none"))
        self.assertEqual(
            (["transaction-consistency", "concurrency-control"], None),
            self.routing.parse_layer3_cell(
                "transaction-consistency, concurrency-control"
            ),
        )

    def test_layer3_cell_rejects_vague_duplicate_and_over_budget_values(self) -> None:
        for value in (
            "transaction, concurrency when triggered",
            "concurrency-control, concurrency-control",
            "one, two, three, four",
            "Concurrency-Control",
            "concurrency-控制",
            "-concurrency-control",
        ):
            with self.subTest(value=value):
                _names, error = self.routing.parse_layer3_cell(value)
                self.assertIsNotNone(error)

    def test_router_row_checks_candidate_role_and_exact_review_name(self) -> None:
        professional = {
            "primary-skill": {
                "task_routable": True,
                "role_support": ["analysis-agent"],
                "layer3_candidates": ["allowed-layer3"],
            },
            "review-skill": {
                "task_routable": True,
                "role_support": ["review-agent"],
                "layer3_candidates": [],
            },
        }
        layer3 = {
            "allowed-layer3": {"role_support": ["task-agent"]},
            "outside-candidate": {"role_support": ["analysis-agent"]},
        }
        errors = self.routing.validate_router_row(
            [
                "signal",
                "analysis-agent",
                "primary-skill",
                "allowed-layer3, outside-candidate",
                "review-skill-extra",
            ],
            professional,
            layer3,
        )
        joined = "\n".join(errors)
        self.assertIn("unsupported profile analysis-agent", joined)
        self.assertIn("outside primary-skill.layer3_candidates", joined)
        self.assertIn("exactly one known Review Skill", joined)

    def test_domain_router_rows_preserve_registry_anti_triggers(self) -> None:
        domain_entries = self.routing.load_yaml_file(self.routing.DOMAIN)[
            "domain_skills"
        ]
        domain = {entry["name"]: entry for entry in domain_entries}
        router_rows = []
        for line in self.routing.ROUTER.read_text(encoding="utf-8").splitlines():
            if (
                line.startswith("|")
                and not line.startswith("| ---")
                and "Task signal" not in line
            ):
                router_rows.append(
                    [cell.strip() for cell in line.strip("|").split("|")]
                )

        self.assertEqual(
            [],
            self.routing.domain_router_coverage_errors(
                router_rows,
                domain,
            ),
        )
        missing_ai = [
            cells
            for cells in router_rows
            if "ai-product-extension" not in cells[3]
        ]
        self.assertTrue(
            any(
                "ai-product-extension" in error
                and "no authoritative router row" in error
                for error in self.routing.domain_router_coverage_errors(
                    missing_ai,
                    domain,
                )
            )
        )

        stale_anti = copy.deepcopy(router_rows)
        ai_row = next(
            cells for cells in stale_anti if "ai-product-extension" in cells[3]
        )
        ai_row[0] = "AI model retrieval or agent-tool authority decision"
        self.assertTrue(
            any(
                "ai-product-extension" in error
                and "Router omits anti-trigger atoms" in error
                for error in self.routing.domain_router_coverage_errors(
                    stale_anti,
                    domain,
                )
            )
        )

        stale_trigger = copy.deepcopy(router_rows)
        ai_row = next(
            cells for cells in stale_trigger if "ai-product-extension" in cells[3]
        )
        ai_row[0] = (
            "AI retrieval boundary; excluding AI terminology, static algorithms, "
            "or ordinary search without a model decision"
        )
        self.assertTrue(
            any(
                "ai-product-extension" in error
                and "Router omits trigger atoms" in error
                for error in self.routing.domain_router_coverage_errors(
                    stale_trigger,
                    domain,
                )
            )
        )

        stale_registry = copy.deepcopy(domain)
        stale_registry["ai-product-extension"]["trigger_signals"].append(
            "unmapped model surface"
        )
        self.assertTrue(
            any(
                "ai-product-extension" in error
                and "Registry/oracle trigger atoms differ" in error
                for error in self.routing.domain_router_coverage_errors(
                    router_rows,
                    stale_registry,
                )
            )
        )

        positive_only_drift = copy.deepcopy(router_rows)
        ai_row = next(
            cells
            for cells in positive_only_drift
            if "ai-product-extension" in cells[3]
        )
        ai_row[0] = ai_row[0].replace("model, ", "", 1)
        self.assertTrue(
            any(
                "ai-product-extension" in error
                and "Router omits trigger atoms: model" in error
                for error in self.routing.domain_router_coverage_errors(
                    positive_only_drift,
                    domain,
                )
            )
        )

        missing_partition = copy.deepcopy(router_rows)
        bigdata_row = next(
            cells
            for cells in missing_partition
            if "bigdata-product-extension" in cells[3]
        )
        bigdata_row[0] = bigdata_row[0].replace("partition, ", "", 1)
        self.assertTrue(
            any(
                "bigdata-product-extension" in error
                and "Router omits boundary atoms: partition" in error
                for error in self.routing.domain_router_coverage_errors(
                    missing_partition,
                    domain,
                )
            )
        )

        missing_recovery = copy.deepcopy(router_rows)
        web3_row = next(
            cells
            for cells in missing_recovery
            if "web3-product-extension" in cells[3]
        )
        web3_row[0] = web3_row[0].replace("recovery, ", "", 1)
        self.assertTrue(
            any(
                "web3-product-extension" in error
                and "Router omits boundary atoms: recovery" in error
                for error in self.routing.domain_router_coverage_errors(
                    missing_recovery,
                    domain,
                )
            )
        )

    def test_domain_oracle_executes_authoritative_atomic_trigger_probes(self) -> None:
        probes = {
            "ai-product-extension": (
                "Migrate ordinary search to a prompt workflow whose tenant permission "
                "controls model context."
            ),
            "bigdata-product-extension": (
                "Migrate one large table to a distributed batch job with partition "
                "ownership and consumer compatibility."
            ),
            "iot-embedded-extension": (
                "Migrate a cloud API into an edge device protocol whose timing "
                "boundary controls hardware safety."
            ),
            "low-level-systems-extension": (
                "Migrate an ordinary Rust backend service to an OS resource boundary "
                "with native memory ownership."
            ),
            "payment-trading-extension": (
                "Migrate a price display into a payment wallet whose accounting and "
                "reconciliation control settlement."
            ),
            "web3-product-extension": (
                "Migrate an ordinary API signature key into chain custody where "
                "recovery authority controls wallet finality."
            ),
        }
        for domain, prompt in probes.items():
            with self.subTest(domain=domain):
                match = domain_route_family(" ".join(prompt.casefold().split()))
                self.assertIsNotNone(match)
                self.assertEqual(domain, match[0])

        migrated = domain_route_family(
            "migrate ordinary search to a prompt workflow whose tenant permission "
            "controls model context; legacy search behavior remains unchanged"
        )
        self.assertEqual(("ai-product-extension", "retrieval-data"), migrated)
        documentation_only = domain_route_family(
            "update rag tenant permission documentation and prompt copy"
        )
        self.assertIsNone(documentation_only)
        self.assertIsNone(
            domain_route_family(
                "replace wallet recovery wording; custody behavior remains unchanged"
            )
        )
        self.assertEqual(
            ("iot-embedded-extension", "firmware-update-recovery"),
            domain_route_family(
                "update firmware and documentation copy to change rollback behavior"
            ),
        )
        self.assertEqual(
            ("low-level-systems-extension", "kernel-realtime-concurrency"),
            domain_route_family(
                "real-time rust kernel deadline handling with memory safety"
            ),
        )
        self.assertIsNone(domain_route_family("ordinary api key recovery"))
        self.assertEqual(
            ("ai-product-extension", "retrieval-data"),
            domain_route_family(
                "change rag prompt behavior for tenant permission; "
                "http api behavior remains unchanged"
            ),
        )
        self.assertIsNone(
            domain_route_family(
                "migrate rag tenant permission documentation; "
                "model behavior remains unchanged"
            )
        )
        for adjacent in (
            "analyze a database model evaluation and schema approval",
            "analyze cloud network protocol timing",
            "change payment wallet account recovery",
        ):
            with self.subTest(adjacent=adjacent):
                self.assertIsNone(domain_route_family(adjacent))

    def test_domain_oracle_executes_each_declared_anti_atom(self) -> None:
        probes = {
            "ai-product-extension": "prompt retrieval permission model context",
            "bigdata-product-extension": "batch pipeline partition consumer",
            "iot-embedded-extension": "device protocol timing hardware",
            "low-level-systems-extension": "rust native memory ownership resource",
            "android-platform-extension": (
                "android application lifecycle permission revocation"
            ),
            "payment-trading-extension": (
                "payment wallet accounting reconciliation settlement"
            ),
            "web3-product-extension": (
                "blockchain wallet custody behavior recovery finality"
            ),
        }
        mismatches: list[str] = []
        anti_execution_counts: dict[str, int] = {}
        declared_anti_probe_counts = {
            domain: len(ALL_DOMAIN_ROUTE_SPECS[domain]["anti_atoms"]) * 2
            for domain in probes
        }
        for domain, prompt in probes.items():
            declared = {domain: ALL_DOMAIN_ROUTE_SPECS[domain]}
            positive_matches = domain_route_families(
                prompt,
                specs=declared,
            )
            anti_execution_counts[domain] = 0
            if not positive_matches:
                mismatches.append(
                    f"[domain={domain!r}] mismatch=positive-nonempty; "
                    f"expected_domain={domain!r}; actual=[]"
                )
                continue
            actual_positive_domains = [
                match[0] for match in positive_matches
            ]
            if actual_positive_domains != [domain]:
                mismatches.append(
                    f"[domain={domain!r}] mismatch=positive-exact; "
                    f"expected={[domain]!r}; "
                    f"actual={actual_positive_domains!r}"
                )
            for anti_atom in ALL_DOMAIN_ROUTE_SPECS[domain]["anti_atoms"]:
                for separator in (" ", "; "):
                    anti_execution_counts[domain] += 1
                    with self.subTest(
                        domain=domain,
                        anti_atom=anti_atom,
                        separator=separator,
                    ):
                        matches = domain_route_families(
                            f"{prompt}{separator}{anti_atom}",
                            specs=declared,
                        )
                        if (
                            domain == "payment-trading-extension"
                            and anti_atom == "no monetary invariant"
                            and separator == "; "
                        ):
                            actual_domains = {
                                match[0] for match in matches
                            }
                            if domain not in actual_domains:
                                mismatches.append(
                                    f"[domain={domain!r}, "
                                    f"anti_atom={anti_atom!r}, "
                                    f"separator={separator!r}] "
                                    "mismatch=anti-exception; "
                                    f"expected_domain={domain!r}; "
                                    f"actual={sorted(actual_domains)!r}"
                                )
                            continue
                        actual_domains = {
                            match[0] for match in matches
                        }
                        if domain in actual_domains:
                            mismatches.append(
                                f"[domain={domain!r}, "
                                f"anti_atom={anti_atom!r}, "
                                f"separator={separator!r}] "
                                "mismatch=anti-suppression; "
                                f"unexpected_domain={domain!r}; "
                                f"actual={sorted(actual_domains)!r}"
                            )
        expected_android_route = (
            "android-platform-extension",
            "platform-lifecycle-authority",
        )
        actual_android_route = domain_route_family(
            "android application lifecycle permission revocation "
            "after process recreation"
        )
        if actual_android_route != expected_android_route:
            mismatches.append(
                "[domain='android-platform-extension'] "
                "mismatch=final-positive-route; "
                f"expected={expected_android_route!r}; "
                f"actual={actual_android_route!r}"
            )
        if mismatches:
            self.fail(
                "\n".join(
                    [
                        *mismatches,
                        "declared-anti-probe-counts="
                        f"{declared_anti_probe_counts!r}",
                        "actual-anti-execution-counts="
                        f"{anti_execution_counts!r}",
                    ]
                )
            )

    def test_adjacent_domain_anti_does_not_cross_domain_boundaries(self) -> None:
        for prompt in (
            "batch pipeline partition consumer; without a distributed pipeline",
            "device protocol timing hardware; firmware behavior remains unchanged",
            "device protocol timing hardware; no firmware or physical device behavior changes",
            "payment wallet accounting settlement; funds and ledger state remain unchanged",
        ):
            with self.subTest(prompt=prompt):
                self.assertIsNone(domain_route_family(prompt))
        self.assertEqual(
            ("ai-product-extension", "retrieval-data"),
            domain_route_family(
                "change rag prompt behavior for tenant permission; "
                "http api behavior remains unchanged"
            ),
        )

    def test_adjacent_monetary_anti_preserves_other_domain_evidence(self) -> None:
        controls = {
            "ai-product-extension": (
                "prompt retrieval permission model context",
                "no monetary invariant and no ai surface",
            ),
            "bigdata-product-extension": (
                "batch pipeline partition consumer",
                "no monetary invariant and without a distributed pipeline",
            ),
            "iot-embedded-extension": (
                "device protocol timing hardware",
                "no monetary invariant and without device or firmware behavior",
            ),
            "web3-product-extension": (
                "blockchain wallet custody behavior recovery finality",
                "no monetary invariant and without chain or custody behavior",
            ),
            "payment-trading-extension": (
                "payment wallet accounting reconciliation settlement",
                "no monetary invariant and without funds, ledger, settlement, "
                "or execution state",
            ),
        }
        for domain, (positive, adjacent_anti) in controls.items():
            with self.subTest(domain=domain):
                matches = domain_route_families(
                    f"{positive}; {adjacent_anti}",
                    specs={domain: ALL_DOMAIN_ROUTE_SPECS[domain]},
                )
                self.assertNotIn(domain, {match[0] for match in matches})

        ai_unchanged = domain_route_families(
            "prompt retrieval permission model context; no monetary invariant "
            "and model behavior remains unchanged",
            specs={
                "ai-product-extension": ALL_DOMAIN_ROUTE_SPECS[
                    "ai-product-extension"
                ]
            },
        )
        self.assertEqual([], ai_unchanged)

        payment_spec = {
            "payment-trading-extension": ALL_DOMAIN_ROUTE_SPECS[
                "payment-trading-extension"
            ]
        }
        adjacent_payment_absence = domain_route_families(
            "payment wallet accounting reconciliation settlement; "
            "a separate wallet has no monetary invariant",
            specs=payment_spec,
        )
        self.assertEqual(
            [("payment-trading-extension", "money-ledger-settlement")],
            adjacent_payment_absence,
        )
        same_clause_payment_absence = domain_route_families(
            "payment wallet accounting reconciliation settlement with "
            "no monetary invariant",
            specs=payment_spec,
        )
        self.assertEqual([], same_clause_payment_absence)

    def test_bare_comma_splits_only_independent_unchanged_clause(self) -> None:
        self.assertEqual(
            (
                "change rag prompt behavior for tenant permission",
                "model behavior remains the same",
            ),
            _domain_clauses(
                "change RAG prompt behavior for tenant permission, "
                "model behavior remains the same"
            ),
        )
        self.assertIsNone(
            domain_route_family(
                "change rag prompt behavior for tenant permission, "
                "model behavior remains the same"
            )
        )
        self.assertEqual(
            (
                "funds, ledger, settlement, and execution state remain unchanged",
            ),
            _domain_clauses(
                "funds, ledger, settlement, and execution state remain unchanged"
            ),
        )
        self.assertEqual(
            ("ai-product-extension", "retrieval-data"),
            domain_route_family(
                "change rag prompt behavior for tenant permission, "
                "http api behavior remains unchanged"
            ),
        )

    def test_contrast_punctuation_keeps_unrelated_unchanged_clause_isolated(self) -> None:
        for separator in (
            "; ",
            ". ",
            ", while ",
            ", but ",
            ", although ",
            ", whereas ",
            ", yet ",
        ):
            with self.subTest(separator=separator):
                prompt = (
                    "change rag prompt behavior for tenant permission"
                    f"{separator}http api behavior remains unchanged"
                )
                self.assertEqual(
                    ("ai-product-extension", "retrieval-data"),
                    domain_route_family(prompt),
                )

    def test_payment_context_beats_weak_web3_terms_without_chain_anchor(self) -> None:
        self.assertEqual(
            ("payment-trading-extension", "money-ledger-settlement"),
            domain_route_family(
                "analyze a payment wallet custody recovery where funds settlement "
                "and accounting must reconcile"
            ),
        )
        for prompt in (
            "analyze a chain key custody recovery where wallet finality survives a reorg",
            "analyze a smart contract payment wallet where chain finality and recovery "
            "protect settlement",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    ("web3-product-extension", "chain-custody-finality"),
                    domain_route_family(prompt),
                )

    def test_multi_domain_web3_payment_overlap_requires_independent_invariants(
        self,
    ) -> None:
        weak_payment_overlap = (
            "Migrate an ordinary API signature key into chain custody where "
            "recovery authority controls wallet finality."
        )
        self.assertEqual(
            [("web3-product-extension", "chain-custody-finality")],
            domain_route_families(weak_payment_overlap),
        )

        payment_only = (
            "Analyze a payment wallet custody recovery where funds settlement "
            "and accounting must reconcile."
        )
        self.assertEqual(
            [("payment-trading-extension", "money-ledger-settlement")],
            domain_route_families(payment_only),
        )

        mixed_invariants = (
            "Analyze a smart contract payment wallet where chain finality and "
            "recovery protect ledger settlement and accounting reconciliation."
        )
        self.assertEqual(
            [
                ("web3-product-extension", "chain-custody-finality"),
                ("payment-trading-extension", "money-ledger-settlement"),
            ],
            domain_route_families(mixed_invariants),
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": [
                    "web3-product-extension",
                    "payment-trading-extension",
                    "repository-context-map",
                ],
                "review_skill": "architecture-impact-reviewer",
            },
            _route(mixed_invariants, task_id=self._testMethodName),
        )

        cross_clause_payment_absence = (
            "Analyze a blockchain chain transaction where custody recovery "
            "protects wallet finality; a separate payment wallet custody has "
            "no monetary invariant."
        )
        self.assertEqual(
            [("web3-product-extension", "chain-custody-finality")],
            domain_route_families(cross_clause_payment_absence),
        )

        cross_clause_independent_invariants = (
            "Analyze a blockchain chain transaction where custody recovery "
            "protects wallet finality; analyze a payment wallet where funds "
            "settlement and accounting reconcile."
        )
        self.assertEqual(
            [
                ("web3-product-extension", "chain-custody-finality"),
                ("payment-trading-extension", "money-ledger-settlement"),
            ],
            domain_route_families(cross_clause_independent_invariants),
        )
        self.assertEqual(
            "engineering-change-analysis",
            _route(cross_clause_independent_invariants, task_id=self._testMethodName)["primary_skill"],
        )

        ordinary_api = (
            "Rotate an ordinary API signature key and update recovery documentation."
        )
        self.assertEqual([], domain_route_families(ordinary_api))

    def test_domain_registry_modes_drive_modifier_oracle_membership(self) -> None:
        registry = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        modifiers = domain_route_specs(registry)
        self.assertEqual(set(DOMAIN_ROUTE_SPECS), set(modifiers))
        self.assertEqual(13, len(modifiers))
        self.assertTrue(
            all(
                row["routing_mode"] == "modifier-only"
                for row in registry["domain_skills"]
            )
        )

        malformed = copy.deepcopy(registry)
        malformed["domain_skills"][0]["routing_mode"] = "sometimes"
        with self.assertRaisesRegex(ValidationProblem, "routing_mode"):
            domain_route_specs(malformed)

        boolean_version = copy.deepcopy(registry)
        boolean_version["schema_version"] = True
        with self.assertRaisesRegex(ValidationProblem, "exact int 6"):
            domain_route_specs(boolean_version)

    def test_cross_platform_contract_rejects_fixed_platform_count_splitting(
        self,
    ) -> None:
        contract_paths = (
            ROOT
            / "src/domain-extensions/cross-platform-client-extension/SKILL.md",
            ROOT
            / "src/domain-extensions/cross-platform-client-extension/references/framework-target-evidence-contracts.md",
        )
        fixed_count_rules = (
            "one or two concrete platform Domains",
            "More than two concrete platforms",
        )
        for path in contract_paths:
            content = path.read_text(encoding="utf-8")
            for rule in fixed_count_rules:
                with self.subTest(path=path.relative_to(ROOT), rule=rule):
                    self.assertNotIn(rule, content)

    def test_ordered_domain_composition_is_bounded_and_platform_anchored(
        self,
    ) -> None:
        registered = [
            "cross-platform-client-extension",
            "android-platform-extension",
            "ios-ipados-platform-extension",
            "windows-platform-extension",
            "macos-platform-extension",
        ]
        with self.assertRaises(RoutingIntegrityError):
            compose_domain_extensions(
                (
                    "ios-ipados-platform-extension",
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "ios-ipados-platform-extension",
                ),
                registered_domains=registered,
            )
        flutter = compose_domain_extensions(
            (
                "ios-ipados-platform-extension",
                "cross-platform-client-extension",
                "android-platform-extension",
            ),
            registered_domains=registered,
        )
        self.assertEqual("selected", flutter["outcome"])
        self.assertEqual(
            [
                "cross-platform-client-extension",
                "android-platform-extension",
                "ios-ipados-platform-extension",
            ],
            flutter["ordered_domains"],
        )
        electron = compose_domain_extensions(
            (
                "windows-platform-extension",
                "cross-platform-client-extension",
            ),
            registered_domains=registered,
        )
        self.assertEqual(
            [
                "cross-platform-client-extension",
                "windows-platform-extension",
            ],
            electron["ordered_domains"],
        )
        cohesive_three_platforms = compose_domain_extensions(
            (
                "cross-platform-client-extension",
                "android-platform-extension",
                "ios-ipados-platform-extension",
                "windows-platform-extension",
            ),
            registered_domains=registered,
            max_domains=4,
        )
        self.assertEqual("selected", cohesive_three_platforms["outcome"])
        self.assertEqual(
            [
                "cross-platform-client-extension",
                "android-platform-extension",
                "ios-ipados-platform-extension",
                "windows-platform-extension",
            ],
            cohesive_three_platforms["ordered_domains"],
        )
        with self.assertRaises(RoutingIntegrityError):
            compose_domain_extensions(
                ("cross-platform-client-extension",),
                registered_domains=registered,
            )
        with self.assertRaises(RoutingIntegrityError):
            compose_domain_extensions(
                (
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "ios-ipados-platform-extension",
                    "windows-platform-extension",
                ),
                registered_domains=registered,
            )

    def test_cross_platform_separability_routes_lower_platform_count_to_analysis(
        self,
    ) -> None:
        prompt = (
            "Implement accepted Flutter changes targeting Android and iOS as "
            "multiple dependent tasks: update the shared bridge contract, then "
            "change the platform adapters; the slices have separate write scopes, "
            "validation, release, and rollback."
        )
        actual = _route(prompt, task_id=self._testMethodName)
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": [
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "ios-ipados-platform-extension",
                ],
                "review_skill": "ai-code-review-refactor",
            },
            actual,
        )

    def test_windows_service_keeps_backend_owner_with_windows_modifier(self) -> None:
        from deterministic_route_oracle import (
            classify_professional_families,
            route_with_trace,
        )

        cases = {
            "windows-service-positive": {
                "prompt": (
                    "Implement an accepted Windows service lifecycle change "
                    "in C# with async disposal and CancellationToken behavior."
                ),
                "domains": [
                    (
                        "windows-platform-extension",
                        "service-lifecycle-authority",
                    )
                ],
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [
                        "windows-platform-extension",
                        "csharp-dotnet-professional-usage",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
            },
            "generic-backend-domain-anti": {
                "prompt": (
                    "Implement an accepted backend service endpoint change "
                    "with no Windows behavior."
                ),
                "domains": [],
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                },
            },
        }
        mismatches: list[str] = []
        executed: list[str] = []
        for label, case in cases.items():
            executed.append(label)
            prompt = case["prompt"]
            actual_families = [
                row["routing_family"]
                for row in classify_professional_families(prompt)
            ]
            if actual_families != ["backend"]:
                mismatches.append(
                    f"[{label}] mismatch=professional-family; "
                    f"expected=['backend']; actual={actual_families!r}"
                )
            actual_domains = domain_route_families(prompt)
            if actual_domains != case["domains"]:
                mismatches.append(
                    f"[{label}] mismatch=domain-family; "
                    f"expected={case['domains']!r}; "
                    f"actual={actual_domains!r}"
                )
            observed = route_with_trace(
                prompt,
                main_execution=_main_execution(
                    f"{self._testMethodName}:{label}"
                ),
            )
            owner_ids = [
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith(
                    "implementation-owner:"
                )
            ]
            expected_owner_ids = [
                "implementation-owner:backend-change-builder"
            ]
            if owner_ids != expected_owner_ids:
                mismatches.append(
                    f"[{label}] mismatch=raw-owner; "
                    f"expected={expected_owner_ids!r}; "
                    f"actual={owner_ids!r}"
                )
            decision = observed["route_decision"]
            route_result = decision["route_result"]
            actual_route = {
                "path": decision["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            }
            if actual_route != case["route"]:
                mismatches.append(
                    f"[{label}] mismatch=route-envelope; "
                    f"expected={case['route']!r}; "
                    f"actual={actual_route!r}"
                )
            trace = observed["winner_trace"]
            if (
                decision.get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{label}] mismatch=route-proof; "
                    f"route_once={decision.get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )
        if executed != list(cases):
            mismatches.append(
                "[windows-service-effect-domain-anti] "
                f"mismatch=case-execution; expected={list(cases)!r}; "
                f"actual={executed!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_cross_platform_router_row_defers_to_proven_concrete_targets(
        self,
    ) -> None:
        rows = []
        for line in self.routing.ROUTER.read_text(encoding="utf-8").splitlines():
            if (
                line.startswith("|")
                and not line.startswith("| ---")
                and "Task signal" not in line
            ):
                rows.append(
                    [cell.strip() for cell in line.strip("|").split("|")]
                )
        shared = [
            cells
            for cells in rows
            if cells[2] == "installed-client-change-builder"
            and cells[0].startswith("shared installed client")
        ]
        self.assertEqual(1, len(shared))
        self.assertEqual(
            "cross-platform-client-extension + proven concrete platform Domain(s)",
            shared[0][3],
        )
        self.assertNotIn("android-platform-extension", shared[0][3])
        self.assertNotIn("ios-ipados-platform-extension", shared[0][3])

        cases = (
            (
                "Implement an accepted Flutter application change targeting "
                "Android and iOS.",
                "installed-client-change-builder",
                [
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "ios-ipados-platform-extension",
                ],
            ),
            (
                "Implement an accepted Electron packaged application change "
                "targeting Windows.",
                "installed-client-change-builder",
                [
                    "cross-platform-client-extension",
                    "windows-platform-extension",
                ],
            ),
            (
                "Implement an accepted Electron packaged application change "
                "targeting macOS.",
                "installed-client-change-builder",
                [
                    "cross-platform-client-extension",
                    "macos-platform-extension",
                ],
            ),
            (
                "Prepare an implementation for a cross-platform packaged client "
                "whose target platforms are not yet known.",
                "engineering-change-analysis",
                ["repository-context-map"],
            ),
        )
        for prompt, expected_primary, expected_layer3 in cases:
            with self.subTest(prompt=prompt):
                actual = _route(prompt, task_id=self._testMethodName)
                self.assertEqual(expected_primary, actual["primary_skill"])
                self.assertEqual(expected_layer3, actual["layer3_skills"])

    def test_trajectory_dispatch_rejects_layer3_profile_mismatch(self) -> None:
        step = {
            "actor": "main-control-agent",
            "action": "dispatch",
            "profile": "analysis-agent",
            "primary_skill": "primary-skill",
            "layer3_skills": ["task-only-layer3"],
            "layer3_references": [],
            "mode": "implementation-preparation",
            "professional_references": [],
            "fixture_capsule": {
                "contract_version": CONTRACT_VERSION,
                "contract_type": "analysis",
                "template": "engineering-brief",
                "goal": "Analyze the bounded source evidence and identify the owning rule.",
                "scope": ["bounded source"],
                "evidence": ["Current owner, consumer, and validation evidence"],
                "validation": ["Use the smallest non-mutating source check"],
                "stop_conditions": ["Stop when evidence leaves the bounded source"],
                "output": ["Source-backed Engineering Brief with proof limits"],
                "canonical_sha256": "0" * 64,
            },
        }
        step["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            step,
            step["fixture_capsule"],
        )
        steps = [step]
        errors = self.trajectory._profile_errors(
            "case",
            steps,
            {
                "primary-skill": {
                    "role_support": ["analysis-agent"],
                    "layer3_candidates": ["task-only-layer3"],
                }
            },
            {"task-only-layer3": {"role_support": ["task-agent"]}},
        )
        self.assertTrue(any("does not support profile 'analysis-agent'" in item for item in errors))

    def test_lightweight_rejects_synchronized_placeholder_fixture_capsule(self) -> None:
        document = self.trajectory._load_json(self.trajectory.FIXTURES)
        step = copy.deepcopy(document["cases"][0]["steps"][1])
        original_goal = step["fixture_capsule"]["goal"]
        original_text = validate_and_render_fixture_capsule(step)
        replacement = "x" * 20
        step["fixture_capsule"]["goal"] = replacement
        forged_render = original_text.replace(original_goal, replacement, 1)
        step["fixture_capsule"]["canonical_sha256"] = hashlib.sha256(
            forged_render.encode("utf-8")
        ).hexdigest()
        professional, layer3 = self.trajectory._skill_registries()

        errors = self.trajectory._profile_errors(
            "mutated",
            [step],
            professional,
            layer3,
        )

        self.assertTrue(
            any("invalid fixture Capsule" in item for item in errors),
            errors,
        )

    def test_progress_requires_supported_checkpoint_type_and_evidence(self) -> None:
        steps = [
            {"action": "progress", "evidence": "Path selected."},
            {
                "action": "progress",
                "checkpoint_type": "unsupported",
                "evidence": "Batch completed.",
            },
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "   ",
            },
        ]
        errors = self.trajectory._progress_errors("case", steps)
        self.assertEqual(
            2,
            sum("must use one of" in error for error in errors),
            errors,
        )
        self.assertTrue(any("requires non-empty evidence" in error for error in errors), errors)

    def test_all_progress_checkpoint_types_can_repeat_with_new_evidence(self) -> None:
        steps = [
            {
                "actor": "main-control-agent",
                "action": "progress",
                "checkpoint_type": "start/path",
                "evidence": "The first bounded execution path is established from fixture evidence.",
                "evidence_anchor": "fixture:case:path",
            },
            {
                "actor": "main-control-agent",
                "action": "progress",
                "checkpoint_type": "start/path",
                "evidence": "The revised bounded path remains established before worker evidence.",
                "evidence_anchor": "fixture:case:path",
            },
            {"action": "dispatch", "batch_id": "analysis-one"},
            {
                "action": "progress",
                "checkpoint_type": "dispatch/batch",
                "evidence": "The first named analysis batch completed with bounded ownership evidence.",
                "evidence_anchor": "batch:analysis-one",
            },
            {"action": "dispatch", "batch_id": "analysis-two"},
            {
                "action": "progress",
                "checkpoint_type": "dispatch/batch",
                "evidence": "The second named analysis batch completed with changed scope evidence.",
                "evidence_anchor": "batch:analysis-two",
            },
            {"action": "validate", "evidence_id": "targeted-one", "outcome": "passed"},
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "The first targeted validation completed with a recorded passing outcome.",
                "evidence_anchor": "validation:targeted-one:passed",
            },
            {"action": "validate", "evidence_id": "targeted-two", "outcome": "passed"},
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "The second targeted validation completed with changed passing evidence.",
                "evidence_anchor": "validation:targeted-two:passed",
            },
            {"action": "review", "evidence_id": "review-one", "outcome": "accepted"},
            {
                "action": "progress",
                "checkpoint_type": "review/close",
                "evidence": "The first independent review recorded an accepted bounded outcome.",
                "evidence_anchor": "review:review-one:accepted",
            },
            {"action": "review", "evidence_id": "review-two", "outcome": "accepted"},
            {
                "action": "progress",
                "checkpoint_type": "review/close",
                "evidence": "The second independent review recorded changed acceptance evidence.",
                "evidence_anchor": "review:review-two:accepted",
            },
        ]
        self.assertEqual([], self.trajectory._progress_errors("case", steps))

    def test_repair_fixture_uses_four_distinct_progress_events_without_noise(self) -> None:
        fixture = self.trajectory._load_json(self.trajectory.FIXTURES)
        case = next(item for item in fixture["cases"] if item["id"] == "repair-and-rereview")
        progress = [step for step in case["steps"] if step.get("action") == "progress"]
        checkpoints = {
            (step.get("checkpoint_type"), step.get("evidence")) for step in progress
        }
        self.assertEqual(4, len(progress))
        self.assertEqual(len(progress), len(checkpoints))
        self.assertEqual(
            self.trajectory.PROGRESS_CHECKPOINT_TYPES,
            {step["checkpoint_type"] for step in progress},
        )
        metrics, errors = self.trajectory._metrics(
            case,
            *self.trajectory._skill_registries(),
        )
        self.assertEqual([], errors)
        self.assertLessEqual(metrics["max_silent_steps"], 5)
        self.assertLessEqual(metrics["progress_to_productive_action_ratio"], 0.75)

    def test_start_path_after_productive_action_is_rejected(self) -> None:
        steps = [
            {"actor": "task-agent", "action": "edit"},
            {
                "actor": "main-control-agent",
                "action": "progress",
                "checkpoint_type": "start/path",
                "evidence": "Started late.",
                "evidence_anchor": "fixture:case:path",
            },
        ]
        self.assertTrue(
            any("must precede the first productive worker action" in error for error in self.trajectory._progress_errors("case", steps))
        )

    def test_multi_agent_fixture_without_progress_fails_density_gate(self) -> None:
        fixture = self.trajectory._load_json(self.trajectory.FIXTURES)
        case = next(item for item in fixture["cases"] if item["id"] == "single-module-feature")
        case = {**case, "steps": [step for step in case["steps"] if step.get("action") != "progress"]}
        _metrics, errors = self.trajectory._metrics(
            case,
            *self.trajectory._skill_registries(),
        )
        self.assertEqual(3, sum(step.get("action") == "dispatch" for step in case["steps"]))
        self.assertTrue(any("requires 3-5 anchored progress" in error for error in errors), errors)

    def test_explicit_complex_case_requires_progress_even_with_fewer_dispatches(self) -> None:
        fixture = self.trajectory._load_json(self.trajectory.FIXTURES)
        case = next(item for item in fixture["cases"] if item["id"] == "diagnosis-only")
        case = {**case, "complexity": "complex"}
        _metrics, errors = self.trajectory._metrics(
            case,
            *self.trajectory._skill_registries(),
        )
        self.assertTrue(any("requires 3-5 anchored progress" in error for error in errors), errors)

    def test_required_complex_and_high_risk_fixtures_have_anchored_progress(self) -> None:
        fixture = self.trajectory._load_json(self.trajectory.FIXTURES)
        required_ids = {
            "single-module-feature",
            "api-contract-change",
            "data-migration",
            "security-ssrf-boundary",
            "cache-stampede-reliability",
            "release-rollback",
        }
        for case in fixture["cases"]:
            if case["id"] not in required_ids:
                continue
            with self.subTest(case=case["id"]):
                metrics, errors = self.trajectory._metrics(
                    case,
                    *self.trajectory._skill_registries(),
                )
                self.assertEqual([], errors)
                self.assertTrue(metrics["required_progress_for_multi_agent"])
                self.assertGreaterEqual(metrics["progress_count"], 3)
                self.assertLessEqual(metrics["progress_count"], 5)
                self.assertLessEqual(metrics["max_silent_steps"], 5)

    def test_generic_progress_evidence_is_rejected_even_with_valid_anchor(self) -> None:
        steps = [
            {
                "action": "progress",
                "checkpoint_type": "start/path",
                "evidence": "a/b/c/d",
                "evidence_anchor": "fixture:case:path",
            }
        ]
        errors = self.trajectory._progress_errors("case", steps)
        self.assertTrue(any("generic marker" in error for error in errors), errors)

    def test_validation_progress_cannot_bind_future_outcome(self) -> None:
        steps = [
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "Targeted validation is reported as passed before its evidence exists.",
                "evidence_anchor": "validation:targeted-check:passed",
            },
            {"action": "validate", "evidence_id": "targeted-check", "outcome": "passed"},
        ]
        errors = self.trajectory._progress_errors("case", steps)
        self.assertTrue(any("prior validation evidence id and outcome" in error for error in errors), errors)

    def test_shared_workspace_parallel_batch_breaks_serial_gate(self) -> None:
        fixture = self.trajectory._load_json(self.trajectory.FIXTURES)
        case = fixture["scheduling_cases"][0]
        case = {**case, "steps": [dict(step) for step in case["steps"]]}
        task_dispatches = [
            step
            for step in case["steps"]
            if step.get("action") == "dispatch" and step.get("profile") == "task-agent"
        ]
        task_dispatches[0]["parallel_batch"] = "unsafe-shared"
        task_dispatches[1]["parallel_batch"] = "unsafe-shared"
        metrics, errors = self.trajectory._metrics(
            case,
            *self.trajectory._skill_registries(),
        )
        self.assertFalse(metrics["shared_workspace_writes_serial"])
        self.assertTrue(errors)

    def test_adjacent_progress_updates_reject_identical_type_and_evidence(self) -> None:
        steps = [
            {"action": "validate", "evidence_id": "targeted-tests", "outcome": "passed"},
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "Targeted tests passed.",
                "evidence_anchor": "validation:targeted-tests:passed",
            },
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "Targeted tests passed.",
                "evidence_anchor": "validation:targeted-tests:passed",
            },
        ]
        errors = self.trajectory._progress_errors("case", steps)
        self.assertTrue(
            any("repeat identical checkpoint_type and evidence" in error for error in errors),
            errors,
        )

    def test_interleaved_checkpoint_repeat_requires_changed_evidence(self) -> None:
        steps = [
            {"action": "validate", "evidence_id": "targeted-tests", "outcome": "passed"},
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "Targeted tests passed.",
                "evidence_anchor": "validation:targeted-tests:passed",
            },
            {"action": "review", "evidence_id": "bounded-review", "outcome": "blocking"},
            {
                "action": "progress",
                "checkpoint_type": "review/close",
                "evidence": "Review found one blocker.",
                "evidence_anchor": "review:bounded-review:blocking",
            },
            {
                "action": "progress",
                "checkpoint_type": "validation",
                "evidence": "Targeted tests passed.",
                "evidence_anchor": "validation:targeted-tests:passed",
            },
        ]
        errors = self.trajectory._progress_errors("case", steps)
        self.assertTrue(any("must carry changed evidence" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
