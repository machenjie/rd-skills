# Model Boundary Mapping Checklist

- Inventory each source, target, generated intermediary, or serializer in the scoped mapping path.
- Record unknown or externally owned representations as evidence limits.
- State owner, layer, contract surface, validation owner, mapping owner, policy owner, serialization owner, persistence owner, and consumer visibility.
- Inspect callers, consumers, mappers, serializers, validators, generated artifacts, schemas, events, persistence models, fixtures, tests, public exports, graph leads, and memory leads.
- Define allowed fields, rejected fields, direction, mapper placement, generated/handwritten boundary, and rejected direct-reuse rationale.
- Separate translation from pricing, authorization, state transition, tenant access, retry behavior, and side effects unless explicitly routed as policy.
- Preserve null, absent, empty, zero, false, unknown, not-applicable, server default, client omitted, enum/default, and value-object semantics with old/new examples.
- Verify persistence metadata, internal IDs, audit fields, tenant/object scope, permission flags, provider fields, ORM metadata, and sensitive fields do not leak without review.
- Confirm generated models stay generated, are not hand-edited, and are mapped through owned handwritten code.
- Map each boundary risk to observable tests, contract checks, generated-client checks, negative/compatibility cases, report paths, exit codes, freshness, and residual risk.
- Hand off schema, persistence, API behavior, compatibility, consumer inventory, side-effect order, test seams, privacy review, or release approval to the correct owner.
