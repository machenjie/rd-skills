# Starter Repo

## Stack

Python payment service code with pytest-style public behavior tests.

## Initial State

`CardPaymentProcessor` and `BankTransferProcessor` share formatting and retry
helpers but differ in provider protocol, lifecycle, initialization, and error
behavior. The benchmark expects a composition/delegation decision unless true
substitutability is proven.

## Files

- `payments/card_processor.py`
- `payments/bank_transfer_processor.py`
- `payments/retry_helper.py`
- `tests/payments/test_processors.py`

## Constraints

The benchmark rejects abstract base classes created only for code reuse and any
hierarchy without base and subtype contract tests.
