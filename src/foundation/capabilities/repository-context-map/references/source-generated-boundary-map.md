# Source Generated Boundary Map

Use this reference when a repository context map must separate editable source from generated, built, or installed artifacts.

## Required Fields

| Field | Required Evidence | Limit |
| --- | --- | --- |
| Editable source | Source file, registry entry, template, script, or config that owns behavior. | Do not infer from generated output alone. |
| Generated artifact | Dist file, report, package output, copied built artifact, or install target. | Impact surface, not edit target unless explicitly source-owned. |
| Generator | Build script, validator, registry compiler, or packaging command. | Command existence does not prove output freshness. |
| Build profile | Recommended, full, dev, or installed output. | Build impact must stay distinct from source authoring. |
| Freshness proof | Commit/order, mtime, source hash, report timestamp, or rerun command. | Stale output is selector evidence only. |
| Rollback clue | Revert source edit, rerun generator, or discard generated output. | Never require deleting unrelated dirty worktree changes. |

## Boundary Rules

1. Edit source under `src/` only when it is the owning authoring artifact.
2. Treat `dist/`, reports, snapshots, and installed folders as generated impact surfaces unless a maintainer says otherwise.
3. Map source to generator before claiming build or install output changed.
4. If source ownership is unknown, continue `repository-context-map` discovery.
5. Stop planning while source ownership remains unknown.
6. Do not hand unresolved ownership to `repository-impact-inspection`.
7. Hand off to `repository-impact-inspection` only after source of truth, candidate owner, and change-surface candidates are known.
8. Use impact inspection to prove bounded impacts after that discovery.
