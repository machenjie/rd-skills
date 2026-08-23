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

- Close triggered compatibility, replay, promotion, failed-data, quality, classification, resource, lineage, and experiment risks through named References and current pipeline evidence.

## High-Value Gotchas

- Schema appearance, averages, or file presence can hide semantic incompatibility, skew, duplicate replay, late data, or classified-data leakage.

## Execution Checklist

1. Identify affected producers, transformations, consumers, invariants, and replay window.
2. Load each named Reference whose decision problem is active.
3. Record mechanisms, negative paths, cost limits, proof limits, and residual risk.

## Stop / Escalation Conditions

- Stop when consumer inventory, replay identity, data classification, or a production data invariant is unknown.
- Escalate irreversible backfills, regulated-data exposure, unbounded cost, and incompatible consumer transitions.

## Output Contract

- State the data invariant, required proof, selected mechanism, replay limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [consumer and schema contracts](references/consumer-and-schema-contracts.md) | targeted | distributed consumer, schema, grain, metric meaning, correction, or compatibility is open | the task changes one database table without a distributed pipeline or replay boundary | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, residual-risk |
| [pipeline replay and event identity](references/pipeline-replay-and-event-identity.md) | targeted | batch, stream, CDC, event-time, checkpoint, replay, backfill, or writer coexistence is open | no pipeline, replay, backfill, checkpoint, or writer-coexistence decision exists | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, failure-decision, residual-risk |
| [quality lineage and point in time correctness](references/quality-lineage-and-point-in-time-correctness.md) | targeted | quality, failed-data, lineage, point-in-time, leakage, or experiment semantics is open | no quality, lineage, point-in-time, leakage, or experiment decision exists | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan, residual-risk |
| [storage performance and recovery](references/storage-performance-and-recovery.md) | targeted | partition, storage, metadata, recovery, skew, state, memory, compute, or cost is open | no storage, recovery, resource, performance, or cost decision exists | analysis-agent, task-agent, review-agent | selected-approach, failure-decision, validation-plan, residual-risk |
| [observability and privacy](references/observability-and-privacy.md) | targeted | pipeline signals or classified samples, logs, failed data, exports, retention, or deletion is open | no pipeline-observability or classified-data handling decision exists | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, residual-risk |
