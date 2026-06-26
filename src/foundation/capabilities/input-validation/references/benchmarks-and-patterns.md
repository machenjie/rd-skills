# Input Validation Benchmarks and Patterns

Use this reference when `SKILL.md` says deeper validation design is needed. Keep the main skill body lightweight; this file carries the detailed matrices.

## Benchmark Anchors

- OWASP ASVS V5: validation, sanitization, and encoding expectations.
- OWASP API Security API3 and API8: property-level authorization and security misconfiguration risks around mass assignment and validation gaps.
- OWASP Top 10 A03: injection failures caused by unvalidated or unsafely interpreted input.
- CWE-20: improper input validation.
- CWE-22: path traversal.
- CWE-79: cross-site scripting.
- CWE-89: SQL injection.
- CWE-434: unrestricted upload of dangerous file type.
- CWE-918: server-side request forgery.
- CWE-915: mass assignment and unsafe modification of object properties.
- RFC 7807 and RFC 9457: problem detail payloads for validation errors.
- JSON Schema 2020-12 and OpenAPI 3.1: machine-readable schema constraints.
- Zod, Pydantic, Joi, Bean Validation, express-validator, and similar strict schema libraries: parse-don't-trust boundary patterns.
- OWASP File Upload, SSRF, SQL Injection, XSS, Deserialization, and Logging cheat sheets.
- HMAC webhook verification patterns from Stripe, GitHub, and cloud providers: raw body, timestamp, replay window, and constant-time comparison.

## Layer Responsibility Matrix

| Layer | Validate here | Do not hide here | Evidence |
| --- | --- | --- | --- |
| Edge or controller | Request shape, required fields, unknown fields, primitive types, size caps, raw body capture for signatures. | Business authorization, domain lifecycle decisions, storage source of truth. | Schema/validator path, rejected malformed payload, unknown-field test. |
| DTO or schema mapper | Allowlisted mapping, null/absent/empty/default semantics, serialization format, generated contract alignment. | Raw request pass-through, ORM exposure, permission decisions. | Field table, mapper test, generated schema diff. |
| Application service | Identifier existence, ownership, tenant scope, permission context, quotas, state transition guards. | HTTP syntax concerns or UI feedback timing. | Trusted source lookup, denied wrong-owner/tenant case. |
| Domain model | Value object invariants, lifecycle invariants, cross-field business rules. | External parsing, user identity derivation, provider protocol details. | Constructor/invariant tests and domain exception mapping. |
| Infrastructure adapter | File magic bytes, archive traversal, URL resolution, webhook raw-body signature, provider payload schemas. | User-facing error taxonomy or business policy. | Malicious fixture, tampered signature, timeout/size limit case. |
| Error/log/metric boundary | Safe field path, stable violation code, redacted rejected value, trace linkage. | Raw regex, stack trace, provider body, full URL or secret. | Error snapshot, log redaction assertion, bounded metric labels. |

## Constraint Taxonomy

Every trust-boundary field should declare the relevant subset:

- Type: string, integer, decimal, boolean, array, object, date, datetime, enum, uuid, opaque id, file, URL.
- Presence: required, optional, nullable, absent means no-op, absent means default, empty string/list/object allowed or rejected.
- Size and bounds: min/max length, min/max value, decimal precision, array item count, object property count, upload size, import row count.
- Format or grammar: allowlisted regex, parser grammar, exact enum set, RFC 3339 datetime, ISO 4217 currency, E.164 phone, BCP 47 locale, slug rules.
- Structure: nested required fields, additional properties policy, discriminated union tag, recursion/depth limit.
- Canonicalization: URL decode, Unicode NFC normalization, whitespace trim, case folding for case-insensitive fields, path resolve, URL parse, timezone normalization.
- Cross-field rule: start before end, currency required when amount exists, one-of/mutually exclusive fields, conditional required fields.
- Authority rule: identifier exists, belongs to caller or tenant, has required lifecycle state, is visible to subject, and matches trusted server-side subject/scope.
- Security rule: no path traversal, no null bytes, no control characters in header-like fields, no raw template, no executable file, no private/link-local URL destination.
- Compatibility rule: whether tightening is additive, conditional, breaking, or requires bridge/version/deprecation.

## Canonicalization Sequence Pattern

1. Preserve raw bytes only for signature verification when required.
2. Decode transport encoding at the boundary.
3. Parse into the intended type without coercing risky values such as `"false"` to truthy strings or floats to money.
4. Normalize Unicode and whitespace according to field semantics.
5. Resolve paths, URLs, hosts, ports, and addresses before containment or allowlist checks.
6. Validate structure, primitive constraints, and grammar.
7. Validate cross-field, authority, tenant, lifecycle, and business rules.
8. Map through an allowlisted DTO/command.
9. Return safe error details and redacted diagnostics.

## URL and Server-Side Fetch Matrix

| Control | Requirement | Evidence |
| --- | --- | --- |
| Scheme | Only explicitly allowed schemes, normally `https` and sometimes `http` for internal allowlists. | Reject `file:`, `gopher:`, `ftp:`, `javascript:`, and missing scheme. |
| Host and port | Exact allowlist or validated destination policy; no prefix/suffix tricks. | Reject `trusted.com.evil.test`, userinfo tricks, and unexpected ports. |
| DNS and address | Resolve before fetch; deny loopback, private RFC 1918, link-local, multicast, and metadata ranges. | Reject `127.0.0.1`, `::1`, `169.254.169.254`, and private ranges. |
| Redirects | Revalidate every redirected destination before following. | Redirect-to-private test blocked. |
| Timeout and size | Bounded connect/read timeout and response size. | Timeout and oversized response tests. |
| Diagnostics | Log normalized host, decision, reason code, request id; redact userinfo, query, fragment, token, key, signature, and secret. | Error/log sample with no sensitive raw URL values. |

## File, Upload, Archive, and Import Matrix

| Control | Requirement | Evidence |
| --- | --- | --- |
| Size | Enforce before reading unbounded data and before expensive transforms. | Oversized request rejected early. |
| Type | Validate magic bytes/content signature against allowlist, not extension or browser MIME. | `.jpg` extension with non-image content rejected. |
| Name and key | Generate storage key server-side; store original filename only as display metadata after sanitization. | Path traversal filename rejected; generated key not attacker-controlled. |
| Archive | Reject absolute paths, `..`, symlinks if unsafe, nested bombs, excessive file count/depth/ratio. | Zip slip and decompression bomb fixtures rejected. |
| Scan and publish | Scan before user-visible availability where user-provided files are shared. | State transition from uploaded to available requires clean scan. |
| Tenant ownership | Bind object key, metadata, and access policy to tenant/account. | Wrong-tenant download/read denied. |

## Webhook and Event Payload Matrix

| Control | Requirement | Evidence |
| --- | --- | --- |
| Raw body | Signature uses exact raw bytes before JSON parsing or normalization. | Tampered raw body rejected. |
| Algorithm | Declared HMAC/hash/signature algorithm and trusted secret/key owner. | Header algorithm confusion rejected. |
| Constant time | Signature comparison avoids timing leaks. | Code review or library proof. |
| Freshness | Timestamp, nonce, event id, or replay window defined. | Old timestamp and duplicate event rejected or idempotently ignored. |
| Schema | Event type/version and payload fields validated after authenticity. | Unknown event type/version handled safely. |
| Idempotency | Event id or business key prevents duplicate side effects. | Replay test proves no duplicate grant/payment/update. |

## Identifier and Authority Pattern

- Treat caller-supplied identifiers as references, not authority.
- Derive subject, tenant, role, and scope from authenticated server-side context.
- Query with both identifier and tenant/visibility predicate where possible.
- Use 404-style safe denial when existence is sensitive.
- Validate lifecycle state from storage, not request body.
- For bulk operations, authorize each object and define partial failure behavior.
- Map every identifier rule to wrong-owner, wrong-tenant, missing, deleted, wrong-state, and unauthorized cases where applicable.

## Validation Error Pattern

Validation errors should include:

- Stable code or RFC 7807/9457 `type`.
- Transport status such as 400 for malformed syntax and 422 for semantically invalid payload where local conventions support it.
- Field path when safe and useful.
- User-safe message or localization key.
- Violation code such as `required`, `too_long`, `invalid_format`, `unknown_field`, `forbidden_value`, `invalid_state`, or `not_visible`.
- Safe rejected-value policy: exact value, truncated value, class only, or no echo.
- Request/trace id for diagnostics.
- Redacted logs that keep operator detail without exposing secrets or attack payloads.

Never include raw stack traces, SQL errors, provider bodies, exact private regexes, raw URLs with secrets, file paths, tenant ids, secret values, or parser internals in client responses.

## Compatibility Classification

| Change | Default classification | Required response |
| --- | --- | --- |
| Add optional field accepted by server | Usually additive. | Add tests and schema docs. |
| Reject unknown request fields where old path ignored them | Potentially breaking. | Consumer scan, rollout, version, or compatibility mode. |
| Make optional field required | Breaking. | Version/deprecation/bridge and client evidence. |
| Tighten length, enum, range, format, parser strictness, or file type | Potentially breaking. | Old payload fixture replay and release gate. |
| Relax validation | Security-sensitive. | Threat review and downstream invariant proof. |
| Move rule from frontend to backend | Usually corrective but observable. | Direct API negative tests and client error handling check. |
| Change error shape or field path | Client-observable. | Error-code-design and frontend/SDK compatibility. |

## Graph, Memory, and Trajectory Coupling

Use graph and memory as evidence leads, not as truth:

- Repository graph: inspect current routes, handlers, validators, schemas, mappers, callers, generated specs, jobs/events, and tests that can reach the boundary.
- Project memory: accept only claims backed by current source, fresh reports, or intentionally preserved architecture decisions; reject or mark stale claims that conflict with source.
- Execution trajectory: note prior failed tests, incident findings, previous validation fixes, and current commands so the contract does not repeat a failed same-path retry.
- Evidence statement: record what was inspected, what it proves, what it does not prove, and which unknowns remain.

## Changed Validation to Test Map

For each changed field or boundary, map to the smallest sufficient proof:

- Happy path: valid canonical input accepted.
- Primitive constraints: required, type mismatch, min/max, enum, format, array/object bounds.
- Canonicalization: encoded, Unicode, whitespace, path/URL normalization, control characters.
- Unknown fields: rejected or tolerated according to policy.
- Authority: missing, deleted, wrong-owner, wrong-tenant, wrong-state, no permission.
- Security payloads: injection strings, traversal, SSRF destinations, redirect abuse, template/query/shell payloads, null bytes, CRLF.
- File/import: spoofed MIME, bad magic bytes, oversize, traversal archive, decompression bomb, malformed rows.
- Webhook/event: bad signature, stale timestamp, replay, unknown event, schema violation.
- Error contract: stable code, safe field path, no secret/raw regex/internal detail, trace id present.
- Compatibility: old valid fixture, generated client compile/contract, old event replay, rollback behavior.

## Handoff Decision Table

| Primary unresolved decision | Hand off to |
| --- | --- |
| Transfer schema shape, null/default semantics, mapping owner | `dto-schema-design` |
| Public validation error taxonomy, status, localization, trace | `error-code-design` |
| Subject/resource/action/condition authorization | `permission-boundary-modeling` |
| XSS, CSRF, SSRF, SQLi, RCE, deserialization, redirect, browser exploit review | `web-security` |
| File lifecycle, storage, scan, retention, signed URLs | `file-storage-processing` |
| Webhook/partner protocol retries, reconciliation, credentials | `integration-change-builder` |
| Validation coverage sufficiency and regression design | `quality-test-gate` |
| Rollout, rollback, canary, release communication for breaking validation | `delivery-release-gate` |
