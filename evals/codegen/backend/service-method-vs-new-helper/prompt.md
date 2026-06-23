# Benchmark Prompt

## Task

Add order cancellation deadline enforcement to the backend order workflow.
The starter repo already has `OrderService.cancelOrder()` and
`OrderPolicy.canCancelBeforeDeadline()`.

## Context

AI-generated code proposes a new `validateCancellationDeadline()` helper under
`src/shared/utils/date.ts`. The business rule belongs to the order capability,
and cancellation already flows through the service and policy.

## Requirements

- Reuse or extend the existing order service and policy.
- Reject a detached shared utility for the cancellation business rule.
- Keep date arithmetic technical helpers separate from order policy decisions.
- Add public-workflow tests for cancellation before, at, and after the deadline.
  Keep the literal phrases `before deadline`, `at deadline`, and
  `after deadline` visible in test names, test descriptions, or nearby comments
  so the boundary evidence is reviewable outside CamelCase identifiers.
- Include an Implementation Structure Plan explaining service method versus helper placement.

## Constraints

- Do not put order business logic in `shared`, `common`, or generic `utils`.
- Do not bypass existing transaction and authorization flow in `OrderService`.
- Do not create a new class unless state, lifecycle, dependency injection, or invariants require it.

## Deliverables

- Updated order cancellation implementation.
- Focused tests for deadline boundaries and existing cancellation success.
- Structure rationale for reused service/policy and rejected helper placement.

## Completion Evidence

- Deadline tests prove the public cancellation workflow behavior.
- Diff shows no new order business helper in shared utils.
- Structure plan names existing service and policy reuse candidates.
