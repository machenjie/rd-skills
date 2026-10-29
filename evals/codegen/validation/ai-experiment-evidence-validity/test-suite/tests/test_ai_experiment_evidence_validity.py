from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import unittest

ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def subject():
    spec = importlib.util.spec_from_file_location("candidate_evidence_checks", ROOT / "evidence_checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rag():
    return {"relevant_ids": ["d1", "d2"], "retrieved_ids": ["d1", "d2"],
            "required_claims": ["c1", "c2"], "answer_claims": {"c1": ["d1"], "c2": ["d2"]},
            "evidence_for_claim": {"c1": ["d1"], "c2": ["d2"]},
            "documents": {"d1": {"valid_until": 30, "conflicts_with": []},
                          "d2": {"valid_until": 30, "conflicts_with": []}},
            "as_of": 20, "certain_answer": True}


def training():
    def row(identity, entity, prediction, feature, target, label):
        return {"sample_id": identity, "entity": entity, "prediction_at": prediction,
                "feature_available_at": feature, "target_at": target, "label_available_at": label}
    return {"splits": {"train": [row("tr", "person-a", 5, 4, 8, 9)],
                       "validation": [row("va", "person-b", 12, 11, 15, 16)],
                       "test": [row("te", "person-c", 20, 19, 22, 23)]},
            "split_kind": "time", "training_cutoff": 10,
            "preprocess_fit_ids": ["tr"], "tuning_sample_ids": ["va"],
            "required_resume_components": ["weights", "optimizer", "rng", "sampler"],
            "resume_components": ["weights", "optimizer", "rng", "sampler"],
            "model_manifest": {"model": "m2", "preprocess": "p2", "tokenizer": "t2", "adapter": "a2"},
            "loaded_artifacts": {"model": "m2", "preprocess": "p2", "tokenizer": "t2", "adapter": "a2"}}


def experiment():
    return {"plan": {"assignment_unit": "user", "allocation_weights": {"a": 1, "b": 1},
                     "srm_statistic_limit": 4.0, "minimum_units": 10, "sample_target": 100,
                     "registered_at": 0, "stopping": "fixed", "sequential_method": None,
                     "maximum_looks": 1, "alpha_budget": 0.05,
                     "maximum_hypotheses": 1, "multiplicity_method": "preselected-single"},
            "assignment_counts": {"a": 50, "b": 50}, "analysis_unit": "user",
            "dependence_handling": "independent", "first_assignment_at": 1,
            "stopped_for_effect": False, "decision_looks": 1, "analysis_method": "fixed",
            "spent_alpha": 0.0, "hypotheses_tested": 1, "multiplicity_method": "preselected-single"}


class EvidenceValidityAssertions(unittest.TestCase):
    def test_retrieval_miss_is_distinct_from_answer_omission(self):
        self.assertEqual(subject().evaluate_rag(rag()), set())
        miss = rag()
        miss["retrieved_ids"] = ["d1"]
        miss["answer_claims"] = {"c1": ["d1"]}
        self.assertEqual(subject().evaluate_rag(miss), {"retrieval-miss", "answer-omission"})
        omission = rag()
        del omission["answer_claims"]["c2"]
        self.assertEqual(subject().evaluate_rag(omission), {"answer-omission"})
        misused = rag()
        misused["answer_claims"]["c1"] = ["d2"]
        self.assertEqual(subject().evaluate_rag(misused), {"unsupported-claim"})

    def test_no_answer_conflicting_and_stale_evidence_cannot_certify_claims(self):
        no_answer = rag()
        no_answer["relevant_ids"] = []
        no_answer["required_claims"] = []
        no_answer["evidence_for_claim"] = {}
        self.assertEqual(subject().evaluate_rag(no_answer), {"unsupported-claim", "unsupported-certainty"})
        conflicting = rag()
        conflicting["documents"]["d1"]["conflicts_with"] = ["d2"]
        conflicting["documents"]["d2"]["valid_until"] = 19
        self.assertEqual(subject().evaluate_rag(conflicting), {"conflicting-evidence", "stale-evidence"})
        abstained = deepcopy(no_answer)
        abstained["certain_answer"] = False
        abstained["answer_claims"] = {}
        self.assertEqual(subject().evaluate_rag(abstained), set())

    def test_trials_use_real_terminal_state_and_declared_uncertainty_budgets(self):
        records = [{"trial_id": str(i), "reported_success": True, "terminal_state": "committed",
                    "latency": i + 1, "cost": 2} for i in range(3)]
        plan = {"minimum_trials": 3, "tuning_case_ids": ["train"], "heldout_case_ids": ["eval"],
                "success_terminal": "committed", "minimum_quality": 0.8,
                "maximum_latency": 5, "maximum_total_cost": 10}
        good = subject().evaluate_trials(records, plan)
        self.assertTrue(good["eligible_for_acceptance"])
        bad = deepcopy(records)
        bad[-1]["terminal_state"] = "pending"
        result = subject().evaluate_trials(bad, plan)
        self.assertEqual(result["actual_successes"], 2)
        self.assertAlmostEqual(result["quality"], 2 / 3)
        self.assertEqual(result["issues"], {"success-claim-mismatch", "quality-below-plan"})
        self.assertIn("insufficient-trials", subject().evaluate_trials(records[:1], plan)["issues"])
        contaminated = dict(plan, tuning_case_ids=["eval"])
        self.assertIn("evaluation-contamination", subject().evaluate_trials(records, contaminated)["issues"])
        self.assertIn("duplicate-trial", subject().evaluate_trials(records + [records[0]], plan)["issues"])
        slow = deepcopy(records)
        slow[0]["latency"] = 20
        self.assertEqual(subject().evaluate_trials(slow, plan)["issues"], {"latency-above-plan"})
        expensive = deepcopy(records)
        expensive[0]["cost"] = 20
        self.assertEqual(subject().evaluate_trials(expensive, plan)["issues"], {"cost-above-plan"})

    def test_future_prediction_target_is_valid_but_future_features_and_immature_labels_are_not(self):
        record = training()
        self.assertGreater(record["splits"]["train"][0]["target_at"], record["splits"]["train"][0]["prediction_at"])
        self.assertEqual(subject().validate_training(record), set())
        future = deepcopy(record)
        future["splits"]["train"][0]["feature_available_at"] = 6
        self.assertEqual(subject().validate_training(future), {"future-feature"})
        immature = deepcopy(record)
        immature["splits"]["train"][0]["label_available_at"] = 11
        self.assertEqual(subject().validate_training(immature), {"immature-training-label"})

    def test_entity_time_preprocessing_and_final_holdout_boundaries(self):
        record = training()
        record["split_kind"] = "entity"
        record["splits"]["test"][0]["entity"] = "person-a"
        self.assertEqual(subject().validate_training(record), {"entity-leakage"})
        time = training()
        time["splits"]["test"][0]["prediction_at"] = 9
        time["splits"]["test"][0]["feature_available_at"] = 8
        self.assertEqual(subject().validate_training(time), {"time-split-leakage"})
        fit = training()
        fit["preprocess_fit_ids"] += ["te"]
        fit["tuning_sample_ids"] += ["te"]
        self.assertEqual(subject().validate_training(fit), {"preprocessing-leakage", "heldout-used-for-tuning"})
        repeated = training()
        repeated["splits"]["test"][0]["sample_id"] = "tr"
        self.assertEqual(subject().validate_training(repeated), {"sample-leakage"})

    def test_resume_and_model_bundle_require_the_declared_components(self):
        record = training()
        record["resume_components"].remove("optimizer")
        record["loaded_artifacts"]["tokenizer"] = "old"
        self.assertEqual(subject().validate_training(record), {"incomplete-resume", "artifact-mismatch"})
        for artifact in ("model", "preprocess", "tokenizer", "adapter"):
            wrong = training()
            wrong["loaded_artifacts"][artifact] = "old"
            self.assertEqual(subject().validate_training(wrong), {"artifact-mismatch"})
        fewer = training()
        fewer["required_resume_components"] = ["weights"]
        fewer["resume_components"] = ["weights"]
        self.assertEqual(subject().validate_training(fewer), set())

    def test_randomization_units_srm_and_repeated_peeking_invalidate_claim(self):
        self.assertEqual(subject().validate_experiment(experiment()), set())
        events = experiment()
        events["analysis_unit"] = "event"
        self.assertEqual(subject().validate_experiment(events), {"unit-dependence-mismatch"})
        events["dependence_handling"] = "clustered-by-assignment"
        self.assertEqual(subject().validate_experiment(events), set())
        imbalance = experiment()
        imbalance["assignment_counts"] = {"a": 90, "b": 10}
        # Independent Pearson arithmetic: (90-50)^2/50 + (10-50)^2/50 = 64.
        self.assertGreater(64, imbalance["plan"]["srm_statistic_limit"])
        self.assertEqual(subject().validate_experiment(imbalance), {"sample-ratio-mismatch"})
        peeking = experiment()
        peeking.update(assignment_counts={"a": 15, "b": 15}, decision_looks=5, stopped_for_effect=True)
        self.assertEqual(subject().validate_experiment(peeking), {"unplanned-fixed-sample-stop"})

    def test_declared_sequential_method_and_multiplicity_are_plan_constraints(self):
        record = experiment()
        record["plan"].update(stopping="sequential", sequential_method="alpha-spending", maximum_looks=5)
        record.update(assignment_counts={"a": 15, "b": 15}, decision_looks=3,
                      stopped_for_effect=True, analysis_method="alpha-spending", spent_alpha=0.03)
        self.assertEqual(subject().validate_experiment(record), set())
        wrong = deepcopy(record)
        wrong["analysis_method"] = "ordinary-p-value"
        self.assertEqual(subject().validate_experiment(wrong), {"invalid-sequential-method"})
        wrong = deepcopy(record)
        wrong["spent_alpha"] = 0.06
        self.assertEqual(subject().validate_experiment(wrong), {"sequential-budget-exceeded"})
        many = experiment()
        many["hypotheses_tested"] = 4
        self.assertEqual(subject().validate_experiment(many), {"multiplicity-plan-violation"})
        many["plan"].update(maximum_hypotheses=4, multiplicity_method="holm")
        many["multiplicity_method"] = "holm"
        self.assertEqual(subject().validate_experiment(many), set())


if __name__ == "__main__":
    unittest.main()
