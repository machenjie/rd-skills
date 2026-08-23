# Version Compatibility Evidence Patterns

Use this evidence-pattern Reference only when a compatibility claim needs current consumer, old/new, retirement, rollback, or proof-limit evidence.

## Evidence Records

| Claim | Minimum current evidence | Explicit limit |
| --- | --- | --- |
| API/DTO | Schema diff, structure/meaning/default/error review, consumer list, and contract fixture. | Unknown consumers, generated clients, and partners remain unproved. |
| Event/schema | Registry mode, producer-consumer matrix, replay fixture/window, and consumer inventory. | Lagged consumers, DLQ behavior, and unregistered schemas remain unproved. |
| Data/config rollback | Reader-writer matrix, config bridge/precedence, migration phase, rollback query, and release order. | Production distributions or deployment skews not represented by this evidence remain proof limits. |
| SDK/package/export | Public/generated API diff, semver decision, downstream compile/test, and change note. | Unpublished consumers or language runtimes not exercised by this evidence remain proof limits. |
| Retirement | Usage telemetry, threshold/window, notification/approval, owner, and removal validation. | Future or uninstrumented use remains unproved. |
| Reused evidence | Current source, generated artifacts, telemetry, accepted/rejected prior evidence, validator/report, and final-edit freshness. | Later contract, client, config, topic, or deployment edits invalidate it. |

## Evidence Status And Authority

- Strong evidence inspects current contracts, consumers, generated artifacts, telemetry, migration/config paths, tests, freshness, and proof limits.
- Record weak or missing local-only searches, docs-only removal, schema-only diffs, happy-path fixtures, stale reports, absent matrices, rollback gaps, unknown consumers, or ownerless claims instead of treating them as closure.
- When old code cannot read new state, strict consumers lack unknown handling, or a breaking change uses an incompatible version class, record the evidence as invalid.
- For telemetry, registry, flag, migration, notification, or rollback actions, record owner, scope, permission, dry-run/staging proof, stop, recovery, and redaction.

## Anti-Patterns

- Do not assume consumers upgrade together, call behavior-changing additions safe, or remove a bridge by calendar without usage, stored-data, queue, and rollback evidence.
