from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "src/control-model/core-contracts.json"
VALIDATION_PATH = ROOT / "scripts/validation_utils.py"
FOUNDATION_REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src/registry/domain-skills.yaml"
SKILL_ROOT = ROOT / "src/foundation/capabilities/filesystem-process-safety"
TRUST_REFERENCE = "references/trust-sensitive-filesystem-process-protection.md"


def _load_validation():
    spec = importlib.util.spec_from_file_location(
        "filesystem_process_validation_utils", VALIDATION_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FilesystemProcessSafetyCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validation = _load_validation()
        cls.core = json.loads(CORE_PATH.read_text(encoding="utf-8"))
        cls.foundation = cls.validation.load_yaml_file(FOUNDATION_REGISTRY)
        cls.professional = cls.validation.load_yaml_file(PROFESSIONAL_REGISTRY)
        cls.domain = cls.validation.load_yaml_file(DOMAIN_REGISTRY)
        cls.foundation_by_name = {
            row["name"]: row for row in cls.foundation["foundation_skills"]
        }

    def test_core_projection_is_exact_and_dereferences_the_candidate(self) -> None:
        expected = {
            "skill": "filesystem-process-safety",
            "selection_effects": [
                "filesystem-effect",
                "direct-child-process-effect",
            ],
            "normal_correctness": [
                "create-replace",
                "atomicity",
                "durability",
                "legitimate-concurrency",
                "cleanup",
                "wait-reap",
                "stdout-stderr",
                "timeout-cancellation",
                "result-reconciliation",
            ],
            "trust_sensitive_reference": TRUST_REFERENCE,
            "trust_load_branches": [
                "current-related-concrete-reachable-trust-evidence",
                "complete-related-critical_unknown",
            ],
            "not_escalation_evidence_refs": [
                "#/environment_risk_calibration_contract/not_escalation_evidence/0",
                "#/environment_risk_calibration_contract/not_escalation_evidence/1",
                "#/environment_risk_calibration_contract/not_escalation_evidence/2",
                "#/environment_risk_calibration_contract/not_escalation_evidence/3",
            ],
            "material_escalation_refs": [
                "#/environment_risk_calibration_contract/escalation_requires_all/0",
                "#/environment_risk_calibration_contract/escalation_requires_all/1",
                "#/environment_risk_calibration_contract/escalation_requires_all/2",
            ],
            "critical_unknown_ref": "#/execution_level_contract/critical_unknown",
            "independent_risk_refs": [
                "#/environment_risk_calibration_contract/independent_risks/0",
                "#/environment_risk_calibration_contract/independent_risks/1",
                "#/environment_risk_calibration_contract/independent_risks/2",
                "#/environment_risk_calibration_contract/independent_risks/3",
                "#/environment_risk_calibration_contract/independent_risks/4",
                "#/environment_risk_calibration_contract/independent_risks/5",
                "#/environment_risk_calibration_contract/independent_risks/6",
                "#/environment_risk_calibration_contract/independent_risks/7",
            ],
        }
        environment = self.core["environment_risk_calibration_contract"]
        self.assertIn("filesystem_process_safety_projection", environment)
        self.assertEqual(
            expected,
            environment["filesystem_process_safety_projection"],
        )
        self.assertEqual([], self.validation.validate_core_contracts(self.core))

        extra = copy.deepcopy(self.core)
        extra["environment_risk_calibration_contract"][
            "filesystem_process_safety_projection"
        ]["extra"] = True
        target = copy.deepcopy(self.core)
        target["environment_risk_calibration_contract"][
            "not_escalation_evidence"
        ][0] = "mutated-ordinary-mutability"
        pointer = copy.deepcopy(self.core)
        pointer["environment_risk_calibration_contract"][
            "filesystem_process_safety_projection"
        ]["critical_unknown_ref"] = "#/environment_risk_calibration_contract/baseline"
        mutations = [
            (
                extra,
                "environment_risk_calibration_contract."
                "filesystem_process_safety_projection",
            ),
            (target, "environment risk calibration"),
            (
                pointer,
                "environment_risk_calibration_contract."
                "filesystem_process_safety_projection",
            ),
        ]
        for candidate, failure_class in mutations:
            with self.subTest(failure_class=failure_class):
                errors = self.validation.validate_core_contracts(candidate)
                self.assertTrue(
                    any(error.startswith(failure_class) for error in errors),
                    errors,
                )

    def test_registry_preserves_effect_selection_and_adds_one_jit_reference(self) -> None:
        row = self.foundation_by_name["filesystem-process-safety"]
        self.assertEqual(
            [
                "local file mutation path resolution file protection writer trust "
                "classification or direct child-process control changes application behavior"
            ],
            row["trigger_signals"],
        )
        self.assertEqual(
            "a path or mutability is mentioned but no filesystem behavior or direct "
            "child-process behavior changes",
            row["anti_trigger_signals"][2],
        )
        contracts = self.validation.reference_contracts(
            row["reference_index"],
            "filesystem-process-safety.reference_index",
            owner="filesystem-process-safety",
        )
        self.assertEqual(3, len(contracts))
        self.assertEqual(
            {
                "path": TRUST_REFERENCE,
                "type": "targeted",
                "load_when": (
                    "A current filesystem or direct child-process effect has concrete "
                    "reachable trust evidence, or a complete related Core critical unknown remains"
                ),
                "do_not_load_when": (
                    "Only normal filesystem or process correctness applies, or trust evidence "
                    "is generic, disconnected from the current effect, or unreachable"
                ),
                "required_by": ["analysis-agent", "task-agent", "review-agent"],
                "required_output": [
                    "boundary-decision",
                    "proof-limit",
                    "residual-risk",
                ],
            },
            contracts[2],
        )
        declarations = row["context_admissibility"]["references"]
        self.assertNotIn(TRUST_REFERENCE, declarations)

    def test_undeclared_trust_reference_projects_a_null_runtime_record(self) -> None:
        authority = self.validation.layer3_selector_authority(
            self.foundation,
            self.professional,
            self.domain,
            context="filesystem/process calibration",
        )
        records = authority["runtime_professionals"][
            "repository-tooling-change-builder"
        ]["reference_records"]
        record = next(
            item
            for item in records
            if item["owner_skill"] == "filesystem-process-safety"
            and item["path"] == TRUST_REFERENCE
        )
        self.assertIsNone(record["context_admissibility"])
        self.assertEqual("singleton", record["residency"])

    def test_normal_references_keep_correctness_without_trust_proof(self) -> None:
        atomic = (SKILL_ROOT / "references/atomic-filesystem-commit-and-containment.md").read_text(
            encoding="utf-8"
        )
        trust = (SKILL_ROOT / TRUST_REFERENCE).read_text(encoding="utf-8")
        child = (SKILL_ROOT / "references/child-process-invocation-and-completion.md").read_text(
            encoding="utf-8"
        )
        for anchor in (
            "exclusive temporary creation",
            "create or replace intent",
            "legitimate concurrency",
            "atomic reader visibility",
            "crash durability",
            "cleanup",
        ):
            self.assertIn(anchor.casefold(), atomic.casefold())
        for anchor in (
            "structured argv",
            "wait and reap",
            "stdout/stderr",
            "timeout and cancellation",
            "result reconciliation",
            "cleanup",
        ):
            self.assertIn(anchor.casefold(), child.casefold())
        forbidden = (
            "attacker-writable",
            "security descriptor",
            "antivirus",
            "filter driver",
            "privileged consumer",
            "untrusted executable lookup",
            "credential or sandbox authority",
            "secret handle exposure",
        )
        for text in (atomic, child):
            for phrase in forbidden:
                with self.subTest(phrase=phrase):
                    self.assertNotIn(phrase, text.casefold())
        for source_link in (
            "- [Microsoft `CreateFileW`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)",
            "- [Microsoft reparse points and file operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations)",
            "- [Microsoft file security and access rights](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights)",
        ):
            with self.subTest(source_link=source_link):
                self.assertEqual(1, trust.count(source_link))
                self.assertEqual(0, atomic.count(source_link))

    def test_trust_reference_has_two_load_branches_and_three_material_dimensions(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        trust = (SKILL_ROOT / TRUST_REFERENCE).read_text(encoding="utf-8")
        self.assertIn(TRUST_REFERENCE, skill)
        self.assertIn("concrete reachable trust evidence", skill)
        self.assertIn("complete related `critical_unknown`", skill)
        self.assertIn("same_trust_principal", trust)
        self.assertIn("critical_unknown", trust)
        self.assertIn("material_assessment", trust)
        for heading in (
            "### Less-trusted actor, input, or writer",
            "### Privilege or sensitive asset",
            "### Reachable material impact path",
        ):
            self.assertEqual(1, trust.count(heading))
        trust_casefold = trust.casefold()
        for trigger in (
            "attacker-controlled path, link, or reparse point",
            "ACL or security descriptor",
            "privileged consumer",
            "untrusted executable lookup",
            "credential or sandbox authority",
            "secret handle exposure",
        ):
            self.assertIn(trigger.casefold(), trust_casefold)


if __name__ == "__main__":
    unittest.main()
