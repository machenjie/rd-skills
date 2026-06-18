from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_action_classifier import classify_event  # noqa: E402
from changeforge_common import load_state, merge_state, reset_state_for_new_prompt  # noqa: E402
from changeforge_runtime_route_resolver import CAPABILITY_IDS, build_active_skill_context  # noqa: E402


def _context_for(event: dict, state: dict | None = None) -> dict:
    classification = classify_event(event)
    return build_active_skill_context(
        runtime="codex",
        stage=classification.get("stage", ""),
        surfaces=classification.get("surfaces", []),
        event_name=event.get("hook_event_name") or event.get("hookEventName") or "PreToolUse",
        state=state or {},
        classification=classification,
    )


def _edit_event(path: str, text: str = "") -> dict:
    patch = f"*** Begin Patch\n*** Update File: {path}\n+{text}\n*** End Patch\n"
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"patch": patch},
    }


class RuntimeRouteResolverTests(unittest.TestCase):
    def test_frontend_tsx_edit_routes_frontend_not_backend(self) -> None:
        context = _context_for(_edit_event("src/components/ProfileCard.tsx"))
        self.assertEqual(context["owner_skill"], "frontend-change-builder")
        self.assertIn("frontend-product", context["product_surfaces"])
        self.assertIn("typescript", context["language_surfaces"])
        self.assertNotIn("backend-change-builder", context["selected_skills"])

    def test_backend_service_edit_routes_backend(self) -> None:
        context = _context_for(_edit_event("src/services/order_service.py"))
        self.assertEqual(context["owner_skill"], "backend-change-builder")
        self.assertIn("backend-product", context["product_surfaces"])

    def test_cpp_edit_selects_cpp_not_go(self) -> None:
        context = _context_for(_edit_event("src/native/socket_pool.cpp", "RAII sanitizer fix"))
        self.assertIn("cpp", context["language_surfaces"])
        self.assertIn("cpp-professional-usage", context["selected_capabilities"])
        self.assertNotIn("go-professional-usage", context["selected_capabilities"])

    def test_go_edit_selects_go_not_cpp(self) -> None:
        context = _context_for(_edit_event("internal/worker/channel_fanout.go", "go channel fix"))
        self.assertIn("go", context["language_surfaces"])
        self.assertIn("go-professional-usage", context["selected_capabilities"])
        self.assertNotIn("cpp-professional-usage", context["selected_capabilities"])

    def test_docs_only_change_has_docs_owner_no_structure_default(self) -> None:
        context = _context_for(_edit_event("docs/runbooks/cache-warmup.md"))
        self.assertEqual(context["owner_skill"], "change-documentation-gate")
        self.assertIn("documentation-only", context["product_surfaces"])
        self.assertNotIn("implementation-structure-design", context["selected_capabilities"])
        self.assertNotIn("backend-change-builder", context["selected_skills"])
        self.assertNotIn("quality-test-gate", context["selected_skills"])
        self.assertNotIn("test gate", context["required_quality_gates"])

    def test_chart_values_route_delivery_not_backend(self) -> None:
        context = _context_for(_edit_event("deploy/chart/values.yaml", "helm Chart.yaml rollout"))
        self.assertEqual(context["owner_skill"], "delivery-release-gate")
        self.assertIn("kubernetes-helm", context["product_surfaces"])
        self.assertNotIn("backend-change-builder", context["selected_skills"])

    def test_permission_action_selects_tool_permission_sandbox(self) -> None:
        context = build_active_skill_context(
            runtime="codex",
            stage="permission",
            surfaces=[],
            event_name="PermissionRequest",
            state={},
            classification={"stage": "permission", "product_surfaces": [], "risk_surfaces": []},
        )
        self.assertIn("agent-tool-permission-sandbox", context["selected_capabilities"])
        self.assertIn(
            "references/capabilities/120-agent-tool-permission-sandbox.md",
            context["required_references"],
        )

    def test_risky_command_state_selects_tool_permission_sandbox(self) -> None:
        state = {
            **_coding_ready_state(),
            "command_risk_surfaces": ["tool-permission-sandbox"],
        }
        context = build_active_skill_context(
            runtime="codex",
            stage="edit",
            surfaces=["backend-product"],
            event_name="PreToolUse",
            state=state,
            classification={
                "stage": "edit",
                "product_surfaces": ["backend-product"],
                "language_surfaces": ["python"],
                "risk_surfaces": [],
            },
        )
        self.assertIn("agent-tool-permission-sandbox", context["selected_capabilities"])
        self.assertIn(
            "references/capabilities/120-agent-tool-permission-sandbox.md",
            context["required_references"],
        )

    def test_classification_permission_state_selects_tool_permission_sandbox(self) -> None:
        context = build_active_skill_context(
            runtime="codex",
            stage="edit",
            surfaces=["backend-product"],
            event_name="PreToolUse",
            state=_coding_ready_state(),
            classification={
                "stage": "edit",
                "product_surfaces": ["backend-product"],
                "language_surfaces": ["python"],
                "risk_surfaces": [],
                "tool_permission_sandbox_seen": True,
            },
        )
        self.assertIn("agent-tool-permission-sandbox", context["selected_capabilities"])
        self.assertIn(
            "references/capabilities/120-agent-tool-permission-sandbox.md",
            context["required_references"],
        )

    def test_release_delivery_deploy_migration_selects_tool_permission_sandbox(self) -> None:
        context = build_active_skill_context(
            runtime="codex",
            stage="release",
            surfaces=["database-migration"],
            event_name="PreToolUse",
            state={},
            classification={
                "stage": "release",
                "product_surfaces": ["database-migration"],
                "risk_surfaces": ["delivery"],
            },
        )
        self.assertEqual(context["current_stage"], "release-delivery")
        self.assertIn("agent-tool-permission-sandbox", context["selected_capabilities"])
        self.assertIn(
            "references/capabilities/120-agent-tool-permission-sandbox.md",
            context["required_references"],
        )

    def test_redis_routes_cache_not_kafka_bigdata(self) -> None:
        context = _context_for(_edit_event("src/cache/redis_store.py", "Redis TTL invalidation"))
        self.assertIn("cache", context["product_surfaces"])
        self.assertEqual(context["owner_skill"], "data-middleware-change-builder")
        self.assertIn("cache-design", context["selected_capabilities"])
        self.assertNotIn("message-queue", context["product_surfaces"])
        self.assertNotIn("bigdata-product-extension", context["selected_domain_extensions"])

    def test_kafka_routes_queue_not_cache(self) -> None:
        context = _context_for(_edit_event("src/queue/kafka_consumer.go", "Kafka DLQ offset replay"))
        self.assertIn("message-queue", context["product_surfaces"])
        self.assertIn("message-queue-design", context["selected_capabilities"])
        self.assertNotIn("cache", context["product_surfaces"])

    def test_ai_rag_selects_ai_not_web3_payment(self) -> None:
        context = _context_for(
            {"hook_event_name": "UserPromptSubmit", "prompt": "Fix RAG permission-aware retrieval for tenant documents"}
        )
        self.assertIn("ai-product-extension", context["selected_domain_extensions"])
        self.assertNotIn("web3-product-extension", context["selected_domain_extensions"])
        self.assertNotIn("payment-trading-extension", context["selected_domain_extensions"])

    def test_web3_signature_selects_web3_not_payment(self) -> None:
        context = _context_for(
            {"hook_event_name": "UserPromptSubmit", "prompt": "Fix Web3 wallet EIP-712 signature nonce replay"}
        )
        self.assertIn("web3-product-extension", context["selected_domain_extensions"])
        self.assertNotIn("payment-trading-extension", context["selected_domain_extensions"])

    def test_web3_sdk_coding_uses_product_owner_not_domain_gate(self) -> None:
        context = build_active_skill_context(
            runtime="codex",
            stage="edit",
            surfaces=["web3", "sdk-library"],
            event_name="PreToolUse",
            state=_coding_ready_state(),
            classification={
                "stage": "edit",
                "product_surfaces": ["web3", "sdk-library"],
                "language_surfaces": ["typescript"],
                "risk_surfaces": ["security"],
                "domain_extensions": ["web3-product-extension"],
            },
        )
        self.assertEqual(context["current_stage"], "coding")
        self.assertEqual(context["owner_skill"], "data-api-contract-changer")
        self.assertIn("web3-product-extension", context["selected_domain_extensions"])

    def test_payment_ledger_selects_payment_not_web3(self) -> None:
        context = _context_for(
            {"hook_event_name": "UserPromptSubmit", "prompt": "Fix payment ledger settlement reconciliation"}
        )
        self.assertIn("payment-trading-extension", context["selected_domain_extensions"])
        self.assertNotIn("web3-product-extension", context["selected_domain_extensions"])

    def test_skill_registry_edit_routes_skill_authoring(self) -> None:
        context = _context_for(_edit_event("src/registry/routing-rules.yaml"))
        self.assertEqual(context["owner_skill"], "change-forge-router")
        self.assertIn("skill-authoring", context["product_surfaces"])
        self.assertIn("repository-context-map", context["selected_capabilities"])
        self.assertIn("skill-authoring-expert", context["selected_capabilities"])
        self.assertIn("skill-efficacy-benchmark", context["selected_capabilities"])
        self.assertIn("plan-execution-consistency", context["selected_capabilities"])
        self.assertNotIn("backend-change-builder", context["selected_skills"])

    def test_prompt_only_skill_authoring_update_routes_skill_authoring(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Update src/registry/routing-rules.yaml and SKILL.md trigger",
        }
        classification = classify_event(event)
        context = _context_for(event)
        self.assertEqual(classification["stage"], "skill_authoring")
        self.assertEqual(context["current_stage"], "skill-authoring")
        self.assertEqual(context["product_surfaces"], ["skill-authoring"])
        self.assertIn("skill-authoring-expert", context["selected_capabilities"])
        self.assertIn("engineering-stage-professionalism", context["selected_capabilities"])
        self.assertNotIn("implementation-structure-design", context["selected_capabilities"])

    def test_bare_business_registry_prompt_does_not_route_skill_authoring(self) -> None:
        prompts = (
            ("Update service registry behavior", "edit"),
            ("Modify package registry cache", "edit"),
            ("Fix user registry table", "repair"),
        )
        for prompt, expected_stage in prompts:
            with self.subTest(prompt=prompt):
                event = {"hook_event_name": "UserPromptSubmit", "prompt": prompt}
                classification = classify_event(event)
                context = _context_for(event)
                self.assertEqual(classification["stage"], expected_stage)
                self.assertNotIn("skill-authoring", context["product_surfaces"])
                self.assertNotEqual(context["current_stage"], "skill-authoring")
                self.assertNotIn("skill-authoring-expert", context["selected_capabilities"])

    def test_skill_md_under_professional_skill_has_skill_authoring_primary_surface(self) -> None:
        context = _context_for(_edit_event("src/professional-skills/change-forge-router/SKILL.md"))
        self.assertEqual(context["current_stage"], "skill-authoring")
        self.assertEqual(context["primary_product_surface"], "skill-authoring")
        self.assertNotIn("documentation-only", context["product_surfaces"])

    def test_unknown_pure_question_has_no_injection(self) -> None:
        classification = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": "what is this concept?"})
        self.assertFalse(classification["should_inject"])
        self.assertEqual(classification["product_surfaces"], [])

    def test_completed_preflight_test_plan_enters_coding_without_validation_run(self) -> None:
        context = build_active_skill_context(
            runtime="codex",
            stage="edit",
            surfaces=["backend-product"],
            event_name="PreToolUse",
            state=_coding_ready_state(),
            classification={
                "stage": "edit",
                "product_surfaces": ["backend-product"],
                "language_surfaces": ["python"],
                "risk_surfaces": [],
            },
        )
        self.assertEqual(context["current_stage"], "coding")
        self.assertFalse(_coding_ready_state()["validation_command_seen"])

    def test_multi_surface_route_preserves_secondary_surface_capabilities(self) -> None:
        context = build_active_skill_context(
            runtime="codex",
            stage="edit",
            surfaces=["backend-product", "api-contract"],
            event_name="PreToolUse",
            state=_coding_ready_state(),
            classification={
                "stage": "edit",
                "product_surfaces": ["backend-product", "api-contract"],
                "language_surfaces": ["python"],
                "risk_surfaces": ["data-api"],
            },
        )
        self.assertEqual(context["product_surfaces"], ["backend-product", "api-contract"])
        self.assertEqual(context["product_surface"], "backend-product")
        self.assertEqual(context["primary_product_surface"], "backend-product")
        self.assertIn("api-contract-design", context["selected_capabilities"])

    def test_skipped_capabilities_are_only_foundation_capabilities(self) -> None:
        context = _context_for(_edit_event("src/components/ProfileCard.tsx"))
        skipped = [
            item["capability"]
            for item in context["skipped_capabilities"]
            if isinstance(item, dict) and "capability" in item
        ]
        self.assertTrue(set(skipped).issubset(set(CAPABILITY_IDS)))
        self.assertNotIn("backend-change-builder", skipped)
        self.assertNotIn("frontend-change-builder", skipped)
        self.assertNotIn("product-coding-owner", skipped)
        skipped_skills = [
            item["skill"]
            for item in context["skipped_skills"]
            if isinstance(item, dict) and "skill" in item
        ]
        self.assertIn("backend-change-builder", skipped_skills)

    def test_user_prompt_submit_resets_state_unless_follow_up(self) -> None:
        old_cache = os.environ.get("XDG_CACHE_HOME")
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            repo = Path(cwd)
            merge_state(
                repo,
                "codex",
                changed_paths=["src/services/order_service.py"],
                risk_surfaces=["security"],
                suggested_skills=["backend-change-builder"],
            )
            reset_state_for_new_prompt(
                repo,
                "codex",
                {"hook_event_name": "UserPromptSubmit", "prompt": "Update docs only"},
            )
            state = load_state(repo)
            self.assertEqual(state["changed_paths"], [])
            self.assertEqual(state["risk_surfaces"], [])
            self.assertEqual(state["suggested_skills"], [])

            merge_state(repo, "codex", changed_paths=["src/services/order_service.py"])
            reset_state_for_new_prompt(
                repo,
                "codex",
                {"hook_event_name": "UserPromptSubmit", "prompt": "continue the same PR review"},
            )
            self.assertEqual(load_state(repo)["changed_paths"], ["src/services/order_service.py"])
        if old_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = old_cache


def _coding_ready_state() -> dict[str, object]:
    return {
        "read_evidence_seen": True,
        "implementation_preflight_required": True,
        "implementation_preflight_complete": True,
        "implementation_preflights": ["paths=src/services/order_service.py; fields=test_plan,risk"],
        "pre_edit_missing_test_plan": False,
        "validation_command_seen": False,
        "validation_seen": False,
    }


if __name__ == "__main__":
    unittest.main()
