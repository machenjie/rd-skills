# Example Output

```markdown
## Domain Event Catalog

mode_selected: new domain event

boundaries_inspected:
- Producer: `src/export/worker.py`
- Consumer candidates: notification service, audit service, reporting projection
- Schema/config: no registry entry found yet
- Prior memory: export completion event mentioned in design notes; accepted only as a naming hint

source_evidence:
- Export worker commits file metadata before emitting the event.
- No current consumer requires mutable callback to reconstruct the completed export.

graph_memory_trajectory_judgment:
- Repository graph confirms one producer and three intended consumers.
- Memory is not sufficient proof of active consumers; consumer registration remains a validation item.

event_catalog:
- event_name: `ExportCompleted`
- event_type: `reporting.export.ExportCompleted.v1`
- owner: reporting platform
- lifecycle_status: proposed

fact_semantics:
- A monthly export finished and a downloadable file is available after file metadata commit.

producer:
- Service: export worker
- Trigger: export generation command reaches `completed` transition
- Owner: reporting platform

commit_boundary:
- Write export metadata and outbox row in the same database transaction.
- Relay publishes after commit; direct broker publish from the worker is rejected.

payload_schema:
- `eventId`: UUID, required, producer-generated
- `eventType`: string, required, `reporting.export.ExportCompleted.v1`
- `aggregateType`: string, required, `Export`
- `aggregateId`: string, required, export id
- `tenantId`: string, required, routing and authorization
- `reportingPeriod`: string, required, ISO month
- `fileId`: string, required, scoped file reference
- `completedAt`: datetime, required, ISO 8601 UTC
- `schemaVersion`: integer, required, `1`

schema_version:
- Current: v1
- Compatibility: additive-only minor changes
- Registry: to be added before release

consumer_inventory:
- Notification service: sends analyst notification; idempotency key `eventId`; DLQ owner notifications.
- Audit service: records immutable export completion; idempotency key `eventId`; DLQ owner audit.
- Reporting projection: updates export list; idempotency key `aggregateId + schemaVersion`; DLQ owner reporting.

ordering_expectation:
- Per export ordering only; partition key `aggregateId`.

retry_policy:
- Max retries: 3
- Backoff: exponential with jitter
- Poison schema errors: route directly to DLQ

dead_letter_strategy:
- DLQ topic: `reporting.export.completed.dlq`
- Alert: depth > 10 or oldest age > 5 minutes
- Replay owner: reporting platform

audit_impact:
- Audit-significant; preserve tenant, actor/source if available, export id, file id, and completed timestamp.

privacy_classification:
- No raw PII in payload; file access remains scoped by `fileId`.

saga_role:
- none

event_to_validation_map:
- Outbox durability: transaction test.
- Schema compatibility: registry compatibility check.
- Duplicate delivery: consumer idempotency fixtures.
- Out-of-order delivery: projection fixture for repeated export state.
- DLQ routing: forced deserialization and dependency-failure fixtures.

reuse_and_placement_rationale:
- Reuse existing export metadata table and outbox relay; do not add a new service.

behavior_preservation:
- Existing export generation remains synchronous until outbox relay publishes.

validation_evidence:
- Not verified yet; planned validators and tests listed above.

handoff_boundaries:
- `message-queue-design` for topic naming and broker binding.
- `security-privacy-gate` if payload adds actor email or customer identifiers.

evidence_limits:
- Unknown whether all consumers are registered in current config.
- Large replay and production DLQ behavior not proven.
- Residual risk owner: reporting platform.
```
