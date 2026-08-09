from __future__ import annotations

import copy
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.scripts.affected_test_support import core_fixture_owner
from tests.scripts.test_eval_core_principles import (
    EVALUATOR,
    PROCESS_PASS,
    REPORT_SCHEMA,
    ROOT,
    impact_graph,
)


_FIXTURES = core_fixture_owner()


class CoreAffectedTests(unittest.TestCase):
    _root = _FIXTURES._root
    _script = _FIXTURES._script
    _contract = _FIXTURES._contract
    _producer = _FIXTURES._producer
    _passing_report = _FIXTURES._passing_report
    _write_contract = _FIXTURES._write_contract

    def test_affected_archive_extracts_only_valid_regular_files(self) -> None:
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as created:
            directory = tarfile.TarInfo("nested")
            directory.type = tarfile.DIRTYPE
            created.addfile(directory)
            payload = b"tracked\n"
            regular = tarfile.TarInfo("nested/tracked.txt")
            regular.size = len(payload)
            regular.mode = 0o640
            created.addfile(regular, io.BytesIO(payload))
        archive.seek(0)
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "repository"
            EVALUATOR._extract_tracked_archive(archive, destination)
            extracted = destination / "nested/tracked.txt"
            self.assertEqual(payload, extracted.read_bytes())
            self.assertEqual(0o640, extracted.stat().st_mode & 0o777)

    def test_affected_archive_rejects_hostile_paths_before_any_write(self) -> None:
        hostile_names = {
            "empty": "",
            "dot": "./outside.txt",
            "empty-component": "nested//outside.txt",
            "posix-parent": "../outside.txt",
            "posix-absolute": "/outside.txt",
            "backslash-parent": r"nested\..\outside.txt",
            "drive-qualified": "C:/outside.txt",
            "unc-forward": "//server/share/outside.txt",
            "unc-backslash": r"\\server\share\outside.txt",
            "device-path": r"\\?\C:\outside.txt",
        }
        for label, hostile_name in hostile_names.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                sentinel = root / "outside.txt"
                sentinel.write_text("unchanged\n", encoding="utf-8")
                archive = io.BytesIO()
                with tarfile.open(fileobj=archive, mode="w") as created:
                    safe_payload = b"must-not-be-written\n"
                    safe = tarfile.TarInfo("safe.txt")
                    safe.size = len(safe_payload)
                    created.addfile(safe, io.BytesIO(safe_payload))
                    hostile = tarfile.TarInfo(hostile_name)
                    hostile.size = 1
                    created.addfile(hostile, io.BytesIO(b"x"))
                archive.seek(0)

                with self.assertRaises(EVALUATOR.ImpactGraphError) as raised:
                    EVALUATOR._extract_tracked_archive(
                        archive, root / "repository"
                    )

                self.assertEqual("unsafe-archive-entry", raised.exception.reason)
                self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))
                self.assertFalse((root / "repository").exists())

    def test_affected_archive_rejects_links_and_non_regular_entries_before_write(self) -> None:
        entry_types = {
            "symlink": tarfile.SYMTYPE,
            "hardlink": tarfile.LNKTYPE,
            "fifo": tarfile.FIFOTYPE,
        }
        for label, entry_type in entry_types.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                sentinel = root / "outside.txt"
                sentinel.write_text("unchanged\n", encoding="utf-8")
                archive = io.BytesIO()
                with tarfile.open(fileobj=archive, mode="w") as created:
                    safe = tarfile.TarInfo("safe.txt")
                    safe.size = 1
                    created.addfile(safe, io.BytesIO(b"x"))
                    hostile = tarfile.TarInfo("hostile")
                    hostile.type = entry_type
                    hostile.linkname = "../outside.txt"
                    created.addfile(hostile)
                archive.seek(0)

                with self.assertRaises(EVALUATOR.ImpactGraphError) as raised:
                    EVALUATOR._extract_tracked_archive(
                        archive, root / "repository"
                    )

                self.assertEqual("unsafe-archive-entry", raised.exception.reason)
                self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))
                self.assertFalse((root / "repository").exists())

    def test_affected_archive_rejects_native_target_outside_resolved_destination(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            destination = root / "repository"
            destination.mkdir()
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")
            try:
                (destination / "redirect").symlink_to(
                    outside, target_is_directory=True
                )
            except OSError as exc:
                self.skipTest(f"directory symlinks are unavailable: {exc}")
            archive = io.BytesIO()
            with tarfile.open(fileobj=archive, mode="w") as created:
                safe = tarfile.TarInfo("safe.txt")
                safe.size = 1
                created.addfile(safe, io.BytesIO(b"x"))
                escaped = tarfile.TarInfo("redirect/sentinel.txt")
                escaped.size = 7
                created.addfile(escaped, io.BytesIO(b"changed"))
            archive.seek(0)

            with self.assertRaises(EVALUATOR.ImpactGraphError) as raised:
                EVALUATOR._extract_tracked_archive(archive, destination)

            self.assertEqual("unsafe-archive-entry", raised.exception.reason)
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))
            self.assertFalse((destination / "safe.txt").exists())

    def test_affected_archive_and_extraction_failures_are_classified(self) -> None:
        head = "a" * 40
        current = subprocess.CompletedProcess(
            ["git", "rev-parse"], 0, stdout=head + "\n", stderr=""
        )
        clean = subprocess.CompletedProcess(
            ["git", "status"], 0, stdout=b"", stderr=b""
        )
        archive_failure = subprocess.CompletedProcess(
            ["git", "archive"], 1, stdout=None, stderr=b"failed"
        )
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            EVALUATOR.subprocess,
            "run",
            side_effect=[current, clean, archive_failure],
        ) as run:
            with self.assertRaises(EVALUATOR.ImpactGraphError) as raised:
                EVALUATOR.run_affected_isolated(Path(raw), {}, [], head)
        self.assertEqual("isolation-archive-failed", raised.exception.reason)
        self.assertEqual(
            ["git", "archive", "--format=tar", head],
            run.call_args_list[2].args[0],
        )

        archive_success = subprocess.CompletedProcess(
            ["git", "archive"], 0, stdout=None, stderr=b""
        )
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            EVALUATOR.subprocess,
            "run",
            side_effect=[current, clean, archive_success],
        ), mock.patch.object(
            EVALUATOR,
            "_extract_tracked_archive",
            side_effect=tarfile.ReadError("invalid archive"),
        ):
            with self.assertRaises(EVALUATOR.ImpactGraphError) as raised:
                EVALUATOR.run_affected_isolated(Path(raw), {}, [], head)
        self.assertEqual("isolation-archive-failed", raised.exception.reason)

    def test_affected_execution_is_deduplicated_and_isolates_reports_and_dist(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        (root / ".gitignore").write_text(".env\n", encoding="utf-8")
        (root / ".env").write_text("IGNORED_SECRET=visible\n", encoding="utf-8")
        (root / "dist").mkdir()
        (root / "dist/original.txt").write_text("original\n", encoding="utf-8")
        (root / "reports/result.json").write_text(
            '{"schema_version":0}\n', encoding="utf-8"
        )
        script = self._script(
            root,
            "isolated",
            "from pathlib import Path\nimport json\n"
            "if Path('.env').exists():\n    raise SystemExit(7)\n"
            "Path('dist').mkdir(exist_ok=True)\n"
            "Path('dist/generated.txt').write_text('generated\\n')\n"
            "Path('reports').mkdir(exist_ok=True)\n"
            "Path('reports/result.json').write_text(json.dumps({'schema_version':1})+'\\n')\n",
        )
        producer = self._producer(
            "isolated", script, reports=["reports/result.json"]
        )
        contract = self._contract(
            [producer],
            [
                {
                    "id": "isolated-pass",
                    "producer": "isolated",
                    "predicates": [PROCESS_PASS, REPORT_SCHEMA],
                }
            ],
        )
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=root,
            check=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        self.assertEqual(b"", status)
        self.assertTrue((root / ".env").is_file())
        result = EVALUATOR.run_affected_isolated(
            root, contract, ["isolated"], head
        )
        self.assertEqual("pass", result["status"])
        self.assertEqual(1, result["command_execution_count"])
        self.assertEqual('{"schema_version":0}\n', (root / "reports/result.json").read_text())
        self.assertEqual("original\n", (root / "dist/original.txt").read_text())
        self.assertFalse((root / "dist/generated.txt").exists())

    def test_affected_execution_supports_a_linked_worktree(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        container = Path(temporary.name)
        primary = container / "primary"
        linked = container / "linked"
        primary.mkdir()
        (primary / "scripts").mkdir()
        (primary / "src/control-model").mkdir(parents=True)
        (primary / "reports").mkdir()
        (primary / ".gitignore").write_text(".env\n", encoding="utf-8")
        (primary / "reports/result.json").write_text(
            '{"schema_version":0}\n', encoding="utf-8"
        )
        script = self._script(
            primary,
            "linked",
            "from pathlib import Path\nimport json\n"
            "if Path('.env').exists():\n    raise SystemExit(7)\n"
            "Path('reports/result.json').write_text(json.dumps({'schema_version':1})+'\\n')\n",
        )
        producer = self._producer(
            "linked", script, reports=["reports/result.json"]
        )
        contract = self._contract(
            [producer],
            [
                {
                    "id": "linked-pass",
                    "producer": "linked",
                    "predicates": [PROCESS_PASS, REPORT_SCHEMA],
                }
            ],
        )
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "."],
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
        ):
            subprocess.run(command, cwd=primary, check=True)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=primary,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        subprocess.run(
            ["git", "worktree", "add", "--detach", "-q", str(linked), head],
            cwd=primary,
            check=True,
        )
        (linked / ".env").write_text("IGNORED_SECRET=visible\n", encoding="utf-8")
        self.assertTrue((linked / ".git").is_file())
        self.assertEqual(
            b"",
            subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=linked,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout,
        )

        result = EVALUATOR.run_affected_isolated(
            linked, contract, ["linked"], head
        )

        self.assertEqual("pass", result["status"])
        self.assertEqual(
            '{"schema_version":0}\n',
            (linked / "reports/result.json").read_text(encoding="utf-8"),
        )

    def test_affected_evaluates_only_authoring_eligible_outcomes(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "affected-authoring",
            "from pathlib import Path\nimport json\n"
            "Path('reports/result.json').write_text(json.dumps({'schema_version':1,'authoring':True,'formal':False})+'\\n')\n",
        )
        producer = self._producer(
            "affected-authoring", script, reports=["reports/result.json"]
        )
        authoring = {
            "id": "affected-authoring-pass",
            "producer": producer["id"],
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/authoring",
                    "operator": "equals",
                    "expected": True,
                },
            ],
        }
        formal = {
            "id": "affected-formal-fail",
            "producer": producer["id"],
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/formal",
                    "operator": "equals",
                    "expected": True,
                },
            ],
        }
        contract = self._contract(
            [producer], [authoring, formal], formal_outcomes=[formal["id"]]
        )

        report = EVALUATOR.evaluate_affected(root, contract, [producer["id"]])

        self.assertEqual("pass", report["status"])
        self.assertEqual([authoring["id"]], [row["id"] for row in report["outcomes"]])

    def test_affected_explain_never_executes_or_writes_reports(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        contract = self._contract(
            [self._producer("pass", self._script(root, "pass", "raise SystemExit(0)\n"))],
            [{"id": "pass", "producer": "pass", "predicates": [PROCESS_PASS]}],
        )
        self._write_contract(root, contract)
        selection = {
            "schema_version": 1,
            "kind": "changeforge.impact_selection",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "status": "resolved",
            "reason": "known-no-impact",
            "changed_paths": [],
            "selected_producer_ids": [],
            "selected_test_modules": [],
            "producer_explanations": [],
        }
        with mock.patch.object(
            EVALUATOR, "validate_core_contracts", return_value=[]
        ), mock.patch.object(
            EVALUATOR, "select_impact", return_value=selection
        ), mock.patch.object(
            EVALUATOR, "run_affected_isolated"
        ) as execute, mock.patch.object(
            sys, "stdout", io.StringIO()
        ) as stdout:
            exit_code = EVALUATOR.main(
                [
                    "--root",
                    str(root),
                    "--gate",
                    "affected",
                    "--base",
                    "a" * 40,
                    "--head",
                    "b" * 40,
                    "--explain",
                ]
            )
        self.assertEqual(0, exit_code)
        execute.assert_not_called()
        self.assertEqual(selection, json.loads(stdout.getvalue()))
        self.assertFalse((root / EVALUATOR.JSON_REPORT).exists())
        self.assertFalse((root / EVALUATOR.MARKDOWN_REPORT).exists())

    def test_affected_gate_explains_deterministic_fixture_commits(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        canonical = json.loads(
            (ROOT / EVALUATOR.CANONICAL_CONTRACT_SOURCE).read_text(encoding="utf-8")
        )
        self._write_contract(root, canonical)
        fixtures = {
            "skill": root / "src/professional-skills/example/SKILL.md",
            "reference": root / "src/professional-skills/example/references/example.md",
            "docs": root / "docs/fixture.md",
            "profile": root / "src/agent-profiles/fixture.json",
            "quickstart": root / "scripts/quickstart.py",
            "codegen": root / "evals/codegen/validation/fixture/prompt.md",
        }
        for path in fixtures.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("base\n", encoding="utf-8")
        registry = root / "src/registry"
        registry.mkdir(parents=True, exist_ok=True)
        for name, value in {
            "professional-skills.yaml": (
                "schema_version: 1\nprofessional_skills:\n"
                "  - name: example\n"
                "    path: src/professional-skills/example\n"
            ),
            "foundation-skills.yaml": (
                "schema_version: 1\nfoundation_skills: []\n"
            ),
            "domain-skills.yaml": "schema_version: 1\ndomain_skills: []\n",
        }.items():
            (registry / name).write_text(value, encoding="utf-8")

        def git(*arguments: str, output: bool = False) -> str:
            completed = subprocess.run(
                ["git", *arguments],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE if output else subprocess.DEVNULL,
            )
            return completed.stdout.strip() if output else ""

        git("init", "-q")
        git("add", ".")
        git(
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "base",
        )
        base = git("rev-parse", "HEAD", output=True)
        expected = {
            "skill": {"audit-skill-content", "validate-reference-content"},
            "reference": {"audit-skill-content", "validate-reference-content"},
            "docs": {"validate-docs-consistency"},
            "profile": {"validate-agent-profiles", "build-recommended"},
            "quickstart": set(),
            "codegen": set(),
        }
        expected_tests = {
            "quickstart": {"tests/scripts/test_quickstart.py"},
            "codegen": {"tests/scripts/test_run_codegen_benchmarks.py"},
        }
        machine_outputs = {}
        with mock.patch.object(
            EVALUATOR, "validate_core_contracts", return_value=[]
        ):
            for label, path in fixtures.items():
                if label == "reference":
                    path.unlink()
                else:
                    path.write_text(f"changed-{label}\n", encoding="utf-8")
                git("add", "-A")
                git(
                    "-c",
                    "user.name=Fixture",
                    "-c",
                    "user.email=fixture@example.invalid",
                    "commit",
                    "-qm",
                    label,
                )
                head = git("rev-parse", "HEAD", output=True)
                with mock.patch.object(sys, "stdout", io.StringIO()) as stdout:
                    exit_code = EVALUATOR.main(
                        [
                            "--root",
                            str(root),
                            "--gate",
                            "affected",
                            "--base",
                            base,
                            "--head",
                            head,
                            "--explain",
                        ]
                    )
                self.assertEqual(0, exit_code, label)
                selection = json.loads(stdout.getvalue())
                machine_outputs[label] = selection
                self.assertTrue(
                    expected[label].issubset(set(selection["selected_producer_ids"])),
                    (label, selection),
                )
                if label in expected_tests:
                    self.assertEqual(
                        expected_tests[label],
                        set(selection["selected_test_modules"]),
                        (label, selection),
                    )
                self.assertEqual(1, len(selection["changed_paths"]), selection)
                base = head
        self.assertEqual(set(fixtures), set(machine_outputs))
        self.assertEqual(
            "D", machine_outputs["reference"]["changed_paths"][0]["status"]
        )



del _FIXTURES


if __name__ == "__main__":
    unittest.main()
