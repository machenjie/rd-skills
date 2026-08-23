# Compatibility Mechanism Benchmarks

Use this benchmark-pattern Reference only when a mixed-version migration mechanism remains unresolved.

## Change Classification

| Change | Breaking condition | Required treatment |
| --- | --- | --- |
| Optional field or operation | Semantics/defaults are not additive or consumers reject unknowns. | Prove old parser/client behavior. |
| Required, removed, or renamed surface | A current producer or consumer depends on the old shape. | Bridge/alias, version, deprecation, and telemetry-gated removal. |
| Type, format, meaning, or default | Interpretation changes despite compatible shape. | New field/version or mapping plus migration and acceptance. |
| Validation policy | Prior valid input is rejected or an invariant is weakened. | Producer migration or threat/invariant review. |
| Enum or event expansion | Exhaustive or closed consumers lack unknown handling. | Unknown fixture, dual publish/version, or downstream compile. |
| Timing, ordering, or async behavior | Timeout, retry, consistency, sort, cursor, or event-order assumptions change. | Behavioral fixtures and migration communication. |

## Mixed-Version Paths

| Path | Pass condition |
| --- | --- |
| Old producer → new consumer | Accept old shape/defaults or apply a deterministic migration/upcaster. |
| New producer → old consumer | Preserve a tolerated representation, old path, or bridge. |
| Old code → new data/config | Old code understands/ignores new state or a bridge writes the old form. |
| New code → old data/config | Defaults, dual-read, upcaster, or backfill guard handles old state. |
| Delayed consumer/replay | Cover actual retention, lag, and replay windows. |
| Generated client → provider | Pass diff/compile/contract proof or establish a version boundary. |

## Selection And Limits

- Choose additive change, bridge/alias, expand-migrate-contract, version, adapter/upcaster, opt-in, dual publish/write, or config bridge from the failing path.
- Record precedence, reconciliation, unknown handling, rollout, rollback, telemetry, and cleanup owner for the selected mechanism.
- When unsafe shortcuts are considered, reject optional/enum safety assumptions, calendar-only removal, redeploy-only rollback, happy-path-only contract proof, unbridged config renames, and registry defaults chosen without producer/consumer direction.
