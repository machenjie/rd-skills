from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PANEL = _load("actionability_panel_fixture", "scripts/expert_panel_review.py")
REGRESSION = _load(
    "actionability_regression_fixture",
    "scripts/validate-professionalism-regression.py",
)


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class ExpertPanelActionabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(
            (ROOT / "reports/skill-content-audit.json").read_text(encoding="utf-8")
        )
        auditor = PANEL._load_skill_content_auditor()
        cls.audit["ai_readability"] = auditor._collect_ai_readability(
            auditor._ai_readability_documents()
        )
        cls.readiness = json.loads(
            (ROOT / "reports/professionalism-release-readiness.json").read_text(
                encoding="utf-8"
            )
        )
        cls.packet = PANEL.prepare_packet(
            audit=cls.audit,
            readiness=cls.readiness,
            review_id="actionability-v2-fixture",
            created_on="2026-07-17",
        )

    @staticmethod
    def _first_substantive_window_line(target: dict) -> tuple[int, str, str]:
        for row in target["front_window"]["lines"]:
            tokens = sorted(PANEL._evidence_tokens(row["text"]))
            if (
                PANEL._actionability_window_line_is_substantive(
                    target["front_window"], row["line"]
                )
                and tokens
            ):
                return row["line"], row["text"], tokens[0]
        raise AssertionError("front window lacks substantive actionability evidence")

    def _ballot(
        self,
        packet: dict,
        packet_sha256: str,
        voter: int,
        *,
        actionability_decision: str = "accepted-current-actionability",
    ) -> dict:
        ballot = PANEL.prepare_readability_ballot_template(
            packet=packet,
            packet_sha256=packet_sha256,
            voter_id=f"actionability-expert-{voter}",
            agent_id=f"actionability-agent-{voter}",
            role=f"senior AI instruction actionability reviewer {voter}",
            expertise=["AI instruction semantics and executable action design"],
            created_on="2026-07-17",
        )
        for vote in ballot["content_votes"]:
            vote.update(
                decision="accepted-current-density",
                reason_code="bounded-density-preserves-professional-coverage",
                rationale=(
                    "This bounded density preserves one complete and coherent "
                    "professional decision model."
                ),
            )
        for vote in ballot["readability_votes"]:
            for finding_review in vote["finding_reviews"]:
                finding_review.update(
                    decision="accepted-current-readability",
                    reason_code="single-indivisible-decision",
                    rationale=(
                        "This sentence preserves one complete and coherent decision "
                        "without separable instructions."
                    ),
                )
        targets = {
            target["target_id"]: target
            for target in packet["actionability_targets"]
        }
        reason_code = {
            "accepted-current-actionability": (
                "explicit-domain-actions-are-front-loaded"
            ),
            "detector-false-positive": "equivalent-action-verb-not-recognized",
            "rewrite-required": "primary-action-not-front-loaded",
        }[actionability_decision]
        for vote in ballot["actionability_votes"]:
            target = targets[vote["target_id"]]
            line, source_line, source_token = self._first_substantive_window_line(
                target
            )
            vote.update(
                decision=actionability_decision,
                reason_code=reason_code,
                rationale=(
                    "The reviewed opening lines provide concrete evidence for "
                    "this actionability disposition."
                ),
                evidence=[
                    {
                        "line": line,
                        "source_line": source_line,
                        "claim": (
                            f"The {source_token} opening instruction provides concrete "
                            "actionability review evidence."
                        ),
                    }
                ],
            )
        return ballot

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
        if "weak_front_loaded_action" not in candidate["review_reasons"]:
            candidate["review_reasons"].append("weak_front_loaded_action")
        audit["summary"]["actionability_applicable_items"] = 1
        audit["summary"]["weak_front_loaded_action_all_items"] = 1
        return PANEL.prepare_packet(
            audit=audit,
            readiness=self.readiness,
            review_id="synthetic-actionability-target-fixture",
            created_on="2026-07-24",
        )

    def test_prepare_emits_schema_two_and_all_weak_targets(self) -> None:
        packet = self.packet
        self.assertEqual(PANEL.READABILITY_SCHEMA_VERSION, packet["schema_version"])
        self.assertEqual(
            "root-body-document-context-v1",
            packet["panel_contract"]["content_source_binding_contract"],
        )
        self.assertEqual(39, len(packet["content_targets"]))
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
            self.audit["skill_detector"]["detector_fingerprint"]["value"],
            packet["source_fingerprints"]["skill_detector"],
        )
        self.assertEqual(0, len(packet["actionability_targets"]))
        self.assertEqual(
            0,
            packet["panel_contract"]["required_actionability_target_count"],
        )
        target_ids = [row["target_id"] for row in packet["actionability_targets"]]
        self.assertEqual(sorted(set(target_ids)), target_ids)
        self.assertEqual(353, len(packet["readability_targets"]))
        self.assertEqual(
            972,
            sum(len(row["findings"]) for row in packet["readability_targets"]),
        )
        self.assertEqual(
            "finding-grounded-document-majority-v1",
            packet["panel_contract"]["readability_document_decision_method"],
        )
        PANEL.validate_packet(packet)

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
                packet["source_fingerprints"]["ai_readability"],
                stale_content,
                packet["readability_targets"],
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
        candidate["review_reasons"].append("weak_front_loaded_action")
        audit["summary"]["actionability_applicable_items"] = 1
        audit["summary"]["weak_front_loaded_action_all_items"] = 1

        packet = PANEL.prepare_packet(
            audit=audit,
            readiness=self.readiness,
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
            (validation_root / "readiness.json").write_text(
                "{}\n", encoding="utf-8"
            )
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
                        "--readiness",
                        "readiness.json",
                        "--review-id",
                        review_id,
                        "--created-on",
                        "2026-07-18",
                        "--out",
                        output,
                    ]
                )

        canonical = f"evals/expert-panel/{review_id}/packet.json"
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
            round_parent = validation_root / "evals" / "expert-panel"
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
        canonical = f"evals/expert-panel/{review_id}/packet.json"

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            (validation_root / "audit.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (validation_root / "readiness.json").write_text(
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
                        "--readiness",
                        "readiness.json",
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
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
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
                PANEL.PanelReviewError, "source is stale|inventory are stale"
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
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
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
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
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
        PANEL.validate_packet(packet)
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
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
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
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
