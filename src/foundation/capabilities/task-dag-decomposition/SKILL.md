---
name: task-dag-decomposition
description: "Analyze candidate task nodes, dependencies, collisions, and critical path before a consumer accepts or rejects a final DAG."
---

# task-dag-decomposition

## Registry Trigger

**Use when**

- two or more candidate work units may form a graph, but node or edge evidence is unresolved;
- dependency, collision, resource-contention, critical-path, or parallel-opportunity claims need pre-DAG analysis.

**Do not use when**

- one acceptance outcome and produced output cannot be separated into useful candidates;
- a consumer has already accepted the authoritative graph and needs execution planning.

## Skill Role

Analyze nodes and edges as advisory pre-DAG candidate graph evidence that a consumer accepts or rejects. This Skill does not emit the final Task DAG or schedule execution.

## Inputs

- acceptance outcomes and candidate produced outputs;
- current evidence for producer-consumer relationships, contracts, and order constraints;
- candidate read, write, shared-resource, and collision surfaces;
- available duration estimates, units, sources, and uncertainty about nodes, edges, ownership, resources, or timing.

## High-Value Rules

1. Propose a candidate node only when it owns an acceptance-linked outcome and produced output.
2. Classify every proposed dependency as a data edge, control edge, contract edge, or order edge.
3. Pair each proposed edge with current evidence and its downstream blocker before accepting it.
4. Record rejected edges with evidence that preference, proximity, or chronology is nonblocking.
5. Map collision, shared-write, and resource surfaces across files, generated outputs, contracts, schemas, fixtures, stores, queues, and external resources.
6. Derive the candidate critical path from supported edges and evidence-backed durations in one time unit. Without duration evidence, report dependency order and mark timing unknown.
7. Identify parallel opportunity only where no supported path dependency exists. Retain collision and resource evidence for the consumer.
8. Detect cycles and ambiguous output ownership; record unresolved facts as uncertainty. State proof limits and residual risk for every material graph conclusion.

## Anti-Patterns

- Different file paths do not by themselves eliminate a collision.
- Chronology, preference, or architectural proximity does not by itself prove an edge.
- More nodes do not improve a graph when outputs or acceptance outcomes are duplicated.
- Absence of a supported edge does not establish an executable parallel schedule.

## Execution Checklist

1. Map each candidate node to its acceptance-linked outcome and produced output.
2. Classify and source every proposed edge.
3. Record rejected edges and cycles.
4. Map collision, shared-write, and resource surfaces.
5. Record duration evidence or timing unknown. Identify parallel opportunity separately.
6. Return uncertainty, proof limits, and residual risk for consumer acceptance or rejection.

## Stop Conditions

- Return insufficient node evidence when a candidate cannot bind both an outcome and an output.
- Return insufficient edge evidence when a proposed dependency lacks a current source or downstream blocker.
- Return a cyclic or uncertain graph when supported edges form a cycle or resource identity remains unresolved.

## Output Contract

- candidate-graph evidence with acceptance-linked nodes, produced outputs, evidence-backed data/control/contract/order edges, rejected edges, and collision/shared-write/resource surfaces. Include a candidate critical path with duration evidence or timing unknown, parallel opportunity, cycles, uncertainty, proof limits, and residual risk for consumer acceptance or rejection

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [candidate graph evidence](references/candidate-graph-evidence.md) | evidence-pattern | candidate nodes edges collisions cycles critical path or parallel opportunity need source-backed comparison | candidate graph evidence and requested timing or parallel-opportunity conclusions are resolved with proof limits | analysis-agent | evidence-record, proof-limit, residual-risk |
