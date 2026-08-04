from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-hookless-residue.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_hookless_residue", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemovedBenchmarkResidueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_removed_paths_and_tokens_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            removed = root / "evals/codex-live"
            removed.mkdir(parents=True)
            runtime = root / "runtime"
            runtime.mkdir()
            (runtime / ".gitkeep").write_text("", encoding="utf-8")
            source = root / "docs/reference.md"
            source.parent.mkdir(parents=True)
            source.write_text("CHANGEFORGE_RUN_CODEX_LIVE and --require-live", encoding="utf-8")

            path_errors = self.module._forbidden_path_errors(root)
            token_errors = self.module._live_benchmark_token_errors(root)

            self.assertTrue(any("evals/codex-live" in error for error in path_errors), path_errors)
            self.assertTrue(any("runtime" in error for error in path_errors), path_errors)
            self.assertTrue(any("CHANGEFORGE_RUN_CODEX_LIVE" in error for error in token_errors), token_errors)
            self.assertTrue(any("--require-live" in error for error in token_errors), token_errors)

    def test_shell_and_extensionless_script_tokens_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            scripts = root / "scripts"
            scripts.mkdir()
            shell_script = scripts / "legacy.sh"
            shell_script.write_text(
                "#!/bin/sh\nCHANGEFORGE_RUN_CODEX_LIVE=1\n",
                encoding="utf-8",
            )
            extensionless_script = scripts / "legacy-runner"
            extensionless_script.write_text(
                "#!/bin/sh\nexec validator --require-live\n",
                encoding="utf-8",
            )

            errors = self.module._live_benchmark_token_errors(root)

            self.assertTrue(
                any("scripts/legacy.sh" in error and "CHANGEFORGE_RUN_CODEX_LIVE" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("scripts/legacy-runner" in error and "--require-live" in error for error in errors),
                errors,
            )

    def test_tmp_text_and_parse_codex_jsonl_token_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            temporary = root / ".dev/obsolete.tmp"
            temporary.parent.mkdir(parents=True)
            temporary.write_text(
                "python3 scripts/parse-codex-jsonl.py",
                encoding="utf-8",
            )

            errors = self.module._live_benchmark_token_errors(root)

            self.assertTrue(
                any(".dev/obsolete.tmp" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("parse-codex-jsonl.py" in error for error in errors),
                errors,
            )

    def test_removed_source_bytecode_names_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            cache = root / "scripts/__pycache__"
            cache.mkdir(parents=True)
            for stem in self.module.FORBIDDEN_BYTECODE_STEMS:
                (cache / f"{stem}.cpython-314.pyc").write_bytes(b"obsolete")

            errors = self.module._forbidden_bytecode_errors(root)

            for stem in self.module.FORBIDDEN_BYTECODE_STEMS:
                self.assertTrue(
                    any(stem in error for error in errors),
                    (stem, errors),
                )

    def test_known_validation_tmp_paths_are_rejected_regardless_of_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            targets = (
                ".dev/validation-p0-fixes.tmp",
                ".dev/validation-p0-fixes-remaining.tmp",
            )
            for target in targets:
                path = root / target
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("benign text without obsolete tokens\n", encoding="utf-8")

            errors = self.module._forbidden_path_errors(root)

            for target in targets:
                self.assertTrue(
                    any(target in error for error in errors),
                    (target, errors),
                )

    def test_hook_runtime_content_references_are_rejected(self) -> None:
        expected_tokens = (
            "tests/hook_runtime",
            "tests/fixtures/hooks",
            "tests/hooks",
            "hook reminder behavior",
            "hook fixture",
        )
        self.assertTrue(
            set(expected_tokens).issubset(
                self.module.FORBIDDEN_HOOKLESS_AI_CONTENT_TOKENS
            )
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            references = root / "src/foundation/capabilities/example/references"
            references.mkdir(parents=True)
            for index, token in enumerate(expected_tokens):
                (references / f"obsolete-{index}.md").write_text(
                    f"# Obsolete\n\n{token}\n", encoding="utf-8"
                )

            errors = self.module._forbidden_ai_content_token_errors(root)

            for token in expected_tokens:
                self.assertTrue(
                    any(token in error for error in errors),
                    (token, errors),
                )

    def test_hookless_content_does_not_trigger_hook_residue_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "src/foundation/capabilities/example/SKILL.md"
            reference.parent.mkdir(parents=True)
            reference.write_text(
                "# Hookless authoring\n\n"
                "Use deterministic validator evidence.\n"
                "Use a webhook fixture to test signature validation.\n"
                "Use tests/hooks-and-events for event adapters.\n"
                "The removed hook fixture must not be\n"
                "restored.\n",
                encoding="utf-8",
            )

            errors = self.module._forbidden_ai_content_token_errors(root)

        self.assertEqual([], errors)

    def test_history_prohibition_cannot_hide_active_hook_residue(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "src/foundation/capabilities/example/SKILL.md"
            reference.parent.mkdir(parents=True)
            reference.write_text(
                "# Mixed residue\n\n"
                "Never restore the old cache; use tests/hooks for active coverage.\n\n"
                "Never restore old hooks; current tests/hooks remain authoritative.\n\n"
                "The removed hook fixture must not be restored; "
                "use tests/hooks for current behavior.\n",
                encoding="utf-8",
            )

            errors = self.module._forbidden_ai_content_token_errors(root)

        self.assertEqual(3, sum("tests/hooks" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
