---
name: model-boundary-mapping
description: "`analysis-agent`/`task-agent`/`review-agent`: use when API/DTO, domain, persistence, event, generated, null/default, or mapper boundaries may leak; skip when models stay isolated."
---

# model-boundary-mapping

## Registry Trigger

**Use when**

- model boundary mapping API DTO command query domain object value object persistence model ORM event payload view model mapper assembler null default optional schema version serialization validation generated handwritten leakage

**Do not use when**

- no task-local model boundary mapping decision is required

## Skill Role

Define representation, validation, mapping authority, preserved semantics, and forbidden leakage across transport, domain, persistence, event, view, and generated-model boundaries.

## High-Value Rules

- Keep DTOs separate from domain, persistence, generated-provider, and view models to prevent authority leakage.
- Do not leak persistence models, lazy proxies, internal IDs, audit fields, or storage metadata into external contracts.
- Domain objects must not import HTTP, JSON schema, ORM decorators, generated clients, provider SDK models, UI view models, or transport-specific serializers.
- Mapper code owns translation, allowlisted fields, and boundary defaults, not pricing, authorization, lifecycle, or policy decisions.
- Validation owner is named for each boundary: trust-boundary DTO validation, domain invariant validation, persistence constraint, event schema validation, or generated-client validation.
- Preserve or intentionally test remapping of null, absent, empty, zero, false, unknown, not-applicable, and default states.
- Event payloads, public DTOs, SDK models, and generated clients are versioned contracts; generated models stay at the generated boundary and are not hand-edited.
- Treat current source, generated artifacts, and fresh validation as boundary evidence.

## Anti-Patterns

- Returning a persistence model exposes storage metadata and lazy behavior as contract.
- Passing an API DTO into domain behavior makes transport defaults, serialization choices, and caller-controlled fields look like trusted domain facts.
- Letting a mapper perform authorization, pricing, lifecycle transitions, repository access, publication, or other IO hides policy and side effects inside translation.
- Importing generated provider models into the domain makes external churn authoritative.
- Collapsing null, absent, empty, false, and default states silently changes compatibility semantics.
- Treating a persistence default as a domain default invents behavior when older rows, other writers, or omitted inputs do not share that meaning.
- Reusing mutable domain objects as events rewrites historical meaning during replay.
- Proving only a happy-path fixture misses forbidden-field leakage, generated-boundary drift, and negative null/default cases.

## Stop Conditions

Escalate public compatibility to `data-api-contract-changer`, domain semantics to `domain-impact-modeler`, and unknown consumers to `consumer-impact-analysis`. Route sensitive-field leakage to `security-privacy-gate` and mapper side effects to `data-side-effect-flow-tracing`.

## Output Contract

- Return a Model Boundary Map: identify source, target, mapping and validation owners, null/default semantics, compatibility, generated/handwritten boundary, tests, and rejected leakage

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | transport domain persistence event or provider models invite competing mappings | one owned mapper preserves every semantic and visibility boundary | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | mapping changes fields defaults null semantics ownership or generated boundaries | source and target models remain unchanged and isolated | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | no-leak compatibility or semantic-preservation claims need fresh proof | current schemas consumers generated outputs and tests prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
