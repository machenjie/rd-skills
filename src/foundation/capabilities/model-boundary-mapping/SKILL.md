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

Own mapping, validation, semantic preservation, and leakage boundaries.

## High-Value Rules

- Define the source, target, mapping, validation, and policy owners.
- Preserve allowed fields and null, absent, empty, false, and default meaning.
- Select one named Reference for mapping choice, closure, or evidence.
- If the mapping decision remains active, load only its named Reference.

## Anti-Patterns

- Local success substituted for boundary and leakage evidence.

## Stop Conditions

Stop on unknown boundary ownership, public-consumer impact, sensitive leakage, or hidden mapper effects.

## Output Contract

- Return a Model Boundary Map: identify source, target, mapping and validation owners, null/default semantics, compatibility, generated/handwritten boundary, tests, and rejected leakage

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | transport domain persistence event or provider models invite competing mappings | one owned mapper preserves every semantic and visibility boundary | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | mapping changes fields defaults null semantics ownership or generated boundaries | source and target models remain unchanged and isolated | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | no-leak compatibility or semantic-preservation claims need fresh proof | current schemas consumers generated outputs and tests prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
