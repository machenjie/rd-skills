# Consumer Impact Strategy Comparison

Compare each option against structure, meaning, validation, defaults, errors, timing/order, persistence/rollback, generated output, and retained data or messages.

- **Additive optional:** preserve semantics and unknown-field tolerance.
- **Bridge/alias:** accept old/new names with explicit mapping and precedence.
- **Expand/migrate/contract:** separate compatibility, migration, telemetry, and cleanup.
- **Version:** isolate breaking behavior; pair SemVer or Sunset signaling with migration guidance.
- **Upcaster/adapter:** version and deterministically map old events, data, or generated models.
- **Flag/opt-in:** retain the old default and an owned rollback.
- **Dual publish/write:** define duplicates, reconciliation, and removal.
- **Configuration bridge:** support old/new keys and defaults through rolling restart.
- **No-ship:** select when no bounded compatible path is proved.

Exercise old-producer/new-consumer, new-producer/old-consumer, rollback readers after new writes, delayed consumers with retained/replayed messages, and generated clients against providers. Structural OpenAPI, AsyncAPI, Protobuf, or registry checks prove only their configured shape and reader/writer mode; separately prove semantics and rollout order.

Bound external, generated, mobile, partner, copied, package, dashboard, and dynamic consumers with inventory, compile/replay/telemetry evidence, and gaps. Return option comparison, selected approach, rejected alternatives, and proof limits.
