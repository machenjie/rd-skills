# API Contract Evidence Patterns

Use this reference when API contract closure depends on generated artifacts, consumer evidence, or changed-contract-to-validation mapping.

## Evidence Map
- **Operation shape change:** prove old/new spec diff, handler or controller boundary, request/response examples, schema validation command, artifact, exit code, and freshness.
- **Error, auth, or permission contract:** prove status/code matrix, denied examples, retryability, redaction, security gate outcome, and negative contract tests.
- **Pagination, filtering, sorting, or idempotency:** prove deterministic ordering, max bounds, replay/conflict behavior, generated examples, and client-visible compatibility.
- **Generated client or SDK:** prove generator command, checked-in diff, representative client compile/test, versioning note, and release owner.
- **Deprecation or breaking change:** prove consumer inventory, telemetry, migration guide, sunset/deprecation headers, rollout gate, and rollback or containment path.

## Evidence Rules
- Every accepted evidence item names command or validator, report artifact, exit code, consumer scope, what it proves, what it does not prove, and residual risk owner.
- Repository graph, generated docs, project memory, and prior validation are freshness leads only; they cannot close contract readiness without current spec/source/generated artifact evidence.
