# Input Validation Checklist

- Select the mode: new boundary, existing evolution, identifier/object scope, URL/path/fetch/execution selector, file/import intake, webhook/event payload, or validation error contract.
- Name every input source, actor, trust level, parser/validator owner, and server-side enforcement point.
- Inspect current routes, handlers, DTOs/schemas, validators, mappers, services, repositories, adapters, jobs/events, generated artifacts, tests, and relevant project memory or graph claims.
- For every field, declare type, required/optional, nullable/absent/empty semantics when relevant, size, length, range, enum, pattern/grammar, format, array/object bounds, and cross-field constraints.
- Define the canonicalization sequence before security checks: decode, Unicode normalize, trim, parse, resolve path/URL, case-fold where valid, and preserve raw body only where signatures require it.
- Reject unknown request fields unless a compatibility path explicitly tolerates them without mapping them into commands, ORM models, prompts, jobs, or provider calls.
- Validate identifiers for syntax, existence, ownership, tenant scope, permission context, lifecycle state, and query/filter placement using trusted server-side data.
- Guard state-changing and business-significant inputs with current-state, invariant, quota, pricing, role, permission, and lifecycle checks at the service/domain boundary.
- For URL/path/fetch/redirect/template/query/shell/selector/tool inputs, define destination or grammar allowlist, deny ranges/base path, timeout/size bounds, fail-closed behavior, and redacted diagnostics.
- For file/upload/import/archive inputs, validate size, magic bytes/content signature, filename/storage key, path containment, archive entries, scan-before-publish state, tenant ownership, and malicious fixtures.
- For webhooks/events, verify raw-body signature before parse, constant-time comparison, timestamp/freshness, replay/idempotency key, schema version, and safe rejection behavior.
- Define validation errors with stable code/type, status, field path, safe message, safe rejected-value echo policy, redaction for logs/metrics/traces, and localization or SDK impact.
- Classify compatibility when constraints tighten, required fields change, enum/range/length changes, parser strictness changes, unknown-field handling changes, or accepted file/event types change.
- Map every changed rule to validation evidence: valid, invalid, boundary, malformed, hostile, unauthorized, unknown-field, file/webhook/fetch, compatibility, and error-contract cases.
- Record reuse/placement rationale, behavior preservation, graph-memory-trajectory judgment, evidence limits, handoff boundaries, residual-risk owner, and final validation freshness.
