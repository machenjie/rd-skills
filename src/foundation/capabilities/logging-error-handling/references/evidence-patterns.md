# Logging Error Evidence Patterns

Use this reference when logging/error closure depends on repository inspection, prior task evidence, same-pattern scans, observable action sequence, validation freshness, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second logging tutorial.

## Logging Change-To-Evidence Map

| Logging or error claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Client error output is safe | Exception mapper, response fixture, stable error code/type, correlation field, and negative assertions for stack, SQL, class names, provider internals, and raw exception text | The inspected client boundary does not expose named internal details | Every localization, SDK wrapper, proxy, or downstream client behavior is covered |
| Sensitive fields are excluded | Logger call site, allowlisted fields, captured log fixture, and forbidden-field assertions for password, token, cookie, authorization header, card data, raw body, and raw query | The inspected path excludes known secret-bearing fields before sink ingestion | Downstream processors, dynamic fields, or untested request shapes are safe |
| Correlation propagates across boundaries | Middleware or entry binding, outbound header injection, queue/job metadata assertion, and log sample with `traceId` or `correlationId` | The inspected request/job can be followed across the named boundary | Every service hop, retry path, or production trace collector is configured |
| Expected failures avoid alert noise | Error taxonomy, level-policy table, log fixture, and alert/non-alert statement for validation, 404, conflict, denial, and rate-limit paths | The inspected expected outcomes do not emit terminal `ERROR` signals | Production alert routing, on-call thresholds, or traffic-volume effects are proven |
| Security-relevant outcome has an audit-contract handoff | Diagnostic boundary, accepted audit owner or named specialist handoff, required actor/action/resource/outcome evidence, and unresolved integrity, retention, access, sink, or durability gaps | The inspected diagnostic path identifies and routes its protected audit dependency | The protected audit record exists, is durable, or satisfies external SIEM, legal, or privileged-workflow requirements |
| Third-party failure is diagnosable | Timeout/5xx/auth/circuit classification, dependency name, retryability, attempt/final flag, correlation id, and client-safe response fixture | The inspected dependency failure can route remediation without provider secret leakage | Provider-side outage cause, sandbox parity, or all integration paths are verified |
| Infrastructure exception stays behind adapter | Adapter catch/translate point, domain exception type, application import search, and API/log fixture | The inspected infrastructure error does not leak through the application boundary | Every repository/adapter implementation follows the same translation policy |
| Prior note or report remains valid | Prior claim source/date, current source reread, same-pattern search, current validation command, exit code, and artifact/report path | The accepted memory or report still matches the inspected implementation | Future edits, uninspected sinks, or production runtime behavior are covered |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, incident notes, previous validation output, generated reports, and compaction summaries as selectors until current source, tests, fixtures, logger configuration, and sink evidence confirm them.
- Accept a prior "logging is safe", "redaction is tested", "trace context exists", "audit sink is append-only", or "expected errors are INFO" claim only when current source paths and fresh validation still match. An audit claim additionally requires the accepted audit owner contract and cannot be closed from diagnostic evidence alone.
- Mark evidence stale after edits to exception mappers, logger wrappers, middleware, job consumers, outbound clients, audit sinks, log schemas, redaction lists, config, fixtures, generated reports, or validation commands.
- Record inspected and skipped boundaries: entry/controller, service/application layer, adapter/repository, queue/worker, scheduled job, outbound dependency, security boundary, audit sink, diagnostic sink, client error contract, tests, and telemetry pipeline.
- Map every final logging/error confidence claim to a current command, fixture, source path, captured output, report artifact, owner review, or explicit not-verified residual risk.

- If log export, telemetry query, SIEM lookup, or production payload sample, require owner, bounded query, redaction, timestamp, dataset, and no-secret disclosure.
- If sink configuration change, retention change, audit export, deploy, or rollback, require explicit permission, dry-run where available, rollback/forward-fix path, owner, and redaction rule.
