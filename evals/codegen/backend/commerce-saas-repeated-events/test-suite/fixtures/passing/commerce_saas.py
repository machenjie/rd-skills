"""Bounded, in-memory acceptance evaluators for this benchmark's stated policies."""
from copy import deepcopy


def _unique(events):
    seen = {}
    for event in events:
        if event["id"] in seen and seen[event["id"]] != event:
            raise ValueError("conflicting event identity")
        seen[event["id"]] = event
    return list(seen.values())


def _quantity(value):
    if type(value) is not int or value < 0:
        raise ValueError("quantity must be a nonnegative integer")
    return value


def reconcile_order(capacity, events):
    capacity = _quantity(capacity)
    available, reserved, fulfilled, returned, retired = capacity, 0, 0, 0, 0
    deadline = None
    payment = "unpaid"
    cancelled = False
    issues = set()
    for event in sorted(_unique(events), key=lambda e: (e["at"], e["id"])):
        if deadline is not None and event["at"] >= deadline:
            available += reserved
            reserved = 0
            deadline = None
        kind = event["kind"]
        if kind == "reserve":
            quantity = _quantity(event["quantity"])
            if quantity == 0 or reserved or quantity > available or event["expires_at"] <= event["at"]:
                raise ValueError("invalid reservation")
            available -= quantity
            reserved = quantity
            deadline = event["expires_at"]
            cancelled = False
        elif kind == "pay":
            payment = "paid"
            if not reserved and not fulfilled:
                issues.add("late-payment")
        elif kind == "cancel":
            available += reserved
            reserved = 0
            deadline = None
            cancelled = True
        elif kind == "fulfill":
            quantity = _quantity(event["quantity"])
            if payment != "paid" or quantity > reserved:
                issues.add("unbacked-fulfillment")
                continue
            reserved -= quantity
            fulfilled += quantity
        elif kind == "return":
            quantity = _quantity(event["quantity"])
            if quantity > fulfilled - returned:
                raise ValueError("return exceeds outstanding fulfillment")
            returned += quantity
            if event["restock"]:
                available += quantity
            else:
                retired += quantity
        elif kind == "refund":
            payment = "refunded"
        elif kind != "tick":
            raise ValueError("unknown event kind")
    return {
        "available": available, "reserved": reserved, "fulfilled": fulfilled,
        "returned": returned, "retired": retired,
        "outstanding": fulfilled - returned,
        "payment_state": payment,
        "order_state": "cancelled" if cancelled else "allocated" if reserved else "unreserved",
        "fulfillment_state": "unfulfilled" if not fulfilled else "part-returned" if returned else "fulfilled",
        "issues": frozenset(issues),
    }


def evaluate_saas(policy, events, now, observed_entitled=None):
    rows = [event for event in _unique(events) if event["at"] <= now]
    rows.sort(key=lambda event: (event["at"], event.get("revision", 0), event["id"]))
    lifecycle = [event for event in rows if event["kind"] in {"cancel", "restore"}]
    lifecycle_versions = {}
    for event in lifecycle:
        previous = lifecycle_versions.get(event["revision"])
        if previous is not None and previous != event["kind"]:
            raise ValueError("conflicting lifecycle revision")
        lifecycle_versions[event["revision"]] = event["kind"]
    cancelled = bool(lifecycle and max(lifecycle, key=lambda e: e["revision"])["kind"] == "cancel")
    financial = "paid"
    seats = set()
    usage_versions = {}
    usage = {}
    for event in rows:
        kind = event["kind"]
        if kind in {"paid", "payment_failed", "refund"}:
            financial = {"paid": "paid", "payment_failed": "past_due", "refund": "refunded"}[kind]
        elif kind == "seat_assign":
            seats.add(event["seat_id"])
        elif kind == "seat_revoke":
            seats.discard(event["seat_id"])
        elif kind == "usage":
            units = _quantity(event["units"])
            identity = (event["usage_id"], event["version"])
            value = (units, event["occurred_at"])
            if identity in usage_versions and usage_versions[identity] != value:
                raise ValueError("conflicting usage version")
            usage_versions[identity] = value
            if event["at"] > policy["usage_receipt_deadline"]:
                continue
            old = usage.get(event["usage_id"])
            if old is None or event["version"] > old["version"]:
                usage[event["usage_id"]] = event
        elif kind not in {"cancel", "restore"}:
            raise ValueError("unknown SaaS event kind")
    total = sum(event["units"] for event in usage.values()
                if policy["period_start"] <= event["occurred_at"] < policy["period_end"])
    limit = policy["new_seat_limit"] if now >= policy["change_effective_at"] else policy["seat_limit"]
    over_seats = len(seats) > limit
    over_quota = total > policy["quota"]
    entitled = not cancelled
    if financial == "past_due":
        entitled = entitled and now < policy["grace_until"]
    if financial == "refunded" and policy["refund_revokes"]:
        entitled = False
    if policy["block_on_seat_overage"] and over_seats:
        entitled = False
    if policy["block_on_quota"] and over_quota:
        entitled = False
    issues = set()
    if observed_entitled is not None and observed_entitled != entitled:
        issues.add("entitlement-mismatch")
    return {"entitled": entitled, "subscription_state": "cancelled" if cancelled else "active",
            "financial_state": financial, "seat_count": len(seats), "seat_limit": limit,
            "seats_over_limit": over_seats, "usage_total": total,
            "quota_exceeded": over_quota, "issues": frozenset(issues)}


def shrink_duplicate_cancellation(events, violates):
    """Delete irrelevant events while preserving reserve-before-cancel validity."""
    if len(events) > 32:
        raise ValueError("fixture sequence budget exceeded")

    def legal(sequence):
        identities = {}
        reserved_once = False
        for event in sequence:
            if event["id"] in identities and identities[event["id"]] != event:
                return False
            identities[event["id"]] = event
            if event["kind"] == "reserve":
                reserved_once = True
            if event["kind"] == "cancel" and not reserved_once:
                return False
        return True

    current = deepcopy(events)
    if not legal(current) or not violates(current):
        raise ValueError("input must be a legal counterexample")
    index = 0
    while index < len(current):
        reduced = current[:index] + current[index + 1:]
        if legal(reduced) and violates(reduced):
            current = reduced
            index = 0
        else:
            index += 1
    return current
