# Logging Output And Gates

Load this reference when `logging-design-gate` needs the full output field list, closure gate, or handoff routing table. Keep the main skill body compact.

## Output Contract

Return a logging design decision with:

- **Mode selected**: no-log decision, diagnostic/error logging, security/access/audit logging, or hot-path signal design, with trigger signal.
- **Boundaries inspected**: entry/controller, domain, application service, adapter, queue/worker, security boundary, existing logger helpers, config sinks, tests, and skipped areas with reason.
- **Current-source reuse map**: accepted/rejected logger helper, field naming, trace context, redaction utility, sink, and test convention, including graph/memory/trajectory freshness.
- **Decision status**: `needed=true` with complete design, or `needed=false` with concrete metric, trace, test, public-behavior, or no-log alternative.
- **Log type and purpose**: diagnostic, audit, business event, security, access, integration/dependency, lifecycle, or no-log rationale.
- **Placement rationale**: owner layer, event boundary, and why the log belongs there instead of caller, domain object, adapter, or sink processor.
- **Level decision**: DEBUG/INFO/WARN/ERROR/CRITICAL policy for expected validation, 404, retry, fallback, degradation, and terminal failure.
- **Structured field schema**: field names, field source, allowed values, hashed identifiers, correlation identifiers, and compatibility with current conventions.
- **Forbidden field exclusions**: raw body, raw webhook body, raw URL query, authorization header, cookie, token, password, signature, secret, session id, and unapproved PII.
- **Redaction and hashing policy**: utility used, values transformed, values omitted, and test or review evidence.
- **Correlation and trace propagation**: trace_id, span_id, request_id, correlation_id, job id hash, or explicit no-correlation rationale.
- **Cardinality and volume controls**: sampling, rate limit, aggregation, DEBUG-only policy, metric-label limits, and hot-path performance assumption.
- **Signal split**: which operational question is answered by logs, metrics, traces, alerts, dashboards, or tests.
- **Audit and retention split**: audit sink, retention, actor/action/resource/result fields, diagnostic sink, and compliance owner when relevant.
- **Validation evidence**: command, test, validator, review artifact, exit code or not-run status, freshness, what evidence proves, and what it does not prove.
- **Tool permission/sandbox record**: shell, connector, log export, telemetry query, or secret-bearing action class, permission state, sandbox boundary, rollback/revert path, and redaction rule.
- **Behavior preservation**: existing API behavior, error contract, retry/fallback semantics, audit retention, privacy promises, and performance preserved or intentionally changed.
- **Residual risk**: sink configuration, retention policy, downstream processor, real traffic volume, unusual logger framework, or unverified production environment with owner.
- **Next gate/handoff**: security, reliability, quality, backend, data middleware, integration, documentation, delivery, or no-next-gate rationale.

## Quality Gate

1. Logging need or no-log rationale is explicit and tied to an operational, audit, security, or test evidence question.
2. Log type, placement, level, event, fields, redaction, correlation, and cardinality controls are concrete when logging is needed.
3. Audit, security, access, diagnostic, business event, integration, and lifecycle purposes are not conflated.
4. Forbidden raw or secret-bearing fields are excluded by design and tested or manually reviewed when relevant.
5. Expected validation/404, retryable intermediate failure, fallback/degradation, and terminal failure levels are distinguishable.
6. Hot paths use metrics, traces, sampling, aggregation, rate limits, or DEBUG-only logs unless bounded lifecycle/business evidence justifies INFO.
7. Required logging behavior maps to tests, validators, or explicit not-run residual risk with owner.
8. Graph, memory, and prior trajectory reuse is accepted only after current logger source confirms it.
9. Validation evidence states what it proves, what it does not prove, freshness, and evidence limits.
10. Sensitive log, audit, production telemetry, connector, and shell actions include tool permission/sandbox evidence.

## Handoff

- **security-privacy-gate**: sensitive fields, audit/access/security logs, denial category, retention, or forbidden raw input risk remains.
- **reliability-observability-gate**: metrics/traces/alerts, SLO signal, hot-path volume, cardinality, dashboard, or incident diagnosis needs broader observability design.
- **quality-test-gate**: required fields, redaction, retry/fallback distinction, denial category, or trace propagation lack tests.
- **backend-change-builder**: entry, service, adapter, worker, transaction, or error-boundary placement needs implementation.
- **data-middleware-change-builder**: queue, consumer, retry, DLQ, lag, cache, source-of-truth, or fallback diagnostics need middleware ownership.
- **integration-change-builder**: provider latency, translated error, retry, timeout, circuit state, reconciliation, or sandbox logs need adapter ownership.
- **change-documentation-gate**: audit evidence, retention, runbook, or operational note must be documented.
- **delivery-release-gate**: sink, retention, config, rollout, or post-release watch must be validated before release.
