# Benchmark Prompt

## Task

Refactor a billing discount module that currently exports `_calculate_discount_for_test` only so tests can call a private helper.

## Context

The starter repository has public `QuoteService.price_quote()` behavior, but tests bypass it by importing a private helper and mocking internal call order. The service also reads wall-clock time and a remote customer tier API directly.

## Requirements

- Test observable quote behavior through the public service or module contract.
- Keep private helpers private; do not export or rename them only for tests.
- Add an explicit seam for the customer tier dependency and deterministic clock behavior.
- Choose fake, stub, mock, spy, contract, or integration tests based on the dependency boundary.
- Assign ownership for quote fixtures and add characterization tests before changing risky pricing behavior.

## Constraints

- Do not mock private implementation details or private call order.
- Do not use uncontrolled wall-clock time, randomness, UUIDs, HTTP calls, file I/O, or environment state in tests.
- Do not create broad shared fixtures without owner and reason to change.
- Do not replace public behavior tests with private helper tests.

## Deliverables

- Testability Seam Plan.
- Public behavior tests for quote pricing.
- Dependency seam map and test-double decision.
- Fixture ownership note and rejected shortcut list.

## Completion Evidence

- Tests prove pricing outcomes through `QuoteService.price_quote()`.
- Private helper exports are removed or rejected.
- Clock and customer tier dependency are deterministic in tests.
