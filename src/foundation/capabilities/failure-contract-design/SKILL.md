---
name: failure-contract-design
description: Defines typed cross-boundary failure semantics, translation, retryability, fallback, partial failure, compensation, DLQ, safe user messages, and observability so errors are not swallowed or leaked raw.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "110"
changeforge_version: 0.1.0
---

# Mission

Make every boundary declare how failures are represented, translated, observed, retried, surfaced to users, and recovered without losing cause or leaking internals.

# When To Use

Use when controllers, services, repositories, adapters, SDK clients, jobs, message consumers, queue handlers, transactions, retries, fallbacks, DLQs, compensation, degraded responses, or user-visible error messages are added or changed.

Use when retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, partial, or internal failures are conflated.

# Do Not Use When

Do not use for pure local calculations with no boundary, no caller-visible failure, and no recoverable error semantics.

Do not use to create a large error hierarchy when a small typed result or local exception mapping satisfies the boundary.

# Non-Negotiable Rules

- Every boundary declares its failure contract.
- Do not swallow errors without typed fallback and observability.
- Retryable, terminal, conflict, validation, permission, and cancellation states must be distinguishable.
- User-visible errors must be safe.
- Internal logs preserve diagnostic cause without leaking secrets or PII.
- Adapter and repository errors are translated at the boundary, not leaked as raw SDK or database internals.
- Partial failure has compensation, rollback, or explicit acceptance.
- Message and async failures have retry, DLQ, and poison-message behavior.

# Industry Benchmarks

Anchor against RFC 7807 problem details, typed error/result patterns, exception boundary practice, OpenTelemetry correlation, SRE incident diagnosability, bounded retries with backoff, saga compensation, DLQ/poison-message handling, and secure error disclosure guidance.

# Selection Rules

Select this capability when the main risk is error semantics across layers. Use `error-code-design` for stable API error codes, `logging-error-handling` for log redaction and diagnostic fields, `idempotency-retry-design` for retry mechanics, `transaction-consistency` for rollback/compensation, and `observability` for production signals.

# Risk Escalation Rules

Escalate to `security-privacy-gate` when errors can expose secrets, PII, auth state, tenant data, or provider internals. Escalate to `reliability-observability-gate` when silent fallback, retries, degraded mode, or dependency failures affect SLOs. Escalate to `data-api-contract-changer` when public API error contracts change.

# Critical Details

- Retryable failures include transient network, timeout, throttling, and dependency saturation only when the operation is idempotent or guarded.
- Terminal failures include malformed input, unsupported state, permanent provider rejection, and non-recoverable domain violations.
- Validation, permission/auth, conflict/concurrency, timeout, cancellation, dependency, and partial failures must be distinguishable in code and tests.
- Adapter translation maps provider/SDK/database errors into local error types at the adapter boundary.
- Repository translation hides raw SQL/ORM internals while preserving cause in logs.
- Controller translation maps internal failures to safe status, code, and user-visible message.
- Job and consumer contracts define ack/nack, retry budget, DLQ, poison-message behavior, and replay safety.
- Panic/exception boundaries recover only at framework, process, job, or task boundaries with logging and fail-fast behavior where appropriate.
- Fallback is a typed decision with user impact, stale data policy, metric, and removal path.

# Failure Modes

- `catch` returns null, empty list, or success without log, metric, or typed degraded state.
- Raw database, SDK, stack trace, query, token, path, or customer data leaks to clients.
- Retrying validation, permission, or non-idempotent failures.
- Treating cancellation as an error that triggers retry or alert noise.
- Losing root cause when wrapping errors.
- Publishing partial success without compensation or explicit acceptance.
- Queue consumer ACKs before durable processing and has no DLQ or replay behavior.

# Output Contract

Return a Failure Contract:

- Error taxonomy.
- Boundary translation map.
- Retryability.
- Fallback and degradation behavior.
- Compensation, rollback, or DLQ behavior.
- User-visible message.
- Log, metric, and trace fields.
- Cause preservation.
- Panic or exception handling.
- Controller, service, repository, adapter, job, and message consumer contracts.
- Tests for negative paths.
- Residual failure risk.

# Evidence Contract

Close the contract only when failure states are typed or otherwise machine-distinguishable, boundary translations are named, retry/fallback/partial behavior is tested or explicitly not testable, logs preserve cause safely, user messages are safe, validation command or review evidence is recorded, and residual failure risks have owners.

# Quality Gate

1. Typed failure states exist.
2. No silent fallback exists.
3. No raw internal, secret, or PII leak exists.
4. Retry semantics are explicit.
5. Partial failure is handled.
6. Async and message failure behavior is handled.
7. Negative paths are tested.
8. Cause is preserved for diagnostics without unsafe disclosure.

# Used By

- backend-change-builder
- data-api-contract-changer
- data-middleware-change-builder
- integration-change-builder
- reliability-observability-gate
- quality-test-gate
- ai-code-review-refactor
- frontend-change-builder

# Handoff

Hand off to `error-code-design` for public error codes, `logging-error-handling` for diagnostics, `observability` for metrics and traces, `idempotency-retry-design` for retries, `transaction-consistency` for compensation, and `delivery-release-gate` when failure behavior affects rollout or rollback.

# Completion Criteria

The capability is complete when every changed boundary has a typed failure taxonomy, translation map, retry/fallback/partial-failure behavior, safe user message, diagnostic cause preservation, negative tests, and residual failure risk statement.
