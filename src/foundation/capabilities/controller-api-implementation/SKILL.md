---
name: controller-api-implementation
description: "`task-agent`: use when implementing routes, request parsing, validation handoff, auth context, responses, or status/error mapping; skip work without a controller/API boundary."
---

# controller-api-implementation

## Registry Trigger

**Use when**

- implement controller routing request parsing validation response and status codes

**Do not use when**

- no task-local controller api implementation decision is required

## Skill Role

Implement transport parsing, structural validation handoff, trusted identity extraction, application invocation, protocol responses, error mapping, resource bounds, and controller evidence. Exclude business and authorization decisions.

## High-Value Rules

- **Keep the controller at the transport boundary.** Parse protocol input, construct validated application input, pass trusted context, invoke the owned use case, and map its result without embedding product or persistence decisions.
- **Treat external fields as untrusted until the right owner accepts them.** Bound decoding, coercion, multiplicity, size, format, content type, and malformed-input behavior, then hand business validation to the application or domain boundary.
- **Preserve identity provenance without deciding entitlement.** Derive subject and tenant context solely from trusted authentication, rejecting conflicting caller fields.
- Pass resource-action decisions to the authoritative authorization owner.
- **Map responses from the current contract.** Preserve status class, headers, body, content negotiation, pagination or streaming semantics, caching, and no-content behavior without returning persistence or internal domain representations.
- **Map failures by stable external meaning.** Translate recognized validation, absence, authentication, authorization, conflict, domain, dependency, and unexpected failures according to the current API contract while redacting internal detail.
- **Bound streaming and expensive work.** Define body, multipart, decompression, buffering, upload, download, cancellation, timeout, and connection-lifecycle behavior from current capacity and abuse constraints.
- **Test transport behavior at the boundary.** Exercise routing, parsing, malformed input, trusted context, application invocation, response mapping, redaction, cancellation, and affected contract fixtures without replacing real integration proof.

## Anti-Patterns

- Put pricing, eligibility, permission, state-transition, or persistence decisions in controller branches.
- Trust subject, tenant, role, scope, resource ownership, or internal identifiers supplied in ordinary request fields.
- Return raw exceptions, persistence entities, internal identifiers, or framework defaults that bypass the owned external contract.

## Stop Conditions

Escalate when the API contract or identity authority is unclear, object authorization exists only in transport code, untrusted payload work is unbounded, or streaming or multipart ownership is unknown. Also escalate when error mapping can leak sensitive detail or consequential writes lack domain and security ownership.

## Output Contract

- controller implementation decision with transport parsing, validation handoff, identity provenance, application boundary, contract response and error mapping, resource bounds, and focused evidence

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [boundary](references/boundary-patterns.md) | benchmark-pattern | Route ownership, DTO mapping, authorization, or idempotency boundaries are unclear | The controller remains a thin transport adapter | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Route changes touch validation, auth context, errors, or response shape | No transport-facing controller behavior changes | task-agent | checklist-result, validation-plan |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Controller claims require fresh routes, specs, generated files, and tests | Current route and transport artifacts prove boundary completeness | task-agent | evidence-record, proof-limit, residual-risk |
