# Pipeline, Replay, and Event Identity

Use this Reference only for the named BigData pipeline-replay-and-event-identity decision.

## Decision Rules

- Define batch, stream, snapshot, incremental CDC, full-refresh, and hybrid boundaries, including the snapshot-to-log cutover position, transaction ordering, handoff, checkpoint, recovery, and authoritative output.
- When event time or delayed or corrected events affect correctness, choose event-time authority, clock semantics, watermark, allowed lateness, finalization, and correction behavior. Replay and consumer requirements bound retraction and retention.
- Define event identity, partition ordering, deduplication, checkpoint commit, retry, and replay semantics. For CDC, preserve transaction boundaries, tombstones, and deletion propagation. Scope exactly-once claims to named engine or storage boundaries and close external side-effect crash windows.
- Assign writer ownership across live processing, backfill, correction, and replay. Define precedence, interruption, resume, overlap detection, and reconciliation so resumed work cannot overwrite a later authoritative correction.
