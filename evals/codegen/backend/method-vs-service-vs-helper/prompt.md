# Benchmark Prompt

## Task

Add cancellation eligibility behavior for orders while deciding whether the new
logic belongs on the existing `Order` object, `OrderPolicy`, `OrderService`, or
a local helper.

## Context

The starter repo has an `Order` domain object with state transitions,
`OrderPolicy` with business deadline rules, and `OrderService` coordinating
authorization, transactions, repositories, and notifications. AI-generated code
proposes `shared/utils/cancelHelpers.ts`, `OrderProcessor`, `data`, and
`handle()` for the new behavior.

## Requirements

- Search existing order object, policy, service, repository, and tests before adding code.
- Place deadline or eligibility behavior where the invariant or orchestration owner lives.
- Use repository vocabulary and TypeScript naming conventions.
- Reject generic names such as `OrderProcessor`, `CancellationHelper`, `data`, `info`, and `handle()` unless a precise responsibility justifies them.
- Add tests for allowed cancellation, deadline denial, and authorization denial.

## Constraints

- Do not move business rules to `shared`, `common`, or generic utils.
- Do not create a class that only groups stateless helper functions.
- Do not bypass the existing service transaction or authorization flow.
- Do not export a helper used by only one module.

## Deliverables

- Updated backend order cancellation implementation.
- Tests covering public behavior and boundary cases.
- Implementation Structure Plan with naming evidence, responsibility taxonomy,
  method placement rationale, rejected alternatives, and test placement.

## Completion Evidence

- Tests fail when deadline business logic is moved to shared utils.
- Review evidence names existing reuse candidates and selected owner.
- Naming evidence shows business concepts use existing order vocabulary.
