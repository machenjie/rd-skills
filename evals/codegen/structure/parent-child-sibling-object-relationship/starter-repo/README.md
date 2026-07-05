# Starter Repo

## Stack

Python backend service with in-memory repositories and public behavior tests.

## Initial State

`OrderLifecycleService` mixes cancellation, refund, and shipping rules in one
object. The refactor must decide whether those rules are parent-child, sibling,
collaborator, or policy relationships before creating files.

## Files

- `orders/lifecycle_service.py`
- `orders/order.py`
- `orders/refunds.py`
- `orders/shipping.py`
- `tests/orders/test_lifecycle_service.py`

## Constraints

The benchmark rejects pass-through parent objects, sibling internal access,
method-name-only splits, and shared/common ownership avoidance.
