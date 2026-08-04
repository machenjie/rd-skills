# Authentication Authorization Benchmarks And Patterns

Load this reference when current subject-authority, derivation, propagation, attribution, freshness, or authorization-handoff semantics leave multiple viable patterns. Do not load it for credential/session/token lifecycle controls or subject-resource-action permission policy.

## Authenticated-Subject Decisions

| Decision | Compare | Required proof |
| --- | --- | --- |
| Subject authority | Current human, workload, partner, or upstream identity sources | Authoritative writer, accepted proof result, caller-controlled fields, and conflict behavior |
| Internal subject derivation | Direct identity mapping, owned lookup, bounded federation mapping, or unresolved identity | Mapping owner, uniqueness and merge/delete/disable behavior, tenant relation, and ambiguity outcome |
| Tenant or organization context | Identity-owned membership, resource-owned scope, delegated context, or explicit unresolved state | Context authority, cross-tenant behavior, update path, and downstream use |
| Actor provenance | Direct actor, real/effective pair, workload, partner, support, or delegated chain | Source, propagation fields, overwrite protection, audit attribution, and unknown-actor behavior |
| Downstream freshness | Current lookup, bounded handed-off context, invalidation signal, or failure on unavailable authority | Protected consequence, change source, stale behavior, authoritative re-resolution, and owner |
| Authorization handoff | Minimal subject and provenance context required by the permission owner | Field authority, tenant semantics, assurance relevance, freshness limit, unresolved fields, and consumer contract |

## Propagation And Handoff Boundaries

- Preserve authority and real/effective actor semantics across API, RPC, worker, consumer, callback, admin, support, generated contract, and audit boundaries found in the changed graph.
- Treat roles, groups, scopes, relationships, and assurance fields as claims with named authority and freshness; the permission owner decides whether they authorize the resource/action.
- Define behavior for missing, conflicting, deleted, merged, disabled, stale, overwritten, or unavailable identity context according to the current failure and disclosure contract.
- Route issuance, renewal, expiry, rotation, revocation mechanisms, replay controls, account recovery, compromise response, and assurance-factor selection to `authentication-security`.

## Proof Limits

Scoped repository and test evidence covers the inspected subject mappings and propagation paths. It does not prove credential lifecycle controls, external identity-provider state, production mapping data, undiscovered clients, or downstream permission enforcement unless those surfaces are independently verified.
