import unittest

from src.order_service import Cache, EventBus, OrderService, Transaction


class OrderServiceTests(unittest.TestCase):
    def test_success_commits_before_event_and_cache(self):
        log = []
        transaction = Transaction(log=log)
        events = EventBus(log=log)
        cache = Cache(log=log)

        order = OrderService().update_status("order-1", "paid", transaction, events, cache)

        self.assertEqual(order, {"id": "order-1", "status": "paid"})
        self.assertEqual(log, ["commit", "event", "cache"])
        self.assertEqual(len(events.published), 1)
        self.assertEqual(cache.values["order-1"], order)

    def test_commit_failure_publishes_no_event_and_writes_no_cache(self):
        log = []
        transaction = Transaction(fail_commit=True, log=log)
        events = EventBus(log=log)
        cache = Cache(log=log)

        with self.assertRaises(RuntimeError):
            OrderService().update_status("order-1", "paid", transaction, events, cache)

        self.assertEqual(log, ["commit_failed"])
        self.assertEqual(events.published, [])
        self.assertEqual(cache.values, {})


if __name__ == "__main__":
    unittest.main()
