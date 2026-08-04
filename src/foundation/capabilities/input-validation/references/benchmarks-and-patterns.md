# Input Validation Benchmarks And Patterns

Load this reference when current input and consumer evidence leaves multiple authority, representation, bounds, current-state, writable-field, rejection, compatibility, or external-response patterns viable. Do not load it for a single field already resolved by the root contract.

## Input Contract Decisions

| Decision | Compare | Required proof |
| --- | --- | --- |
| Source and authority | Direct actor, authenticated context owned elsewhere, partner or service, stored or replayed data, configuration, generated client, or unknown source | Authoritative writer, caller-controlled fields, alternate entry points, consumer, and unresolved-source behavior |
| Representation order | Raw-preserved segment, decoded transport, parsed structure, normalized field, canonical form, or intentionally distinct forms | Parser behavior, ambiguity and duplicates, transformation owner, comparison representation, and bypass case |
| Shape and resource bounds | Strict, extensible, versioned, partially consumed, streamed, deferred, or rejected representation | Consumer contract, unknown-field behavior, nesting/collection/byte/parser-work bound, amplification effect, and compatibility case |
| Cross-field and current state | Snapshot validation, version-bound decision, revalidation before effect, transactional guard, owner-supplied replay/duplicate indicators, or conflict outcome | Invariant authority, state-change window, owning command semantics, stale/replay/duplicate case, protected effect, and failure behavior |
| Writable field surface | Explicit command, owned mapper, patch contract, versioned mutation, or read-only external field | Accepted field set, sensitive-field owner, new-field behavior, authority-changing case, and persistence/effect trace |
| Rejection and compatibility | Local violation, semantic conflict, stale state, unavailable authority, policy-owned denial, compatibility bridge, or staged tightening | Safe location/remediation, disclosure and diagnostic bounds, affected consumers, old-valid case, rollout, and owner |
| External response | Validate at adapter, validate before mapping, version-specific parser, quarantine or degraded result, or reject before use | Expected authority/version/shape/semantics/freshness/bounds, malformed or stale case, downstream effect, and failure contract |

## Boundary Guardrails

- Derive constraints and representation order from the actual transport, consumer, storage, and effect; the same field can require distinct forms for authenticity, comparison, display, or persistence.
- Keep browser/server exploit paths with `web-security`; subject-resource-action policy with `permission-boundary-modeling`; cross-graph protected outcomes, abuse reachability/prioritization, and candidate control placement with `threat-modeling`; authenticated-subject authority/derivation/propagation/handoff with `authentication-authorization`; and credential/session/token lifecycle/replay/recovery/assurance/compromise with `authentication-security`.
- Validate replay/duplicate indicators against the owning command semantics, while `idempotency-retry-design` owns business uniqueness, key/result reuse, retry budget, and duplicate side-effect outcomes. Revalidate after transformations, state changes, retries, replays, merges, provider mapping, or generated-code changes when they can invalidate earlier evidence.

## Proof Limits

Scoped source and tests prove the inspected entry points, parsers, consumers, state fixtures, mappings, and external-response samples. They do not establish unknown callers, production payload diversity, provider behavior, deployment limits, future fields, concurrent state outside tested cases, or adjacent security and permission contracts unless independently verified.
