# Domain Event Modeling Benchmarks And Patterns

Load this reference when a durable fact, producer commit boundary, event schema, consumer/replay behavior, or payload policy changes. Do not load it for commands, transient internal notifications, or broker topology with no domain fact decision.

## Event Classification

| Class | Use when | Required owner/proof |
| --- | --- | --- |
| Domain event | A meaningful fact inside one bounded context becomes true. | Aggregate/context owner, fact boundary, durable history need, and internal consumers. |
| Integration event | A stable fact crosses a bounded-context or external contract. | Public schema/version owner, consumer inventory, compatibility and retirement. |
| Notification event | A fact triggers user/operator communication. | Source fact, minimized payload, delivery/retry owner, and privacy rules. |
| Audit record | Actor/action/subject evidence has append-only retention/access obligations. | Audit authority, immutability, access, retention, and correction semantics. |
| Analytics event | Measurement is not domain state authority. | Metric/grain owner, consent/minimization, dedupe, and deletion behavior. |
| CDC record | Committed storage change is the intended integration input. | Connector/offset/schema/tombstone owner and mapping from row change to meaning. |
| Workflow/Saga event | A durable step or compensation fact coordinates long work. | Correlation, timeout, compensation, stuck detection, and version owner. |

Name facts after what became true and state exactly when truth begins. Command-like names express intent, not an event. A derived fact names its source fact and transformation owner.

## Commit, Delivery, And Consumer Contract

- When state and publication must agree, persist an outbox or equivalent durable handoff in the state transaction.
- Consider CDC only when its offset, mapping, tombstone, and replay ownership fit.
- Require equally strong failure and recovery evidence for direct publish.
- The envelope carries stable event identity, source/type/schema reference, occurred time, subject/aggregate identity, tenant/routing scope when required, and correlation/causation context. Include only facts consumers need; exclude credentials, unnecessary PII, unbounded arrays, and mutable snapshots used as a substitute for a fact.
- Dedupe consumers at the durable side-effect boundary.
- Choose event identity, aggregate sequence, workflow step, or a natural unique business key from the current invariant.
- Do not treat broker “exactly once” as exactly-once payment, email, webhook, file, or ledger effects.
- Define the ordering boundary—aggregate, tenant, workflow, or none—and connect it to partition or message-group key and consumer concurrency. Global ordering remains a costly candidate rather than a default.
- Classify transient, rate/quota, poison-schema, duplicate, delayed/out-of-order, and unknown-outcome failures. Each applicable class gets bounded retry or immediate quarantine, an owned terminal state/DLQ, safe diagnostics, and a controlled replay path.

## Evolution, Replay, And Proof

Additive fields are compatible only when old consumers tolerate absence/defaults and new consumers tolerate old producers. Required/removed/renamed/type/semantic changes need a current compatibility strategy such as dual read/write, a new event type/version, consumer migration, or an explicitly accepted break. Verify mixed producer/consumer versions, generated artifacts, replay/backfill, and rollback.

Replay-safe projections may rebuild from durable history; irreversible consumers require a replay gate, dedupe, or a different repair path. Saga compensation is ordered, idempotent, reconcilable, and owned. Deletion, visibility, tenant, and privacy changes propagate within their current policy window.

Source and contract inspection do not prove broker acknowledgement, live ordering, production lag, consumer completeness, provider side effects, or replay at scale. State which producer/schema/consumer paths and runtime behaviors remain unverified.

Reject event-before-commit, command-shaped events, and unowned outbox or DLQ paths.
Reject callback-dependent mutable payloads and schema edits without consumer evidence.
Reject irreversible-effect replay without a gate and sensitive data copied “for convenience.”

Route lifecycle legality to `state-machine-modeling`.
Route topology and backpressure to `event-driven-architecture` or `message-queue-design`.
Route commit and compensation to `transaction-consistency` and schema rollout to `version-compatibility`.
Route privacy to `security-privacy-gate`.
Route operational lag and replay proof to `reliability-observability-gate`.
