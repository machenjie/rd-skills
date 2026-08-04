# Big Data Product Extension Checklist

- Identify authoritative source systems, sinks, owners, freshness contracts, classified fields, and downstream consumers for affected assets.
- Make metric meaning explicit: grain, dimensions, filters, time-zone and calendar rules, aggregation, correction, and consumer-visible null or default behavior.
- Separate structural compatibility from semantic consumer compatibility. Treat changes to grain, meaning, units, defaults, ordering, or correction as contract changes, and cover active readers plus replay within the compatibility window.
- Define batch, stream, snapshot, incremental CDC, full-refresh, and hybrid boundaries, including the snapshot-to-log cutover position, transaction ordering, handoff, checkpoint, recovery, and authoritative output.
- When event time or delayed or corrected events affect correctness, choose event-time authority, clock semantics, watermark, allowed lateness, finalization, and correction behavior. Replay and consumer requirements bound retraction and retention.
- Define event identity, partition ordering, deduplication, checkpoint commit, retry, and replay semantics. For CDC, preserve transaction boundaries, tombstones, and deletion propagation. Scope exactly-once claims to named engine or storage boundaries and close external side-effect crash windows.
- Assign writer ownership across live processing, backfill, correction, and replay. Define precedence, interruption, resume, overlap detection, and reconciliation so resumed work cannot overwrite a later authoritative correction.
- Preserve point-in-time correctness for mutable dimensions and features without temporal leakage, using backfill and live-coexistence validation against authoritative totals and representative historical snapshots.
- Define quality invariants for completeness, uniqueness, validity, referential integrity, distributions, row counts, and semantic drift. Consumer impact and replay capability determine failed-data disposition.
- Record lineage from source and schema through transformation, storage, dashboard, model, and API consumers, owner, deployment version, and recovery evidence.
- For partitioned, file-based, table-format, or stateful processing, derive keys, layout, compaction, metadata and manifest lifecycles, and state evolution. Observed cardinality, access, skew, small-file growth, and state-store growth constrain the choice.
- Prove metadata, manifests, snapshots, or checkpoints are recoverable before claiming the data files are restorable.
- Inspect representative joins, repartitioning, scans, state, spill, memory, storage, and compute cost as evidence for pruning, clustering or indexing, retention, compaction, and query controls.
- Monitor freshness, lag, volume, bad records, task failure, state or partition growth, replay or backfill progress, correction debt, quality drift, and cost. Each signal has bounded labels, an alert owner, and a recovery action.
- Apply data classification to samples, logs, dead-letter or quarantine records, temporary storage, exports, and human-review or evaluation stores. Applicable policy and debugging needs determine access, retention, deletion, masking, tokenization, isolation, or exclusion.
