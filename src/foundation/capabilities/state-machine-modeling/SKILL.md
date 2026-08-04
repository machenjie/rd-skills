---
name: state-machine-modeling
description: "`analysis-agent`/`task-agent`/`review-agent`: use when lifecycle states, transitions, guards, or terminal states need modeling; skip when no state-machine decision exists."
---

# state-machine-modeling

## Registry Trigger

**Use when**

- model lifecycle states transitions guards side effects and terminal states

**Do not use when**

- no task-local state machine modeling decision is required

## Skill Role

Define lifecycle state meaning, transition authority, guards, concurrency, side effects, time, recovery, terminal behavior, persistence, and state-machine evidence. Exclude broad domain modeling and storage implementation.

## High-Value Rules

- **Define states by invariant and observable consequence.** Use a distinct state when allowed actions, required data, authority, side effects, or recovery differ; avoid labels that merely mirror UI steps or implementation flags.
- **Make lifecycle coverage explicit.** Show which valid conditions each state represents, how overlapping facts are resolved, and how unknown, legacy, corrupt, or partially migrated records are handled.
- **Name transition trigger and authority.** Record source state, trigger, actor or system authority, guard, target state, rejected outcome, and authoritative writer for each material transition.
- **Control concurrency and repeat delivery.** Define optimistic or pessimistic coordination, idempotency, duplicate and out-of-order triggers, stale writes, and allowed terminal results under concurrent attempts.
- **Coordinate transition and side effects.** Define compensation or reconciliation from mapped persistence, effect, acknowledgement, and crash boundaries.
- **Model time and recovery as state semantics.** Treat expiry, timeout, delayed work, cancellation, retry exhaustion, pause, resume, repair, and rollback according to authoritative clock and outcome evidence.
- **Prove transitions and forbidden paths.** Exercise valid, denied, duplicate, stale, concurrent, partial, recovery, and terminal cases, and identify legacy or external paths not represented by current evidence.

## Anti-Patterns

- Encode independent facts in one status enum until combinations become ambiguous or invalid states appear.
- Allow callers to set target state directly while bypassing trigger authority, guard, and side-effect coordination.
- Infer completion from request acceptance, timeout, or one stored flag while external effects and recovery remain unresolved.

## Stop Conditions

Escalate when state invariants overlap ambiguously, transition authority is unknown, legacy data cannot map safely, or concurrent writers cannot be coordinated. Also escalate when side effects can diverge from state, or money, permission, safety, regulated-data, or irreversible transitions lack recovery ownership.

## Output Contract

- state-machine decision with state invariants, transition authority and guards, concurrency, side-effect boundaries, time and recovery semantics, forbidden-path evidence, legacy handling, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | transition authority persistence effects or recovery ordering remains unresolved | one established lifecycle authority determines transition behavior | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects states transitions guards actors effects retries or recovery | no lifecycle state or transition behavior changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | transition denial ordering or stored-state claims need fresh proof | current writers events migrations and tests prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
