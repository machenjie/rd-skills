# Contract Evolution Choice Check

**Load when:** a schema, API, event, version, migration, list/expansion, filter, or compatibility design has a material consumer, data-growth, or recovery tradeoff.

**Do not load when:** the change is demonstrably additive and bounded with no affected consumer, storage, query, migration, or coexistence decision.

Derive thresholds from the current repository baseline, representative workload, user/business objective, platform policy, and measured evidence; pagination, versioning, indexing, and migration techniques are candidates, not defaults.

## Decision Questions

1. Which known or indirect consumers and data shapes are affected, and what payload/query/validation cost appears at current and expected scale?
2. What does the actual datastore and deployment model imply for locks, backfill, index/build cost, version skew, and old/new coexistence?
3. Is pagination, expansion limiting, projection, indexing, versioning, tolerant reading, or a compatibility shim needed for a demonstrated boundary, and what evidence selects it?
4. What rollback, forward-repair, or irreversible migration outcome is credible for the affected data, and which duration or impact limit comes from current policy and measured operations?
5. If consumer, storage, and operational tradeoffs cannot be bounded locally, identify `solution-optimality-evaluation` as the broader owner without assuming this reference loads it.
