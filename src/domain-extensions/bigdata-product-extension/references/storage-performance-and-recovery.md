# Storage, Performance, and Recovery

Use this Reference only for the named BigData storage-performance-and-recovery decision.

## Decision Rules

- For partitioned, file-based, table-format, or stateful processing, derive keys, layout, compaction, metadata and manifest lifecycles, and state evolution. Observed cardinality, access, skew, small-file growth, and state-store growth constrain the choice.
- Prove metadata, manifests, snapshots, or checkpoints are recoverable before claiming the data files are restorable.
- Inspect representative joins, repartitioning, scans, state, spill, memory, storage, and compute cost as evidence for pruning, clustering or indexing, retention, compaction, and query controls.
