from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def run_structure(event: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event["cwd"] = cwd
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env.pop("CHANGEFORGE_HOOK_MODE", None)
        env.pop("CHANGEFORGE_AGENT", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "changeforge_post_edit_structure_gate.py")],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=cwd,
            env=env,
            check=False,
        )


def run_gate(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str | None = None,
    agent: str | None = None,
) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    if mode is None:
        env.pop("CHANGEFORGE_HOOK_MODE", None)
    else:
        env["CHANGEFORGE_HOOK_MODE"] = mode
    if agent is None:
        env.pop("CHANGEFORGE_AGENT", None)
    else:
        env["CHANGEFORGE_AGENT"] = agent
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "changeforge_post_edit_structure_gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def apply_patch_event(patch: str) -> dict:
    return {
        "runtime": "codex",
        "hook_event_name": "PostToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": patch},
    }


def add_file_patch(path: str, body: str) -> str:
    lines = "\n".join(f"+{line}" for line in body.splitlines())
    return f"*** Begin Patch\n*** Add File: {path}\n{lines}\n*** End Patch\n"


def _git_init(cwd: Path) -> None:
    # Pin the hook's repo_root resolution to this temp dir so sibling-file
    # discovery is deterministic regardless of any parent git repository.
    subprocess.run(
        ["git", "init", "-q"],
        cwd=str(cwd),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class PostEditStructureGateTests(unittest.TestCase):
    def test_readme_edit_does_not_warn(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "README.md"},
        }
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Structure Gate triggered", result.stdout)

    def test_new_service_file_warns(self) -> None:
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_apply_patch.json").read_text())
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Structure Gate triggered", result.stdout)
        self.assertIn("implementation-structure-design", result.stdout)

    def test_utils_common_shared_edit_warns(self) -> None:
        event = {
            "runtime": "claude",
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/shared/utils/date_helpers.py"},
        }
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Structure Gate triggered", result.stdout)

    def test_file_naming_mismatch_against_siblings_warns(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s).resolve()
            cache = Path(cache_s)
            _git_init(cwd)
            collector = cwd / "collector"
            collector.mkdir()
            for name in ("exchange.go", "rvol.go", "source_whitelist.go", "exchange_test.go"):
                (collector / name).write_text("package collector\n", encoding="utf-8")
            event = apply_patch_event(
                add_file_patch("collector/exchangeInfo.go", "package collector\n\nvar localValue = 1")
            )
            result = run_gate(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("file naming findings", result.stdout)
        self.assertIn("camelCase/PascalCase", result.stdout)

    def test_file_naming_few_siblings_no_strong_warning(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s).resolve()
            cache = Path(cache_s)
            _git_init(cwd)
            collector = cwd / "collector"
            collector.mkdir()
            (collector / "exchange.go").write_text("package collector\n", encoding="utf-8")
            event = apply_patch_event(
                add_file_patch("collector/exchangeInfo.go", "package collector\n\nvar localValue = 1")
            )
            result = run_gate(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        # New file still produces a weak structural reminder, but the gate must
        # not make a strong naming-mismatch judgment with too few siblings.
        self.assertNotIn("file naming findings", result.stdout)

    def test_new_utils_helper_file_triggers_reuse_gate(self) -> None:
        event = apply_patch_event(
            add_file_patch("src/lib/utils/string_utils.py", "def slugify(value):\n    return value.lower()")
        )
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("reuse findings", result.stdout)

    def test_new_repository_service_file_triggers_reuse_and_placement(self) -> None:
        event = apply_patch_event(
            add_file_patch(
                "internal/services/order_repository.go",
                "package services\n\nfunc NewOrderRepository() error { return nil }",
            )
        )
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("reuse findings", result.stdout)
        self.assertIn("implementation-structure-design", result.stdout)

    def test_extension_reuse_gate_on_modified_function_with_case(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Update File: internal/router/dispatch.go\n"
            "@@\n"
            " func Dispatch(kind string) error {\n"
            "     switch kind {\n"
            "     case \"a\":\n"
            "         return handleA()\n"
            "+    case \"b\":\n"
            "+        return handleB()\n"
            "     }\n"
            "+    return nil\n"
            " }\n"
            "*** End Patch\n"
        )
        result = run_structure(apply_patch_event(patch))
        self.assertEqual(result.returncode, 0)
        self.assertIn("extension reuse findings", result.stdout)

    def test_advanced_refactor_keywords_trigger_gate(self) -> None:
        body = (
            "export interface PaymentStrategy {\n"
            "  pay(): void;\n"
            "}\n"
            "export class CardPayment implements PaymentStrategy {\n"
            "  pay() {}\n"
            "}"
        )
        result = run_structure(apply_patch_event(add_file_patch("src/payment/strategy.ts", body)))
        self.assertEqual(result.returncode, 0)
        self.assertIn("advanced refactor findings", result.stdout)

    def test_go_exported_function_without_doc_comment_triggers_comment_gate(self) -> None:
        body = "package collector\n\nfunc ExchangeInfo() error {\n    return nil\n}"
        result = run_structure(apply_patch_event(add_file_patch("collector/exchange_info.go", body)))
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment findings", result.stdout)
        self.assertIn("exported function", result.stdout)

    def test_go_test_function_triggers_comment_reminder(self) -> None:
        body = (
            "package order\n\n"
            "func TestCreateOrder(t *testing.T) {\n"
            "    if Create() == nil {\n"
            "        t.Fatal(\"expected order\")\n"
            "    }\n"
            "}"
        )
        result = run_structure(apply_patch_event(add_file_patch("internal/order/order_test.go", body)))
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment findings", result.stdout)
        self.assertIn("test", result.stdout)

    def test_typescript_export_function_triggers_comment_gate(self) -> None:
        body = (
            "export function fetchOrders(): Promise<Order[]> {\n"
            "  return http.get('/orders');\n"
            "}"
        )
        result = run_structure(apply_patch_event(add_file_patch("web/src/api/orders.ts", body)))
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment findings", result.stdout)

    def test_python_complex_public_def_triggers_comment_gate(self) -> None:
        body = (
            "def reconcile_ledger(entries):\n"
            "    total = 0\n"
            "    for entry in entries:\n"
            "        total += entry.amount\n"
            "    return total"
        )
        result = run_structure(apply_patch_event(add_file_patch("billing/reconcile.py", body)))
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment findings", result.stdout)
        self.assertIn("public function", result.stdout)

    def test_complex_logic_keywords_trigger_comment_gate(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Update File: internal/payment/charge.go\n"
            "@@\n"
            " func charge() {\n"
            "+    if shouldRetry() { doRetry() }\n"
            "+    useCache()\n"
            "+    beginTransaction()\n"
            "+    enforceSecurity()\n"
            " }\n"
            "*** End Patch\n"
        )
        result = run_structure(apply_patch_event(patch))
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment findings", result.stdout)
        self.assertIn("complex logic", result.stdout)

    def test_private_helper_does_not_trigger_strong_comment_reminder(self) -> None:
        body = "package widget\n\nfunc helper() int {\n    return 1\n}"
        result = run_structure(apply_patch_event(add_file_patch("pkg/widget/widget.go", body)))
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("comment findings", result.stdout)

    def test_monitor_mode_updates_state_without_warning(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s).resolve()
            cache = Path(cache_s)
            event = apply_patch_event(
                add_file_patch("internal/services/order_service.go", "package services")
            )
            result = run_gate(event, cwd, cache, mode="monitor")
            state_files = list(cache.glob("changeforge/hooks/*/current-turn.json"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(state_files), 1)

    def test_warn_mode_outputs_codex_additional_context(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s).resolve()
            cache = Path(cache_s)
            event = apply_patch_event(
                add_file_patch("internal/services/order_service.go", "package services")
            )
            result = run_gate(event, cwd, cache, mode="warn", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("additionalContext", payload["hookSpecificOutput"])
        self.assertIn(
            "ChangeForge Structure Gate triggered",
            payload["hookSpecificOutput"]["additionalContext"],
        )

    def test_block_mode_outputs_block_decision(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s).resolve()
            cache = Path(cache_s)
            event = apply_patch_event(
                add_file_patch("internal/services/order_service.go", "package services")
            )
            result = run_gate(event, cwd, cache, mode="block", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")

    def test_missing_sibling_directory_fails_open(self) -> None:
        body = "package collector\n\nfunc ExchangeInfo() error { return nil }"
        # The added file lives in a directory that does not exist on disk; the
        # file-naming scan must fail open rather than crash.
        result = run_structure(apply_patch_event(add_file_patch("nowhere/deep/exchangeInfo.go", body)))
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
