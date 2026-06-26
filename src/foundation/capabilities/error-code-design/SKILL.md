---
name: error-code-design
description: Designs stable, actionable, product-grade error responses and prevents raw internal exceptions from becoming client contracts.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "28"
changeforge_version: 0.1.0
---

# Mission

Design stable, safe, actionable, and diagnosable client-visible error contracts so callers can branch on machine-readable codes, users receive safe recovery guidance, support can trace failures through correlation ids, and raw internal exceptions, provider bodies, stack traces, SQL details, secrets, tenant existence signals, and diagnostic-only messages never become public API behavior.

# When To Use

Use this capability when a change defines or changes API error response shapes, error code taxonomies, HTTP/gRPC status mappings, validation problem details, retryability semantics, rate-limit or dependency-failure responses, authorization 403/404 posture, localization keys, support diagnostics, correlation ids, public error catalogs, SDK client behavior, or controller/service/adapter error translation that affects clients.

# Do Not Use When

Do not use this capability to expose raw exceptions as error bodies; that is prohibited. Do not use it as the primary owner for internal exception architecture, log field design, retry implementation, or cross-layer failure taxonomy. Route to `failure-contract-design` for typed failure semantics across layers, `logging-error-handling` for diagnostic log design, `idempotency-retry-design` for retry mechanics, `api-contract-design` for full operation contracts, and `security-privacy-gate` when error detail leakage is the primary risk.

# Stage Fit

Use during planning when new error semantics or an error catalog are introduced; during coding and review when controllers, adapters, validators, generated clients, or SDKs map errors; during testing when negative paths, retryability, trace ids, and raw-exception suppression need proof; and during release when published codes, deprecations, localization, or consumer compatibility are affected. Hand off when the unresolved decision is operation shape, DTO schema, cross-layer failure typing, log schema, retry implementation, release approval, or security incident response.

# Non-Negotiable Rules

- **Error codes are compatibility contracts.** Published machine-readable codes, `type` URIs, and retry semantics must remain stable unless a breaking-change path is declared.
- **Never return raw internals.** Stack traces, exception class names, SQL/ORM/database messages, provider bodies, file paths, secrets, tokens, tenant ids, and internal policy names must be translated before reaching clients.
- **Use correct transport semantics.** HTTP errors use appropriate 4xx/5xx status codes; gRPC errors use canonical `google.rpc.Code`; never return `200 OK` with an error body for failures.
- **Branch on codes, not messages.** User messages can be localized or refined. Client logic must use stable `code` or RFC 7807/9457 `type`.
- **Retryability is declared.** Every code states not-retryable, retryable-after-delay, retryable-idempotent-only, or conditionally retryable, with `Retry-After` or backoff guidance where applicable.
- **Non-idempotent retryable operations need idempotency guidance.** POST/write failures that can be retried must state whether an idempotency key, replay lookup, or state query is required.
- **Separate user-safe message from operator diagnostics.** Client response says what the user/client can do; logs preserve cause and provider detail safely, linked by trace/request id.
- **Authorization posture must avoid enumeration.** Use 404 instead of 403 when confirming resource existence is sensitive; document the chosen posture per resource class.
- **Validation errors need structured field violations.** Field paths, constraints, safe rejected values, and stable violation codes are required when clients need to highlight or repair input.
- **Correlation ids are mandatory.** Error responses include request/trace id in body and/or headers, and server diagnostics can be found with the same id.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| New error catalog | New service, endpoint family, SDK surface, or domain error taxonomy. | Stable code namespace, transport mapping, user action, retryability, catalog governance. | Existing conventions, code table, examples, publication owner, tests. | `api-contract-design`, `contract-testing` | Per-endpoint full contract unless shape changes. |
| Existing error semantics change | Code renamed, status changed, message meaning changed, retryability changed, or clients branch on errors. | Compatibility and old-client behavior. | Old/new code map, consumer impact, deprecation/version decision. | `version-compatibility`, `consumer-impact-analysis` | Silent semantic replacement. |
| Validation problem detail | Request validation, field violations, RFC 7807/9457 payload, or invalid DTO behavior. | Client-actionable field repair without leaking schema internals. | Constraint table, violation schema, safe echo policy, negative tests. | `dto-schema-design`, `input-validation`, `quality-test-gate` | Generic "invalid input". |
| Security-sensitive error | Authn/authz, tenant/object access, PII, secret, provider, database, or AI/tool error detail. | Non-enumerating posture and safe disclosure. | Existence-leak analysis, redaction rules, denied-case tests or review. | `security-privacy-gate`, `permission-boundary-modeling` | Raw provider/internal messages. |
| Retry and capacity error | 408, 409, 429, 502, 503, 504, timeout, rate limit, dependency, or circuit-breaker error. | Retryability, idempotency, backoff, and observability semantics. | Retry matrix, `Retry-After`, idempotency requirement, metric label policy. | `idempotency-retry-design`, `reliability-observability-gate` | Retry guidance without duplicate-side-effect proof. |
| Cross-layer translation | Controller/service/repository/adapter/job errors collapse or leak across boundaries. | Safe public mapping while preserving diagnostic cause. | Boundary translation map, internal cause preservation, negative tests. | `failure-contract-design`, `logging-error-handling` | Designing public codes without source failure taxonomy. |
| Localization and support | User-facing copy, message keys, support workflows, or public docs change. | Stable code with localizable message and traceable support path. | Message key, locale fallback, support runbook link, catalog publication. | `change-documentation-gate`, `frontend-api-integration` | Clients branching on localized text. |

# Industry Benchmarks

Anchor against RFC 7807/9457 Problem Details, RFC 9110 HTTP semantics, gRPC canonical status codes and detail types, OWASP secure error handling, OWASP API8 and CWE-209 for information exposure, W3C TraceContext for correlation, and consumer-driven contract testing for client behavior. Load [references/industry-benchmarks.md](references/industry-benchmarks.md) for detailed status-code, retryability, taxonomy, graph-memory-trajectory, and validation matrices.

# Selection Rules

Select this capability when **client-visible error taxonomy and remediation behavior** are primary. Adjacent routing:

- Prefer `api-contract-design` when the whole operation contract, auth, request, response, pagination, or idempotency surface is primary.
- Prefer `dto-schema-design` when the main decision is field-level error payload shape or validation DTO structure.
- Prefer `failure-contract-design` when retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, or partial failures must be typed across layers.
- Prefer `logging-error-handling` when log schema, redaction, and diagnostic fields are primary.
- Prefer `input-validation` when trust-boundary validation rules are primary.
- Prefer `version-compatibility` when published code semantics may break deployed clients.
- Prefer `security-privacy-gate` when the error may leak auth state, tenant existence, secrets, PII, provider internals, or prompt/tool details.

# Risk Escalation Rules

Escalate when an error response can reveal account/resource existence, tenant boundaries, authentication state, payment or financial state, healthcare/regulated data, secrets/tokens/private keys, provider internals, SQL/schema names, AI prompt/tool content, or internal policy names. Escalate when retryable write errors can duplicate side effects, when a public/mobile/partner SDK branches on codes, when generated clients need regeneration, or when project memory claims the catalog is stable without current-source and consumer evidence.

# Proactive Professional Triggers

- **Signal:** A handler returns string errors, raw exception messages, provider bodies, stack traces, SQL text, or framework default errors. **Hidden risk:** information exposure and unstable client contract. **Required professional action:** map to safe catalog code and diagnostic log path. **Route to:** `security-privacy-gate`, `logging-error-handling`. **Evidence required:** raw-detail suppression test or review and trace id linkage.
- **Signal:** Error code, HTTP status, gRPC code, retryability, or validation message changes on an existing API. **Hidden risk:** deployed clients classify failures incorrectly or retry unsafe operations. **Required professional action:** classify compatibility and consumer impact. **Route to:** `version-compatibility`, `contract-testing`. **Evidence required:** old/new matrix, affected consumers, negative/contract tests.
- **Signal:** 401, 403, 404, permission, tenant, user lookup, or resource lookup behavior is generic or inconsistent. **Hidden risk:** user enumeration, tenant leakage, or broken recovery UX. **Required professional action:** define auth posture and safe response per resource class. **Route to:** `security-privacy-gate`, `permission-boundary-modeling`. **Evidence required:** existence-leak decision and denied-path proof.
- **Signal:** 429, 503, gateway, timeout, or dependency errors have no retry policy. **Hidden risk:** retry storm, duplicate side effect, or clients giving up incorrectly. **Required professional action:** define retryability, `Retry-After`, idempotency requirement, and metric labels. **Route to:** `idempotency-retry-design`, `reliability-observability-gate`. **Evidence required:** retry/client behavior matrix and duplicate-side-effect residual risk.
- **Signal:** Validation returns one generic error or exposes exact regex/internal field names. **Hidden risk:** clients cannot repair input or attackers learn bypass details. **Required professional action:** define field violations and safe echo policy. **Route to:** `input-validation`, `dto-schema-design`. **Evidence required:** field-path map and invalid-input examples.
- **Signal:** Repository, adapter, service, or queue errors collapse into `INTERNAL_ERROR`. **Hidden risk:** retryable, permission, conflict, timeout, and dependency failures become indistinguishable. **Required professional action:** define boundary translation before public error mapping. **Route to:** `failure-contract-design`. **Evidence required:** failure taxonomy and controller/adapter translation map.
- **Signal:** Memory, generated docs, or repository graph says an error catalog already exists. **Hidden risk:** stale code table, generated SDK drift, or hidden consumer branching. **Required professional action:** confirm current source, generated artifacts, callers, and validation freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected prior claim, freshness limit.

# Critical Details

Error responses are security, compatibility, reliability, and support surfaces:

- **200 OK with an error body** breaks clients, caches, load balancers, error-rate metrics, and retry logic.
- **Message-based branching** breaks when wording is localized, shortened, or clarified.
- **403 vs 404 is a security decision** when resource existence is sensitive.
- **Retryable without guidance** creates thundering herds or silent abandonment; 429/503 need `Retry-After` or explicit backoff.
- **Retryable writes without idempotency** can duplicate payments, orders, or state transitions.
- **Provider error leakage** can reveal secrets, account identifiers, query fragments, versions, or internal topology.
- **Trace id absence** turns every support ticket into a log search problem and weakens incident diagnosis.
- **High-cardinality error metrics** should use catalog code/status/category, not raw message, resource id, user id, or provider text.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `return 200` with `{ "error": "User not found" }` | HTTP semantics, caches, metrics, and client libraries misclassify failure. |
| Stack trace or SQL error in response | CWE-209 information exposure and exploit guidance. |
| Client branches on `message` text | Localization or copy edit breaks logic. |
| `403` for every protected missing resource | Confirms resource existence and enables enumeration. |
| `503` or `429` without retry guidance | Retry storm or inconsistent client behavior. |
| Forwarding provider error JSON | Provider internals, tokens, account ids, or API versions leak. |
| Validation error `"Invalid input"` only | Client cannot highlight or repair the failing field. |

# Failure Modes

- Published code is renamed and SDK clients silently route the wrong UI state.
- Raw exception body exposes framework version, file path, provider secret, or SQL table name.
- Unauthorized lookup uses 403 while missing resource uses 404, allowing enumeration.
- Payment creation returns transient failure; client retries without idempotency and creates duplicates.
- Validation errors lack field paths, so forms cannot preserve input or focus the failing field.
- Support receives an error screenshot without request id and cannot correlate logs.
- Metric labels use raw provider messages and overwhelm telemetry cardinality.
- Project memory says "catalog exists", but current generated clients or OpenAPI examples still expose stale codes.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, ownership, and output rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete error catalog, status map, validation problem detail, retryability matrix, or authorization posture. Load [references/industry-benchmarks.md](references/industry-benchmarks.md) for detailed HTTP/gRPC status decisions, RFC 7807/9457 examples, retry trees, graph-memory-trajectory coupling, and validation matrices. Use [examples/example-output.md](examples/example-output.md) when the expected output shape is unclear. Do not load references for pure routing or metadata-only edits with no error contract decision.

# Output Contract

Return an error catalog with:

- `mode_selected` (new catalog / existing semantics change / validation problem detail / security-sensitive error / retry and capacity error / cross-layer translation / localization and support)
- `boundaries_inspected` (controllers, validators, service/domain errors, repositories, adapters/providers, SDKs, generated specs, logs, metrics, support docs, consumers, tests, and skipped boundaries with reason)
- `source_evidence` (current files, generated artifacts, callers, catalog entries, tests, or telemetry inspected)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for prior catalog claims, consumer lists, generated docs, old validation, and previous repair paths)
- `error_surface` (API, gRPC, GraphQL, webhook, SDK, CLI, job, event, or UI-facing backend response)
- `catalog_entries` (code/type URI, category, transport status, user-safe message key, client action, retryability, idempotency requirement, authorization posture, correlation behavior, field violations if applicable)
- `transport_mapping` (HTTP status, gRPC code/detail type, GraphQL extension, webhook/SDK mapping)
- `diagnostic_separation` (what appears in response, what appears only in logs, redaction rule, trace/request id behavior)
- `retryability_matrix` (retryable/non-retryable/conditional, `Retry-After`, backoff, duplicate-side-effect guard)
- `validation_error_shape` (field path, violation code, safe rejected value policy, localization key)
- `compatibility_classification` (new, additive, semantic change, breaking rename/removal/status/retryability change, deprecation/version path)
- `consumer_behavior` (client branch rule, SDK/generated-client impact, frontend recovery state, support workflow)
- `observability_contract` (metric labels limited to stable code/category/status, trace/log linkage, alert ownership when applicable)
- `tests_or_validation` (no raw detail, stable code branch, status mapping, retry guidance, idempotency, field violations, denied posture, trace id, provider leakage)
- `changed_error_to_validation_map` (each code/status/message/retry/authorization/validation/provider mapping to proof or residual risk)
- `reuse_and_placement_rationale` (existing catalog, problem-detail type namespace, translation boundary, and rejected raw/internal or duplicate taxonomy path)
- `behavior_preservation` (old codes, status semantics, retry behavior, localization keys, SDK behavior, and support workflow preserved or migrated)
- `handoff_boundaries` (API contract, DTO validation payload, failure contract, logging, security/privacy, reliability/observability, contract testing, docs)
- `evidence_limits` (unknown consumers, untested SDKs, missing telemetry, unverified provider paths, production log/query gaps, stale generated docs)

# Evidence Contract

Close an error-code design only when these answers are concrete:

- **Basis:** selected mode, standards used, and compatibility/security/reliability risk class.
- **Boundaries inspected:** client-visible surfaces, translation boundaries, generated specs/SDKs, logs/metrics, consumers, tests, and prior memory/graph claims checked or explicitly skipped.
- **Placement rationale:** why the catalog, translation map, validation payload, retry guidance, and diagnostic detail belong at the selected boundary.
- **Validation evidence:** validator/test/report commands, negative cases, generated diffs, or not-verified disclosure with freshness after the final edit.
- **Behavior preservation:** old codes, status, retryability, support workflow, localization behavior, and SDK/client branching preserved or intentionally migrated.
- **Evidence limits and residual risk:** unknown consumers, provider paths not exercised, telemetry not queried, SDK languages not rebuilt, or auth existence posture not proven, with owner.

# Benchmark Coverage

This capability covers stable machine-readable error taxonomy, RFC 7807/9457 problem details, HTTP/gRPC status discipline, safe user messages, raw-detail suppression, authorization existence posture, validation field violations, retryability and idempotency guidance, trace correlation, localization, catalog governance, compatibility classification, graph/memory/trajectory verification, and error-to-validation mapping while keeping deep matrices in references.

# Routing Coverage

Routes from `data-api-contract-changer`, `backend-change-builder`, `frontend-change-builder`, `api-contract-design`, `dto-schema-design`, `form-validation-design`, `frontend-api-integration`, `failure-contract-design`, `logging-error-handling`, `version-compatibility`, `contract-testing`, `security-privacy-gate`, and `reliability-observability-gate` should arrive here when client-visible error semantics are primary. Route away when endpoint shape, field schema, internal failure typing, diagnostic log schema, retry implementation, security incident response, or release approval is primary.

# Quality Gate

The error catalog is complete only when:

1. Mode, inspected boundaries, source evidence, graph-memory-trajectory judgment, and evidence limits are recorded.
2. All public codes or `type` URIs are stable, namespaced, documented, and not human-message strings.
3. HTTP/gRPC/GraphQL/SDK transport mapping is semantically correct; no failure returns success status.
4. User-safe messages are localizable and contain no internal detail, secrets, PII, provider text, SQL, stack traces, or policy names.
5. Developer diagnostics stay in logs with safe redaction and trace/request id linkage.
6. Authorization posture is documented per resource class, including 404-vs-403 existence-leak decisions.
7. Validation errors include field-level violations where clients need repair guidance.
8. Retryability, `Retry-After` or backoff, and idempotency requirements are explicit.
9. Error metric labels use bounded catalog values, not raw messages or identifiers.
10. Compatibility is classified for changed codes, statuses, retry semantics, messages used by clients, and generated SDK/docs.
11. Client behavior and support workflow are mapped to codes, not message text.
12. Negative validation covers raw-detail suppression, provider leakage, stable-code branching, status mapping, trace id, field violations, retry guidance, and denied posture or names residual risk.
13. Reuse and placement rationale rejects duplicate taxonomies, controller-local strings, raw framework errors, and speculative wrappers.

# Used By

- data-api-contract-changer
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `api-contract-design` for operation-level contract; `dto-schema-design` for validation error response schema; `failure-contract-design` for cross-layer failure taxonomy; `logging-error-handling` for diagnostic logging; `security-privacy-gate` for detail leakage and enumeration risk; `reliability-observability-gate` or `observability` for trace, metric, and alert semantics; `version-compatibility` for published-code changes; and `contract-testing` for executable client behavior.

# Completion Criteria

The capability is complete when every client-visible error scenario has a stable code/type URI, correct transport status, safe localizable user message, explicit retryability and idempotency guidance, non-enumerating authorization posture, trace-linked diagnostics, validation field detail when needed, compatibility classification, negative validation evidence, and residual-risk owner, with no raw internal detail reachable from any response path.
