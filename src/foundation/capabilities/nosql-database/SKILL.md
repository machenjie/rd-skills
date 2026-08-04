---
name: nosql-database
description: "`task-agent`: use when document, key-value, wide-column, or graph storage changes access, partitioning, consistency, or evolution; skip vendor-only mentions and unchanged storage."
---

# nosql-database

## Registry Trigger

**Use when**

- design document key value wide column or graph storage access patterns partitioning and consistency

**Do not use when**

- a vendor or NoSQL term appears without a changed access, key, consistency, or storage contract
- only cache, search, queue delivery, or relational behavior changes
- no task-local nosql database decision is required

## Skill Role

Define non-relational access paths, distribution, consistency, keys, and stored-shape evolution. Exclude business meaning, adapters, caching, search, queues, and transaction protocols.

## High-Value Rules

- Map named reads, writes, deletes, ranges, scans, and unknown consumers to supported store, key, embedding, or index operations, exposing fallback scans and fan-out.
- Design partitions from peak distribution and growth, testing skew and bounds before selecting split, bucket, overflow, or repartition behavior.
- Classify each invariant as item or document-local, partition-local, or cross-boundary. The proof covers actual conditional-write, transaction, read-consistency, and replica guarantees, plus stale-read and read-your-writes behavior.
- Define concurrent and unknown outcomes across version ownership, reordered or duplicate writes, conflict policy, retries, partial effects, and reconciliation.
- Give each denormalized field and projection an authoritative writer, propagation and delete/visibility order, accepted staleness, drift signal, replay source, and repair/rebuild path. Query convenience does not make a derived copy authoritative.
- Define compatible reader/writer evolution across versions, defaults, unknown fields, backfill/index effects, rollback, and oldest replayable data.
- Derive TTL, tombstone, compaction, retention, capacity, and quota from policy, replay/recovery windows, skew, configuration, and late-replay behavior.

## Anti-Patterns

- Selecting a store family from an entity diagram, brand, or average throughput before proving access paths and worst-case distribution.
- Calling data schemaless while old items, deleted fields, index projections, or mixed writers have no compatibility and repair contract.
- Treating a convenient filter/scan, eventually consistent projection, or TTL expiry as safe without bounding fan-out, stale decisions, protected records, and late replay.

## Stop Conditions

Stop when unknown store guarantees, writer authority, partition distribution, cross-boundary invariants, replay, or repair can change correctness. Local evidence does not prove production skew, quotas, cost, global consistency, or restore behavior.

## Output Contract

- NoSQL decision naming access paths, keys/partitions, invariant consistency, evolution and retention semantics, repair, limits, and adjacent handoffs.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Access consistency partition denormalization or evolution forces leave multiple viable designs | Named workload invariants and deployed-store guarantees select one bounded design | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Change affects access paths keys partitions consistency copies versions retention quotas or repair | No NoSQL access invariant or stored-shape contract changes | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Distribution staleness evolution retention or repair claims need current evidence | Current workload telemetry schemas configuration and tests prove each bounded claim | task-agent | evidence-record, proof-limit, residual-risk |
