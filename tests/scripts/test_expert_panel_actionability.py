from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import readability_review_test_support as readability_support

ROOT = Path(__file__).resolve().parents[2]
PANEL = source_support.PANEL
REGRESSION = source_support.REGRESSION


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class ExpertPanelActionabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = readability_support.current_audit()
        cls.packet = readability_support.current_packet()

    @staticmethod
    def _first_substantive_window_line(target: dict) -> tuple[int, str, str]:
        return readability_support._first_substantive_window_line(target)

    def _ballot(
        self,
        packet: dict,
        packet_sha256: str,
        voter: int,
        *,
        actionability_decision: str = "accepted-current-actionability",
    ) -> dict:
        return readability_support.ballot(
            packet,
            packet_sha256,
            voter,
            actionability_decision=actionability_decision,
        )

    @staticmethod
    def _synchronize_actionability_audit_contract(audit: dict) -> None:
        auditor = PANEL._load_skill_content_auditor()
        readability_by_owner = auditor._readability_by_owner(
            audit["ai_readability"]["documents"]
        )
        for row in audit["skills"]:
            row["review_state"], row["review_reasons"] = (
                auditor._review_state_and_reasons(
                    row,
                    readability_by_owner.get(row["name"]),
                )
            )
        audit["summary"]["review_states"] = {
            state: sum(row["review_state"] == state for row in audit["skills"])
            for state in auditor.REVIEW_STATE_PRIORITY
            if any(row["review_state"] == state for row in audit["skills"])
        }
        audit["summary"]["review_reasons"] = {
            reason: sum(
                reason in row["review_reasons"] for row in audit["skills"]
            )
            for reason in auditor.REVIEW_REASON_PRIORITY
        }
        actionability_count = sum(
            row["actionability_applicable"] for row in audit["skills"]
        )
        audit["summary"]["actionability_applicable_items"] = actionability_count
        audit["summary"]["weak_front_loaded_action_all_items"] = (
            actionability_count
        )

    def _synthetic_actionability_packet(self) -> dict:
        audit = copy.deepcopy(self.audit)
        for row in audit["skills"]:
            row["actionability_applicable"] = False
            row["actionability_findings"] = []
            row["review_reasons"] = [
                reason
                for reason in row["review_reasons"]
                if reason != "weak_front_loaded_action"
            ]
        candidate = next(
            row for row in audit["skills"] if row["kind"] == "professional-skill"
        )
        candidate["actionability_model"] = "runtime-front-loaded-v1"
        candidate["actionability_applicable"] = True
        candidate["actionability_findings"] = [
            "runtime-front-loaded-score-below-threshold"
        ]
        candidate["front_loaded_action_score"] = 0
        self._synchronize_actionability_audit_contract(audit)
        return PANEL.prepare_packet(
            audit=audit,
            review_id="synthetic-actionability-target-fixture",
            created_on="2026-07-24",
        )

    @staticmethod
    def _current_readability_authority(
        packet: dict, *, track_source_changes: bool = True
    ):
        def projection():
            if not track_source_changes:
                return (
                    packet["source_fingerprints"],
                    packet["content_targets"],
                    packet["readability_targets"],
                    packet["actionability_targets"],
                )
            actionability_targets = copy.deepcopy(packet["actionability_targets"])
            for target in actionability_targets:
                target["front_window"] = PANEL._actionability_front_window(
                    target["path"],
                    limit=packet["panel_contract"][
                        "actionability_front_window_lines"
                    ],
                )
            fingerprints = dict(packet["source_fingerprints"])
            fingerprints["readability_target_manifest"] = (
                PANEL._canonical_json_sha256(
                    PANEL._readability_target_manifest_projection(
                        content_targets=packet["content_targets"],
                        readability_targets=packet["readability_targets"],
                        actionability_targets=actionability_targets,
                    )
                )
            )
            return (
                fingerprints,
                packet["content_targets"],
                packet["readability_targets"],
                actionability_targets,
            )

        return mock.patch.object(
            PANEL,
            "_current_readability_target_projection",
            side_effect=projection,
        )

    def test_prepare_emits_schema_two_and_all_weak_targets(self) -> None:
        packet = self.packet
        self.assertEqual(PANEL.READABILITY_SCHEMA_VERSION, packet["schema_version"])
        self.assertEqual(
            "root-body-document-context-v1",
            packet["panel_contract"]["content_source_binding_contract"],
        )
        self.assertEqual(43, len(packet["content_targets"]))
        advisory_paths = {
            row["path"] for row in packet["readability_targets"]
        }
        body_documents = {
            row["path"]: row
            for row in self.audit["ai_readability"]["documents"]
            if row["document_part"] == "body"
        }
        missing_advisory = 0
        for target in packet["content_targets"]:
            source = body_documents[target["path"]]
            self.assertEqual(source["document_id"], target["document_id"])
            self.assertEqual(source["owner"], target["owner"])
            self.assertEqual("body", source["document_part"])
            self.assertEqual(source["document_part"], target["document_part"])
            self.assertEqual(
                {"kind": "yaml-body", "path": target["path"]},
                target["source_selector"],
            )
            context = target["document_context"]
            self.assertEqual(context["sha256"], target["content_fingerprint"])
            self.assertEqual(context["text"].splitlines(), [
                row["text"] for row in context["lines"]
            ])
            missing_advisory += target["path"] not in advisory_paths
        self.assertEqual(7, missing_advisory)
        self.assertLess(
            len(json.dumps(packet, sort_keys=True).encode("utf-8")),
            16 * 1024 * 1024,
        )
        self.assertEqual(
            {
                "actionability_detector_contract",
                "readability_detector_contract",
                "readability_target_manifest",
            },
            set(packet["source_fingerprints"]),
        )
        self.assertEqual(0, len(packet["actionability_targets"]))
        self.assertEqual(
            0,
            packet["panel_contract"]["required_actionability_target_count"],
        )
        target_ids = [row["target_id"] for row in packet["actionability_targets"]]
        self.assertEqual(sorted(set(target_ids)), target_ids)
        readability_target_ids = [
            row["document_id"] for row in packet["readability_targets"]
        ]
        expected_readability_target_ids = sorted(
            row["document_id"]
            for row in self.audit["ai_readability"]["documents"]
            if row["highest_advisory_band"] is not None
        )
        self.assertEqual(
            expected_readability_target_ids,
            readability_target_ids,
        )
        self.assertEqual(
            sorted(set(readability_target_ids)),
            readability_target_ids,
        )
        audit_findings_by_document: dict[str, list[dict]] = {}
        for finding in self.audit["ai_readability"]["findings"]:
            audit_findings_by_document.setdefault(
                finding["document_id"], []
            ).append(finding)
        packet_finding_ids: list[str] = []
        for target in packet["readability_targets"]:
            expected_findings = [
                {
                    "finding_id": finding["finding_id"],
                    "line": finding["line"],
                    "band": finding["band"],
                    "words": finding["words"],
                    "kind": finding["kind"],
                    "sentence": finding["sentence"],
                    "sentence_fingerprint": finding[
                        "sentence_fingerprint"
                    ],
                    "source_span": copy.deepcopy(
                        finding["source_span"]
                    ),
                }
                for finding in audit_findings_by_document[
                    target["document_id"]
                ]
            ]
            expected_findings.sort(
                key=lambda row: (
                    row["source_span"]["start_offset"],
                    row["source_span"]["end_offset"],
                    row["kind"],
                    row["finding_id"],
                )
            )
            self.assertEqual(expected_findings, target["findings"])
            target_finding_ids = [
                finding["finding_id"] for finding in target["findings"]
            ]
            self.assertEqual(
                len(target_finding_ids), len(set(target_finding_ids))
            )
            packet_finding_ids.extend(target_finding_ids)
        self.assertEqual(
            sorted(
                finding["finding_id"]
                for finding in self.audit["ai_readability"]["findings"]
            ),
            sorted(packet_finding_ids),
        )
        self.assertEqual(
            len(packet_finding_ids), len(set(packet_finding_ids))
        )
        self.assertEqual(
            "finding-grounded-document-majority-v1",
            packet["panel_contract"]["readability_document_decision_method"],
        )
        PANEL.validate_packet(packet)

    def test_packet_source_fingerprints_are_target_local_and_contract_owned(
        self,
    ) -> None:
        packet = PANEL.prepare_packet(
            audit=self.audit,
            review_id="current-source-authority-fixture",
            created_on="2026-08-10",
        )
        changed = copy.deepcopy(self.audit)
        changed["root_content"]["source_fingerprint"]["value"] = "0" * 64
        changed["reference_content"]["preface_contract"][
            "source_fingerprint"
        ]["value"] = "1" * 64
        changed["root_content"]["documents"].append(
            {
                "document_part": "body",
                "path": "src/foundation/unrelated/SKILL.md",
                "content_fingerprint": "2" * 64,
            }
        )
        changed["reference_content"]["unrelated_inventory_metadata"] = {
            "path": "src/foundation/unrelated/references/note.md",
            "sha256": "3" * 64,
        }
        changed["summary"]["unrelated_report_metadata"] = 1
        changed_packet = PANEL.prepare_packet(
            audit=changed,
            review_id="changed-unrelated-authority-fixture",
            created_on="2026-08-10",
        )
        self.assertEqual(
            packet["source_fingerprints"],
            changed_packet["source_fingerprints"],
        )

        arguments = {
            "readability_contract": self.audit["ai_readability"]["contract"],
            "content_targets": packet["content_targets"],
            "readability_targets": packet["readability_targets"],
            "actionability_targets": packet["actionability_targets"],
            "actionability_score_threshold": packet["panel_contract"][
                "actionability_score_threshold"
            ],
            "actionability_front_window_lines": packet["panel_contract"][
                "actionability_front_window_lines"
            ],
        }
        baseline = PANEL._readability_source_fingerprints(**arguments)

        administrative = copy.deepcopy(arguments)
        administrative["content_targets"] = copy.deepcopy(
            packet["content_targets"]
        )
        administrative["content_targets"][0]["review_state"] = "REPORT_ONLY"
        administrative["content_targets"][0]["review_reasons"] = [
            "report-only"
        ]
        self.assertEqual(
            baseline,
            PANEL._readability_source_fingerprints(**administrative),
        )

        target_changed = copy.deepcopy(arguments)
        target_changed["readability_targets"] = copy.deepcopy(
            packet["readability_targets"]
        )
        target_changed["readability_targets"][0]["findings"][0][
            "sentence_fingerprint"
        ] = "0" * 64
        target_changed_fingerprints = PANEL._readability_source_fingerprints(
            **target_changed
        )
        self.assertNotEqual(
            baseline["readability_target_manifest"],
            target_changed_fingerprints["readability_target_manifest"],
        )

        readability_detector_changed = copy.deepcopy(arguments)
        readability_detector_changed["readability_contract"] = copy.deepcopy(
            self.audit["ai_readability"]["contract"]
        )
        readability_detector_changed["readability_contract"][
            "ordinary_target_words"
        ] += 1
        detector_fingerprints = PANEL._readability_source_fingerprints(
            **readability_detector_changed
        )
        self.assertNotEqual(
            baseline["readability_detector_contract"],
            detector_fingerprints["readability_detector_contract"],
        )
        self.assertEqual(
            baseline["readability_target_manifest"],
            detector_fingerprints["readability_target_manifest"],
        )

        actionability_changed = {
            **arguments,
            "actionability_score_threshold": (
                arguments["actionability_score_threshold"] + 1
            ),
        }
        actionability_fingerprints = PANEL._readability_source_fingerprints(
            **actionability_changed
        )
        self.assertNotEqual(
            baseline["actionability_detector_contract"],
            actionability_fingerprints["actionability_detector_contract"],
        )

    def test_schema_two_cli_rejects_removed_readiness_flag(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            PANEL._parse_args(
                [
                    "prepare",
                    "--panel-kind",
                    PANEL.READABILITY_PANEL_KIND,
                    "--audit",
                    "audit.json",
                    "--readiness",
                    "readiness.json",
                    "--review-id",
                    "removed-readiness-flag",
                    "--created-on",
                    "2026-08-10",
                    "--out",
                    ".rd-skills/expert-panel/removed-readiness-flag/packet.json",
                ]
            )
        self.assertEqual(2, raised.exception.code)

    def test_current_audit_actionability_projection_is_fail_closed(self) -> None:
        weak_reason = "weak_front_loaded_action"
        mutations = (
            lambda value: value["skills"][0].pop("actionability_model"),
            lambda value: value["skills"][0]["review_reasons"].append(
                weak_reason
            ),
            lambda value: value["summary"]["review_reasons"].update(
                {
                    weak_reason: value["summary"]["review_reasons"].get(
                        weak_reason, 0
                    )
                    + 1
                }
            ),
        )
        for index, mutate in enumerate(mutations):
            stale = copy.deepcopy(self.audit)
            mutate(stale)
            with self.subTest(mutation=index), self.assertRaises(PANEL.PanelReviewError):
                PANEL.prepare_packet(
                    audit=stale,
                    review_id="stale-actionability-authority",
                    created_on="2026-08-10",
                )

        duplicate = {
            "path": "src/professional-skills/duplicate/SKILL.md",
            "name": "duplicate-actionability",
            "front_loaded_action_score": 0,
            "review_reasons": [weak_reason],
            "actionability_model": "runtime-front-loaded-v1",
            "actionability_applicable": True,
        }
        with self.assertRaisesRegex(ValueError, "target IDs must be unique"):
            REGRESSION._required_actionability_disposition_rows(
                [duplicate, copy.deepcopy(duplicate)]
            )

    def test_attest_and_promotion_paths_reach_shared_source_authority(self) -> None:
        record = {
            "review_id": self.packet["review_id"],
            "decided_on": self.packet["created_on"],
            "voters": [],
        }
        with mock.patch.object(
            PANEL,
            "_json_object",
            return_value=self.audit,
        ) as load, mock.patch.object(
            PANEL,
            "_readability_target_authorities",
            wraps=PANEL._readability_target_authorities,
        ) as build_authority:
            _path, authority, validate_after_parse = (
                PANEL._current_attestation_validation(
                    PANEL.READABILITY_PANEL_KIND,
                    review_id=self.packet["review_id"],
                    decided_on=self.packet["created_on"],
                    attestation_selector={},
                )
            )
            currentness_builds = build_authority.call_count
            validate_after_parse({})
            self.assertEqual(currentness_builds, build_authority.call_count)
        load.assert_called_once()
        self.assertEqual(2, currentness_builds)
        self.assertEqual(
            self.packet["source_fingerprints"],
            authority["expected_source_fingerprints"],
        )

        drifted_audit = copy.deepcopy(self.audit)
        drifted_audit["thresholds"]["weak_front_loaded_action"] += 1
        with mock.patch.object(
            PANEL, "validate_decision_record"
        ), mock.patch.object(
            PANEL,
            "_decision_packet_and_ballots",
            return_value=(Path("packet.json"), self.packet, []),
        ), self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "readability decision source_fingerprints is incomplete or stale",
        ):
            PANEL._readability_attestation_from_decision(
                record,
                decision_path=Path("decision.json"),
                audit=drifted_audit,
            )

    def test_readability_manifest_authority_is_shared_end_to_end(self) -> None:
        packet = copy.deepcopy(self.packet)
        bindings = PANEL._readability_target_authorities(packet)
        manifest = (
            PANEL.panel_attestation.readability_target_manifest_projection(
                bindings
            )
        )
        self.assertEqual(
            manifest,
            PANEL._readability_target_manifest_projection(
                content_targets=packet["content_targets"],
                readability_targets=packet["readability_targets"],
                actionability_targets=packet["actionability_targets"],
            ),
        )
        self.assertEqual(
            PANEL.panel_contracts.READABILITY_TARGET_MANIFEST_CONTRACT_ID,
            manifest["contract_id"],
        )
        self.assertEqual(
            packet["source_fingerprints"]["readability_target_manifest"],
            PANEL.panel_attestation.readability_target_manifest_fingerprint(
                bindings
            ),
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write(packet_path, packet)
            packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter in range(1, 4):
                ballot = self._ballot(packet, packet_sha256, voter)
                ballot_path = root / f"ballot-{voter}.json"
                _write(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            decision = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on=packet["created_on"],
            )
            decision_path = root / "decision.json"
            _write(decision_path, decision)
            attestation = PANEL._readability_attestation_from_decision(
                decision,
                decision_path=decision_path,
                audit=self.audit,
            )

        validation = {
            "expected_source_fingerprints": packet["source_fingerprints"],
            "expected_review_contract_fingerprint": PANEL._canonical_json_sha256(
                packet["panel_contract"]
            ),
            "expected_readability_current_bindings": bindings,
        }
        payload = PANEL.panel_attestation.canonical_attestation_bytes(
            attestation,
            expected_path=(
                PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
            ),
            **validation,
        )
        parsed = PANEL.panel_attestation.parse_attestation_bytes(
            payload,
            expected_path=(
                PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
            ),
            **validation,
        )
        self.assertEqual(attestation, parsed)
        storage = json.loads(payload)
        self.assertEqual(
            packet["source_fingerprints"]["readability_target_manifest"],
            storage["target_manifest_binding"],
        )

        without_sources = dict(validation)
        without_sources.pop("expected_source_fingerprints")
        with self.assertRaisesRegex(
            PANEL.panel_attestation.AttestationError,
            "source fingerprints",
        ):
            PANEL.panel_attestation.parse_attestation_bytes(
                payload,
                expected_path=(
                    PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
                ),
                **without_sources,
            )

        for key in (
            "target_manifest_binding",
            "readability_detector_contract",
            "actionability_detector_contract",
        ):
            changed = copy.deepcopy(storage)
            if key == "target_manifest_binding":
                changed[key] = "0" * 64
            else:
                changed["detector_contract_fingerprints"][key] = "0" * 64
            tampered = (
                json.dumps(
                    changed,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            with self.subTest(tamper=key), self.assertRaises(
                PANEL.panel_attestation.AttestationError
            ):
                PANEL.panel_attestation.parse_attestation_bytes(
                    tampered,
                    expected_path=(
                        PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
                    ),
                    **validation,
                )

        partial = copy.deepcopy(bindings)
        partial["content"].pop(next(iter(partial["content"])))
        with self.assertRaises(PANEL.panel_attestation.AttestationError):
            PANEL.panel_attestation.parse_attestation_bytes(
                payload,
                expected_path=(
                    PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
                ),
                **{
                    **validation,
                    "expected_readability_current_bindings": partial,
                },
            )

        overwritten = copy.deepcopy(attestation)
        overwritten["source_fingerprints"][
            "readability_target_manifest"
        ] = "0" * 64
        with self.assertRaisesRegex(
            PANEL.panel_attestation.AttestationError,
            "manifest",
        ):
            PANEL.panel_attestation.finalize_attestation(
                overwritten,
                expected_path=(
                    PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
                ),
                expected_readability_current_bindings=bindings,
            )

    def test_content_source_binding_is_current_only_and_fail_closed(self) -> None:
        packet = self.packet
        thin = copy.deepcopy(packet)
        thin["panel_contract"].pop("content_source_binding_contract", None)
        for target in thin["content_targets"]:
            target.pop("document_id", None)
            target.pop("owner", None)
            target.pop("document_part", None)
            target.pop("source_selector", None)
            target.pop("document_context", None)
            target.pop("content_fingerprint", None)

        PANEL.validate_packet(thin, validation_mode="historical")
        with self.assertRaisesRegex(PANEL.PanelReviewError, "content source binding"):
            PANEL.validate_packet(thin)
        with self.assertRaisesRegex(PANEL.PanelReviewError, "content source binding"):
            PANEL.prepare_readability_ballot_template(
                packet=thin,
                packet_sha256="a" * 64,
                voter_id="thin-current",
                agent_id="thin-current-agent",
                role="thin current reviewer",
                expertise=["readability"],
                created_on="2026-07-17",
            )

        mutations = {
            "delete": lambda value: value["content_targets"].pop(),
            "document-part-missing": lambda value: value["content_targets"][
                0
            ].pop("document_part"),
            "document-part-non-body": lambda value: value["content_targets"][
                0
            ].__setitem__("document_part", "description"),
            "document-part-tamper": lambda value: value["content_targets"][
                0
            ].__setitem__("document_part", "body "),
            "selector-swap": lambda value: (
                value["content_targets"][0].__setitem__(
                    "source_selector",
                    copy.deepcopy(value["content_targets"][1]["source_selector"]),
                )
            ),
            "owner-swap": lambda value: value["content_targets"][0].__setitem__(
                "owner", value["content_targets"][1]["owner"]
            ),
            "document-id-swap": lambda value: value["content_targets"][0].__setitem__(
                "document_id", value["content_targets"][1]["document_id"]
            ),
            "context-swap": lambda value: value["content_targets"][0].__setitem__(
                "document_context",
                copy.deepcopy(value["content_targets"][1]["document_context"]),
            ),
            "fingerprint-tamper": lambda value: value["content_targets"][0].__setitem__(
                "content_fingerprint", "0" * 64
            ),
            "text-tamper": lambda value: value["content_targets"][0][
                "document_context"
            ].__setitem__("text", "tampered"),
            "line-tamper": lambda value: value["content_targets"][0][
                "document_context"
            ]["lines"][0].__setitem__("text", "tampered"),
        }
        for label, mutate in mutations.items():
            changed = copy.deepcopy(packet)
            mutate(changed)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL.validate_packet(changed)

        stale_content = copy.deepcopy(packet["content_targets"])
        stale_content[0]["owner"] = stale_content[1]["owner"]
        with mock.patch.object(
            PANEL,
            "_current_readability_target_projection",
            return_value=(
                packet["source_fingerprints"],
                stale_content,
                packet["readability_targets"],
                packet["actionability_targets"],
            ),
        ), self.assertRaisesRegex(PANEL.PanelReviewError, "bindings or inventory"):
            PANEL.validate_packet(packet)

        digest = hashlib.sha256(
            (json.dumps(thin, indent=2) + "\n").encode("utf-8")
        ).hexdigest()
        ballot = self._ballot(packet, digest, 1)
        with self.assertRaisesRegex(PANEL.PanelReviewError, "content source binding"):
            PANEL.validate_ballot(thin, ballot, packet_sha256=digest)
        PANEL.validate_ballot(
            thin,
            ballot,
            packet_sha256=digest,
            validation_mode="historical",
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write(packet_path, thin)
            ballots = [
                (Path(raw) / f"ballot-{voter}.json", self._ballot(packet, digest, voter))
                for voter in range(1, 4)
            ]
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "content source binding"
            ):
                PANEL.aggregate_ballots(
                    packet=thin,
                    packet_path=packet_path,
                    ballot_values=ballots,
                    decided_on="2026-07-17",
                )

    def test_prepare_uses_explicit_kind_model_and_applicability_not_raw_score(
        self,
    ) -> None:
        audit = copy.deepcopy(self.audit)
        candidate = next(
            row for row in audit["skills"] if row["kind"] == "professional-skill"
        )
        for row in audit["skills"]:
            row["actionability_model"] = {
                "professional-skill": "runtime-front-loaded-v1",
                "foundation-capability": "foundation-decision-card-v1",
                "domain-extension": "domain-front-loaded-v1",
            }[row["kind"]]
            row["actionability_applicable"] = False
            row["review_reasons"] = [
                reason
                for reason in row["review_reasons"]
                if reason != "weak_front_loaded_action"
            ]
        candidate["actionability_applicable"] = True
        candidate["front_loaded_action_score"] = 100
        self._synchronize_actionability_audit_contract(audit)

        packet = PANEL.prepare_packet(
            audit=audit,
            review_id="explicit-actionability-model-fixture",
            created_on="2026-07-24",
        )

        self.assertEqual(1, len(packet["actionability_targets"]))
        self.assertEqual(
            candidate["path"],
            packet["actionability_targets"][0]["path"],
        )
        self.assertEqual(
            "runtime-front-loaded-v1",
            packet["actionability_targets"][0]["actionability_model"],
        )

    def test_schema_two_cli_packet_is_canonical_and_create_only(self) -> None:
        review_id = self.packet["review_id"]

        def invoke(
            *,
            validation_root: Path,
            command: str,
            output: str,
        ) -> int:
            (validation_root / "audit.json").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(
                PANEL, "ROOT", validation_root
            ), mock.patch.object(
                PANEL,
                "prepare_packet",
                return_value=copy.deepcopy(self.packet),
            ):
                return PANEL.main(
                    [
                        command,
                        "--panel-kind",
                        PANEL.READABILITY_PANEL_KIND,
                        "--audit",
                        "audit.json",
                        "--review-id",
                        review_id,
                        "--created-on",
                        "2026-07-18",
                        "--out",
                        output,
                    ]
                )

        canonical = f".rd-skills/expert-panel/{review_id}/packet.json"
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            self.assertEqual(
                0,
                invoke(
                    validation_root=validation_root,
                    command="prepare",
                    output=canonical,
                ),
            )
            packet_path = validation_root / canonical
            original_bytes = packet_path.read_bytes()
            original_sha256 = hashlib.sha256(original_bytes).hexdigest()

            self.assertEqual(
                1,
                invoke(
                    validation_root=validation_root,
                    command="build-packet",
                    output=canonical,
                ),
            )
            self.assertEqual(original_bytes, packet_path.read_bytes())
            self.assertEqual(
                original_sha256,
                hashlib.sha256(packet_path.read_bytes()).hexdigest(),
            )

            noncanonical = "scratch/readability-packet.json"
            self.assertEqual(
                1,
                invoke(
                    validation_root=validation_root,
                    command="prepare",
                    output=noncanonical,
                ),
            )
            self.assertFalse((validation_root / noncanonical).exists())

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            actual = validation_root / "actual-round"
            actual.mkdir()
            round_parent = validation_root / ".rd-skills" / "expert-panel"
            round_parent.mkdir(parents=True)
            (round_parent / review_id).symlink_to(
                actual, target_is_directory=True
            )
            self.assertEqual(
                1,
                invoke(
                    validation_root=validation_root,
                    command="build-packet",
                    output=canonical,
                ),
            )
            self.assertFalse((actual / "packet.json").exists())

    def test_schema_two_cli_delegates_to_atomic_create_only_writer(self) -> None:
        review_id = self.packet["review_id"]
        canonical = f".rd-skills/expert-panel/{review_id}/packet.json"

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            (validation_root / "audit.json").write_text(
                "{}\n", encoding="utf-8"
            )
            with mock.patch.object(
                PANEL, "ROOT", validation_root
            ), mock.patch.object(
                PANEL,
                "prepare_packet",
                return_value=copy.deepcopy(self.packet),
            ), mock.patch.object(PANEL, "_write_json") as write_json:
                result = PANEL.main(
                    [
                        "prepare",
                        "--panel-kind",
                        PANEL.READABILITY_PANEL_KIND,
                        "--audit",
                        "audit.json",
                        "--review-id",
                        review_id,
                        "--created-on",
                        "2026-07-18",
                        "--out",
                        canonical,
                    ]
                )

            self.assertEqual(0, result)
            write_json.assert_called_once()
            self.assertEqual(
                (validation_root / canonical).resolve(),
                write_json.call_args.args[0].resolve(),
            )
            self.assertEqual(self.packet, write_json.call_args.args[1])
            self.assertIs(True, write_json.call_args.kwargs["create_only"])
            self.assertIs(
                validation_root,
                write_json.call_args.kwargs["validation_root"],
            )

    def test_schema_two_packet_rejects_sentence_span_line_and_fingerprint_tamper(self) -> None:
        mutations = {
            "sentence": lambda finding: finding.__setitem__(
                "sentence", finding["sentence"] + " changed"
            ),
            "sentence-fingerprint": lambda finding: finding.__setitem__(
                "sentence_fingerprint", "0" * 64
            ),
            "line": lambda finding: finding.__setitem__(
                "line", finding["line"] + 1
            ),
            "span": lambda finding: finding["source_span"].__setitem__(
                "end_offset", finding["source_span"]["end_offset"] - 1
            ),
        }
        for label, mutate in mutations.items():
            changed = copy.deepcopy(self.packet)
            mutate(changed["readability_targets"][0]["findings"][0])
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL.validate_packet(changed)

    def test_schema_two_packet_rejects_context_identity_and_inventory_tamper(
        self,
    ) -> None:
        def mutate_selector(packet: dict) -> None:
            packet["readability_targets"][0]["source_selector"]["path"] = (
                "src/other.md"
            )

        def mutate_context(packet: dict) -> None:
            packet["readability_targets"][0]["document_context"]["lines"][0][
                "text"
            ] += " changed"

        def mutate_finding_id(packet: dict) -> None:
            packet["readability_targets"][0]["findings"][0]["finding_id"] = (
                "0" * 64
            )

        def mutate_column(packet: dict) -> None:
            packet["readability_targets"][0]["findings"][0]["source_span"][
                "start_column"
            ] += 1

        def mutate_span_digest(packet: dict) -> None:
            packet["readability_targets"][0]["findings"][0]["source_span"][
                "sha256"
            ] = "0" * 64

        def delete_inventory_member(packet: dict) -> None:
            packet["readability_targets"].pop()

        for label, mutate in (
            ("selector", mutate_selector),
            ("context", mutate_context),
            ("finding-id", mutate_finding_id),
            ("column", mutate_column),
            ("span-digest", mutate_span_digest),
            ("inventory-deletion", delete_inventory_member),
        ):
            changed = copy.deepcopy(self.packet)
            mutate(changed)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL.validate_packet(changed)

    def test_prior_schema_two_r7_shape_is_not_formal_current_contract(self) -> None:
        prior = copy.deepcopy(self.packet)
        prior["panel_contract"].pop("readability_document_decision_method")
        prior["panel_contract"].pop("readability_reviewer_derivation")
        with self.assertRaisesRegex(PANEL.PanelReviewError, "panel_contract"):
            PANEL.validate_packet(prior)

    def test_schema_two_ballot_requires_exact_finding_review_coverage(self) -> None:
        digest = "a" * 64
        original = self._ballot(self.packet, digest, 1)
        target_vote = next(
            row for row in original["readability_votes"] if len(row["finding_reviews"]) > 1
        )
        for label, mutate in (
            (
                "missing",
                lambda reviews: reviews.pop(),
            ),
            (
                "duplicate",
                lambda reviews: reviews.__setitem__(-1, copy.deepcopy(reviews[0])),
            ),
            (
                "replaced",
                lambda reviews: reviews[0].__setitem__("finding_id", "f" * 64),
            ),
        ):
            ballot = copy.deepcopy(original)
            reviews = next(
                row["finding_reviews"]
                for row in ballot["readability_votes"]
                if row["document_id"] == target_vote["document_id"]
            )
            mutate(reviews)
            with self.subTest(label=label), self.assertRaisesRegex(
                PANEL.PanelReviewError, "finding_reviews"
            ):
                PANEL.validate_ballot(
                    self.packet, ballot, packet_sha256=digest
                )

    def test_full_actionability_ballot_validates_and_aggregates(self) -> None:
        packet = self._synthetic_actionability_packet()
        with self._current_readability_authority(
            packet
        ), tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write(packet_path, packet)
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter in range(1, 4):
                ballot_path = root / f"actionability-expert-{voter}.json"
                ballot = self._ballot(packet, packet_sha, voter)
                _write(ballot_path, ballot)
                PANEL.validate_ballot(
                    packet, ballot, packet_sha256=packet_sha
                )
                ballot_values.append((ballot_path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-17",
            )
            decision_path = root / "decision.json"
            _write(decision_path, record)
            PANEL.validate_decision_record(record, record_path=decision_path)

            target = packet["actionability_targets"][0]
            target_source = (ROOT / target["path"]).resolve()
            evidence_line = next(
                item
                for item in record["actionability_decisions"]
                if item["target_id"] == target["target_id"]
            )["winning_rationales"][0]["evidence"][0]["line"]
            original_read_text = Path.read_text

            def changed_source_read_text(path: Path, *args, **kwargs) -> str:
                content = original_read_text(path, *args, **kwargs)
                if path.resolve() != target_source:
                    return content
                lines = content.splitlines()
                lines[evidence_line - 1] = ""
                suffix = "\n" if content.endswith("\n") else ""
                return "\n".join(lines) + suffix

            with mock.patch.object(
                Path,
                "read_text",
                new=changed_source_read_text,
            ), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "target or detector authority is stale|source is stale|inventory are stale",
            ):
                PANEL.validate_decision_record(record, record_path=decision_path)

        self.assertEqual(1, len(record["actionability_decisions"]))
        self.assertEqual(
            {
                "accepted-current-actionability": 1,
                "detector-false-positive": 0,
                "rewrite-required": 0,
            },
            record["summary"]["actionability"],
        )

    def test_document_majority_is_fail_closed_from_nested_finding_reviews(self) -> None:
        packet = self._synthetic_actionability_packet()
        target = next(
            row for row in packet["readability_targets"] if len(row["findings"]) >= 2
        )
        with self._current_readability_authority(
            packet
        ), tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write(packet_path, packet)
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter in range(1, 4):
                ballot = self._ballot(packet, packet_sha, voter)
                document_vote = next(
                    row
                    for row in ballot["readability_votes"]
                    if row["document_id"] == target["document_id"]
                )
                if voter <= 2:
                    finding = document_vote["finding_reviews"][voter - 1]
                    finding.update(
                        decision="tracked-tightening",
                        reason_code="multiple-independent-actions",
                        rationale=(
                            "This exact finding contains separable actions that need "
                            "a tracked tightening disposition."
                        ),
                    )
                ballot_path = root / f"reviewer-{voter}.json"
                _write(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-18",
            )
        decision = next(
            row
            for row in record["readability_decisions"]
            if row["document_id"] == target["document_id"]
        )
        self.assertEqual("tracked-tightening", decision["winning_disposition"])
        self.assertTrue(
            all(
                item["winning_disposition"] == "accepted-current-readability"
                for item in decision["finding_decisions"][:2]
            )
        )
        self.assertTrue(
            record["actionability_decisions"][0]["winning_rationales"][0][
                "evidence"
            ]
        )

    def test_actionability_ballot_requires_exact_coverage_and_valid_evidence(self) -> None:
        packet = self._synthetic_actionability_packet()
        with self._current_readability_authority(
            packet
        ), tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write(packet_path, packet)
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = self._ballot(packet, packet_sha, 1)

            missing = copy.deepcopy(ballot)
            missing["actionability_votes"].pop()
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "coverage does not match"
            ):
                PANEL.validate_ballot(
                    packet, missing, packet_sha256=packet_sha
                )

            invalid = copy.deepcopy(ballot)
            invalid["actionability_votes"][0]["decision"] = "abstain"
            with self.assertRaisesRegex(PANEL.PanelReviewError, "abstention"):
                PANEL.validate_ballot(
                    packet, invalid, packet_sha256=packet_sha
                )

            stale = copy.deepcopy(ballot)
            stale["actionability_votes"][0]["evidence"][0]["source_line"] += " stale"
            with self.assertRaisesRegex(PANEL.PanelReviewError, "source_line is stale"):
                PANEL.validate_ballot(
                    packet, stale, packet_sha256=packet_sha
                )

            outside = copy.deepcopy(ballot)
            target_id = outside["actionability_votes"][0]["target_id"]
            target = next(
                row
                for row in packet["actionability_targets"]
                if row["target_id"] == target_id
            )
            outside["actionability_votes"][0]["evidence"][0]["line"] = (
                target["front_window"]["end_line"] + 1
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "outside"):
                PANEL.validate_ballot(
                    packet, outside, packet_sha256=packet_sha
                )

            targets = {
                target["target_id"]: target
                for target in packet["actionability_targets"]
            }

            def find_non_substantive_line(predicate):
                for vote_index, vote in enumerate(ballot["actionability_votes"]):
                    target = targets[vote["target_id"]]
                    for row in target["front_window"]["lines"]:
                        if predicate(row["text"]):
                            return vote_index, row
                raise AssertionError("fixture lacks requested non-substantive line")

            blank_index, blank_line = find_non_substantive_line(
                lambda text: not text.strip()
            )
            blank = copy.deepcopy(ballot)
            blank["actionability_votes"][blank_index]["evidence"] = [
                {
                    "line": blank_line["line"],
                    "source_line": blank_line["text"],
                    "claim": "Blank lines cannot establish executable action evidence here.",
                }
            ]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "substantive body text"):
                PANEL.validate_ballot(packet, blank, packet_sha256=packet_sha)

            heading_index, heading_line = find_non_substantive_line(
                lambda text: text.strip().startswith("#")
            )
            heading = copy.deepcopy(ballot)
            heading["actionability_votes"][heading_index]["evidence"] = [
                {
                    "line": heading_line["line"],
                    "source_line": heading_line["text"],
                    "claim": "Heading text alone cannot establish executable action evidence.",
                }
            ]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "substantive body text"):
                PANEL.validate_ballot(packet, heading, packet_sha256=packet_sha)

            mismatch = copy.deepcopy(ballot)
            mismatch["actionability_votes"][0]["evidence"][0]["claim"] = (
                "Zygote quasar nebula claims unrelated platypus semantics today."
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "overlap"):
                PANEL.validate_ballot(
                    packet, mismatch, packet_sha256=packet_sha
                )

    def test_fenced_window_content_cannot_support_actionability_evidence(self) -> None:
        texts = [
            "- Example:",
            "  ```python",
            "  validate_action()",
            "  ```",
            "Use the owned rule to validate the real decision.",
        ]
        start_line = 10
        window = {
            "start_line": start_line,
            "end_line": start_line + len(texts) - 1,
            "line_count": len(texts),
            "lines": [
                {"line": start_line + index, "text": text}
                for index, text in enumerate(texts)
            ],
            "sha256": hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest(),
        }
        PANEL._validate_actionability_front_window(
            window,
            label="fixture.front_window",
            limit=60,
        )
        self.assertFalse(
            PANEL._actionability_window_line_is_substantive(window, start_line + 2)
        )
        self.assertTrue(
            PANEL._actionability_window_line_is_substantive(window, start_line + 4)
        )

        packet = self._synthetic_actionability_packet()
        target = packet["actionability_targets"][0]
        target["front_window"] = window
        with self._current_readability_authority(
            packet, track_source_changes=False
        ):
            PANEL.validate_packet(packet)
        with self._current_readability_authority(
            packet, track_source_changes=False
        ), tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write(packet_path, packet)
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = self._ballot(packet, packet_sha, 1)
            vote = next(
                item
                for item in ballot["actionability_votes"]
                if item["target_id"] == target["target_id"]
            )
            vote["evidence"] = [
                {
                    "line": start_line + 2,
                    "source_line": texts[2],
                    "claim": (
                        "The validate action example is fenced and cannot prove "
                        "an executable instruction."
                    ),
                }
            ]
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "substantive body text"
            ):
                PANEL.validate_ballot(packet, ballot, packet_sha256=packet_sha)

    def test_majority_rewrite_is_counted_and_blocks_formal_predicate(self) -> None:
        packet = self._synthetic_actionability_packet()
        with self._current_readability_authority(
            packet
        ), tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write(packet_path, packet)
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter in range(1, 4):
                ballot_path = root / f"actionability-expert-{voter}.json"
                ballot = self._ballot(
                    packet,
                    packet_sha,
                    voter,
                    actionability_decision=(
                        "rewrite-required" if voter < 3 else "detector-false-positive"
                    ),
                )
                _write(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-17",
            )
        self.assertEqual(
            {
                "accepted-current-actionability": 0,
                "detector-false-positive": 0,
                "rewrite-required": 1,
            },
            record["summary"]["actionability"],
        )
        formal = {
            "panel_kind": PANEL.READABILITY_PANEL_KIND,
            "scope": "ai-readability-and-density",
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": False,
            "decision_method": PANEL.DECISION_METHOD,
            "panel_size": PANEL.PANEL_SIZE,
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": 2,
            "attestation_status": "panel-majority-actionability-rewrite-required",
            "tracked_tightening_count": 0,
            "rewrite_required_count": 1,
            "blocker_count": 0,
            "required_density_disposition_count": 2,
            "applied_density_disposition_count": 2,
            "required_readability_disposition_count": 298,
            "applied_readability_disposition_count": 298,
            "required_actionability_disposition_count": 1,
            "applied_actionability_disposition_count": 1,
        }
        self.assertFalse(REGRESSION._readability_review_formal_ready(formal))

    def test_schema_one_readability_artifacts_remain_historical_only(self) -> None:
        formal = {
            "panel_kind": PANEL.READABILITY_PANEL_KIND,
            "scope": "ai-readability-and-density",
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": True,
            "decision_method": PANEL.DECISION_METHOD,
            "panel_size": PANEL.PANEL_SIZE,
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": 1,
            "attestation_status": "panel-majority-current",
            "tracked_tightening_count": 0,
            "rewrite_required_count": 0,
            "blocker_count": 0,
            "required_density_disposition_count": 1,
            "applied_density_disposition_count": 1,
            "required_readability_disposition_count": 1,
            "applied_readability_disposition_count": 1,
            "required_actionability_disposition_count": 0,
            "applied_actionability_disposition_count": 0,
        }
        self.assertFalse(REGRESSION._readability_review_formal_ready(formal))

    def test_regression_reports_all_weak_skills_not_professional_subset(self) -> None:
        summary = REGRESSION._content_audit_summary(self.audit)
        self.assertEqual(0, summary["weak_front_loaded_skills"])
        self.assertEqual(
            self.audit["summary"]["review_reasons"]["weak_front_loaded_action"],
            summary["weak_front_loaded_skills"],
        )

    def test_unknown_professional_expertise_tag_is_rejected(self) -> None:
        with self.assertRaisesRegex(PANEL.PanelReviewError, "unknown expertise tag"):
            PANEL._expertise_tags(
                ["not-a-registered-expertise"],
                label="fixture.expertise_tags",
                allow_architecture=False,
            )


if __name__ == "__main__":
    unittest.main()
