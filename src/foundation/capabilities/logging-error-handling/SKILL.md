---
name: logging-error-handling
description: Designs structured logs with correlation IDs, sensitive-data redaction, and an error model that distinguishes user, system, third-party, and security errors.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "44"
changeforge_version: 0.1.0
---

# Mission

Design **structured logging and error handling** that supports incident diagnosis, safe client responses, audit trail integrity, distributed trace correlation, and sensitive-data protection — ensuring logs carry sufficient context to diagnose any failure in production while never exposing secrets, personal data, or internal stack traces to external consumers.

# When To Use

Use this capability when a change: adds or modifies exception handling, error responses, or error mapping at any layer; introduces structured log statements with fields beyond message string; adds correlation ID / trace context propagation to services, queues, or scheduled jobs; designs audit events for regulated or security-sensitive workflows; handles third-party API failures and must decide on retry signal, alerting, and client messaging; or is flagged in review for "logs contain PII", "no trace context on outbound calls", or "raw exception in API response."

# Do Not Use When

Do not use this capability to log raw request or response payloads, credentials, tokens, session cookies, passwords, encryption keys, or internal stack traces into client-facing responses. Do not use it as an alternative to proper secret management (secrets must never appear in log sinks at all — not redacted, not masked — they must be excluded at the source).

# Stage Fit

Use this capability during planning, implementation, review, testing, and release when the change modifies error taxonomy, log fields, client-visible error behavior, correlation propagation, audit events, or sensitive diagnostic handling. It is especially relevant when memory, graph context, or prior execution notes claim logging is already safe: those signals may identify patterns, but current source, tests, logger configuration, and sink behavior must provide the closing evidence.

Do not expand it into general observability, alerting, or dashboard design unless log-derived signals are the primary decision. Pair it with `observability` only when log events feed alerts, SLOs, dashboards, or incident response workflows.

# Non-Negotiable Rules

- **Correlation IDs must propagate across every boundary.** Every inbound HTTP request, queue message, scheduled job, and outbound external call must carry a `correlationId` (or W3C `traceparent`) in all log statements. Without correlation, an error in a downstream job is disconnected from the originating request, making root-cause analysis impossible in distributed systems.
- **Sensitive data must be excluded at the log call site — not redacted downstream.** Field-level redaction (replacing PAN with `****`) is a fallback, not the primary strategy. The primary strategy is to never pass sensitive fields to the logger. Regex scrubbers in log pipelines cannot reliably catch all patterns. **OWASP Logging Cheat Sheet**: never log: passwords, auth tokens, session identifiers, full card numbers (PCI DSS Req 3.4), SSNs, private keys.
- **Error taxonomy must be explicit: User / System / ThirdParty / Security.** User errors (`4xx`; validation failure, not-found, duplicate) are expected; log at `INFO` or `WARN`. System errors (`5xx`; unexpected exceptions, infrastructure failure) are unexpected; log at `ERROR` with stack trace and correlation. ThirdParty errors (dependency timeout, external API `5xx`) are boundary failures; log with upstream context, retryability, and SLO impact. Security errors (authN failure, authZ denial, suspicious pattern, token forgery attempt) are security events; emit to security audit log at `WARN`/`SECURITY`; never leak decision details to the client.
- **Client-facing error responses must be stable, opaque, and actionable.** API error responses (RFC 7807 `application/problem+json`) must expose: `type` (stable URI), `title`, `status`, `detail` (user-actionable message), `instance` (request path or trace ID). They must NOT expose: stack traces, SQL queries, internal exception messages, class names, database column names, or internal identifiers.
- **Expected error paths must not produce noisy ERROR logs.** `404 Not Found` for a resource lookup is an expected outcome — log at `DEBUG` or `INFO`. `429 Rate Limited` is expected — log at `INFO`. Only log at `ERROR` or `WARN` when a genuinely unexpected condition occurs. Noisy ERROR logs mask real incidents and cause alert fatigue.
- **Audit events for security-sensitive operations are mandatory.** Authentication (success + failure), authorization denial, permission change, sensitive data access, configuration change, and account management events must be written to an append-only audit log sink (separate from application logs) with: actor, action, resource, outcome, timestamp (ISO 8601 UTC), IP, and correlation ID. NIST SP 800-92, SOC 2 CC7.2, PCI DSS Req 10.
- **Infrastructure exception types must not propagate to application or domain layers.** `psycopg2.errors.UniqueViolation`, `SqlException`, `MongoWriteConcernError`, `RedisConnectionError` must be caught at the adapter boundary and re-raised as domain exceptions. The application layer must never import or catch infrastructure-specific exception classes.
- **Structured log format must be machine-parseable.** Log in JSON (structured logging) with fixed schema fields: `timestamp`, `level`, `service`, `correlationId`, `traceId`, `spanId`, `message`, `error.type`, `error.message`, `error.stacktrace` (system errors only), `userId` (pseudonymized / hashed), `requestId`. Human-readable messages are for development mode only; production log sinks must be JSON.

# Industry Benchmarks

Anchor against OWASP Logging Cheat Sheet, NIST SP 800-92, W3C Trace Context, OpenTelemetry Logs Data Model, RFC 7807 Problem Details, PCI DSS logging requirements, SOC 2 security-event evidence, Elastic Common Schema, and APM error grouping practices. Keep the main skill focused on routing and closure; use [references/checklist.md](references/checklist.md) for the lightweight execution checklist and [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed matrices, schemas, trace propagation, redaction, and audit examples.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capability | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Error taxonomy and client response | Exception mapping, status codes, error bodies, user-facing failures | Stable user/system/third-party/security classification with opaque RFC 7807 responses | Exception mapper, API response tests, sample failure responses | `error-code-design` | No client-visible error semantics changed |
| Structured diagnostic logging | New logger fields, severity changes, stack traces, request context | Parseable schema, level discipline, support diagnosis, no alert noise | Log output fixture, logger configuration, severity assertions | `observability` | Copy-only message change preserving fields and level |
| Correlation and async context | HTTP boundaries, queues, jobs, outbound calls, workflow fan-out | `traceparent` or `correlationId` propagation through every execution boundary | Middleware, job headers, outbound client tests, log assertions | `async-job-design` | Single-process path with existing verified context binding |
| Audit and security logging | AuthN/AuthZ, permission changes, sensitive access, admin override | Append-only audit sink, actor/action/resource/outcome, no protected detail leakage | Audit event tests, sink configuration, retention or immutability evidence | `authentication-security` | Non-security diagnostic path |
| Regression and release evidence | Refactor, config change, log pipeline change, prior-memory claim | Prove current behavior rather than trusting previous notes or generated summaries | Fresh validation commands, source paths, what evidence proves and does not prove | `quality-test-gate` | No behavior, schema, sink, or permission change |

# Selection Rules

Select this capability when: error handling semantics, log field design, correlation propagation, or sensitive-data redaction strategy is the primary concern. Route elsewhere when: **error-code-design** is primary (API error contract shape and error code registry); **observability** is primary (metrics, dashboards, SLI/SLO, alerting on log-derived signals); **authentication-security** is primary (authentication event design and token security); **secret-configuration-security** is primary (secrets never reaching the log pipeline).

# Risk Escalation Rules

Escalate when: any log statement may contain PII, PAN, password, token, or private key; an error response may leak internal exception messages or SQL; audit events are required for a regulated workflow (PCI, SOC 2, HIPAA, GDPR); a third-party failure causes silent data loss (no dead letter, no alert); a security denial event is not being written to the audit log; or the error taxonomy conflates user errors with system errors (causing alert storms on normal traffic).

# Proactive Professional Triggers

- **Signal:** A handler returns `str(error)`, raw exception messages, stack frames, SQL fragments, or provider responses to clients. **Hidden risk:** an implementation detail becomes an enumeration or exploit aid. **Required professional action:** separate internal diagnostics from RFC 7807 client output, map to stable error codes, and prove no internal detail leaves the boundary. **Route to:** `error-code-design`, `security-privacy-gate`. **Evidence required:** response fixture plus negative assertion for stack, SQL, class names, and provider internals.
- **Signal:** A log statement includes raw payloads, request bodies, query strings, cookies, tokens, credentials, payment data, or unnecessary personal data. **Hidden risk:** secret or privacy exposure persists in replicated log sinks. **Required professional action:** replace field capture with allow-listed diagnostic fields and test forbidden-field absence at the log call site. **Route to:** `secret-configuration-security`, `security-privacy-gate`. **Evidence required:** logger call diff, captured log fixture, and explicit forbidden-field assertion.
- **Signal:** An async job, queue consumer, scheduler, worker, or outbound dependency logs without `traceparent`, `traceId`, or `correlationId`. **Hidden risk:** incidents cannot be connected across execution boundaries. **Required professional action:** bind context before the first log statement and inject correlation into headers or metadata rather than domain payloads. **Route to:** `async-job-design`, `integration-change-builder`. **Evidence required:** middleware or consumer binding, message-header assertion, and cross-boundary log sample.
- **Signal:** Expected validation, not-found, conflict, denial, or rate-limit paths are logged at `ERROR` or alert directly. **Hidden risk:** on-call loses trust in error signals and real incidents are buried. **Required professional action:** reclassify expected outcomes to `INFO` or `DEBUG`, reserve `WARN` and `ERROR` for unexpected or degraded conditions, and document alert eligibility. **Route to:** `observability`, `quality-test-gate`. **Evidence required:** level-policy table, log fixture, and alert rule or non-alert statement.
- **Signal:** Memory, graph context, previous validation output, or generated summaries state that logging is safe after fields, adapters, middleware, or sink configuration changed. **Hidden risk:** stale evidence masks a privacy or diagnosis regression. **Required professional action:** re-open the current source path, compare against same-pattern implementations, rerun focused assertions, and disclose what remains unverified. **Route to:** `plan-execution-consistency`, `validation-broker`. **Evidence required:** inspected file list, command results, and residual-risk note.

# Critical Details

- **Log level discipline prevents alert fatigue.** `ERROR` must mean: a human must investigate this now. `WARN` must mean: this is unexpected but the system recovered. `INFO` must mean: normal business event worth recording. `DEBUG` must mean: diagnostic detail for development. Never log validation failures at `ERROR`. Never log `404` lookups at `WARN`. The signal-to-noise ratio of `ERROR` logs determines whether on-call engineers trust alerts.
- **Async and queue consumers need explicit correlation injection.** An HTTP request that enqueues a job must embed `correlationId` (or `traceparent`) in the message header/attribute — NOT in the message body (to avoid schema coupling). The consumer must extract it and bind it to the logging context (MDC in Java, `contextvars` in Python, AsyncLocalStorage in Node.js) before processing begins.
- **Audit log must be append-only and tamper-evident.** Application logs can be rotated and expired. Audit logs for security-sensitive operations (auth, permission changes, data access) must be written to a separate, append-only sink (AWS CloudTrail, GCP Cloud Audit Logs, Azure Monitor, a dedicated append-only database table with write-only role). Audit logs must not be deletable by the application service account.
- **Error response must carry a `traceId` / `correlationId` for support handoff.** When a user reports an error, the support team needs to find the corresponding log entry. The client-facing RFC 7807 response `instance` field or a custom `correlationId` field must give the exact identifier needed for log search. Without this, support cannot diagnose reported errors.
- **ThirdParty failure logging must distinguish timeout / 5xx / circuit-open / auth-failure.** These require different remediation: timeout → increase timeout or add retry with backoff; `5xx` → back-off and alert; circuit-open → dependency is degraded, apply fallback; auth failure → rotate credentials, alert security. One generic "external call failed" log message defeats incident response.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `logger.error(f"User login failed: {password}")` | Password in log | Remove password from log call entirely; log only username and failure reason |
| `return JsonResponse({"error": str(e)})` in view | Stack trace / internal message in client response | Map exception to RFC 7807; log full exception internally; return stable error code |
| `logger.error("Request failed")` for every 404 | Alert fatigue; 404 is normal | Log 404 at `INFO` or `DEBUG`; `ERROR` only for unexpected conditions |
| `except Exception: pass` in consumer | Silent failure; messages lost | Log at `ERROR` with correlation; republish to DLQ; never silently swallow |
| No `correlationId` in async job log | Cannot trace job failure to request | Inject `correlationId` from message header into job logging context |
| Audit events written to same sink as app logs | Audit log deleted with log rotation | Write security events to separate append-only audit sink |
| `logger.info(json.dumps(request.json()))` | Full request body in logs (may contain PII, tokens) | Log only approved fields with explicit allow-list |

# Failure Modes

- Logs lack correlation IDs — an error in a queue consumer cannot be linked to the triggering HTTP request; root cause analysis requires code reading rather than log search.
- Password, token, or credit card number appears in log during a new feature debug session; credential is harvested from log aggregation system.
- `500 Internal Server Error` response body contains raw `NullPointerException: Cannot read property 'id' of undefined at OrderService.confirm:57` — attacker learns internal class structure and file paths.
- `ERROR` log for every `404` resource lookup generates 10,000 error events per hour; real `500` system failures are buried; on-call engineer misses the actual incident.
- Third-party payment API timeout logged as generic "payment failed" — no distinction between timeout/5xx/auth-failure; wrong remediation applied.
- Security denial events (invalid token, permission denied) not written to audit log — SOC 2 audit finds no evidence of access control event logging; compliance failure.
- Async job processing fails silently (`except Exception: pass`) — messages are lost; dead-letter queue never fills; no alert fires; data inconsistency accumulates undetected.
- Infrastructure exception (`psycopg2.errors.UniqueViolation`) propagates to application service — application imports `psycopg2`; switching to a different database requires changes in application layer.
- Log sink is also used as audit log — log rotation policy deletes 30-day-old entries; regulatory requirement mandates 1-year audit retention; compliance gap discovered at audit.
- `traceId` not included in error response body — user reports error with screenshot; support cannot find the log entry without full timestamp correlation.

# Reference Loading Policy

Read `references/checklist.md` when the change touches client-visible errors, audit events, third-party failure handling, async/queue correlation, or sensitive-data logging risk. Read `references/benchmarks-and-patterns.md` when the decision needs benchmark mapping, taxonomy tables, structured schema, trace propagation, redaction boundaries, audit/diagnostic split, or graph-memory-execution coupling rules. Do not load references for a pure log-message copy change that preserves fields, levels, correlation behavior, sink configuration, and client output.

# Output Contract

Return a logging and error handling design with:

- `mode_selected` (taxonomy, structured logging, correlation, audit/security, or regression/release evidence)
- `error_taxonomy` (User / System / ThirdParty / Security; with HTTP status and log level for each)
- `client_error_response` (RFC 7807 fields; stable codes; no internal detail)
- `exception_mapping` (infrastructure exception → domain exception → HTTP response: table)
- `correlation_strategy` (W3C traceparent propagation; MDC/contextvars/AsyncLocalStorage binding; queue message header injection)
- `structured_log_schema` (fields: timestamp, level, service, correlationId, traceId, spanId, message, error.type, error.message, error.stacktrace[system only], userId[pseudonymized], http.*)
- `redaction_rules` (fields never logged; allow-list of loggable fields per request type)
- `audit_events` (actor, action, resource, outcome, timestamp, IP, correlationId; separate append-only sink)
- `third_party_failure_handling` (timeout / 5xx / circuit-open / auth-failure: log context + retryability + alert signal for each)
- `log_level_policy` (DEBUG/INFO/WARN/ERROR criteria; expected error paths at INFO; only unexpected at ERROR)
- `alert_relevance` (which log events trigger alerts; error rate thresholds; dependency failure signals)
- `test_strategy` (assert: correlation ID present in all log statements; no sensitive fields in log output; RFC 7807 shape for error responses; audit events written to audit sink on security-relevant paths)
- `source_evidence` (current source paths, logger configuration, middleware/adapters, tests, and fixtures inspected)
- `graph_memory_execution_coupling` (how prior memory, repository graph, and actual execution evidence agreed or conflicted)
- `validation_freshness` (commands run now, timestamp or run context, and stale evidence explicitly rejected)
- `tool_permission_boundary` (read-only versus state-mutating tools used, sandbox/approval context, and any secret-bearing output avoided)
- `evidence_scope` (what the current log fixtures, response assertions, audit checks, and propagation tests prove, plus the sink/runtime behavior left outside scope)
- `residual_risk` (privacy, diagnosis, audit, alerting, and untested sink behavior)

# Evidence Contract

Close logging/error design only when the output states the error taxonomy boundary, inspected log/error/audit paths, same-pattern scan, sensitive-field exclusion evidence, correlation propagation, client-visible behavior preservation, audit sink boundary, validation command or not-verified disclosure, graph-memory-execution consistency, tool permission/sandbox record, what evidence proves, what it does not prove, residual privacy/diagnosis risk, and handoff to observability or security when needed.

# Quality Gate

The design is complete only when:

1. All log statements include `correlationId` / `traceId` — no log statement without trace context.
2. Sensitive field exclusion list is explicit and enforced by test (assert no `password`, `token`, `card_number` in log output).
3. Error taxonomy covers all 4 classes (User / System / ThirdParty / Security) with correct log levels.
4. API error responses conform to RFC 7807; no internal exception messages or stack traces in response body.
5. Expected error paths (validation errors, 404s, 429s) do not log at `ERROR`.
6. Security events (authN failure, authZ denial, permission change) written to separate audit log sink.
7. W3C traceparent propagated on all outbound HTTP calls and queue message headers.
8. Async jobs bind correlation context before first log statement in job processing.
9. Infrastructure exceptions mapped to domain exceptions at adapter boundary; no infrastructure imports in application or domain layers.
10. Audit log sink is append-only; separate from application log rotation policy.
11. Current source, tests, and configuration confirm any memory or graph claim about logging behavior.
12. Validation evidence is fresh for this change and states its limits.
13. Tool use avoids printing or storing raw secrets, environment dumps, full payloads, or private diagnostic output.

# Used By

- backend-change-builder
- reliability-observability-gate
- logging-design-gate

# Benchmark Coverage

This capability covers industry anchors for safe log content, structured event schema, distributed trace correlation, client-safe HTTP error details, security audit evidence, and operational log search. Detailed mappings live in `references/benchmarks-and-patterns.md` so the router can keep `SKILL.md` small while still supporting deep review when selected.

# Routing Coverage

Route here for logging/error coupling across Skill + Memory + Graph + Execution when the user asks for professional diagnosis, privacy-safe logging, safe error responses, or evidence-backed closure. Route away to `observability` for metrics and alert design, `error-code-design` for central API error registries, `authentication-security` for authentication-specific audit semantics, and `secret-configuration-security` when the primary issue is secret source control or configuration handling.

# Handoff

Hand off to `observability` for SLI/SLO definition, alert threshold design, and dashboard construction from log-derived metrics; `error-code-design` for the full API error code registry; `secret-configuration-security` for ensuring secrets never reach logging pipelines; `authentication-security` for audit event schema for authentication flows.

# Completion Criteria

The capability is complete when **every log statement carries correlation context, sensitive data is excluded at the call site, error taxonomy is explicit with correct log levels, client responses are RFC 7807-compliant and opaque, security events flow to an append-only audit sink, and all constraints are verified by automated tests**.
