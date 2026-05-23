# Starter Repo

## Stack

Python 3.11 service code with a relational repository abstraction, a provider
adapter, and pytest style tests. The benchmark expects standard library money
and hashing primitives unless the existing starter files already include a
library.

## Initial State

The payment controller accepts amount, currency, customer id, and source token.
The service calls the provider adapter directly and then writes a payment row.
There is no idempotency table, no payload fingerprint, and retry behavior is
left to the client.

## Files

- `payments/controller.py` handles request validation and response mapping.
- `payments/service.py` owns payment creation and provider calls.
- `payments/repository.py` stores payment records and exposes transactions.
- `payments/provider.py` simulates success, decline, and timeout responses.
- `tests/test_payments.py` covers the existing happy path only.

## Constraints

Preserve the existing controller route and success response shape. New database
state must be represented as a migration note or migration file. Tests should
exercise the repository contract rather than mocking away the transaction path.