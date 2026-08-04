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

- Current acceptance, non-goals, reachable consumers, and owner boundaries decide existence; a speculative variant, scale, or reuse story does not create a present requirement.
- Compare delete or omit, existing repository behavior, standard or native behavior, installed dependencies, direct local code, and new structure against the task's actual boundaries.
- Select the first complete candidate unless a later option has a proved boundary advantage.
- Fewer lines or files are not minimality evidence when the change hides ownership, effects, public behavior, test seams, compatibility, rollback, or deletion paths.
- An abstraction has a current substitution axis, independent boundary contract, lifecycle need, or demonstrated duplication with one owner; convenience indirection is removable.
- A dependency needs a current capability gap and a smaller total ownership surface than local or existing behavior; package and supply-chain decisions route outward.
- A deliberate shortcut records the simplification, current ceiling, owner, measurable replacement trigger, focused validation, and residual risk without weakening required safety.
- Deletion or shrink proof covers reachable callers, generated or reflective paths, behavior-preserving outcomes, and the failure mechanism protected by tests.

## Anti-Patterns

- Future-proof configuration, one-implementation interfaces, pass-through wrappers, and scaffold-for-later code have no current force.
- Custom code or a new package duplicates repository, standard-library, runtime, framework, browser, or database behavior without a boundary advantage.
- A smaller diff removes authorization, data integrity, compatibility, accessibility, observability, recovery, or incident evidence.
- A shortcut note is treated as permission to skip validation or leave an unowned indefinite ceiling.

## Stop Conditions

- After existence is accepted, route owner-internal placement to `implementation-structure-design`.
- Route a real variation, lifecycle, protocol, concurrency, or extension relationship to `design-pattern-selection`.
- Route dependency governance to `package-dependency-management`.
- Route behavior-preserving movement to `refactoring` after the destination is fixed.
- Leave placement and pattern selection to their named decision owners.
- Route public compatibility to the API owner, clarity to `code-clarity-maintainability`, runtime cost to `language-performance-safety`, and cleanup lifecycle to `cleanup-deletion-governance`.

## Output Contract

- minimality decision with retained or removed structure candidate comparison current force rejected nearer alternatives behavior-preservation proof specialist routes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [simplicity ladder](references/simplicity-ladder.md) | benchmark-pattern | Multiple minimal-correct candidates differ in ownership safety compatibility recovery or deletion behavior | One repository-conforming candidate already satisfies acceptance and protected obligations with no added structure | analysis-agent, task-agent, review-agent | option-comparison, selected-approach, residual-risk |
