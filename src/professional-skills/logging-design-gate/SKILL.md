---
name: logging-design-gate
description: Designs development-time logging decisions for code changes, including log taxonomy, placement, level policy, structured fields, correlation, redaction, audit versus diagnostic boundaries, and log-versus-metric tradeoffs.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Logging Design Gate

## Mission
Design code-level logging as an engineering decision, not as benchmark runner output. Use this skill to decide whether logs are needed, where they belong, what type and level they have, which structured fields are safe, how they connect to traces and metrics, and how retry, fallback, degradation, and final failure paths remain diagnosable without exposing secrets or creating noise.

Own the SDD/TDD logging slice for ChangeForge process traces: the SDD logging decision, safe schema, placement, redaction, correlation, cardinality controls, and the TDD evidence that proves required logging or no-log rationale.

## When To Use
- A code change adds, removes, or changes logs.
- Error handling, retries, fallback, degraded mode, dependency calls, workers, queues, or scheduled jobs need diagnosability.
- Security denial, authorization, access, audit, webhook, payment, or sensitive data handling touches observability.
- A reviewer sees "add structured logging" without a concrete type, placement, level, fields, and redaction policy.
- A reliability, backend, data middleware, integration, security, or quality gate needs log evidence tied to tests.
- A high-frequency path risks log volume, high-cardinality labels, or performance overhead.

## Do Not Use When
- The task is only benchmark runner logging, report generation logs, or CLI progress output unrelated to product code behavior.
- A higher-level reliability design only needs metrics, traces, SLOs, and alerting, with no code log decision.
- The change is a comment-only or docs-only edit with no runtime behavior or operational evidence impact.

## Stage Fit
Use this skill during coding, bug-fix, debugging, code-review, refactoring, and testing stages when product log behavior changes or is required evidence. For release handoff, pair it with `reliability-observability-gate` and `security-privacy-gate` when sink, retention, alerting, or audit policy must be validated.

## Non-Negotiable Rules
- **Logs are evidence, not decoration**: each added production log must have a diagnostic, audit, business, security, access, integration, or lifecycle purpose.
- **Declare placement before fields**: choose the owning layer first, such as entry/controller, domain, application service, adapter, queue/worker, or security boundary.
- **Separate audit from diagnostic logs**: audit logs prove actor/action/resource/decision/result; diagnostic logs explain execution and failure.
- **Never log raw secret-bearing input**: password, token, authorization header, cookie, API key, secret, private key, raw request body, raw webhook body, raw URL query, signature, code, session identifier, full card data, and unapproved PII are forbidden.
- **Use correlation by default on request or job paths**: include trace_id, span_id, request_id, or correlation_id when the path crosses services, queues, or retries.
- **Production error logs need classification**: include error_code or error_category, retryable, attempt, dependency when relevant, and correlation identifiers.
- **Intermediate retry failures are not final failures**: do not emit ERROR for every retry attempt; use DEBUG or WARN with attempt and retryable semantics, then ERROR only for terminal failure.
- **High-frequency paths require controls**: prefer metrics, sampling, rate limiting, aggregation, or debug-only logs over per-iteration INFO.
- **Metric labels are stricter than log fields**: entity_id_hash may be acceptable in logs but not as an unbounded metric label.
- **Test logging when it is part of the design**: fields, redaction, denial categories, retry/fallback logs, and trace propagation must map to tests or validation commands when they are required behavior.

## Industry Benchmarks
- **OpenTelemetry semantic conventions**: use trace and span correlation so logs can be joined with distributed traces rather than becoming isolated strings.
- **OWASP Logging Cheat Sheet**: record security-relevant events, avoid sensitive data exposure, and protect log integrity.
- **NIST SP 800-92**: distinguish operational logging from audit evidence, retention, review, and tamper resistance needs.
- **Google SRE practices**: logs are expensive and are not a substitute for metrics, alerts, SLOs, or traces on high-volume paths.
- **CNCF observability practice**: logs, metrics, and traces answer different questions; choose the signal that matches the operational question.

## Technical Selection Criteria
Classify each log decision by type, owner layer, level, fields, redaction, and validation path.

### Log Taxonomy
- **Diagnostic log**: used for troubleshooting and execution reconstruction. Focus on operation, error_code, duration_ms, dependency, attempt, retryable, fallback_used, and correlation identifiers.
- **Audit log**: used for compliance or security audit. Focus on actor, action, resource, decision, timestamp, result, and integrity controls. It must not be casually deleted or mixed with transient diagnostics.
- **Business event log**: used for key domain state changes such as order_cancelled or payment_failed. Focus on domain_event, entity_type, entity_id_hash, state_from, state_to, result, and business-safe context.
- **Security log**: used for denials, authorization failures, abnormal access, and policy matches. Focus on policy, reason, category, actor_hash, resource_type, and result. Never log raw secret-bearing input.
- **Access log**: used at request entry. Focus on method, route_template, status_class, latency_ms, request_id, and user_or_tenant hash where allowed. Never log raw query, raw body, or authorization material.
- **Integration/dependency log**: used for external dependency calls. Focus on dependency, operation, latency_ms, status, retryable, attempt, timeout, circuit_state, and correlation identifiers.
- **Lifecycle log**: used for startup, shutdown, configuration loading, migration, and job scheduling. Focus on version, environment, config fingerprint, migration id, scheduler state, and readiness result.

### Level Policy
- **DEBUG**: low-frequency deep diagnostics; production default off or sampled; never the only signal needed for incident diagnosis.
- **INFO**: key lifecycle events, important business state changes, and important successful transitions; not every function entry or cache miss.
- **WARN**: recoverable anomaly, retry, fallback, degradation, stale dependency state, or unexpected condition that did not make the operation fail; include retryable when relevant.
- **ERROR**: request, job, command, or operation finally failed with user impact, data impact, lost side effect, or required investigation. Expected validation errors and ordinary 404s are not ERROR.
- **CRITICAL/FATAL**: process cannot continue, startup is unrecoverable, data may be corrupted, or a required dependency is unavailable with no degradation path.

### Structured Fields
Prefer structured fields with stable names:
- timestamp
- level
- service
- environment
- version
- trace_id
- span_id
- request_id
- correlation_id
- operation
- domain_event
- entity_type
- entity_id_hash
- tenant_id_hash
- status
- error_code
- error_category
- retryable
- attempt
- duration_ms
- dependency
- fallback_used
- degradation_reason

Fields suitable for logs may be too high-cardinality for metric labels. Use route_template, status_class, dependency, error_category, retryable, and operation as metric labels; avoid raw IDs, raw URL, raw query, raw payload, request_id, trace_id, entity_id_hash, tenant_id_hash, and arbitrary user input as metric labels.

### Redaction And Forbidden Inputs
Forbidden in production logs:
- password
- token
- access_token
- refresh_token
- authorization header
- cookie
- api key
- secret
- private key
- full credit card
- raw request body
- raw webhook body
- raw URL query
- signature, code, or session identifiers
- PII unless hashed, explicitly allowed, and retention-reviewed

Allowed with care:
- hashed user, entity, or tenant id
- route template
- status class
- error code or category
- dependency name
- duration
- attempt count
- policy or denial category

### Placement Policy
- **Entry/controller**: access logs, request identity, route template, status_class, latency_ms, request_id, and validation boundary outcomes.
- **Domain**: avoid infrastructure logging in pure domain objects. Emit domain events or return decisions that application services can log.
- **Application service**: workflow decisions, domain event publication, transaction boundary results, fallback decisions, and final operation result.
- **Adapter/infrastructure**: dependency latency, timeout, retryable status, circuit state, translated error categories, and safe provider metadata.
- **Queue/worker**: job id hash, attempt, idempotency key hash, lag bucket, retry/final failure, DLQ decision, and correlation propagation.
- **Security boundary**: denial category, policy, actor/resource hash, result, and audit handoff without raw secret-bearing input.

## Mode Matrix
Select the logging design mode that matches the operational evidence need.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
|---|---|---|---|---|---|
| No-log decision | Code path is already proven by tests, metrics, traces, or public behavior and adding logs would add noise. | State why logs are not needed and what signal replaces them. | No-log rationale, metric/trace/test alternative, validation command, residual risk. | `quality-test-gate`, `reliability-observability-gate` | Skip log schema design when no production log is required. |
| Diagnostic/error logging | Error, retry, fallback, degradation, dependency call, or lifecycle behavior needs operator diagnosis. | Choose placement, level, fields, correlation, and final-vs-intermediate failure semantics. | Log type, owner layer, event, level, structured fields, redaction, cardinality control, tests. | `logging-error-handling`, `reliability-observability-gate`, `quality-test-gate` | Skip audit retention design unless audit evidence is required. |
| Security/access/audit logging | Authorization, access, webhook, policy denial, audit evidence, token, cookie, PII, or raw payload risk appears. | Separate audit from diagnostic logs and block secret-bearing fields. | Policy/category fields, actor/resource hash policy, sink/retention decision, redaction tests, trace_id/request_id. | `security-privacy-gate`, `quality-test-gate` | Skip raw request body, raw query, authorization header, cookie, token, signature, and PII fields. |
| Hot-path signal design | High-frequency INFO, cache miss, loop, async path, worker stream, or per-event logging is proposed. | Prefer metrics, sampling, aggregation, rate limits, or DEBUG-only logs over per-event noise. | Frequency estimate, sampling/rate limit, metric alternative, high-cardinality controls, performance validation. | `reliability-observability-gate`, `performance/event-loop-blocking-async-path` | Skip per-operation INFO unless a bounded business/lifecycle event justifies it. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A change says "add structured logging" without log type, placement, event, level, fields, or redaction. **Hidden risk:** logs become noisy strings or leak secrets while reviewers assume observability improved. **Required professional action:** require a structured logging decision before implementation. **Route to:** `logging-error-handling`, `quality-test-gate`. **Evidence required:** logging_decision object with type, placement, events, level, fields, redaction, cardinality controls, and tests or no-log rationale.
- **Signal:** Retry, fallback, degradation, DLQ, worker, or dependency-call logs use ERROR for intermediate failures. **Hidden risk:** alert fatigue hides terminal failures and operators cannot distinguish retryable from final states. **Required professional action:** split WARN intermediate attempts from ERROR terminal failures. **Route to:** `reliability-observability-gate`, `data-middleware-change-builder`. **Evidence required:** levels, retryable/attempt/final fields, failure-mode tests, and validation output.
- **Signal:** Security, access, audit, webhook, token, cookie, authorization header, raw request body, raw URL query, or PII appears in a log decision. **Hidden risk:** diagnostic evidence creates a data leak or audit-retention breach. **Required professional action:** route through security logging design and remove forbidden raw/secret fields. **Route to:** `security-privacy-gate`, `quality-test-gate`. **Evidence required:** allowed field list, redaction policy, denial category/policy, and redaction/security tests.
- **Signal:** Audit and diagnostic logs share the same event, sink, or retention rationale. **Hidden risk:** audit evidence loss and hidden retention collision make compliance review unverified. **Required professional action:** split audit purpose, sink, retention, and diagnostic schema before approval. **Route to:** `security-privacy-gate`, `change-documentation-gate`. **Evidence required:** log sink/retention map, actor/action/resource/result fields, validation command or review note, and residual risk.
- **Signal:** INFO logging is proposed on a hot path, loop, cache miss, every request, or high-frequency worker event. **Hidden risk:** cost, latency, and high-cardinality labels regress while logs fail to answer incident questions. **Required professional action:** use metrics, traces, sampling, aggregation, or DEBUG-only logs unless bounded lifecycle/business evidence is needed. **Route to:** `reliability-observability-gate`, `quality-test-gate`. **Evidence required:** metric/trace alternative, sampling or rate-limit control, and performance/noise validation.

## Risk Escalation Rules
- Escalate to `security-privacy-gate` when logs touch PII, credentials, authorization, audit evidence, access control, or webhook signatures.
- Escalate to `reliability-observability-gate` when logs must be balanced with metrics, traces, alerts, SLOs, dashboards, recovery, or incident diagnosis.
- Escalate to `backend-change-builder` when entry, service, adapter, or transaction-boundary log placement is unclear.
- Escalate to `data-middleware-change-builder` when queues, consumers, retries, DLQs, cache stampedes, lag, or fallback paths require logs.
- Escalate to `integration-change-builder` when dependency latency, error translation, retry, timeout, circuit breaker, reconciliation, or sandbox behavior needs logs.
- Escalate to `quality-test-gate` when logging fields, redaction, security denial, retry, fallback, or trace propagation must be tested.

## Critical Details
Use this decision sequence:
1. Decide whether a log is needed. If not, state the no-log rationale and the alternative evidence signal.
2. Choose log type: diagnostic, audit, business event, security, access, integration/dependency, or lifecycle.
3. Choose owner layer and event boundary.
4. Choose level using the policy above.
5. Define structured fields and correlation identifiers.
6. Define forbidden fields and redaction/hashing.
7. Decide whether metrics, traces, or alerts are the primary signal instead of logs.
8. Add cardinality, sampling, rate limit, and performance controls for hot paths.
9. Map required logging behavior to tests or validation commands.

### PDD / DDD / SDD / TDD Relationship
- **PDD**: identify which user, system, audit, or operational impacts must be observable.
- **DDD**: identify which domain events, state transitions, and invariant violations need diagnostic or audit evidence.
- **SDD**: design log schema, placement, level, fields, redaction, high-cardinality controls, and trace correlation.
- **TDD**: test log fields, redaction, security denial, retry/fallback/error paths, and trace_id propagation when logging is required.

## Failure Modes
- Expected 404 or validation errors are logged as ERROR.
- Every cache miss or retry attempt emits ERROR.
- INFO is emitted inside a hot loop without sampling or rate limits.
- Raw exception plus raw request body, webhook body, URL query, token, password, cookie, or authorization header is logged.
- Audit evidence is mixed with short-retention diagnostic logs.
- Logs use raw IDs or arbitrary user input as metric labels.
- Security denials omit policy category or record secret-bearing input.
- Retry logs cannot distinguish intermediate retryable failure from final failure.
- Logs are added with no tests for redaction or required fields.

## Reference Loading Policy
Read `references/capabilities/index.md` only when the selected capability list is available and the task needs deeper foundation detail. Load only the selected capability references for the active L1, L2, L3, L4, or L5 route. Do not read all references by default. When a selected capability needs more detail, read `references/capabilities/<capability-id>-<capability-name>.md` and only the adjacent references explicitly named there.

## Output Contract
Return or embed a logging decision with this shape when logs are relevant:

```json
{
  "needed": true,
  "log_types": [],
  "placement": [],
  "events": [],
  "levels": [],
  "fields": [],
  "redaction": [],
  "correlation": [],
  "metrics_traces_alerts": [],
  "cardinality_controls": [],
  "tests_or_validation": [],
  "rationale": ""
}
```

When logs are not needed, return:

```json
{
  "needed": false,
  "rationale": "specific reason and alternative evidence signal"
}
```

- **Decision status:** return `needed=true` with the complete logging design, or `needed=false` with a concrete metric, trace, test, or public-behavior alternative.
- **Required fields:** include log_types, placement, events, levels, fields, redaction, correlation, cardinality_controls, tests_or_validation, and rationale when logging is needed.
- **Forbidden fields:** list raw request body, raw webhook body, raw URL query, authorization header, cookie, token, password, signature, and PII exclusions.
- **Level decision:** state why expected validation errors, retry attempts, fallback, degradation, and terminal failures use their selected levels.
- **Validation evidence:** map required fields, redaction, denial category, retry/fallback distinction, and trace propagation to tests or validation commands.
- **Residual risk:** state any sink, retention, downstream processor, or traffic-volume assumption not proven by local validation.
- **Handoff:** name the next gate for security, reliability, audit, or test follow-up.

## Evidence Contract
Close logging design only when these evidence obligations are answered:
- **Files and boundaries inspected**: entry/controller, domain, application service, adapter, queue/worker, security boundary, existing logger helpers, tests, and config sinks inspected or explicitly unavailable.
- **Reuse / placement rationale**: existing logger helpers, field names, trace context, redaction utilities, and owner layer conventions reused; new log placement justified by event ownership.
- **Behavior preservation**: existing API behavior, error contract, retry/fallback semantics, audit retention, and performance on hot paths remain compatible or are explicitly changed.
- **Validation evidence**: logging design validator output, redaction/security tests, retry/fallback tests, audit sink checks, or no-log metric/trace/test alternative.
- **What evidence proves**: required logs have safe type, level, placement, fields, redaction, correlation, cardinality controls, and TDD evidence.
- **What evidence does not prove**: validator output does not prove production sink configuration, retention policy, alert thresholds, or real traffic volume unless those artifacts were inspected.
- **Residual risk**: unusual logger frameworks, dynamic fields, downstream processors, or external retention policies may require manual review.
- **Next gate**: `security-privacy-gate` for sensitive/audit/access logs, `reliability-observability-gate` for metrics/traces/alerts, and `quality-test-gate` for logging tests.

## Quality Gate
- Log type, placement, level, fields, redaction, correlation, and cardinality controls are explicit when logging is needed.
- Audit, security, access, diagnostic, business event, integration, and lifecycle logs are not conflated.
- No forbidden secret-bearing or raw input field is allowed.
- Retry, fallback, degradation, and terminal failures remain distinguishable.
- Metrics, traces, alerts, and logs are assigned to the right signal role.
- Required logging behavior maps to tests or validation commands.

## Handoff
Report the logging design, the no-log rationale when applicable, sensitive fields excluded, tests or validation run, residual logging risk, and any required follow-up with security, reliability, backend, data middleware, integration, or quality owners.

## Completion Criteria
- A reviewer can tell whether logs are needed and why.
- Required logs have type, owner layer, level, fields, redaction, correlation, and high-cardinality controls.
- Sensitive input exposure is blocked by design and, when relevant, by tests.
- Operational diagnosis does not depend on DEBUG-only logs.
- The design names metrics, traces, alerts, or no-log alternatives where logs are the wrong signal.
