from __future__ import annotations

import copy
import importlib.util
import json
import os
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


def _load_regression_module():
    path = SCRIPTS / "validate-professionalism-regression.py"
    spec = importlib.util.spec_from_file_location(
        "expert_panel_release_manifest_tests",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


REGRESSION = _load_regression_module()
from validation_utils import validate_expert_panel_release_manifest  # noqa: E402


HEAD = "1" * 40


def _artifacts() -> list[dict]:
    return [
        {
            "axis": "readability",
            "path": "evals/expert-panel/readability.json",
            "external_sha256": "a" * 64,
            "size_bytes": 101,
            "review_id": "readability-current-a",
            "verdict": "accepted-current-readability",
            "head_byte_equal": True,
            "clean": True,
        },
        {
            "axis": "semantic-disposition",
            "path": "evals/expert-panel/semantic-disposition.json",
            "external_sha256": "b" * 64,
            "size_bytes": 202,
            "review_id": "semantic-current-b",
            "verdict": "accepted-current-semantic-disposition",
            "head_byte_equal": True,
            "clean": True,
        },
        {
            "axis": "professional-completeness",
            "path": "evals/expert-panel/professional-completeness.json",
            "external_sha256": "c" * 64,
            "size_bytes": 303,
            "review_id": "professional-current-c",
            "verdict": "accepted-current-professional-completeness",
            "head_byte_equal": True,
            "clean": True,
        },
    ]


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _release_repository(repository: Path) -> tuple[str, str]:
    _git(repository, "init")
    _git(repository, "config", "user.name", "Release Manifest Test")
    _git(repository, "config", "user.email", "release-manifest@example.invalid")
    for axis, relative, accepted_verdict in (
        REGRESSION.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "axis": axis,
                    "review_id": f"{axis}-review",
                    "verdict": accepted_verdict,
                }
            ),
            encoding="utf-8",
        )
    marker = repository / "marker.txt"
    marker.write_text("captured\n", encoding="utf-8")
    _git(repository, "add", "--", "evals/expert-panel", "marker.txt")
    _git(
        repository,
        "-c",
        "commit.gpgsign=false",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-m",
        "captured",
    )
    captured_commit = _git(repository, "rev-parse", "--verify", "HEAD")

    marker.write_text("moved\n", encoding="utf-8")
    _git(repository, "add", "--", "marker.txt")
    _git(
        repository,
        "-c",
        "commit.gpgsign=false",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-m",
        "moved",
    )
    moved_commit = _git(repository, "rev-parse", "--verify", "HEAD")
    _git(repository, "checkout", "--detach", captured_commit)
    return captured_commit, moved_commit


class ExpertPanelReleaseManifestTests(unittest.TestCase):
    def test_formal_professionalism_writer_rejects_symlinked_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            outside = root / "outside"
            outside.mkdir()
            (root / ".rd-skills").symlink_to(outside, target_is_directory=True)
            destination = (
                root
                / ".rd-skills"
                / "formal-release"
                / ("a" * 40)
                / "reports"
                / "professionalism-regression-report.json"
            )

            with self.assertRaisesRegex(ValueError, "symlink|safe directory"):
                REGRESSION._atomic_write(
                    destination,
                    "{}\n",
                    trusted_root=root,
                )

            self.assertFalse((outside / "formal-release").exists())

    def test_formal_manifest_rejects_head_outside_captured_core_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repository = Path(raw)
            captured_commit, _moved_commit = _release_repository(repository)
            with mock.patch.object(
                REGRESSION, "ROOT", repository
            ), mock.patch.dict(
                os.environ,
                {REGRESSION.FORMAL_HEAD_COMMIT_ENV: "f" * 40},
                clear=False,
            ), self.assertRaisesRegex(
                ValueError,
                "captured Core HEAD",
            ):
                REGRESSION._expert_panel_release_manifest(
                    formal=True,
                    storage_statuses={
                        "readability": "current",
                        "semantic-disposition": "current",
                        "professional-completeness": "current",
                    },
                )

            self.assertNotEqual("f" * 40, captured_commit)

    def test_formal_manifest_reads_artifacts_from_captured_commit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repository = Path(raw)
            captured_commit, _moved_commit = _release_repository(repository)
            with mock.patch.object(
                REGRESSION, "ROOT", repository
            ), mock.patch.object(
                REGRESSION,
                "_git_head_blob",
                wraps=REGRESSION._git_head_blob,
            ) as read_blob:
                manifest = REGRESSION._expert_panel_release_manifest(
                    formal=True,
                    storage_statuses={
                        "readability": "current",
                        "semantic-disposition": "current",
                        "professional-completeness": "current",
                    },
                )

            self.assertEqual(captured_commit, manifest["head_commit"])
            self.assertEqual(
                [
                    mock.call(relative, commit=captured_commit)
                    for _axis, relative, _verdict in (
                        REGRESSION.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
                    )
                ],
                read_blob.call_args_list,
            )

    def test_formal_manifest_rejects_head_swap_before_return(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repository = Path(raw)
            captured_commit, moved_commit = _release_repository(repository)
            read_head = REGRESSION._git_head_commit
            read_count = 0

            def read_head_then_swap() -> str:
                nonlocal read_count
                commit = read_head()
                read_count += 1
                if read_count == 1:
                    _git(repository, "update-ref", "HEAD", moved_commit)
                return commit

            with mock.patch.object(
                REGRESSION, "ROOT", repository
            ), mock.patch.object(
                REGRESSION,
                "_git_head_commit",
                side_effect=read_head_then_swap,
            ), self.assertRaisesRegex(
                ValueError,
                "HEAD is not the current commit",
            ):
                REGRESSION._expert_panel_release_manifest(
                    formal=True,
                    storage_statuses={
                        "readability": "current",
                        "semantic-disposition": "current",
                        "professional-completeness": "current",
                    },
                )

            self.assertEqual(2, read_count)
            self.assertEqual(moved_commit, _git(repository, "rev-parse", "HEAD"))
            self.assertNotEqual(captured_commit, moved_commit)
            for _axis, relative, _verdict in (
                REGRESSION.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
            ):
                self.assertEqual(
                    "",
                    _git(
                        repository,
                        "status",
                        "--porcelain=v1",
                        "--",
                        relative,
                    ),
                )

    def test_formal_manifest_is_exact_current_external_identity(self) -> None:
        manifest = REGRESSION._derive_expert_panel_release_manifest(
            formal=True,
            storage_statuses={
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            },
            current_head_commit=HEAD,
            manifest_head_commit=HEAD,
            artifact_observations=_artifacts(),
        )
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual("current", manifest["status"])
        self.assertEqual(HEAD, manifest["head_commit"])
        self.assertEqual(3, len(manifest["artifacts"]))
        self.assertEqual(
            [
                "evals/expert-panel/readability.json",
                "evals/expert-panel/semantic-disposition.json",
                "evals/expert-panel/professional-completeness.json",
            ],
            [row["path"] for row in manifest["artifacts"]],
        )
        for row in manifest["artifacts"]:
            self.assertEqual(
                {
                    "axis",
                    "path",
                    "external_sha256",
                    "size_bytes",
                    "review_id",
                    "verdict",
                },
                set(row),
            )
        self.assertEqual(
            {
                "head_commit_matches_current": True,
                "artifact_count": 3,
                "accepted_artifact_count": 3,
                "head_byte_equal_count": 3,
                "clean_artifact_count": 3,
            },
            manifest["verification_toolchain"],
        )

    def test_ordinary_manifest_is_nonblocking_and_does_not_hash_artifacts(self) -> None:
        expected = {
            "all-current": "not-evaluated",
            "missing": "missing",
            "stale": "stale",
            "pending": "pending",
        }
        for label, expected_status in expected.items():
            statuses = {
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            }
            if label != "all-current":
                statuses["readability"] = label
            with self.subTest(label=label):
                manifest = REGRESSION._derive_expert_panel_release_manifest(
                    formal=False,
                    storage_statuses=statuses,
                    current_head_commit=None,
                    manifest_head_commit=None,
                    artifact_observations=None,
                )
                self.assertEqual(expected_status, manifest["status"])
                self.assertIsNone(manifest["head_commit"])
                self.assertEqual([], manifest["artifacts"])
                self.assertIsNone(manifest["verification_toolchain"])

    def test_formal_manifest_fails_closed_on_identity_or_acceptance_tamper(self) -> None:
        mutations = {
            "missing": lambda rows: rows.pop(),
            "wrong-axis": lambda rows: rows[0].update(
                {"axis": "semantic-disposition"}
            ),
            "wrong-path": lambda rows: rows[0].update(
                {"path": "evals/expert-panel/fourth.json"}
            ),
            "adverse-verdict": lambda rows: rows[2].update(
                {"verdict": "requires-professional-correction"}
            ),
            "head-drift": lambda rows: rows[1].update(
                {"head_byte_equal": False}
            ),
            "dirty": lambda rows: rows[0].update({"clean": False}),
        }
        for label, mutate in mutations.items():
            rows = _artifacts()
            mutate(rows)
            with self.subTest(label=label), self.assertRaises(ValueError):
                REGRESSION._derive_expert_panel_release_manifest(
                    formal=True,
                    storage_statuses={
                        "readability": "current",
                        "semantic-disposition": "current",
                        "professional-completeness": "current",
                    },
                    current_head_commit=HEAD,
                    manifest_head_commit=HEAD,
                    artifact_observations=rows,
                )

        with self.assertRaises(ValueError):
            REGRESSION._derive_expert_panel_release_manifest(
                formal=True,
                storage_statuses={
                    "readability": "current",
                    "semantic-disposition": "current",
                    "professional-completeness": "current",
                },
                current_head_commit=HEAD,
                manifest_head_commit="2" * 40,
                artifact_observations=_artifacts(),
            )

    def test_formal_manifest_requires_all_storage_axes_current(self) -> None:
        for state in ("missing", "stale", "pending", "not-evaluated"):
            statuses = {
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            }
            statuses["semantic-disposition"] = state
            with self.subTest(state=state), self.assertRaises(ValueError):
                REGRESSION._derive_expert_panel_release_manifest(
                    formal=True,
                    storage_statuses=statuses,
                    current_head_commit=HEAD,
                    manifest_head_commit=HEAD,
                    artifact_observations=copy.deepcopy(_artifacts()),
                )

    def test_report_schema_rechecks_manifest_commit_and_closed_artifacts(self) -> None:
        manifest = REGRESSION._derive_expert_panel_release_manifest(
            formal=True,
            storage_statuses={
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            },
            current_head_commit=HEAD,
            manifest_head_commit=HEAD,
            artifact_observations=_artifacts(),
        )
        self.assertEqual(
            [],
            validate_expert_panel_release_manifest(
                manifest,
                require_current=True,
                expected_head_commit=HEAD,
            ),
        )
        self.assertTrue(
            validate_expert_panel_release_manifest(
                manifest,
                require_current=True,
                expected_head_commit="2" * 40,
            )
        )
        tampered = copy.deepcopy(manifest)
        tampered["artifacts"].append(copy.deepcopy(tampered["artifacts"][0]))
        self.assertTrue(
            validate_expert_panel_release_manifest(
                tampered,
                require_current=True,
                expected_head_commit=HEAD,
            )
        )


if __name__ == "__main__":
    unittest.main()
