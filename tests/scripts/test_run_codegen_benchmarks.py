from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "hookless_codegen_runner_tests",
        SCRIPTS / "run-codegen-benchmarks.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


class CodegenBenchmarkEvidenceTests(unittest.TestCase):
    def test_default_limit_selects_assertion_backed_cases(self) -> None:
        args = argparse.Namespace(
            category=None,
            benchmark=None,
            limit=3,
            candidate_dir=None,
            candidate_root=None,
        )
        cases = RUNNER._select_cases(args)
        self.assertEqual(3, len(cases))
        self.assertTrue(all(RUNNER._real_assertion_files(case_dir) for _, _, case_dir in cases))

    def test_evidence_snapshot_excludes_control_artifacts_links_and_final(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "evidence"
            (source / ".agents/skills/example").mkdir(parents=True)
            (source / ".agents/skills/example/SKILL.md").write_text("bait\n", encoding="utf-8")
            (source / ".codex/agents").mkdir(parents=True)
            (source / ".codex/agents/task.toml").write_text("bait\n", encoding="utf-8")
            (source / "src").mkdir()
            (source / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (source / "final.md").write_text("answer bait\n", encoding="utf-8")
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            (source / "src/escape.txt").symlink_to(outside)
            os.link(outside, source / "src/hardlink.txt")

            RUNNER._copy_candidate_evidence(source, destination)

            self.assertTrue((destination / "src/app.py").is_file())
            self.assertFalse((destination / ".agents").exists())
            self.assertFalse((destination / ".codex").exists())
            self.assertFalse((destination / "final.md").exists())
            self.assertFalse((destination / "src/escape.txt").exists())
            self.assertFalse((destination / "src/hardlink.txt").exists())

    def test_assertion_runner_executes_zero_argument_test_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "test_free_function.py"
            path.write_text("def test_failure() -> None:\n    assert False\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(RUNNER.ASSERTION_RUNNER), str(path)],
                cwd=ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, completed.returncode)
            self.assertIn("AssertionError", completed.stdout + completed.stderr)

    def test_candidate_setup_is_not_executed(self) -> None:
        case_dir = ROOT / "evals/codegen/review/repair-rereview-required"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            shutil.copytree(case_dir / "starter-repo", candidate)
            marker = root / "candidate-setup-ran"
            (candidate / "setup.sh").write_text(
                f"#!/usr/bin/env bash\ntouch {marker}\n",
                encoding="utf-8",
            )

            RUNNER._run_case("review", "repair-rereview-required", case_dir, candidate)
            self.assertFalse(marker.exists())

    def test_assertion_environment_does_not_inherit_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_dir = root / "case"
            assertion_dir = case_dir / "test-suite/tests"
            assertion_dir.mkdir(parents=True)
            (assertion_dir / "test_environment.py").write_text(
                "import os\n\ndef test_no_secret() -> None:\n"
                "    assert os.getenv('OPENAI_API_KEY') is None\n",
                encoding="utf-8",
            )
            candidate = root / "candidate"
            candidate.mkdir()
            (candidate / "README.md").write_text("candidate\n", encoding="utf-8")

            with mock.patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "must-not-leak"},
            ):
                errors = RUNNER._run_assertion_files(
                    "test",
                    "environment",
                    case_dir,
                    candidate,
                )
            self.assertEqual([], errors)

    def test_checked_in_harness_environment_does_not_inherit_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "run.sh"
            script.write_text(
                "#!/usr/bin/env bash\n"
                "test -z \"${OPENAI_API_KEY:-}\"\n",
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ,
                {**os.environ, "OPENAI_API_KEY": "must-not-leak"},
                clear=True,
            ):
                ok, output, returncode = RUNNER._run_script(
                    "test-suite",
                    script,
                    root,
                    {"PYTHONDONTWRITEBYTECODE": "1"},
                )
            self.assertTrue(ok, output)
            self.assertEqual(0, returncode)

    def test_candidate_cli_requires_explicit_execution_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate"
            candidate.mkdir()
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SystemExit) as raised:
                    RUNNER.main(
                        [
                            "--benchmark",
                            "security/ssrf-url-allowlist",
                            "--candidate-dir",
                            str(candidate),
                        ]
                    )
            self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
