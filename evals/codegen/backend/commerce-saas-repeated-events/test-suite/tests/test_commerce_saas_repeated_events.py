from copy import deepcopy
import importlib.util
import itertools
import os
from pathlib import Path
import unittest

ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def subject():
    spec = importlib.util.spec_from_file_location("candidate_commerce_saas", ROOT / "commerce_saas.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy(**changes):
    result = {"grace_until": 20, "change_effective_at": 30, "seat_limit": 3,
              "new_seat_limit": 1, "refund_revokes": True, "quota": 8,
              "block_on_quota": False, "block_on_seat_overage": False,
              "period_start": 0, "period_end": 20, "usage_receipt_deadline": 25}
    result.update(changes)
    return result


def event(identity, kind, at, **fields):
    return {"id": identity, "kind": kind, "at": at, **fields}


MINIMAL_REPLAY = [event("r", "reserve", 0, quantity=3, expires_at=10),
                  event("c", "cancel", 2), event("c", "cancel", 2)]


class CommerceSaasAssertions(unittest.TestCase):
    def test_expired_reservation_cannot_be_fulfilled_by_late_payment(self):
        events = [event("r", "reserve", 0, quantity=3, expires_at=10),
                  event("expiry", "tick", 10), event("p", "pay", 12),
                  event("f", "fulfill", 13, quantity=3), event("c", "cancel", 14)]
        events.append(deepcopy(events[-1]))
        before = deepcopy(events)
        result = subject().reconcile_order(5, events)
        self.assertEqual(result["available"], 5)
        self.assertEqual(result["fulfilled"], 0)
        self.assertEqual(result["payment_state"], "paid")
        self.assertEqual(result["fulfillment_state"], "unfulfilled")
        self.assertEqual(result["issues"], {"late-payment", "unbacked-fulfillment"})
        self.assertEqual(events, before)

    def test_partial_returns_preserve_physical_conservation(self):
        events = [event("r", "reserve", 0, quantity=5, expires_at=100),
                  event("p", "pay", 1), event("f", "fulfill", 2, quantity=4),
                  event("t1", "return", 3, quantity=2, restock=True),
                  event("t2", "return", 4, quantity=1, restock=False),
                  event("refund", "refund", 5)]
        result = subject().reconcile_order(5, events)
        self.assertEqual((result["available"], result["reserved"], result["outstanding"], result["retired"]), (2, 1, 1, 1))
        self.assertEqual(sum(result[k] for k in ("available", "reserved", "outstanding", "retired")), 5)
        self.assertEqual(result["payment_state"], "refunded")
        self.assertEqual(result["fulfillment_state"], "part-returned")
        with self.assertRaises(ValueError):
            subject().reconcile_order(5, events + [event("too-much", "return", 6, quantity=2, restock=True)])

    def test_bounded_generated_duplicate_sequences_preserve_capacity(self):
        for quantity, copies in itertools.product(range(1, 6), range(1, 5)):
            reserve = event("r", "reserve", 0, quantity=quantity, expires_at=10)
            cancel = event("c", "cancel", 1)
            rows = [reserve] + [deepcopy(cancel) for _ in range(copies)]
            result = subject().reconcile_order(5, rows)
            self.assertEqual(result["available"], 5, (quantity, copies))
            self.assertEqual(sum(result[k] for k in ("available", "reserved", "outstanding", "retired")), 5)
        with self.assertRaises(ValueError):
            subject().reconcile_order(5, [event("zero", "reserve", 0, quantity=0, expires_at=10)])
        for invalid_quantity in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                subject().reconcile_order(5, [event("invalid", "reserve", 0, quantity=invalid_quantity, expires_at=10)])
        conflict = deepcopy(MINIMAL_REPLAY)
        conflict[-1]["at"] = 3
        with self.assertRaises(ValueError):
            subject().reconcile_order(5, conflict)

    def test_shrinking_preserves_preconditions_and_replays_minimal_failure(self):
        # Independent deliberately faulty accounting: every cancellation re-releases the allocation.
        examined = []
        def violates(rows):
            available, allocation = 5, 0
            has_reservation = False
            for row in rows:
                if row["kind"] == "reserve":
                    has_reservation = True
                    allocation = row["quantity"]
                    available -= allocation
                elif row["kind"] == "cancel":
                    self.assertTrue(has_reservation, "shrinker called oracle on an invalid sequence")
                    available += allocation
            examined.append(deepcopy(rows))
            return available > 5
        long = [event("noise0", "tick", -1), MINIMAL_REPLAY[0], event("noise1", "tick", 1),
                MINIMAL_REPLAY[1], event("noise2", "tick", 3), MINIMAL_REPLAY[2], event("noise3", "tick", 4)]
        result = subject().shrink_duplicate_cancellation(long, violates)
        self.assertEqual(result, MINIMAL_REPLAY)
        self.assertTrue(violates(result))
        self.assertEqual(subject().shrink_duplicate_cancellation(result, violates), MINIMAL_REPLAY)
        for i in range(len(result)):
            reduced = result[:i] + result[i+1:]
            if reduced and reduced[0]["kind"] == "reserve":
                self.assertFalse(violates(reduced))
        self.assertGreater(len(examined), 1)
        self.assertEqual(subject().reconcile_order(5, result)["available"], 5)

    def test_grace_downgrade_and_overage_follow_explicit_policy(self):
        events = [event("failed", "payment_failed", 1), event("s1", "seat_assign", 2, seat_id="one"),
                  event("s2", "seat_assign", 3, seat_id="two")]
        before = subject().evaluate_saas(policy(), events, 19)
        self.assertTrue(before["entitled"])
        self.assertEqual(before["financial_state"], "past_due")
        self.assertEqual(before["seat_limit"], 3)
        self.assertFalse(subject().evaluate_saas(policy(), events, 20)["entitled"])
        after = subject().evaluate_saas(policy(grace_until=50), events, 31)
        self.assertEqual(after["seat_limit"], 1)
        self.assertTrue(after["seats_over_limit"])
        self.assertTrue(after["entitled"])
        self.assertFalse(subject().evaluate_saas(policy(grace_until=50, block_on_seat_overage=True), events, 31)["entitled"])

    def test_late_corrected_usage_is_identity_based_and_order_independent(self):
        rows = [event("u1", "usage", 2, usage_id="job1", version=1, units=4, occurred_at=1),
                event("u2", "usage", 22, usage_id="job2", version=1, units=3, occurred_at=18),
                event("correction", "usage", 24, usage_id="job1", version=2, units=2, occurred_at=1)]
        rows.append(deepcopy(rows[0]))
        for permutation in (rows, list(reversed(rows)), rows[1:] + rows[:1]):
            result = subject().evaluate_saas(policy(quota=4), permutation, 25)
            self.assertEqual(result["usage_total"], 2 + 3)
            self.assertTrue(result["quota_exceeded"])
            self.assertTrue(result["entitled"])
            self.assertFalse(subject().evaluate_saas(policy(quota=4, block_on_quota=True), permutation, 25)["entitled"])
        late = rows + [event("too-late", "usage", 26, usage_id="job3", version=1, units=99, occurred_at=19)]
        self.assertEqual(subject().evaluate_saas(policy(), late, 27)["usage_total"], 5)

    def test_cancel_restore_revision_and_refund_entitlement_are_separate(self):
        rows = [event("restore", "restore", 10, revision=2), event("cancel", "cancel", 12, revision=1)]
        self.assertTrue(subject().evaluate_saas(policy(), rows, 15)["entitled"])
        refunded = rows + [event("refund", "refund", 13)]
        result = subject().evaluate_saas(policy(), refunded, 15, observed_entitled=True)
        self.assertEqual(result["subscription_state"], "active")
        self.assertEqual(result["financial_state"], "refunded")
        self.assertFalse(result["entitled"])
        self.assertEqual(result["issues"], {"entitlement-mismatch"})
        self.assertTrue(subject().evaluate_saas(policy(refund_revokes=False), refunded, 15)["entitled"])


if __name__ == "__main__":
    unittest.main()
