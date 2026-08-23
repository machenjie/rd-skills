---
name: minimal-correct-implementation
description: "`analysis-agent`/`task-agent`/`review-agent`: use when added code, dependency, abstraction, configuration, or shortcut may exceed current need; skip when minimality is proven."
---

# minimal-correct-implementation

## Registry Trigger

**Use when**

- Accepted behavior may be met by deletion, reuse, standard or native behavior, an installed dependency, or direct local code.
- A diff adds a wrapper, interface, registry, dependency, file, configuration branch, speculative variant, or deliberate shortcut.

**Do not use when**

- Current requirements and owner boundaries already select one structure with no unresolved existence or minimality decision.
- The open question is placement, pattern fit, package policy, public contract, clarity, or performance rather than whether added structure is needed.

## Skill Role

Decide whether structure exists. Compare delete or omit, repository behavior, standard or native behavior, an installed dependency, direct local code, and new structure in that order. Preserve accepted behavior, invariants, safety, testability, and recovery. Leave placement, pattern relationships, dependency governance, public contracts, and language rules to their owners.

## High-Value Rules

- Define present need from current acceptance, non-goals, reachable consumers, and owner boundaries.
- Reject speculative variant, scale, or reuse stories as present requirements.
- Use the simplicity ladder for candidate comparison without trading ownership, effects, contracts, safety, compatibility, rollback, or proof for fewer lines.

## Anti-Patterns

- Local success substituted for evidence of the minimal correct implementation contract.

## Stop Conditions

- After existence is accepted, route owner-internal placement to `implementation-structure-design`.
- Route a real variation, lifecycle, protocol, concurrency, or extension relationship to `design-pattern-selection`.
- Route dependency governance to `package-dependency-management`.
- Route behavior-preserving movement to `refactoring` after the destination is fixed.
- Route public compatibility to the API owner, clarity to `code-clarity-maintainability`, runtime cost to `language-performance-safety`, and cleanup lifecycle to `cleanup-deletion-governance`.

## Output Contract

- minimality decision with retained or removed structure candidate comparison current force rejected nearer alternatives behavior-preservation proof specialist routes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [simplicity ladder](references/simplicity-ladder.md) | benchmark-pattern | Multiple minimal-correct candidates differ in ownership safety compatibility recovery or deletion behavior | One repository-conforming candidate already satisfies acceptance and protected obligations with no added structure | analysis-agent, task-agent, review-agent | option-comparison, selected-approach, residual-risk |
