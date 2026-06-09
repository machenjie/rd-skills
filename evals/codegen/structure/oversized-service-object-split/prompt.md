# Benchmark Prompt

## Task

Implement a new order cancellation rule without adding more business logic to an already oversized `OrderService`.

## Context

The starter repository has a 700-line `OrderService` that already validates cancellation deadlines, refund eligibility, shipment state, invoice state, and notification side effects. The new requirement adds a cancellation grace period for premium customers and a refund hold rule for disputed orders.

## Requirements

- Inspect existing order domain, policy, adapter, and test files before adding code.
- Split behavior into cohesive policy/rule/value-object/adapter structure when responsibility boundaries justify it.
- Keep `OrderService` as orchestration, authorization, transaction, and collaborator coordination.
- Preserve existing public behavior and add public behavior tests for normal, denied, premium grace, disputed refund hold, and edge deadline cases.
- Keep pure decision logic testable without database, payment API, notification, or cache mocks.

## Constraints

- Do not add another large method to `OrderService`.
- Do not put order business rules in shared/common/utils.
- Do not introduce factories, strategies, or interfaces unless there is current variation and a contract test.
- Do not test only private helpers.

## Deliverables

- Implementation Structure Plan with file/object split decision.
- Refactor plan showing behavior-preserving steps.
- Tests that prove public order cancellation behavior.
- Review note explaining rejected splits and rejected shared utility placement.

## Completion Evidence

- Passing unit tests for pure cancellation decisions.
- Passing service-level behavior tests through the public order use case.
- Before/after complexity or responsibility evidence for the split.
