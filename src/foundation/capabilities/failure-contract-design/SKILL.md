---
name: failure-contract-design
description: Use when cross-boundary failure semantics are unclear or changed, including retryable versus terminal outcomes, validation, permission, conflict, timeout, cancellation, dependency, partial failure, fallback, compensation, DLQ, safe user/internal messages, boundary translation, and cause preservation without raw internal leaks.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "110"
changeforge_version: 0.1.0
---

# Mission

Define a compact, typed, cross-boundary failure contract so every failure is represented, translated, observed, retried or not retried, surfaced safely, and recovered without swallowing cause, leaking internals, or hiding partial completion.

# When To Use

Use when controllers, services, repositories, adapters, SDK clients, jobs, message consumers, transactions, retries, fallbacks, DLQs, compensation, degraded responses, or user-visible error messages are added or changed.

Use when retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, partial, degraded, poison-message, or internal failures are conflated.

Use when tests, reviews, incident notes, repository graph evidence, project memory, or execution trajectory show silent fallback, raw dependency leakage, generic "internal error", unclear retryability, or partial success without recovery ownership.

# Do Not Use When

Do not use for pure local calculations with no boundary, no caller-visible failure, no recoverable error semantics, and no diagnostic or recovery obligation.

Do not create a large error hierarchy when a small typed result, local exception mapping, or boundary table satisfies the contract.

Do not use this capability only to design public API error code format; use `error-code-design`. Do not use it only to design log fields; use `logging-error-handling`. Do not use it only to design retry keys, dedupe, replay, or backoff mechanics; use `idempotency-retry-design`.

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release readiness, validation mapping, repair, and final handoff when a change crosses a boundary where failure semantics matter.

- **Planning / system design:** classify failure states, owning boundary, public/private semantics, and adjacent capability handoffs before implementation.
- **Coding / refactoring:** ensure translation happens at controller, service, repository, adapter, job, or consumer boundaries instead of leaking raw infrastructure details.
- **Bug-fix / debugging:** verify cause before changing error handling; scan for the same silent fallback, generic catch, raw leak, or retryability confusion elsewhere.
- **Testing / review:** require negative-path proof that each failure state is machine-distinguishable and mapped to the expected user, operator, retry, or DLQ outcome.
- **Release / handoff:** disclose what validation proves, what provider or production failure paths remain untested, and which adjacent owner must close residual risk.

# Non-Negotiable Rules

- Every material boundary declares its failure contract.
- Failure states are typed or otherwise machine-distinguishable; message text alone is not a contract.
- Retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, partial, degraded, and internal states remain distinct.
- Do not swallow errors without a typed fallback or typed degraded state plus observable cause.
- User-visible errors are safe, stable, and actionable without raw internals, secrets, PII, tenant hints, stack traces, SQL, paths, tokens, or provider bodies.
- Internal diagnostics preserve cause, correlation, and boundary context without unsafe disclosure.
- Adapter, repository, SDK, framework, and database failures are translated at the boundary where the dependency is owned.
- Partial failure has compensation, rollback, reconciliation, DLQ, operator visibility, or explicit residual-risk acceptance.
- Async and message failures define ack/nack timing, retry exhaustion, poison-message behavior, replay safety, and terminal ownership.
- Graph, memory, and prior validation are selectors only; current source and fresh validation must confirm failure behavior before closure.

# Industry Benchmarks

Anchor against typed error/result patterns, exception boundary practice, RFC 7807/9457 problem details, gRPC canonical status mapping, OpenTelemetry correlation, SRE incident diagnosability, bounded retry with jitter, saga compensation, transactional outbox and DLQ recovery, OWASP secure error handling, and consumer-driven negative-path testing.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Failure taxonomy definition | New or unclear error states, generic `Exception`, `INTERNAL_ERROR`, boolean success/failure, or string messages. | Define machine-distinguishable states and terminal outcomes. | Taxonomy, owner boundary, user/operator action, tests. | `error-code-design`, `quality-test-gate` | Large hierarchy when a small typed result works. |
| Boundary translation | Raw SDK, database, framework, provider, repository, or adapter errors cross layers. | Translate at owning boundary while preserving cause internally. | Source error, local outcome, public mapping, diagnostic path. | `logging-error-handling`, `model-boundary-mapping` | Catch-all wrappers that lose cause. |
| Retryability split | Timeout, throttling, 429/503, network failure, duplicate delivery, or uncertain write outcome. | Distinguish retryable, terminal, conditional, and unknown outcomes. | Retryable list, non-retryable list, idempotency precondition, terminal state. | `idempotency-retry-design`, `degradation-circuit-breaking` | Retrying all errors or all 5xx blindly. |
| Partial failure recovery | Multi-step write, external IO, file/storage write, event publish, cache mutation, or compensation path can partially succeed. | Name consistency outcome, recovery owner, and irreversible residue. | Step map, compensation/reconciliation/DLQ, operator visibility, residual risk. | `data-side-effect-flow-tracing`, `transaction-consistency` | Generic "show error" after partial commit. |
| Async/message failure | Queue consumer, job, webhook, cron, replay, DLQ, poison message, ack/nack, or retry exhaustion. | Prevent lost work, duplicate side effects, and invisible terminal failure. | Ack timing, retry budget, DLQ payload, replay safety, alert owner. | `message-queue-design`, `integration-change-builder` | ACK before durable success. |
| Fallback/degradation | Null, empty/default data, stale cache, skip, circuit-open, or degraded mode is returned. | Make degraded state explicit and safe. | Fallback type, user impact, stale policy, metric/log/trace, removal path. | `degradation-circuit-breaking`, `observability` | Silent null/empty fallback. |
| Safe diagnostics | Error detail can reveal secrets, PII, tenant existence, auth state, provider internals, SQL, paths, or prompt/tool data. | Separate user-safe output from operator diagnostics. | Redaction rule, trace id, no-raw-detail proof, security escalation. | `security-privacy-gate`, `logging-error-handling` | Raw exception forwarding. |
| Negative proof | Tests or review cannot distinguish validation, permission, conflict, timeout, cancellation, retryable, terminal, degraded, or partial failure. | Map each changed failure path to a test, validator, or residual risk. | Negative cases, changed-failure-to-validation map, freshness. | `quality-test-gate`, `validation-broker` | Happy-path-only confidence. |

# Selection Rules

Select this capability when the primary risk is failure semantics across owned boundaries. It owns the cross-layer taxonomy, translation map, public/private separation, retryability classification, fallback/degraded outcome, partial-failure recovery stance, async/message terminal behavior, and evidence limits.

Prefer `error-code-design` when the main decision is client-visible code, HTTP/gRPC status, response body shape, localization, SDK behavior, or public catalog compatibility. Prefer `logging-error-handling` when the main decision is log schema, correlation fields, levels, redaction, or audit logging. Prefer `idempotency-retry-design` when the main decision is idempotency keys, dedupe storage, replay, retry budget, or backoff. Prefer `transaction-consistency` when the main decision is invariant protection, isolation, outbox, or saga mechanics. Prefer `degradation-circuit-breaking` when the main decision is timeout, fallback, circuit, bulkhead, or fail-open/closed policy.

# Technical Selection Criteria

Evaluate each failure by source, boundary, local type, caller-visible outcome, user message, diagnostic cause, retryability, idempotency precondition, cancellation behavior, partial side effect, compensation or DLQ path, security disclosure risk, observability signal, negative test, current source evidence, graph/memory freshness, and residual owner.

A failure contract is professionally defined only when the normal path, each expected failure, each unexpected failure, and each terminal or degraded outcome can be distinguished by code, test, operator signal, or explicit not-verified disclosure.

# Proactive Professional Triggers

- **Signal:** `catch`, `except`, `rescue`, promise rejection, or error callback returns `null`, `None`, empty/default data, success, or "best effort" without a typed degraded state. **Hidden risk:** silent failure becomes normal behavior. **Required professional action:** define typed fallback or propagate a safe failure. **Route to:** `logging-error-handling`, `observability`. **Evidence required:** fallback state, cause preservation, metric/log/trace, negative test.
- **Signal:** Repository, adapter, SDK, database, framework, provider, or CLI errors cross into service, controller, UI, job, or public API code as raw exceptions or raw messages. **Hidden risk:** internal leakage and dependency coupling become public contract. **Required professional action:** add boundary translation and safe public/private split. **Route to:** `error-code-design`, `security-privacy-gate`. **Evidence required:** source-to-local translation map and raw-detail suppression proof.
- **Signal:** Validation, permission, not-found, conflict, timeout, cancellation, dependency, and internal errors all map to one generic failure. **Hidden risk:** callers retry incorrectly, users receive wrong recovery guidance, and operators cannot diagnose cause. **Required professional action:** define taxonomy and caller action per state. **Route to:** `quality-test-gate`. **Evidence required:** state table and negative tests for each changed state.
- **Signal:** Timeout or cancellation is treated as ordinary error or retried automatically. **Hidden risk:** cancelled work is resurrected, duplicate side effects occur, or alerts page on expected aborts. **Required professional action:** define timeout, cancellation, unknown-outcome, and retry stance. **Route to:** `idempotency-retry-design`, `degradation-circuit-breaking`. **Evidence required:** timeout/cancellation contract and retry/no-retry proof.
- **Signal:** A multi-step operation can persist, publish, cache, write files, or call a provider before a later step fails. **Hidden risk:** partial success is hidden behind a generic error. **Required professional action:** trace side effects and define compensation, reconciliation, or operator-visible terminal state. **Route to:** `data-side-effect-flow-tracing`, `transaction-consistency`. **Evidence required:** step order, irreversible effects, compensation/DLQ, residual risk owner.
- **Signal:** Queue, job, webhook, or consumer failure lacks ack/nack timing, retry exhaustion, DLQ payload, poison-message rule, or replay safety. **Hidden risk:** lost work, retry loops, or duplicate side effects. **Required professional action:** define async failure contract and terminal ownership. **Route to:** `message-queue-design`, `idempotency-retry-design`. **Evidence required:** ack timing, retry budget, DLQ/replay test, operator alert.
- **Signal:** Fallback returns stale, cached, empty, skipped, or degraded output without user impact, staleness, observability, or cleanup rule. **Hidden risk:** degraded mode is indistinguishable from correct data. **Required professional action:** define degraded state and fail-open/closed rationale. **Route to:** `degradation-circuit-breaking`, `observability`. **Evidence required:** degraded response, metric/log/trace, product or owner acceptance, test.
- **Signal:** Error response, log, metric, trace, support screenshot, or event includes raw stack, SQL, path, token, key, provider payload, tenant hint, resource existence detail, prompt, or tool output. **Hidden risk:** security or privacy disclosure. **Required professional action:** separate user-safe message from diagnostic detail and redact at source. **Route to:** `security-privacy-gate`, `logging-error-handling`. **Evidence required:** no-leak test or review artifact and trace correlation.
- **Signal:** Project memory, generated docs, repository graph, or prior validation says failure handling is already safe. **Hidden risk:** stale source or generated artifact drift masks a broken failure path. **Required professional action:** confirm current source, callers, tests, and validation freshness before accepting. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limit.
- **Signal:** Tests only assert happy path or generic failure while changed logic branches on failure class. **Hidden risk:** implementation can invert permission, retry, conflict, cancellation, or partial-failure behavior and tests still pass. **Required professional action:** add behavior-sensitive negative proof or disclose residual risk. **Route to:** `quality-test-gate`, `testability-seam-design`. **Evidence required:** changed-failure-to-validation map and assertion quality.

# Risk Escalation Rules

Escalate to `security-privacy-gate` when failure detail can reveal secrets, PII, auth state, tenant existence, provider internals, SQL, file paths, prompts, tool output, or resource existence. Escalate to `reliability-observability-gate` when silent fallback, retry storms, degraded mode, dependency failure, DLQ depth, or cancellation noise affects SLOs or incident response. Escalate to `data-api-contract-changer` when public API, SDK, event, or webhook failure contracts change. Escalate to `delivery-release-gate` when rollout, rollback, feature flags, migration, or production operation depends on the new failure behavior.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active cross-boundary failure contract rules, output contract, and evidence contract.

If deep references are added later, load them only for L3+ work, public API or async/message boundaries, partial failure, raw dependency leakage, fallback/degradation, compensation, DLQ, or unclear retryable versus terminal semantics. Do not load deep references for L1/L2 local error handling where this inline taxonomy, translation, output contract, and handoff contract are sufficient.

# Critical Details

- Retryable failures are narrow: transient network, timeout, throttling, and dependency saturation only when the operation is idempotent or guarded.
- Terminal failures include malformed input, unsupported state, permanent provider rejection, failed authorization, invalid credentials, and non-recoverable domain violations.
- Unknown write outcome after timeout is not ordinary retryability; reconcile by idempotency key or durable reference before retry.
- Cancellation should preserve caller intent and usually avoids retry or alert unless cleanup failed.
- Adapter translation maps provider/SDK/database errors into local outcomes at the adapter boundary.
- Repository translation hides raw SQL/ORM/storage internals while preserving diagnostic cause safely.
- Controller translation maps local failures to safe status, code, message, and trace id when the response is public.
- Job and consumer contracts define ack/nack, retry exhaustion, DLQ, poison-message handling, and replay safety.
- Panic or process exception recovery belongs at framework, process, job, or task boundary with fail-fast or restart semantics where appropriate.
- Fallback is a typed decision with user impact, stale data policy, metric, removal path, and owner acceptance.

# Execution Coupling

- **Repository graph:** inspect the owning boundary, callers, downstream adapters, generated clients or specs, tests, async consumers, and generated artifacts before claiming a failure path is covered.
- **Project memory:** treat prior incidents, fragile files, stale validation, or previous review findings as search leads; accept or reject them only after current-source confirmation.
- **Execution path:** connect planned edits, review findings, and validation commands to the failure taxonomy so a repair does not change the failure contract without re-review.
- **Validation freshness:** mark failure-contract evidence stale when later edits touch translation code, public error mapping, fallback, retry wrapper, side-effect order, DLQ behavior, tests, generated specs, or reports.
- **Plan consistency:** final handoff reconciles planned failure states, actual changed files, validation run order, skipped failure paths, and residual owners.

# Failure Modes

- **Silent fallback:** `catch` returns null, empty list, cached default, or success without typed degraded state or observable cause.
- **Raw leak:** database, SDK, stack trace, SQL, query, token, path, prompt, provider body, tenant hint, or customer data reaches a client, event, or log sink.
- **Retry confusion:** validation, permission, permanent provider rejection, cancellation, or non-idempotent writes are retried as transient failures.
- **Lost cause:** error wrapping replaces root cause, provider status, correlation id, or boundary context with a generic message.
- **Cancellation noise:** caller cancellation triggers retries, ERROR alerts, or work resurrection.
- **Partial success hidden:** durable write, cache update, event publish, file write, or provider side effect succeeds while the response says generic failure.
- **ACK-before-durability:** consumer acknowledges before durable processing and lacks DLQ or replay behavior.
- **Untested negative path:** tests cannot distinguish validation, permission, conflict, timeout, cancellation, degraded, partial, retryable, and terminal outcomes.
- **Stale memory:** prior notes or generated docs claim coverage while current source, consumers, or validation have drifted.
- **Boundary drift:** controller, service, repository, adapter, job, and UI each invent local error semantics and clients receive inconsistent behavior.

# Output Contract

Return a Failure Contract with:

- `mode_selected` (taxonomy definition, boundary translation, retryability split, partial failure recovery, async/message failure, fallback/degradation, safe diagnostics, or negative proof).
- `boundaries_inspected` (controller, service, domain, repository, adapter, SDK/provider, job, consumer, UI/client, logs/metrics/traces, tests, graph, memory, and skipped boundaries with reason).
- `source_evidence` (current files, callers, generated specs/clients, tests, reports, prior memory, or graph slices inspected).
- `graph_memory_execution_judgment` (accepted, rejected, stale, or not verified for prior failure-contract claims).
- `failure_taxonomy` (state, source, local type, retryability, terminal/degraded outcome, user action, operator action).
- `boundary_translation_map` (raw source failure -> local failure -> public response/event/job outcome -> diagnostic record).
- `retryability_and_cancellation` (retryable, non-retryable, conditional, timeout unknown outcome, cancellation stance, idempotency precondition).
- `partial_failure_recovery` (step order, durable effects, compensation, rollback, reconciliation, DLQ, irreversible residue, owner).
- `fallback_degradation_contract` (typed degraded state, stale policy, fail-open/closed rationale, user impact, removal path).
- `async_message_contract` (ack/nack timing, retry budget, DLQ payload, poison-message rule, replay safety, alert).
- `safe_diagnostics` (user-safe message, internal cause preservation, redaction rule, correlation/trace behavior).
- `changed_failure_to_validation_map` (each changed failure state mapped to test, validator, review evidence, or residual risk).
- `handoff_boundaries` (error-code, logging, retry/idempotency, transaction, degradation, observability, security, release, docs).
- `evidence_limits` (untested provider paths, unknown consumers, production-only failures, stale graph/memory, skipped validators).

# Evidence Contract

Close a failure contract only when these answers are concrete:

- **Basis:** selected mode, changed boundary, failure state, and standard or repository convention used.
- **Boundaries inspected:** source files, callers/callees, adapters/providers, repositories, controllers, jobs/consumers, generated specs/clients, tests, graph leads, memory leads, and skipped boundaries.
- **Placement rationale:** why taxonomy and translation live at the selected boundary and why public code, logging, retry, transaction, or degradation details are handed to adjacent owners.
- **Validation evidence:** literal commands, tests, evals, review artifacts, or not-verified disclosure, with freshness after final material edits.
- **What evidence proves:** the specific failure state, translation, safe message, retry/no-retry, partial recovery, fallback, or DLQ behavior covered.
- **What evidence does not prove:** external provider behavior, production timing, unknown consumers, skipped async paths, stale generated artifacts, or untested chaos/retry conditions.
- **Behavior preservation:** old public errors, retry behavior, logging correlation, user messages, and terminal states preserved or intentionally migrated.
- **Residual risk and next gate:** untested state, owner, rollback or recovery note, and next capability or professional skill.

# Benchmark Coverage

This capability covers typed failure taxonomies, boundary translation, retryable/terminal classification, validation/permission/conflict/timeout/cancellation distinctions, safe public/private diagnostics, partial-failure recovery, fallback/degraded state, async DLQ and poison-message behavior, cause preservation, graph/memory/execution freshness, changed-failure-to-validation mapping, and evidence-limited handoff without expanding into API code catalogs, log schemas, retry algorithms, or transaction mechanics.

# Routing Coverage

Routes from `backend-change-builder`, `data-api-contract-changer`, `data-middleware-change-builder`, `integration-change-builder`, `reliability-observability-gate`, `quality-test-gate`, `ai-code-review-refactor`, and `frontend-change-builder` should arrive here when failure states, translation, retryability classification, safe diagnostics, fallback/degradation, partial recovery, or async terminal behavior are unclear. Route away when the primary decision is public error response shape, structured logging schema, idempotency storage, retry backoff, transaction isolation, resilience circuit settings, or release approval.

# Quality Gate

1. Mode, boundaries inspected, source evidence, graph-memory-execution judgment, and evidence limits are recorded.
2. Failure states are typed or otherwise machine-distinguishable; message text alone is rejected.
3. Boundary translation maps raw dependency/framework/storage/provider failures to local outcomes before public or higher-layer use.
4. User-visible failures are safe and contain no raw internals, secrets, PII, tenant hints, stack traces, SQL, paths, tokens, prompt/tool data, or provider bodies.
5. Diagnostic cause, correlation, and boundary context are preserved internally with redaction.
6. Retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, degraded, partial, and internal states are distinct where material.
7. Unknown write outcome after timeout has reconciliation or idempotency guidance before retry.
8. Fallback and degraded responses are typed, observable, and distinguishable from correct data.
9. Partial failure has compensation, rollback, reconciliation, DLQ, operator visibility, or explicit residual-risk acceptance.
10. Async/job/message behavior defines ack/nack, retry exhaustion, DLQ or poison-message handling, replay safety, and terminal owner.
11. Negative validation covers each changed failure state or names not-verified residual risk.
12. Graph, memory, and prior validation are current-source confirmed or downgraded before closure.
13. Handoff boundaries keep API code catalogs, log schema, retry mechanics, transaction consistency, degradation policy, security review, and release approval with the correct adjacent owner.

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

Hand off to `error-code-design` for public error codes, response shapes, status mapping, localization, SDK behavior, and compatibility; to `logging-error-handling` for diagnostic fields, levels, correlation, redaction, and audit logging; to `idempotency-retry-design` for idempotency keys, dedupe, replay, retry budget, and backoff; to `transaction-consistency` or `data-side-effect-flow-tracing` for side-effect order, invariant protection, compensation, and reconciliation mechanics; to `degradation-circuit-breaking` or `observability` for timeout, fallback, circuit, metric, dashboard, and alert design; to `security-privacy-gate` for disclosure risk; and to `delivery-release-gate` when rollout or rollback depends on failure behavior.

Keep ownership narrow: this capability defines failure categories and boundary semantics, then hands formatting, telemetry, retry implementation, transaction mechanics, degradation tuning, and release approval to their owners.

# Completion Criteria

The capability is complete when every changed boundary has a typed failure taxonomy, translation map, retry/no-retry and cancellation stance, fallback/degraded state, partial-failure recovery or residual-risk owner, async/message terminal behavior when relevant, safe user message, internal cause preservation, fresh negative validation or not-verified disclosure, graph/memory/execution freshness statement, and explicit handoff to adjacent owners.
