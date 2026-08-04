---
name: scenario-decomposition
description: "`analysis-agent`: use when a request needs normal, failure, edge, abuse, recovery, or operational scenarios; skip when no scenario-decomposition decision exists."
---

# scenario-decomposition

## Registry Trigger

**Use when**

- any applicable task-local scenario category requires decomposition

**Do not use when**

- no task-local scenario decomposition decision is required

## Skill Role

Define the smallest scenario set that exposes material behavior, boundary states, failure mechanisms, abuse, recovery, and operational consequences. Exclude detailed use cases and test portfolios.

## High-Value Rules

- **Start from changed behavior and consequence.** Name actor or trigger, pre-state, action, expected state or effect, and why a deviation matters before expanding scenarios.
- **Partition by distinct decision or failure mechanism.** Add a scenario when it changes authority, invariant, state transition, side effect, recovery, consumer, or observable oracle; avoid generic category completion.
- **Cover material boundary states.** Include missing, empty, minimum or maximum, duplicate, stale, conflicting, partial, denied, and unsupported conditions only where the affected contract distinguishes them.
- **Model time and concurrency where reachable.** Expose timeout, cancellation, replay, reordering, simultaneous action, late result, retry exhaustion, and mixed-version behavior that can change the terminal state.
- **Include abuse at changed trust boundaries.** Trace untrusted input, identity or tenant confusion, resource amplification, disclosure, and bypass paths, then route deeper attacker analysis to the security owner.
- **Describe recovery and operations as outcomes.** Capture detection, containment, retry or reconciliation, rollback or forward repair, cleanup, ownership, and unresolved state without prescribing a universal incident process.
- **Keep traceability explicit.** Link each retained scenario to current rule or contract evidence, an observable oracle, and the Professional or Foundation owner that decides implementation or proof.

## Anti-Patterns

- Produce a broad happy, sad, and edge catalog with no task-specific decision or failure mechanism.
- Treat every hypothetical combination as equally important or omit a consequential negative path because the normal flow is clear.
- Turn scenario decomposition into UI choreography, test commands, or a fixed operational checklist.

## Stop Conditions

Escalate when changed behavior, authoritative rule, initial state, consequential side effect, trust boundary, or observable terminal state is unknown. Also escalate when money, permission, safety, regulated data, destructive action, or irreversible external effects lack an accountable scenario owner.

## Output Contract

- primary scenario with trigger, pre-state, decision, observable postcondition, acceptance mapping, traceable oracle, and proof limits
- applicable task-local failure, abuse, recovery, and operational paths only
- considered-but-excluded task-local category with cited omission or non-applicability rationale
- residual scenario-risk owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | active slice risk leaves scenario coverage or criticality unresolved | accepted scenario model covers every triggered failure category | analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | a task-local scenario trigger lacks an applicable scenario or evidence-backed omission rationale | current scenario set maps every triggered path to verification | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | scenario relevance freshness or release-critical claims need current proof | current source and validators substantiate every retained scenario | analysis-agent | evidence-record, proof-limit, residual-risk |
