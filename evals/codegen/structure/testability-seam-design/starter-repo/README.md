# Starter Repo

## Stack

Python service module with pytest-style tests and a fake customer tier dependency.

## Initial State

Tests import `_calculate_discount_for_test`, assert helper call order, call a real clock, and use broad shared fixtures. The public quote behavior is under-tested.

## Files

- `billing/quote_service.py`
- `billing/customer_tiers.py`
- `tests/billing/test_quote_service.py`
- `tests/fixtures/quotes.py`

## Constraints

The starting point deliberately exposes a private helper for tests. The benchmark expects observable behavior tests, deterministic seams, and local fixture ownership.
