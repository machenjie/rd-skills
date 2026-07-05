# Starter Repo

## Stack

Python backend payment service with pytest-style contract tests.

## Initial State

`payments/service.py` branches on provider names for CardPay and BankPay. Each
provider has different SDK setup, retryable errors, terminal errors, and
timeout behavior.

## Files

- `payments/service.py`
- `payments/cardpay.py`
- `payments/bankpay.py`
- `payments/provider_contract.py`
- `tests/payments/test_provider_contract.py`

## Constraints

The benchmark rejects scattered provider branching, shared-code base classes,
per-request client construction, and missing provider contract tests.
