# Transaction Consistency Checklist

- For a transaction boundary under review, name the business or consistency invariant that determines its atomic scope; split or remove a boundary with no such invariant.
- For the named invariant, define the minimal data and operations required to commit atomically.
- Verify the selected isolation, lock, conflict, timeout, connection, datastore, and replica-read boundary, including read-your-writes and stale-read recovery derived from replication guarantees and the named invariant.
- Choose remote-call and commit ordering from the invariant, external protocol, lock and latency evidence, failure window, and available compensation or reconciliation.
- Choose optimistic checks, locks, constraints, conditional writes, or serialization from anomaly, contention, latency, and storage guarantees, with concurrent uniqueness races, conflict visibility, and recovery covered where relevant.
- Place selected deadlock or serialization retry at an idempotent outer boundary that can rerun the complete transaction with fresh reads.
- Derive the retry budget and delay from contention, deadline, and datastore signals.
- Return the defined terminal conflict after that budget is exhausted.
- When an after-commit callback or equivalent hook starts an external effect, treat the committed transaction outcome as fixed. Expose callback failure, assign durable retry or reconciliation ownership, and make replay safe against duplicate effects and stale payloads.
- When an invariant crosses transaction managers, select a distributed transaction, local transaction plus event, outbox, saga, compensation, or reconciliation from participant guarantees and recovery evidence, with uncovered failure windows and owners recorded.
- Select anomaly and failure tests triggered by the named invariant and topology.
- Record unrun paths with their reason.
