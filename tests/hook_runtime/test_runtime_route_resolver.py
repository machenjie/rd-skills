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
from changeforge_runtime_route_resolver import build_active_skill_context  # noqa: E402


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

    def test_chart_values_route_delivery_not_backend(self) -> None:
        context = _context_for(_edit_event("deploy/chart/values.yaml", "helm Chart.yaml rollout"))
        self.assertEqual(context["owner_skill"], "delivery-release-gate")
        self.assertIn("kubernetes-helm", context["product_surfaces"])
        self.assertNotIn("backend-change-builder", context["selected_skills"])

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
        self.assertIn("skill-authoring-expert", context["selected_capabilities"])
        self.assertNotIn("backend-change-builder", context["selected_skills"])

    def test_unknown_pure_question_has_no_injection(self) -> None:
        classification = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": "what is this concept?"})
        self.assertFalse(classification["should_inject"])
        self.assertEqual(classification["product_surfaces"], [])

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


if __name__ == "__main__":
    unittest.main()
