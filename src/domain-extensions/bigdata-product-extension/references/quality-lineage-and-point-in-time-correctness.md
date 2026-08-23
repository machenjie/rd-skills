# Quality, Lineage, and Point-in-Time Correctness

Use this Reference only for the named BigData quality-lineage-and-point-in-time-correctness decision.

## Decision Rules

- Preserve point-in-time correctness for mutable dimensions and features without temporal leakage, using backfill and live-coexistence validation against authoritative totals and representative historical snapshots.
- Define quality invariants for completeness, uniqueness, validity, referential integrity, distributions, row counts, and semantic drift. Consumer impact and replay capability determine failed-data disposition.
- Record lineage from source and schema through transformation, storage, dashboard, model, and API consumers, owner, deployment version, and recovery evidence.
