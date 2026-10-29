import importlib.util
import os
import unittest
from pathlib import Path


def subject():
    path = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"]) / "subject.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LoadAssertions(unittest.TestCase):
    def test_fixed_concurrency_cannot_hide_unsent_arrivals(self):
        planned = list(range(0, 1000, 100))
        rows = [{"id": i, "start": start, "end": start + 50, "outcome": "success"} for i, start in enumerate((0, 250, 500, 750))]
        result = subject().analyse_load(planned, rows)
        self.assertEqual((result["intended"], result["sent"], result["unsent"]), (10, 4, 6))
        self.assertEqual(result["queue_delay"], {0: 0, 1: 150, 2: 300, 3: 450})
        self.assertEqual(result["planned_latency"], {0: 50, 1: 200, 2: 350, 3: 500})
        self.assertEqual(result["service_latency"], {0: 50, 1: 50, 2: 50, 3: 50})

    def test_success_rejection_timeout_pending_and_unsent_are_distinct(self):
        rows = [
            {"id": 0, "start": 0, "end": 25, "outcome": "success"},
            {"id": 1, "start": 100, "end": 100, "outcome": "rejected"},
            {"id": 2, "start": 200, "end": 300, "outcome": "timeout"},
            {"id": 3, "start": 300, "end": None, "outcome": None},
            {"id": 4, "start": None, "end": None, "outcome": None},
        ]
        result = subject().analyse_load([0, 100, 200, 300, 400], rows)
        self.assertEqual({key: result[key] for key in ("success", "rejected", "timeout", "pending", "unsent")}, dict.fromkeys(("success", "rejected", "timeout", "pending", "unsent"), 1))
        self.assertEqual(result["sent"], 4)
        self.assertNotIn(3, result["planned_latency"])
        self.assertNotIn(4, result["service_latency"])

    def test_duplicate_and_impossible_records_are_rejected(self):
        candidate = subject()
        row = {"id": 0, "start": 0, "end": 10, "outcome": "success"}
        for rows in ([row, row], [{**row, "id": 2}], [{**row, "start": None}], [{**row, "end": -1}], [{**row, "end": None}]):
            with self.assertRaises(ValueError):
                candidate.analyse_load([0], rows)

    def test_throughput_cannot_override_declared_quality_tail_or_cost(self):
        candidate = subject()
        policy = {"min_quality": 0.95, "max_p99_ms": 500, "max_unit_cost": 0.02}
        base = {"quality": 0.97, "p99_ms": 400, "unit_cost": 0.01, "throughput": 100,
                "hosted": {"input_tokens": 200, "output_tokens": 100, "quota": 10, "billed_after_cancel": 3}}
        self.assertEqual(candidate.configuration_failures(base, policy, "hosted"), set())
        for field, value, reason in (("quality", 0.8, "quality"), ("p99_ms", 700, "tail-latency"), ("unit_cost", 0.03, "cost")):
            observed = {**base, "throughput": 1000, field: value}
            self.assertEqual(candidate.configuration_failures(observed, policy, "hosted"), {reason})

    def test_hosted_and_self_hosted_evidence_are_not_interchangeable(self):
        candidate = subject()
        policy = {"min_quality": 0.95, "max_p99_ms": 500, "max_unit_cost": 0.02}
        observed = {"quality": 0.97, "p99_ms": 400, "unit_cost": 0.01,
                    "self_hosted": {"prefill_ms": 20, "decode_ms": 50, "weights_bytes": 40, "kv_bytes": 30, "device_bytes": 100}}
        self.assertEqual(candidate.configuration_failures(observed, policy, "self-hosted"), set())
        self.assertEqual(candidate.configuration_failures(observed, policy, "hosted"), {"hosted-evidence"})
        observed["self_hosted"]["kv_bytes"] = 70
        self.assertEqual(candidate.configuration_failures(observed, policy, "self-hosted"), {"device-memory"})
        observed.pop("self_hosted")
        self.assertEqual(candidate.configuration_failures(observed, policy, "self-hosted"), {"self-hosted-evidence"})


if __name__ == "__main__":
    unittest.main()
