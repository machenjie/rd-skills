# Domain Event Modeling Checklist

- Select the mode: new domain event, schema evolution, producer transaction boundary, consumer safety/replay, saga/audit event, or sensitive payload.
- Record source evidence: producer paths, consumer paths, schemas, registry/config, outbox/relay, generated artifacts, tests, docs, runbooks, and memory accepted or rejected.
- Name each event as a past-tense domain fact, not a command or intent.
- Define the producing aggregate/service, triggering transition, owner, and commit boundary.
- Use transactional outbox, CDC, post-commit relay, or a documented equivalent for durable publication.
- Define payload fields with type, required/optional status, stable identifiers, examples, semantics, tenant/object identifiers, and schema version.
- Classify PII, financial, health, credential, tenant, object, permission, and audit fields; restrict or tokenize sensitive payloads.
- Define the schema registry, compatibility mode, migration plan, and rollback behavior for schema changes.
- Inventory known consumers, side effects, owners, subscription mechanisms, each consumer's idempotency key and duplicate/replay handling, and DLQ owner.
- Identify unknown consumers or repository inspection/prior evidence assumptions that current source does not prove.
- Declare ordering expectations and partition or message-group key, or explicitly state that no ordering is guaranteed.
- Define retry count, backoff, poison-message behavior, DLQ destination, alert threshold, replay tool, runbook, and owner.
- Define saga role, compensation event, timeout, reconciliation path, audit fields, and retention where applicable.
- For each producer, schema, consumer, idempotency rule, ordering rule, retry/DLQ policy, replay path, privacy decision, and rollback path, map validation evidence. Record what evidence proves and does not prove, the residual-risk owner, handoff boundary, and next professional gate.
- State behavior preservation for old producers, consumers, schemas, topics/channels, replay procedures, DLQ procedures, and runbooks.
