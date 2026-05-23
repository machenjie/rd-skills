# Starter Repo

## Stack

Python 3.11 HTTP style controller, service layer, repository abstraction, and
pytest tests. The starter state models users, tenants, orders, and support
cases with simple in-memory fixtures.

## Initial State

The order controller accepts an order id and current actor. It calls the
repository by primary key and returns the serialized order. Existing tests only
verify that a known order id returns a successful response for a logged in user.

## Files

- `orders/controller.py` maps request parameters and response status.
- `orders/policy.py` contains a placeholder authorization function.
- `orders/repository.py` loads orders and support cases.
- `orders/audit.py` records security relevant decisions.
- `tests/test_order_read.py` covers the existing happy path.

## Constraints

Keep the public route stable and do not add a new global permission model. The
solution should express the smallest policy needed for order read while keeping
the policy reusable by future order detail surfaces.