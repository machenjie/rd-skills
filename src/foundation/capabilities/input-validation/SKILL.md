---
name: input-validation
description: Designs server-enforced validation for type, length, format, range, allowlist, ownership, and semantic constraints because client validation is insufficient.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "53"
changeforge_version: 0.1.0
---

# Mission

Define server-enforced validation at every trust boundary so malformed, hostile, unauthorized, oversized, stale, or semantically invalid input is rejected before it can corrupt state, bypass authorization, poison downstream contracts, or trigger unsafe processing. Validation work must bind current source evidence, repository graph, project memory, execution trajectory, changed fields, and test evidence into one contract rather than listing field rules in isolation.

# When To Use

Use this capability when a change accepts or changes HTTP bodies, query parameters, path parameters, headers, cookies, files, form submissions, CLI arguments, environment/configuration inputs, webhook payloads, event payloads, import records, server-side fetch URLs, path selectors, template fragments, AI/tool inputs, automation parameters, or any data crossing from an external actor, lower-trust subsystem, generated client, queue, storage import, or partner integration. Also use it when adding security-meaningful fields to existing endpoints or tightening validation in a way deployed clients may observe.

# Do Not Use When

Do not use this capability as a substitute for internal type safety, pure UI form feedback, full web exploit review, object-level authorization modeling, DTO schema design, or client-visible error taxonomy. Route to `dto-schema-design` for transfer schema shape, `permission-boundary-modeling` for object access rules, `web-security` for exploit-class review, `error-code-design` for public error semantics, and `form-validation-design` for frontend validation timing and UX.

# Stage Fit

Use during planning when a new boundary, field, parser, upload, webhook, fetch, import, or automation input is introduced. Use during coding and review when validators, parsers, DTO binding, canonicalization, ownership guards, allowlists, adapters, or error mapping change. Use during testing and release when hostile-input cases, client compatibility, rollback, generated clients, prior incidents, project memory claims, or graph-discovered callers need proof. Hand off when endpoint semantics, authorization policy, file lifecycle, exploit-class analysis, or release approval becomes the primary decision.

# Non-Negotiable Rules

- **Server trust-boundary enforcement is mandatory.** Client validation, HTML attributes, generated clients, SDK types, UI hiding, API gateway checks, and form libraries are convenience or defense-in-depth only.
- **Allowlists beat blocklists.** Define accepted type, length, range, enum, character set, pattern, and parser grammar; do not rely on filtering known-bad substrings.
- **Canonicalize before security decisions.** Decode, normalize, trim, resolve, and parse before checking paths, URLs, encodings, identifiers, filenames, or header-like values.
- **Reject unknown request fields unless compatibility requires an explicit tolerant path.** Silent pass-through creates mass assignment and hidden semantic drift.
- **Identifiers require syntax, existence, ownership, tenant scope, lifecycle state, and permission-context checks.** A valid UUID is not valid authorization evidence.
- **User-controlled URL, path, file, template, command, query, selector, prompt, or tool parameter is security-sensitive.** Validate destination, grammar, size, scheme, path containment, and safe logging before processing.
- **File intake validates content, not declarations.** Browser MIME type, extension, filename, archive path, object key, and client-declared size are untrusted.
- **Webhook and integration payloads are not trusted until authenticity, freshness, replay protection, schema, and idempotency expectations are checked.**
- **Validation errors must be actionable without exposing bypass details.** Return stable codes, safe field paths, and sensitivity-aware messages; never return exact private regexes, stack traces, parser internals, secrets, raw URLs, provider bodies, or tenant existence hints.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| New trust-boundary schema | New request, parser, import, CLI, config, event, webhook, or automation input. | Define field constraints, canonicalization, unknown-field policy, safe errors, and negative tests before implementation. | Source boundary, schema/validator path, field table, error contract, hostile-input cases. | `dto-schema-design`, `quality-test-gate` | Pure internal type assertions. |
| Existing validation evolution | Field constraints tightened, relaxed, renamed, made required, or moved between layers. | Preserve client compatibility and old behavior while fixing invalid input paths. | Old/new rule diff, consumer impact, rollout/rollback path, regression cases. | `version-compatibility`, `consumer-impact-analysis` | Silent breaking 400/422 change. |
| Identifier and object scope | Input contains user, tenant, account, owner, resource, role, status, permission, or classification fields. | Prevent IDOR, tenant spoofing, mass assignment, and client-controlled policy conditions. | Trusted source of subject/scope, ownership query, denied wrong-tenant test. | `permission-boundary-modeling`, `security-privacy-gate` | Role-only controller check. |
| URL, path, fetch, or execution selector | User input reaches server-side fetch, filesystem path, redirect, parser, renderer, shell, template, SQL/LDAP builder, or AI/tool call. | Canonicalize, constrain grammar/destination, fail closed, and redact diagnostics. | Allowlist, deny ranges/base path, timeout/size bounds, malicious payload tests. | `web-security`, `threat-modeling` | Regex-only validation after execution starts. |
| File upload or archive/import intake | Upload, attachment, direct-to-storage object, archive, CSV/XML/JSON import, or media processing changes. | Validate size, content signature, structure, storage key, scan/publish state, and tenant ownership. | Magic-byte/type rule, archive traversal rule, scan gate, malicious fixture result. | `file-storage-processing`, `security-privacy-gate` | Browser `Content-Type` or extension trust. |
| Webhook or external event payload | Signed/unsigned webhook, partner event, queue message, replayable callback, or cross-service payload. | Verify authenticity before parse/use; validate schema, freshness, replay, idempotency, and safe errors. | Signature algorithm, raw-body handling, timestamp/replay window, tamper tests. | `integration-change-builder`, `idempotency-retry-design` | Parsing payload before signature validation. |
| Validation error contract | Field violations, RFC 7807/9457 payload, safe echo policy, localization, or SDK behavior changes. | Make invalid-input handling client-actionable and non-leaky. | Field-path map, violation codes, safe rejected-value policy, negative examples. | `error-code-design`, `frontend-api-integration` | One generic "invalid input" or raw regex leak. |

# Industry Benchmarks

Anchor against OWASP ASVS V5 validation/sanitization, OWASP API Security API3/API4/API8, OWASP Top 10 A03 injection and A01 broken access control, CWE-20, CWE-22, CWE-79, CWE-89, CWE-434, CWE-918, CWE-915, RFC 7807/9457 problem details, JSON Schema/OpenAPI validation practice, strict schema libraries such as Zod and Pydantic, Bean Validation, OWASP File Upload, SSRF, XSS, and SQL Injection cheat sheets, and constant-time webhook signature verification patterns. Keep the body focused on routing, evidence, and output; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed layer responsibility, constraint taxonomy, parser/fetch/upload/webhook matrices, graph-memory-trajectory coupling, anti-patterns, and test mapping.

# Selection Rules

Select this capability when **trust-boundary validation design and enforcement evidence** are primary. Adjacent routing:

- Prefer `dto-schema-design` when field naming, null/default semantics, transfer schema source, generated clients, or DTO/domain mapping are primary.
- Prefer `web-security` when exploit-class review across XSS, CSRF, SSRF, injection, upload abuse, deserialization, redirects, or browser controls is primary.
- Prefer `permission-boundary-modeling` when the main decision is subject/resource/action/condition authorization and object-level enforcement.
- Prefer `error-code-design` when public error taxonomy, retryability, localization, or support diagnostics are primary.
- Prefer `form-validation-design` when frontend timing, field preservation, async validation UX, or accessibility feedback is primary.
- Prefer `integration-change-builder` when external partner protocol behavior, retries, reconciliation, credentials, or webhook operational ownership dominates.

# Risk Escalation Rules

Escalate when input can affect financial amounts, billing, permissions, roles, tenant scope, regulated data, files, executable paths, templates, queries, deserialization, server-side URL fetches, CI/CD or automation actions, AI/tool calls, configuration, webhooks, replayable events, or privileged support/admin workflows. Escalate when prior memory says validation exists but current source, callers, generated schemas, and tests have not been inspected.

# Proactive Professional Triggers

- **Signal:** validation is described as frontend-only, SDK-only, HTML attribute-only, API gateway-only, or "the client cannot send that." **Hidden risk:** direct API or alternate client bypass stores invalid or hostile data. **Required professional action:** require server-side trust-boundary validation and negative direct-call proof. **Route to:** `backend-change-builder`, `quality-test-gate`. **Evidence required:** server validator path and bypass test.
- **Signal:** handler spreads, auto-binds, deserializes, or passes raw request bodies into commands, ORM updates, jobs, prompts, or provider calls. **Hidden risk:** mass assignment, object-property authorization bypass, prompt/tool injection, or unsafe provider behavior. **Required professional action:** define strict DTO allowlist, unknown-field rejection, and mapping owner. **Route to:** `dto-schema-design`, `security-privacy-gate`. **Evidence required:** allowlisted mapper and denied unknown-field case.
- **Signal:** path, URL, redirect, filename, object key, archive entry, template, query, shell argument, selector, or AI/tool parameter comes from caller-controlled input. **Hidden risk:** SSRF, path traversal, open redirect, injection, RCE, prompt injection, or data exfiltration. **Required professional action:** canonicalize before use, constrain destination/grammar, fail closed, and redact diagnostics. **Route to:** `web-security`, `threat-modeling`. **Evidence required:** malicious-input test, deny-before-use proof, and safe log/error sample.
- **Signal:** request includes `user_id`, `tenant_id`, `owner_id`, `resource_id`, role, permission, status, classification, price, quota, or state transition fields. **Hidden risk:** IDOR, tenant spoofing, client-controlled policy, or business invariant bypass. **Required professional action:** derive authority from trusted server state and validate identifier ownership/scope. **Route to:** `permission-boundary-modeling`, `business-rule-extraction`. **Evidence required:** trusted source, ownership query, denied wrong-owner/tenant case.
- **Signal:** validation tightening changes required fields, enum values, length/range, unknown-field handling, parser strictness, or accepted file/payload types on an existing public path. **Hidden risk:** deployed clients, mobile apps, partners, fixtures, or replayed events break after release. **Required professional action:** classify compatibility and provide rollout or deprecation path. **Route to:** `version-compatibility`, `consumer-impact-analysis`. **Evidence required:** old/new rule diff, consumer inventory, compatibility tests or residual risk.
- **Signal:** a validation change lists field constraints but has no changed-validation-to-test map, validator command, artifact path, or freshness statement. **Hidden risk:** invalid, malformed, unauthorized, hostile, compatibility, or error-contract regressions remain untested while the contract looks complete. **Required professional action:** map every changed rule to a runnable validator, test, manual proof, or named residual risk before handoff. **Route to:** `quality-test-gate`, `validation-broker`. **Evidence required:** changed rule, validator/test name, exit code or not-run status, what evidence proves, what evidence does not prove, and residual-risk owner.
- **Signal:** memory, repository graph, generated docs, or prior test reports claim validation coverage without current source inspection. **Hidden risk:** stale validators, missing new entry points, or generated-client drift. **Required professional action:** confirm current validator, caller graph, schema source, tests, and report freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limit.

# Critical Details

Validation precision failures usually arise from boundary confusion:

- A field can be syntactically valid but unauthorized for the caller, tenant, lifecycle state, or object relationship.
- Encoding and parser ambiguity defeat late blocklists; validate the canonical representation before security decisions.
- Generated schemas and SDK types do not prove runtime enforcement unless the server boundary rejects invalid direct calls.
- Unknown-field tolerance is a compatibility decision, not a default. Tolerating unknown request fields must not map them to domain mutations.
- "Sanitize" is not one operation. Validation, canonicalization, output encoding, parameterization, and authorization each protect different boundaries.
- Error responses, logs, metrics, and traces are output boundaries; rejected values can still leak secrets or attack payloads.
- Project memory and repository graph are evidence leads. Current source, current callers, current validators, and current tests decide the validation contract.

### Anti-examples

| Anti-pattern | Failure | Required correction |
| --- | --- | --- |
| Frontend validates email; API accepts direct invalid POST | Downstream data corruption and bounce loops. | Server-side schema and negative direct-call test. |
| `Model.update(req.body)` | Mass assignment to role, price, tenant, or status fields. | Strict DTO, allowlisted mapper, unknown-field rejection. |
| URL regex before fetch only checks prefix | SSRF via redirects, DNS rebinding, private ranges, or userinfo tricks. | Parse, resolve, allowlist, deny private/link-local/metadata, revalidate redirects. |
| File accepts `.jpg` extension and browser MIME | Type spoof, malware, or executable upload. | Size cap, magic bytes, storage isolation, scan-before-publish. |
| Webhook parses JSON before signature check | Forged event can trigger side effects or parser abuse. | Verify raw body signature, freshness, replay, then parse. |
| Error returns exact regex or raw parser message | Attackers learn bypass boundary or internals. | Stable violation codes and sensitivity-aware messages. |

# Failure Modes

- **Frontend-only bypass:** direct API calls bypass frontend validation and store invalid data because the server boundary lacks the same rule.
- **Raw binding / mass assignment:** raw request bodies map into commands, ORM models, jobs, prompts, or provider calls and mutate privileged fields.
- **Canonicalization gap:** encoded, Unicode, or path-normalized payloads pass late blocklists and trigger injection, traversal, SSRF, or unsafe parser behavior.
- **Identifier authority gap:** valid-looking identifiers reference another tenant, owner, deleted resource, forbidden state, or invisible object.
- **Unsafe file intake:** file uploads trust extension, browser MIME, filename, archive path, or client size and publish unsafe content.
- **Webhook parse-before-verify:** webhooks are parsed or processed before signature, freshness, replay, schema, or idempotency checks.
- **Compatibility break:** validation tightening breaks deployed clients, mobile apps, generated SDKs, partner payloads, imports, or replayed events without a rollout path.
- **Leaky diagnostics:** error responses, logs, metrics, or traces leak regexes, stack traces, raw URLs, secrets, tenant existence, or provider/parser internals.
- **Stale graph or memory claim:** project memory says validation already exists, but current repository graph exposes a new route, job, import, or generated client path without coverage.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, non-negotiable rules, triggers, and output requirements. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete validator, field table, parser, upload, webhook, URL/fetch rule, identifier guard, or validation test plan. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when layer responsibility, constraint taxonomy, file/upload rules, SSRF/path/canonicalization, webhook authenticity, graph-memory-trajectory evidence, compatibility, or changed-validation-to-test mapping needs deeper detail. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on boundaries inspected, graph/memory/execution freshness, tool permission boundaries, validation evidence quality, what evidence proves, what evidence does not prove, or residual risk ownership. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or metadata-only edits with no validation decision.

# Output Contract

Return an input validation contract with:

- `mode_selected` (new trust-boundary schema, existing validation evolution, identifier/object scope, URL/path/fetch/execution selector, file/import intake, webhook/event payload, validation error contract)
- `boundaries_inspected` (routes, handlers, DTOs/schemas, validators, parsers, mappers, services, repositories, files/uploads, webhook adapters, jobs/events, generated clients/specs, tests, logs/errors, registry/project memory, and skipped boundaries with reason)
- `source_evidence` (current files, caller graph, schema source, generated artifacts, validators, reports, test fixtures, or telemetry inspected)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified claims about existing validation, callers, contracts, prior failures, generated artifacts, and test freshness)
- `input_sources` (body, query, path, headers, cookies, files, webhooks, events, imports, CLI/config, URL/fetch, automation/tool parameters, trust level, and actor)
- `schema_constraints` (per field: type, required/optional, nullable/absent/empty semantics when relevant, length/size/range, enum, pattern/grammar, format, array/object bounds, cross-field rules)
- `canonicalization_sequence` (decode, Unicode normalization, trimming, path resolution, URL parsing/resolution, case folding, timezone/currency normalization, and when the raw value is still needed)
- `unknown_field_policy` (reject, tolerate for forward compatibility, or strip at boundary; rationale and safety constraints)
- `identifier_and_authority_checks` (field, trusted source, existence, ownership, tenant scope, permission, lifecycle state, query/filter location)
- `state_and_business_guards` (per status-changing field or command: invariant, current state, permitted transition, enforcement layer)
- `url_path_file_controls` (scheme/host/port/address allowlist, private/metadata denial, redirect revalidation, base-path containment, filename/storage key, MIME/magic bytes, size, archive traversal, scan gate, timeout/response bounds)
- `webhook_event_controls` (raw-body signature, algorithm, timestamp/freshness, replay protection, schema version, idempotency key/event id, parse-after-verify rule)
- `error_contract` (status/code/type, field path, safe message, safe rejected-value echo policy, redaction for errors/logs/metrics/traces, localization or SDK impact)
- `changed_validation_to_test_map` (each field, parser, canonicalization step, unknown-field policy, identifier check, upload rule, webhook rule, error shape, compatibility decision, and security constraint mapped to validator/test/manual proof or residual risk)
- `reuse_and_placement_rationale` (existing schema, validator library, mapper, service boundary, policy module, parser, helper, fixture, and reference files reused or rejected; why no client-only, duplicated, or speculative abstraction was introduced)
- `behavior_preservation` (old valid inputs, old clients, old generated artifacts, old error semantics, old replayed events, old storage/import records, and rollback behavior preserved or intentionally migrated)
- `validation_evidence` (commands, validators, reports, fixtures, exit codes, artifact names, manual verification, freshness after final edit, or not-verified disclosure)
- `handoff_boundaries` (DTO schema, error catalog, object authorization, web exploit review, file lifecycle, integration/retry, release/docs)
- `evidence_limits` (unknown clients, unqueried telemetry, uninspected generated artifacts, unavailable production payloads, stale memory, untested malicious cases, or residual risk owner)

# Evidence Contract

Close an input-validation design only when these answers are concrete:

- **Boundary basis:** selected mode, trust boundary, actor, input source, parser/validator owner, and security or compatibility risk class.
- **Current-source inspection:** paths for routes, validators, DTOs/schemas, parsers, mappers, services, repositories, adapters, jobs/events, generated artifacts, tests, and prior reports checked or explicitly skipped.
- **Placement rationale:** why validation belongs at the chosen boundary, and why client-only, gateway-only, late sanitizer-only, duplicate helper, raw binding, or speculative shared abstraction was rejected.
- **Validation proof:** each changed rule maps to valid, invalid, boundary, malformed, canonicalization, unauthorized, unknown-field, malicious payload, file/webhook/fetch, compatibility, and error-contract evidence where applicable.
- **Behavior preservation:** old valid inputs, public clients, generated clients, replayed events, imports, error semantics, and rollback stay valid or have a migration path.
- **Evidence limits and residual risk:** unknown consumers, untested parsers, unavailable telemetry, stale project memory, unverified generated clients, or manual security review gaps have owner and next gate.

The final handoff must name the boundaries inspected, the validator/test/report artifacts used, what evidence proves, what evidence does not prove, residual risk, and the next handoff owner; a field-rule table without that evidence contract is not closure.

# Benchmark Coverage

This capability covers server-side trust-boundary validation, strict schema and allowlisted mapping, canonicalization ordering, unknown-field policy, identifier ownership and tenant scope, file/upload/import intake, URL/path/fetch controls, webhook authenticity and replay checks, safe validation errors, compatibility classification, graph-memory-trajectory verification, and changed-validation-to-test mapping. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed matrices and implementation patterns.

# Routing Coverage

Routes from `security-privacy-gate`, `backend-change-builder`, `frontend-change-builder`, `data-api-contract-changer`, `api-contract-design`, `dto-schema-design`, `error-code-design`, `form-validation-design`, `file-storage-processing`, `integration-change-builder`, `web-security`, `permission-boundary-modeling`, `contract-testing`, and `quality-test-gate` should arrive here when trust-boundary validation evidence is primary. Route away when endpoint semantics, DTO field modeling, public error taxonomy, authorization policy, exploit-class threat review, file lifecycle, retry/reconciliation, or release approval is primary.

# Quality Gate

The validation contract is complete only when:

1. Mode, inspected boundaries, source evidence, graph-memory-trajectory judgment, and evidence limits are recorded.
2. Every input source and actor has a trust level, parser/validator owner, and server-side enforcement point.
3. Every accepted field has type, required/optional status, size/length/range, format/grammar, enum/allowlist, array/object bounds, and cross-field rules where applicable.
4. Canonicalization order is defined before security-sensitive checks.
5. Unknown request fields are rejected or tolerated only with explicit compatibility and non-mapping rationale.
6. Identifiers validate existence, ownership, tenant scope, permission context, and lifecycle state using trusted server-side data.
7. State-changing and business-significant inputs have invariant and transition guards at the service/domain boundary.
8. URL, path, fetch, redirect, template, query, selector, command, and AI/tool inputs have destination or grammar allowlists, fail-closed behavior, and redacted diagnostics.
9. File/import/archive inputs validate size, content signature, structure, storage key/path, scan/publish state, and tenant ownership.
10. Webhooks/events verify raw-body authenticity, freshness, replay/idempotency, schema, and parse-after-verify ordering.
11. Validation errors use stable codes/field paths and do not leak regexes, internals, secrets, raw URLs, provider bodies, or tenant existence.
12. Tightened validation is compatibility-classified with consumer, generated-client, fixture, replay, and rollback impact.
13. Changed validation-to-test map covers valid, invalid, boundary, malformed, hostile, unauthorized, unknown-field, file/webhook/fetch, and error-contract cases or names residual risk.
14. Reuse and placement rationale identifies existing validators/schemas/helpers/tests and rejects client-only, late sanitizer-only, raw-binding, or speculative shared paths.
15. Handoff boundaries and residual-risk owner are explicit.

# Used By

- security-privacy-gate
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `dto-schema-design` for transfer schema and mapper semantics; `error-code-design` for public validation error taxonomy; `permission-boundary-modeling` for object-level authorization; `web-security` for exploit-class review; `file-storage-processing` for file lifecycle and storage controls; `integration-change-builder` for webhook/partner protocol operation; `quality-test-gate` for coverage sufficiency; and `delivery-release-gate` when validation tightening needs rollout, rollback, or release approval.

# Completion Criteria

The capability is complete when every trust-boundary input has server-side validation, canonicalization, unknown-field policy, authority checks, safe errors, behavior-preservation analysis, changed-validation-to-test mapping, graph-memory-trajectory evidence, handoff boundaries, and residual-risk owner, with no validation concern deferred to client behavior alone.
