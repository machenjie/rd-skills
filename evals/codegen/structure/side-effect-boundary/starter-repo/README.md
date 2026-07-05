# Starter Repo

## Stack

Python service code with pytest-style tests and fake repository/payment/cache adapters.

## Initial State

`OrderPolicy.can_cancel` both decides cancellation eligibility and performs side effects. The policy is hard to unit test without repository, payment, event, cache, and logger mocks.

## Files

- `orders/policy.py`
- `orders/service.py`
- `orders/repository.py`
- `orders/payment_client.py`
- `tests/orders/test_cancellation.py`

## Constraints

The starting point deliberately mixes pure policy and side effects. The benchmark expects explicit separation and public behavior tests.
