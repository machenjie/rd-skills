import unittest

from src.aggregate import collect_request_ids


class AggregateTests(unittest.TestCase):
    def test_default_calls_do_not_share_state(self):
        self.assertEqual(collect_request_ids("first"), ["first"])
        self.assertEqual(collect_request_ids("second"), ["second"])

    def test_explicit_list_behavior_is_preserved(self):
        provided = ["existing"]
        self.assertEqual(collect_request_ids("new", provided), ["existing", "new"])
        self.assertEqual(provided, ["existing", "new"])


if __name__ == "__main__":
    unittest.main()
