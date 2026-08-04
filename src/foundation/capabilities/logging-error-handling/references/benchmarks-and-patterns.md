# Logging And Error Handling Benchmarks And Patterns

Load this reference when error classification, structured schema, trace propagation, redaction, audit separation, or logging proof changes. OWASP/NIST/OpenTelemetry/RFC guidance anchors the decision but does not prove the implementation.

## Event And Error Contract

| Surface | Required decision | Guardrail/proof |
| --- | --- | --- |
| Expected user/business outcome | Stable client code/remediation and a log level consistent with operator action. | Do not emit system-failure noise or stack traces for routine denied/invalid/not-found/conflict outcomes. |
| Unexpected/system/dependency failure | Internal cause/stack only where safe, opaque client response, correlation and dependency/retry context. | No raw exception/provider body, SQL, topology, policy, or secret leakage. |
| Security-relevant outcome | Keep the diagnostic event separate and consume an accepted audit contract when protected actor/action/resource/outcome evidence is required. | Record the audit owner and hand off unresolved semantics, integrity, retention, access, sink, or durability instead of defining the protected record here. |
| Retry/overload | Classify retryability and circuit/rate state without promising unsafe replay. | Client and log guidance match idempotency and current provider semantics. |

## Structured Context, Redaction, And Propagation

- Choose fields from the diagnostic need and accepted audit contract. Typical safe fields include timestamp, severity, service/version/environment, event/error code, operation, bounded resource/tenant context, correlation, status, and failure class.
- At a changed logging or diagnostic boundary, allowlist safe fields. Exclude passwords, cryptographic keys, bearer or session material, sensitive authentication or payment data, unrestricted payloads, query or provider bodies, and unredacted rejected input. Hash or pseudonymize identifiers when direct identity is unnecessary.
- Bind inbound trace/correlation context before the first log, propagate on outbound calls and async metadata, and extract before consumer work. Start a new trace only for an independent operation with an explicit link.
- Keep message prose evolvable; dashboards/alerts and client behavior depend on stable structured codes and bounded labels, not free text.

## Freshness And Validation

| Claim | Evidence and limit |
| --- | --- |
| Schema/redaction | Captured output proves required fields and forbidden-field absence for the changed path; local fixtures do not prove sink transforms/retention/access. |
| Error mapping | Success, expected failure, unexpected failure, dependency failure, and sensitive denial fixtures cover changed branches. |
| Trace continuity | HTTP/RPC and queue/job test shows context before logs and across the changed boundary. |
| Audit-contract handoff | Current accepted policy and owner identify required actor/action/resource/outcome evidence, integrity, retention, access, sink, and durability; this Skill verifies only the diagnostic boundary and dependency, not protected-record closure. |
| Freshness | Inspect current wrappers, middleware, mappers, consumers, clients, sinks and same-pattern paths; rerun after final edit. |

Route public error taxonomy to `error-code-design`, telemetry/cardinality to `observability`, sensitive/audit policy to `security-privacy-gate`, and retry semantics to `idempotency-retry-design`.

Reject blanket `ERROR` logging, client-visible internals, trace ids regenerated mid-request, correlation stored in domain payload, security audit mixed with disposable diagnostics, secret-bearing tool output, or green local assertions reported as live-sink proof.
