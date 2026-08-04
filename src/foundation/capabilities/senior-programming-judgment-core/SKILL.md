---
name: senior-programming-judgment-core
description: "`analysis-agent`/`task-agent`/`review-agent`: use for cross-cutting source-backed judgment only when no narrower capability owns it; skip trivial or narrower-owned work."
---

# senior-programming-judgment-core

## Registry Trigger

**Use when**

- no narrower capability owns a task-local cross-cutting judgment about purpose facts objects states rules invariants boundaries failures side effects reuse placement validation observability or residual risk
- no narrower capability owns a structural decision spanning ownership state transitions failure paths side effects reuse validation or observability
- no narrower capability owns a Skill-authoring decision spanning profile registry build evaluation benchmark or closure evidence

**Do not use when**

- a narrower capability owns the task-local decision
- no task-local senior programming judgment core decision is required

## Skill Role

Resolve cross-cutting judgment only when no narrower capability owns it, covering purpose, facts, objects, invariants, boundaries, failures, effects, reuse, evidence, and residual risk.

## High-Value Rules

- **Start from purpose and current facts.** Name the changed outcome, affected actors or systems, authoritative sources, assumptions, and proof limits before proposing structure.
- **Model behavior through objects, states, and rules.** Identify identity, ownership, relationships, transitions, invariants, authority, and invalid outcomes that code needs to preserve.
- **Trace boundaries and side effects.** Follow validation, permission, persistence, external calls, events, cache, files, time, randomness, failure, retry, cleanup, and recovery relevant to the change.
- **Reuse by semantic fit and ownership.** Prefer existing boundaries that already own the behavior, and justify new shared structure by distinct consumers, stable contract, placement, and expected change direction.
- **Choose the smallest complete change.** Include implementation, migration, compatibility, cleanup, documentation, and operational effects required by the outcome while excluding speculative generalization.
- **Map claims to evidence.** Select focused tests, static checks, builds, contract comparisons, runtime observations, logs, and negative proof capable of falsifying material behavior claims.
- **State residual risk and handoff.** Separate verified, inferred, unverified, blocked, and externally owned facts, and name the owner or trigger for unresolved consequential behavior.

## Anti-Patterns

- Treat code shape, framework convention, or familiar pattern as authority for business behavior.
- Add a shared abstraction, state, dependency, or process without a current consumer, owner, and decision consequence.
- Claim completion from implementation or a green command while failure, side effects, consumers, and proof limits remain unexamined.

## Stop Conditions

Escalate unclear purpose or authority, conflicting invariants, unowned effects or consumers, changed trust/data boundaries, untestable claims, or risks owned by narrower specialists.

## Output Contract

- bounded engineering judgment with purpose and facts, objects and invariants, boundaries and side effects, reuse and placement, minimal complete change, validation evidence, and residual risk

## Targeted References

- No task-local Reference is indexed for this Skill.
