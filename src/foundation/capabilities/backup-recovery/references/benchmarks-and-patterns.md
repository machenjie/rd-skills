# Backup Recovery Decision Patterns

These patterns compare recovery-unit, objective, artifact, dependency, and failure-isolation decisions.

## Recoverable State And Failure Model

| Decision | Easy-to-miss boundary | Scoped proof |
| --- | --- | --- |
| Recovery unit | authoritative records, files, keys, config, identity, offsets, derived views, and compatible code | dependency graph plus source/rebuild authority for each component |
| Recovery objective | tolerated loss and outage differ by failure scenario, tenant scope, and consequence | accountable objective source plus achieved exercise result and gap |
| Capture consistency | components may be captured at different transaction or checkpoint positions | quiesce, checkpoint, replay, fencing, or reconciliation behavior |
| Artifact lineage | snapshot or log may need older schema, key, runtime, and tool versions | artifact identity, capture point, key/schema lineage, and restore target |
| Failure isolation | replication can copy deletion or corruption; shared credentials can erase copies | selected operator/provider/attacker failure boundary and surviving source |
| Restore order | identity, keys, data, files, config, applications, indexes, and consumers may have prerequisites | ordered restore with readiness and reversal conditions |
| Validation | command success can leave semantic corruption or missing side effects | domain invariants, reconciliation, and representative business behavior |
| Retention and expiry | key removal, erasure, legal hold, and late replay can conflict | policy source, retained lineage, deletion behavior, and residual owner |

## Selection Notes

- Choose full, incremental, log, snapshot, versioned-copy, rebuild, or another mechanism from the recovery unit and failure model rather than from a universal copy rule.
- Select isolated or immutable copies when the named operator, credential, provider, or attacker path can destroy ordinary recovery sources.
- Exercise enough dependency scope and data shape to expose order, throughput, key access, and reconciliation limits; disclose production-scale or region behavior not exercised.
- Revisit the recovery proof after material schema, key, configuration, dependency, retention, region, or volume change.
