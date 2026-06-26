# Logging Selection Criteria

Load this reference when a logging design needs detailed taxonomy, level-by-level policy, structured field candidates, redaction allow/deny lists, or layer placement guidance. Do not load it for simple no-log decisions or one local log where the main `SKILL.md` output contract is sufficient.

## Log Taxonomy

- **Diagnostic log**: used for troubleshooting and execution reconstruction. Focus on operation, error_code, duration_ms, dependency, attempt, retryable, fallback_used, and correlation identifiers.
- **Audit log**: used for compliance or security audit. Focus on actor, action, resource, decision, timestamp, result, and integrity controls. It must not be casually deleted or mixed with transient diagnostics.
- **Business event log**: used for key domain state changes such as order_cancelled or payment_failed. Focus on domain_event, entity_type, entity_id_hash, state_from, state_to, result, and business-safe context.
- **Security log**: used for denials, authorization failures, abnormal access, and policy matches. Focus on policy, reason, category, actor_hash, resource_type, and result. Never log raw secret-bearing input.
- **Access log**: used at request entry. Focus on method, route_template, status_class, latency_ms, request_id, and user_or_tenant hash where allowed. Never log raw query, raw body, or authorization material.
- **Integration/dependency log**: used for external dependency calls. Focus on dependency, operation, latency_ms, status, retryable, attempt, timeout, circuit_state, and correlation identifiers.
- **Lifecycle log**: used for startup, shutdown, configuration loading, migration, and job scheduling. Focus on version, environment, config fingerprint, migration id, scheduler state, and readiness result.

## Level Policy

- **DEBUG**: low-frequency deep diagnostics; production default off or sampled; never the only signal needed for incident diagnosis.
- **INFO**: key lifecycle events, important business state changes, and important successful transitions; not every function entry or cache miss.
- **WARN**: recoverable anomaly, retry, fallback, degradation, stale dependency state, or unexpected condition that did not make the operation fail; include retryable when relevant.
- **ERROR**: request, job, command, or operation finally failed with user impact, data impact, lost side effect, or required investigation. Expected validation errors and ordinary 404s are not ERROR.
- **CRITICAL/FATAL**: process cannot continue, startup is unrecoverable, data may be corrupted, or a required dependency is unavailable with no degradation path.

## Structured Fields

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

## Redaction And Forbidden Inputs

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

## Placement Policy

- **Entry/controller**: access logs, request identity, route template, status_class, latency_ms, request_id, and validation boundary outcomes.
- **Domain**: avoid infrastructure logging in pure domain objects. Emit domain events or return decisions that application services can log.
- **Application service**: workflow decisions, domain event publication, transaction boundary results, fallback decisions, and final operation result.
- **Adapter/infrastructure**: dependency latency, timeout, retryable status, circuit state, translated error categories, and safe provider metadata.
- **Queue/worker**: job id hash, attempt, idempotency key hash, lag bucket, retry/final failure, DLQ decision, and correlation propagation.
- **Security boundary**: denial category, policy, actor/resource hash, result, and audit handoff without raw secret-bearing input.
