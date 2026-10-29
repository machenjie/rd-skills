import copy
import importlib.util
import os
import unittest
from pathlib import Path


OLD = "def accepts(units):\n    return units >= 0\n"
FIXED = "def accepts(units):\n    return units >= 1\n"
HEAD = "commit-current"
PATH = "quantity.py"


def subject():
    path = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"]) / "subject.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finding(identity="f1", commit=HEAD, kind="defect", minimum=1):
    return {"id": identity, "commit": commit, "path": PATH, "anchor": OLD.splitlines()[1],
            "kind": kind, "subject": "accepted quantity", "minimum": minimum}


def proof(source=OLD, commit=HEAD, relocated=False):
    """Observed outcomes come from execution, not an expected-result input flag."""
    namespace = {"__builtins__": {}}
    exec(compile(source, "quantity.py", "exec"), namespace)
    result = {"commit": commit, "source": source, "line": 2, "anchor": source.splitlines()[1],
              "observations": [{"units": units, "accepted": namespace["accepts"](units)} for units in range(4)]}
    if relocated:
        result["relocates_from"] = OLD.splitlines()[1]
    return result


def plan(choice="accept", reason="Zero quantities violate the supplied positive-unit rule."):
    return {"choice": choice, "reason": reason,
            "edit": {"path": PATH, "line": 2, "before": OLD.splitlines()[1], "after": FIXED.splitlines()[1]},
            "validation": {"check": "execute quantity boundary cases", "inputs": [0, 1, 2]},
            "remaining_risk": "Only integer boundary probes are covered; callers and concurrent updates remain unproved."}


class FeedbackAssertions(unittest.TestCase):
    def test_current_verified_finding_maps_to_bounded_edit_and_proof(self):
        data = ({PATH: OLD}, [finding()], {PATH: proof()}, {"f1": plan()})
        before = copy.deepcopy(data)
        result = subject().triage(HEAD, *data)["f1"]
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["commit"], HEAD)
        self.assertEqual(result["anchor"], {"path": PATH, "line": 2, "text": OLD.splitlines()[1]})
        self.assertEqual(result["validation"]["inputs"], [0, 1, 2])
        self.assertTrue(result["remaining_risk"])
        lines = OLD.splitlines(keepends=True)
        lines[result["edit"]["line"] - 1] = result["edit"]["after"] + "\n"
        actual = proof("".join(lines))["observations"]
        self.assertEqual([item["accepted"] for item in actual], [False, True, True, True])
        self.assertEqual(data, before)

    def test_old_commit_can_remain_valid_after_current_reverification(self):
        old = finding(commit="commit-before-rebase")
        result = subject().triage(HEAD, {PATH: OLD}, [old], {PATH: proof()}, {"f1": plan()})["f1"]
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["origin_commit"], "commit-before-rebase")
        self.assertEqual(result["commit"], HEAD)

    def test_stale_mismatched_and_insufficient_proofs_cannot_accept(self):
        wrong_anchor = proof()
        wrong_anchor["line"] = 1
        sparse = proof()
        sparse["observations"] = sparse["observations"][:1]
        for evidence in (proof(commit="old"), proof(FIXED), wrong_anchor, sparse):
            with self.subTest(evidence=evidence):
                result = subject().triage(HEAD, {PATH: OLD}, [finding()], {PATH: evidence}, {"f1": plan()})["f1"]
                self.assertEqual(result["status"], "needs-validation")
                self.assertNotIn("edit", result)

    def test_obsolete_and_already_fixed_are_distinct(self):
        missing = subject().triage(HEAD, {}, [finding()], {}, {})["f1"]
        self.assertEqual(missing["status"], "obsolete")
        changed = subject().triage(HEAD, {PATH: FIXED}, [finding()], {PATH: proof(FIXED)}, {})["f1"]
        self.assertEqual(changed["status"], "obsolete")
        fixed = subject().triage(HEAD, {PATH: FIXED}, [finding()], {PATH: proof(FIXED, relocated=True)}, {})["f1"]
        self.assertEqual(fixed["status"], "resolved")
        self.assertNotIn("edit", fixed)

    def test_duplicate_and_conflicting_rules_are_not_blindly_applied(self):
        duplicate = subject().triage(HEAD, {PATH: OLD}, [finding(), finding("f2")], {PATH: proof()}, {"f1": plan()})
        self.assertEqual(duplicate["f1"]["status"], "accepted")
        self.assertEqual(duplicate["f2"]["status"], "duplicate")
        self.assertEqual(duplicate["f2"]["canonical"], "f1")
        conflict = subject().triage(HEAD, {PATH: OLD}, [finding(), finding("f2", minimum=2)], {PATH: proof()}, {"f1": plan(), "f2": plan()})
        self.assertEqual([conflict[key]["status"] for key in ("f1", "f2")], ["conflicting", "conflicting"])
        self.assertTrue(all("edit" not in value for value in conflict.values()))
        already_satisfied = subject().triage(HEAD, {PATH: FIXED}, [finding(), finding("f2", minimum=2)], {PATH: proof(FIXED, relocated=True)}, {})
        self.assertEqual([already_satisfied[key]["status"] for key in ("f1", "f2")], ["conflicting", "conflicting"])

    def test_feedback_kinds_rejections_and_alternatives_keep_reasons(self):
        kinds = [finding("suggest", kind="suggestion"), finding("style", kind="preference"),
                 finding("ask", kind="question"), finding("scope", kind="out-of-scope")]
        rejected = {"suggest": {"choice": "reject", "reason": "The requested threshold conflicts with this task's accepted quantity contract."},
                    "style": {"choice": "reject", "reason": "The repository formatter already owns this spelling."}}
        result = subject().triage(HEAD, {PATH: OLD}, kinds, {PATH: proof()}, rejected)
        self.assertEqual([result[key]["status"] for key in ("suggest", "style", "ask", "scope")],
                         ["rejected", "rejected", "question", "out-of-scope"])
        self.assertEqual([result[item["id"]]["kind"] for item in kinds], [item["kind"] for item in kinds])
        self.assertEqual(result["suggest"]["reason"], rejected["suggest"]["reason"])
        no_reason = subject().triage(HEAD, {PATH: OLD}, [finding()], {PATH: proof()}, {"f1": {"choice": "reject"}})["f1"]
        self.assertEqual(no_reason["status"], "needs-decision")
        alternative = subject().triage(HEAD, {PATH: OLD}, [finding()], {PATH: proof()}, {"f1": plan("alternative", "Keep this change in the existing quantity boundary instead of adding a new validator.")})["f1"]
        self.assertEqual(alternative["status"], "alternative")
        self.assertTrue(alternative["reason"])
        for field in ("edit", "validation", "remaining_risk"):
            incomplete = plan()
            incomplete.pop(field)
            result = subject().triage(HEAD, {PATH: OLD}, [finding()], {PATH: proof()}, {"f1": incomplete})["f1"]
            self.assertEqual(result["status"], "needs-plan")

    def test_every_authority_boundary_is_independent(self):
        accepted = subject().triage(HEAD, {PATH: OLD}, [finding()], {PATH: proof()}, {"f1": plan()})["f1"]
        names = ("judge", "edit", "reply", "resolve", "request-rereview")
        for granted in names:
            with self.subTest(granted=granted):
                permissions = subject().action_permissions("task-agent", {granted}, accepted)
                self.assertEqual({name for name, value in permissions.items() if value["authorized"]}, {granted})
        fixed = subject().triage(HEAD, {PATH: FIXED}, [finding()], {PATH: proof(FIXED, relocated=True)}, {})["f1"]
        self.assertTrue(all(not item["authorized"] for item in subject().action_permissions("task-agent", set(), fixed).values()))
        permissions = subject().action_permissions("review-agent", set(names), accepted)
        self.assertEqual({name for name, value in permissions.items() if value["authorized"]}, {"judge"})
        permissions = subject().action_permissions("analysis-agent", set(names), accepted)
        self.assertEqual({name for name, value in permissions.items() if value["authorized"]}, {"judge"})
        self.assertFalse(subject().action_permissions("task-agent", {"edit"}, fixed)["edit"]["authorized"])
        with self.assertRaises(ValueError):
            subject().action_permissions("task-agent", {"merge"}, accepted)

    def test_invalid_record_identity_and_role_are_rejected(self):
        with self.assertRaises(ValueError):
            subject().triage(HEAD, {PATH: OLD}, [finding(), finding()], {PATH: proof()}, {})
        with self.assertRaises(ValueError):
            subject().triage(HEAD, {PATH: OLD}, [finding(kind="approval")], {PATH: proof()}, {})
        with self.assertRaises(ValueError):
            subject().action_permissions("unowned-role", {"judge"}, {})
