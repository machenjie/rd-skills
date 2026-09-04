# API Style and Semantics Reference

Load this reference for L3+ API contract decisions, public/partner/mobile contracts, ambiguous protocol choices, retry/idempotency/status-code disputes, long-running operations, or versioning/deprecation design.

## API Style Selection Matrix

- REST/JSON fits public or browser resource interactions and cacheable reads; specify cursor or page semantics and the governing media/URL version policy.
- gRPC fits internal polyglot RPC or streaming when browser access and HTTP debuggability are not primary; version packages, preserve deployed wire compatibility, and migrate consumers for incompatible change.
- GraphQL fits aggregated client reads only when resolver cost is controlled; use schema-policy additions/deprecations and connection pagination.
- Events and webhooks fit owned asynchronous notification, not synchronous completion; bind event identity, ordering/offset, schema compatibility, and versioned type.
- A long-running operation exposes an operation identity plus polling or callback only when work exceeds the request budget.

## Idempotency and Method Semantics

- GET/HEAD remain safe and idempotent requested semantics; OPTIONS describes capability or preflight rather than business mutation.
- PUT is idempotent only for the contract's full-replacement effect. DELETE defines the repeated resource outcome and its documented synchronous, accepted, absent, or gone response.
- POST is not idempotent by default. Consequential duplicates require contract-owned operation identity with carrier, scope, expiry, mismatch, and result-replay behavior.
- PATCH uses explicitly selected ordered-patch, merge-patch, or domain-command semantics and states concurrency and replay behavior.

## Status Code Discipline

- `200`, `201`, `202`, and `204` distinguish returned success, created resource, accepted asynchronous work, and no-content success; `201` resource/location and `202` operation link follow the governing contract, while `204` has no body.
- `400` represents the protocol-selected malformed/invalid request; `409` a state conflict; `410` permanent removal; `422` understood but unprocessable content only when selected by method and representation semantics; `428` a required precondition.
- `401` means unauthenticated and `403` unauthorized. Use `404` for absence or a documented existence-hiding policy, never as an unexplained authorization substitute.
- `429` includes `Retry-After` only from authoritative retry timing. `5xx` is server failure, not a client or business-rule error.

## Versioning Approach

Apply the governing published API and consumer-compatibility policy before selecting a versioning mechanism.
An additive field or endpoint avoids a version change only when consumer evidence preserves validation, exhaustive matching, generated clients, defaults, ordering, and side effects.
For removal, required fields, or observable semantic change, select a major version, compatibility bridge, or coordinated migration from policy and consumer evidence; document mixed-version behavior, deprecation, and rollback.
Use expand-contract only with current writer/reader coordination and rollback evidence. A GraphQL addition or `@deprecated(reason)` still requires schema-policy compliance and current consumer proof.
