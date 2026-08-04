# Contract Compatibility Decision Patterns

These patterns select scoped compatibility proof without treating one mechanism as universal.

## Select Proof From The Boundary

| Surface at risk | Easy-to-miss incompatibility | Scoped proof |
| --- | --- | --- |
| Request or response | absent/null/default differences, error and authorization shape, unknown fields, ordering, pagination | provider verification plus representative consumer parsing or behavior |
| Event or retained message | reader/writer direction, field identity, replay, duplicate delivery, old payloads | changed schema check plus old/new producer-consumer and retained-payload cases |
| Generated client | generator/runtime version, closed enums, deserialization, call-site adoption | regenerate and compile or execute named client versions and affected calls |
| External provider or webhook | documented behavior differs from observed behavior, signing, partial payloads, capture drift | redacted provenance-bearing fixture replay plus stated unobserved behavior |
| Independently deployed consumer | unknown release order, long-lived installation, hidden dependency | named coexistence matrix and explicit unknown-consumer residual risk |

## Mixed-Version Pattern

1. Name versions that can coexist and which side reads or writes each representation.
2. Record the authoritative schema or observed fixture, compatibility policy, retention or replay source, and rollout order.
3. Exercise semantic branches consumers use, including old readers receiving new values and new readers receiving retained old payloads.
4. Preserve stable identifiers and migration meaning until the consuming population or retained data no longer needs them.
5. Remove compatibility paths only with current consumer and replay evidence plus an owned rollback or recovery path.

## Decision Boundaries

- Schema shape checks structural evolution; semantic compatibility still needs named provider and consumer behavior.
- Provider verification closes named expectations; consumer discovery and production adoption remain separate claims.
- Captured provider behavior is evidence for its source, version, environment, and capture time, not an evergreen specification.
- Contract tests route real transport, persistence, timing, and deployment interaction to integration or journey proof.
