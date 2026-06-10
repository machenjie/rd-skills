# Benchmark Prompt

## Task

Refactor two payment processors that share some formatting and retry helper code
without introducing inheritance for code sharing.

## Context

The starter repository has `CardPaymentProcessor` and `BankTransferProcessor`.
They share small technical helpers but differ in lifecycle, provider protocol,
error behavior, and initialization needs. They are not currently a true
substitutable taxonomy.

## Requirements

- Decide whether inheritance is accepted or rejected before creating an
  abstract base class.
- Reject inheritance when the only benefit is shared code.
- Use composition, delegation, or a private technical helper for shared
  formatting/retry behavior when taxonomy is absent.
- Use strategy or interface only when current variants have a stable contract
  and contract tests.
- Preserve public payment behavior and provider-specific failure handling.

## Constraints

- Do not create an abstract base class only for code reuse.
- Do not require callers to branch on concrete subtype.
- Do not skip base contract or variant contract tests if a hierarchy or
  strategy is accepted.
- Do not ignore initialization safety or lifecycle compatibility.

## Deliverables

- Implementation Structure Plan with Inheritance vs Composition Decision.
- Contract-test plan for any accepted interface, strategy, or hierarchy.
- Refactor evidence showing behavior preservation.
- Public tests for both processors.

## Completion Evidence

- Payment processing tests pass for success, decline, retryable failure, and
  provider-specific errors.
- Decision record rejects inheritance or proves substitutability and contract
  tests.
- Review evidence names the selected composition/delegation/helper boundary.
