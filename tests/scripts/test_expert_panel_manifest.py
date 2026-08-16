from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import tracemalloc
import unittest
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_completeness_test_support as professional_support

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


import expert_panel_manifest as MANIFEST

PANEL = source_support.PANEL

def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _template_sha256(template: dict) -> str:
    rendered = json.dumps(template, indent=2, ensure_ascii=False) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _blank_template(ballot: dict) -> dict:
    """Return the current builder's unfilled shape without corpus I/O."""

    template = copy.deepcopy(ballot)
    if ballot["kind"] == PANEL.SEMANTIC_DISPOSITION_BALLOT_KIND:
        for vote in template["semantic_votes"]:
            vote.update(
                disposition=None,
                rationale="",
                authority_or_condition="",
                decision_owner="",
                mitigation="",
                review_after=None,
            )
        template["limitations"] = [
            "Unfilled template: every decision and rationale must be completed independently before validation."
        ]
        return template
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


def _semantic_ballot_fixture() -> dict:
    votes = [
        {
            "target_id": f"reference:{'a' * 64}",
            "axis": "reference",
            "candidate_id": "a" * 64,
            "disposition": "false-positive",
            "rationale": (
                "The complete candidate evidence shows a detector-only grouping."
            ),
            "authority_or_condition": (
                "The bounded Reference grouping and exception contract apply."
            ),
            "decision_owner": "semantic-reference-owner",
            "mitigation": "Re-review when detector or source evidence changes.",
            "review_after": None,
        },
        {
            "target_id": f"root:{'b' * 64}",
            "axis": "root",
            "candidate_id": "b" * 64,
            "disposition": "valid-contextual-rule",
            "rationale": (
                "The complete candidate evidence supports a bounded Root rule."
            ),
            "authority_or_condition": (
                "The current Root governance boundary remains authoritative."
            ),
            "decision_owner": "semantic-root-owner",
            "mitigation": "Re-review when detector or source evidence changes.",
            "review_after": None,
        },
    ]
    return {
        "schema_version": 2,
        "kind": PANEL.SEMANTIC_DISPOSITION_BALLOT_KIND,
        "review_id": "semantic-manifest-review",
        "created_on": "2026-08-10",
        "packet_sha256": "c" * 64,
        "source_fingerprints": {"semantic": "d" * 64},
        "voter": {
            "voter_id": "semantic-manifest-voter",
            "agent_id": "semantic-manifest-agent",
            "role": "senior-semantic-reviewer",
            "expertise": ["Semantic boundary governance."],
            "independent_review": True,
        },
        "semantic_votes": votes,
        "limitations": ["Static reviewer evidence does not prove runtime behavior."],
    }


def _readability_packet_fixture() -> dict:
    return {
        "schema_version": 2,
        "kind": PANEL.PACKET_KIND,
        "review_id": "readability-manifest-review",
        "created_on": "2026-08-10",
        "source_fingerprints": {
            "reference_content": "a" * 64,
            "root_content": "b" * 64,
            "ai_readability": "c" * 64,
            "skill_detector": "d" * 64,
        },
        "panel_contract": {},
        "rubric": {},
        "content_targets": [
            {
                "path": "src/foundation/capabilities/fixture-a/SKILL.md",
                "classification": "REVIEW_DENSITY",
            },
            {
                "path": "src/foundation/capabilities/fixture-b/SKILL.md",
                "classification": "REVIEW_DENSITY",
            }
        ],
        "readability_targets": [
            {
                "document_id": "src/foundation/capabilities/fixture/SKILL.md#body",
                "highest_band": "review-as-complex",
                "findings": [
                    {
                        "finding_id": "e" * 64,
                        "sentence_fingerprint": "f" * 64,
                    }
                ],
            }
        ],
        "actionability_targets": [
            {
                "target_id": "fixture-actionability-target",
                "front_window": {
                    "start_line": 1,
                    "end_line": 1,
                    "line_count": 1,
                    "lines": [
                        {
                            "line": 1,
                            "text": (
                                "Run the bounded fixture with explicit verification steps."
                            ),
                        }
                    ],
                    "sha256": hashlib.sha256(
                        b"Run the bounded fixture with explicit verification steps."
                    ).hexdigest(),
                },
            }
        ],
        "limitations": ["Synthetic manifest fixture."],
    }


def _readability_ballot_fixture(packet: dict, *, voter: int) -> dict:
    return {
        "schema_version": 2,
        "kind": PANEL.BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": packet["created_on"],
        "packet_sha256": hashlib.sha256(
            json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "source_fingerprints": copy.deepcopy(packet["source_fingerprints"]),
        "voter": {
            "voter_id": f"readability-manifest-voter-{voter}",
            "agent_id": f"readability-manifest-agent-{voter}",
            "role": f"senior-readability-reviewer-{voter}",
            "expertise": ["AI instruction readability and actionability."],
            "independent_review": True,
        },
        "content_votes": [
            {
                "path": target["path"],
                "classification": "REVIEW_DENSITY",
                "decision": "accepted-current-density",
                "reason_code": "bounded-density-preserves-professional-coverage",
                "rationale": "The bounded fixture remains one coherent decision.",
            }
            for target in packet["content_targets"]
        ],
        "readability_votes": [
            {
                "document_id": packet["readability_targets"][0]["document_id"],
                "highest_band": "review-as-complex",
                "finding_reviews": [
                    {
                        **packet["readability_targets"][0]["findings"][0],
                        "decision": "accepted-current-readability",
                        "reason_code": "single-indivisible-decision",
                        "rationale": "The sentence expresses one indivisible decision.",
                    }
                ],
            }
        ],
        "actionability_votes": [
            {
                "target_id": packet["actionability_targets"][0]["target_id"],
                "decision": "accepted-current-actionability",
                "reason_code": "explicit-domain-actions-are-front-loaded",
                "evidence": [
                    {
                        "line": 1,
                        "source_line": (
                            "Run the bounded fixture with explicit verification steps."
                        ),
                        "claim": "Run explicit verification steps for the fixture.",
                    }
                ],
                "rationale": "The first line names the executable action.",
            }
        ],
        "limitations": ["Synthetic manifest fixture vote."],
    }


def _professional_ballot_fixture(*, voter: int) -> dict:
    packet = professional_support._professional_packet()
    skill_id = packet["professional_targets"][0]["skill_id"]
    ballot = professional_support._professional_ballot(
        packet,
        "9" * 64,
        voter=voter,
        reviewer_kind="domain",
        skill_ids=[skill_id],
    )
    ballot["schema_version"] = 3
    ballot.pop("source_fingerprints")
    ballot["review_contract_fingerprint"] = (
        PANEL._professional_evidence_review_contract_fingerprint()
    )
    ballot["capsule"] = {
        "path": (
            ".rd-skills/expert-panel/professional-manifest-review/capsules/"
            f"professional-expert-{voter}.json"
        ),
        "sha256": hashlib.sha256(
            f"professional-manifest-capsule-{voter}".encode()
        ).hexdigest(),
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
        "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": ballot["review_id"],
    }
    return ballot


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


class ExpertPanelSemanticManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ballot = _semantic_ballot_fixture()
        cls.template = _blank_template(cls.ballot)
        cls.template_sha256 = _template_sha256(cls.template)

    def _records(self) -> list[dict]:
        return MANIFEST.project_ballot_to_manifest(
            copy.deepcopy(self.ballot),
            template_sha256=self.template_sha256,
        )

    def test_semantic_schema2_roundtrips_exactly(self) -> None:
        records, encoded, candidate = _roundtrip(self.ballot, self.template)
        self.assertEqual(self.ballot, candidate)
        self.assertEqual(
            ["header", "limitation", "semantic_vote", "semantic_vote"],
            [row["record_type"] for row in records],
        )
        self.assertIsNone(records[0]["capsule_sha256"])
        self.assertEqual(encoded, MANIFEST.encode_manifest_records(records))

    def test_semantic_schema1_ballot_template_and_header_are_rejected(self) -> None:
        legacy_ballot = copy.deepcopy(self.ballot)
        legacy_ballot["schema_version"] = 1
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.project_ballot_to_manifest(
                legacy_ballot,
                template_sha256=self.template_sha256,
            )

        records = self._records()
        legacy_template = copy.deepcopy(self.template)
        legacy_template["schema_version"] = 1
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.materialize_manifest(legacy_template, records)

        legacy_header = copy.deepcopy(records)
        legacy_header[0]["ballot_schema_version"] = 1
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.encode_manifest_records(legacy_header)

    def test_zero_target_semantic_manifest_roundtrips_and_validates_current(self) -> None:
        audit = _json(ROOT / "reports" / "skill-content-audit.json")
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=audit,
            review_id="semantic-zero-manifest-review",
            created_on="2026-08-10",
        )
        self.assertEqual([], packet["semantic_targets"])
        self.assertIs(
            packet,
            PANEL.validate_semantic_packet_current(packet, audit),
        )
        packet_raw = (
            json.dumps(packet, indent=2, ensure_ascii=False).encode("utf-8")
            + b"\n"
        )
        packet_sha256 = hashlib.sha256(packet_raw).hexdigest()
        template = PANEL.prepare_semantic_ballot_template(
            packet=packet,
            packet_sha256=packet_sha256,
            voter_id="semantic-zero-manifest-voter",
            agent_id="semantic-zero-manifest-agent",
            role="senior-semantic-reviewer",
            expertise=["Semantic boundary governance."],
            created_on="2026-08-10",
        )

        records, encoded, candidate = _roundtrip(template, template)

        self.assertEqual(["header", "limitation"], [
            row["record_type"] for row in records
        ])
        self.assertEqual(2, records[0]["record_count"])
        self.assertEqual(records, MANIFEST.parse_manifest_bytes(encoded))
        self.assertEqual([], candidate["semantic_votes"])
        self.assertIs(
            candidate,
            PANEL.validate_ballot(
                packet,
                candidate,
                packet_sha256=packet_sha256,
            ),
        )

        invalid_records = []
        wrong_count = copy.deepcopy(records)
        wrong_count[0]["record_count"] = 3
        invalid_records.append(wrong_count)
        missing_limitation = [copy.deepcopy(records[0])]
        missing_limitation[0]["record_count"] = 1
        invalid_records.append(missing_limitation)
        extra_field = copy.deepcopy(records)
        extra_field[1]["unexpected"] = True
        invalid_records.append(extra_field)
        for mutation in invalid_records:
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.encode_manifest_records(mutation)

    def test_semantic_identity_coverage_and_order_are_template_bound(self) -> None:
        records = self._records()
        vote_indexes = [
            index
            for index, row in enumerate(records)
            if row["record_type"] == "semantic_vote"
        ]
        mutations: list[tuple[str, list[dict], bool]] = []

        missing = copy.deepcopy(records)
        missing.pop(vote_indexes[-1])
        missing[0]["record_count"] = len(missing)
        mutations.append(("missing", missing, False))

        duplicate = copy.deepcopy(records)
        duplicate.insert(vote_indexes[-1], copy.deepcopy(duplicate[vote_indexes[0]]))
        duplicate[0]["record_count"] = len(duplicate)
        mutations.append(("duplicate", duplicate, True))

        extra = copy.deepcopy(records)
        extra_vote = copy.deepcopy(extra[vote_indexes[-1]])
        extra_vote.update(
            target_id=f"root:{'e' * 64}",
            candidate_id="e" * 64,
        )
        extra.append(extra_vote)
        extra[0]["record_count"] = len(extra)
        mutations.append(("extra", extra, False))

        reordered = copy.deepcopy(records)
        reordered[vote_indexes[0]], reordered[vote_indexes[-1]] = (
            reordered[vote_indexes[-1]],
            reordered[vote_indexes[0]],
        )
        mutations.append(("reordered", reordered, True))

        substituted = copy.deepcopy(records)
        substituted[vote_indexes[0]]["axis"] = "root"
        mutations.append(("identity-substitution", substituted, False))

        for label, mutation, encoding_rejects in mutations:
            with self.subTest(label=label):
                if encoding_rejects:
                    with self.assertRaises(MANIFEST.ManifestError):
                        MANIFEST.encode_manifest_records(mutation)
                else:
                    with self.assertRaises(MANIFEST.ManifestError):
                        MANIFEST.materialize_manifest(self.template, mutation)

    def test_semantic_header_and_template_bindings_are_closed(self) -> None:
        for key, value in (
            ("panel_kind", MANIFEST.READABILITY_PANEL_KIND),
            ("ballot_kind", MANIFEST.READABILITY_BALLOT_KIND),
            ("ballot_schema_version", 1),
            ("packet_sha256", "0" * 64),
            ("voter_id", "different-voter"),
            ("review_id", "different-review"),
            ("template_sha256", "0" * 64),
        ):
            with self.subTest(key=key):
                records = self._records()
                records[0][key] = value
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.materialize_manifest(self.template, records)

    def test_semantic_raw_and_framed_transports_are_byte_identical(self) -> None:
        raw = MANIFEST.encode_manifest_records(self._records())
        digest = hashlib.sha256(raw).hexdigest()
        stream_id = (
            f"{self.ballot['review_id']}:{self.ballot['voter']['voter_id']}"
        )
        framed = _chunk_stream(raw, stream_id=stream_id, chunk_size=31)
        self.assertEqual(
            raw,
            MANIFEST.read_raw_manifest_stream(
                _FragmentedStream(raw),
                expected_size=len(raw),
                expected_sha256=digest,
            ),
        )

    def test_semantic_transport_bindings_reject_every_envelope_axis(self) -> None:
        raw = MANIFEST.encode_manifest_records(self._records())
        digest = hashlib.sha256(raw).hexdigest()
        stream_id = (
            f"{self.ballot['review_id']}:{self.ballot['voter']['voter_id']}"
        )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_raw_manifest_stream(
                io.BytesIO(raw),
                expected_size=len(raw) + 1,
                expected_sha256=digest,
            )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_raw_manifest_stream(
                io.BytesIO(raw),
                expected_size=len(raw),
                expected_sha256="0" * 64,
            )

        framed = _chunk_stream(raw, stream_id=stream_id, chunk_size=31)
        values = [json.loads(line) for line in framed.rstrip(b"\n").split(b"\n")]
        mutations = []
        for key, value in (
            ("stream_id", "different-review:different-voter"),
            ("sequence", 1),
            ("chunk_count", len(values) + 1),
            ("total_raw_bytes", len(raw) + 1),
            ("manifest_sha256", "0" * 64),
            ("chunk_raw_sha256", "0" * 64),
        ):
            mutation = copy.deepcopy(values)
            mutation[0][key] = value
            mutations.append(mutation)
        for index, mutation in enumerate(mutations):
            encoded = b"".join(
                json.dumps(
                    row,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
                for row in mutation
            )
            with self.subTest(index=index), self.assertRaises(
                MANIFEST.ManifestError
            ):
                MANIFEST.read_framed_manifest_stream(
                    io.BytesIO(encoded),
                    expected_size=len(raw),
                    expected_sha256=digest,
                )
        self.assertEqual(
            raw,
            MANIFEST.read_framed_manifest_stream(
                _FragmentedStream(framed),
                expected_size=len(raw),
                expected_sha256=digest,
            ),
        )


class ExpertPanelSemanticMaterializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = source_support.semantic_audit_with_synthetic_delta()
        cls.packet = PANEL.prepare_semantic_disposition_packet(
            audit=cls.audit,
            review_id="semantic-manifest-review",
            created_on="2026-08-10",
        )
        cls.packet_raw = (
            json.dumps(cls.packet, indent=2, ensure_ascii=False).encode("utf-8")
            + b"\n"
        )
        cls.packet_sha256 = hashlib.sha256(cls.packet_raw).hexdigest()
        cls.template = PANEL.prepare_semantic_ballot_template(
            packet=cls.packet,
            packet_sha256=cls.packet_sha256,
            voter_id="semantic-manifest-voter",
            agent_id="semantic-manifest-agent",
            role="senior-semantic-reviewer",
            expertise=["Semantic boundary governance."],
            created_on="2026-08-10",
        )
        cls.ballot = copy.deepcopy(cls.template)
        for index, vote in enumerate(cls.ballot["semantic_votes"]):
            vote.update(
                disposition="valid-contextual-rule",
                rationale=(
                    "The reviewer independently evaluated complete current "
                    f"semantic evidence for target {index}."
                ),
                authority_or_condition=(
                    "The current bounded candidate context and authority apply."
                ),
                decision_owner="semantic-manifest-owner",
                mitigation=(
                    "Re-review when bound source or detector evidence changes."
                ),
                review_after=None,
            )
        cls.template_raw = MANIFEST.canonical_ballot_bytes(
            cls.template, compact=False
        )
        cls.template_sha256 = hashlib.sha256(cls.template_raw).hexdigest()
        cls.records = MANIFEST.project_ballot_to_manifest(
            cls.ballot,
            template_sha256=cls.template_sha256,
        )
        cls.manifest_raw = MANIFEST.encode_manifest_records(cls.records)
        cls.manifest_sha256 = hashlib.sha256(cls.manifest_raw).hexdigest()

    def _workspace(self, root: Path, *, audit: dict | None = None) -> dict[str, Path]:
        run = (
            root
            / ".rd-skills"
            / "expert-panel"
            / self.packet["review_id"]
        )
        ballots = run / "ballots"
        inputs = run / "inputs"
        ballots.mkdir(parents=True)
        inputs.mkdir()
        packet_path = run / "packet.json"
        audit_path = inputs / "skill-content-audit.json"
        template_path = ballots / "semantic-manifest-voter.template.json"
        packet_path.write_bytes(self.packet_raw)
        audit_path.write_text(
            json.dumps(self.audit if audit is None else audit, indent=2) + "\n",
            encoding="utf-8",
        )
        template_path.write_bytes(self.template_raw)
        return {
            "run": run,
            "packet": packet_path,
            "audit": audit_path,
            "template": template_path,
            "output": ballots / "semantic-manifest-voter.json",
        }

    def _arguments(self, paths: dict[str, Path]) -> list[str]:
        relative = {
            key: path.relative_to(paths["run"].parents[2]).as_posix()
            for key, path in paths.items()
            if key not in {"run"}
        }
        return [
            "materialize-ballot",
            "--packet",
            relative["packet"],
            "--template",
            relative["template"],
            "--template-sha256",
            self.template_sha256,
            "--manifest",
            "-",
            "--manifest-size",
            str(len(self.manifest_raw)),
            "--manifest-sha256",
            self.manifest_sha256,
            "--stdin-framing",
            "raw",
            "--audit",
            relative["audit"],
            "--out",
            relative["output"],
        ]

    def test_semantic_raw_and_framed_cli_outputs_are_byte_identical(self) -> None:
        outputs = []
        for framing in ("raw", "changeforge-base64-chunks-v1"):
            with self.subTest(framing=framing), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._workspace(root)
                arguments = self._arguments(paths)
                arguments[arguments.index("--stdin-framing") + 1] = framing
                payload = (
                    self.manifest_raw
                    if framing == "raw"
                    else _chunk_stream(
                        self.manifest_raw,
                        stream_id=(
                            f"{self.packet['review_id']}:semantic-manifest-voter"
                        ),
                    )
                )
                stdin = mock.Mock(buffer=io.BytesIO(payload))
                with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                    sys, "stdin", stdin
                ):
                    self.assertEqual(0, PANEL.main(arguments))
                outputs.append(paths["output"].read_bytes())
                self.assertEqual(self.template_raw, paths["template"].read_bytes())
                self.assertEqual([], list(paths["output"].parent.glob(".*.materialize*")))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(self.ballot, json.loads(outputs[0]))

    def test_empty_manifest_cannot_authorize_nonzero_semantic_template(self) -> None:
        empty_ballot = copy.deepcopy(self.template)
        empty_ballot["semantic_votes"] = []
        empty_records = MANIFEST.project_ballot_to_manifest(
            empty_ballot,
            template_sha256=self.template_sha256,
        )
        empty_raw = MANIFEST.encode_manifest_records(empty_records)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._workspace(root)
            arguments = self._arguments(paths)
            arguments[arguments.index("--manifest-size") + 1] = str(len(empty_raw))
            arguments[arguments.index("--manifest-sha256") + 1] = hashlib.sha256(
                empty_raw
            ).hexdigest()
            stdin = mock.Mock(buffer=io.BytesIO(empty_raw))
            stdout = io.StringIO()
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                sys, "stdin", stdin
            ), mock.patch.object(
                sys, "stdout", stdout
            ):
                self.assertEqual(1, PANEL.main(arguments))

            self.assertIn(
                "semantic manifest identity coverage does not match template",
                stdout.getvalue(),
            )
            self.assertFalse(paths["output"].exists())
            self.assertEqual(self.template_raw, paths["template"].read_bytes())
            self.assertEqual([], list(paths["output"].parent.glob(".*.materialize*")))

    def test_semantic_missing_or_stale_audit_fails_before_manifest_read(self) -> None:
        stale = copy.deepcopy(self.audit)
        detector_contract = stale["root_content"]["semantic_advisories"][
            "detector_contract"
        ]
        current_fingerprint = detector_contract["value"]
        detector_contract["value"] = current_fingerprint[:-1] + (
            "0" if current_fingerprint[-1] != "0" else "1"
        )
        for mode in ("missing", "stale"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._workspace(root, audit=stale)
                arguments = self._arguments(paths)
                if mode == "missing":
                    audit_index = arguments.index("--audit")
                    del arguments[audit_index : audit_index + 2]
                with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                    PANEL.reviewer_manifest,
                    "read_raw_manifest_stream",
                ) as manifest_read:
                    self.assertEqual(1, PANEL.main(arguments))
                manifest_read.assert_not_called()
                self.assertFalse(paths["output"].exists())
                self.assertEqual(self.template_raw, paths["template"].read_bytes())
                self.assertEqual([], list(paths["output"].parent.glob(".*.materialize*")))

    def test_semantic_canonical_paths_and_create_once_fail_closed(self) -> None:
        for mode in (
            "cross-run-audit",
            "packet-traversal",
            "wrong-template-name",
            "wrong-output-name",
            "template-symlink",
            "existing-output",
            "output-symlink",
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._workspace(root)
                arguments = self._arguments(paths)
                template_target = paths["template"]
                output_sentinel: Path | None = None
                output_before: bytes | None = None
                if mode == "cross-run-audit":
                    arguments[arguments.index("--audit") + 1] = (
                        ".rd-skills/expert-panel/other-review/inputs/"
                        "skill-content-audit.json"
                    )
                elif mode == "packet-traversal":
                    arguments[arguments.index("--packet") + 1] = (
                        ".rd-skills/expert-panel/semantic-manifest-review/../"
                        "semantic-manifest-review/packet.json"
                    )
                elif mode == "wrong-template-name":
                    arguments[arguments.index("--template") + 1] = (
                        paths["template"].with_name("wrong.template.json")
                        .relative_to(root)
                        .as_posix()
                    )
                elif mode == "wrong-output-name":
                    arguments[arguments.index("--out") + 1] = (
                        paths["output"].with_name("wrong.json")
                        .relative_to(root)
                        .as_posix()
                    )
                elif mode == "template-symlink":
                    template_target = paths["run"] / "template-target.json"
                    template_target.write_bytes(self.template_raw)
                    paths["template"].unlink()
                    paths["template"].symlink_to(template_target)
                elif mode == "existing-output":
                    paths["output"].write_bytes(b'{"existing":true}\n')
                    output_before = paths["output"].read_bytes()
                else:
                    output_sentinel = paths["run"] / "unrelated.json"
                    output_sentinel.write_bytes(b'{"unrelated":true}\n')
                    paths["output"].symlink_to(output_sentinel)
                    output_before = output_sentinel.read_bytes()

                stdin = mock.Mock(buffer=io.BytesIO(self.manifest_raw))
                with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                    sys, "stdin", stdin
                ):
                    self.assertEqual(1, PANEL.main(arguments))
                self.assertEqual(self.template_raw, template_target.read_bytes())
                if mode == "existing-output":
                    self.assertEqual(output_before, paths["output"].read_bytes())
                elif mode == "output-symlink":
                    self.assertEqual(output_before, output_sentinel.read_bytes())
                    self.assertTrue(paths["output"].is_symlink())
                else:
                    self.assertFalse(paths["output"].exists())
                self.assertEqual([], list(paths["output"].parent.glob(".*.materialize*")))


class ExpertPanelSemanticPrepareTests(unittest.TestCase):
    REVIEW_ID = "semantic-canonical-prepare"
    REVIEWERS = (
        (
            "semantic-prepare-root",
            "semantic_prepare_root_agent",
            "senior-root-semantic-reviewer",
            "Root semantic authority and contextual rule evaluation.",
        ),
        (
            "semantic-prepare-reference",
            "semantic_prepare_reference_agent",
            "senior-reference-semantic-reviewer",
            "Reference contract and semantic evidence evaluation.",
        ),
        (
            "semantic-prepare-governance",
            "semantic_prepare_governance_agent",
            "senior-semantic-governance-reviewer",
            "Semantic governance, ownership, and bounded exceptions.",
        ),
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.audit_raw = (
            ROOT / "reports" / "skill-content-audit.json"
        ).read_bytes()
        cls.audit = json.loads(cls.audit_raw)

    def _git_output(
        self,
        *,
        status: bytes = b"",
        head_audit: bytes | None = None,
    ):
        def run(*arguments: str, check: bool = True):
            if arguments and arguments[0] == "status":
                return mock.Mock(stdout=status, stderr=b"", returncode=0)
            if arguments[:2] == ("ls-files", "--error-unmatch"):
                return mock.Mock(
                    stdout=b"reports/skill-content-audit.json\n",
                    stderr=b"",
                    returncode=0,
                )
            if arguments and arguments[0] == "show":
                return mock.Mock(
                    stdout=self.audit_raw if head_audit is None else head_audit,
                    stderr=b"",
                    returncode=0,
                )
            if arguments[:2] == ("rev-parse", "HEAD"):
                return mock.Mock(stdout=b"ed0a028\n", stderr=b"", returncode=0)
            raise AssertionError(f"unexpected Git authority query: {arguments}")

        return run

    def _arguments(self, *, out: str | None = None) -> list[str]:
        arguments = [
            "prepare",
            "--panel-kind",
            "semantic-disposition",
            "--audit",
            "reports/skill-content-audit.json",
            "--review-id",
            self.REVIEW_ID,
            "--created-on",
            "2026-08-10",
            "--semantic-re-review-axis",
            "root",
            "--semantic-re-review-axis",
            "reference",
            "--out",
            out
            or f".rd-skills/expert-panel/{self.REVIEW_ID}/packet.json",
        ]
        for reviewer in self.REVIEWERS:
            arguments.extend(["--reviewer", *reviewer])
        return arguments

    def _prepare(
        self,
        root: Path,
        *,
        status: bytes = b"",
        head_audit: bytes | None = None,
    ) -> int:
        audit_path = root / "reports" / "skill-content-audit.json"
        audit_path.parent.mkdir(parents=True)
        audit_path.write_bytes(self.audit_raw)
        stdout = io.StringIO()
        with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
            PANEL,
            "_git_output",
            side_effect=self._git_output(status=status, head_audit=head_audit),
        ), mock.patch.object(sys, "stdout", stdout):
            return PANEL.main(self._arguments())

    def test_prepare_creates_complete_full_fresh_semantic_layout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertEqual(0, self._prepare(root))
            run = root / ".rd-skills" / "expert-panel" / self.REVIEW_ID
            packet_path = run / "packet.json"
            audit_path = run / "inputs" / "skill-content-audit.json"
            packet = _json(packet_path)
            self.assertEqual(self.audit_raw, audit_path.read_bytes())
            self.assertGreater(len(packet["semantic_targets"]), 0)
            self.assertIs(
                packet,
                PANEL.validate_semantic_packet_current(packet, self.audit),
            )
            packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            for voter_id, agent_id, role, _expertise in self.REVIEWERS:
                template_path = run / "ballots" / f"{voter_id}.template.json"
                template = _json(template_path)
                self.assertEqual(
                    len(packet["semantic_targets"]),
                    len(template["semantic_votes"]),
                )
                self.assertEqual(
                    (voter_id, agent_id, role),
                    (
                        template["voter"]["voter_id"],
                        template["voter"]["agent_id"],
                        template["voter"]["role"],
                    ),
                )
                self.assertIs(
                    template,
                    PANEL.validate_ballot_template(
                        packet,
                        template,
                        packet_sha256=packet_sha256,
                    ),
                )
            self.assertEqual(
                sorted(
                    [
                        f"ballots/{voter_id}.template.json"
                        for voter_id, *_rest in self.REVIEWERS
                    ]
                    + ["inputs/skill-content-audit.json", "packet.json"]
                ),
                sorted(
                    path.relative_to(run).as_posix()
                    for path in run.rglob("*")
                    if path.is_file()
                ),
            )

    def test_prepared_full_fresh_template_materializes_through_cli(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertEqual(0, self._prepare(root))
            run = root / ".rd-skills" / "expert-panel" / self.REVIEW_ID
            packet_path = run / "packet.json"
            voter_id = self.REVIEWERS[0][0]
            template_path = run / "ballots" / f"{voter_id}.template.json"
            output_path = run / "ballots" / f"{voter_id}.json"
            template = _json(template_path)
            template_raw = template_path.read_bytes()
            filled = copy.deepcopy(template)
            for index, vote in enumerate(filled["semantic_votes"]):
                vote.update(
                    disposition="valid-contextual-rule",
                    rationale=(
                        "The synthetic reviewer fixture evaluated complete current "
                        f"semantic evidence for target {index}."
                    ),
                    authority_or_condition=(
                        "The current bounded candidate context and authority apply."
                    ),
                    decision_owner="semantic-prepare-fixture-owner",
                    mitigation=(
                        "Re-review when bound source or detector evidence changes."
                    ),
                    review_after=None,
                )
            records = MANIFEST.project_ballot_to_manifest(
                filled,
                template_sha256=hashlib.sha256(template_raw).hexdigest(),
            )
            manifest_raw = MANIFEST.encode_manifest_records(records)
            arguments = [
                "materialize-ballot",
                "--packet",
                packet_path.relative_to(root).as_posix(),
                "--template",
                template_path.relative_to(root).as_posix(),
                "--template-sha256",
                hashlib.sha256(template_raw).hexdigest(),
                "--manifest",
                "-",
                "--manifest-size",
                str(len(manifest_raw)),
                "--manifest-sha256",
                hashlib.sha256(manifest_raw).hexdigest(),
                "--stdin-framing",
                "raw",
                "--audit",
                (run / "inputs" / "skill-content-audit.json")
                .relative_to(root)
                .as_posix(),
                "--out",
                output_path.relative_to(root).as_posix(),
            ]
            stdin = mock.Mock(buffer=io.BytesIO(manifest_raw))
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                sys, "stdin", stdin
            ):
                self.assertEqual(0, PANEL.main(arguments))
            ballot = _json(output_path)
            packet = _json(packet_path)
            self.assertEqual(filled, ballot)
            self.assertIs(
                ballot,
                PANEL.validate_ballot(
                    packet,
                    ballot,
                    packet_sha256=hashlib.sha256(
                        packet_path.read_bytes()
                    ).hexdigest(),
                ),
            )

    def test_prepare_collision_symlink_and_partial_failure_leave_no_mixed_run(self) -> None:
        for mode in ("collision", "symlink", "partial"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                run = root / ".rd-skills" / "expert-panel" / self.REVIEW_ID
                sentinel: Path | None = None
                if mode == "collision":
                    run.mkdir(parents=True)
                    sentinel = run / "existing.json"
                    sentinel.write_bytes(b'{"existing":true}\n')
                elif mode == "symlink":
                    run.parent.mkdir(parents=True)
                    target = root / "outside"
                    target.mkdir()
                    run.symlink_to(target, target_is_directory=True)
                    sentinel = target

                if mode == "partial":
                    original_fsync = PANEL.os.fsync
                    fsync_calls = 0

                    def fail_during_prepare(descriptor: int) -> None:
                        nonlocal fsync_calls
                        fsync_calls += 1
                        if fsync_calls == 3:
                            raise OSError("injected prepare fsync failure")
                        original_fsync(descriptor)

                    with mock.patch.object(
                        PANEL.os, "fsync", side_effect=fail_during_prepare
                    ):
                        self.assertEqual(1, self._prepare(root))
                    self.assertGreaterEqual(fsync_calls, 3)
                    self.assertFalse(run.exists())
                else:
                    self.assertEqual(1, self._prepare(root))
                    if mode == "collision":
                        self.assertEqual(b'{"existing":true}\n', sentinel.read_bytes())
                    else:
                        self.assertTrue(run.is_symlink())
                        self.assertEqual([], list(sentinel.iterdir()))

    def test_prepare_rejects_dirty_stale_and_tracked_output_before_write(self) -> None:
        for mode in ("dirty", "stale-audit", "tracked-output"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                audit_path = root / "reports" / "skill-content-audit.json"
                audit_path.parent.mkdir(parents=True)
                audit_path.write_bytes(self.audit_raw)
                arguments = self._arguments(
                    out=(
                        "evals/expert-panel/semantic-disposition.json"
                        if mode == "tracked-output"
                        else None
                    )
                )
                stdout = io.StringIO()
                with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                    PANEL,
                    "_git_output",
                    side_effect=self._git_output(
                        status=b" M scripts/example.py\n" if mode == "dirty" else b"",
                        head_audit=b"{}\n" if mode == "stale-audit" else None,
                    ),
                ), mock.patch.object(sys, "stdout", stdout):
                    self.assertEqual(1, PANEL.main(arguments))
                self.assertFalse(
                    (root / ".rd-skills" / "expert-panel" / self.REVIEW_ID).exists()
                )


class ExpertPanelManifestRoundtripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readability_packet = _readability_packet_fixture()
        cls.readability_ballots = [
            _readability_ballot_fixture(cls.readability_packet, voter=voter)
            for voter in range(1, 4)
        ]
        cls.readability_packet_sha256 = cls.readability_ballots[0][
            "packet_sha256"
        ]
        cls.professional_ballots = [
            _professional_ballot_fixture(voter=voter) for voter in range(1, 4)
        ]

    def test_all_three_readability_ballots_roundtrip_exactly(self) -> None:
        self.assertEqual(3, len(self.readability_ballots))
        for ballot in self.readability_ballots:
            with self.subTest(ballot=ballot["voter"]["voter_id"]):
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
        for ballot in self.professional_ballots:
            with self.subTest(ballot=ballot["voter"]["voter_id"]):
                template = _blank_template(ballot)
                records, _encoded, candidate = _roundtrip(ballot, template)
                self.assertEqual(ballot, candidate)
                for record in records:
                    for candidate_row in record.get(
                        "examined_adjacent_candidates", []
                    ):
                        self.assertNotIn("review_origin", candidate_row)
                        self.assertNotIn("discovery_reason", candidate_row)

    def test_current_professional_transport_omits_source_fingerprints(self) -> None:
        ballot = copy.deepcopy(self.professional_ballots[0])
        self.assertNotIn("source_fingerprints", ballot)
        template = _blank_template(ballot)
        _records, _encoded, candidate = _roundtrip(ballot, template)
        self.assertEqual(ballot, candidate)

        for value in ({}, {"professional_packages": "0" * 64}):
            with self.subTest(value=value):
                forged = copy.deepcopy(ballot)
                forged["source_fingerprints"] = value
                with self.assertRaises(MANIFEST.ManifestError):
                    MANIFEST.project_ballot_to_manifest(
                        forged,
                        template_sha256=_template_sha256(template),
                    )

    def test_synthetic_ballot_corpus_fits_deterministic_transport_bounds(self) -> None:
        corpus = [*self.readability_ballots, *self.professional_ballots]
        self.assertEqual(6, len(corpus))
        self.assertEqual(3, len(self.professional_ballots))
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
        self.assertLessEqual(
            max_manifest,
            MANIFEST.MAX_REVIEWER_MANIFEST_BYTES,
        )
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

    def test_professional_ballots_use_semantic_review_contract(self) -> None:
        semantic_contract_fingerprint = (
            PANEL.panel_contracts.professional_review_contract_fingerprint()
        )
        self.assertEqual(
            {semantic_contract_fingerprint},
            {
                ballot["review_contract_fingerprint"]
                for ballot in self.professional_ballots
            },
        )
        self.assertEqual(
            semantic_contract_fingerprint,
            PANEL._professional_evidence_review_contract_fingerprint(),
        )


class ExpertPanelManifestClosedSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readability_packet = _readability_packet_fixture()
        cls.readability_ballot = _readability_ballot_fixture(
            cls.readability_packet, voter=1
        )
        cls.readability_template = _build_readability_template(
            cls.readability_packet,
            cls.readability_ballot["packet_sha256"],
            cls.readability_ballot,
        )
        cls.readability_records = MANIFEST.project_ballot_to_manifest(
            cls.readability_ballot,
            template_sha256=_template_sha256(cls.readability_template),
        )
        cls.professional_ballot = _professional_ballot_fixture(voter=1)
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
        self.assertEqual(16_777_216, MANIFEST.MAX_REVIEWER_MANIFEST_BYTES)
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
        cls._scratch = tempfile.TemporaryDirectory(dir=ROOT)
        cls.addClassCleanup(cls._scratch.cleanup)
        cls.packet_path = Path(cls._scratch.name) / "packet.json"
        cls.packet = _readability_packet_fixture()
        cls.ballot = _readability_ballot_fixture(cls.packet, voter=1)
        cls.packet_path.write_text(
            json.dumps(cls.packet, indent=2) + "\n", encoding="utf-8"
        )
        cls.packet_sha256 = hashlib.sha256(cls.packet_path.read_bytes()).hexdigest()
        cls.ballot["packet_sha256"] = cls.packet_sha256
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

    def test_generic_artifact_binding_supports_current_professional_packet_size(
        self,
    ) -> None:
        packet_size = 20_880_201
        prefix = b'{"padding":"'
        suffix = b'"}\n'
        packet_raw = (
            prefix
            + b"x" * (packet_size - len(prefix) - len(suffix))
            + suffix
        )
        self.assertEqual(packet_size, len(packet_raw))

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet_relative = (
                ".rd-skills/expert-panel/current-professional/packet.json"
            )
            packet_path = root / packet_relative
            packet_path.parent.mkdir(parents=True)
            packet_path.write_bytes(packet_raw)
            decision_path = packet_path.parent / "panel" / "decision.json"
            decision_path.parent.mkdir()
            record = {
                "packet": {
                    "path": packet_relative,
                    "sha256": hashlib.sha256(packet_raw).hexdigest(),
                },
                "voters": [],
            }
            with mock.patch.object(PANEL, "ROOT", root):
                bound_path, packet, ballots = PANEL._decision_packet_and_ballots(
                    record,
                    decision_path=decision_path,
                )

        self.assertEqual(packet_path.resolve(), bound_path.resolve())
        self.assertEqual(
            packet_size - len(prefix) - len(suffix),
            len(packet["padding"]),
        )
        self.assertEqual([], ballots)

    def test_generic_and_reviewer_manifest_limits_remain_separate(self) -> None:
        self.assertEqual(33_554_432, MANIFEST.MAX_MANIFEST_BYTES)
        self.assertEqual(16_777_216, MANIFEST.MAX_REVIEWER_MANIFEST_BYTES)
        self.assertEqual(
            MANIFEST.MAX_REVIEWER_MANIFEST_BYTES,
            MANIFEST.MAX_CHUNK_COUNT * MANIFEST.MAX_CHUNK_RAW_BYTES,
        )

        oversized_reviewer_size = MANIFEST.MAX_REVIEWER_MANIFEST_BYTES + 1
        oversized_reviewer = b"x" * oversized_reviewer_size
        oversized_digest = hashlib.sha256(oversized_reviewer).hexdigest()
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.parse_manifest_bytes(oversized_reviewer)
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_raw_manifest_stream(
                io.BytesIO(oversized_reviewer),
                expected_size=oversized_reviewer_size,
                expected_sha256=oversized_digest,
            )
        with self.assertRaises(MANIFEST.ManifestError):
            MANIFEST.read_framed_manifest_stream(
                io.BytesIO(b""),
                expected_size=oversized_reviewer_size,
                expected_sha256=oversized_digest,
            )
        with tempfile.TemporaryDirectory() as raw:
            manifest_path = Path(raw) / "reviewer-manifest.jsonl"
            manifest_path.write_bytes(oversized_reviewer)
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_manifest_file(
                    manifest_path,
                    expected_size=oversized_reviewer_size,
                    expected_sha256=oversized_digest,
                    repository_root=ROOT,
                )

            oversized_artifact = Path(raw) / "oversized-artifact.json"
            with oversized_artifact.open("wb") as stream:
                stream.truncate(MANIFEST.MAX_MANIFEST_BYTES + 1)
            with self.assertRaises(MANIFEST.ManifestError):
                MANIFEST.read_bound_regular_file(
                    oversized_artifact,
                    label="oversized generic artifact",
                )

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
                forbidden_audit = copy.deepcopy(arguments)
                forbidden_audit[1:1] = ["--audit", str(self.packet_path)]
                self.assertEqual(1, PANEL.main(forbidden_audit))

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
