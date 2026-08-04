# Logging Selection Criteria

Owner: `logging-design-gate`. In task mode, `task-agent` implements an accepted logging decision; in review mode, `review-agent` independently inspects the actual diff and runs only non-modifying checks. Load this reference only when purpose, placement, level, fields, redaction, correlation, or signal choice is unresolved.

## Purpose Before Signal

| Question to answer | Candidate signal and fields | Reject or escalate when |
| --- | --- | --- |
| Why did one operation fail or degrade? | Diagnostic log or trace with operation, safe error category/code, dependency, attempt, duration, fallback, and correlation. | The event cannot distinguish failure stages or would expose payloads/identifiers. |
| Who performed a governed action and what was decided? | Audit record with actor, scoped subject/resource, action, decision/reason, policy/version, purpose, and integrity/retention owner. | It is mixed into disposable diagnostics or the privileged actor is obscured. |
| Did a security boundary deny or detect abuse? | Security/audit signal with policy/category, actor/resource scope, result, request/run context, and safe investigation link. | Raw hostile input, secrets, or sensitive identity would be retained. |
| Which business lifecycle fact changed? | Domain event or business-safe record with fact, entity type/scoped identifier, state transition, result, and owner. | A diagnostic log is being used as the authoritative business ledger. |
| Is an external dependency or worker healthy and recoverable? | Dependency/worker signal with operation, latency, timeout/failure class, retry/terminal state, queue age/attempt, and correlation. | Per-item volume, unbounded IDs, or duplicate signals overwhelm the diagnostic value. |
| Did process/config/migration/readiness lifecycle change? | Lifecycle event with version/config fingerprint or migration ID, readiness/result, environment, and safe cause. | Startup success is logged before the actual readiness boundary. |

Use access logs only when request entry, latency, or status is an owned diagnostic or operational need.
Use route templates and bounded classes.
Do not log raw URLs, queries, bodies, credentials, or personal data.

## Placement, Level, And Data Safety

- Place request identity at entry, workflow/final outcome in the application owner, dependency details in the adapter, and job delivery state in the worker. Pure domain code returns decisions/events rather than importing infrastructure logging.
- Choose severity from final operation consequence and current platform policy. Expected validation/not-found behavior is not automatically an error; retries/fallbacks are not automatically warnings; fatal/critical is reserved for an actually unrecoverable process or integrity condition.
- Allowlist stable fields. Omit or transform passwords, tokens, authorization/cookies, keys, signatures, session material, raw URLs/queries/bodies/webhooks/provider payloads, regulated data, and unnecessary PII according to classification and retention policy.
- Preserve approved trace/request/correlation context across the actual boundary, but keep request, trace, actor, entity, tenant, free-text, and other unbounded values out of metric labels.
- When frequency or value space is material, estimate volume and cardinality.
- Choose aggregation, sampling, rate control, shorter retention, a metric, a trace, a test, or no new signal from that evidence.
- Do not log every occurrence by default.

## Mode-Specific Proof Limits

Task mode proves the final diff emits the intended safe event through mapped tests or runtime capture available in scope. Review mode returns a verdict and reviewed/unreviewed scope without repair. Static source review does not prove runtime emission, sink redaction, sampling, retention, access control, production cardinality, or audit immutability; name the residual owner.

Route implementation mechanics to `logging-error-handling` and cross-signal telemetry to `observability`.
Route secret classification or configuration to `secret-configuration-security`.
Route release-blocking evidence to the selected Professional owner.
Reject function-entry INFO spam and default ERROR logs for validation or ordinary absence.
Reject audit mixed with transient diagnostics, raw payload logging, high-cardinality labels, and logs in pure domain objects.
