from __future__ import annotations

import base64
import copy
import glob
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import tracemalloc
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MANIFEST = _load("expert_panel_manifest_fixture", "scripts/expert_panel_manifest.py")
PANEL = _load("expert_panel_manifest_panel_fixture", "scripts/expert_panel_review.py")

READABILITY_ROOT = (
    ROOT / "evals/expert-panel/readability-panel-2026-07-18-r9"
)
PROFESSIONAL_ROOT = (
    ROOT / "evals/expert-panel/professional-completeness-panel-2026-07-18-r9"
)
HISTORICAL_REVIEW_CONTRACT_FINGERPRINT = (
    "88a60c74fa8c47f9b9e5eed6a9caaf9381073057ee806b2dc2d0836709dccdde"
)
LIVE_REVIEW_CONTRACT_FINGERPRINT = (
    "f80ffe96349a5cf35fc5c02ea698ede77e01c892a24fa35b1baecc1d9ec48fa1"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _template_sha256(template: dict) -> str:
    rendered = json.dumps(template, indent=2, ensure_ascii=False) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _blank_template(ballot: dict) -> dict:
    """Return the current builder's unfilled shape without corpus I/O."""

    template = copy.deepcopy(ballot)
    if ballot["schema_version"] == 2:
        for vote in template["content_votes"]:
            vote.update(decision=None, reason_code=None, rationale="")
        for vote in template["readability_votes"]:
            for finding in vote["finding_reviews"]:
                finding.update(decision=None, reason_code=None, rationale="")
        for vote in template["actionability_votes"]:
            vote.update(
                decision=None,
                reason_code=None,
                evidence=[],
                rationale="",
            )
        template["limitations"] = [
            "Unfilled template: every decision, reason code, and rationale must be completed independently before validation."
        ]
        return template

    for claim in template["voter"]["qualification_claims"]:
        claim["qualification_basis"] = ""
        claim["proof_limit"] = ""
    for vote in template["professional_votes"]:
        vote.update(
            decision=None,
            reason_code=None,
            evidence_anchors=[],
            examined_failure_modes=[],
            examined_omission_candidates=[],
            proof_limits=[],
            rationale="",
        )
        vote["criteria"] = {
            criterion: {"status": None, "evidence_assertions": []}
            for criterion in sorted(vote["criteria"])
        }
        vote["examined_adjacent_candidates"] = [
            {
                "skill_id": candidate["skill_id"],
                "review_origin": candidate["review_origin"],
                "discovery_reason": candidate["discovery_reason"],
                "disposition": None,
                "target_anchor_ids": [],
                "candidate_anchor_ids": [],
                "rationale": "",
            }
            for candidate in vote["examined_adjacent_candidates"]
        ]
    template["limitations"] = [
        "Unfilled schema-3 template: every vote is fresh, capsule-scoped, and must be completed independently before validation."
    ]
    return template


def _build_readability_template(packet: dict, packet_sha256: str, ballot: dict) -> dict:
    voter = ballot["voter"]
    # The checked-in r9 packet is intentionally historical relative to the
    # current generated reports.  Patch only the freshness gate while invoking
    # the current canonical builder; ballot semantics are validated separately.
    with mock.patch.object(PANEL, "validate_packet", return_value=packet):
        return PANEL.prepare_readability_ballot_template(
            packet=packet,
            packet_sha256=packet_sha256,
            voter_id=voter["voter_id"],
            agent_id=voter["agent_id"],
            role=voter["role"],
            expertise=voter["expertise"],
            created_on=ballot["created_on"],
        )


def _build_professional_template(packet: dict, packet_sha256: str, ballot: dict) -> dict:
    voter = ballot["voter"]
    return PANEL.prepare_professional_completeness_ballot_template_v3(
        packet=packet,
        packet_sha256=packet_sha256,
        capsule_path=ROOT / ballot["capsule"]["path"],
        voter_id=voter["voter_id"],
        agent_id=voter["agent_id"],
        role=voter["role"],
        expertise=voter["expertise"],
        expertise_tags=voter["expertise_tags"],
        skill_ids=[vote["skill_id"] for vote in ballot["professional_votes"]],
        created_on=ballot["created_on"],
        validation_root=ROOT,
    )


def _roundtrip(ballot: dict, template: dict) -> tuple[list[dict], bytes, dict]:
    digest = _template_sha256(template)
    projected = MANIFEST.project_ballot_to_manifest(
        ballot,
        template_sha256=digest,
    )
    encoded = MANIFEST.encode_manifest_records(projected)
    parsed = MANIFEST.parse_manifest_bytes(encoded)
    candidate = MANIFEST.materialize_manifest(template, parsed)
    if candidate != ballot:
        raise AssertionError("materialized ballot differs from source ballot")
    reprojected = MANIFEST.project_ballot_to_manifest(
        candidate,
        template_sha256=digest,
    )
    if reprojected != projected:
        raise AssertionError("reprojected manifest differs from source records")
    return projected, encoded, candidate


def _chunk_stream(raw: bytes, *, stream_id: str, chunk_size: int = 32_768) -> bytes:
    chunks = [raw[index : index + chunk_size] for index in range(0, len(raw), chunk_size)]
    digest = hashlib.sha256(raw).hexdigest()
    lines = []
    for sequence, chunk in enumerate(chunks):
        envelope = {
            "protocol": MANIFEST.CHUNK_PROTOCOL,
            "version": MANIFEST.CHUNK_PROTOCOL_VERSION,
            "stream_id": stream_id,
            "sequence": sequence,
            "chunk_count": len(chunks),
            "total_raw_bytes": len(raw),
            "manifest_sha256": digest,
            "chunk_raw_sha256": hashlib.sha256(chunk).hexdigest(),
            "payload_base64": base64.b64encode(chunk).decode("ascii"),
        }
        lines.append(
            json.dumps(
                envelope,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    return b"".join(lines)


class _FragmentedStream(io.BytesIO):
    def read(self, size: int = -1) -> bytes:
        return super().read(3 if size < 0 else min(size, 3))


class ExpertPanelManifestRoundtripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readability_packet_path = READABILITY_ROOT / "packet.json"
        cls.readability_packet = _json(cls.readability_packet_path)
        cls.readability_packet_sha256 = _sha256(cls.readability_packet_path)
        cls.readability_ballot_paths = [
            Path(path)
            for path in sorted(
                glob.glob(str(READABILITY_ROOT / "panel/readability-r9-*.json"))
            )
        ]
        cls.professional_packet_path = PROFESSIONAL_ROOT / "packet.json"
        cls.professional_packet = _json(cls.professional_packet_path)
        cls.professional_packet_sha256 = _sha256(cls.professional_packet_path)
        cls.professional_ballot_paths = [
            Path(path)
            for path in sorted(glob.glob(str(PROFESSIONAL_ROOT / "panel/r9-*.json")))
        ]
        cls.readability_ballots = [_json(path) for path in cls.readability_ballot_paths]
        cls.professional_ballots = [
            _json(path) for path in cls.professional_ballot_paths
        ]

    def test_all_three_readability_ballots_roundtrip_exactly(self) -> None:
        self.assertEqual(3, len(self.readability_ballots))
        for path, ballot in zip(
            self.readability_ballot_paths,
            self.readability_ballots,
            strict=True,
        ):
            with self.subTest(ballot=path.name):
                template = _build_readability_template(
                    self.readability_packet,
                    self.readability_packet_sha256,
                    ballot,
                )
                self.assertEqual(_blank_template(ballot), template)
                records, _encoded, candidate = _roundtrip(ballot, template)
                with mock.patch.object(
                    PANEL, "validate_packet", return_value=self.readability_packet
                ):
                    self.assertIs(
                        candidate,
                        PANEL.validate_ballot(
                            self.readability_packet,
                            candidate,
                            packet_sha256=self.readability_packet_sha256,
                        ),
                    )
                self.assertNotIn("classification", records[-1])

    def test_representative_professional_axes_roundtrip_and_validate(self) -> None:
        names = (
            "r9-architecture-platform-arch.json",
            "r9-architecture-platform-d1.json",
            "r9-architecture-platform-d2.json",
        )
        ballots_by_name = {
            path.name: ballot
            for path, ballot in zip(
                self.professional_ballot_paths,
                self.professional_ballots,
                strict=True,
            )
        }
        for name in names:
            with self.subTest(ballot=name):
                ballot = ballots_by_name[name]
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "professional completeness schema-3 review contract is stale",
                ):
                    _build_professional_template(
                        self.professional_packet,
                        self.professional_packet_sha256,
                        ballot,
                    )
                template = _blank_template(ballot)
                records, _encoded, candidate = _roundtrip(ballot, template)
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "professional completeness schema-3 review contract is stale",
                ):
                    PANEL.validate_ballot(
                        self.professional_packet,
                        candidate,
                        packet_sha256=self.professional_packet_sha256,
                        validation_root=ROOT,
                        artifact_path=PROFESSIONAL_ROOT / "panel" / name,
                    )
                for record in records:
                    for candidate_row in record.get(
                        "examined_adjacent_candidates", []
                    ):
                        self.assertNotIn("review_origin", candidate_row)
                        self.assertNotIn("discovery_reason", candidate_row)

    def test_all_42_r9_ballots_fit_deterministic_transport_bounds(self) -> None:
        corpus = [*self.readability_ballots, *self.professional_ballots]
        self.assertEqual(42, len(corpus))
        self.assertEqual(39, len(self.professional_ballots))
        templates = [_blank_template(ballot) for ballot in corpus]
        max_record = 0
        max_manifest = 0
        tracemalloc.start()
        try:
            for ballot, template in zip(corpus, templates, strict=True):
                records = MANIFEST.project_ballot_to_manifest(
                    ballot,
                    template_sha256=_template_sha256(template),
                )
                encoded = MANIFEST.encode_manifest_records(records)
                parsed = MANIFEST.parse_manifest_bytes(encoded)
                candidate = MANIFEST.materialize_manifest(template, parsed)
                self.assertEqual(ballot, candidate)
                max_manifest = max(max_manifest, len(encoded))
                max_record = max(
                    max_record,
                    *(len(line) + 1 for line in encoded.rstrip(b"\n").split(b"\n")),
                )
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLessEqual(max_record, MANIFEST.MAX_RECORD_BYTES)
        self.assertLessEqual(max_manifest, MANIFEST.MAX_MANIFEST_BYTES)
        self.assertLessEqual(peak, 128 * 1024 * 1024)

    def test_largest_current_ballot_stays_within_peak_memory_gate(self) -> None:
        corpus = [*self.readability_ballots, *self.professional_ballots]
        ballot = max(
            corpus,
            key=lambda value: len(
                json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            ),
        )
        template = _blank_template(ballot)
        tracemalloc.start()
        try:
            records = MANIFEST.project_ballot_to_manifest(
                ballot,
                template_sha256=_template_sha256(template),
            )
            encoded = MANIFEST.encode_manifest_records(records)
            parsed = MANIFEST.parse_manifest_bytes(encoded)
            self.assertEqual(
                ballot,
                MANIFEST.materialize_manifest(template, parsed),
            )
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLessEqual(peak, 32 * 1024 * 1024)

    def test_professional_review_contract_fingerprint_is_unchanged(self) -> None:
        self.assertEqual(
            HISTORICAL_REVIEW_CONTRACT_FINGERPRINT,
            self.professional_packet["source_fingerprints"][
                "professional_review_contract"
            ],
        )
        self.assertEqual(
            LIVE_REVIEW_CONTRACT_FINGERPRINT,
            PANEL._professional_evidence_review_contract_fingerprint(),
        )


class ExpertPanelManifestClosedSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        readability_path = (
            READABILITY_ROOT
            / "panel/readability-r9-instruction-actionability.json"
        )
        cls.readability_ballot = _json(readability_path)
        packet_path = READABILITY_ROOT / "packet.json"
        cls.readability_packet = _json(packet_path)
        cls.readability_template = _build_readability_template(
            cls.readability_packet,
            _sha256(packet_path),
            cls.readability_ballot,
        )
        cls.readability_records = MANIFEST.project_ballot_to_manifest(
            cls.readability_ballot,
            template_sha256=_template_sha256(cls.readability_template),
        )
        professional_path = (
            PROFESSIONAL_ROOT / "panel/r9-architecture-platform-d1.json"
        )
        cls.professional_ballot = _json(professional_path)
        cls.professional_template = _blank_template(cls.professional_ballot)
        cls.professional_records = MANIFEST.project_ballot_to_manifest(
            cls.professional_ballot,
            template_sha256=_template_sha256(cls.professional_template),
        )

    def _records(self, *, professional: bool = False) -> list[dict]:
        source = self.professional_records if professional else self.readability_records
        return copy.deepcopy(source)

    @staticmethod
    def _set_count(records: list[dict]) -> list[dict]:
        records[0]["record_count"] = len(records)
        return records

    def test_unknown_and_template_owned_fields_are_rejected(self) -> None:
        mutations = []
        records = self._records()
        records[0]["unknown"] = True
        mutations.append(records)
        records = self._records()
        content = next(
            row for row in records if row["record_type"] == "readability_content_vote"
        )
        content["classification"] = "REVIEW_DENSITY"
        mutations.append(records)
        records = self._records()
        actionability = next(
            row for row in records if row["record_type"] == "actionability_vote"
        )
        actionability["evidence"][0]["unknown"] = "override"
        mutations.append(records)
        records = self._records(professional=True)
        vote = next(row for row in records if row["record_type"] == "professional_vote")
        vote["examined_adjacent_candidates"][0]["review_origin"] = "reviewer-added"
        mutations.append(records)
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.encode_manifest_records(mutation)

    def test_header_overrides_and_invalid_types_are_rejected(self) -> None:
        mutations = []
        for key, value in (
            ("review_id", "different-review"),
            ("created_on", "2026-07-19"),
            ("voter_id", "different-voter"),
            ("packet_sha256", "b" * 64),
            ("ballot_kind", MANIFEST.PROFESSIONAL_BALLOT_KIND),
            ("template_sha256", "b" * 64),
        ):
            records = self._records()
            records[0][key] = value
            mutations.append(records)
        for index, records in enumerate(mutations):
            with self.subTest(binding=index):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.materialize_manifest(self.readability_template, records)
        records = self._records(professional=True)
        records[0]["capsule_sha256"] = "0" * 64
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.materialize_manifest(self.professional_template, records)
        for key, value in (
            ("manifest_schema_version", True),
            ("record_count", True),
            ("capsule_sha256", "a" * 64),
            ("template_sha256", "A" * 64),
        ):
            records = self._records()
            records[0][key] = value
            with self.subTest(type_field=key):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.encode_manifest_records(records)

    def test_cross_axis_and_record_order_are_rejected(self) -> None:
        records = self._records()
        content_index = next(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "readability_content_vote"
        )
        records.insert(
            content_index,
            {
                "record_type": "qualification_claim",
                "expertise_tag": "skill-reference-architecture",
                "qualification_basis": "A sufficiently detailed qualification basis exists here.",
                "proof_limit": "A sufficiently detailed static proof limit exists here.",
            },
        )
        self._set_count(records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(records)

        records = self._records()
        content_indices = [
            index
            for index, row in enumerate(records)
            if row["record_type"] == "readability_content_vote"
        ]
        records[content_indices[0]], records[content_indices[1]] = (
            records[content_indices[1]],
            records[content_indices[0]],
        )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(records)

        records = self._records()
        first_finding = next(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "readability_finding"
        )
        first_actionability = next(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "actionability_vote"
        )
        records[first_finding], records[first_actionability] = (
            records[first_actionability],
            records[first_finding],
        )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(records)

    def test_missing_extra_and_duplicate_readability_identities_are_rejected(self) -> None:
        selectors = (
            "readability_content_vote",
            "readability_finding",
            "actionability_vote",
        )
        for record_type in selectors:
            records = self._records()
            index = next(
                index
                for index, row in enumerate(records)
                if row["record_type"] == record_type
            )
            records.pop(index)
            self._set_count(records)
            with self.subTest(missing=record_type):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.materialize_manifest(self.readability_template, records)

            records = self._records()
            index = next(
                index
                for index, row in enumerate(records)
                if row["record_type"] == record_type
            )
            records.insert(index + 1, copy.deepcopy(records[index]))
            self._set_count(records)
            with self.subTest(duplicate=record_type):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.encode_manifest_records(records)

        records = self._records()
        last_content = max(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "readability_content_vote"
        )
        extra = copy.deepcopy(records[last_content])
        extra["path"] = "zz/extra.md"
        records.insert(last_content + 1, extra)
        self._set_count(records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.materialize_manifest(self.readability_template, records)

    def test_missing_extra_and_duplicate_professional_identities_are_rejected(self) -> None:
        records = self._records(professional=True)
        qualification_index = next(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "qualification_claim"
        )
        records.insert(qualification_index + 1, copy.deepcopy(records[qualification_index]))
        self._set_count(records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(records)

        records = self._records(professional=True)
        vote_index = next(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "professional_vote"
        )
        records.insert(vote_index + 1, copy.deepcopy(records[vote_index]))
        self._set_count(records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(records)

        records = self._records(professional=True)
        records.pop(vote_index)
        self._set_count(records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.materialize_manifest(self.professional_template, records)

        records = self._records(professional=True)
        last_vote = max(
            index
            for index, row in enumerate(records)
            if row["record_type"] == "professional_vote"
        )
        extra = copy.deepcopy(records[last_vote])
        extra["skill_id"] = "zz-extra-skill"
        records.insert(last_vote + 1, extra)
        self._set_count(records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.materialize_manifest(self.professional_template, records)

    def test_duplicate_professional_nested_identities_are_rejected(self) -> None:
        def vote(records: list[dict]) -> dict:
            return next(
                row for row in records if row["record_type"] == "professional_vote"
            )

        mutations = []
        records = self._records(professional=True)
        vote(records)["evidence_anchors"].append(
            copy.deepcopy(vote(records)["evidence_anchors"][0])
        )
        mutations.append(records)
        records = self._records(professional=True)
        vote(records)["examined_failure_modes"].append(
            copy.deepcopy(vote(records)["examined_failure_modes"][0])
        )
        vote(records)["examined_failure_modes"].sort(key=lambda row: row["failure_mode"])
        mutations.append(records)
        records = self._records(professional=True)
        vote(records)["examined_omission_candidates"].append(
            copy.deepcopy(vote(records)["examined_omission_candidates"][0])
        )
        vote(records)["examined_omission_candidates"].sort(
            key=lambda row: row["omission_candidate"]
        )
        mutations.append(records)
        records = self._records(professional=True)
        vote(records)["examined_adjacent_candidates"].append(
            copy.deepcopy(vote(records)["examined_adjacent_candidates"][0])
        )
        vote(records)["examined_adjacent_candidates"].sort(key=lambda row: row["skill_id"])
        mutations.append(records)
        records = self._records(professional=True)
        vote(records)["proof_limits"].append(vote(records)["proof_limits"][0])
        vote(records)["proof_limits"].sort()
        mutations.append(records)
        records = self._records(professional=True)
        assertion = next(iter(vote(records)["criteria"].values()))[
            "evidence_assertions"
        ][0]
        assertion["evidence_anchor_ids"].append(assertion["evidence_anchor_ids"][0])
        assertion["evidence_anchor_ids"].sort()
        mutations.append(records)
        for index, records in enumerate(mutations):
            with self.subTest(nested_identity=index):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.encode_manifest_records(records)

    def test_invalid_utf8_and_noncanonical_jsonl_are_rejected(self) -> None:
        raw = MANIFEST.encode_manifest_records(self.readability_records)
        invalid_values = (
            b"\xff\n",
            b"\xef\xbb\xbf" + raw,
            raw.replace(b"\n", b"\r\n"),
            raw[:-1],
            raw.split(b"\n", 1)[0] + b"\n\n" + raw.split(b"\n", 1)[1],
            b" " + raw,
            b'{"record_type":"header","value":NaN}\n',
            b'{"record_type":"header","value":"\\ud800"}\n',
        )
        for index, value in enumerate(invalid_values):
            with self.subTest(invalid=index):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.parse_manifest_bytes(value)

    def test_duplicate_json_keys_are_rejected_recursively(self) -> None:
        values = (
            b'{"record_type":"header","record_type":"header"}\n',
            b'{"evidence":{"claim":"first","claim":"second"}}\n',
        )
        for value in values:
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.parse_manifest_bytes(value)

    def test_record_and_manifest_size_limits_are_enforced(self) -> None:
        records = self._records()
        limitation = next(row for row in records if row["record_type"] == "limitation")
        limitation["text"] = "x" * MANIFEST.MAX_RECORD_BYTES
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(records)

        header = copy.deepcopy(self.readability_records[0])
        large_records = [header]
        for ordinal in range(68):
            large_records.append(
                {
                    "record_type": "limitation",
                    "ordinal": ordinal,
                    "text": "x" * 250_000,
                }
            )
        header["record_count"] = len(large_records)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(large_records)

    def test_unicode_and_embedded_newlines_are_lossless(self) -> None:
        ballot = copy.deepcopy(self.readability_ballot)
        ballot["limitations"] = ["范围 café αβ 雪 🚀\nsecond line remains exact"]
        ballot["content_votes"][0]["rationale"] = (
            "Unicode café 雪 🚀 remains exact.\nThe second line remains reviewer text."
        )
        records, encoded, candidate = _roundtrip(ballot, self.readability_template)
        self.assertEqual(ballot, candidate)
        self.assertIn("雪".encode("utf-8"), encoded)
        self.assertIn(b"\\nThe second line", encoded)
        self.assertEqual(records, MANIFEST.parse_manifest_bytes(encoded))

    def test_materialized_ballots_never_receive_manifest_fields(self) -> None:
        _records, _encoded, candidate = _roundtrip(
            self.professional_ballot,
            self.professional_template,
        )
        forbidden = {
            "record_type",
            "manifest_kind",
            "manifest_schema_version",
            "panel_kind",
            "template_sha256",
            "record_count",
        }

        def walk(value: object) -> None:
            if isinstance(value, dict):
                self.assertFalse(forbidden & set(value))
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(candidate)


class ExpertPanelManifestTransportAndFinalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packet_path = READABILITY_ROOT / "packet.json"
        cls.packet = _json(cls.packet_path)
        cls.packet_sha256 = _sha256(cls.packet_path)
        cls.ballot = _json(
            READABILITY_ROOT
            / "panel/readability-r9-instruction-actionability.json"
        )
        cls.template = _build_readability_template(
            cls.packet,
            cls.packet_sha256,
            cls.ballot,
        )
        cls.template_raw = MANIFEST.canonical_ballot_bytes(
            cls.template,
            compact=False,
        )
        cls.records = MANIFEST.project_ballot_to_manifest(
            cls.ballot,
            template_sha256=hashlib.sha256(cls.template_raw).hexdigest(),
        )
        cls.manifest_raw = MANIFEST.encode_manifest_records(cls.records)
        cls.manifest_sha256 = hashlib.sha256(cls.manifest_raw).hexdigest()
        header = cls.records[0]
        cls.stream_id = f"{header['review_id']}:{header['voter_id']}"

    def test_file_raw_and_fragmented_chunk_transports_are_byte_exact(self) -> None:
        raw_result = MANIFEST.read_raw_manifest_stream(
            _FragmentedStream(self.manifest_raw),
            expected_size=len(self.manifest_raw),
            expected_sha256=self.manifest_sha256,
        )
        framed = _chunk_stream(
            self.manifest_raw,
            stream_id=self.stream_id,
        )
        framed_result = MANIFEST.read_framed_manifest_stream(
            _FragmentedStream(framed),
            expected_size=len(self.manifest_raw),
            expected_sha256=self.manifest_sha256,
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "reviewer-manifest.jsonl"
            path.write_bytes(self.manifest_raw)
            file_result = MANIFEST.read_manifest_file(
                path,
                expected_size=len(self.manifest_raw),
                expected_sha256=self.manifest_sha256,
                repository_root=ROOT,
            )
        self.assertEqual(self.manifest_raw, raw_result)
        self.assertEqual(raw_result, framed_result)
        self.assertEqual(framed_result, file_result)

    def test_deeply_nested_template_recursion_fails_closed_before_create(self) -> None:
        voter_id = self.ballot["voter"]["voter_id"]
        nested_text = '{"nested":' + "[" * 2_048 + "0" + "]" * 2_048 + "}"
        nested_raw = nested_text.encode("utf-8")
        original_loads = json.loads

        def recurse_on_nested(value, *args, **kwargs):
            if value == nested_text:
                raise RecursionError("injected JSON nesting limit")
            return original_loads(value, *args, **kwargs)

        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            template_path = scratch / f"{voter_id}.template.json"
            output_path = scratch / f"{voter_id}.json"
            manifest_path = scratch / "manifest.jsonl"
            template_path.write_bytes(nested_raw)
            manifest_path.write_bytes(self.manifest_raw)
            arguments = [
                "materialize-ballot",
                "--packet",
                str(self.packet_path),
                "--template",
                str(template_path),
                "--template-sha256",
                hashlib.sha256(nested_raw).hexdigest(),
                "--manifest",
                str(manifest_path),
                "--manifest-size",
                str(len(self.manifest_raw)),
                "--manifest-sha256",
                self.manifest_sha256,
                "--stdin-framing",
                "raw",
                "--out",
                str(output_path),
            ]
            stdout = io.StringIO()
            with mock.patch.object(
                PANEL,
                "validate_packet",
                return_value=self.packet,
            ), mock.patch.object(
                PANEL.reviewer_manifest.json,
                "loads",
                side_effect=recurse_on_nested,
            ), mock.patch.object(sys, "stdout", stdout):
                result = PANEL.main(arguments)

            self.assertNotEqual(0, result)
            self.assertIn("ballot template is not strict UTF-8 JSON", stdout.getvalue())
            self.assertNotIn("Traceback", stdout.getvalue())
            self.assertFalse(output_path.exists())
            self.assertEqual(nested_raw, template_path.read_bytes())
            self.assertEqual([], list(scratch.glob(".*.materialize*")))

    def test_deeply_nested_framed_envelope_recursion_fails_closed(self) -> None:
        voter_id = self.ballot["voter"]["voter_id"]
        nested_text = '{"nested":' + "[" * 2_048 + "0" + "]" * 2_048 + "}"
        framed_raw = nested_text.encode("utf-8") + b"\n"
        original_loads = json.loads

        def recurse_on_nested(value, *args, **kwargs):
            if value == nested_text:
                raise RecursionError("injected JSON nesting limit")
            return original_loads(value, *args, **kwargs)

        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            template_path = scratch / f"{voter_id}.template.json"
            output_path = scratch / f"{voter_id}.json"
            template_path.write_bytes(self.template_raw)
            arguments = [
                "materialize-ballot",
                "--packet",
                str(self.packet_path),
                "--template",
                str(template_path),
                "--template-sha256",
                hashlib.sha256(self.template_raw).hexdigest(),
                "--manifest",
                "-",
                "--manifest-size",
                str(len(self.manifest_raw)),
                "--manifest-sha256",
                self.manifest_sha256,
                "--stdin-framing",
                "changeforge-base64-chunks-v1",
                "--out",
                str(output_path),
            ]
            stdout = io.StringIO()
            stdin = mock.Mock(buffer=io.BytesIO(framed_raw))
            with mock.patch.object(
                PANEL,
                "validate_packet",
                return_value=self.packet,
            ), mock.patch.object(
                PANEL.reviewer_manifest.json,
                "loads",
                side_effect=recurse_on_nested,
            ), mock.patch.object(sys, "stdin", stdin), mock.patch.object(
                sys,
                "stdout",
                stdout,
            ):
                result = PANEL.main(arguments)

            self.assertNotEqual(0, result)
            self.assertIn(
                "reviewer manifest chunk 0 is not strict UTF-8 JSON",
                stdout.getvalue(),
            )
            self.assertNotIn("Traceback", stdout.getvalue())
            self.assertFalse(output_path.exists())
            self.assertEqual(self.template_raw, template_path.read_bytes())
            self.assertEqual([], list(scratch.glob(".*.materialize*")))

    def test_manifest_size_digest_and_external_file_guards_fail_closed(self) -> None:
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_raw_manifest_stream(
                io.BytesIO(self.manifest_raw),
                expected_size=len(self.manifest_raw) + 1,
                expected_sha256=self.manifest_sha256,
            )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_raw_manifest_stream(
                io.BytesIO(self.manifest_raw),
                expected_size=len(self.manifest_raw),
                expected_sha256="0" * 64,
            )
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "manifest.jsonl"
            path.write_bytes(self.manifest_raw)
            symlink = directory / "manifest-link.jsonl"
            symlink.symlink_to(path)
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_manifest_file(
                    symlink,
                    expected_size=len(self.manifest_raw),
                    expected_sha256=self.manifest_sha256,
                    repository_root=ROOT,
                )
            hardlink = directory / "manifest-hardlink.jsonl"
            os.link(path, hardlink)
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_manifest_file(
                    path,
                    expected_size=len(self.manifest_raw),
                    expected_sha256=self.manifest_sha256,
                    repository_root=ROOT,
                )
            hardlink.unlink()
            parent_link = directory / "parent-link"
            actual_parent = directory / "actual-parent"
            actual_parent.mkdir()
            nested = actual_parent / "nested.jsonl"
            nested.write_bytes(self.manifest_raw)
            parent_link.symlink_to(actual_parent, target_is_directory=True)
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_manifest_file(
                    parent_link / nested.name,
                    expected_size=len(self.manifest_raw),
                    expected_sha256=self.manifest_sha256,
                    repository_root=ROOT,
                )
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            inside = Path(raw) / "manifest.jsonl"
            inside.write_bytes(self.manifest_raw)
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_manifest_file(
                    inside,
                    expected_size=len(self.manifest_raw),
                    expected_sha256=self.manifest_sha256,
                    repository_root=ROOT,
                )

    def test_chunk_protocol_rejects_missing_reordered_mixed_and_corrupt_data(self) -> None:
        framed = _chunk_stream(
            self.manifest_raw,
            stream_id=self.stream_id,
            chunk_size=max(1, len(self.manifest_raw) // 3),
        )
        lines = framed.rstrip(b"\n").split(b"\n")
        self.assertGreaterEqual(len(lines), 3)
        mutations: list[bytes] = []
        mutations.append(b"\n".join(lines[:-1]) + b"\n")
        mutations.append(b"\n".join([lines[1], lines[0], *lines[2:]]) + b"\n")
        values = [json.loads(line) for line in lines]
        mixed = copy.deepcopy(values)
        mixed[1]["stream_id"] = "different-review:different-voter"
        mutations.append(
            b"".join(
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
                + b"\n"
                for value in mixed
            )
        )
        corrupt = copy.deepcopy(values)
        corrupt[0]["payload_base64"] = (
            "A" + corrupt[0]["payload_base64"][1:]
        )
        mutations.append(
            b"".join(
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
                + b"\n"
                for value in corrupt
            )
        )
        stale_chunk = copy.deepcopy(values)
        stale_chunk[0]["chunk_raw_sha256"] = "0" * 64
        mutations.append(
            b"".join(
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
                + b"\n"
                for value in stale_chunk
            )
        )
        stale_whole = copy.deepcopy(values)
        stale_whole[0]["manifest_sha256"] = "0" * 64
        mutations.append(
            b"".join(
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
                + b"\n"
                for value in stale_whole
            )
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(fault=index), self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_framed_manifest_stream(
                    _FragmentedStream(mutation),
                    expected_size=len(self.manifest_raw),
                    expected_sha256=self.manifest_sha256,
                )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_framed_manifest_stream(
                io.BytesIO(framed[:-1]),
                expected_size=len(self.manifest_raw),
                expected_sha256=self.manifest_sha256,
            )

    def test_schema2_cli_is_create_only_and_preserves_scratch_template(self) -> None:
        voter_id = self.ballot["voter"]["voter_id"]
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            template_path = scratch / f"{voter_id}.template.json"
            output_path = scratch / f"{voter_id}.json"
            manifest_path = scratch / "manifest.jsonl"
            template_path.write_bytes(self.template_raw)
            manifest_path.write_bytes(self.manifest_raw)
            original = template_path.read_bytes()
            arguments = [
                "materialize-ballot",
                "--packet",
                str(self.packet_path),
                "--template",
                str(template_path),
                "--template-sha256",
                hashlib.sha256(original).hexdigest(),
                "--manifest",
                str(manifest_path),
                "--manifest-size",
                str(len(self.manifest_raw)),
                "--manifest-sha256",
                self.manifest_sha256,
                "--stdin-framing",
                "raw",
                "--out",
                str(output_path),
            ]
            with mock.patch.object(
                PANEL,
                "validate_packet",
                return_value=self.packet,
            ):
                wrong_path = copy.deepcopy(arguments)
                wrong_path[-1] = str(scratch / "wrong-output.json")
                self.assertEqual(1, PANEL.main(wrong_path))
                wrong_template_sha = copy.deepcopy(arguments)
                wrong_template_sha[
                    wrong_template_sha.index("--template-sha256") + 1
                ] = "0" * 64
                self.assertEqual(1, PANEL.main(wrong_template_sha))

                invalid_records = copy.deepcopy(self.records)
                invalid_actionability = next(
                    record
                    for record in invalid_records
                    if record["record_type"] == "actionability_vote"
                )
                invalid_actionability["evidence"][0]["source_line"] += " altered"
                invalid_manifest = MANIFEST.encode_manifest_records(invalid_records)
                manifest_path.write_bytes(invalid_manifest)
                invalid_arguments = copy.deepcopy(arguments)
                invalid_arguments[
                    invalid_arguments.index("--manifest-size") + 1
                ] = str(len(invalid_manifest))
                invalid_arguments[
                    invalid_arguments.index("--manifest-sha256") + 1
                ] = hashlib.sha256(invalid_manifest).hexdigest()
                self.assertEqual(1, PANEL.main(invalid_arguments))
                self.assertFalse(output_path.exists())
                self.assertEqual(original, template_path.read_bytes())

                manifest_path.write_bytes(self.manifest_raw)
                self.assertEqual(0, PANEL.main(arguments))
                self.assertEqual(1, PANEL.main(arguments))
            self.assertEqual(original, template_path.read_bytes())
            self.assertEqual(self.ballot, _json(output_path))
            self.assertFalse(
                any(
                    key.startswith("manifest_") or key == "record_type"
                    for key in _json(output_path)
                )
            )

    def test_noncanonical_template_bytes_fail_before_schema2_create(self) -> None:
        voter_id = self.ballot["voter"]["voter_id"]
        template_value = json.loads(self.template_raw.decode("utf-8"))
        reordered_value = dict(reversed(list(template_value.items())))
        variants = {
            "trailing-whitespace": self.template_raw + b" ",
            "reordered-keys": MANIFEST.canonical_ballot_bytes(
                reordered_value,
                compact=False,
            ),
            "duplicate-key": self.template_raw.replace(
                b"{\n",
                b'{\n  "schema_version": 2,\n',
                1,
            ),
            "duplicate-nested-key": self.template_raw.replace(
                b'  "voter": {\n',
                (
                    b'  "voter": {\n    "voter_id": "'
                    + voter_id.encode("utf-8")
                    + b'",\n'
                ),
                1,
            ),
        }
        for label, altered_raw in variants.items():
            self.assertNotEqual(self.template_raw, altered_raw)
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                scratch = Path(raw)
                template_path = scratch / f"{voter_id}.template.json"
                output_path = scratch / f"{voter_id}.json"
                manifest_path = scratch / "manifest.jsonl"
                template_path.write_bytes(altered_raw)
                altered_digest = hashlib.sha256(altered_raw).hexdigest()
                records = copy.deepcopy(self.records)
                records[0]["template_sha256"] = altered_digest
                manifest_raw = MANIFEST.encode_manifest_records(records)
                manifest_path.write_bytes(manifest_raw)
                arguments = [
                    "materialize-ballot",
                    "--packet",
                    str(self.packet_path),
                    "--template",
                    str(template_path),
                    "--template-sha256",
                    altered_digest,
                    "--manifest",
                    str(manifest_path),
                    "--manifest-size",
                    str(len(manifest_raw)),
                    "--manifest-sha256",
                    hashlib.sha256(manifest_raw).hexdigest(),
                    "--stdin-framing",
                    "raw",
                    "--out",
                    str(output_path),
                ]
                with mock.patch.object(
                    PANEL,
                    "validate_packet",
                    return_value=self.packet,
                ):
                    self.assertEqual(1, PANEL.main(arguments))
                self.assertFalse(output_path.exists())
                self.assertEqual(altered_raw, template_path.read_bytes())
                self.assertEqual([], list(scratch.glob(".*.materialize*")))

    def test_manifest_header_binds_raw_template_before_materialization(self) -> None:
        voter_id = self.ballot["voter"]["voter_id"]
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            template_path = scratch / f"{voter_id}.template.json"
            output_path = scratch / f"{voter_id}.json"
            manifest_path = scratch / "manifest.jsonl"
            template_path.write_bytes(self.template_raw)
            records = copy.deepcopy(self.records)
            records[0]["template_sha256"] = "0" * 64
            manifest_raw = MANIFEST.encode_manifest_records(records)
            manifest_path.write_bytes(manifest_raw)
            arguments = [
                "materialize-ballot",
                "--packet",
                str(self.packet_path),
                "--template",
                str(template_path),
                "--template-sha256",
                hashlib.sha256(self.template_raw).hexdigest(),
                "--manifest",
                str(manifest_path),
                "--manifest-size",
                str(len(manifest_raw)),
                "--manifest-sha256",
                hashlib.sha256(manifest_raw).hexdigest(),
                "--stdin-framing",
                "raw",
                "--out",
                str(output_path),
            ]
            with mock.patch.object(
                PANEL,
                "validate_packet",
                return_value=self.packet,
            ), mock.patch.object(
                PANEL.reviewer_manifest,
                "materialize_manifest",
            ) as materialize:
                self.assertEqual(1, PANEL.main(arguments))
            materialize.assert_not_called()
            self.assertFalse(output_path.exists())
            self.assertEqual(self.template_raw, template_path.read_bytes())
            self.assertEqual([], list(scratch.glob(".*.materialize*")))

    def test_schema2_create_and_schema3_replace_faults_cleanup_only_owned_files(self) -> None:
        final_value = {"kind": "final", "value": "validated"}
        final_raw = MANIFEST.canonical_ballot_bytes(final_value, compact=True)
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            template = directory / "voter.json"
            template.write_bytes(b"template\n")
            bound = MANIFEST.bind_regular_file(
                template,
                expected_sha256=hashlib.sha256(template.read_bytes()).hexdigest(),
                label="test template",
            )
            with mock.patch.object(MANIFEST.os, "replace", side_effect=OSError("fault")):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.replace_bound_ballot_once(
                        bound,
                        final_raw,
                        validate_final=lambda value: self.assertEqual(final_value, value),
                    )
            self.assertEqual(b"template\n", template.read_bytes())
            self.assertEqual([], list(directory.glob(".*.materialize-*.tmp")))
            self.assertFalse((directory / ".voter.json.materialize.lock").exists())

            lock = directory / ".voter.json.materialize.lock"
            lock.write_bytes(b"other-owner")
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.replace_bound_ballot_once(
                    bound,
                    final_raw,
                    validate_final=lambda _value: None,
                )

            post_template = directory / "post-validation.json"
            post_template.write_bytes(b"template\n")
            post_bound = MANIFEST.bind_regular_file(
                post_template,
                expected_sha256=hashlib.sha256(
                    post_template.read_bytes()
                ).hexdigest(),
                label="post-validation template",
            )

            def reject_final(_value: dict) -> None:
                raise MANIFEST.ManifestError("injected final validation failure")

            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.replace_bound_ballot_once(
                    post_bound,
                    final_raw,
                    validate_final=reject_final,
                )
            self.assertEqual(final_raw, post_template.read_bytes())
            post_lock = directory / ".post-validation.json.materialize.lock"
            self.assertTrue(post_lock.exists())
            post_lock.unlink()
            self.assertEqual(b"other-owner", lock.read_bytes())
            lock.unlink()

            original_write = MANIFEST._write_all

            def fail_nonempty(descriptor: int, payload: bytes) -> None:
                if payload:
                    raise OSError("injected temporary write failure")
                original_write(descriptor, payload)

            with mock.patch.object(MANIFEST, "_write_all", side_effect=fail_nonempty):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.replace_bound_ballot_once(
                        bound,
                        final_raw,
                        validate_final=lambda _value: None,
                    )
            self.assertEqual(b"template\n", template.read_bytes())
            self.assertEqual([], list(directory.glob(".*.materialize-*.tmp")))
            self.assertFalse(lock.exists())

            MANIFEST.replace_bound_ballot_once(
                bound,
                final_raw,
                validate_final=lambda value: self.assertEqual(final_value, value),
            )
            self.assertEqual(final_raw, template.read_bytes())
            self.assertFalse(lock.exists())
            self.assertEqual([], list(directory.glob(".*.materialize-*.tmp")))
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.replace_bound_ballot_once(
                    bound,
                    final_raw,
                    validate_final=lambda _value: None,
                )

    def test_concurrent_template_swap_is_detected_before_replace(self) -> None:
        final_raw = b'{"kind":"final"}\n'
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            template = directory / "voter.json"
            template.write_bytes(b"template\n")
            bound = MANIFEST.bind_regular_file(
                template,
                expected_sha256=hashlib.sha256(template.read_bytes()).hexdigest(),
                label="test template",
            )
            original_recheck = MANIFEST._recheck_bound_at
            calls = 0

            def swap_on_last_check(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    template.write_bytes(b"concurrent swap\n")
                return original_recheck(*args, **kwargs)

            with mock.patch.object(
                MANIFEST,
                "_recheck_bound_at",
                side_effect=swap_on_last_check,
            ):
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.replace_bound_ballot_once(
                        bound,
                        final_raw,
                        validate_final=lambda _value: None,
                    )
            self.assertEqual(b"concurrent swap\n", template.read_bytes())
            self.assertFalse((directory / ".voter.json.materialize.lock").exists())
            self.assertEqual([], list(directory.glob(".*.materialize-*.tmp")))

    def test_cli_rejects_semantic_schema1_and_professional_schema2_packets(self) -> None:
        packets = (
            {"kind": PANEL.PACKET_KIND, "schema_version": 1},
            {"kind": PANEL.SEMANTIC_DISPOSITION_PACKET_KIND, "schema_version": 1},
            {
                "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                "schema_version": 2,
            },
        )
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            for index, packet in enumerate(packets):
                packet_path = directory / f"packet-{index}.json"
                packet_path.write_text(json.dumps(packet), encoding="utf-8")
                with self.subTest(packet=index):
                    self.assertEqual(
                        1,
                        PANEL.main(
                            [
                                "materialize-ballot",
                                "--packet",
                                str(packet_path),
                                "--template",
                                str(directory / "missing.template.json"),
                                "--template-sha256",
                                "0" * 64,
                                "--manifest",
                                "-",
                                "--manifest-size",
                                "1",
                                "--manifest-sha256",
                                "0" * 64,
                                "--stdin-framing",
                                "raw",
                                "--out",
                                str(directory / "missing.json"),
                            ]
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
