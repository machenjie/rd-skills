# Benchmark Prompt

## Task

Fix the order read endpoint so users can only read orders they are allowed to
see. The starter service currently loads an order by id and returns it without
checking tenant, owner, or support role scope.

## Context

The product supports customer users, tenant administrators, and support agents.
Orders include customer id, tenant id, line items, shipment address, and status.
Support agents may read an order only when they have an active support case for
that order.

## Requirements

- Enforce object level authorization before returning any order data.
- Distinguish not found from forbidden only when that distinction is safe.
- Add denial audit events with actor id, order id, and reason code.
- Keep repository queries efficient and tenant scoped.
- Add tests for owner, tenant admin, support agent, cross tenant, and anonymous access.

## Constraints

- Do not rely on frontend route guards for backend authorization.
- Do not fetch full order details before authorization when a scoped query can avoid it.
- Do not leak shipment address or line item data in denial responses or logs.

## Deliverables

- Updated controller, authorization policy, repository query, and tests.
- Short policy note describing which roles can read an order.
- Regression evidence for cross tenant and inactive support case denial.

## Completion Evidence

- Passing unit and integration tests for allowed and denied reads.
- Security review note covering object authorization and response shaping.
- Explanation of repository scoping and audit event behavior.