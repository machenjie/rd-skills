import unittest

from compaction_workflow import summarize_delivery_state


class CompactionWorkflowTests(unittest.TestCase):
    def test_counts_known_and_unknown_states(self) -> None:
        result = summarize_delivery_state(
            [
                {"state": "todo"},
                {"state": "doing"},
                {"state": "done"},
                {"state": "blocked"},
            ]
        )
        self.assertEqual(result, {"todo": 2, "doing": 1, "done": 1})


if __name__ == "__main__":
    unittest.main()
