"""Implement the deterministic evaluators defined in task.md."""

def reconcile_order(capacity, events):
    return {"available": capacity, "reserved": 0, "fulfilled": 0, "returned": 0,
            "retired": 0, "outstanding": 0, "payment_state": "unpaid",
            "order_state": "unreserved", "fulfillment_state": "unfulfilled", "issues": frozenset()}


def evaluate_saas(policy, events, now, observed_entitled=None):
    return {"entitled": True, "subscription_state": "active", "financial_state": "paid",
            "seat_count": 0, "seat_limit": policy["seat_limit"], "seats_over_limit": False,
            "usage_total": 0, "quota_exceeded": False, "issues": frozenset()}


def shrink_duplicate_cancellation(events, violates):
    return list(events)
