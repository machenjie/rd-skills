from __future__ import annotations

import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
RUNNER_PATH = SCRIPTS / "run-ci-tests.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_ci_tests", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CiTestRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = _load_runner()
        cls.core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )

    def test_selection_is_the_unsharded_shared_resolver_result(self) -> None:
        resolved = {
            "schema_version": 1,
            "kind": "changeforge.impact_selection",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "status": "resolved",
            "reason": "affected-targets",
            "changed_paths": [],
            "selected_producer_ids": ["validate-task-contracts"],
            "selected_test_modules": [
                "tests/scripts/test_validation_utils.py",
                "tests/scripts/test_run_ci_tests.py",
                "tests/scripts/test_impact_graph.py",
            ],
            "selected_test_modules_by_layer": {
                "unit": ["tests/scripts/test_validation_utils.py"],
                "integration": [],
                "contract": [
                    "tests/scripts/test_impact_graph.py",
                    "tests/scripts/test_run_ci_tests.py",
                ],
                "governance": [],
                "release": [],
            },
            "producer_explanations": [],
        }
        with mock.patch.object(self.runner, "select", return_value=resolved) as select:
            result = self.runner._selection(
                ROOT, self.core, resolved["base_sha"], resolved["head_sha"]
            )
        select.assert_called_once_with(
            ROOT, self.core, resolved["base_sha"], resolved["head_sha"]
        )
        self.assertEqual(resolved, result)
        self.assertNotIn("shards", result)

    def test_runner_projects_resolver_flat_targets_without_layer_policy(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("always_layers", source)
        self.assertNotIn("direct_only_layers", source)
        self.assertNotIn("forbidden_layers", source)
        real_pattern = ROOT / "tests/scripts/test_professional_completeness_schema3.py"
        self.assertEqual(
            "repository-root-temporary-state",
            self.runner._exclusive_lane_reason(real_pattern),
        )

        with tempfile.TemporaryDirectory() as raw:
            harmless = Path(raw) / "test_harmless_root_attribute.py"
            harmless.write_text(
                textwrap.dedent(
                    """
                    import tempfile
                    import unittest

                    class Panel:
                        ROOT_SEMANTIC_SCHEMA_VERSION = 5

                    PANEL = Panel()

                    class Harmless(unittest.TestCase):
                        def test_harmless(self):
                            with tempfile.TemporaryDirectory():
                                self.assertEqual(5, PANEL.ROOT_SEMANTIC_SCHEMA_VERSION)
                    """
                ),
                encoding="utf-8",
            )
            self.assertIsNone(self.runner._exclusive_lane_reason(harmless))

    def test_jobs_one_and_two_preserve_the_same_selection_and_decisions(self) -> None:
        selection = {
            "reason": "affected-targets",
            "selected_test_modules": [
                "tests/scripts/test_impact_graph.py",
                "tests/scripts/test_run_ci_tests.py",
            ],
            "changed_paths": [{"path": "scripts/run-ci-tests.py"}],
        }
        with mock.patch.object(
            self.runner, "load_core", return_value=self.core
        ), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ) as selected, mock.patch.object(
            self.runner, "_execute_modules", return_value=[]
        ) as execute, mock.patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(0, self.runner.main(["run", "--jobs", "1"]))
            self.assertEqual(0, self.runner.main(["run", "--jobs", "2"]))

        payloads = [
            payload
            for line in stdout.getvalue().splitlines()
            if "reason" in (payload := json.loads(line))
        ]
        self.assertEqual(
            ["affected-targets", "affected-targets"],
            [payload["reason"] for payload in payloads],
        )
        self.assertEqual(2, selected.call_count)
        self.assertEqual(
            [
                mock.call(
                    ROOT,
                    selection["selected_test_modules"],
                    jobs=1,
                    timeout_seconds=self.runner.DEFAULT_TIMEOUT_SECONDS,
                ),
                mock.call(
                    ROOT,
                    selection["selected_test_modules"],
                    jobs=2,
                    timeout_seconds=self.runner.DEFAULT_TIMEOUT_SECONDS,
                ),
            ],
            execute.call_args_list,
        )

    def test_affected_child_argv_stays_direct_without_signal_mask_support(
        self,
    ) -> None:
        arguments = ("-m", "unittest", "tests/scripts/test_probe.py")
        expected = [sys.executable, "-P", *arguments]
        with self.subTest(platform="non-posix"), mock.patch.object(
            self.runner.os, "name", "nt"
        ), mock.patch.object(self.runner, "Path") as path:
            self.assertEqual(expected, self.runner._python_child_command(*arguments))
            path.assert_not_called()
        with self.subTest(platform="posix-without-pthread-sigmask"), mock.patch.object(
            self.runner.os, "name", "posix"
        ), mock.patch.object(
            self.runner.signal, "pthread_sigmask", None, create=True
        ):
            self.assertEqual(expected, self.runner._python_child_command(*arguments))

    def test_full_fails_closed_before_unsupported_child_dispatch(self) -> None:
        module = "tests/scripts/test_probe.py"
        with mock.patch.object(
            self.runner, "_supports_owned_process_groups", return_value=True
        ), mock.patch.object(
            self.runner, "_supports_atomic_interrupt_lifecycle", return_value=False
        ), mock.patch.object(self.runner.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(
                self.runner.SelectionError, "atomic signal lifecycle"
            ):
                self.runner._discover_full_manifest(ROOT, timeout_seconds=5.0)
            popen.assert_not_called()

        with mock.patch.object(
            self.runner, "_supports_owned_process_groups", return_value=True
        ), mock.patch.object(
            self.runner, "_supports_atomic_interrupt_lifecycle", return_value=False
        ), mock.patch.object(self.runner, "_start_worker") as start:
            with self.assertRaisesRegex(
                self.runner.SelectionError, "atomic signal lifecycle"
            ):
                self.runner._execute_full_modules(
                    ROOT,
                    [module],
                    exclusive_modules=[],
                    jobs=1,
                    timeout_seconds=5.0,
                )
            start.assert_not_called()

        with mock.patch.object(
            self.runner, "_supports_atomic_interrupt_lifecycle", return_value=False
        ), mock.patch.object(self.runner.subprocess, "Popen") as popen, mock.patch.object(
            self.runner, "_start_worker"
        ) as start, mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual(2, self.runner.main(["full"]))
            popen.assert_not_called()
            start.assert_not_called()

    @staticmethod
    def _write_test(root: Path, name: str, body: str) -> str:
        path = root / name
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return name

    @staticmethod
    def _write_discovery_test(root: Path, relative: str, body: str) -> str:
        path = root / "tests" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path.relative_to(root).as_posix()

    def _discovery_root(self, root: Path) -> None:
        (root / "tests/scripts").mkdir(parents=True)
        (root / "tests/__init__.py").write_text("", encoding="utf-8")
        (root / "tests/scripts/__init__.py").write_text("", encoding="utf-8")

    @staticmethod
    def _signal_mask_probe_source(marker: Path | None = None) -> str:
        destination = (
            f"Path({str(marker)!r}).write_text(encoded, encoding='utf-8')"
            if marker is not None
            else "print('SIGNAL_MASK ' + encoded, flush=True)"
        )
        return textwrap.dedent(
            f"""
            import json
            import os
            from pathlib import Path
            import signal
            import unittest

            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, ())
            encoded = json.dumps(
                {{
                    "blocked": sorted(int(number) for number in blocked),
                    "pgid": os.getpgrp(),
                    "pid": os.getpid(),
                    "sid": os.getsid(0),
                }},
                sort_keys=True,
            )
            {destination}

            class SignalMaskProbe(unittest.TestCase):
                def test_probe(self):
                    self.assertTrue(True)
            """
        )

    def test_full_resource_classifier_accepts_closed_literals_and_missing_default(
        self,
    ) -> None:
        fixtures = {
            "standard": "FULL_TEST_RESOURCE_CLASS = 'standard'\n",
            "heavy": "FULL_TEST_RESOURCE_CLASS = 'heavy'\n",
            "tokenizer": "FULL_TEST_RESOURCE_CLASS = 'tokenizer'\n",
            "heavy-tokenizer": (
                "FULL_TEST_RESOURCE_CLASS: str = 'heavy-tokenizer'\n"
            ),
            "missing": "import unittest\n",
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for expected, source in fixtures.items():
                with self.subTest(expected=expected):
                    path = root / f"test_{expected}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertEqual(
                        "standard" if expected == "missing" else expected,
                        self.runner._full_test_resource_class(path),
                    )

    def test_timeout_classifier_accepts_closed_literal_and_missing_default(
        self,
    ) -> None:
        fixtures = {
            "standard": "TEST_TIMEOUT_CLASS = 'standard'\n",
            "source-validation": (
                "TEST_TIMEOUT_CLASS: str = 'source-validation'\n"
            ),
            "missing": "import unittest\n",
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for expected, source in fixtures.items():
                with self.subTest(expected=expected):
                    path = root / f"test_{expected}.py"
                    path.write_text(source, encoding="utf-8")
                    self.assertEqual(
                        "standard" if expected == "missing" else expected,
                        self.runner._test_timeout_class(path),
                    )

    def test_timeout_classifier_rejects_duplicate_dynamic_and_unknown_classes(
        self,
    ) -> None:
        fixtures = {
            "duplicate": (
                "TEST_TIMEOUT_CLASS = 'source-validation'\n"
                "TEST_TIMEOUT_CLASS = 'standard'\n",
                "duplicate",
            ),
            "dynamic": (
                "TEST_TIMEOUT_CLASS = 'source-validation'.strip()\n",
                "dynamic",
            ),
            "nested": (
                "if True:\n    TEST_TIMEOUT_CLASS = 'source-validation'\n",
                "top-level",
            ),
            "unknown": ("TEST_TIMEOUT_CLASS = 'unbounded'\n", "unknown"),
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for label, (source, expected_reason) in fixtures.items():
                with self.subTest(label=label):
                    path = root / f"test_{label}.py"
                    path.write_text(source, encoding="utf-8")
                    with self.assertRaisesRegex(
                        self.runner.SelectionError,
                        (
                            f"timeout class.*{expected_reason}"
                            f"|{expected_reason}.*timeout class"
                        ),
                    ):
                        self.runner._test_timeout_class(path)

    def test_source_validation_timeout_class_extends_only_declared_worker(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            standard = self._write_test(
                root,
                "test_standard.py",
                """
                import unittest
                class Standard(unittest.TestCase):
                    def test_standard(self):
                        self.assertTrue(True)
                """,
            )
            source_validation = self._write_test(
                root,
                "test_source_validation.py",
                """
                import time
                import unittest
                TEST_TIMEOUT_CLASS = "source-validation"
                class SourceValidation(unittest.TestCase):
                    def test_source_validation(self):
                        time.sleep(1.2)
                        self.assertTrue(True)
                """,
            )
            results = self.runner._execute_modules(
                root,
                [standard, source_validation],
                jobs=1,
                timeout_seconds=1.0,
            )

        self.assertEqual(
            [(source_validation, "pass"), (standard, "pass")],
            [(result.module, result.status) for result in results],
        )

    def test_source_validation_timeout_owners_are_exact(self) -> None:
        expected = {
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_eval_rendered_context_budget.py",
        }
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in sorted((ROOT / "tests").rglob("test*.py"))
            if self.runner._test_timeout_class(path) == "source-validation"
        }
        self.assertEqual(expected, actual)
        for module in sorted(expected):
            with self.subTest(module=module):
                self.assertEqual(
                    2 * self.runner.DEFAULT_TIMEOUT_SECONDS,
                    self.runner._test_timeout_seconds(
                        ROOT, module, self.runner.DEFAULT_TIMEOUT_SECONDS
                    ),
                )

    @unittest.skipUnless(os.name == "posix", "POSIX full regression discovery")
    def test_full_discovery_rejects_duplicate_dynamic_and_unknown_resource_classes(
        self,
    ) -> None:
        fixtures = {
            "duplicate": (
                (
                    "FULL_TEST_RESOURCE_CLASS = 'heavy'\n"
                    "FULL_TEST_RESOURCE_CLASS = 'standard'\n"
                ),
                "duplicate",
            ),
            "dynamic": (
                "FULL_TEST_RESOURCE_CLASS = 'heavy'.strip()\n",
                "dynamic",
            ),
            "import-binding": (
                "from math import pi as FULL_TEST_RESOURCE_CLASS\n",
                "dynamic",
            ),
            "function-binding": (
                "def FULL_TEST_RESOURCE_CLASS(): return 'heavy'\n",
                "dynamic",
            ),
            "unknown": ("FULL_TEST_RESOURCE_CLASS = 'gpu'\n", "unknown"),
        }
        for label, (declaration, expected_reason) in fixtures.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._discovery_root(root)
                self._write_discovery_test(
                    root,
                    "scripts/test_invalid_resource.py",
                    declaration
                    + "import unittest\n"
                    + "class ResourceProbe(unittest.TestCase):\n"
                    + "    def test_one(self): pass\n",
                )
                with self.assertRaisesRegex(
                    self.runner.SelectionError,
                    (
                        f"resource class.*{expected_reason}"
                        f"|{expected_reason}.*resource class"
                    ),
                ):
                    self.runner._discover_full_manifest(root, timeout_seconds=5.0)

    @unittest.skipUnless(os.name == "posix", "POSIX full regression discovery")
    def test_full_discovery_lists_every_test_module_and_id_without_running(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._discovery_root(root)
            marker = root / "must-not-run"
            (root / "tests/scripts/support.py").write_text(
                "SUPPORT_VALUE = 3\n", encoding="utf-8"
            )
            self._write_discovery_test(
                root,
                "scripts/test_alpha.py",
                f"""
                import pathlib
                import unittest
                import scripts.support

                FULL_TEST_RESOURCE_CLASS = "heavy"
                RESOURCE_CLASS_USES = {{}}
                RESOURCE_CLASS_USES[FULL_TEST_RESOURCE_CLASS] = True

                class Alpha(unittest.TestCase):
                    def test_one(self):
                        pathlib.Path({str(marker)!r}).write_text("ran")

                    def test_two(self):
                        self.assertEqual(3, scripts.support.SUPPORT_VALUE)
                """,
            )
            self._write_discovery_test(
                root,
                "scripts/test_empty.py",
                "VALUE = 'discovered but contains no test cases'\n",
            )
            self._write_discovery_test(
                root,
                "test_top.py",
                """
                import unittest
                class Top(unittest.TestCase):
                    def test_three(self):
                        self.assertTrue(True)
                """,
            )
            self._write_discovery_test(
                root,
                "scripts/test_root_temp.py",
                """
                import tempfile
                import unittest
                from pathlib import Path
                ROOT = Path(__file__).resolve().parents[2]
                class RootTemporary(unittest.TestCase):
                    def test_root_temporary(self):
                        with tempfile.TemporaryDirectory(dir=ROOT):
                            pass
                """,
            )

            manifest = self.runner._discover_full_manifest(root, timeout_seconds=5.0)

        self.assertFalse(marker.exists())
        self.assertEqual(
            [
                "tests/scripts/test_alpha.py",
                "tests/scripts/test_empty.py",
                "tests/scripts/test_root_temp.py",
                "tests/test_top.py",
            ],
            manifest.modules,
        )
        self.assertEqual(
            [
                "scripts.test_alpha.Alpha.test_one",
                "scripts.test_alpha.Alpha.test_two",
                "scripts.test_root_temp.RootTemporary.test_root_temporary",
                "test_top.Top.test_three",
            ],
            manifest.test_ids,
        )
        self.assertEqual(
            ["tests/scripts/test_root_temp.py"], manifest.exclusive_modules
        )
        self.assertEqual(
            {
                "tests/scripts/test_alpha.py": "heavy",
                "tests/scripts/test_empty.py": "standard",
                "tests/scripts/test_root_temp.py": "standard",
                "tests/test_top.py": "standard",
            },
            manifest.resource_classes,
        )
        self.assertNotIn("tests/scripts/support.py", manifest.modules)

    @unittest.skipUnless(
        os.name == "posix"
        and hasattr(signal, "pthread_sigmask")
        and hasattr(signal, "SIGUSR1"),
        "POSIX child signal-mask bootstrap",
    )
    def test_full_discovery_child_unblocks_only_runner_signals_before_exec(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._discovery_root(root)
            marker = root / "discovery-signal-mask.json"
            self._write_discovery_test(
                root,
                "scripts/test_signal_mask.py",
                self._signal_mask_probe_source(marker),
            )
            real_popen = self.runner.subprocess.Popen
            started = []

            def record_popen(*args, **kwargs):
                process = real_popen(*args, **kwargs)
                started.append(process)
                return process

            previous_mask = signal.pthread_sigmask(
                signal.SIG_BLOCK, {signal.SIGUSR1}
            )
            try:
                with mock.patch.object(
                    self.runner.subprocess, "Popen", side_effect=record_popen
                ):
                    manifest = self.runner._discover_full_manifest(
                        root, timeout_seconds=5.0
                    )
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)

            payload = json.loads(marker.read_text(encoding="utf-8"))

        self.assertEqual(["tests/scripts/test_signal_mask.py"], manifest.modules)
        self.assertEqual(1, len(started))
        self.assertEqual(started[0].pid, payload["pid"])
        self.assertEqual(payload["pid"], payload["sid"])
        self.assertEqual(payload["pid"], payload["pgid"])
        self.assertTrue(
            set(self.runner.RUNNER_SIGNALS).isdisjoint(payload["blocked"])
        )
        self.assertIn(signal.SIGUSR1, payload["blocked"])

    @unittest.skipUnless(os.name == "posix", "POSIX full regression discovery")
    def test_full_discovery_rejects_duplicate_test_ids_and_import_errors(self) -> None:
        fixtures = {
            "duplicate": """
                import unittest
                class Duplicate(unittest.TestCase):
                    def test_same(self): pass
                def load_tests(loader, tests, pattern):
                    case = Duplicate("test_same")
                    return unittest.TestSuite([case, case])
            """,
            "import error": "raise RuntimeError('broken import')\n",
        }
        for label, source in fixtures.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._discovery_root(root)
                self._write_discovery_test(root, "scripts/test_invalid.py", source)
                with self.assertRaises(self.runner.SelectionError):
                    self.runner._discover_full_manifest(root, timeout_seconds=5.0)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._discovery_root(root)
            marker = root / "import-finished"
            self._write_discovery_test(
                root,
                "scripts/test_noisy_import.py",
                f"""
                import sys
                from pathlib import Path

                for _ in range(512):
                    sys.stdout.write("x" * 1024)
                Path({str(marker)!r}).write_text("finished", encoding="utf-8")

                import unittest
                class NoisyImport(unittest.TestCase):
                    def test_one(self): pass
                """,
            )
            with mock.patch.object(self.runner, "FULL_MAX_LOG_BYTES", 4096):
                with self.assertRaisesRegex(
                    self.runner.SelectionError, "output exceeded"
                ):
                    self.runner._discover_full_manifest(root, timeout_seconds=5.0)
            self.assertFalse(marker.exists())

        unrelated = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        descendant_pid: int | None = None
        try:
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._discovery_root(root)
                child_pid_path = root / "discovery-child.pid"
                self._write_discovery_test(
                    root,
                    "scripts/test_interrupted_import.py",
                    f"""
                    import subprocess
                    import sys
                    import time
                    from pathlib import Path

                    child = subprocess.Popen(
                        [sys.executable, "-c", "import time; time.sleep(30)"],
                        stdin=subprocess.DEVNULL,
                    )
                    Path({str(child_pid_path)!r}).write_text(str(child.pid), encoding="utf-8")
                    time.sleep(30)
                    """,
                )

                probe = textwrap.dedent(
                    f"""
                    import importlib.util
                    import os
                    from pathlib import Path
                    import signal
                    import sys
                    import threading
                    import time

                    runner_path = Path({str(RUNNER_PATH)!r})
                    sys.path.insert(0, str(runner_path.parent))
                    spec = importlib.util.spec_from_file_location(
                        "full_discovery_interrupt_probe", runner_path
                    )
                    runner = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = runner
                    spec.loader.exec_module(runner)
                    child_pid_path = Path({str(child_pid_path)!r})

                    def interrupt_after_descendant_starts():
                        deadline = time.monotonic() + 5.0
                        while not child_pid_path.exists() and time.monotonic() < deadline:
                            time.sleep(0.01)
                        if child_pid_path.exists():
                            os.kill(os.getpid(), signal.SIGTERM)

                    runner._acquire_full_interrupt_ownership()
                    interrupter = threading.Thread(
                        target=interrupt_after_descendant_starts, daemon=True
                    )
                    interrupter.start()
                    try:
                        runner._discover_full_manifest(
                            Path({str(root)!r}),
                            timeout_seconds=5.0,
                            manage_interrupts=False,
                        )
                    except runner.SelectionError as exc:
                        interrupter.join(timeout=5.0)
                        print(str(exc))
                        raise SystemExit(runner._finalize_full_exit_code(2))
                    raise SystemExit(0)
                    """
                )
                completed = subprocess.run(
                    [sys.executable, "-c", probe],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=15.0,
                )
                self.assertEqual(2, completed.returncode, completed.stderr)
                self.assertIn("discovery interrupted", completed.stdout)
                descendant_pid = int(child_pid_path.read_text(encoding="utf-8"))
                with self.assertRaises(ProcessLookupError):
                    os.kill(descendant_pid, 0)
                self.assertIsNone(unrelated.poll())
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=5.0)
            if descendant_pid is not None:
                try:
                    os.kill(descendant_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    @unittest.skipUnless(os.name == "posix", "POSIX full regression execution")
    def test_full_jobs_one_and_four_have_same_decisions_and_exclusive_never_overlaps(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            active = root / "active"
            active.mkdir()
            safe_modules = []
            for index in range(4):
                safe_modules.append(
                    self._write_test(
                        root,
                        f"test_safe_{index}.py",
                        f"""
                        import pathlib
                        import time
                        import unittest
                        class Safe(unittest.TestCase):
                            def test_safe(self):
                                marker = pathlib.Path({str(active)!r}) / "{index}"
                                marker.write_text("active")
                                time.sleep(0.05)
                                marker.unlink()
                        """,
                    )
                )
            exclusive = self._write_test(
                root,
                "test_z_exclusive.py",
                f"""
                import pathlib
                import unittest
                class Exclusive(unittest.TestCase):
                    def test_exclusive(self):
                        self.assertEqual([], list(pathlib.Path({str(active)!r}).iterdir()))
                """,
            )
            modules = [*safe_modules, exclusive]
            sequential = self.runner._execute_full_modules(
                root,
                modules,
                exclusive_modules=[exclusive],
                jobs=1,
                timeout_seconds=5.0,
            )
            parallel = self.runner._execute_full_modules(
                root,
                modules,
                exclusive_modules=[exclusive],
                jobs=4,
                timeout_seconds=5.0,
            )

        self.assertEqual(
            [(row.module, row.status) for row in sequential],
            [(row.module, row.status) for row in parallel],
        )
        self.assertTrue(all(row.status == "pass" for row in parallel))

    def test_full_weighted_safe_lane_is_heavy_first_and_first_fit(self) -> None:
        heavy_a = "tests/test_a_heavy.py"
        heavy_b = "tests/test_b_heavy.py"
        standard_a = "tests/test_c_standard.py"
        standard_b = "tests/test_d_standard.py"
        modules = [standard_b, heavy_b, standard_a, heavy_a]
        resource_classes = {
            heavy_a: "heavy",
            heavy_b: "heavy",
            standard_a: "standard",
            standard_b: "standard",
        }
        started: list[str] = []
        occupancy: list[tuple[str, ...]] = []
        completion_order = [standard_a, standard_b, heavy_a, heavy_b]

        def start(_root, module, _timeout, **_kwargs):
            started.append(module)
            return object()

        def poll(active):
            occupancy.append(tuple(sorted(active)))
            module = completion_order[len(occupancy) - 1]
            self.assertIn(module, active)
            active.pop(module)
            return [
                self.runner.WorkerResult(
                    module=module,
                    status="pass",
                    exit_code=0,
                    timed_out=False,
                    duration_seconds=0.01,
                    stdout="",
                    stderr="",
                    detail="",
                    pid=123,
                    tmpdir="/tmp/probe",
                )
            ]

        with mock.patch.object(
            self.runner, "_start_worker", side_effect=start
        ), mock.patch.object(self.runner, "_poll_workers", side_effect=poll):
            results = self.runner._execute_modules(
                ROOT,
                modules,
                jobs=4,
                timeout_seconds=5.0,
                resource_classes=resource_classes,
            )

        self.assertEqual(
            [heavy_a, standard_a, standard_b, heavy_b],
            started,
        )
        self.assertEqual(
            [
                (heavy_a, standard_a),
                (heavy_a, standard_b),
                (heavy_a,),
                (heavy_b,),
            ],
            occupancy,
        )
        self.assertEqual(sorted(modules), [result.module for result in results])
        self.assertTrue(all(result.status == "pass" for result in results))

    def test_full_weighted_safe_lane_enforces_capacity_semaphores_and_jobs(self) -> None:
        classes = {
            "heavy": "heavy",
            "heavy-two": "heavy",
            "tokenizer": "tokenizer",
            "tokenizer-two": "tokenizer",
            "heavy-tokenizer": "heavy-tokenizer",
            "standard": "standard",
        }
        ordered = self.runner._ordered_full_modules(list(classes), classes)
        self.assertEqual(
            ["heavy", "heavy-tokenizer", "heavy-two"],
            ordered[:3],
        )
        self.assertEqual(
            "standard",
            self.runner._first_full_dispatch_candidate(
                ordered[1:], ["heavy"], classes, jobs=4
            ),
        )
        self.assertIsNone(
            self.runner._first_full_dispatch_candidate(
                ordered[1:], ["heavy", "standard"], classes, jobs=4
            )
        )
        self.assertEqual(
            "standard",
            self.runner._first_full_dispatch_candidate(
                ["tokenizer-two", "standard"], ["tokenizer"], classes, jobs=4
            ),
        )
        self.assertIsNone(
            self.runner._first_full_dispatch_candidate(
                ["heavy-two", "tokenizer-two"],
                ["heavy-tokenizer"],
                classes,
                jobs=4,
            )
        )
        self.assertIsNone(
            self.runner._first_full_dispatch_candidate(
                ["standard"], ["tokenizer"], classes, jobs=1
            )
        )

    def test_full_resource_class_map_flows_only_to_the_safe_lane(self) -> None:
        safe = "tests/test_a_safe.py"
        exclusive = "tests/test_z_exclusive.py"
        resource_classes = {safe: "heavy", exclusive: "heavy-tokenizer"}
        safe_result = self.runner.WorkerResult(
            module=safe,
            status="pass",
            exit_code=0,
            timed_out=False,
            duration_seconds=0.01,
            stdout="",
            stderr="",
            detail="",
            pid=123,
            tmpdir="/tmp/safe",
        )
        exclusive_result = self.runner.WorkerResult(
            module=exclusive,
            status="pass",
            exit_code=0,
            timed_out=False,
            duration_seconds=0.01,
            stdout="",
            stderr="",
            detail="",
            pid=124,
            tmpdir="/tmp/exclusive",
        )
        with mock.patch.object(
            self.runner, "_supports_owned_process_groups", return_value=True
        ), mock.patch.object(
            self.runner, "_supports_atomic_interrupt_lifecycle", return_value=True
        ), mock.patch.object(
            self.runner,
            "_execute_modules",
            side_effect=[[safe_result], [exclusive_result]],
        ) as execute:
            results = self.runner._execute_full_modules(
                ROOT,
                [exclusive, safe],
                exclusive_modules=[exclusive],
                jobs=4,
                timeout_seconds=5.0,
                resource_classes=resource_classes,
            )

        self.assertEqual([safe, exclusive], [result.module for result in results])
        self.assertEqual(
            [
                mock.call(
                    ROOT,
                    [safe],
                    jobs=4,
                    timeout_seconds=5.0,
                    max_log_bytes=self.runner.FULL_MAX_LOG_BYTES,
                    owns_process_group=True,
                    manage_interrupts=False,
                    resource_classes={safe: "heavy"},
                ),
                mock.call(
                    ROOT,
                    [exclusive],
                    jobs=1,
                    timeout_seconds=5.0,
                    max_log_bytes=self.runner.FULL_MAX_LOG_BYTES,
                    owns_process_group=True,
                    manage_interrupts=False,
                ),
            ],
            execute.call_args_list,
        )

    def test_full_weighted_failure_stops_new_heavy_and_standard_dispatch(self) -> None:
        for failed_class in ("heavy", "standard"):
            with self.subTest(failed_class=failed_class):
                failed = f"tests/test_a_{failed_class}.py"
                unstarted = "tests/test_z_unstarted.py"
                started: list[str] = []

                def start(_root, module, _timeout, **_kwargs):
                    started.append(module)
                    return object()

                def poll(active):
                    module = next(iter(active))
                    active.pop(module)
                    return [
                        self.runner.WorkerResult(
                            module=module,
                            status="fail",
                            exit_code=1,
                            timed_out=False,
                            duration_seconds=0.01,
                            stdout="",
                            stderr="failure",
                            detail="",
                            pid=123,
                            tmpdir="/tmp/probe",
                        )
                    ]

                with mock.patch.object(
                    self.runner, "_start_worker", side_effect=start
                ), mock.patch.object(self.runner, "_poll_workers", side_effect=poll):
                    results = self.runner._execute_modules(
                        ROOT,
                        [unstarted, failed],
                        jobs=1,
                        timeout_seconds=5.0,
                        resource_classes={
                            failed: failed_class,
                            unstarted: "standard",
                        },
                    )
                self.assertEqual([failed], started)
                self.assertEqual(
                    ["fail", "not-run"],
                    [result.status for result in results],
                )

    def test_full_failure_paths_stop_exclusive_and_require_owned_process_groups(
        self,
    ) -> None:
        if os.name == "posix":
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                failed = self._write_test(
                    root,
                    "test_a_fail.py",
                    """
                    import unittest
                    class Failure(unittest.TestCase):
                        def test_failure(self): self.fail("stop full dispatch")
                    """,
                )
                exclusive = self._write_test(
                    root,
                    "test_z_exclusive.py",
                    """
                    import unittest
                    class Exclusive(unittest.TestCase):
                        def test_exclusive(self): self.fail("must not run")
                    """,
                )
                results = self.runner._execute_full_modules(
                    root,
                    [failed, exclusive],
                    exclusive_modules=[exclusive],
                    jobs=2,
                    timeout_seconds=5.0,
                )
            self.assertEqual(["fail", "not-run"], [row.status for row in results])

        with mock.patch.object(
            self.runner,
            "_supports_owned_process_groups",
            create=True,
            return_value=False,
        ), mock.patch.object(self.runner, "_execute_modules", return_value=[]) as execute:
            with self.assertRaisesRegex(
                self.runner.SelectionError, "process-group cleanup"
            ):
                self.runner._execute_full_modules(
                    ROOT,
                    ["tests/scripts/test_run_ci_tests.py"],
                    exclusive_modules=[],
                    jobs=1,
                    timeout_seconds=5.0,
                )
        execute.assert_not_called()

        if os.name == "posix":
            unrelated = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            leaked_pid: int | None = None
            try:
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    child_pid_path = root / "child.pid"
                    exclusive_marker = root / "exclusive-ran"
                    leaky = self._write_test(
                        root,
                        "test_a_leaky.py",
                        f"""
                        import subprocess
                        import sys
                        import unittest
                        from pathlib import Path

                        class Leaky(unittest.TestCase):
                            def test_leaky(self):
                                child = subprocess.Popen(
                                    [sys.executable, "-c", "import time; time.sleep(30)"],
                                    stdin=subprocess.DEVNULL,
                                )
                                Path({str(child_pid_path)!r}).write_text(str(child.pid), encoding="utf-8")
                        """,
                    )
                    exclusive = self._write_test(
                        root,
                        "test_z_exclusive.py",
                        f"""
                        import unittest
                        from pathlib import Path

                        class Exclusive(unittest.TestCase):
                            def test_exclusive(self):
                                Path({str(exclusive_marker)!r}).write_text("ran", encoding="utf-8")
                        """,
                    )
                    results = self.runner._execute_full_modules(
                        root,
                        [leaky, exclusive],
                        exclusive_modules=[exclusive],
                        jobs=1,
                        timeout_seconds=5.0,
                    )
                    leaked_pid = int(child_pid_path.read_text(encoding="utf-8"))

                    self.assertEqual(
                        ["error", "not-run"], [row.status for row in results]
                    )
                    self.assertIn("descendant", results[0].detail)
                    self.assertFalse(exclusive_marker.exists())
                    with self.assertRaises(ProcessLookupError):
                        os.kill(leaked_pid, 0)
                    self.assertIsNone(unrelated.poll())
            finally:
                unrelated.terminate()
                unrelated.wait(timeout=5.0)
                if leaked_pid is not None:
                    try:
                        os.kill(leaked_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipUnless(os.name == "posix", "POSIX full regression execution")
    def test_full_worker_log_limit_bounds_storage_during_sustained_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            capture_root = root / "worker-capture"
            capture_root.mkdir()

            class RetainedTemporaryDirectory:
                name = str(capture_root)

                def cleanup(self) -> None:
                    return None

            exact = self._write_test(
                root,
                "test_exact_log_limit.py",
                """
                import sys
                import unittest
                class Exact(unittest.TestCase):
                    def test_exact(self):
                        sys.stdout.buffer.write(b"x" * 1024)
                        sys.stdout.buffer.flush()
                """,
            )
            noisy = self._write_test(
                root,
                "test_noisy.py",
                """
                import sys
                import time
                import unittest
                class Noisy(unittest.TestCase):
                    def test_noisy(self):
                        for _ in range(4096):
                            sys.stdout.write("x" * 1024)
                            sys.stdout.flush()
                            time.sleep(0.0001)
                """,
            )
            with mock.patch.object(
                self.runner.tempfile,
                "TemporaryDirectory",
                return_value=RetainedTemporaryDirectory(),
            ), mock.patch.object(self.runner, "FULL_MAX_LOG_BYTES", 1024):
                exact_results = self.runner._execute_full_modules(
                    root,
                    [exact],
                    exclusive_modules=[],
                    jobs=1,
                    timeout_seconds=5.0,
                )
                results = self.runner._execute_full_modules(
                    root,
                    [noisy],
                    exclusive_modules=[],
                    jobs=1,
                    timeout_seconds=5.0,
                )
            self.assertEqual("pass", exact_results[0].status)
            self.assertEqual(1024, len(exact_results[0].stdout.encode("utf-8")))
            self.assertEqual("error", results[0].status)
            self.assertIn("exceeded 1024 bytes", results[0].detail)
            self.assertLessEqual(len(results[0].stdout.encode("utf-8")), 1024)
            self.assertTrue(
                all(path.stat().st_size <= 1024 for path in capture_root.glob("*.log"))
            )

    def test_full_list_tests_prints_manifest_without_loading_core_or_running(self) -> None:
        manifest = self.runner.FullDiscoveryManifest(
            modules=["tests/test_alpha.py"],
            test_ids=["test_alpha.Alpha.test_one"],
            exclusive_modules=[],
            resource_classes={"tests/test_alpha.py": "heavy"},
        )
        with mock.patch.object(
            self.runner, "_discover_full_manifest", return_value=manifest
        ) as discover, mock.patch.object(
            self.runner, "load_core"
        ) as load_core, mock.patch.object(
            self.runner, "_execute_full_modules"
        ) as execute, mock.patch.object(
            self.runner, "_acquire_full_interrupt_ownership"
        ) as acquire, mock.patch.object(
            self.runner, "_finalize_full_exit_code", side_effect=lambda code: code
        ), mock.patch.object(sys, "stdout", io.StringIO()) as stdout:
            exit_code = self.runner.main(["full", "--list-tests"])
        self.assertEqual(0, exit_code)
        acquire.assert_called_once_with()
        discover.assert_called_once_with(
            ROOT,
            timeout_seconds=self.runner.FULL_DISCOVERY_TIMEOUT_SECONDS,
            manage_interrupts=False,
        )
        load_core.assert_not_called()
        execute.assert_not_called()
        payload = json.loads(stdout.getvalue())
        self.assertEqual("full-regression", payload["reason"])
        self.assertEqual(manifest.test_ids, payload["test_ids"])
        self.assertEqual(
            manifest.resource_classes,
            payload["test_module_resource_classes"],
        )

        with mock.patch.object(
            self.runner,
            "_discover_full_manifest",
            side_effect=self.runner.SelectionError(
                "full unittest discovery interrupted"
            ),
        ), mock.patch.object(
            self.runner, "_acquire_full_interrupt_ownership"
        ), mock.patch.object(
            self.runner, "_finalize_full_exit_code", return_value=2
        ), mock.patch.object(sys, "stderr", io.StringIO()) as stderr:
            self.assertEqual(2, self.runner.main(["full", "--list-tests"]))
        self.assertIn("discovery interrupted", stderr.getvalue())

        with mock.patch.object(
            self.runner,
            "_supports_atomic_interrupt_lifecycle",
            create=True,
            return_value=False,
        ), mock.patch.object(
            self.runner, "_discover_full_manifest", return_value=manifest
        ) as discover, mock.patch.object(sys, "stderr", io.StringIO()) as stderr:
            self.assertEqual(2, self.runner.main(["full", "--list-tests"]))
        discover.assert_not_called()
        self.assertIn("atomic signal lifecycle", stderr.getvalue())

        original_handlers = {
            number: signal.getsignal(number) for number in self.runner.RUNNER_SIGNALS
        }
        real_signal = signal.signal
        install_calls = 0

        def interrupt_full_handler_install(signum, handler):
            nonlocal install_calls
            install_calls += 1
            if install_calls == 2:
                raise self.runner.RunnerInterrupted("install interrupted")
            return real_signal(signum, handler)

        if os.name == "posix":
            with mock.patch.object(
                self.runner.signal,
                "signal",
                side_effect=interrupt_full_handler_install,
            ):
                with self.assertRaisesRegex(
                    self.runner.SelectionError, "discovery interrupted"
                ):
                    self.runner._discover_full_manifest(ROOT, timeout_seconds=5.0)
            self.assertGreaterEqual(install_calls, 3)
            self.assertTrue(
                all(
                    signal.getsignal(number) == handler
                    for number, handler in original_handlers.items()
                )
            )

        if os.name == "posix":
            first = "tests/test_a_safe.py"
            exclusive = "tests/test_z_exclusive.py"
            safe_result = self.runner.WorkerResult(
                module=first,
                status="pass",
                exit_code=0,
                timed_out=False,
                duration_seconds=0.01,
                stdout="",
                stderr="",
                detail="",
                pid=123,
                tmpdir="/tmp/safe",
            )
            runner = self.runner

            class InterruptAfterSafeResult:
                def __iter__(self):
                    yield safe_result
                    raise runner.RunnerInterrupted("between lanes")

            with mock.patch.object(
                self.runner,
                "_execute_modules",
                side_effect=[InterruptAfterSafeResult(), AssertionError("exclusive started")],
            ) as execute:
                interrupted = self.runner._execute_full_modules(
                    ROOT,
                    [first, exclusive],
                    exclusive_modules=[exclusive],
                    jobs=1,
                    timeout_seconds=5.0,
                )
            execute.assert_called_once()
            self.assertEqual([first, exclusive], [row.module for row in interrupted])
            self.assertEqual(
                ["pass", "interrupted"], [row.status for row in interrupted]
            )
            self.assertEqual(2, self.runner._exit_code(interrupted))

            manifest = self.runner.FullDiscoveryManifest(
                modules=[first, exclusive],
                test_ids=["test_a.Safe.test_one", "test_z.Exclusive.test_one"],
                exclusive_modules=[exclusive],
                resource_classes={first: "standard", exclusive: "standard"},
            )

            def signal_before_full_dispatch(*_args, **_kwargs):
                raise self.runner.RunnerInterrupted("before full dispatch")

            with mock.patch.object(
                self.runner, "_discover_full_manifest", return_value=manifest
            ) as discover, mock.patch.object(
                self.runner,
                "_execute_full_modules",
                side_effect=signal_before_full_dispatch,
            ) as execute, mock.patch.object(
                self.runner, "_acquire_full_interrupt_ownership"
            ), mock.patch.object(
                self.runner, "_finalize_full_exit_code", return_value=2
            ), mock.patch.object(
                sys, "stdout", io.StringIO()
            ) as stdout:
                self.assertEqual(2, self.runner.main(["full"]))
            discover.assert_called_once_with(
                ROOT,
                timeout_seconds=self.runner.FULL_DISCOVERY_TIMEOUT_SECONDS,
                manage_interrupts=False,
            )
            execute.assert_called_once()
            execute.assert_called_once_with(
                ROOT,
                manifest.modules,
                exclusive_modules=manifest.exclusive_modules,
                jobs=self.runner.DEFAULT_JOBS,
                timeout_seconds=self.runner.DEFAULT_TIMEOUT_SECONDS,
                resource_classes=manifest.resource_classes,
            )
            output = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual("full-regression", output[0]["reason"])
            self.assertEqual(
                ["interrupted", "not-run"],
                [row["status"] for row in output[-1]["worker_results"]],
            )

    @unittest.skipUnless(os.name == "posix", "POSIX full regression discovery")
    def test_current_full_manifest_covers_repository_test_files_without_tree_changes(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        manifest = self.runner._discover_full_manifest(
            ROOT, timeout_seconds=self.runner.FULL_DISCOVERY_TIMEOUT_SECONDS
        )
        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        expected_modules = sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "tests").rglob("test*.py")
        )
        self.assertEqual(expected_modules, manifest.modules)
        self.assertEqual(len(manifest.modules), len(set(manifest.modules)))
        self.assertEqual(len(manifest.test_ids), len(set(manifest.test_ids)))
        self.assertEqual(
            "heavy",
            manifest.resource_classes[
                "tests/scripts/test_validate_capabilities.py"
            ],
        )
        self.assertEqual(
            "heavy-tokenizer",
            manifest.resource_classes[
                "tests/scripts/test_validate_root_content.py"
            ],
        )
        self.assertTrue(
            all(
                resource_class in self.runner.FULL_RESOURCE_PROFILES
                for resource_class in manifest.resource_classes.values()
            )
        )
        self.assertEqual(before, after)

    def test_real_workers_isolate_pid_tmpdir_and_global_state_and_sort_summary(self) -> None:
        probe = """
            import builtins
            import json
            import os
            import sys
            import time
            import unittest

            class Probe(unittest.TestCase):
                def test_probe(self):
                    self.assertFalse(hasattr(builtins, "_ci_runner_probe"))
                    builtins._ci_runner_probe = True
                    self.assertEqual("1", os.environ.get("PYTHONDONTWRITEBYTECODE"))
                    self.assertTrue(os.environ.get("TMPDIR"))
                    time.sleep({delay})
                    print("PROBE " + json.dumps({{"pid": os.getpid(), "tmpdir": os.environ["TMPDIR"]}}, sort_keys=True))
                    print("DIAGNOSTIC", file=sys.stderr)
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            slow = self._write_test(root, "test_a_slow.py", probe.format(delay=0.15))
            fast = self._write_test(root, "test_z_fast.py", probe.format(delay=0.0))
            results = self.runner._execute_modules(
                root, [slow, fast], jobs=2, timeout_seconds=5.0
            )
            self.assertFalse((root / "__pycache__").exists())

        self.assertEqual([slow, fast], [result.module for result in results])
        self.assertEqual(["pass", "pass"], [result.status for result in results])
        observations = []
        for result in results:
            line = next(
                line for line in result.stdout.splitlines() if line.startswith("PROBE ")
            )
            observations.append(json.loads(line.removeprefix("PROBE ")))
        self.assertEqual(2, len({row["pid"] for row in observations}))
        self.assertEqual(2, len({row["tmpdir"] for row in observations}))
        self.assertTrue(all("DIAGNOSTIC" in result.stderr for result in results))
        self.assertTrue(all("DIAGNOSTIC" not in result.stdout for result in results))
        self.assertTrue(all(result.duration_seconds >= 0 for result in results))

        if os.name == "posix":
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                child_pid_path = root / "affected-child.pid"
                background = self._write_test(
                    root,
                    "test_affected_background.py",
                    f"""
                    import subprocess
                    import sys
                    import unittest
                    from pathlib import Path

                    class Background(unittest.TestCase):
                        def test_background(self):
                            child = subprocess.Popen(
                                [sys.executable, "-c", "import time; time.sleep(30)"],
                                stdin=subprocess.DEVNULL,
                            )
                            Path({str(child_pid_path)!r}).write_text(str(child.pid), encoding="utf-8")
                    """,
                )
                try:
                    affected_results = self.runner._execute_modules(
                        root, [background], jobs=1, timeout_seconds=5.0
                    )
                    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
                    self.assertEqual("pass", affected_results[0].status)
                    os.kill(child_pid, 0)
                finally:
                    if "affected_results" in locals():
                        try:
                            os.killpg(affected_results[0].pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass

    @unittest.skipUnless(
        os.name == "posix"
        and hasattr(signal, "pthread_sigmask")
        and hasattr(signal, "SIGUSR1"),
        "POSIX child signal-mask bootstrap",
    )
    def test_full_worker_unblocks_only_runner_signals_before_exec(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            module = self._write_test(
                root,
                "test_signal_mask.py",
                self._signal_mask_probe_source(),
            )
            previous_mask = signal.pthread_sigmask(
                signal.SIG_BLOCK, {signal.SIGUSR1}
            )
            try:
                results = self.runner._execute_full_modules(
                    root,
                    [module],
                    exclusive_modules=[],
                    jobs=1,
                    timeout_seconds=5.0,
                )
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)

        self.assertEqual(["pass"], [result.status for result in results])
        line = next(
            line
            for line in results[0].stdout.splitlines()
            if line.startswith("SIGNAL_MASK ")
        )
        payload = json.loads(line.removeprefix("SIGNAL_MASK "))
        self.assertEqual(results[0].pid, payload["pid"])
        self.assertEqual(payload["pid"], payload["sid"])
        self.assertEqual(payload["pid"], payload["pgid"])
        self.assertTrue(
            set(self.runner.RUNNER_SIGNALS).isdisjoint(payload["blocked"])
        )
        self.assertIn(signal.SIGUSR1, payload["blocked"])

    def test_worker_runs_quickstart_without_prior_test_module_imports(self) -> None:
        results = self.runner._execute_modules(
            ROOT,
            ["tests/scripts/test_quickstart.py"],
            jobs=1,
            timeout_seconds=30.0,
        )

        self.assertEqual(1, len(results))
        self.assertEqual("pass", results[0].status, results[0].stderr)

    def test_worker_import_path_rejects_ambient_pythonpath_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Path(raw)
            root = fixture / "repository"
            scripts = root / "scripts"
            ambient = fixture / "ambient"
            scripts.mkdir(parents=True)
            ambient.mkdir()
            (root / "import_precedence_probe.py").write_text(
                "SOURCE = 'repository-root'\n", encoding="utf-8"
            )
            (scripts / "scripts_only_probe.py").write_text(
                "SOURCE = 'repository-scripts'\n", encoding="utf-8"
            )
            (ambient / "import_precedence_probe.py").write_text(
                "SOURCE = 'ambient'\n", encoding="utf-8"
            )
            (ambient / "scripts_only_probe.py").write_text(
                "SOURCE = 'ambient'\n", encoding="utf-8"
            )
            ambient_marker = fixture / "ambient-sitecustomize-ran"
            (ambient / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(ambient_marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8",
            )
            module = self._write_test(
                root,
                "test_import_environment.py",
                f"""
                import sys
                import unittest
                import import_precedence_probe
                import scripts_only_probe

                class ImportEnvironment(unittest.TestCase):
                    def test_canonical_path(self):
                        self.assertEqual(
                            [{str(root.resolve())!r}, {str(scripts.resolve())!r}],
                            sys.path[:2],
                        )
                        self.assertEqual(
                            "repository-root", import_precedence_probe.SOURCE
                        )
                        self.assertEqual(
                            "repository-scripts", scripts_only_probe.SOURCE
                        )
                """,
            )
            with mock.patch.dict(
                os.environ,
                {"PYTHONPATH": str(ambient), "PYTHONSAFEPATH": "1"},
                clear=False,
            ):
                results = self.runner._execute_modules(
                    root, [module], jobs=1, timeout_seconds=5.0
                )

            self.assertFalse(ambient_marker.exists())

        self.assertEqual("pass", results[0].status, results[0].stderr)

    def test_worker_safe_path_does_not_break_nested_cli_sibling_imports(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Path(raw)
            root = fixture / "repository"
            scripts = root / "scripts"
            cli = root / "nested-cli"
            ambient = fixture / "ambient"
            scripts.mkdir(parents=True)
            cli.mkdir()
            ambient.mkdir()
            (cli / "sibling.py").write_text(
                "SOURCE = 'nested-cli-sibling'\n", encoding="utf-8"
            )
            (ambient / "sibling.py").write_text(
                "SOURCE = 'hostile-ambient'\n", encoding="utf-8"
            )
            ambient_marker = fixture / "ambient-sitecustomize-ran"
            (ambient / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(ambient_marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8",
            )
            (cli / "main.py").write_text(
                textwrap.dedent(
                    f"""
                    import json
                    import os
                    import sys
                    import sibling

                    print(json.dumps({{
                        "safe_path_environment": os.environ.get("PYTHONSAFEPATH"),
                        "no_user_site": os.environ.get("PYTHONNOUSERSITE"),
                        "pythonpath": os.environ.get("PYTHONPATH"),
                        "script_path": sys.path[0],
                        "sibling_source": sibling.SOURCE,
                    }}, sort_keys=True))
                    """
                ),
                encoding="utf-8",
            )
            worker_pythonpath = os.pathsep.join(
                str(path)
                for path in dict.fromkeys(
                    (root.resolve(), scripts.resolve(), RUNNER_PATH.parent.resolve())
                )
            )
            module = self._write_test(
                root,
                "test_nested_cli.py",
                f"""
                import json
                import os
                import subprocess
                import sys
                import unittest

                class NestedCli(unittest.TestCase):
                    def test_sibling_import_uses_standard_script_directory(self):
                        self.assertTrue(sys.flags.safe_path)
                        self.assertIsNone(os.environ.get("PYTHONSAFEPATH"))
                        completed = subprocess.run(
                            [sys.executable, {str(cli / 'main.py')!r}],
                            cwd={str(root)!r},
                            text=True,
                            capture_output=True,
                            check=False,
                        )
                        self.assertEqual(
                            0, completed.returncode, completed.stderr or completed.stdout
                        )
                        self.assertEqual(
                            {{
                                "safe_path_environment": None,
                                "no_user_site": "1",
                                "pythonpath": {worker_pythonpath!r},
                                "script_path": {str(cli.resolve())!r},
                                "sibling_source": "nested-cli-sibling",
                            }},
                            json.loads(completed.stdout),
                        )
                """,
            )
            with mock.patch.dict(
                os.environ, {"PYTHONPATH": str(ambient)}, clear=False
            ):
                results = self.runner._execute_modules(
                    root, [module], jobs=1, timeout_seconds=5.0
                )

            self.assertFalse(ambient_marker.exists())

        self.assertEqual("pass", results[0].status, results[0].stderr)

    def test_jobs_one_failure_stops_dispatch_and_marks_remaining_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            failed = self._write_test(
                root,
                "test_a_fail.py",
                """
                import unittest
                class Failure(unittest.TestCase):
                    def test_failure(self):
                        self.fail("negative control")
                """,
            )
            marker = root / "must-not-exist"
            unstarted = self._write_test(
                root,
                "test_b_unstarted.py",
                f"""
                from pathlib import Path
                import unittest
                class Unstarted(unittest.TestCase):
                    def test_unstarted(self):
                        Path({str(marker)!r}).write_text("ran", encoding="utf-8")
                """,
            )
            results = self.runner._execute_modules(
                root, [failed, unstarted], jobs=1, timeout_seconds=5.0
            )

        self.assertEqual(["fail", "not-run"], [row.status for row in results])
        self.assertEqual(1, self.runner._exit_code(results))
        self.assertFalse(marker.exists())

    def test_abnormal_worker_exit_is_execution_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            crashed = self._write_test(
                root,
                "test_crash.py",
                """
                import os
                import unittest
                class Crash(unittest.TestCase):
                    def test_crash(self):
                        os._exit(7)
                """,
            )
            results = self.runner._execute_modules(
                root, [crashed], jobs=1, timeout_seconds=5.0
            )
        self.assertEqual("error", results[0].status)
        self.assertEqual(7, results[0].exit_code)
        self.assertEqual(2, self.runner._exit_code(results))

    def test_timeout_is_execution_error_and_worker_is_reaped(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            slow = self._write_test(
                root,
                "test_timeout.py",
                """
                import time
                import unittest
                class Slow(unittest.TestCase):
                    def test_slow(self):
                        time.sleep(30)
                """,
            )
            results = self.runner._execute_modules(
                root, [slow], jobs=1, timeout_seconds=0.05
            )
        self.assertEqual("timeout", results[0].status)
        self.assertTrue(results[0].timed_out)
        self.assertIsNotNone(results[0].exit_code)
        self.assertEqual(2, self.runner._exit_code(results))

    def test_jobs_two_collects_started_worker_but_does_not_dispatch_more(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            failed = self._write_test(
                root,
                "test_a_fail.py",
                """
                import unittest
                class Failure(unittest.TestCase):
                    def test_failure(self):
                        self.fail("stop dispatch")
                """,
            )
            started = self._write_test(
                root,
                "test_b_started.py",
                """
                import time
                import unittest
                class Started(unittest.TestCase):
                    def test_started(self):
                        time.sleep(0.2)
                """,
            )
            marker = root / "third-must-not-run"
            unstarted = self._write_test(
                root,
                "test_c_unstarted.py",
                f"""
                from pathlib import Path
                import unittest
                class Unstarted(unittest.TestCase):
                    def test_unstarted(self):
                        Path({str(marker)!r}).write_text("ran", encoding="utf-8")
                """,
            )
            results = self.runner._execute_modules(
                root,
                [failed, started, unstarted],
                jobs=2,
                timeout_seconds=5.0,
            )
            self.assertFalse(marker.exists())

        self.assertEqual(
            ["fail", "pass", "not-run"], [result.status for result in results]
        )

    def test_temporary_cleanup_failure_is_execution_error(self) -> None:
        process = mock.Mock(pid=123)
        process.poll.return_value = 0
        temporary = mock.Mock(name="/tmp/changeforge-worker")
        temporary.name = "/tmp/changeforge-worker"
        temporary.cleanup.side_effect = OSError("busy")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            stdout_path = root / "stdout.log"
            stderr_path = root / "stderr.log"
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            with stdout_path.open("rb") as stdout_stream, stderr_path.open(
                "rb"
            ) as stderr_stream:
                handle = self.runner.WorkerHandle(
                    module="tests/scripts/test_cleanup.py",
                    process=process,
                    temporary=temporary,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    stdout_stream=stdout_stream,
                    stderr_stream=stderr_stream,
                    started_at=self.runner.time.monotonic(),
                    timeout_seconds=5.0,
                )
                result = self.runner._finish_worker(handle)
        self.assertEqual("error", result.status)
        self.assertIn("temporary cleanup failed", result.detail)

    def test_duplicate_module_selection_is_rejected_before_start(self) -> None:
        with self.assertRaisesRegex(self.runner.SelectionError, "duplicate-free"):
            self.runner._execute_modules(
                ROOT,
                ["tests/scripts/test_run_ci_tests.py"] * 2,
                jobs=2,
                timeout_seconds=5.0,
            )

    def test_start_failure_is_error_and_stops_new_dispatch(self) -> None:
        with mock.patch.object(
            self.runner, "_start_worker", side_effect=OSError("cannot start")
        ) as start:
            results = self.runner._execute_modules(
                ROOT,
                ["tests/scripts/test_a.py", "tests/scripts/test_b.py"],
                jobs=1,
                timeout_seconds=5.0,
            )
        start.assert_called_once()
        self.assertEqual(["error", "not-run"], [row.status for row in results])
        self.assertIn("cannot start", results[0].detail)
        self.assertEqual(2, self.runner._exit_code(results))

        original_handlers = {
            number: signal.getsignal(number) for number in self.runner.RUNNER_SIGNALS
        }
        real_signal = signal.signal
        install_calls = 0

        def interrupt_handler_install(signum, handler):
            nonlocal install_calls
            install_calls += 1
            if install_calls == 2:
                raise self.runner.RunnerInterrupted("install interrupted")
            return real_signal(signum, handler)

        with mock.patch.object(
            self.runner.signal,
            "signal",
            side_effect=interrupt_handler_install,
        ), mock.patch.object(self.runner, "_start_worker") as start:
            install_interrupted = self.runner._execute_modules(
                ROOT,
                ["tests/scripts/test_a.py", "tests/scripts/test_b.py"],
                jobs=1,
                timeout_seconds=5.0,
            )
        start.assert_not_called()
        self.assertEqual(
            ["tests/scripts/test_a.py", "tests/scripts/test_b.py"],
            [row.module for row in install_interrupted],
        )
        self.assertEqual(
            ["interrupted", "not-run"],
            [row.status for row in install_interrupted],
        )
        self.assertEqual(2, self.runner._exit_code(install_interrupted))
        self.assertGreaterEqual(install_calls, 3)
        self.assertTrue(
            all(
                signal.getsignal(number) == handler
                for number, handler in original_handlers.items()
            )
        )

        requested = ["tests/scripts/test_a.py", "tests/scripts/test_b.py"]
        for full in (False, True):
            if full and os.name != "posix":
                continue
            with self.subTest(full=full, window="during-start"), mock.patch.object(
                self.runner,
                "_start_worker",
                side_effect=self.runner.RunnerInterrupted("startup interrupt"),
            ):
                if full:
                    interrupted = self.runner._execute_full_modules(
                        ROOT,
                        requested,
                        exclusive_modules=[requested[1]],
                        jobs=1,
                        timeout_seconds=5.0,
                    )
                else:
                    interrupted = self.runner._execute_modules(
                        ROOT, requested, jobs=1, timeout_seconds=5.0
                    )
            self.assertEqual(requested, [row.module for row in interrupted])
            self.assertEqual(
                ["interrupted", "not-run"], [row.status for row in interrupted]
            )
            self.assertEqual(2, self.runner._exit_code(interrupted))

        if os.name == "posix":
            for full in (False, True):
                with self.subTest(full=full, window="post-start-pre-registration"):
                    with tempfile.TemporaryDirectory() as raw:
                        root = Path(raw)
                        slow = self._write_test(
                            root,
                            "test_a_slow.py",
                            """
                            import time
                            import unittest
                            class Slow(unittest.TestCase):
                                def test_slow(self): time.sleep(30)
                            """,
                        )
                        never_started = self._write_test(
                            root,
                            "test_z_never_started.py",
                            "import unittest\n",
                        )
                        real_start = self.runner._start_worker

                        def start_then_interrupt(*args, **kwargs):
                            handle = real_start(*args, **kwargs)
                            if full:
                                raise self.runner.RunnerInterrupted(
                                    "full startup interrupt"
                                )
                            os.kill(os.getpid(), signal.SIGTERM)
                            return handle

                        with mock.patch.object(
                            self.runner,
                            "_start_worker",
                            side_effect=start_then_interrupt,
                        ):
                            if full:
                                window_results = self.runner._execute_full_modules(
                                    root,
                                    [slow, never_started],
                                    exclusive_modules=[never_started],
                                    jobs=1,
                                    timeout_seconds=5.0,
                                )
                            else:
                                window_results = self.runner._execute_modules(
                                    root,
                                    [slow, never_started],
                                    jobs=1,
                                    timeout_seconds=5.0,
                                )
                    self.assertEqual(
                        [slow, never_started], [row.module for row in window_results]
                    )
                    self.assertEqual(
                        ["interrupted", "not-run"],
                        [row.status for row in window_results],
                    )
                    self.assertEqual(2, self.runner._exit_code(window_results))
                    with self.assertRaises(ProcessLookupError):
                        os.kill(window_results[0].pid, 0)

    def test_interrupt_cleans_up_every_started_worker(self) -> None:
        process = mock.Mock()
        process.poll.return_value = None
        handles = {
            module: mock.Mock(module=module, process=process)
            for module in (
                "tests/scripts/test_a.py",
                "tests/scripts/test_b.py",
            )
        }

        def finish(handle, *, forced_status, **_kwargs):
            return self.runner.WorkerResult(
                module=handle.module,
                status=forced_status,
                exit_code=-15,
                timed_out=False,
                duration_seconds=0.01,
                stdout="",
                stderr="",
                detail="runner interrupted",
                pid=123,
                tmpdir="/tmp/worker",
            )

        with mock.patch.object(
            self.runner,
            "_start_worker",
            side_effect=lambda _root, module, _timeout, **_kwargs: handles[module],
        ), mock.patch.object(
            self.runner, "_poll_workers", side_effect=KeyboardInterrupt
        ), mock.patch.object(
            self.runner, "_terminate_worker", return_value=True
        ) as terminate, mock.patch.object(
            self.runner, "_finish_worker", side_effect=finish
        ):
            results = self.runner._execute_modules(
                ROOT,
                list(handles),
                jobs=2,
                timeout_seconds=5.0,
            )
        self.assertEqual(2, terminate.call_count)
        self.assertEqual(["interrupted", "interrupted"], [row.status for row in results])
        self.assertEqual(2, self.runner._exit_code(results))

    @unittest.skipUnless(os.name == "posix", "POSIX signal cleanup contract")
    def test_real_sigterm_interrupt_reaps_active_worker(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            slow = self._write_test(
                root,
                "test_signal.py",
                """
                import time
                import unittest
                class Slow(unittest.TestCase):
                    def test_slow(self):
                        time.sleep(30)
                """,
            )
            real_poll = self.runner._poll_workers
            signalled = False

            def interrupt_after_start(active):
                nonlocal signalled
                if not signalled:
                    signalled = True
                    os.kill(os.getpid(), self.runner.signal.SIGTERM)
                return real_poll(active)

            with mock.patch.object(
                self.runner, "_poll_workers", side_effect=interrupt_after_start
            ):
                results = self.runner._execute_modules(
                    root, [slow], jobs=1, timeout_seconds=5.0
                )

        self.assertEqual("interrupted", results[0].status)
        self.assertEqual(2, self.runner._exit_code(results))
        with self.assertRaises(ProcessLookupError):
            os.kill(results[0].pid, 0)
        self._assert_real_full_process_signal_ownership()

    @unittest.skipUnless(
        os.name == "posix"
        and hasattr(signal, "pthread_sigmask")
        and hasattr(signal, "sigpending")
        and hasattr(signal, "sigwait"),
        "POSIX atomic signal lifecycle",
    )
    def _assert_real_full_process_signal_ownership(self) -> None:
        probe = textwrap.dedent(
            f"""
            import argparse
            import importlib.util
            import json
            import os
            from pathlib import Path
            import signal
            import sys
            import tempfile
            import threading
            import time

            runner_path = Path({str(RUNNER_PATH)!r})
            sys.path.insert(0, str(runner_path.parent))
            spec = importlib.util.spec_from_file_location("atomic_signal_probe", runner_path)
            runner = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = runner
            spec.loader.exec_module(runner)

            phase, lane, prior, marker_root = sys.argv[1:]
            marker_root = Path(marker_root)
            trigger_marker = marker_root / "triggered"
            prior_marker = marker_root / "prior-handler"
            prior_hits = []
            def prior_handler(number, _frame):
                prior_hits.append(number)
                prior_marker.write_text(str(number), encoding="utf-8")
            for number in runner.RUNNER_SIGNALS:
                signal.signal(
                    number,
                    prior_handler if prior == "custom" else signal.SIG_DFL,
                )
            previous = {{number: signal.getsignal(number) for number in runner.RUNNER_SIGNALS}}
            real_signal = runner.signal.signal
            real_sigmask = runner.signal.pthread_sigmask
            triggered = False
            senders = []

            def send_owned_signal():
                global triggered
                triggered = True
                trigger_marker.write_text("yes", encoding="utf-8")
                sent = threading.Event()
                def send_signal():
                    os.kill(os.getpid(), signal.SIGTERM)
                    sent.set()
                sender = threading.Thread(target=send_signal)
                senders.append(sender)
                sender.start()
                if not sent.wait(1.0):
                    raise RuntimeError("signal sender did not run")
                time.sleep(0.05)

            def delayed_signal(number, handler):
                installing = handler in (
                    runner._raise_runner_interrupted,
                    runner._raise_full_runner_interrupted,
                )
                if phase == "install" and not triggered and installing:
                    send_owned_signal()
                return real_signal(number, handler)

            def delayed_sigmask(how, mask):
                affected_final = lane == "affected" and all(
                    signal.getsignal(number) == handler
                    for number, handler in previous.items()
                )
                full_final = lane == "full" and runner._FULL_EXIT_CODE_FINALIZED
                if (
                    phase == "final"
                    and not triggered
                    and how == signal.SIG_SETMASK
                    and (affected_final or full_final)
                ):
                    send_owned_signal()
                return real_sigmask(how, mask)

            runner.signal.signal = delayed_signal
            runner.signal.pthread_sigmask = delayed_sigmask
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                modules = []
                for name in ("test_a.py", "test_z.py"):
                    (root / name).write_text(
                        "import unittest\\nclass Probe(unittest.TestCase):\\n    def test_ok(self): self.assertTrue(True)\\n",
                        encoding="utf-8",
                    )
                    modules.append(name)
                try:
                    if lane == "affected":
                        rows = runner._execute_modules(
                            root, modules, jobs=1, timeout_seconds=5.0
                        )
                        exit_code = runner._exit_code(rows)
                    else:
                        runner._acquire_full_interrupt_ownership()
                        rows = runner._execute_full_modules(
                            root,
                            modules,
                            exclusive_modules=[modules[-1]],
                            jobs=1,
                            timeout_seconds=5.0,
                        )
                        exit_code = runner._finalize_full_exit_code(
                            runner._exit_code(rows)
                        )
                except (runner.RunnerInterrupted, runner.SelectionError):
                    rows = []
                    exit_code = (
                        runner._finalize_full_exit_code(2)
                        if runner._FULL_SIGNAL_OWNED
                        else 2
                    )

            for sender in senders:
                sender.join(timeout=1.0)
                if sender.is_alive():
                    raise RuntimeError("signal sender leaked")
            payload = {{
                "exit_code": exit_code,
                "statuses": [row.status for row in rows],
                "modules": [row.module for row in rows],
                "restored": all(
                    signal.getsignal(number) == handler
                    for number, handler in previous.items()
                ),
                "triggered": triggered,
                "prior_hits": prior_hits,
            }}
            print(json.dumps(payload, sort_keys=True))
            raise SystemExit(exit_code)
            """
        )
        for lane, phase, prior in (
            ("affected", "install", "custom"),
            ("full", "install", "custom"),
            ("affected", "final", "custom"),
            ("affected", "final", "default"),
            ("full", "final", "custom"),
            ("full", "final", "default"),
        ):
            with self.subTest(lane=lane, phase=phase, prior=prior):
                with tempfile.TemporaryDirectory() as marker_root:
                    completed = subprocess.run(
                        [
                            sys.executable,
                            "-c",
                            probe,
                            phase,
                            lane,
                            prior,
                            marker_root,
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        timeout=15.0,
                    )
                    self.assertTrue((Path(marker_root) / "triggered").is_file())
                    prior_called = (Path(marker_root) / "prior-handler").exists()
                if phase == "install":
                    self.assertEqual(2, completed.returncode, completed.stderr)
                    payload = json.loads(completed.stdout)
                    self.assertEqual(2, payload["exit_code"])
                    self.assertFalse(prior_called)
                    if lane == "affected":
                        self.assertTrue(payload["restored"])
                        self.assertEqual(
                            ["interrupted", "not-run"], payload["statuses"]
                        )
                elif lane == "full":
                    self.assertEqual(2, completed.returncode, completed.stderr)
                    self.assertFalse(prior_called)
                elif prior == "custom":
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    payload = json.loads(completed.stdout)
                    self.assertTrue(payload["restored"])
                    self.assertTrue(prior_called)
                    self.assertEqual(["pass", "pass"], payload["statuses"])
                else:
                    self.assertEqual(-signal.SIGTERM, completed.returncode)
                    self.assertFalse(prior_called)

    def test_parser_rejects_non_positive_jobs_and_timeout(self) -> None:
        for argv in (
            ["run", "--jobs", "0"],
            ["run", "--timeout", "0"],
            ["run", "--timeout", "nan"],
            ["run", "--timeout", "inf"],
        ):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as raised:
                self.runner._parser().parse_args(argv)
            self.assertEqual(2, raised.exception.code)

    def test_empty_no_impact_selection_exits_zero_with_explicit_signal(self) -> None:
        selection = {
            "reason": "known-no-impact",
            "selected_test_modules": [],
        }
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ), mock.patch.object(self.runner, "_execute_modules") as execute, mock.patch.object(
            sys, "stdout", io.StringIO()
        ) as stdout:
            exit_code = self.runner.main(
                ["run", "--base", "a" * 40, "--head", "b" * 40]
            )
        self.assertEqual(0, exit_code)
        execute.assert_not_called()
        payload = json.loads(stdout.getvalue())
        self.assertEqual("known-no-impact", payload["reason"])
        self.assertEqual([], payload["test_modules"])

    def test_deleted_test_is_classified_but_never_executed(self) -> None:
        selection = {
            "reason": "affected-targets",
            "selected_test_modules": [],
        }
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ), mock.patch.object(self.runner, "_execute_modules") as execute:
            exit_code = self.runner.main(
                ["run", "--base", "a" * 40, "--head", "b" * 40]
            )
        self.assertEqual(0, exit_code)
        execute.assert_not_called()

    def test_renamed_test_executes_only_the_new_path(self) -> None:
        new_path = "tests/scripts/test_new.py"
        selection = {
            "reason": "affected-targets",
            "selected_test_modules": [new_path],
        }
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ), mock.patch.object(self.runner, "_execute_modules") as execute:
            self.assertEqual(
                0,
                self.runner.main(
                    [
                        "run",
                        "--base",
                        "a" * 40,
                        "--head",
                        "b" * 40,
                    ]
                ),
            )
        execute.assert_called_once_with(
            ROOT,
            [new_path],
            jobs=self.runner.DEFAULT_JOBS,
            timeout_seconds=self.runner.DEFAULT_TIMEOUT_SECONDS,
        )

    def test_resolver_failure_is_nonzero_and_machine_readable(self) -> None:
        failure = self.runner.ImpactGraphError(
            "unmatched-path", "path has no Core classification"
        )
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", side_effect=failure
        ), mock.patch.object(sys, "stderr", io.StringIO()) as stderr:
            exit_code = self.runner.main(
                ["explain", "--base", "a" * 40, "--head", "b" * 40]
            )
        self.assertEqual(2, exit_code)
        diagnostic = json.loads(stderr.getvalue().split(": ", 1)[1])
        self.assertEqual("unmatched-path", diagnostic["reason"])

    def test_runner_contains_no_path_mapping_or_full_fallback(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn("from impact_graph import", source)
        self.assertNotIn("ci_validation_contract", source)
        self.assertNotIn("fnmatch", source)
        self.assertNotIn("fallback", source.casefold())
        self.assertNotIn("shard", source.casefold())
        self.assertNotIn("test_validate_capabilities", source)
        self.assertNotIn("test_validate_root_content", source)

    def test_full_help_and_source_use_official_regression_terminology(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        help_text = self.runner._parser().format_help()
        stale_marker = "opt" + "-in"
        self.assertNotIn(stale_marker, source.casefold())
        self.assertNotIn(stale_marker, help_text.casefold())
        self.assertIn("full regression action", help_text.casefold())

    def test_timeout_help_describes_base_duration_and_class_multiplier(self) -> None:
        help_text = self.runner._parser().format_help().casefold()

        self.assertIn("base timeout in seconds per test module", help_text)
        self.assertIn("test_timeout_class multiplier", help_text)


if __name__ == "__main__":
    unittest.main()
