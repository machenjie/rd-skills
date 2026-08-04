# Input Validation Checklist

Load this reference when one change spans several input boundaries, representations, constraint classes, state checks, writable fields, rejection outcomes, or consumer effects. Do not load it when the root contract resolves one bounded field or boundary.

- Record each changed or reachable input source, actor or system, trust level, transport form, parser, enforcement owner, downstream consumer, and unknown entry point.
- Separate raw-preserved, decoded, parsed, normalized, and canonical forms; name ambiguity, duplicate, coercion, and transformation behavior plus the representation used for each decision.
- Derive relevant presence, null/empty/default, type, unit, precision, grammar, unknown-field, nesting, collection, byte, parser-work, and amplification constraints from the consumer contract.
- Define cross-field and business invariants, lifecycle or version authority, the state-change window, revalidation point, and stale, replay, or duplicate indicators.
- Route business uniqueness, key or result reuse, retry budget, and duplicate side-effect outcomes to `idempotency-retry-design`.
- Map accepted external fields into an owned command or update surface and identify authority-, tenant-, money-, lifecycle-, destination-, execution-, or publication-sensitive fields.
- Define malformed, unsupported, conflicting, stale, unavailable-authority, and policy-owned denial outcomes with safe location/remediation, disclosure bounds, redacted diagnostics, and consumer compatibility.
- Validate provider, service, callback, generated-client, cache, and stored responses for expected authority, version, structure, semantics, freshness, bounds, and failure behavior before trusted use.
- Route browser/server exploit paths to `web-security`. Subject-resource-action policy belongs to `permission-boundary-modeling`. Cross-graph protected outcomes, abuse reachability/prioritization, and candidate control placement belong to `threat-modeling`. Authenticated-subject authority/derivation/propagation/handoff belongs to `authentication-authorization`. Credential/session/token lifecycle/replay/recovery/assurance/compromise belongs to `authentication-security`. Business idempotency outcomes belong to `idempotency-retry-design`.
- Select applicable valid, invalid, boundary, malformed, ambiguous, unknown-field, resource-amplification, stale, replay, sensitive-write, external-response, and compatibility cases.
- Record final-edit freshness, explicit non-applicability, proof limits, unverified entry points or consumers, and residual owners.
