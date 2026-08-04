---
name: bigdata-product-extension
description: "For analysis/task/review agents using a Professional Skill on batch, stream, warehouse, lineage, replay, or data quality; not for transactions without distributed-data impact."
---

# bigdata-product-extension

## Role

Apply this focused Layer 3 Domain Skill to distributed pipeline decisions.
Provide `analysis-agent`, `task-agent`, and `review-agent` with
distributed-schema, replay, lineage, quality, privacy, and cost constraints for
affected pipelines and consumers.

## When To Use

- batch, stream, warehouse, data lake, distributed compute, schema evolution, or high-volume pipeline

## Do Not Use

- ordinary transactional persistence with no distributed data behavior
- single-database large-table work without a distributed pipeline, replay, or downstream consumer boundary

## Required Inputs

- producers, consumers, schema ownership, volume, latency, replay, and retention boundaries
- current storage/compute behavior, quality contract, classification policy, and validation evidence

## Professional Decision Rules

- **Prove consumer compatibility**: verify every active consumer can read the deployed schema transition.
- **Make replay correct**: prevent duplicates, omissions, and cross-window corruption during retries and backfills.
- **Gate promotion on invariants**: prevent failed required invariants from reaching affected consumers.
- **Own failed-data disposition**: name recovery behavior and an owner for every failed invariant.
- **Derive quality thresholds**: use observed distributions and consumer impact instead of fixed universal cutoffs.
- **Protect classified data**: apply current access, deletion, retention, and logging obligations across the pipeline.
- **Bound distributed resources**: use representative plans and profiles to constrain skew, spill, memory, and cost.
- **Maintain decision-relevant lineage**: trace producer, transformation, consumer, owner, and recovery evidence for affected assets.
- **Preserve experiment semantics**: prove stable assignment, event compatibility, point-in-time correctness, and applicable online/offline parity.

## High-Value Gotchas

- a compatible-looking schema change silently maps a removed or retyped field to null
- hot keys turn an acceptable average runtime into one failed long-tail partition
- a replay appends an already-processed interval and doubles downstream metrics
- late events, timezone boundaries, or mutable dimensions invalidate a backfill
- raw identifiers escape through task logs, samples, dead-letter queues, or debug exports

## Execution Checklist

1. Identify affected producers, transformations, consumers, invariants, and replay window.
2. Select compatibility, quality, recovery, and resource controls from current engine and data evidence.
3. Record negative-path tests, cost limits, escalation, and residual risk.

## Stop / Escalation Conditions

- Stop when consumer inventory, replay identity, data classification, or a production data invariant is unknown.
- Escalate irreversible backfills, regulated-data exposure, unbounded cost, and incompatible consumer transitions.

## Output Contract

- State the data invariant, required proof, selected mechanism, replay limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | distributed batch stream schema replay backfill or consumer behavior needs domain risk closure | the task changes one database table without a distributed pipeline or replay boundary | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
