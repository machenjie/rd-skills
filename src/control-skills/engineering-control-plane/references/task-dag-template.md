# Dependency Plan

Use this optional plan only when real dependencies, integration ownership, or useful isolated parallel work require coordination. An explicit user request can also justify it. A file count or ordinary single-agent change does not.

List each necessary task with its accountable owner, goal, relevant write scope, validation, and the concrete output or invariant a downstream consumer needs. Add a blocking edge only when that consumer cannot proceed without it. Keep jointly validated work together; do not split by files, layers, tests, or edit steps alone.

Record the integration owner and cross-task validation where real boundaries require them. Preserve established behavior and invariants; resolve competing decisions before the affected work. Shared or unknown workspaces use serial writes; parallel writes require Host-provided isolation and disjoint, independent write surfaces.

No complete Task Contract, Review Round, fixed Review Boundary, or Evidence Ledger is required. Add a review dependency only when an actual independent judgment must precede the consumer.
