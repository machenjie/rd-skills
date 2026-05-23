# Test Suite

## Required Checks

- Owner reads own order and receives the expected order payload.
- Tenant administrator reads an order from the same tenant.
- Tenant administrator cannot read an order from another tenant.
- Support agent reads only when an active case references the order.
- Anonymous or missing actor requests are rejected before repository detail access.

## Fixtures

- Two tenants with at least one order each.
- Customer actor, tenant admin actor, support agent actor, and anonymous actor.
- Active and closed support case fixtures linked to different orders.

## Expected Commands

- `python3 -m pytest tests/test_order_read.py`
- `python3 -m pytest tests/test_order_authorization.py`

## Regression Cases

- Existing owner read behavior still succeeds.
- Denied requests do not serialize shipment address or line items.
- Denial audit events are emitted exactly once for forbidden reads.