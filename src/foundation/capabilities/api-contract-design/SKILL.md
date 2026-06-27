---
name: api-contract-design
description: Designs API contracts with request, response, errors, authentication, pagination, idempotency, compatibility, and describable HTTP semantics.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "26"
changeforge_version: 0.1.0
---

# Mission

Design API contracts that clients can implement safely under retries, version skew, partial failure, and adversarial input — through explicit requests, responses, errors, authentication, pagination, idempotency, concurrency control, and compatibility rules.

# When To Use

Use this capability when a change adds, removes, renames, versions, splits, merges, or alters: endpoints, methods, resources, payloads, status codes, error models, auth requirements, pagination, filtering, sorting, field semantics, rate limits, idempotency keys, webhook deliveries, long-running operation patterns, or content negotiation.

# Do Not Use When

Do not use this capability to expose internal functions, ORM entities, database tables, or domain aggregates directly without a stable contract boundary. Do not use it as a substitute for `dto-schema-design` (field-level validation), `error-code-design` (error taxonomy), `version-compatibility` (rollout across clients), or `authentication-authorization` (policy implementation).

# Stage Fit

Use during planning when a client-visible operation, method, endpoint, RPC, event callback, webhook, pagination model, idempotency behavior, error surface, auth requirement, or versioning path is introduced or changed. Use during implementation and review when controllers, specs, generated clients, SDKs, examples, docs, route handlers, or compatibility bridges must stay aligned. Use during testing and release when contract validation, consumer compatibility, generated artifact freshness, deprecation, security posture, or rollback behavior needs proof. Treat repository graph, project memory, generated docs, and prior validation as selectors only until current source/spec files, consumers, generated artifacts, and validation outcomes confirm or reject them.

At each coding, debugging, code-review, refactoring, testing, and release stage, handoff only after the changed contract behavior, skipped surfaces, validation evidence, and residual consumer risk are explicit.

# Non-Negotiable Rules

- Define request shape, response shape, status codes, error model, and auth/authorization requirements explicitly — defaults are not a contract.
- Define pagination, filtering, sorting, and partial response rules for any collection endpoint; never return unbounded lists.
- Define idempotency for every create, retryable, or side-effecting operation; document key scope, retention window, and replay semantics.
- Define compatibility expectations and a versioning/deprecation path; breaking changes require a migration plan before merge.
- HTTP APIs must be describable through OpenAPI ≥ 3.0 (or AsyncAPI for event APIs, gRPC `.proto` for gRPC, GraphQL SDL for GraphQL). Contract-first, not code-first reverse-derivation.
- Use stable, language-agnostic identifiers (UUID/ULID/opaque cursor), never database row ids in public contracts unless the resource is the database row by design.
- Return resource representations, not actions on internals; commands map to resources or RPC-style verbs explicitly chosen.
- Current-source evidence is required: spec files, handlers/controllers, generated clients, docs/examples, known consumers, tests, project memory or ADR freshness, and validation status must be cited or explicitly marked unavailable.
- Time values are RFC 3339 UTC with explicit offset; monetary values use ISO 4217 currency + minor-unit integer (never floats).
- Rate-limit responses (`429`) and authentication failures (`401`/`403`) must distinguish "missing", "invalid", "expired", "insufficient scope", and "rate limited" — never collapse.
- Webhooks/callbacks require signed payloads, replay protection, retry policy, and timeout contract.

# Industry Benchmarks

Anchor against: **OpenAPI 3.1 / JSON Schema 2020-12**, **AsyncAPI 2.6+** for event APIs, **gRPC + Protobuf 3** for low-latency internal RPC, **GraphQL** spec (October 2021) + Relay cursor connection spec, **RFC 9110/9111/9112** (HTTP semantics, caching, syntax), **RFC 7807 / 9457 Problem Details for HTTP APIs** (error model), **RFC 5988 / 8288 Web Linking** (HATEOAS where applicable), **RFC 7234** caching, **RFC 6585** additional status codes (`429`), **RFC 7231 §4.2** safe/idempotent methods, **RFC 6749 / 6750 OAuth 2.0**, **RFC 7519 JWT** (when chosen), **OWASP API Security Top 10 (2023)**, **Google AIPs (aip.dev)**, **Microsoft REST API Guidelines**, **Zalando RESTful API Guidelines**, **PayPal API Style Guide**, **Stripe API design** (resource modeling, idempotency-key header, expandable fields, pagination), **Consumer-Driven Contracts (Pact)**, **JSON:API** spec where applicable. For SLO/error budgets follow Google SRE Workbook.

Keep the default body focused on contract decisions. For detailed style, method, status-code, and versioning matrices, load the API style and semantics deep reference when style choice, retry semantics, status-code discipline, or compatibility class is part of the work.

# Selection Rules

Select this capability when **client-visible API behavior** is the primary decision. Adjacent routing:

- Prefer `dto-schema-design` when field-level serialization, validation rules, defaults, and nullability dominate.
- Prefer `error-code-design` when the error taxonomy and client remediation guidance are the main work.
- Prefer `version-compatibility` when rollout across old and new clients is the dominant risk.
- Prefer `event-driven-architecture` or `message-queue-design` for async producer/consumer topology.
- Prefer `authentication-authorization` for policy modeling and enforcement.
- Prefer `idempotency-retry-design` when duplicate side effects are the headline risk.
- Use **with** `frontend-api-integration` to ensure the contract is consumable, not just specifiable.

Selection must record the lifecycle stage, why sibling API/data capabilities were skipped, the evidence required for handoff, and whether the next gate is DTO/schema, error taxonomy, compatibility, contract testing, release, security, or implementation.

# Proactive Professional Triggers

- **Signal:** An existing endpoint, method, path, status code, error shape, auth requirement, pagination behavior, idempotency rule, filter, sort, or response semantics changes. **Hidden risk:** deployed clients, generated SDKs, caches, retries, and observability depend on the old behavior. **Required professional action:** classify compatibility, identify consumers, and choose version/bridge/deprecation or prove additive safety. **Route to:** `consumer-impact-analysis`, `version-compatibility`, `contract-testing`. **Evidence required:** old/new contract diff, consumer inventory, generated-client impact, contract/validator result.
- **Signal:** A request/response payload field, enum, null/default rule, validation constraint, example, or generated model changes. **Hidden risk:** field-level schema drift is hidden inside operation design. **Required professional action:** hand field semantics to DTO/schema design and map generated artifacts. **Route to:** `dto-schema-design`, `input-validation`, `quality-test-gate`. **Evidence required:** schema diff, examples, validation behavior, generated-client freshness.
- **Signal:** Error behavior uses raw strings, `200` with an error body, collapsed 401/403/404 posture, retry ambiguity, or inconsistent RFC 7807/9457 problem detail. **Hidden risk:** clients branch incorrectly, sensitive details leak, and retry behavior becomes unsafe. **Required professional action:** define stable error taxonomy, auth posture, retryability, and negative contract tests. **Route to:** `error-code-design`, `security-privacy-gate`, `failure-contract-design`. **Evidence required:** error matrix, denied-path policy, negative examples, contract proof.
- **Signal:** A write, create, webhook, callback, async operation, retryable POST/PATCH, or queue-facing API lacks idempotency and replay semantics. **Hidden risk:** duplicate side effects or lost work under retry and partial failure. **Required professional action:** define idempotency key scope, retention, replay, conflict, timeout, retry, and DLQ/callback behavior. **Route to:** `idempotency-retry-design`, `message-queue-design`, `integration-change-builder`. **Evidence required:** key scope, retention window, replay/conflict examples, duplicate-delivery validation.
- **Signal:** Repository graph, project memory, generated docs, prior context, or old validation claims the API contract or consumer list is current. **Hidden risk:** stale generated specs, hidden consumers, or validation predating edits become false completion evidence. **Required professional action:** reconcile against current source/specs, consumers, generated artifacts, and execution order. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected claims, freshness limit, rerun or not-verified status.
- **Signal:** Contract is public, partner/mobile-facing, permission-sensitive, PII/financial/regulated, high-volume, or changes auth scopes. **Hidden risk:** compatibility, privacy, abuse, traffic, and rollback obligations exceed local API shape. **Required professional action:** escalate security, release, reliability, and documentation gates with explicit skipped-surface rationale. **Route to:** `security-privacy-gate`, `delivery-release-gate`, `reliability-observability-gate`, `change-documentation-gate`. **Evidence required:** data classification, auth scope matrix, rollout/rollback plan, SLO/rate-limit impact.

# Risk Escalation Rules

Escalate when the API is: public, partner-facing, mobile-client-facing (long client upgrade tail), high-volume (> 100 RPS sustained), payment / money-movement, permission-sensitive, PII-bearing, regulated (PCI/HIPAA/PSD2/GDPR), incompatible with deployed clients, or when a deprecation window shorter than 6 months is proposed for an external API. Escalate to architecture for cross-service contracts, to security for auth/scope changes, to product for breaking changes affecting paying customers, to SRE when the contract change shifts traffic patterns (e.g., chatty → batch).

# Reference Loading Policy

Load [references/api-style-and-semantics.md](references/api-style-and-semantics.md) only for L3+ API design, public/partner/mobile contracts, ambiguous REST/gRPC/GraphQL/event choices, retry/idempotency/status-code disputes, long-running operations, or versioning/deprecation decisions.

Source/dev-only authoring path: `references/api-style-and-semantics.md`; compiled runtime profiles place the same deep reference under the selected capability reference bundle.

Use [references/checklist.md](references/checklist.md) for compact review passes. Use [examples/example-output.md](examples/example-output.md) only when the final output shape is unclear. Do not load deep references for L1/L2 local contract edits when the inline output contract already determines request, response, error, auth, pagination, idempotency, and compatibility expectations.

# Critical Details

Contracts describe **behavior, not only shapes**. The following details cause production incidents when ignored:

- **Authentication and authorization are part of the contract.** Document required scopes, roles, tenant scoping, and the exact failure shape per failure class.
- **Errors need stable codes and client actions.** Use RFC 7807/9457 `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, and stable application-specific `code` and `retryable` boolean.
- **Pagination must be deterministic under concurrent writes.** Prefer opaque cursors over offset/limit; offsets skip or duplicate rows when the dataset mutates. Cursors must encode sort key + tiebreaker. Document max page size; reject larger.
- **Idempotency keys** need: client-supplied scope (per-operation), server-side retention window (≥ 24h typical, ≥ 7d for billing), response replay (same body + status for same key), key-collision rejection (`409` if same key with different payload), and storage cost ownership.
- **Optimistic concurrency.** Use `ETag` + `If-Match`/`If-None-Match` or a `version` field for mutable resources. Returning a `412 Precondition Failed` is the contract.
- **Partial responses & sparse fieldsets.** If supported, document the projection grammar (`fields=`, GraphQL selection) and the always-included minimal set.
- **Filtering grammar.** Avoid ad-hoc string DSLs. Either RHS-colon (`status:active`), structured query params (`filter[status]=active`), or a documented expression grammar (RSQL/CQL). Reject unknown filter fields explicitly, not silently.
- **Sorting.** Always define a deterministic tiebreaker (typically id) to make pagination stable.
- **Time, numbers, money.** RFC 3339 UTC, integers for ids, decimal strings or minor-unit integers for money. Never floats for monetary values. Document timezone semantics for dates that are not instants.
- **Internationalization.** `Accept-Language` honored or rejected explicitly; localized fields documented; locale-dependent formats (dates, numbers) returned in canonical form, not display form.
- **Rate limiting.** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers (or RFC 9180 draft `RateLimit-*`); `429` with `Retry-After` (seconds or HTTP-date).
- **Long-running operations.** Return `202` with an operation resource (Google AIP-151): `name`, `done`, `error`, `response`. Polling and webhook callback semantics documented.
- **Compatibility classes** (must declare): additive (safe), additive-optional (safe), additive-required (breaking), removal (breaking), semantic change (breaking even if shape unchanged), enum addition (often breaking for strict clients).
- **Hide persistence internals.** Do not expose ORM relation graphs, surrogate keys, or transaction-only fields. Hide implementation details (auto-increment ids, internal status enums) behind stable representations.
- **Content negotiation.** Pin `Content-Type` and `Accept`; reject `*/*` for write paths in machine APIs.
- **Webhook security.** HMAC-SHA256 signature over body + timestamp; replay protection via timestamp tolerance (≤ 5 min) and nonce; retry policy (exponential backoff, ≥ 24h horizon, DLQ).

### Decision Tree: Versioning Approach

```
Is the change additive-optional (new optional field, new endpoint)?
├─ Yes → No version bump; document under current version; semver minor in changelog.
└─ No → Is the change a semantic change to an existing field/code?
        ├─ Yes → BREAKING. Choose:
        │       ├─ Public/partner API → New major version (`/v2/`) + deprecation timeline ≥ 12 months.
        │       ├─ Internal API → Coordinated rollout via expand-contract (add new, dual-write/read, retire old).
        │       └─ GraphQL → New field + `@deprecated(reason)`; never bump.
        └─ No → Is the change a removal?
                ├─ Yes → Mark `Sunset` + `Deprecation` headers (RFC 8594, draft); retain ≥ 1 release; then 410.
                └─ No → Re-classify; you are not yet ready.
```

# Failure Modes

- **Undeclared response-shape break:** fields change type, name, nullability, or meaning because the contract lived only in code comments. Detection: old/new schema diff, generated-client diff, and consumer contract test. Impact: deployed clients crash or silently corrupt data.
- **Unbounded or unstable collection contract:** list endpoints omit max page size, cursor semantics, stable sort, or tiebreaker. Detection: pagination boundary test under concurrent inserts plus contract examples. Impact: duplicate/missing records, slow deep pages, and broken dashboards.
- **Retry duplicate side effect:** POST/PATCH/create webhook lacks idempotency key scope, retention, replay, and conflict semantics. Detection: same-key replay and same-key-different-payload tests. Impact: duplicate orders, refunds, notifications, or irreversible side effects.
- **Unsafe error contract:** raw strings, stack traces, `200` error bodies, or ambiguous 401/403/404/409/422 semantics reach clients. Detection: error matrix, negative contract tests, and safe public problem-detail examples. Impact: unsafe retries, existence leaks, brittle client string matching, and noisy observability.
- **Stale generated/spec evidence:** generated docs, SDKs, examples, or prior validation predate the final route/controller/spec change. Detection: repository graph delta, generated artifact diff, validation command output, and freshness timestamp. Impact: agents or reviewers approve behavior that no client can reliably implement.
- **Persistence model leakage:** surrogate database ids, ORM relation graphs, internal status enums, or transaction-only fields become public. Detection: model-boundary map and DTO/domain/persistence split review. Impact: storage changes become breaking API changes and enumeration leaks row counts.
- **Incompatible enum/filter/query semantics:** enum values, filter grammar, sparse fields, or ad-hoc query DSLs evolve without compatibility mode. Detection: strict-client fixture, unknown-filter rejection test, and generated schema comparison. Impact: strict clients reject responses, filters inject unsafe expressions, or old dashboards misread data.
- **Webhook or async operation ambiguity:** unsigned callbacks, missing replay window, `200 pending` long-running operations, or undocumented retry horizon are accepted. Detection: signature/replay tests, `202` operation-resource example, and timeout/retry matrix. Impact: forgery, replay, lost callbacks, and clients confusing async with sync.
- **Deprecation without protocol evidence:** removal is announced outside the spec and lacks `Deprecation`/`Sunset`, migration examples, telemetry, owner, or rollback path. Detection: spec headers, consumer inventory, cleanup ticket, and old-path usage evidence. Impact: pinned or unknown consumers break after release.

# Output Contract

Return an API contract specification containing, for each operation:

- `mode_selected` (new operation, existing contract evolution, compatibility repair, error/auth repair, idempotency/retry contract, async/webhook contract, or generated-spec alignment)
- `boundaries_inspected` (spec files, handlers/controllers, DTOs, error catalogs, auth policy, generated clients, SDKs, docs/examples, consumers, tests, telemetry, and skipped surfaces with reason)
- `source_evidence` (current source/spec/generated artifacts that prove operation behavior, consumers, compatibility, and validation freshness)
- `graph_memory_trajectory_judgment` (accepted, rejected, stale, partial, or not verified claims from repository graph, project memory, ADRs, generated docs, prior summaries, or validation order)
- `operation_id` (stable, unique)
- `method`, `path` (or RPC service.method)
- `summary`, `description`, `tags`
- `auth_requirements` (scheme, scopes, tenant scope)
- `request`: headers, path params, query params, body schema (ref to DTO), examples
- `response`: per status code → headers, body schema, examples
- `error_responses`: per error class → status, RFC 7807 problem document with stable `code`, `retryable`, `remediation`
- `idempotency`: required? key header name, scope, retention, replay semantics
- `pagination`: style (cursor/offset/none), max page size, sort keys, tiebreaker
- `concurrency`: ETag/version, precondition headers, conflict response
- `rate_limit`: limits, headers, retry guidance
- `caching`: `Cache-Control`, `ETag`, `Vary` rules
- `compatibility`: change class (additive / breaking), affected clients, deprecation/sunset dates
- `versioning`: version selector, current/previous/next
- `examples`: complete request/response pairs including at least one error
- `contract_tests`: Pact/OpenAPI-Examples/Schemathesis test ids that prove the contract
- `observability`: emitted metrics (latency, error rate by code), trace span name, log correlation fields
- `security_notes`: input validation rules, sensitive-field redaction in logs, scope-vs-data checks
- `consumer_inventory`: known clients, generated SDKs, mobile/partner/public clients, internal services, dashboards/jobs, and unknown-consumer risk
- `changed_contract_to_validation_map`: each changed method/path/status/error/schema/auth/idempotency/pagination/version/generated artifact/consumer class mapped to a validator, contract test, generated-client check, rollout gate, or residual risk
- `reuse_and_placement_rationale`: existing spec, route, controller, DTO, error catalog, generated source, or versioning path reused or rejected; no internal model exposure
- `evidence_limits`: unknown consumers, stale generated artifacts, telemetry not queried, untested SDK languages, unproven rollback, security paths not inspected, and residual risk owner

Deliverable artifact: an OpenAPI 3.1 / AsyncAPI / `.proto` / GraphQL SDL document **plus** a human-readable change summary classifying each operation as new / additive / breaking / removed.

# Quality Gate

The contract passes only when:

1. A client developer can implement against the spec **without reading server source** and without asking clarifying questions on auth, pagination, errors, idempotency, or compatibility.
2. The spec is machine-validated (e.g., Spectral lint passes; OpenAPI validator passes; Schemathesis property tests pass on a running server).
3. Every operation has at least one success and one error example, and the examples validate against the schema.
4. Every breaking change has an explicit migration path, a deprecation window, and a named owner.
5. Contract tests (consumer-driven where there is a known consumer; provider tests otherwise) exist and run in CI.
6. Auth scopes match `authentication-authorization` outputs; error codes match `error-code-design`; DTOs match `dto-schema-design`.
7. Current source/spec, generated clients, docs/examples, consumers, tests, graph/memory/trajectory claims, and validation freshness are cited or explicitly marked unavailable.
8. Each changed client-visible behavior maps to contract validation, generated-client verification, consumer compatibility evidence, rollout gate, or accepted residual risk.
9. Public/partner/mobile, sensitive, high-volume, async/webhook, or auth-scope changes include security, reliability, release, and documentation gate outcomes or skipped-surface rationale.

# Evidence Contract

Close an API contract design only when these answers are concrete: selected mode, standards/style chosen, boundaries inspected, current source/spec/generated artifacts inspected, consumers and unknown-consumer risk, old/new compatibility class, auth/error/DTO/idempotency/pagination/version boundaries, graph-memory-trajectory freshness judgment, changed-contract-to-validation map, reuse and placement rationale, behavior preservation for existing clients, validation evidence with command/output/artifact and validation results, what evidence proves, what evidence does not prove, evidence limits, residual risk owner, and next gate or explicit not-verified disclosure. A generic "OpenAPI updated" or "no callers found" claim is not sufficient evidence.

# Benchmark Coverage

This capability covers operation-level API behavior, OpenAPI/AsyncAPI/gRPC/GraphQL contract shape, HTTP semantics, idempotency and retry safety, pagination/filtering/sorting, auth and scope declaration, RFC 7807/9457 errors, compatibility/versioning, generated-spec alignment, consumer impact, graph-memory-trajectory freshness, and contract-to-validation mapping while keeping deep style matrices in references.

# Routing Coverage

Routes from `data-api-contract-changer`, `integration-change-builder`, `backend-change-builder`, `frontend-api-integration`, `dto-schema-design`, `error-code-design`, `version-compatibility`, `consumer-impact-analysis`, `contract-testing`, `idempotency-retry-design`, `security-privacy-gate`, and `reliability-observability-gate` should arrive here when operation-level client-visible behavior is primary. Route away when field schema, error taxonomy, stored data model, release approval, implementation wiring, or executable contract testing is primary.

# Used By

- data-api-contract-changer
- integration-change-builder

# Handoff

Hand off to `dto-schema-design` for field validation/serialization detail; `error-code-design` for the canonical error taxonomy; `version-compatibility` for rollout sequencing across clients; `security-privacy-gate` for sensitive-data exposure and OWASP API Top 10 review; `idempotency-retry-design` for retry safety detail; `frontend-api-integration` and `controller-api-implementation` for consumer/provider implementation; `observability` and `reliability-observability-gate` for SLI/SLO and rate-limit alerting.

# Completion Criteria

The capability is complete when the API is **stable, describable, testable, and safe for clients across retries, version skew, partial failure, and hostile input** — and when every change class (additive, breaking, removed) is named explicitly, with rollout, deprecation, and verification owned by a named party.
