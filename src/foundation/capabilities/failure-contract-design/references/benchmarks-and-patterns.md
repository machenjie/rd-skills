# Failure Contract Design Benchmarks And Patterns

Use this reference when `failure-contract-design` needs more depth than the main `SKILL.md` should carry efficiently. Keep it focused on stable failure meaning, translation, classification, partial or degraded outcomes, safe representations, and specialist handoff.

## Benchmark Anchors

- Typed result and exception boundary practice: boundary failures should be machine-distinguishable.
- RFC 7807/9457 and gRPC canonical mapping: public error responses need stable shape and safe meaning.
- OWASP secure error handling: At a public error trust boundary, translate failures to stable safe meaning. Exclude secrets, internals, SQL, paths, provider payloads, prompts, and protected tenant-existence signals. Retain sensitive causes in authorized diagnostics with correlation and redaction.
- Cause-preserving translation: keep external details safe while preserving authorized internal evidence that identifies the failing boundary.
- Partial and degraded-result practice: escaped effects and reduced-quality results need explicit meaning and a named specialist owner.

## Failure State Matrix

| State | Caller action | Operator action | Retry stance | Escalate when |
| --- | --- | --- | --- | --- |
| Validation | Correct input. | Inspect validation rule drift only if unexpected. | Do not retry unchanged request. | Public schema or localization changes. |
| Permission | Authenticate, request access, or stop. | Check policy and audit context. | Do not retry without auth change. | Resource existence or tenant hint can leak. |
| Conflict | Refresh state or retry with new precondition. | Inspect concurrent writers. | Conditional retry only with conflict contract. | Invariant or transaction boundary is unclear. |
| Timeout | Preserve unknown outcome unless current evidence proves otherwise. | Retain safe dependency and correlation context. | Route retry mechanics when outcome or identity is unresolved. | Write outcome is unknown. |
| Cancellation | Preserve caller intent and distinguish cleanup failure. | Retain evidence only when cleanup or continued work matters. | Do not classify abandoned work as retryable by default. | Work may continue after cancellation. |
| Dependency | Translate to local stable meaning and preserve authorized cause. | Retain the failing boundary and safe correlation. | Record the classification and route retry or fallback mechanisms. | Provider detail can leak or partial state exists. |
| Degraded | Surface typed reduced-quality or stale meaning. | Name the specialist owner of the degradation decision. | Depends on the routed mechanism contract. | Degraded output can be mistaken for correct data. |
| Partial | State completed and incomplete effects plus residual owner. | Route recovery mechanics to the effect owner. | Do not retry without routed duplicate-safety proof. | A durable effect already escaped. |

## Boundary Translation Pattern

```text
raw dependency or framework failure
  -> local typed failure
  -> public safe response, event, job result, or UI state
  -> internal diagnostic record with cause, boundary, correlation, and redaction
```

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Catch returns null or empty success. | Silent failure becomes normal behavior. | Typed degraded or terminal failure plus observability. |
| Raw provider exception crosses boundary. | Public contract couples to dependency and may leak internals. | Adapter translation with cause preservation. |
| All failures become INTERNAL_ERROR. | Retry, user recovery, and incident diagnosis are wrong. | Typed taxonomy and changed-failure-to-validation map. |
| Unknown outcome labeled retryable. | Duplicate effects or false caller guidance. | Preserve unknown meaning and route retry identity/reconciliation. |
| Partial success returns generic error. | Escaped durable state and ownership disappear. | Return explicit partial meaning and route recovery mechanics. |
| Negative tests assert message text only. | Semantics can change while tests pass. | Assert machine-distinguishable type/status/code/outcome. |

## Handoff Boundaries

- Use `error-code-design` for public status, response body, code catalog, SDK behavior, localization, or compatibility.
- Use `logging-error-handling` for diagnostic fields, correlation, levels, redaction, audit, and log tests.
- Use `idempotency-retry-design` for idempotency keys, dedupe, replay, retry budget, and backoff.
- Use `transaction-consistency` or `data-side-effect-flow-tracing` for side-effect order, invariants, compensation, and reconciliation.
- Use `degradation-circuit-breaking` and `observability` for timeout, fallback, circuit, metrics, dashboards, and alerts.
- Use `security-privacy-gate` when failure detail can disclose sensitive data.
