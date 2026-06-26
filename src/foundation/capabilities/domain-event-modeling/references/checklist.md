# Domain Event Modeling Checklist

- Select the mode: new domain event, schema evolution, producer transaction boundary, consumer safety/replay, saga/audit event, or sensitive payload.
- Record source evidence: producer paths, consumer paths, schemas, registry/config, outbox/relay, generated artifacts, tests, docs, runbooks, and memory accepted or rejected.
- Name each event as a past-tense domain fact, not a command or intent.
- Define the producing aggregate/service, triggering transition, owner, and commit boundary.
- Use transactional outbox, CDC, post-commit relay, or a documented equivalent for durable publication.
- Define payload fields with type, required/optional status, stable identifiers, examples, semantics, tenant/object identifiers, and schema version.
- Classify PII, financial, health, credential, tenant, object, permission, and audit fields; restrict or tokenize sensitive payloads.
- Define the schema registry, compatibility mode, migration plan, and rollback behavior for schema changes.
- Inventory known consumers, side effects, owners, subscription mechanisms, idempotency method, and DLQ owner.
- Identify unknown consumers or graph/memory assumptions that current source does not prove.
- Define idempotency key and duplicate/replay handling per consumer.
- Declare ordering expectations and partition or message-group key, or explicitly state that no ordering is guaranteed.
- Define retry count, backoff, poison-message behavior, DLQ destination, alert threshold, replay tool, runbook, and owner.
- Define saga role, compensation event, timeout, reconciliation path, audit fields, and retention where applicable.
- Map each producer, schema, consumer, idempotency rule, ordering rule, retry/DLQ policy, replay path, privacy decision, and rollback path to validation.
- State behavior preservation for old producers, consumers, schemas, topics/channels, replay procedures, DLQ procedures, and runbooks.
- Record what evidence proves, what it does not prove, residual risk, owner, handoff boundaries, and next professional gate.
