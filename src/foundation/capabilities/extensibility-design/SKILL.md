---
name: extensibility-design
description: "`analysis-agent`/`review-agent`: use when proven variation needs extension points, plugins, policy hooks, compatibility, or deprecation; skip when no extension decision exists."
---

# extensibility-design

## Registry Trigger

**Use when**

- design extension points configuration variation plugins and policy hooks

**Do not use when**

- no task-local extensibility design decision is required

## Skill Role

Prove real variation and define extension authority, isolation, lifecycle, compatibility, failure containment, observability, and retirement conditions. Exclude speculative roadmaps and implementation.

## High-Value Rules

- **Require evidence of variation before abstraction.** Name current consumers, distinct change reasons, ownership, and likely evolution; prefer direct code or configuration when the variation is unproven or locally owned.
- **Keep the extension contract narrow and semantic.** Define inputs, outputs, lifecycle, state, error, cancellation, ordering, resource, and compatibility behavior without exposing internal objects or unrestricted execution.
- **Split host compatibility from library compatibility.** This capability owns host registration, discovery, negotiation, isolation, lifecycle, and retirement. For a distributed SDK or library, hand package compatibility, migration, and consumer proof to `sdk-library-contract-design`; it does not redefine host semantics.
- **Bind artifact trust.** Executables crossing install or update trust boundaries use policy- or threat-model-selected origin, authenticity, or integrity controls; failures are rejected, and existing channels authenticate update metadata. Mutable or consequential activation requires rehearsed last-known-good rollback; config-only or static extensions instead record evidence-backed non-applicability.
- **Contain extension failure.** Define validation, time and resource bounds, isolation, partial effect, retry, disablement, fallback, and host recovery according to the consequence of extension failure.
- **Version for mixed host and extension populations.** Derive negotiation, compatibility, deprecation, and removal conditions from current consumers and policy rather than fixed notice periods or universal version rules.
- **Make registration and discovery deterministic.** Define identity, conflict handling, precedence, loading scope, ownership, and duplicate behavior so discovery order cannot silently change business meaning.
- **Observe and retire the boundary.** Capture attributable use, failures, cost, version adoption, and residual dependencies, then remove an extension path only when current evidence satisfies its exit condition.

## Anti-Patterns

- Introduce a plugin or hook for one hypothetical variation or to avoid making a current product decision.
- Give extension code ambient filesystem, network, secret, tenant, or mutation authority without an explicit host boundary.
- Freeze internal models into a broad extension API whose compatibility cost exceeds the proven variation.

## Stop Conditions

- Escalate unclear ownership, executable trust or tenant crossings, corrupting failure, unknown compatibility populations, unavailable isolation, or unobservable retirement.
- Escalate executable installation or update without selected origin, authenticity, or integrity proof, or an existing update channel without authenticated metadata.
- Escalate unproved last-known-good recovery when activation mutability or consequence triggers it.
- Require concise rationale and inspected evidence for inapplicable controls.

## Output Contract

- extensibility decision with variation evidence, narrow contract, authority and isolation, lifecycle and compatibility, failure containment, observability, retirement condition, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Strategy, plugin, webhook, or configuration extension patterns compete | No shared variation or extension contract is needed | analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Extension changes invariants, privileges, lifecycle, compatibility, or observability | The variation remains private behind one stable implementation | analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Extension claims require current implementers, contracts, and sandbox tests | No compatibility or extension-safety claim awaits proof | analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
