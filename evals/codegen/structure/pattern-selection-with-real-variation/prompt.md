# Benchmark Prompt

## Task

Support multiple current payment providers with provider-specific retry and
error mapping while choosing the right pattern.

## Context

The starter repository has two active payment providers, CardPay and BankPay.
Both expose charge, refund, and status lookup behavior, but their SDK errors,
retry semantics, and client initialization differ. The current service has
provider-specific if/else branches spread across application code.

## Requirements

- Produce a Design Pattern Decision Record before restructuring.
- Choose strategy, adapter/provider, or another justified pattern only because
  multiple current providers exist.
- Keep provider-specific retry, timeout, error mapping, and client lifecycle in
  provider-owned adapters or strategies.
- Add shared contract tests for every provider implementation.
- Ensure callers use the stable provider contract and do not branch on concrete
  provider types.

## Constraints

- Do not scatter provider if/else branches across services.
- Do not introduce a base class only for shared code.
- Do not create HTTP or SDK clients per request.
- Do not skip contract tests for the provider contract.

## Deliverables

- Provider pattern implementation with lifecycle-managed clients.
- Contract tests for all current providers.
- Design Pattern Decision Record and Implementation Structure Plan.
- Runtime note for timeout, retry, pool, and cleanup behavior.

## Completion Evidence

- Contract tests pass for both providers.
- Review evidence rejects shared-code inheritance and scattered branching.
- Metrics or design notes identify reusable client/pool lifecycle and no
  per-operation client construction.
