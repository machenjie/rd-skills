from __future__ import annotations

import ast
import importlib.util
import hashlib
import inspect
import os
import stat
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit-skill-content.py"
ROOT_DETECTOR_V3_FINGERPRINT = (
    "1c511eaa70d9a4138d6acb6a989e598c3221089312363d5e077a15032357c464"
)
SKILL_DETECTOR_V3_FINGERPRINT = (
    "0d57d32d45961cd4a542edb99256ccba1cf1905aacc42d4af3ba803ffd21f3c3"
)


def _load_module(
    name: str = "root_disposition_lifecycle_test_auditor",
):
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RootDispositionLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _document(self, text: str, *, path: str = "src/example/SKILL.md") -> dict:
        return {
            "path": path,
            "document_part": "body",
            "layer": "foundation-capability",
            "owner": "example",
            "text": text,
        }

    def _detector_source_change(
        self,
        original: str,
        replacement: str,
        *,
        relative: str = "scripts/audit-skill-content.py",
    ):
        source_path = (ROOT / relative).resolve()
        source_reader = self.module._detector_repository_source_text

        def changed(path: Path) -> str:
            text = source_reader(path)
            if path.resolve() != source_path:
                return text
            self.assertEqual(1, text.count(original))
            return text.replace(original, replacement, 1)

        return mock.patch.object(
            self.module,
            "_detector_repository_source_text",
            side_effect=changed,
        )

    def _entry(
        self,
        candidate: str,
        *,
        text_fingerprint: str = "1" * 64,
        path: str = "src/example/SKILL.md",
        disposition: str = "valid-contextual-rule",
    ) -> dict:
        return {
            "candidate_id": candidate * 64,
            "finding": "unconditional_mechanism_candidate",
            "path": path,
            "document_part": "body",
            "fingerprint": text_fingerprint,
            "skill_owner": "example",
            "priority": "P1",
            "disposition": disposition,
        }

    def _snapshot(
        self,
        entries: list[dict],
        documents: list[dict],
        *,
        kind: str,
        release_id: str | None = None,
        released_on: str | None = None,
        prior: dict | None = None,
        reviews: list[dict] | None = None,
        bootstrap_reviews: list[dict] | None = None,
        bootstrap_refresh_origin_state_fingerprint: str | None = None,
    ) -> dict:
        return self.module._root_semantic_snapshot(
            entries,
            self.module._root_document_fingerprints(documents),
            kind=kind,
            release_id=release_id,
            released_on=released_on,
            prior=prior,
            change_reviews=reviews,
            bootstrap_refresh_reviews=bootstrap_reviews,
            bootstrap_refresh_origin_state_fingerprint=(
                bootstrap_refresh_origin_state_fingerprint
            ),
        )

    def _bootstrap_refresh(
        self,
        prior: dict,
        entries: list[dict],
        documents: list[dict],
        *,
        reviewer: str = "changeforge-maintainers",
        rationale: str = "Current Root source and detector evidence was reviewed for authoring bootstrap freshness.",
    ) -> dict:
        current = self._snapshot(
            entries,
            documents,
            kind="bootstrap",
            prior=prior,
            bootstrap_reviews=prior["bootstrap_refresh_reviews"],
            bootstrap_refresh_origin_state_fingerprint=prior[
                "bootstrap_refresh_origin_state_fingerprint"
            ],
        )
        review = self.module._root_recorded_bootstrap_refresh_review(
            prior,
            current,
            reviewed_by=reviewer,
            rationale=rationale,
        )
        current["bootstrap_refresh_reviews"] = [
            *prior["bootstrap_refresh_reviews"],
            review,
        ]
        current["bootstrap_refresh_review_count"] = len(
            current["bootstrap_refresh_reviews"]
        )
        return current

    def _record_reviews(
        self,
        previous: dict,
        current: dict,
        documents: list[dict],
        *,
        change_reviews: list[tuple[str, str, str]] | None = None,
        source_replacement_reviews: list[tuple[str, str, str, str]] | None = None,
        source_removal_reviews: list[tuple[str, str, str]] | None = None,
        replacement_reviews: list[tuple[str, str, str, str]] | None = None,
        removal_reviews: list[tuple[str, str, str]] | None = None,
    ) -> list[dict]:
        fingerprints = self.module._root_document_fingerprints(documents)
        comparison, errors = self.module._root_lifecycle_comparison(
            previous, current, fingerprints
        )
        self.assertEqual([], errors)
        return self.module._root_recorded_change_reviews(
            list(change_reviews or []),
            comparison,
            previous=previous,
            current=current,
            current_document_fingerprints=fingerprints,
            source_replacement_reviews=source_replacement_reviews,
            source_removal_reviews=source_removal_reviews,
            source_detector_replacement_reviews=replacement_reviews,
            source_detector_removal_reviews=removal_reviews,
        )

    def _record_release(
        self,
        lifecycle: dict,
        entries: list[dict],
        documents: list[dict],
        *,
        release_id: str,
        released_on: str,
        evaluation_date: date,
    ) -> tuple[dict, list[dict]]:
        report = {"disposition_contract": {"entries": entries, "errors": []}}
        written: list[dict] = []
        with (
            mock.patch.object(
                self.module, "_root_skill_documents", return_value=documents
            ),
            mock.patch.object(
                self.module,
                "_collect_root_semantic_advisories",
                return_value=report,
            ),
            mock.patch.object(
                self.module,
                "_load_root_semantic_dispositions_for_recorder",
                return_value=(
                    {
                        "schema_version": self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                        "lifecycle": lifecycle,
                        "entries": entries,
                    },
                    self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                    "a" * 64,
                    [],
                ),
            ),
            mock.patch.object(
                self.module,
                "_replace_root_semantic_lifecycle_block",
                side_effect=lambda _path, value, **_kwargs: written.append(value),
            ),
        ):
            result = self.module._record_root_semantic_release(
                release_id,
                released_on,
                evaluation_date=evaluation_date,
            )
        return result, written

    def _dual_snapshots(
        self,
        previous_entries: list[dict],
        current_entries: list[dict],
        previous_documents: list[dict],
        current_documents: list[dict],
    ) -> tuple[dict, dict]:
        previous = self._snapshot(
            previous_entries,
            previous_documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-12",
        )
        previous["detector_fingerprint"] = "0" * 64
        current = self._snapshot(
            current_entries,
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )
        return previous, current

    def _replace_lifecycle(self, target: Path, lifecycle: dict) -> None:
        source_schema = self.module.load_yaml_file(target)[
            self.module.ROOT_SEMANTIC_DISPOSITION_KEY
        ]["schema_version"]
        self.module._replace_root_semantic_lifecycle_block(
            target,
            lifecycle,
            source_schema_version=source_schema,
            expected_preimage_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        )

    def _legacy_v2_config_text(self, snapshot: dict) -> str:
        lines = [
            f"{self.module.ROOT_SEMANTIC_DISPOSITION_KEY}:",
            f"  schema_version: {self.module.ROOT_SEMANTIC_LEGACY_DISPOSITION_SCHEMA_VERSION}",
            "  lifecycle:",
            f"    schema_version: {self.module.ROOT_SEMANTIC_LEGACY_LIFECYCLE_SCHEMA_VERSION}",
            "    previous: null",
            "    current:",
        ]
        scalar_fields = (
            "schema_version",
            "kind",
            "release_id",
            "released_on",
            "document_fingerprint",
            "detector_fingerprint",
        )
        for field in scalar_fields:
            lines.append(
                f"      {field}: "
                + self.module.json.dumps(snapshot[field], separators=(",", ":"))
            )
        for field in sorted(set(snapshot) - set(scalar_fields) - {"entries", "change_reviews"}):
            lines.append(
                f"      {field}: "
                + self.module.json.dumps(snapshot[field], separators=(",", ":"))
            )
        for field in ("entries", "change_reviews"):
            lines.append(f"      {field}:")
            if snapshot[field]:
                lines.extend(
                    "        - "
                    + self.module.json.dumps(item, separators=(",", ":"))
                    for item in snapshot[field]
                )
            else:
                lines[-1] += " []"
        lines.append("  entries: []")
        return "\n".join(lines) + "\n"

    def _schema_config_text(
        self,
        lifecycle: dict,
        *,
        root_schema_version: int,
        lifecycle_schema_version: int,
    ) -> str:
        rendered = self.module._render_root_semantic_lifecycle_yaml(lifecycle)
        rendered = rendered.replace(
            f"    schema_version: {self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION}\n",
            f"    schema_version: {lifecycle_schema_version}\n",
            1,
        )
        return (
            f"{self.module.ROOT_SEMANTIC_DISPOSITION_KEY}:\n"
            f"  schema_version: {root_schema_version}\n"
            f"{rendered}\n"
            "  entries: []\n"
        )

    def test_bootstrap_has_null_deltas_and_unknown_age(self) -> None:
        documents = [self._document("bootstrap source")]
        entries = [self._entry("a")]
        lifecycle = self.module._root_bootstrap_lifecycle(
            entries, self.module._root_document_fingerprints(documents)
        )
        report = self.module._evaluate_root_semantic_lifecycle(
            lifecycle, entries, documents, evaluation_date=date(2026, 7, 14)
        )
        self.assertEqual("bootstrap-current", report["status"])
        self.assertFalse(report["formal_release_ready"])
        for field in (
            "added_count",
            "removed_count",
            "source_rewrite_count",
            "detector_improvement_count",
            "unclassified_count",
        ):
            self.assertIsNone(report["comparison"][field])
        self.assertEqual(
            {"known_age_count": 0, "unknown_age_count": 1, "max_age_days": None},
            report["age"],
        )
        self.assertEqual(
            {"valid": True, "count": 0, "latest_delta": None},
            report["bootstrap_refresh_chain"],
        )

    def test_bootstrap_refresh_chain_covers_each_change_surface_and_repeat(self) -> None:
        first_documents = [self._document("first source")]
        first_entries = [self._entry("a"), self._entry("b", text_fingerprint="2" * 64)]
        bootstrap = self._snapshot(first_entries, first_documents, kind="bootstrap")

        second_documents = [self._document("second source")]
        document_only = self._bootstrap_refresh(
            bootstrap, first_entries, second_documents
        )
        latest = document_only["bootstrap_refresh_reviews"][-1]["evidence"]
        self.assertEqual(2, len(latest["prior_overrides"]))
        self.assertNotEqual(
            latest["prior_document_fingerprint"],
            latest["current_document_fingerprint"],
        )

        disposition_entries = [
            self._entry("a", disposition="false-positive"),
            self._entry("b", text_fingerprint="2" * 64),
        ]
        disposition_only = self._bootstrap_refresh(
            document_only, disposition_entries, second_documents
        )
        latest = disposition_only["bootstrap_refresh_reviews"][-1]["evidence"]
        self.assertEqual(1, len(latest["prior_overrides"]))
        self.assertNotEqual(
            latest["prior_disposition_fingerprint"],
            latest["current_disposition_fingerprint"],
        )

        replacement_entries = [
            self._entry("b", text_fingerprint="2" * 64),
            self._entry("c", text_fingerprint="3" * 64),
        ]
        replacement = self._bootstrap_refresh(
            disposition_only, replacement_entries, second_documents
        )
        latest = replacement["bootstrap_refresh_reviews"][-1]["evidence"]
        self.assertEqual(["c" * 64], latest["added_candidate_ids"])
        self.assertEqual(
            ["a" * 64],
            [entry["candidate_id"] for entry in latest["removed_entries"]],
        )

        detector_only = self._snapshot(
            replacement_entries,
            second_documents,
            kind="bootstrap",
            prior=replacement,
            bootstrap_reviews=replacement["bootstrap_refresh_reviews"],
            bootstrap_refresh_origin_state_fingerprint=replacement[
                "bootstrap_refresh_origin_state_fingerprint"
            ],
        )
        detector_only["detector_fingerprint"] = "f" * 64
        detector_review = self.module._root_recorded_bootstrap_refresh_review(
            replacement,
            detector_only,
            reviewed_by="changeforge-maintainers",
            rationale="The changed detector contract and stable candidate set were reviewed for authoring bootstrap freshness.",
        )
        detector_only["bootstrap_refresh_reviews"] = [
            *replacement["bootstrap_refresh_reviews"],
            detector_review,
        ]
        detector_only["bootstrap_refresh_review_count"] = len(
            detector_only["bootstrap_refresh_reviews"]
        )
        summary, errors = self.module._root_bootstrap_refresh_chain_summary(
            detector_only
        )
        self.assertEqual([], errors)
        self.assertTrue(summary["valid"])
        self.assertEqual(4, summary["count"])
        self.assertEqual(
            {
                "added_count": 0,
                "removed_count": 0,
                "prior_override_count": 0,
                "document_changed": False,
                "detector_changed": True,
                "candidate_changed": False,
                "disposition_changed": False,
            },
            summary["latest_delta"],
        )

    def test_bootstrap_refresh_rejects_every_fingerprint_and_delta_tamper(self) -> None:
        prior_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        prior_entries = [
            self._entry("a"),
            self._entry("b", text_fingerprint="2" * 64),
            self._entry("c", text_fingerprint="3" * 64),
        ]
        current_entries = [
            self._entry(
                "b",
                text_fingerprint="2" * 64,
                disposition="false-positive",
            ),
            self._entry("d", text_fingerprint="4" * 64),
        ]
        prior = self._snapshot(prior_entries, prior_documents, kind="bootstrap")
        current = self._bootstrap_refresh(prior, current_entries, current_documents)
        evidence = current["bootstrap_refresh_reviews"][0]["evidence"]
        fingerprint_fields = [
            field for field in evidence if field.endswith("_fingerprint")
        ]
        for field in fingerprint_fields:
            forged = deepcopy(current)
            value = forged["bootstrap_refresh_reviews"][0]["evidence"][field]
            forged["bootstrap_refresh_reviews"][0]["evidence"][field] = (
                "0" * 64 if value != "0" * 64 else "1" * 64
            )
            with self.subTest(fingerprint=field):
                _normalized, errors = self.module._validate_root_semantic_snapshot(
                    forged,
                    label="snapshot",
                    evaluation_date=date(2026, 7, 14),
                )
                self.assertTrue(errors, field)

        forged_origin = deepcopy(current)
        forged_origin["bootstrap_refresh_origin_state_fingerprint"] = "0" * 64
        _normalized, errors = self.module._validate_root_semantic_snapshot(
            forged_origin,
            label="snapshot",
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(errors)
        forged_count = deepcopy(current)
        forged_count["bootstrap_refresh_review_count"] += 1
        _normalized, errors = self.module._validate_root_semantic_snapshot(
            forged_count,
            label="snapshot",
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(errors)

        for field in ("added_candidate_ids", "removed_entries", "prior_overrides"):
            forged = deepcopy(current)
            forged["bootstrap_refresh_reviews"][0]["evidence"][field] = []
            with self.subTest(delta=field):
                _normalized, errors = self.module._validate_root_semantic_snapshot(
                    forged,
                    label="snapshot",
                    evaluation_date=date(2026, 7, 14),
                )
                self.assertTrue(errors, field)

    def test_bootstrap_refresh_chain_rejects_deletion_reorder_gap_and_first_observed(self) -> None:
        entries = [self._entry("a")]
        snapshots = [
            self._snapshot(entries, [self._document("source-0")], kind="bootstrap")
        ]
        for index in range(1, 4):
            snapshots.append(
                self._bootstrap_refresh(
                    snapshots[-1],
                    entries,
                    [self._document(f"source-{index}")],
                )
            )
        current = snapshots[-1]
        variants = {}
        deleted_first = deepcopy(current)
        deleted_first["bootstrap_refresh_reviews"] = deleted_first[
            "bootstrap_refresh_reviews"
        ][1:]
        variants["delete-first"] = deleted_first
        deleted_middle = deepcopy(current)
        del deleted_middle["bootstrap_refresh_reviews"][1]
        variants["delete-middle"] = deleted_middle
        deleted_all = deepcopy(current)
        deleted_all["bootstrap_refresh_reviews"] = []
        variants["delete-all"] = deleted_all
        deleted_all_recounted = deepcopy(snapshots[1])
        deleted_all_recounted["bootstrap_refresh_reviews"] = []
        deleted_all_recounted["bootstrap_refresh_review_count"] = 0
        variants["delete-only-review-and-recount"] = deleted_all_recounted
        reordered = deepcopy(current)
        reordered["bootstrap_refresh_reviews"][0:2] = reversed(
            reordered["bootstrap_refresh_reviews"][0:2]
        )
        variants["reorder"] = reordered
        gap = deepcopy(current)
        gap["bootstrap_refresh_reviews"][1]["evidence"][
            "prior_state_fingerprint"
        ] = "0" * 64
        variants["gap"] = gap
        for label, forged in variants.items():
            with self.subTest(label=label):
                _normalized, errors = self.module._validate_root_semantic_snapshot(
                    forged,
                    label="snapshot",
                    evaluation_date=date(2026, 7, 14),
                )
                self.assertTrue(errors, label)

        first_observed = deepcopy(current)
        first_observed["entries"][0]["first_observed"] = {
            "status": "known",
            "release_id": "forged",
            "released_on": "2026-07-14",
        }
        _normalized, errors = self.module._validate_root_semantic_snapshot(
            first_observed,
            label="snapshot",
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(any("first_observed" in item for item in errors), errors)

    def test_bootstrap_refresh_closed_schema_rejects_unknown_duplicate_and_overlap(self) -> None:
        prior_entries = [self._entry("a"), self._entry("b", text_fingerprint="2" * 64)]
        current_entries = [
            self._entry("b", text_fingerprint="2" * 64, disposition="false-positive"),
            self._entry("c", text_fingerprint="3" * 64),
        ]
        prior = self._snapshot(
            prior_entries, [self._document("old source")], kind="bootstrap"
        )
        current = self._bootstrap_refresh(
            prior, current_entries, [self._document("new source")]
        )
        variants = {}
        unknown_snapshot = deepcopy(current)
        unknown_snapshot["unknown"] = True
        variants["snapshot-unknown"] = unknown_snapshot
        unknown_review = deepcopy(current)
        unknown_review["bootstrap_refresh_reviews"][0]["unknown"] = True
        variants["review-unknown"] = unknown_review
        unknown_evidence = deepcopy(current)
        unknown_evidence["bootstrap_refresh_reviews"][0]["evidence"][
            "unknown"
        ] = True
        variants["evidence-unknown"] = unknown_evidence
        wrong_schema = deepcopy(current)
        wrong_schema["bootstrap_refresh_reviews"][0]["schema_version"] = 2
        variants["review-schema"] = wrong_schema
        duplicate_added = deepcopy(current)
        duplicate_added["bootstrap_refresh_reviews"][0]["evidence"][
            "added_candidate_ids"
        ] *= 2
        variants["duplicate-added"] = duplicate_added
        duplicate_removed = deepcopy(current)
        duplicate_removed["bootstrap_refresh_reviews"][0]["evidence"][
            "removed_entries"
        ] *= 2
        variants["duplicate-removed"] = duplicate_removed
        overlap = deepcopy(current)
        overlap["bootstrap_refresh_reviews"][0]["evidence"][
            "prior_overrides"
        ].append(deepcopy(current["entries"][1]))
        overlap["bootstrap_refresh_reviews"][0]["evidence"][
            "prior_overrides"
        ].sort(key=lambda item: item["candidate_id"])
        variants["overlap"] = overlap
        wrong_delta_type = deepcopy(current)
        wrong_delta_type["bootstrap_refresh_reviews"][0]["evidence"][
            "added_candidate_ids"
        ] = 1
        variants["wrong-delta-type"] = wrong_delta_type
        for label, forged in variants.items():
            with self.subTest(label=label):
                _normalized, errors = self.module._validate_root_semantic_snapshot(
                    forged,
                    label="snapshot",
                    evaluation_date=date(2026, 7, 14),
                )
                self.assertTrue(errors, label)

        malformed_lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": None,
            "current": wrong_delta_type,
        }
        evaluated = self.module._evaluate_root_semantic_lifecycle(
            malformed_lifecycle,
            current_entries,
            [self._document("new source")],
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual("invalid", evaluated["status"])
        self.assertFalse(evaluated["bootstrap_refresh_chain"]["valid"])

    def test_legacy_contract_is_fail_closed_except_exact_recorder_migration(self) -> None:
        documents = [self._document("legacy source")]
        current = self._snapshot([self._entry("a")], documents, kind="bootstrap")
        legacy_current = deepcopy(current)
        legacy_current["schema_version"] = (
            self.module.ROOT_SEMANTIC_LEGACY_SNAPSHOT_SCHEMA_VERSION
        )
        for field in (
            "bootstrap_refresh_reviews",
            "bootstrap_refresh_origin_state_fingerprint",
            "bootstrap_refresh_review_count",
        ):
            del legacy_current[field]
        legacy = {
            self.module.ROOT_SEMANTIC_DISPOSITION_KEY: {
                "schema_version": self.module.ROOT_SEMANTIC_LEGACY_DISPOSITION_SCHEMA_VERSION,
                "lifecycle": {
                    "schema_version": self.module.ROOT_SEMANTIC_LEGACY_LIFECYCLE_SCHEMA_VERSION,
                    "previous": None,
                    "current": legacy_current,
                },
                "entries": [],
            }
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "config") as raw:
            target = Path(raw) / "legacy.yaml"
            target.write_text(
                self._legacy_v2_config_text(legacy_current), encoding="utf-8"
            )
            expected_source_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
            with mock.patch.object(
                self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
            ):
                _strict, strict_errors = self.module._load_root_semantic_dispositions()
                migrated, source_schema, source_sha256, migration_errors = (
                    self.module._load_root_semantic_dispositions_for_recorder(
                        evaluation_date=date(2026, 7, 14)
                    )
                )
        self.assertTrue(strict_errors)
        self.assertEqual(
            self.module.ROOT_SEMANTIC_LEGACY_DISPOSITION_SCHEMA_VERSION,
            source_schema,
        )
        self.assertEqual(expected_source_sha256, source_sha256)
        self.assertEqual([], migration_errors)
        self.assertEqual(
            self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            migrated["schema_version"],
        )
        normalized, errors = self.module._validate_root_semantic_lifecycle(
            migrated["lifecycle"], evaluation_date=date(2026, 7, 14)
        )
        self.assertEqual([], errors)
        self.assertIsNotNone(normalized)

        malformed = deepcopy(legacy)
        malformed[self.module.ROOT_SEMANTIC_DISPOSITION_KEY]["lifecycle"][
            "current"
        ]["unknown"] = True
        with tempfile.TemporaryDirectory(dir=ROOT / "config") as raw:
            target = Path(raw) / "malformed.yaml"
            target.write_text(
                self._legacy_v2_config_text(
                    malformed[self.module.ROOT_SEMANTIC_DISPOSITION_KEY][
                        "lifecycle"
                    ]["current"]
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
            ):
                _contract, _schema, _digest, errors = (
                    self.module._load_root_semantic_dispositions_for_recorder(
                        evaluation_date=date(2026, 7, 14)
                    )
                )
        self.assertTrue(any("legacy schema must contain exactly" in item for item in errors))

    def test_schema3_bootstrap_chain_migrates_without_rewriting_evidence_and_appends(self) -> None:
        entry = self._entry("a")
        first = self._snapshot(
            [entry], [self._document("source-0")], kind="bootstrap"
        )
        second = self._bootstrap_refresh(
            first, [entry], [self._document("source-1")]
        )
        third = self._bootstrap_refresh(
            second, [entry], [self._document("source-2")]
        )
        raw_current = deepcopy(third)
        raw_current["schema_version"] = (
            self.module.ROOT_SEMANTIC_PREVIOUS_SNAPSHOT_SCHEMA_VERSION
        )
        historical_reviews = deepcopy(raw_current["bootstrap_refresh_reviews"])
        historical_origin = raw_current[
            "bootstrap_refresh_origin_state_fingerprint"
        ]
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_PREVIOUS_LIFECYCLE_SCHEMA_VERSION,
            "previous": None,
            "current": raw_current,
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "config") as raw:
            target = Path(raw) / "schema3.yaml"
            target.write_text(
                self._schema_config_text(
                    lifecycle,
                    root_schema_version=self.module.ROOT_SEMANTIC_PREVIOUS_DISPOSITION_SCHEMA_VERSION,
                    lifecycle_schema_version=self.module.ROOT_SEMANTIC_PREVIOUS_LIFECYCLE_SCHEMA_VERSION,
                ),
                encoding="utf-8",
            )
            expected_digest = hashlib.sha256(target.read_bytes()).hexdigest()
            with mock.patch.object(
                self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
            ):
                migrated, source_schema, digest, errors = (
                    self.module._load_root_semantic_dispositions_for_recorder(
                        evaluation_date=date(2026, 7, 14)
                    )
                )
        self.assertEqual([], errors)
        self.assertEqual(
            self.module.ROOT_SEMANTIC_PREVIOUS_DISPOSITION_SCHEMA_VERSION,
            source_schema,
        )
        self.assertEqual(expected_digest, digest)
        migrated_current = migrated["lifecycle"]["current"]
        self.assertEqual(
            self.module.ROOT_SEMANTIC_SNAPSHOT_SCHEMA_VERSION,
            migrated_current["schema_version"],
        )
        self.assertEqual(historical_origin, migrated_current["bootstrap_refresh_origin_state_fingerprint"])
        self.assertEqual(historical_reviews, migrated_current["bootstrap_refresh_reviews"])
        self.assertEqual(
            self.module._root_bootstrap_base_state_fingerprint(raw_current),
            self.module._root_bootstrap_base_state_fingerprint(migrated_current),
        )
        for review in historical_reviews:
            self.assertEqual(
                self.module._root_bootstrap_chained_state_fingerprint(
                    raw_current, review
                ),
                self.module._root_bootstrap_chained_state_fingerprint(
                    migrated_current, review
                ),
            )

        next_snapshot = self._snapshot(
            [entry],
            [self._document("source-3")],
            kind="bootstrap",
            prior=migrated_current,
            bootstrap_reviews=migrated_current["bootstrap_refresh_reviews"],
            bootstrap_refresh_origin_state_fingerprint=migrated_current[
                "bootstrap_refresh_origin_state_fingerprint"
            ],
        )
        appended = self.module._root_recorded_bootstrap_refresh_review(
            migrated_current,
            next_snapshot,
            reviewed_by="independent-bootstrap-reviewer",
            rationale="The migrated bootstrap chain tail and current source delta were independently reviewed before appending.",
        )
        self.assertEqual(
            historical_reviews[-1]["evidence"]["current_state_fingerprint"],
            appended["evidence"]["prior_state_fingerprint"],
        )
        next_snapshot["bootstrap_refresh_reviews"] = [*historical_reviews, appended]
        next_snapshot["bootstrap_refresh_review_count"] = len(
            next_snapshot["bootstrap_refresh_reviews"]
        )
        self.assertEqual(
            historical_reviews,
            next_snapshot["bootstrap_refresh_reviews"][:-1],
        )
        _normalized, append_errors = self.module._validate_root_semantic_snapshot(
            next_snapshot,
            label="migrated.appended",
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual([], append_errors)

    def test_schema3_migration_handles_both_lifecycle_positions(self) -> None:
        entry = self._entry("a")
        bootstrap = self._snapshot(
            [entry], [self._document("bootstrap-0")], kind="bootstrap"
        )
        bootstrap = self._bootstrap_refresh(
            bootstrap, [entry], [self._document("bootstrap-1")]
        )
        release_one = self._snapshot(
            [entry],
            [self._document("bootstrap-1")],
            kind="release",
            release_id="r1",
            released_on="2026-07-13",
            prior=bootstrap,
        )
        release_two = self._snapshot(
            [entry],
            [self._document("bootstrap-1")],
            kind="release",
            release_id="r2",
            released_on="2026-07-14",
            prior=release_one,
        )
        raw_bootstrap = deepcopy(bootstrap)
        raw_bootstrap["schema_version"] = 3
        raw_release_one = deepcopy(release_one)
        raw_release_one["schema_version"] = 3
        raw_release_two = deepcopy(release_two)
        raw_release_two["schema_version"] = 3
        cases = {
            "current-bootstrap": (None, raw_bootstrap),
            "previous-bootstrap": (raw_bootstrap, raw_release_one),
            "both-release": (raw_release_one, raw_release_two),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "config") as raw:
            for label, (previous, current) in cases.items():
                lifecycle = {
                    "schema_version": 3,
                    "previous": previous,
                    "current": current,
                }
                target = Path(raw) / f"{label}.yaml"
                target.write_text(
                    self._schema_config_text(
                        lifecycle,
                        root_schema_version=5,
                        lifecycle_schema_version=3,
                    ),
                    encoding="utf-8",
                )
                with self.subTest(label=label), mock.patch.object(
                    self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
                ):
                    migrated, _schema, _digest, errors = (
                        self.module._load_root_semantic_dispositions_for_recorder(
                            evaluation_date=date(2026, 7, 14)
                        )
                    )
                self.assertEqual([], errors, label)
                self.assertEqual(4, migrated["lifecycle"]["current"]["schema_version"])
                if previous is not None:
                    self.assertEqual(4, migrated["lifecycle"]["previous"]["schema_version"])

    def test_recorder_loader_rejects_mixed_or_unknown_schema_triples(self) -> None:
        snapshot = self._snapshot(
            [self._entry("a")], [self._document("source")], kind="bootstrap"
        )
        raw_snapshot = deepcopy(snapshot)
        raw_snapshot["schema_version"] = 3
        cases = (
            (5, 2, raw_snapshot),
            (4, 3, raw_snapshot),
            (6, 4, raw_snapshot),
            (7, 4, snapshot),
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "config") as raw:
            for root_schema, lifecycle_schema, current in cases:
                lifecycle = {
                    "schema_version": lifecycle_schema,
                    "previous": None,
                    "current": current,
                }
                target = Path(raw) / f"{root_schema}-{lifecycle_schema}.yaml"
                target.write_text(
                    self._schema_config_text(
                        lifecycle,
                        root_schema_version=root_schema,
                        lifecycle_schema_version=lifecycle_schema,
                    ),
                    encoding="utf-8",
                )
                with self.subTest(
                    root=root_schema, lifecycle=lifecycle_schema
                ), mock.patch.object(
                    self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
                ):
                    _contract, _schema, _digest, errors = (
                        self.module._load_root_semantic_dispositions_for_recorder(
                            evaluation_date=date(2026, 7, 14)
                        )
                    )
                self.assertTrue(errors)

    def test_schema3_migration_rejects_tampered_bootstrap_chain_before_migration(self) -> None:
        entry = self._entry("a")
        snapshots = [
            self._snapshot([entry], [self._document("source-0")], kind="bootstrap")
        ]
        for index in range(1, 3):
            snapshots.append(
                self._bootstrap_refresh(
                    snapshots[-1],
                    [entry],
                    [self._document(f"source-{index}")],
                )
            )
        raw_snapshot = deepcopy(snapshots[-1])
        raw_snapshot["schema_version"] = 3
        variants: dict[str, dict] = {}
        origin = deepcopy(raw_snapshot)
        origin["bootstrap_refresh_origin_state_fingerprint"] = "f" * 64
        variants["origin"] = origin
        count = deepcopy(raw_snapshot)
        count["bootstrap_refresh_review_count"] += 1
        variants["count"] = count
        for field in (
            "prior_state_fingerprint",
            "current_state_fingerprint",
            "prior_document_fingerprint",
            "current_document_fingerprint",
            "prior_detector_fingerprint",
            "current_detector_fingerprint",
            "prior_candidate_fingerprint",
            "current_candidate_fingerprint",
            "prior_disposition_fingerprint",
            "current_disposition_fingerprint",
        ):
            forged = deepcopy(raw_snapshot)
            forged["bootstrap_refresh_reviews"][0]["evidence"][field] = "f" * 64
            variants[field] = forged
        for field in ("added_candidate_ids", "removed_entries", "prior_overrides"):
            forged = deepcopy(raw_snapshot)
            forged["bootstrap_refresh_reviews"][0]["evidence"][field] = [
                deepcopy(raw_snapshot["entries"][0])
            ] if field != "added_candidate_ids" else ["f" * 64]
            variants[field] = forged
        reordered = deepcopy(raw_snapshot)
        reordered["bootstrap_refresh_reviews"].reverse()
        variants["reviewer-order"] = reordered
        deleted = deepcopy(raw_snapshot)
        del deleted["bootstrap_refresh_reviews"][0]
        variants["deletion"] = deleted
        gap = deepcopy(raw_snapshot)
        gap["bootstrap_refresh_reviews"][1]["evidence"]["prior_state_fingerprint"] = "f" * 64
        variants["chain-gap"] = gap
        unknown = deepcopy(raw_snapshot)
        unknown["unknown"] = True
        variants["unknown-field"] = unknown
        future_review_schema = deepcopy(raw_snapshot)
        future_review_schema["bootstrap_refresh_reviews"][0]["schema_version"] = 2
        variants["review-schema-2"] = future_review_schema

        with tempfile.TemporaryDirectory(dir=ROOT / "config") as raw:
            for label, forged in variants.items():
                lifecycle = {"schema_version": 3, "previous": None, "current": forged}
                target = Path(raw) / f"{label}.yaml"
                content = self._schema_config_text(
                    lifecycle,
                    root_schema_version=5,
                    lifecycle_schema_version=3,
                )
                if label == "unknown-field":
                    content = content.replace(
                        "      kind:", "      unknown: true\n      kind:", 1
                    )
                target.write_text(content, encoding="utf-8")
                with self.subTest(label=label), mock.patch.object(
                    self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
                ):
                    migrated, _schema, _digest, errors = (
                        self.module._load_root_semantic_dispositions_for_recorder(
                            evaluation_date=date(2026, 7, 14)
                        )
                    )
                self.assertTrue(errors, label)
                self.assertIsNone(migrated["lifecycle"]["current"], label)

            current_release = self._snapshot(
                [entry],
                [self._document("source-2")],
                kind="release",
                release_id="r1",
                released_on="2026-07-14",
                prior=snapshots[-1],
            )
            current_release["schema_version"] = 3
            lifecycle = {
                "schema_version": 3,
                "previous": origin,
                "current": current_release,
            }
            target = Path(raw) / "tampered-previous.yaml"
            target.write_text(
                self._schema_config_text(
                    lifecycle,
                    root_schema_version=5,
                    lifecycle_schema_version=3,
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                self.module, "SKILL_CONTENT_EXCEPTIONS_FILE", target
            ):
                migrated, _schema, _digest, errors = (
                    self.module._load_root_semantic_dispositions_for_recorder(
                        evaluation_date=date(2026, 7, 14)
                    )
                )
            self.assertTrue(errors)
            self.assertIsNone(migrated["lifecycle"]["previous"])

    def test_comparable_add_remove_and_rollover_preserve_first_observed(self) -> None:
        documents = [self._document("stable source")]
        first = self._entry("a")
        second = self._entry("b", text_fingerprint="2" * 64)
        third = self._entry("c", text_fingerprint="3" * 64)
        bootstrap = self._snapshot([first], documents, kind="bootstrap")
        release_one = self._snapshot(
            [first, second],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-13",
            prior=bootstrap,
        )
        comparison, errors = self.module._root_lifecycle_comparison(
            bootstrap,
            release_one,
            self.module._root_document_fingerprints(documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, comparison["added_count"])
        self.assertEqual(0, comparison["removed_count"])
        self.assertEqual("unknown-pre-baseline", release_one["entries"][0]["first_observed"]["status"])
        self.assertEqual("r1", release_one["entries"][1]["first_observed"]["release_id"])

        release_two = self._snapshot(
            [first, second, third],
            documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-14",
            prior=release_one,
        )
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": release_one,
            "current": release_two,
        }
        _normalized, lifecycle_errors = self.module._validate_root_semantic_lifecycle(
            lifecycle, evaluation_date=date(2026, 7, 14)
        )
        self.assertEqual([], lifecycle_errors)
        first_seen = {
            entry["candidate_id"]: entry["first_observed"] for entry in release_two["entries"]
        }
        self.assertEqual("unknown-pre-baseline", first_seen[first["candidate_id"]]["status"])
        self.assertEqual("r1", first_seen[second["candidate_id"]]["release_id"])
        self.assertEqual("r2", first_seen[third["candidate_id"]]["release_id"])

    def test_source_detector_and_dual_change_classification(self) -> None:
        prior_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old = self._entry("a")
        replacement = self._entry("b", text_fingerprint="2" * 64)
        previous = self._snapshot(
            [old],
            prior_documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-12",
        )
        current = self._snapshot(
            [replacement],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )
        source, errors = self.module._root_lifecycle_comparison(
            previous,
            current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, source["source_rewrite_count"])
        self.assertEqual(1, source["source_replacement_count"])
        self.assertEqual(0, source["new_disposition_count"])

        detector_previous = deepcopy(previous)
        detector_previous["detector_fingerprint"] = "0" * 64
        detector_current = self._snapshot(
            [],
            prior_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=detector_previous,
        )
        detector, errors = self.module._root_lifecycle_comparison(
            detector_previous,
            detector_current,
            self.module._root_document_fingerprints(prior_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, detector["detector_change_removal_count"])
        self.assertEqual(0, detector["detector_improvement_count"])
        self.assertEqual(1, detector["unclassified_count"])
        self.assertEqual(
            "unreviewed-detector-change-removal",
            detector["unclassified"][0]["reason"],
        )

        review = self._record_reviews(
            detector_previous,
            detector_current,
            prior_documents,
            change_reviews=[
                (
                    old["candidate_id"],
                    "changeforge-maintainers",
                    "Current unchanged source proves this removal came from the reviewed detector refinement.",
                )
            ],
        )[0]
        reviewed_current = deepcopy(detector_current)
        reviewed_current["change_reviews"] = [review]
        reviewed, errors = self.module._root_lifecycle_comparison(
            detector_previous,
            reviewed_current,
            self.module._root_document_fingerprints(prior_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, reviewed["detector_improvement_count"])
        self.assertEqual(0, reviewed["unclassified_count"])

        dual, errors = self.module._root_lifecycle_comparison(
            detector_previous,
            detector_current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, dual["unclassified_count"])
        self.assertEqual("source-and-detector-changed", dual["unclassified"][0]["reason"])

    def test_dual_replacement_review_allows_one_to_many_selected_split(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old = self._entry("a")
        replacements = [
            self._entry("b", text_fingerprint="2" * 64),
            self._entry("c", text_fingerprint="3" * 64),
        ]
        previous, current = self._dual_snapshots(
            [old], replacements, previous_documents, current_documents
        )
        reviews = self._record_reviews(
            previous,
            current,
            current_documents,
            replacement_reviews=[
                (
                    old["candidate_id"],
                    f"{replacements[1]['candidate_id']},{replacements[0]['candidate_id']}",
                    "changeforge-maintainers",
                    "The changed source and detector produce exactly these same-lineage replacements.",
                )
            ],
        )
        reviewed_current = deepcopy(current)
        reviewed_current["change_reviews"] = reviews
        comparison, errors = self.module._root_lifecycle_comparison(
            previous,
            reviewed_current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(0, comparison["unclassified_count"])
        self.assertEqual(1, comparison["source_rewrite_count"])
        self.assertEqual(1, comparison["source_replacement_count"])
        self.assertEqual(0, comparison["new_disposition_count"])
        rewrite = comparison["source_rewrites"][0]
        self.assertEqual("source-and-detector-replacement", rewrite["classification"])
        self.assertEqual("changeforge-maintainers", rewrite["reviewed_by"])
        evidence = reviews[0]["evidence"]
        self.assertEqual(
            sorted(item["candidate_id"] for item in replacements),
            evidence["replacement_candidate_ids"],
        )
        self.assertEqual(previous["detector_fingerprint"], evidence["prior_detector_fingerprint"])
        self.assertEqual(current["detector_fingerprint"], evidence["current_detector_fingerprint"])

    def test_dual_replacements_partition_selected_and_independent_additions(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old_entries = [self._entry(candidate) for candidate in ("a", "b", "c")]
        additions = [
            self._entry(candidate, text_fingerprint=str(index) * 64)
            for index, candidate in enumerate(("d", "e", "f", "1", "2"), start=2)
        ]
        previous, current = self._dual_snapshots(
            old_entries, additions, previous_documents, current_documents
        )
        for index, entry in enumerate(previous["entries"]):
            entry["first_observed"] = {
                "status": "known",
                "release_id": f"origin-{index}",
                "released_on": f"2026-07-{9 + index:02d}",
            }
        selected_pairs = list(zip(old_entries, additions[:3], strict=True))
        reviews = self._record_reviews(
            previous,
            current,
            current_documents,
            replacement_reviews=[
                (
                    old["candidate_id"],
                    replacement["candidate_id"],
                    "changeforge-maintainers",
                    f"Selected replacement {index} preserves only its reviewed prior lineage.",
                )
                for index, (old, replacement) in enumerate(selected_pairs, start=1)
            ],
        )
        reviewed_current = self._snapshot(
            additions,
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=reviews,
        )
        comparison, errors = self.module._root_lifecycle_comparison(
            previous,
            reviewed_current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(3, comparison["source_rewrite_count"])
        self.assertEqual(3, comparison["source_replacement_count"])
        self.assertEqual(2, comparison["new_disposition_count"])
        current_by_id = {
            entry["candidate_id"]: entry for entry in reviewed_current["entries"]
        }
        previous_by_id = {
            entry["candidate_id"]: entry for entry in previous["entries"]
        }
        for old, replacement in selected_pairs:
            self.assertEqual(
                previous_by_id[old["candidate_id"]]["first_observed"],
                current_by_id[replacement["candidate_id"]]["first_observed"],
            )
        for independent in additions[3:]:
            self.assertEqual(
                "r2",
                current_by_id[independent["candidate_id"]]["first_observed"][
                    "release_id"
                ],
            )

    def test_dual_removal_reviews_cover_changed_and_removed_documents(self) -> None:
        old = self._entry("a")
        previous_documents = [self._document("old source")]
        for current_documents in (
            [self._document("rewritten source")],
            [],
        ):
            with self.subTest(document_removed=not current_documents):
                previous, current = self._dual_snapshots(
                    [old], [], previous_documents, current_documents
                )
                reviews = self._record_reviews(
                    previous,
                    current,
                    current_documents,
                    removal_reviews=[
                        (
                            old["candidate_id"],
                            "changeforge-maintainers",
                            "The source change removes this lineage while the detector also changed.",
                        )
                    ],
                )
                reviewed_current = deepcopy(current)
                reviewed_current["change_reviews"] = reviews
                comparison, errors = self.module._root_lifecycle_comparison(
                    previous,
                    reviewed_current,
                    self.module._root_document_fingerprints(current_documents),
                )
                self.assertEqual([], errors)
                self.assertEqual(0, comparison["unclassified_count"])
                self.assertEqual(
                    "source-and-detector-removal",
                    comparison["source_rewrites"][0]["classification"],
                )
                self.assertEqual([], reviews[0]["evidence"]["replacement_candidate_ids"])
                self.assertEqual(
                    None if not current_documents else self.module._root_document_fingerprints(
                        current_documents
                    )[old["path"] + "#body"],
                    reviews[0]["evidence"]["current_document_fingerprint"],
                )

    def test_dual_review_accepts_subset_and_removal_with_nonempty_pool(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [
            self._document("new source"),
            self._document("other source", path="src/other/SKILL.md"),
        ]
        old = self._entry("a")
        same_lineage = [
            self._entry("b", text_fingerprint="2" * 64),
            self._entry("c", text_fingerprint="3" * 64),
        ]
        cross_lineage = self._entry(
            "d", text_fingerprint="4" * 64, path="src/other/SKILL.md"
        )
        previous, current = self._dual_snapshots(
            [old],
            [*same_lineage, cross_lineage],
            previous_documents,
            current_documents,
        )
        rationale = "The selected subset is reviewed against source and detector changes."
        subset_reviews = self._record_reviews(
            previous,
            current,
            current_documents,
            replacement_reviews=[
                (
                    old["candidate_id"],
                    same_lineage[0]["candidate_id"],
                    "changeforge-maintainers",
                    rationale,
                )
            ],
        )
        subset_current = self._snapshot(
            [*same_lineage, cross_lineage],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=subset_reviews,
        )
        subset, errors = self.module._root_lifecycle_comparison(
            previous,
            subset_current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(2, subset["new_disposition_count"])
        self.assertEqual(
            [same_lineage[0]["candidate_id"]],
            subset["source_rewrites"][0]["replacement_candidate_ids"],
        )

        removal_reviews = self._record_reviews(
            previous,
            current,
            current_documents,
            removal_reviews=[
                (old["candidate_id"], "changeforge-maintainers", rationale)
            ],
        )
        removal_current = self._snapshot(
            [*same_lineage, cross_lineage],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=removal_reviews,
        )
        removal, errors = self.module._root_lifecycle_comparison(
            previous,
            removal_current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(3, removal["new_disposition_count"])
        self.assertEqual(
            "source-and-detector-removal",
            removal["source_rewrites"][0]["classification"],
        )
        self.assertEqual(
            [], removal_reviews[0]["evidence"]["replacement_candidate_ids"]
        )

    def test_dual_review_rejects_cross_lineage_and_non_added_selection(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [
            self._document("new source"),
            self._document("other source", path="src/other/SKILL.md"),
        ]
        old = self._entry("a")
        same_lineage = self._entry("b", text_fingerprint="2" * 64)
        cross_lineage = self._entry(
            "c", text_fingerprint="3" * 64, path="src/other/SKILL.md"
        )
        previous, current = self._dual_snapshots(
            [old],
            [same_lineage, cross_lineage],
            previous_documents,
            current_documents,
        )
        for selected in (cross_lineage["candidate_id"], "f" * 64):
            with self.subTest(selected=selected), self.assertRaisesRegex(
                self.module.ValidationProblem, "current same-lineage additions"
            ):
                self._record_reviews(
                    previous,
                    current,
                    current_documents,
                    replacement_reviews=[
                        (
                            old["candidate_id"],
                            selected,
                            "changeforge-maintainers",
                            "The selected replacement must exist in the eligible lineage pool.",
                        )
                    ],
                )

    def test_dual_review_rejects_duplicates_generic_rationale_and_disposition_drift(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old = self._entry("a")
        replacement = self._entry("b", text_fingerprint="2" * 64)
        previous, current = self._dual_snapshots(
            [old], [replacement], previous_documents, current_documents
        )
        replacement_request = (
            old["candidate_id"],
            replacement["candidate_id"],
            "changeforge-maintainers",
            "The exact same-lineage replacement is accountable and source-backed.",
        )
        with self.assertRaisesRegex(self.module.ValidationProblem, "duplicate"):
            self._record_reviews(
                previous,
                current,
                current_documents,
                replacement_reviews=[replacement_request],
                removal_reviews=[
                    (
                        old["candidate_id"],
                        "changeforge-maintainers",
                        "The exact removal is separately reviewed and source-backed.",
                    )
                ],
            )
        with self.assertRaisesRegex(self.module.ValidationProblem, "generic"):
            self._record_reviews(
                previous,
                current,
                current_documents,
                replacement_reviews=[
                    (
                        old["candidate_id"],
                        replacement["candidate_id"],
                        "changeforge-maintainers",
                        "approved",
                    )
                ],
            )
        for replacement_csv, expected in (
            ("", "non-empty"),
            (
                f"{replacement['candidate_id']},{replacement['candidate_id']}",
                "duplicate replacement IDs",
            ),
        ):
            with self.subTest(replacement_csv=replacement_csv):
                with self.assertRaisesRegex(self.module.ValidationProblem, expected):
                    self._record_reviews(
                        previous,
                        current,
                        current_documents,
                        replacement_reviews=[
                            (
                                old["candidate_id"],
                                replacement_csv,
                                "changeforge-maintainers",
                                "The exact replacement identifiers are source-backed and accountable.",
                            )
                        ],
                    )

        drifted = self._entry(
            "b", text_fingerprint="2" * 64, disposition="false-positive"
        )
        drift_previous, drift_current = self._dual_snapshots(
            [old], [drifted], previous_documents, current_documents
        )
        with self.assertRaisesRegex(
            self.module.ValidationProblem, "selected dispositions must match"
        ):
            self._record_reviews(
                drift_previous,
                drift_current,
                current_documents,
                replacement_reviews=[
                    (
                        old["candidate_id"],
                        drifted["candidate_id"],
                        "changeforge-maintainers",
                        "The replacement disposition is reviewed against the prior candidate.",
                    )
                ],
            )
        drift_comparison, errors = self.module._root_lifecycle_comparison(
            drift_previous,
            drift_current,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, drift_comparison["new_disposition_count"])
        self.assertEqual(
            "source-and-detector-changed",
            drift_comparison["unclassified"][0]["reason"],
        )

    def test_dual_review_rejects_duplicate_selected_candidate_across_priors(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old_entries = [self._entry("a"), self._entry("b")]
        replacement = self._entry("c", text_fingerprint="2" * 64)
        previous, current = self._dual_snapshots(
            old_entries,
            [replacement],
            previous_documents,
            current_documents,
        )
        with self.assertRaisesRegex(
            self.module.ValidationProblem, "cannot bind multiple prior candidates"
        ):
            self._record_reviews(
                previous,
                current,
                current_documents,
                replacement_reviews=[
                    (
                        old["candidate_id"],
                        replacement["candidate_id"],
                        "changeforge-maintainers",
                        f"Prior {index} explicitly selects this replacement candidate.",
                    )
                    for index, old in enumerate(old_entries, start=1)
                ],
            )

    def test_lifecycle_rejects_implicit_many_prior_merge(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old_entries = [self._entry("a"), self._entry("b")]
        replacement = self._entry("c", text_fingerprint="2" * 64)
        previous, current = self._dual_snapshots(
            old_entries,
            [replacement],
            previous_documents,
            current_documents,
        )
        fingerprints = self.module._root_document_fingerprints(current_documents)
        previous_by_id = {
            entry["candidate_id"]: entry for entry in previous["entries"]
        }
        reviews = [
            {
                "prior_candidate_id": old["candidate_id"],
                "classification": "source-and-detector-replacement",
                "reviewed_by": "changeforge-maintainers",
                "rationale": f"Prior {index} claims the same candidate as a replacement.",
                "evidence": self.module._root_change_review_evidence(
                    previous,
                    current,
                    fingerprints,
                    previous_by_id[old["candidate_id"]],
                    [replacement["candidate_id"]],
                ),
            }
            for index, old in enumerate(old_entries, start=1)
        ]
        forged_current = self._snapshot(
            [replacement],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=reviews,
        )
        _normalized, errors = self.module._validate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": forged_current,
            },
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(
            any("cannot bind multiple prior candidates" in item for item in errors),
            errors,
        )

    def test_source_only_ambiguity_reviews_assign_one_owner_and_one_removal(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        first = self._entry("a")
        second = self._entry("b", text_fingerprint="2" * 64)
        replacement = self._entry("c", text_fingerprint="3" * 64)
        previous = self._snapshot(
            [first, second],
            previous_documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-12",
        )
        provisional = self._snapshot(
            [replacement],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )
        comparison, errors = self.module._root_lifecycle_comparison(
            previous,
            provisional,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(2, comparison["unclassified_count"])

        reviews = self._record_reviews(
            previous,
            provisional,
            current_documents,
            source_replacement_reviews=[
                (
                    first["candidate_id"],
                    replacement["candidate_id"],
                    "independent-source-reviewer",
                    "The current source candidate exclusively succeeds the first prior candidate under the reviewed split.",
                )
            ],
            source_removal_reviews=[
                (
                    second["candidate_id"],
                    "independent-source-reviewer",
                    "The second prior candidate was removed by the reviewed source split and owns no current successor.",
                )
            ],
        )
        self.assertEqual(
            ["source-replacement", "source-removal"],
            [review["classification"] for review in reviews],
        )
        current = self._snapshot(
            [replacement],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=reviews,
        )
        evaluated = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": current,
            },
            [replacement],
            current_documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual([], evaluated["errors"])
        self.assertEqual("release-current", evaluated["status"])
        self.assertEqual(0, evaluated["comparison"]["unclassified_count"])
        self.assertEqual(2, evaluated["comparison"]["source_rewrite_count"])
        self.assertEqual(1, evaluated["comparison"]["source_replacement_count"])
        self.assertEqual(
            previous["entries"][0]["first_observed"],
            current["entries"][0]["first_observed"],
        )
        removal = next(
            review
            for review in reviews
            if review["classification"] == "source-removal"
        )
        self.assertEqual([], removal["evidence"]["replacement_candidate_ids"])

    def test_current_r7_source_reviews_produce_expected_r8_comparison_without_writing(self) -> None:
        replacement_prior = "0aca75c66bb335710883f0006a784f34247a7790b4b3878a447c31a687b99b52"
        removed_prior = "69070ff4063b409289c61ff9dec3c30b70b289647dc094bf55c5d1a2f46089e0"
        successor = "24cba4fb951adedce60a07a7c67130f4f5406c0388a3db4b491af1c47e69674a"
        first = self._entry("a", path="src/example-0/SKILL.md")
        first["candidate_id"] = replacement_prior
        second = self._entry(
            "b", text_fingerprint="2" * 64, path="src/example-0/SKILL.md"
        )
        second["candidate_id"] = removed_prior
        prior_entries = [first, second]
        for index in range(1, 5):
            entry = self._entry("d", path=f"src/example-{index}/SKILL.md")
            entry["candidate_id"] = hashlib.sha256(
                f"prior-{index}".encode("utf-8")
            ).hexdigest()
            prior_entries.append(entry)
        replacement = self._entry(
            "c", text_fingerprint="3" * 64, path="src/example-0/SKILL.md"
        )
        replacement["candidate_id"] = successor
        automatic_replacement = self._entry(
            "e", path="src/example-1/SKILL.md"
        )
        automatic_replacement["candidate_id"] = hashlib.sha256(
            b"automatic-replacement"
        ).hexdigest()
        independent_entries = []
        for index in range(6):
            entry = self._entry(
                "f", path=f"src/independent-{index}/SKILL.md"
            )
            entry["candidate_id"] = hashlib.sha256(
                f"independent-{index}".encode("utf-8")
            ).hexdigest()
            independent_entries.append(entry)
        entries = [replacement, automatic_replacement, *independent_entries]
        previous_documents = [
            self._document("old source", path=f"src/example-{index}/SKILL.md")
            for index in range(5)
        ]
        documents = [
            self._document("new source", path=f"src/example-{index}/SKILL.md")
            for index in range(5)
        ] + [
            self._document("independent source", path=f"src/independent-{index}/SKILL.md")
            for index in range(6)
        ]
        previous = self._snapshot(
            prior_entries,
            previous_documents,
            kind="release",
            release_id="r7-fixture",
            released_on="2026-07-18",
        )
        fingerprints = self.module._root_document_fingerprints(documents)
        provisional = self.module._root_semantic_snapshot(
            entries,
            fingerprints,
            kind="release",
            release_id="r8-fixture",
            released_on="2026-07-20",
            prior=previous,
        )
        comparison, comparison_errors = self.module._root_lifecycle_comparison(
            previous, provisional, fingerprints
        )
        self.assertEqual([], comparison_errors)
        reviews = self.module._root_recorded_change_reviews(
            [],
            comparison,
            previous=previous,
            current=provisional,
            current_document_fingerprints=fingerprints,
            source_replacement_reviews=[
                (
                    replacement_prior,
                    successor,
                    "independent-source-reviewer",
                    "The current one-mode role candidate exclusively succeeds the prior one-mode role candidate under the reviewed source split.",
                )
            ],
            source_removal_reviews=[
                (
                    removed_prior,
                    "independent-source-reviewer",
                    "The prior combined mode and reference decision rule was removed by the reviewed source split and owns no current successor.",
                )
            ],
        )
        current = self.module._root_semantic_snapshot(
            entries,
            fingerprints,
            kind="release",
            release_id="r8-fixture",
            released_on="2026-07-20",
            prior=previous,
            change_reviews=reviews,
        )
        evaluated = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": current,
            },
            entries,
            documents,
            evaluation_date=date(2026, 7, 21),
        )
        self.assertEqual([], evaluated["errors"])
        self.assertEqual(
            {
                "added_count": 8,
                "removed_count": 6,
                "new_disposition_count": 6,
                "source_rewrite_count": 6,
                "source_replacement_count": 2,
                "unclassified_count": 0,
            },
            {
                key: evaluated["comparison"][key]
                for key in (
                    "added_count",
                    "removed_count",
                    "new_disposition_count",
                    "source_rewrite_count",
                    "source_replacement_count",
                    "unclassified_count",
                )
            },
        )
        current_by_id = {
            entry["candidate_id"]: entry for entry in current["entries"]
        }
        previous_by_id = {
            entry["candidate_id"]: entry for entry in previous["entries"]
        }
        self.assertEqual(
            previous_by_id[replacement_prior]["first_observed"],
            current_by_id[successor]["first_observed"],
        )
        self.assertEqual("valid-contextual-rule", current_by_id[successor]["disposition"])
        self.assertEqual(
            previous["detector_fingerprint"], current["detector_fingerprint"]
        )

    def test_source_only_ambiguity_reviews_reject_partial_duplicate_and_invalid_inputs(self) -> None:
        old_documents = [self._document("old source")]
        new_documents = [self._document("new source")]
        first = self._entry("a")
        second = self._entry("b", text_fingerprint="2" * 64)
        replacement = self._entry("c", text_fingerprint="3" * 64)
        previous = self._snapshot(
            [first, second],
            old_documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-12",
        )
        current = self._snapshot(
            [replacement],
            new_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )
        replacement_review = (
            first["candidate_id"],
            replacement["candidate_id"],
            "independent-source-reviewer",
            "The reviewed source split assigns this current successor to the first prior candidate only.",
        )
        with self.assertRaisesRegex(
            self.module.ValidationProblem, "adjudicate every eligible prior"
        ):
            self._record_reviews(
                previous,
                current,
                new_documents,
                source_replacement_reviews=[replacement_review],
            )
        with self.assertRaisesRegex(
            self.module.ValidationProblem, "cannot bind multiple prior"
        ):
            self._record_reviews(
                previous,
                current,
                new_documents,
                source_replacement_reviews=[
                    replacement_review,
                    (
                        second["candidate_id"],
                        replacement["candidate_id"],
                        "independent-source-reviewer",
                        "The second prior incorrectly claims the already selected current successor.",
                    ),
                ],
            )
        with self.assertRaisesRegex(
            self.module.ValidationProblem, "lowercase sha256"
        ):
            self._record_reviews(
                previous,
                current,
                new_documents,
                source_replacement_reviews=[
                    (
                        first["candidate_id"],
                        "not-a-candidate",
                        "independent-source-reviewer",
                        "The malformed successor must be rejected before evidence construction.",
                    )
                ],
            )
        with self.assertRaisesRegex(
            self.module.ValidationProblem, "same-lineage ambiguity additions"
        ):
            self._record_reviews(
                previous,
                current,
                new_documents,
                source_replacement_reviews=[
                    (
                        first["candidate_id"],
                        first["candidate_id"],
                        "independent-source-reviewer",
                        "A prior candidate that is not a current addition cannot be selected as its own successor.",
                    )
                ],
            )

        unchanged_current = self._snapshot(
            [replacement],
            old_documents,
            kind="release",
            release_id="r2-unchanged",
            released_on="2026-07-13",
            prior=previous,
        )
        with self.assertRaisesRegex(self.module.ValidationProblem, "unused source"):
            self._record_reviews(
                previous,
                unchanged_current,
                old_documents,
                source_replacement_reviews=[replacement_review],
            )

        cross_lineage = self._entry(
            "c", text_fingerprint="3" * 64, path="src/other/SKILL.md"
        )
        cross_documents = [
            self._document("new source"),
            self._document("other source", path="src/other/SKILL.md"),
        ]
        cross_current = self._snapshot(
            [cross_lineage],
            cross_documents,
            kind="release",
            release_id="r2-cross",
            released_on="2026-07-13",
            prior=previous,
        )
        with self.assertRaisesRegex(self.module.ValidationProblem, "unused source"):
            self._record_reviews(
                previous,
                cross_current,
                cross_documents,
                source_replacement_reviews=[replacement_review],
            )

        with self.assertRaisesRegex(
            self.module.ValidationProblem, "unused root lifecycle change review"
        ):
            self._record_reviews(
                previous,
                current,
                new_documents,
                change_reviews=[
                    (
                        first["candidate_id"],
                        "independent-source-reviewer",
                        "A source-only ambiguity cannot be mislabeled as a generic detector or disposition review.",
                    )
                ],
            )

        detector_changed = deepcopy(current)
        detector_changed["detector_fingerprint"] = "f" * 64
        with self.assertRaisesRegex(self.module.ValidationProblem, "unused source"):
            self._record_reviews(
                previous,
                detector_changed,
                new_documents,
                source_replacement_reviews=[replacement_review],
                source_removal_reviews=[
                    (
                        second["candidate_id"],
                        "independent-source-reviewer",
                        "The second prior removal cannot use a source-only review after detector drift.",
                    )
                ],
            )

        drifted = self._entry(
            "c", text_fingerprint="3" * 64, disposition="false-positive"
        )
        drifted_current = self._snapshot(
            [drifted],
            new_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )
        with self.assertRaisesRegex(self.module.ValidationProblem, "unused source"):
            self._record_reviews(
                previous,
                drifted_current,
                new_documents,
                source_replacement_reviews=[replacement_review],
            )

    def test_source_only_review_evidence_is_derived_and_forgery_fails(self) -> None:
        old_documents = [self._document("old source")]
        new_documents = [self._document("new source")]
        first = self._entry("a")
        second = self._entry("b", text_fingerprint="2" * 64)
        replacement = self._entry("c", text_fingerprint="3" * 64)
        previous = self._snapshot(
            [first, second], old_documents, kind="release", release_id="r1", released_on="2026-07-12"
        )
        provisional = self._snapshot(
            [replacement], new_documents, kind="release", release_id="r2", released_on="2026-07-13", prior=previous
        )
        reviews = self._record_reviews(
            previous,
            provisional,
            new_documents,
            source_replacement_reviews=[
                (
                    first["candidate_id"], replacement["candidate_id"], "independent-source-reviewer",
                    "The first prior owns the reviewed current successor after the source split.",
                )
            ],
            source_removal_reviews=[
                (
                    second["candidate_id"], "independent-source-reviewer",
                    "The second prior was independently reviewed as removed without a successor.",
                )
            ],
        )
        forged_reviews = deepcopy(reviews)
        forged_reviews[0]["evidence"]["current_detector_fingerprint"] = "f" * 64
        forged = self._snapshot(
            [replacement], new_documents, kind="release", release_id="r2", released_on="2026-07-13", prior=previous, reviews=forged_reviews
        )
        evaluated = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": forged,
            },
            [replacement],
            new_documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(
            any("canonical recomputation" in error for error in evaluated["errors"]),
            evaluated["errors"],
        )

    def test_unselected_addition_cannot_inherit_replacement_provenance(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old = self._entry("a")
        selected = self._entry("b", text_fingerprint="2" * 64)
        independent = self._entry("c", text_fingerprint="3" * 64)
        previous, current = self._dual_snapshots(
            [old],
            [selected, independent],
            previous_documents,
            current_documents,
        )
        reviews = self._record_reviews(
            previous,
            current,
            current_documents,
            replacement_reviews=[
                (
                    old["candidate_id"],
                    selected["candidate_id"],
                    "changeforge-maintainers",
                    "Only the selected candidate inherits the prior disposition provenance.",
                )
            ],
        )
        reviewed_current = self._snapshot(
            [selected, independent],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=reviews,
        )
        prior_first_observed = previous["entries"][0]["first_observed"]
        independent_entry = next(
            entry
            for entry in reviewed_current["entries"]
            if entry["candidate_id"] == independent["candidate_id"]
        )
        independent_entry["first_observed"] = deepcopy(prior_first_observed)
        _normalized, errors = self.module._validate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": reviewed_current,
            },
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(
            any("must start at current release" in item for item in errors), errors
        )

    def test_review_evidence_is_recomputed_and_later_drift_fails_closed(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        drifted_documents = [self._document("later drift")]
        old = self._entry("a")
        replacement = self._entry("b", text_fingerprint="2" * 64)
        previous, current = self._dual_snapshots(
            [old], [replacement], previous_documents, current_documents
        )
        reviews = self._record_reviews(
            previous,
            current,
            current_documents,
            replacement_reviews=[
                (
                    old["candidate_id"],
                    replacement["candidate_id"],
                    "changeforge-maintainers",
                    "The exact same-lineage replacement binds current source and detector evidence.",
                )
            ],
        )
        forged_current = deepcopy(current)
        forged_current["change_reviews"] = deepcopy(reviews)
        forged_current["change_reviews"][0]["evidence"][
            "prior_document_fingerprint"
        ] = "f" * 64
        forged_report = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": forged_current,
            },
            [replacement],
            current_documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual("invalid", forged_report["status"])
        self.assertTrue(
            any("canonical recomputation" in item for item in forged_report["errors"]),
            forged_report["errors"],
        )

        reviewed_current = deepcopy(current)
        reviewed_current["change_reviews"] = reviews
        _comparison, drift_errors = self.module._root_lifecycle_comparison(
            previous,
            reviewed_current,
            self.module._root_document_fingerprints(drifted_documents),
        )
        self.assertTrue(
            any("canonical recomputation" in item for item in drift_errors),
            drift_errors,
        )

    def test_review_wrong_classification_unknown_fields_and_v1_current_fail(self) -> None:
        previous_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        old = self._entry("a")
        replacement = self._entry("b", text_fingerprint="2" * 64)
        previous, current = self._dual_snapshots(
            [old], [replacement], previous_documents, current_documents
        )
        review = self._record_reviews(
            previous,
            current,
            current_documents,
            replacement_reviews=[
                (
                    old["candidate_id"],
                    replacement["candidate_id"],
                    "changeforge-maintainers",
                    "The exact same-lineage replacement is reviewed for both changed inputs.",
                )
            ],
        )[0]
        wrong = deepcopy(current)
        wrong_review = deepcopy(review)
        wrong_review["classification"] = "source-and-detector-removal"
        wrong["change_reviews"] = [wrong_review]
        comparison, errors = self.module._root_lifecycle_comparison(
            previous,
            wrong,
            self.module._root_document_fingerprints(current_documents),
        )
        self.assertEqual(1, comparison["unclassified_count"])
        self.assertTrue(
            any("must not select replacement IDs" in item for item in errors), errors
        )

        unknown = deepcopy(current)
        unknown_review = deepcopy(review)
        unknown_review["evidence"]["claimed_by_cli"] = True
        unknown["change_reviews"] = [unknown_review]
        _normalized, unknown_errors = self.module._validate_root_semantic_snapshot(
            unknown, label="snapshot", evaluation_date=date(2026, 7, 14)
        )
        self.assertTrue(any("evidence must contain exactly" in item for item in unknown_errors))

        v1_current = deepcopy(current)
        v1_current["schema_version"] = 1
        _normalized, v1_errors = self.module._validate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": previous,
                "current": v1_current,
            },
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(
            any(
                f"current.schema_version must equal {self.module.ROOT_SEMANTIC_SNAPSHOT_SCHEMA_VERSION}"
                in item
                for item in v1_errors
            )
        )

    def test_contract_rejects_stale_future_duplicate_and_unknown_fields(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        bootstrap = self._snapshot([entry], documents, kind="bootstrap")
        stale = deepcopy(bootstrap)
        stale["detector_fingerprint"] = "0" * 64
        stale_report = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": None,
                "current": stale,
            },
            [entry],
            documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual("invalid", stale_report["status"])
        self.assertTrue(any("bootstrap snapshot is stale" in item for item in stale_report["errors"]))

        future = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="future",
            released_on="2026-07-15",
            prior=bootstrap,
        )
        _normalized, errors = self.module._validate_root_semantic_snapshot(
            future, label="snapshot", evaluation_date=date(2026, 7, 14)
        )
        self.assertTrue(any("non-future ISO date" in item for item in errors), errors)

        duplicate = deepcopy(bootstrap)
        duplicate["entries"].append(deepcopy(duplicate["entries"][0]))
        _normalized, errors = self.module._validate_root_semantic_snapshot(
            duplicate, label="snapshot", evaluation_date=date(2026, 7, 14)
        )
        self.assertTrue(any("candidate_id must be unique" in item for item in errors), errors)

        unknown = deepcopy(bootstrap)
        unknown["unexpected"] = True
        _normalized, errors = self.module._validate_root_semantic_snapshot(
            unknown, label="snapshot", evaluation_date=date(2026, 7, 14)
        )
        self.assertTrue(any("must contain exactly" in item for item in errors), errors)

    def test_detector_fingerprint_binds_repository_source_operator_and_constant(
        self,
    ) -> None:
        baseline = self.module._root_semantic_detector_fingerprint()
        with mock.patch.object(
            self.module,
            "DESCRIPTION_ROOTS",
            self.module.DESCRIPTION_ROOTS[:-1],
        ):
            self.assertEqual(
                baseline, self.module._root_semantic_detector_fingerprint()
            )

        with self._detector_source_change(
            "ROOT_LONG_EXAMPLE_LINES = 12",
            "ROOT_LONG_EXAMPLE_LINES = 13",
        ):
            self.assertNotEqual(
                baseline, self.module._root_semantic_detector_fingerprint()
            )

        with self._detector_source_change(
            "and section.line_count > ROOT_LONG_EXAMPLE_LINES",
            "and section.line_count >= ROOT_LONG_EXAMPLE_LINES",
        ):
            self.assertNotEqual(
                baseline, self.module._root_semantic_detector_fingerprint()
            )

    def test_detector_v3_cross_version_portable_golden(self) -> None:
        self.assertEqual(
            ROOT_DETECTOR_V3_FINGERPRINT,
            self.module._root_semantic_detector_fingerprint(),
        )
        self.assertEqual(
            SKILL_DETECTOR_V3_FINGERPRINT,
            self.module._skill_detector_fingerprint(),
        )
        self.assertEqual(3, self.module._skill_detector_contract()["schema_version"])

    def test_detector_fingerprint_follows_comprehension_and_cross_module_closure(
        self,
    ) -> None:
        baseline = self.module._root_semantic_detector_fingerprint()
        with self._detector_source_change(
            'return f"{path}#{document_part}"',
            'return f"{path}::{document_part}"',
        ):
            self.assertNotEqual(
                baseline, self.module._root_semantic_detector_fingerprint()
            )

        with self._detector_source_change(
            "return _simple_yaml_load(text)",
            "return dict(_simple_yaml_load(text))",
            relative="scripts/validation_utils.py",
        ):
            self.assertNotEqual(
                baseline, self.module._root_semantic_detector_fingerprint()
            )

    def test_detector_source_catalog_fails_closed(self) -> None:
        source_files = self.module._DETECTOR_REPOSITORY_SOURCE_FILES
        with mock.patch.object(
            self.module,
            "_DETECTOR_REPOSITORY_SOURCE_FILES",
            (
                ("audit-skill-content", ROOT / "missing-audit-detector.py"),
                source_files[1],
            ),
        ):
            with self.assertRaisesRegex(
                self.module.ValidationProblem,
                "detector source is missing",
            ):
                self.module._root_semantic_detector_fingerprint()

        source_reader = self.module._detector_repository_source_text

        def duplicate_source(path: Path) -> str:
            text = source_reader(path)
            if path.resolve() == SCRIPT.resolve():
                return text + (
                    "\n\ndef _root_document_id(path: str, document_part: str) -> str:\n"
                    "    return f'{path}#{document_part}'\n"
                )
            return text

        with mock.patch.object(
            self.module,
            "_detector_repository_source_text",
            side_effect=duplicate_source,
        ):
            with self.assertRaisesRegex(
                self.module.ValidationProblem,
                "duplicate detector source symbol",
            ):
                self.module._root_semantic_detector_fingerprint()

        def unparseable_source(path: Path) -> str:
            text = source_reader(path)
            return text + "\nif (\n" if path.resolve() == SCRIPT.resolve() else text

        with mock.patch.object(
            self.module,
            "_detector_repository_source_text",
            side_effect=unparseable_source,
        ):
            with self.assertRaisesRegex(
                self.module.ValidationProblem,
                "cannot parse detector source",
            ):
                self.module._root_semantic_detector_fingerprint()

    def test_detector_payload_excludes_code_objects_and_external_source(self) -> None:
        payload = self.module._root_semantic_detector_payload()
        self.assertEqual("root-semantic-detector-v3", payload["contract"])

        def keys(value: object) -> set[str]:
            if isinstance(value, dict):
                return {
                    *(str(key) for key in value),
                    *(item for child in value.values() for item in keys(child)),
                }
            if isinstance(value, list):
                return {item for child in value for item in keys(child)}
            return set()

        self.assertTrue(
            {
                "bytecode_sha256",
                "names",
                "varnames",
                "argcount",
                "posonlyargcount",
                "kwonlyargcount",
                "flags",
            }.isdisjoint(keys(payload))
        )
        baseline = self.module._root_semantic_detector_fingerprint()
        with mock.patch.object(
            inspect,
            "getsource",
            side_effect=AssertionError("external callable source must not be read"),
        ):
            self.assertEqual(
                baseline, self.module._root_semantic_detector_fingerprint()
            )

    def test_detector_loaded_names_respect_python_lexical_scope(self) -> None:
        function = ast.parse(
            """
def root(parameter):
    assigned = module_assignment_source
    for loop_value in module_iterable:
        sink(loop_value)
    with module_context() as entered:
        sink(entered)
    try:
        sink(module_try)
    except ModuleError as caught:
        sink(caught)
    import dataclasses as imported_module
    from pathlib import Path as imported_name
    local_lambda = lambda lambda_arg: lambda_arg + lambda_global
    closure_value = closure_seed
    def nested(nested_arg):
        nested_local = nested_seed
        return nested_arg + nested_local + nested_global
    def mutate_closure():
        nonlocal closure_value
        closure_value += nonlocal_rhs
        return closure_value + nested_nonlocal_global
    def force_global():
        global forced_global
        return forced_global
    class Nested:
        class_local = class_seed
        def method(self):
            method_local = method_seed
            return self, method_local, method_global
    comp_result = [
        comp_item + comp_global
        for comp_item in comp_iterable
        if comp_item
    ]
    return (
        parameter, assigned, loop_value, entered, caught,
        imported_module, imported_name, local_lambda, nested,
        mutate_closure, force_global, Nested, comp_result, module_return,
    )
"""
        ).body[0]

        self.assertEqual(
            {
                "ModuleError",
                "class_seed",
                "closure_seed",
                "comp_global",
                "comp_iterable",
                "forced_global",
                "lambda_global",
                "method_global",
                "method_seed",
                "module_assignment_source",
                "module_context",
                "module_iterable",
                "module_return",
                "module_try",
                "nested_global",
                "nested_nonlocal_global",
                "nested_seed",
                "nonlocal_rhs",
                "sink",
            },
            set(self.module._detector_loaded_names(function)),
        )

    def test_skill_detector_excludes_shadowed_external_import_binding(self) -> None:
        payload = self.module._skill_detector_payload()
        self.assertNotIn(
            "audit-skill-content._readability_by_owner:field",
            payload["bindings"],
        )

    def test_skill_detector_includes_reachable_class_source(self) -> None:
        payload = self.module._skill_detector_payload()
        class_id = "audit-skill-content.SkillMetrics"
        self.assertIn(class_id, payload["symbols"])
        self.assertEqual(
            {
                "kind": "repository-symbol",
                "target": class_id,
            },
            payload["bindings"]["audit-skill-content._base_metrics:SkillMetrics"],
        )
        self.assertEqual("class", payload["symbols"][class_id]["kind"])
        self.assertTrue(
            payload["symbols"][class_id]["source"].startswith(
                "@dataclass\nclass SkillMetrics:"
            )
        )

        baseline = self.module._skill_detector_fingerprint()
        with self._detector_source_change(
            'risk_of_change: str = "low"',
            'risk_of_change: str = "medium"',
        ):
            self.assertNotEqual(baseline, self.module._skill_detector_fingerprint())

        with self._detector_source_change(
            "class SkillMetrics:",
            "class RemovedSkillMetrics:",
        ):
            with self.assertRaisesRegex(
                self.module.ValidationProblem,
                "unknown detector source symbol.*SkillMetrics",
            ):
                self.module._skill_detector_fingerprint()

    def test_detector_fingerprint_is_independent_of_module_load_name(self) -> None:
        alias = "root_disposition_lifecycle_alias_auditor"
        try:
            alias_module = _load_module(alias)
            self.assertEqual(
                self.module._root_semantic_detector_fingerprint(),
                alias_module._root_semantic_detector_fingerprint(),
            )
        finally:
            sys.modules.pop(alias, None)

    def test_removed_document_uses_global_source_and_detector_classification(self) -> None:
        documents = [self._document("owned source")]
        entry = self._entry("a")
        previous = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-12",
        )
        current = self._snapshot(
            [],
            [],
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )

        source_only, errors = self.module._root_lifecycle_comparison(
            previous, current, {}
        )
        self.assertEqual([], errors)
        self.assertEqual(1, source_only["source_rewrite_count"])

        both_previous = deepcopy(previous)
        both_previous["detector_fingerprint"] = "0" * 64
        both, errors = self.module._root_lifecycle_comparison(
            both_previous, current, {}
        )
        self.assertEqual([], errors)
        self.assertEqual("source-and-detector-changed", both["unclassified"][0]["reason"])

        unchanged_global = self.module._root_document_set_fingerprint({})
        detector_previous = deepcopy(previous)
        detector_previous["document_fingerprint"] = unchanged_global
        detector_previous["detector_fingerprint"] = "0" * 64
        detector, errors = self.module._root_lifecycle_comparison(
            detector_previous, current, {}
        )
        self.assertEqual([], errors)
        self.assertEqual(1, detector["detector_change_removal_count"])
        self.assertEqual(0, detector["source_rewrite_count"])

        neither_previous = deepcopy(previous)
        neither_previous["document_fingerprint"] = unchanged_global
        neither, errors = self.module._root_lifecycle_comparison(
            neither_previous, current, {}
        )
        self.assertEqual([], errors)
        self.assertEqual("unexplained-removal", neither["unclassified"][0]["reason"])

    def test_disposition_change_requires_exact_review(self) -> None:
        documents = [self._document("stable source")]
        previous_entry = self._entry("a", disposition="valid-contextual-rule")
        current_entry = self._entry("a", disposition="false-positive")
        previous = self._snapshot(
            [previous_entry],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-12",
        )
        current = self._snapshot(
            [current_entry],
            documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
        )
        comparison, errors = self.module._root_lifecycle_comparison(
            previous,
            current,
            self.module._root_document_fingerprints(documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, comparison["disposition_change_count"])
        self.assertEqual([previous_entry["candidate_id"]], comparison["disposition_changes"])
        self.assertEqual(1, comparison["unclassified_count"])

        reviews = self._record_reviews(
            previous,
            current,
            documents,
            change_reviews=[
                (
                    previous_entry["candidate_id"],
                    "changeforge-maintainers",
                    "The current source and governing policy support this exact disposition transition.",
                )
            ],
        )
        reviewed_current = self._snapshot(
            [current_entry],
            documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-13",
            prior=previous,
            reviews=reviews,
        )
        reviewed, errors = self.module._root_lifecycle_comparison(
            previous,
            reviewed_current,
            self.module._root_document_fingerprints(documents),
        )
        self.assertEqual([], errors)
        self.assertEqual(0, reviewed["unclassified_count"])
        self.assertEqual(
            "changeforge-maintainers",
            reviewed["disposition_change_details"][0]["reviewed_by"],
        )

        with self.assertRaisesRegex(self.module.ValidationProblem, "duplicate"):
            self.module._root_recorded_change_reviews(
                [
                    (previous_entry["candidate_id"], "one", "A specific accountable rationale."),
                    (previous_entry["candidate_id"], "two", "Another specific accountable rationale."),
                ],
                comparison,
                previous=previous,
                current=current,
                current_document_fingerprints=self.module._root_document_fingerprints(
                    documents
                ),
            )
        with self.assertRaisesRegex(self.module.ValidationProblem, "unused"):
            self.module._root_recorded_change_reviews(
                [("f" * 64, "owner", "A specific accountable rationale.")],
                comparison,
                previous=previous,
                current=current,
                current_document_fingerprints=self.module._root_document_fingerprints(
                    documents
                ),
            )

    def test_stale_bootstrap_can_be_consumed_only_by_release_recorder(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        bootstrap = self._snapshot([entry], documents, kind="bootstrap")
        bootstrap["detector_fingerprint"] = "0" * 64
        bootstrap["bootstrap_refresh_origin_state_fingerprint"] = (
            self.module._root_bootstrap_base_state_fingerprint(bootstrap)
        )
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": None,
            "current": bootstrap,
        }

        strict = self.module._evaluate_root_semantic_lifecycle(
            lifecycle,
            [entry],
            documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual("invalid", strict["status"])
        recording = self.module._evaluate_root_semantic_lifecycle(
            lifecycle,
            [entry],
            documents,
            evaluation_date=date(2026, 7, 14),
            allow_stale_current=True,
        )
        self.assertEqual("pending-changes", recording["status"])
        self.assertEqual([], recording["errors"])

        report = {"disposition_contract": {"entries": [entry], "errors": []}}
        written = []

        def synthetic_root_documents():
            return documents

        synthetic_root_documents.__module__ = self.module.__name__
        synthetic_root_documents.__name__ = "_root_skill_documents"
        with (
            mock.patch.object(
                self.module,
                "_root_skill_documents",
                new=synthetic_root_documents,
            ),
            mock.patch.object(
                self.module,
                "_collect_root_semantic_advisories",
                return_value=report,
            ) as collect,
            mock.patch.object(
                self.module,
                "_load_root_semantic_dispositions_for_recorder",
                return_value=(
                    {
                        "schema_version": self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                        "lifecycle": lifecycle,
                        "entries": [entry],
                    },
                    self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                    "a" * 64,
                    [],
                ),
            ),
            mock.patch.object(
                self.module,
                "_replace_root_semantic_lifecycle_block",
                side_effect=lambda _path, value, **_kwargs: written.append(value),
            ),
        ):
            result = self.module._record_root_semantic_release(
                "r1", "2026-07-14", evaluation_date=date(2026, 7, 14)
            )
        self.assertTrue(collect.call_args.kwargs["allow_stale_lifecycle"])
        self.assertEqual("release-current", result["status"])
        self.assertTrue(result["formal_release_ready"])
        self.assertEqual(bootstrap, written[0]["previous"])
        self.assertEqual("release", written[0]["current"]["kind"])

    def test_recorder_does_not_bypass_duplicate_or_future_snapshot_errors(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        bootstrap = self._snapshot([entry], documents, kind="bootstrap")
        duplicate = deepcopy(bootstrap)
        duplicate["entries"].append(deepcopy(duplicate["entries"][0]))
        future = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="future",
            released_on="2026-07-15",
            prior=bootstrap,
        )
        report = {"disposition_contract": {"entries": [entry], "errors": []}}
        for current, expected in (
            (duplicate, "candidate_id must be unique"),
            (future, "non-future ISO date"),
        ):
            lifecycle = {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": bootstrap if current is future else None,
                "current": current,
            }
            with (
                self.subTest(expected=expected),
                mock.patch.object(
                    self.module, "_root_skill_documents", return_value=documents
                ),
                mock.patch.object(
                    self.module,
                    "_collect_root_semantic_advisories",
                    return_value=report,
                ),
                mock.patch.object(
                    self.module,
                    "_load_root_semantic_dispositions_for_recorder",
                    return_value=(
                        {
                            "schema_version": self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                            "lifecycle": lifecycle,
                            "entries": [entry],
                        },
                        self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                        "a" * 64,
                        [],
                    ),
                ),
                mock.patch.object(
                    self.module, "_replace_root_semantic_lifecycle_block"
                ) as replace,
                self.assertRaisesRegex(self.module.ValidationProblem, expected),
            ):
                self.module._record_root_semantic_release(
                    "r2", "2026-07-14", evaluation_date=date(2026, 7, 14)
                )
            replace.assert_not_called()

    def test_release_recorder_allows_unique_same_day_snapshot(self) -> None:
        documents = [self._document("stable source")]
        inherited = self._entry("a")
        first_seen = self._entry("b")
        bootstrap = self._snapshot([inherited], documents, kind="bootstrap")
        first_release = self._snapshot(
            [inherited, first_seen],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-14",
            prior=bootstrap,
        )
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": bootstrap,
            "current": first_release,
        }

        result, written = self._record_release(
            lifecycle,
            [inherited, first_seen],
            documents,
            release_id="r2",
            released_on="2026-07-14",
            evaluation_date=date(2026, 7, 14),
        )

        self.assertEqual("release-current", result["status"])
        self.assertEqual(1, result["age"]["known_age_count"])
        self.assertEqual(1, result["age"]["unknown_age_count"])
        self.assertEqual(0, result["age"]["max_age_days"])
        self.assertEqual("r1", written[0]["previous"]["release_id"])
        self.assertEqual("r2", written[0]["current"]["release_id"])
        self.assertEqual(
            {"status": "unknown-pre-baseline", "release_id": None, "released_on": None},
            written[0]["current"]["entries"][0]["first_observed"],
        )

    def test_release_recorder_rejects_same_day_duplicate_chain_id(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        previous = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="r0",
            released_on="2026-07-14",
        )
        current = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-14",
            prior=previous,
        )
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": previous,
            "current": current,
        }

        for duplicate_id in ("r0", "r1"):
            with self.subTest(release_id=duplicate_id), self.assertRaisesRegex(
                self.module.ValidationProblem, "unique"
            ):
                self._record_release(
                    lifecycle,
                    [entry],
                    documents,
                    release_id=duplicate_id,
                    released_on="2026-07-14",
                    evaluation_date=date(2026, 7, 14),
                )

    def test_release_recorder_rejects_earlier_date(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        previous = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="r0",
            released_on="2026-07-13",
        )
        current = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-14",
            prior=previous,
        )
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": previous,
            "current": current,
        }

        with self.assertRaisesRegex(self.module.ValidationProblem, "cannot be earlier"):
            self._record_release(
                lifecycle,
                [entry],
                documents,
                release_id="r2",
                released_on="2026-07-13",
                evaluation_date=date(2026, 7, 14),
            )

    def test_release_recorder_rejects_future_date(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        bootstrap = self._snapshot([entry], documents, kind="bootstrap")
        current = self._snapshot(
            [entry],
            documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-14",
            prior=bootstrap,
        )
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": bootstrap,
            "current": current,
        }

        with self.assertRaisesRegex(self.module.ValidationProblem, "non-future ISO date"):
            self._record_release(
                lifecycle,
                [entry],
                documents,
                release_id="r2",
                released_on="2026-07-15",
                evaluation_date=date(2026, 7, 14),
            )

    def test_change_review_cli_is_repeatable_and_requires_recorder(self) -> None:
        parsed = self.module._args(
            [
                "--gate",
                "authoring",
                "--record-root-disposition-release",
                "r1",
                "--released-on",
                "2026-07-14",
                "--change-review",
                "a" * 64,
                "owner-a",
                "First accountable rationale.",
                "--change-review",
                "b" * 64,
                "owner-b",
                "Second accountable rationale.",
                "--source-replacement-review",
                "3" * 64,
                "4" * 64,
                "owner-three",
                "Exact source-only replacement rationale.",
                "--source-removal-review",
                "5" * 64,
                "owner-five",
                "Exact source-only removal rationale.",
                "--source-detector-replacement-review",
                "c" * 64,
                f"{'d' * 64},{'e' * 64}",
                "owner-c",
                "Exact replacement rationale.",
                "--source-detector-replacement-review",
                "f" * 64,
                "1" * 64,
                "owner-f",
                "Second exact replacement rationale.",
                "--source-detector-removal-review",
                "2" * 64,
                "owner-two",
                "Exact removal rationale.",
            ]
        )
        self.assertEqual(2, len(parsed.change_review))
        self.assertEqual(1, len(parsed.source_replacement_review))
        self.assertEqual(1, len(parsed.source_removal_review))
        self.assertEqual(2, len(parsed.source_detector_replacement_review))
        self.assertEqual(1, len(parsed.source_detector_removal_review))
        for flag, values in (
            (
                "--change-review",
                ["a" * 64, "owner", "Accountable rationale."],
            ),
            (
                "--source-replacement-review",
                ["a" * 64, "b" * 64, "owner", "Accountable rationale."],
            ),
            (
                "--source-removal-review",
                ["a" * 64, "owner", "Accountable rationale."],
            ),
            (
                "--source-detector-replacement-review",
                ["a" * 64, "b" * 64, "owner", "Accountable rationale."],
            ),
            (
                "--source-detector-removal-review",
                ["a" * 64, "owner", "Accountable rationale."],
            ),
        ):
            with self.subTest(flag=flag), self.assertRaises(SystemExit):
                self.module._args(["--gate", "authoring", flag, *values])

        with self.assertRaises(SystemExit):
            self.module._args(
                [
                    "--gate",
                    "authoring",
                    "--record-root-disposition-release",
                    "r1",
                    "--released-on",
                    "2026-07-14",
                    "--change-review",
                    "a" * 64,
                    "owner",
                    "Accountable rationale.",
                    "--source-removal-review",
                    "a" * 64,
                    "owner",
                    "Another accountable rationale.",
                ]
            )

    def test_bootstrap_refresh_cli_rejects_missing_blank_generic_mutual_and_repeat(self) -> None:
        parsed = self.module._args(
            [
                "--gate",
                "authoring",
                "--refresh-root-disposition-bootstrap",
                "changeforge-maintainers",
                "The current Root source rewrite and detector evidence were reviewed for authoring bootstrap freshness.",
            ]
        )
        self.assertEqual(
            (
                "changeforge-maintainers",
                "The current Root source rewrite and detector evidence were reviewed for authoring bootstrap freshness.",
            ),
            parsed.refresh_root_disposition_bootstrap,
        )
        invalid = (
            ["--refresh-root-disposition-bootstrap"],
            ["--refresh-root-disposition-bootstrap", "owner"],
            ["--refresh-root-disposition-bootstrap", "", "Specific source review rationale."],
            ["--refresh-root-disposition-bootstrap", "owner", "looks good"],
            [
                "--refresh-root-disposition-bootstrap",
                "owner",
                "Specific source and detector review rationale.",
                "--refresh-root-disposition-bootstrap",
                "owner-two",
                "Second specific source and detector review rationale.",
            ],
            [
                "--refresh-root-disposition-bootstrap",
                "owner",
                "Specific source and detector review rationale.",
                "--record-root-disposition-release",
                "r1",
                "--released-on",
                "2026-07-14",
            ],
            [
                "--refresh-root-disposition-bootstrap",
                "owner",
                "Specific source and detector review rationale.",
                "--change-review",
                "a" * 64,
                "formal-owner",
                "Specific formal change review rationale.",
            ],
            [
                "--refresh-root-disposition-bootstrap",
                "owner",
                "Specific source and detector review rationale.",
                "--released-on",
                "",
            ],
            [
                "--refresh-root-disposition-bootstrap",
                "owner",
                "Specific source and detector review rationale.",
                "--record-root-disposition-release",
                "",
            ],
            [
                "--refresh-root-disposition-bootstrap",
                "owner",
                "Specific source and detector review rationale.",
                "--record-root-disposition-release",
                "",
                "--released-on",
                "",
            ],
            [
                "--record-root-disposition-release",
                "",
                "--released-on",
                "2026-07-14",
            ],
            [
                "--record-root-disposition-release",
                "r1",
                "--released-on",
                "",
            ],
            [
                "--record-root-disposition-release",
                "",
                "--released-on",
                "",
            ],
        )
        for argv in invalid:
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.module._args(["--gate", "authoring", *argv])

    def test_bootstrap_refresh_recorder_enforces_eligibility_unresolved_and_no_op(self) -> None:
        prior_documents = [self._document("old source")]
        current_documents = [self._document("new source")]
        entry = self._entry("a")
        prior = self._snapshot([entry], prior_documents, kind="bootstrap")
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": None,
            "current": prior,
        }
        loaded = {
            "schema_version": self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            "lifecycle": lifecycle,
            "entries": [entry],
        }
        report = {
            "disposition_contract": {"entries": [entry], "errors": []},
            "summary": {"unresolved_candidates": 0},
        }
        written = []
        with (
            mock.patch.object(
                self.module,
                "_load_root_semantic_dispositions_for_recorder",
                return_value=(
                    loaded,
                    self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                    "a" * 64,
                    [],
                ),
            ),
            mock.patch.object(
                self.module, "_root_skill_documents", return_value=current_documents
            ),
            mock.patch.object(
                self.module,
                "_collect_root_semantic_advisories",
                return_value=report,
            ),
            mock.patch.object(
                self.module,
                "_replace_root_semantic_lifecycle_block",
                side_effect=lambda _path, value, **kwargs: written.append(
                    (value, kwargs)
                ),
            ),
        ):
            result = self.module._record_root_semantic_bootstrap_refresh(
                "changeforge-maintainers",
                "The current Root source rewrite and disposition evidence were reviewed for authoring bootstrap freshness.",
                evaluation_date=date(2026, 7, 14),
            )
        self.assertEqual("bootstrap-current", result["status"])
        self.assertFalse(result["formal_release_ready"])
        self.assertEqual(1, result["bootstrap_refresh_chain"]["count"])
        self.assertEqual(1, len(written))
        self.assertEqual(
            self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            written[0][1]["source_schema_version"],
        )
        self.assertEqual("a" * 64, written[0][1]["expected_preimage_sha256"])

        cases = []
        no_op_loaded = deepcopy(loaded)
        no_op_loaded["lifecycle"]["current"] = self._snapshot(
            [entry], current_documents, kind="bootstrap"
        )
        cases.append(("no-op", no_op_loaded, report, "no-op"))
        previous_loaded = deepcopy(loaded)
        previous_loaded["lifecycle"]["previous"] = deepcopy(prior)
        cases.append(("previous", previous_loaded, report, "previous=null"))
        release_loaded = deepcopy(loaded)
        release_loaded["lifecycle"]["current"] = self._snapshot(
            [entry],
            prior_documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-13",
            prior=prior,
        )
        release_loaded["lifecycle"]["previous"] = prior
        cases.append(("release", release_loaded, report, "previous=null"))
        unresolved_report = deepcopy(report)
        unresolved_report["summary"]["unresolved_candidates"] = 1
        cases.append(("unresolved", loaded, unresolved_report, "unresolved"))
        stale_report = deepcopy(report)
        stale_report["disposition_contract"]["errors"] = ["stale disposition"]
        cases.append(("stale", loaded, stale_report, "stale or invalid"))
        for label, case_loaded, case_report, expected in cases:
            with (
                self.subTest(label=label),
                mock.patch.object(
                    self.module,
                    "_load_root_semantic_dispositions_for_recorder",
                    return_value=(
                        case_loaded,
                        self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                        "a" * 64,
                        [],
                    ),
                ),
                mock.patch.object(
                    self.module,
                    "_root_skill_documents",
                    return_value=current_documents,
                ),
                mock.patch.object(
                    self.module,
                    "_collect_root_semantic_advisories",
                    return_value=case_report,
                ),
                mock.patch.object(
                    self.module, "_replace_root_semantic_lifecycle_block"
                ) as replace,
                self.assertRaisesRegex(self.module.ValidationProblem, expected),
            ):
                self.module._record_root_semantic_bootstrap_refresh(
                    "changeforge-maintainers",
                    "The current Root source rewrite and disposition evidence were reviewed for authoring bootstrap freshness.",
                    evaluation_date=date(2026, 7, 14),
                )
            replace.assert_not_called()

    def test_release_recorder_forwards_loader_schema_and_exact_preimage(self) -> None:
        documents = [self._document("stable source")]
        entry = self._entry("a")
        bootstrap = self._snapshot([entry], documents, kind="bootstrap")
        lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": None,
            "current": bootstrap,
        }
        loaded = {
            "schema_version": self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            "lifecycle": lifecycle,
            "entries": [entry],
        }
        report = {"disposition_contract": {"entries": [entry], "errors": []}}
        with (
            mock.patch.object(
                self.module,
                "_load_root_semantic_dispositions_for_recorder",
                return_value=(loaded, 5, "b" * 64, []),
            ) as loader,
            mock.patch.object(
                self.module, "_root_skill_documents", return_value=documents
            ),
            mock.patch.object(
                self.module,
                "_collect_root_semantic_advisories",
                return_value=report,
            ),
            mock.patch.object(
                self.module, "_replace_root_semantic_lifecycle_block"
            ) as replace,
        ):
            self.module._record_root_semantic_release(
                "r1", "2026-07-14", evaluation_date=date(2026, 7, 14)
            )
        loader.assert_called_once_with(evaluation_date=date(2026, 7, 14))
        self.assertEqual(5, replace.call_args.kwargs["source_schema_version"])
        self.assertEqual(
            "b" * 64,
            replace.call_args.kwargs["expected_preimage_sha256"],
        )

    def test_bootstrap_refresh_chain_rolls_into_first_release_then_expires(self) -> None:
        entry = self._entry("a")
        initial_documents = [self._document("initial source")]
        current_documents = [self._document("current source")]
        bootstrap = self._snapshot([entry], initial_documents, kind="bootstrap")
        refreshed = self._bootstrap_refresh(
            bootstrap, [entry], current_documents
        )
        release_one = self._snapshot(
            [entry],
            current_documents,
            kind="release",
            release_id="r1",
            released_on="2026-07-13",
            prior=refreshed,
        )
        first_lifecycle = {
            "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
            "previous": refreshed,
            "current": release_one,
        }
        first = self.module._evaluate_root_semantic_lifecycle(
            first_lifecycle,
            [entry],
            current_documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertEqual("release-current", first["status"])
        self.assertTrue(first["formal_release_ready"])
        self.assertEqual(1, first["bootstrap_refresh_chain"]["count"])
        self.assertEqual([], release_one["bootstrap_refresh_reviews"])
        self.assertIsNone(
            release_one["bootstrap_refresh_origin_state_fingerprint"]
        )
        self.assertEqual(0, release_one["bootstrap_refresh_review_count"])
        self.assertEqual(
            bootstrap["bootstrap_refresh_origin_state_fingerprint"],
            refreshed["bootstrap_refresh_origin_state_fingerprint"],
        )

        release_two = self._snapshot(
            [entry],
            current_documents,
            kind="release",
            release_id="r2",
            released_on="2026-07-14",
            prior=release_one,
        )
        second = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": release_one,
                "current": release_two,
            },
            [entry],
            current_documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertTrue(second["formal_release_ready"])
        self.assertEqual(0, second["bootstrap_refresh_chain"]["count"])

        changed = self._entry("a", disposition="false-positive")
        unreviewed_release = self._snapshot(
            [changed],
            current_documents,
            kind="release",
            release_id="r1-changed",
            released_on="2026-07-13",
            prior=refreshed,
        )
        unreviewed = self.module._evaluate_root_semantic_lifecycle(
            {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": refreshed,
                "current": unreviewed_release,
            },
            [changed],
            current_documents,
            evaluation_date=date(2026, 7, 14),
        )
        self.assertFalse(unreviewed["formal_release_ready"])
        self.assertEqual(1, unreviewed["comparison"]["unclassified_count"])

    def test_detector_and_lifecycle_calculation_do_not_require_git(self) -> None:
        original = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as raw:
                os.chdir(raw)
                fingerprint = self.module._root_semantic_detector_fingerprint()
                self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
                documents = [self._document("source")]
                entry = self._entry("a")
                lifecycle = self.module._root_bootstrap_lifecycle(
                    [entry], self.module._root_document_fingerprints(documents)
                )
                report = self.module._evaluate_root_semantic_lifecycle(
                    lifecycle,
                    [entry],
                    documents,
                    evaluation_date=date(2026, 7, 14),
                )
                self.assertEqual("bootstrap-current", report["status"])
        finally:
            os.chdir(original)

    def test_managed_block_update_is_bounded_and_round_trips(self) -> None:
        source = ROOT / "config" / "skill-content-exceptions.yaml"
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / source.name
            target.write_bytes(source.read_bytes())
            target.chmod(0o640)
            current_text = target.read_text(encoding="utf-8")
            current_data = self.module.load_yaml_file(target)
            current_snapshot = current_data[
                self.module.ROOT_SEMANTIC_DISPOSITION_KEY
            ]["lifecycle"]["current"]
            legacy_current = deepcopy(current_snapshot)
            legacy_current["schema_version"] = (
                self.module.ROOT_SEMANTIC_LEGACY_SNAPSHOT_SCHEMA_VERSION
            )
            for field in (
                "bootstrap_refresh_reviews",
                "bootstrap_refresh_origin_state_fingerprint",
                "bootstrap_refresh_review_count",
            ):
                del legacy_current[field]
            legacy_lines = [
                self.module.ROOT_LIFECYCLE_START_MARKER,
                "  lifecycle:",
                "    schema_version: "
                + str(self.module.ROOT_SEMANTIC_LEGACY_LIFECYCLE_SCHEMA_VERSION),
                "    previous: null",
                "    current:",
            ]
            for field in (
                "schema_version",
                "kind",
                "release_id",
                "released_on",
                "document_fingerprint",
                "detector_fingerprint",
            ):
                legacy_lines.append(
                    f"      {field}: "
                    + self.module.json.dumps(
                        legacy_current[field],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                )
            for field in ("entries", "change_reviews"):
                legacy_lines.append(f"      {field}:")
                if legacy_current[field]:
                    legacy_lines.extend(
                        "        - "
                        + self.module.json.dumps(
                            item, ensure_ascii=False, separators=(",", ":")
                        )
                        for item in legacy_current[field]
                    )
                else:
                    legacy_lines[-1] += " []"
            legacy_lines.append(self.module.ROOT_LIFECYCLE_END_MARKER)
            start = current_text.index(self.module.ROOT_LIFECYCLE_START_MARKER)
            end = current_text.index(
                self.module.ROOT_LIFECYCLE_END_MARKER, start
            ) + len(self.module.ROOT_LIFECYCLE_END_MARKER)
            legacy_text = (
                current_text[:start]
                + "\n".join(legacy_lines)
                + current_text[end:]
            ).replace(
                "root_semantic_dispositions:\n  schema_version: 5\n",
                "root_semantic_dispositions:\n  schema_version: 4\n",
                1,
            )
            target.write_text(legacy_text, encoding="utf-8")
            before_mode = stat.S_IMODE(target.stat().st_mode)
            before_text = target.read_text(encoding="utf-8")
            before = self.module.load_yaml_file(target)
            legacy = before[self.module.ROOT_SEMANTIC_DISPOSITION_KEY]["lifecycle"]
            current, errors = self.module._migrate_root_semantic_snapshot_v2(
                legacy["current"], label="legacy.current"
            )
            self.assertEqual([], errors)
            lifecycle = {
                "schema_version": self.module.ROOT_SEMANTIC_LIFECYCLE_SCHEMA_VERSION,
                "previous": None,
                "current": current,
            }
            self._replace_lifecycle(target, lifecycle)
            after = self.module.load_yaml_file(target)
            expected = deepcopy(before)
            expected[self.module.ROOT_SEMANTIC_DISPOSITION_KEY][
                "schema_version"
            ] = self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION
            expected[self.module.ROOT_SEMANTIC_DISPOSITION_KEY][
                "lifecycle"
            ] = lifecycle
            self.assertEqual(expected, after)
            text = target.read_text(encoding="utf-8")
            start = before_text.index(self.module.ROOT_LIFECYCLE_START_MARKER)
            end = before_text.index(
                self.module.ROOT_LIFECYCLE_END_MARKER, start
            ) + len(self.module.ROOT_LIFECYCLE_END_MARKER)
            expected_text = (
                before_text[:start]
                + self.module._render_root_semantic_lifecycle_yaml(lifecycle)
                + before_text[end:]
            ).replace(
                "root_semantic_dispositions:\n  schema_version: 4\n",
                "root_semantic_dispositions:\n  schema_version: 6\n",
                1,
            )
            self.assertEqual(expected_text, text)
            self.assertEqual(before_mode, stat.S_IMODE(target.stat().st_mode))
            self.assertEqual(1, text.count(self.module.ROOT_LIFECYCLE_START_MARKER))
            self.assertEqual(1, text.count(self.module.ROOT_LIFECYCLE_END_MARKER))
            self._replace_lifecycle(target, lifecycle)
            self.assertEqual(text, target.read_text(encoding="utf-8"))

    def test_managed_block_rejects_marker_yaml_and_prewrite_failures_atomically(self) -> None:
        documents = [self._document("source")]
        lifecycle = self.module._root_bootstrap_lifecycle(
            [self._entry("a")],
            self.module._root_document_fingerprints(documents),
        )
        valid = (
            "root_semantic_dispositions:\n"
            f"  schema_version: {self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION}\n"
            + self.module._render_root_semantic_lifecycle_yaml(lifecycle)
            + "\n  entries:\n    - marker: true\nreference_semantic_dispositions:\n"
            "  schema_version: 2\n  entries: []\n"
        )
        variants = {
            "missing-marker": valid.replace(
                self.module.ROOT_LIFECYCLE_END_MARKER, ""
            ),
            "duplicate-marker": valid.replace(
                self.module.ROOT_LIFECYCLE_START_MARKER,
                self.module.ROOT_LIFECYCLE_START_MARKER
                + "\n"
                + self.module.ROOT_LIFECYCLE_START_MARKER,
                1,
            ),
        }
        with tempfile.TemporaryDirectory() as raw:
            for label, content in variants.items():
                target = Path(raw) / f"{label}.yaml"
                target.write_text(content, encoding="utf-8")
                before = target.read_bytes()
                with self.subTest(label=label), self.assertRaises(
                    (self.module.ValidationProblem, ValueError)
                ):
                    self._replace_lifecycle(target, lifecycle)
                self.assertEqual(before, target.read_bytes())

            target = Path(raw) / "prewrite.yaml"
            target.write_text(valid, encoding="utf-8")
            before = target.read_bytes()
            original = self.module.load_yaml_text
            calls = 0

            def fail_second_parse(text, path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise self.module.ValidationProblem("synthetic updated YAML failure")
                return original(text, path)

            with (
                mock.patch.object(
                    self.module, "load_yaml_text", side_effect=fail_second_parse
                ),
                self.assertRaisesRegex(
                    self.module.ValidationProblem, "synthetic updated YAML failure"
                ),
            ):
                self._replace_lifecycle(target, lifecycle)
            self.assertEqual(before, target.read_bytes())

            changed_lifecycle = self.module._root_bootstrap_lifecycle(
                [self._entry("a")],
                self.module._root_document_fingerprints(
                    [self._document("changed source")]
                ),
            )
            for failure in ("partial-temp-write", "replace"):
                with self.subTest(failure=failure):
                    target = Path(raw) / f"{failure}.yaml"
                    target.write_text(valid, encoding="utf-8")
                    target.chmod(0o640)
                    before = target.read_bytes()
                    before_mode = stat.S_IMODE(target.stat().st_mode)

                    def partial_temp_write(stream, text):
                        stream.write(text[:47])
                        stream.flush()
                        raise OSError("synthetic partial temporary write")

                    patcher = (
                        mock.patch.object(
                            self.module,
                            "_write_root_atomic_temp",
                            side_effect=partial_temp_write,
                        )
                        if failure == "partial-temp-write"
                        else mock.patch.object(
                            self.module.os,
                            "replace",
                            side_effect=OSError("synthetic replace failure"),
                        )
                    )
                    with patcher, self.assertRaises(OSError):
                        self._replace_lifecycle(target, changed_lifecycle)
                    self.assertEqual(before, target.read_bytes())
                    self.assertEqual(
                        before_mode,
                        stat.S_IMODE(target.stat().st_mode),
                    )
                    self.assertEqual(
                        [],
                        list(target.parent.glob(f".{target.name}.*.tmp")),
                    )

    def test_managed_block_preimage_rejects_same_schema_changes(self) -> None:
        lifecycle = self.module._root_bootstrap_lifecycle(
            [self._entry("a")],
            self.module._root_document_fingerprints([self._document("source")]),
        )
        initial = (
            "# stable leading comment\n"
            f"{self.module.ROOT_SEMANTIC_DISPOSITION_KEY}:\n"
            f"  schema_version: {self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION}\n"
            + self.module._render_root_semantic_lifecycle_yaml(lifecycle)
            + "\n  entries:\n    - marker: true\n"
            "semantic_disposition_application:\n  marker: stable\n"
            "reference_semantic_dispositions:\n  schema_version: 2\n  entries: []\n"
        )
        mutations = {
            "entries": initial.replace("marker: true", "marker: false", 1),
            "application": initial.replace("marker: stable", "marker: changed", 1),
            "lifecycle": initial.replace(
                "bootstrap_refresh_review_count: 0",
                "bootstrap_refresh_review_count: 1",
                1,
            ),
            "comment": initial.replace(
                "# stable leading comment", "# concurrently changed comment", 1
            ),
            "whitespace": initial.replace("  entries:\n", "  entries: \n", 1),
        }
        expected_preimage = hashlib.sha256(initial.encode("utf-8")).hexdigest()
        with tempfile.TemporaryDirectory() as raw:
            for label, concurrent in mutations.items():
                target = Path(raw) / f"{label}.yaml"
                target.write_text(concurrent, encoding="utf-8")
                before = target.read_bytes()
                with (
                    self.subTest(label=label),
                    mock.patch.object(self.module.os, "replace") as replace,
                    self.assertRaisesRegex(
                        self.module.ValidationProblem, "changed since recorder load"
                    ),
                ):
                    self.module._replace_root_semantic_lifecycle_block(
                        target,
                        lifecycle,
                        source_schema_version=self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                        expected_preimage_sha256=expected_preimage,
                    )
                replace.assert_not_called()
                self.assertEqual(before, target.read_bytes())
                self.assertEqual([], list(target.parent.glob(f".{target.name}.*.tmp")))

    def test_managed_block_final_preimage_check_preserves_concurrent_bytes(self) -> None:
        lifecycle = self.module._root_bootstrap_lifecycle(
            [self._entry("a")],
            self.module._root_document_fingerprints([self._document("source")]),
        )
        changed_lifecycle = self.module._root_bootstrap_lifecycle(
            [self._entry("a")],
            self.module._root_document_fingerprints(
                [self._document("changed source")]
            ),
        )
        initial = (
            f"{self.module.ROOT_SEMANTIC_DISPOSITION_KEY}:\n"
            f"  schema_version: {self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION}\n"
            + self.module._render_root_semantic_lifecycle_yaml(lifecycle)
            + "\n  entries:\n    - marker: true\n"
            "semantic_disposition_application:\n  marker: stable\n"
            "reference_semantic_dispositions:\n  schema_version: 2\n  entries: []\n"
        )
        concurrent = initial.replace("marker: stable", "marker: concurrent", 1).encode(
            "utf-8"
        )
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "race.yaml"
            target.write_text(initial, encoding="utf-8")
            expected_preimage = hashlib.sha256(target.read_bytes()).hexdigest()
            original_write = self.module._write_root_atomic_temp

            def write_then_mutate(stream, text):
                original_write(stream, text)
                target.write_bytes(concurrent)

            with (
                mock.patch.object(
                    self.module,
                    "_write_root_atomic_temp",
                    side_effect=write_then_mutate,
                ),
                mock.patch.object(self.module.os, "replace") as replace,
                self.assertRaisesRegex(
                    self.module.ValidationProblem,
                    "changed before atomic replacement",
                ),
            ):
                self.module._replace_root_semantic_lifecycle_block(
                    target,
                    changed_lifecycle,
                    source_schema_version=self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                    expected_preimage_sha256=expected_preimage,
                )
            replace.assert_not_called()
            self.assertEqual(concurrent, target.read_bytes())
            self.assertEqual([], list(target.parent.glob(f".{target.name}.*.tmp")))

    def test_managed_block_rejects_bad_digest_and_source_schema(self) -> None:
        lifecycle = self.module._root_bootstrap_lifecycle(
            [self._entry("a")],
            self.module._root_document_fingerprints([self._document("source")]),
        )
        initial = (
            f"{self.module.ROOT_SEMANTIC_DISPOSITION_KEY}:\n"
            f"  schema_version: {self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION}\n"
            + self.module._render_root_semantic_lifecycle_yaml(lifecycle)
            + "\n  entries:\n    - marker: true\n"
            "reference_semantic_dispositions:\n  schema_version: 2\n  entries: []\n"
        )
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "invalid-preimage.yaml"
            target.write_text(initial, encoding="utf-8")
            before = target.read_bytes()
            with self.assertRaisesRegex(
                self.module.ValidationProblem, "preimage must be lowercase sha256"
            ):
                self.module._replace_root_semantic_lifecycle_block(
                    target,
                    lifecycle,
                    source_schema_version=self.module.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                    expected_preimage_sha256="bad",
                )
            with self.assertRaisesRegex(
                self.module.ValidationProblem, "source schema line is missing"
            ):
                self.module._replace_root_semantic_lifecycle_block(
                    target,
                    lifecycle,
                    source_schema_version=self.module.ROOT_SEMANTIC_PREVIOUS_DISPOSITION_SCHEMA_VERSION,
                    expected_preimage_sha256=hashlib.sha256(before).hexdigest(),
                )
            self.assertEqual(before, target.read_bytes())


if __name__ == "__main__":
    unittest.main()
