---
name: implementation-structure-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when reuse or method/class/file placement inside one owner is disputed; skip fixed placement or cross-module ownership."
---

# implementation-structure-design

## Registry Trigger

**Use when**

- Semantic-compatible reuse inside an established owner is disputed.
- Method, class, file, or test placement inside an established owner is disputed.
- Co-location or private extraction inside an established owner is disputed.
- An owner-private new structure inside an established owner is disputed.
- A deliberate separate implementation inside an established owner is disputed.
- Generated-source separation or placement inside an established owner is disputed.

**Do not use when**

- Cross-module ownership, dependency direction, public/shared/exported surfaces, cycles, or shared packages change; use `module-boundary-design`.
- A distributable SDK or library contract changes; use `sdk-library-contract-design`.
- Architecture style, layer responsibilities, or extension compatibility is primary; use `architecture-style-selection`, `layered-architecture-design`, or `extensibility-design`.
- Model translation, side-effect ordering, persistence semantics, or transport contracts are primary; use their owning capability.
- Behavior-preserving movement is primary; use `refactoring`. For local flow or readability, use `code-clarity-maintainability`.
- The current owner and repository convention already fix placement.

## Skill Role

Choose reuse, placement, visibility, extraction, generated-source separation, and test location inside one fixed owner. Do not redefine business rules, external contracts, or module architecture.

## High-Value Rules

- Consume an accepted need for structure from `minimal-correct-implementation`; this capability decides only semantic-compatible reuse and placement inside the accepted owner.
- Route exports, cross-owner/shared modules, public surfaces, dependencies, cycles, or distributable artifacts to `module-boundary-design` or `sdk-library-contract-design`.
- Load the object-decomposition, reuse-placement, or evidence Reference for its named open decision; after placement, route movement to `refactoring` and local clarity to its owner.

## Anti-Patterns

- Local success substituted for evidence of the implementation structure design contract.

## Stop Conditions

Stop when placement would change an accepted owner, public contract, model semantics, effect order, resource lifetime, persistence, API behavior, or another observable without authority and proof.

Stop when generated-source authority is unknown or a requested edit bypasses its accepted generator, template, or configuration authority.

## Output Contract

- Implementation placement decision with accepted existence input, inspected reuse and deliberate-separation candidates, selected owner-private location, visibility, and co-location/extraction rationale. It records semantic and generated-source handling, tests/fixtures, evidence and validation plan, proof limits, delete/drift conditions, specialist handoffs, and residual risks.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [object module decomposition](references/object-module-decomposition.md) | targeted | co-location extraction visibility split merge or test placement remains disputed inside one owning module | the current owner and change lifecycle already fix the object or file boundary | task-agent, review-agent, analysis-agent | decision-record, validation-plan, proof-limit, residual-risk |
| [reuse and placement](references/reuse-and-placement.md) | targeted | repository-local reuse leaves more than one semantic-compatible owner-private placement or deliberate-separation decision | one semantic-compatible owner-private placement is already proved | task-agent, review-agent, analysis-agent | selected-approach, validation-plan, proof-limit, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | placement generated-source or deliberate-separation claims need current owner consumer and freshness evidence | no placement or source-authority claim awaits closure | task-agent, review-agent, analysis-agent | evidence-record, validation-plan, proof-limit, residual-risk |
