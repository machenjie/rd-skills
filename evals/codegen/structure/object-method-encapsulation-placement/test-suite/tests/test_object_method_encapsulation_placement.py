from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def subjects():
    sys.path.insert(0, str(ROOT))
    for name in list(sys.modules):
        if name == "orders" or name.startswith("orders."):
            del sys.modules[name]
    package = importlib.import_module("orders")
    return package.Order, package.PaymentAdapter, package.OrderCancellationService


class ObjectMethodPlacementAssertions(unittest.TestCase):
    def test_domain_object_owns_lifecycle_decision_without_payment_side_effects(self) -> None:
        Order, _, _ = subjects()
        source = (ROOT / "orders" / "order.py").read_text(encoding="utf-8").casefold()
        for forbidden in ("paymentadapter", "payment_adapter", "refund(", "requests."):
            self.assertNotIn(forbidden, source)
        self.assertEqual(Order("a", 0).cancellation_decision(10), "allowed")
        self.assertEqual(Order("b", 0, status="shipped").cancellation_decision(10), "denied")
        self.assertEqual(Order("c", 0).cancellation_decision(31), "expired")
        self.assertEqual(Order("d", 0, refund_hold=True).cancellation_decision(10), "refund-hold")

    def test_service_orchestrates_adapter_and_preserves_state_on_payment_failure(self) -> None:
        Order, PaymentAdapter, Service = subjects()
        order = Order("paid", 0)
        payments = PaymentAdapter()
        self.assertEqual(Service().cancel(order, now_minute=10, payments=payments), "cancelled")
        self.assertEqual(payments.refunded, ["paid"])
        self.assertEqual(order.status, "cancelled")

        failing = Order("fail", 0)
        with self.assertRaises(RuntimeError):
            Service().cancel(failing, now_minute=10, payments=PaymentAdapter(fail=True))
        self.assertEqual(failing.status, "pending")

    def test_refund_hold_never_calls_adapter(self) -> None:
        Order, PaymentAdapter, Service = subjects()
        order = Order("held", 0, refund_hold=True)
        payments = PaymentAdapter()
        self.assertEqual(Service().cancel(order, now_minute=10, payments=payments), "refund-hold")
        self.assertEqual(payments.refunded, [])
        self.assertEqual(order.status, "pending")


if __name__ == "__main__":
    unittest.main()
