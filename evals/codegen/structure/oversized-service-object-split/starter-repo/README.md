# Starter Repo

## Stack

TypeScript service code with Jest-style unit tests and a simple in-memory repository fixture.

## Initial State

`OrderService` owns authorization, transaction orchestration, cancellation decisions, refund decisions, shipment checks, invoice checks, notification calls, and payment calls. The service works but has multiple unrelated method clusters.

## Files

- `src/orders/order-service.ts`
- `src/orders/order.ts`
- `src/orders/payment-client.ts`
- `src/orders/order-repository.ts`
- `tests/orders/order-service.test.ts`

## Constraints

Starter files intentionally model an oversized service. The benchmark expects a split or an explicit rejection with evidence, not a continuation of the same service-growth pattern.
