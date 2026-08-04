---
name: architecture-style-selection
description: "`analysis-agent`: use when selecting monolith, modular, layered, service, event-driven, or hybrid architecture; skip when no style decision is required."
---

# architecture-style-selection

## Registry Trigger

**Use when**

- select monolith modular layered service event driven or hybrid architecture style

**Do not use when**

- no task-local architecture style selection decision is required

## Skill Role

Select the least complex architecture style that satisfies current ownership, change, data, reliability, regulatory, and delivery constraints.

## High-Value Rules

- Select the simplest style that satisfies current constraints without relying on preference, fashion, or speculative scale.
- Choose a service or distributed boundary only when independent lifecycle, deployment, scaling, failure isolation, regulation, or ownership outweighs network, consistency, and operating cost.
- Compare viable alternatives across material forces, including the required rejected-alternative rationale.
- When the chosen style changes an existing boundary, define migration, coexistence, freeze, recovery, and deletion decisions only where the transition can expose mixed state or irreversible cost.
- Approve a new runtime responsibility only with a capable owner and consequence-derived controls, omitting unrelated operational bundles.
- Align architecture boundaries with current change authority and communication paths; reject distribution used to mask unclear module ownership or unenforced dependencies.

## Anti-Patterns

- A modular monolith without enforced ownership and dependency direction can decay into a coupled monolith.
- A service split without data authority and failure semantics creates a distributed monolith.
- Organization structure is evidence about sustainable ownership, not a universal command to mirror the current org chart.
- Platform capability gaps change the cost and feasibility of a distributed option; they do not automatically select or reject it.

## Stop Conditions

Escalate when a style decision materially changes deployment, data ownership, regulated or failure boundaries, operating responsibility, vendor exit, or rewrite-versus-evolve cost. Also escalate when its owner, constraints, alternatives, or transition evidence is missing. Derive the escalation owner and evidence depth from current governance and consequence rather than a fixed title, workload threshold, or schedule.

## Output Contract

- architecture style decision with forces tradeoffs constraints selected style operating owner transition migration coexistence freeze recovery deletion retirement evidence proof limits and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Runtime boundary, migration, and reversibility forces leave competing styles | Current constraints already require the least-complex viable style | analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Style choice changes data ownership, deployability, or failure isolation | No system-wide boundary or operating model changes | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Style justification depends on current topology or operational readiness | No topology, migration, or readiness claim requires proof | analysis-agent | evidence-record, proof-limit, residual-risk |
