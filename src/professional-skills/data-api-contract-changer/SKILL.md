---
name: data-api-contract-changer
description: Designs and modifies data models, schemas, migrations, API contracts, DTOs, validation, error codes, pagination, compatibility, idempotency, versioning, deprecation, rollout, and rollback paths.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Data API Contract Changer

## Mission
Design, modify, and safely roll out changes to data models, schemas, API contracts, serialization formats, error semantics, and versioning strategies — so that existing consumers are protected, new capabilities are clean, migration paths are tested, and rollback is always possible without data loss or unrecoverable state.

## When To Use
- Adding or modifying database schemas, table columns, indexes, or constraints.
- Modifying API endpoint paths, request schemas, response shapes, status codes, or error codes.
- Changing DTO, serialization format, or field names that consumer clients rely on.
- Adding pagination, filtering, or sorting parameters to existing endpoints.
- Versioning or deprecating API endpoints or response fields.
- Designing idempotency for endpoints that can be retried.
- Adding data validation rules or changing validation semantics for existing inputs.
- Writing database migration scripts that run against live data.

## Do Not Use When
- Changes are purely internal implementation (private methods, internal data structures) with no effect on API shape, data persistence, serialization, or external contracts.
- The change is a frontend-only rendering decision with no backend data model impact.
- Performance optimization within existing contract behavior — use `data-middleware-change-builder` for query and index work.

## Non-Negotiable Rules
- **Backward compatibility is the default obligation**: any change that removes fields, changes types, narrows allowed values, or breaks client assumptions is a breaking change and must be versioned or staged.
- **Expand/migrate/contract (EMC) discipline**: never combine remove-old with add-new in the same deployment; expand first (add new), migrate clients, then contract (remove old).
- **Rollback migration required before forward migration ships**: every migration that alters schema must have a tested, executable rollback migration before the forward migration is reviewed.
- **No destructive migration during peak traffic windows**: `DROP COLUMN`, `DROP TABLE`, large `ALTER TABLE`, mass data rewrites must be scheduled during low-traffic windows with maintenance-mode or zero-downtime strategies.
- **Client-facing validation must return machine-readable error codes** — never return unstructured error strings for validation failures that clients may need to act on.
- **Idempotency is required for all endpoints that accept payment, state transitions, or writes that can be retried**: idempotency key design must precede implementation.
- **Deprecation requires a sunset timeline and migration alternative**: deprecated endpoints, fields, and schemas must document the removal date, the replacement, and the migration path before deprecation is announced.
- **Never rely on application-layer enforcement for critical data constraints**: data integrity rules (uniqueness, foreign keys, non-null) must be enforced at the database level, not only in application code.
- **API contracts are public commitments**: once an API is documented and consumed externally, changing it requires the same discipline as a public release — stakeholder notification, versioning, and migration guide.

## Industry Benchmarks
- **REST API Design Guidelines (Google, Microsoft, Stripe)**: Use semantic HTTP methods correctly; use consistent resource naming (plural nouns); use standard error formats (RFC 7807 Problem Details); paginate all list endpoints.
- **OpenAPI 3.0 / AsyncAPI 2.0**: Machine-readable API specification — every public or internal API contract must have a spec that is versioned alongside the implementation.
- **Consumer-Driven Contract Testing (Pact)**: Verify API changes against all known consumer contract expectations before release — prevents integration regressions.
- **SemVer (Semantic Versioning)**: Breaking changes increment the major version; backward-compatible additions increment minor; patches for bug fixes. Applied to API versioning.
- **Stripe API Versioning Model**: API versions are date-stamped; each consumer pins to a version; new versions are additive; old versions are maintained with a declared sunset.
- **Zero-Downtime Migration Patterns (Depesz, Flyway)**: Online schema changes using shadow columns, copy-and-swap, or pt-online-schema-change for large tables in PostgreSQL and MySQL.
- **RFC 7807 (Problem Details for HTTP APIs)**: Standard error response format: `type` (URI), `title`, `status`, `detail`, `instance` — required for machine-readable error handling.
- **CQRS + Event Sourcing Schema Evolution**: When events are immutable, schema evolution requires upcasters, versioned event types, or read-model projections.

### Compatibility Classification Matrix

| Change Type | Compatibility Class | Required Strategy |
|---|---|---|
| Add optional field to response | Non-breaking | Add + document; no version bump required |
| Add optional request parameter | Non-breaking | Add with default; backward-compatible |
| Add required request parameter | Breaking | Version endpoint; provide migration guide |
| Remove or rename response field | Breaking | EMC: add new, deprecate old, remove after cutover |
| Change field type (widening) | Usually non-breaking | Verify all consumers handle both types |
| Change field type (narrowing) | Breaking | Version; migration guide; sunset timeline |
| Change error code semantics | Breaking | Version; consumer migration required |
| Add database column (nullable) | Non-breaking | Online migration; backfill separately |
| Drop database column | Breaking | EMC: deprecate app usage, then drop column |
| Rename database table | Breaking | Two-phase: add new, migrate, drop old |

## Technical Selection Criteria
Evaluate every proposed data or API contract change against:
- **Compatibility class**: Non-breaking, breaking (versioned), or breaking (immediate) — with explicit declaration.
- **Consumer enumeration**: Who calls this endpoint or reads this schema? Internal services, mobile clients, third-party integrators, analytics pipelines?
- **Migration sequencing**: What is the exact order of deploy steps (service A before B, migration before or after code deploy)?
- **Idempotency design**: Can this endpoint be safely called multiple times with the same effect? What is the idempotency key scope and storage?
- **Validation model**: What is valid input? What validation errors are returned and in what format? What happens to invalid input in existing records?
- **Error code taxonomy**: Is there a stable, machine-readable error code for each failure mode? Does the new error map to the existing taxonomy or require an addition?
- **Pagination design**: Cursor-based (stable ordering, no offset drift) or offset-based (simpler, inconsistent under writes)? Page size limits and defaults?
- **Rollback safety**: If the new code is rolled back, does the old code still function with the new schema? Is the rollback migration executable?
- **Performance impact**: Does the schema change affect query plans for existing high-frequency queries? Are indexes required or affected?
- **Deprecation timeline**: If this change deprecates an existing contract, what is the sunset date and how are consumers notified?

### Decision Tree: Breaking Change Handling

```
Does the change remove, rename, or change the type of an existing field?
├── Yes → Breaking change
│   ├── External consumers exist? → Version endpoint; migration guide required before release
│   └── Internal consumers only? → EMC staged rollout; coordinate service deployments
Does the change add a required parameter?
├── Yes → Breaking change → Version endpoint; default value or migration guide
Does the change alter error code semantics?
├── Yes → Breaking change → Version; consumer testing required
Does the change only add optional fields?
└── Non-breaking → Document and release
```

## Risk Escalation Rules
- Escalate when a migration script runs against a table with > 10 million rows — requires online migration strategy (pt-online-schema-change, pg_repack, or copy-and-swap).
- Escalate when a migration is not reversible in a single transaction — the rollback path requires manual intervention.
- Escalate when an API change breaks a consumer with a known SLA or external customer commitment.
- Escalate when a data migration handles financial amounts, PII, legal records, or regulated data that requires data owner sign-off.
- Escalate when multi-tenant data isolation could be affected by the schema change.
- Escalate when the change involves cross-service schema access without API mediation — direct cross-service database reads create hidden coupling.
- Escalate when write-path changes affect idempotency guarantees that downstream consumers depend on.
- Escalate when a consumer version skew window (old API + new API coexisting) exceeds the planned deployment window.

## Critical Details
- **EMC is not optional for breaking changes**: Expand (deploy new schema + code that supports both), Migrate (move consumers to new format), Contract (deploy code that removes old format, then drop old column/endpoint). Each phase is a separate deployment.
- **Online ALTER TABLE**: For MySQL tables > 100k rows, `ALTER TABLE ADD COLUMN` takes an exclusive lock — use `pt-online-schema-change` or `gh-ost`. For PostgreSQL, use `ADD COLUMN ... DEFAULT NULL` (instant) instead of `ADD COLUMN ... DEFAULT <value>` (table rewrite).
- **Cursor-based pagination is required for large result sets**: Offset-based pagination with `LIMIT / OFFSET` produces inconsistent results when rows are inserted or deleted during pagination and degrades quadratically with page number.
- **Enum type changes are always dangerous**: Adding a value to a database enum type requires a full table rewrite in PostgreSQL before 12.x. Use a VARCHAR with a CHECK constraint or a separate lookup table for evolvable enumeration.
- **Idempotency key TTL**: Idempotency keys stored in a database table must have a TTL index and a policy for expired-key re-use — not defined = undefined behavior.
- **Response envelope consistency**: If existing endpoints return `{ data: [...] }`, new endpoints must use the same envelope — mixed response shapes require every consumer to handle both.
- **Nullable vs. optional vs. absent**: A field being `null` vs. absent from a JSON response have different semantics for many clients — define the contract explicitly.

### Anti-Examples

| Contract Change | Problem | Corrected Approach |
|---|---|---|
| Rename `user_id` to `userId` in response | Breaking for all consumers expecting `user_id` | Add `userId` alongside `user_id` (expand); deprecate `user_id` with sunset; remove after migration |
| `ALTER TABLE orders ADD COLUMN status VARCHAR(20) NOT NULL` on 50M row table | Exclusive lock, 10-minute downtime | `ADD COLUMN status VARCHAR(20)` (nullable), backfill, then add `NOT NULL` constraint online |
| Remove deprecated `v1/users` without migration guide | Breaks pinned consumers | Publish migration guide, notify consumers, respect sunset date |
| Error response: `{"error": "Invalid input"}` | No machine-readable code | `{"type": "/errors/validation", "title": "Validation Failed", "status": 400, "detail": "email: must be a valid email address", "instance": "/requests/abc123"}` |
| Offset pagination on orders endpoint | Inconsistent results, slow at depth | Cursor pagination: `?cursor=<opaque_token>&limit=50` |

## Failure Modes
- **Breaking clients with undeclared response changes**: A field type changes from string to integer — Python clients that call `field.upper()` crash with an `AttributeError` at runtime.
- **Running a destructive migration at peak traffic**: `DROP COLUMN` acquires an exclusive lock during peak hours — all writes block, the service times out, and a P1 incident is triggered.
- **Removing fields before consumers migrate**: A deprecated field is removed 2 weeks after the deprecation notice — consumers using old client libraries haven't released an update yet.
- **Lost idempotency on retries**: A payment endpoint has no idempotency key — a network timeout causes the client to retry, the charge is created twice, and reconciliation takes days.
- **Enum value added to database type**: PostgreSQL rewrites the entire table to add an enum value — 2 hours of migration on a 500 GB table.
- **Rollback fails because schema has moved forward**: Code is rolled back but the new nullable column added during the deploy returns unexpected values to the old code.
- **Pagination drift under load**: An admin panel fetches pages of users with `OFFSET / LIMIT` while user records are being created — users on page 2 appear on page 1 or are skipped entirely.

## Output Contract
Return a structured contract change plan with:
- **Compatibility declaration**: Breaking or non-breaking, with class from compatibility matrix.
- **Consumer list**: Named consumers with version, dependency, and migration readiness.
- **Migration plan**: Forward migration steps in deployment order; rollback migration steps; tested execution plan for large tables.
- **EMC schedule**: Expand / Migrate / Contract phases with deployment sequence and consumer coordination timeline.
- **Idempotency design**: Key source, scope, storage, TTL, and expired-key behavior.
- **Validation and error model**: Validation rules, error code taxonomy, RFC 7807 compliance.
- **Deprecation notice**: Sunset date, replacement, migration guide link (if applicable).
- **Rollback safety**: Whether rollback is safe without data intervention; required rollback script.
- **Test obligations**: Consumer contract tests, migration tests, rollback tests, idempotency tests.

## Quality Gate
1. Compatibility class is explicitly declared for every contract change.
2. All consumers are enumerated with migration readiness assessment.
3. Breaking changes have either a version strategy or an EMC staged rollout plan.
4. Every migration has a tested rollback migration script.
5. Large table migrations use zero-downtime online migration strategies.
6. Idempotency is designed for all mutating endpoints that accept retried requests.
7. Validation failures return machine-readable error codes (RFC 7807 compliant).
8. Deprecated contracts have a documented sunset timeline, replacement, and consumer notification plan.
9. Consumer contract tests (Pact or equivalent) are defined for breaking changes.
10. Rollback safety is confirmed: old code functions correctly with the new schema.

## Handoff
- **backend-change-builder** — for server-side implementation of validation, idempotency, and error handling.
- **data-middleware-change-builder** — for index design, query plan analysis, and migration execution strategy.
- **integration-change-builder** — when external consumer coordination and API versioning notification is needed.
- **reliability-observability-gate** — when schema or API changes affect SLO-critical paths.
- **quality-test-gate** — for consumer contract test obligations and migration test design.
- **delivery-release-gate** — for deployment sequencing, migration rollout windows, and rollback procedure.

## Completion Criteria
Data and API changes are implementable with an explicit compatibility declaration, a consumer enumeration with migration readiness, a tested rollback migration, a zero-downtime strategy for large table changes, idempotency design for all retry-safe operations, RFC 7807 error responses, and an EMC deployment sequence that prevents consumer breakage during rollout.
