# Shortcut Ledger

Load this reference when a deliberate shortcut remains or when a review finds `changeforge-shortcut:`.

## Marker Format

```text
changeforge-shortcut: <simplification>; ceiling: <limit>; upgrade when: <trigger>
```

Example:

```go
// changeforge-shortcut: global mutex; ceiling: low write throughput; upgrade when: per-account contention is measured
```

## Required Fields

- **Simplification:** what was intentionally simplified.
- **Ceiling:** scale, behavior, traffic, correctness, or lifecycle limit where it stops being acceptable.
- **Upgrade trigger:** measurable signal or explicit requirement that forces replacement.
- **Owner:** team or module boundary that owns the shortcut.
- **Validation:** runnable check or review evidence proving the shortcut is currently safe enough.
- **Residual risk:** what remains unproven.

## Review Rules

- A shortcut without `ceiling:` is unbounded debt.
- A shortcut without `upgrade when:` has no removal trigger.
- A shortcut cannot bypass security, authorization, data integrity, money correctness, migration safety, accessibility, or production reliability obligations.
- A shortcut marker is review evidence, not permission to skip tests.
- Stale shortcuts route to `cleanup-deletion-governance`.

## Ledger Output

```text
marker:
owner:
current ceiling:
upgrade trigger:
validation evidence:
accepted residual risk:
cleanup issue or next gate:
```
