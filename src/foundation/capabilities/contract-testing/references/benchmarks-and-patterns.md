# Contract Compatibility Decision Patterns

Compare proof strategies against the actual boundary:

- **Request/response:** provider verification plus named consumer parsing/behavior for absent/null/default, errors/authorization, unknown values, ordering, and pagination.
- **Event/retained message:** structural rule plus old/new writer-reader, replay, duplicate, stable-identifier, and retained-payload cases.
- **Generated client:** regenerate and compile/execute named generator/runtime versions and affected calls.
- **External provider/webhook:** replay redacted provenance-bearing captures and state unobserved signing, partial, error, and drift behavior.
- **Independent consumer:** exercise named coexistence/release-order cases and retain unknown-consumer risk.

Name provider, consumers, authoritative schema or observed fixture, versions, compatibility direction/policy, retention/replay source, and rollout order. Select structural versus semantic proof explicitly: schema shape cannot prove meanings or consumer tolerance. Exercise old readers with new values and new readers with retained old payloads; preserve identifiers and migration meaning until current consumer/replay evidence and rollback permit removal.

Bound provider checks to the named expectations, captures to source/version/environment/time, and contract tests to the modeled transport/persistence/timing behavior. Return the option comparison, selected approach, rejected strategies, and proof limits.
