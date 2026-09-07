# Authentication Authorization Evidence Patterns

Load this reference when subject authority, derivation, propagation, attribution, freshness, authorization handoff, reachability, or negative-path claims require fresh proof. Do not use it as a credential lifecycle or permission-policy tutorial.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Subject authority is known | Current human/workload/partner identity source, authoritative writer, accepted proof result, caller-controlled fields, and conflict behavior | Does not prove credential/session/token lifecycle controls |
| Internal derivation is unambiguous | Current mapping path, uniqueness and merge/delete/disable behavior, tenant relation, plus missing and conflicting mapping cases | Does not prove production mapping data or external provider state |
| Provenance survives propagation | API/RPC/worker/consumer/callback/admin/support trace, real/effective actor fields, overwrite protection, generated contract, and audit mapping | Does not cover unknown or externally owned paths |
| Downstream freshness is bounded | Changed identity/membership/delegation authority, re-resolution or failure path, stale-context case, and owner | Does not establish the subject-resource permission rule |
| Delegated or machine attribution is preserved | Real/effective subject, delegation source, credential owner, workload or purpose, propagation path, audit field check, and unattributable-context case | Does not prove credential lifecycle or resource/action entitlement |
| Authorization handoff is bounded | Subject and provenance, tenant semantics, relevant assurance, authority and freshness of handed-off fields, unresolved conditions, and permission-owner contract | Does not prove downstream enforcement without permission evidence |
| Reachable derivation paths were inspected | In-scope source/config, API, RPC, worker, consumer, callback, admin, support, generated contract, and tests classified as inspected, not applicable, or unknown | Unknown paths remain residual scope |

## Freshness And Closure

- Treat prior mapping decisions, provider notes, generated clients, old identity diagrams, and compaction summaries as search leads until current source, configuration, owner, scope, and affected paths match.
- Re-run selected negative cases after the final identity mapping, propagation, configuration, fixture, generated artifact, or audit edit.
- Map the final confidence claim to current source/config paths, parsed validation outcomes, audit samples, owner evidence, and explicit unverified scope.
- Keep credential lifecycle, external provider behavior, production mapping data, undiscovered clients, and permission enforcement outside the proven boundary unless inspected by their owning decision.

## Anti-Patterns

- Treat an authenticated session, signed assertion, embedded role, or internal caller as sufficient authorization for a protected action.
- Trust caller-supplied subject, tenant, delegation, role, group, or scope, or propagate identity context whose authority and freshness cannot be reconstructed downstream.
- Expand this Skill into credential/session/token control selection, or generalize one successful login or API path to workers, callbacks, recovery, support, and external identity mappings.
