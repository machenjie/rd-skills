# API Contract Evidence Patterns

Use this reference when API contract closure depends on generated artifacts, consumer evidence, or changed-contract-to-validation mapping.

## Evidence Map
- **Operation shape change:** prove the old/new diff in the authoritative contract representation and implementation or provider boundary.
- **Operation shape evidence:** include applicable examples, validation outcomes, and generated artifact or client diffs.
- **Error, auth, or permission contract:** prove status/code matrix, denied examples, retryability, redaction, security gate outcome, and negative contract tests.
- **Pagination, filtering, sorting, or idempotency:** prove deterministic ordering, max bounds, replay/conflict behavior, generated examples, and client-visible compatibility.
- **Generated client or SDK:** prove generator command, checked-in diff, representative client compile/test, versioning note, and release owner.
- **Deprecation or breaking change:** prove consumer inventory, telemetry, migration guide, sunset/deprecation headers, rollout gate, and rollback or containment path.

## Evidence Rules
- For each evidence item supporting a final API-contract claim, record its source, outcome, consumer scope, proof limit, and residual-risk owner.
- Preserve identifying fields from evidence-producing reports or artifacts.
- When API readiness relies on earlier evidence, confirm the changed operation against its current authoritative contract representation.
- Confirm current implementation or provider evidence independently.
- Confirm relevant consumers.
- Include generated artifact or client evidence when the workflow produces those surfaces.
- Disclose missing or unverified contract, implementation, provider, consumer, and deployed-version evidence.
