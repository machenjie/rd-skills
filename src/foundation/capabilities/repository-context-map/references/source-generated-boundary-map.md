# Source Generated Boundary Map

Use this reference when a repository context map must separate editable source from generated, installed, or runtime support artifacts.

## Required Fields

| Field | Required Evidence | Limit |
| --- | --- | --- |
| Editable source | Source file, registry entry, template, script, or config that owns behavior. | Do not infer from generated output alone. |
| Generated artifact | Dist file, report, package output, copied runtime artifact, or install target. | Impact surface, not edit target unless explicitly source-owned. |
| Generator | Build script, validator, registry compiler, or packaging command. | Command existence does not prove output freshness. |
| Runtime profile | Recommended, full, dev, installed, or hook support artifact. | Profile impact must stay distinct from source authoring. |
| Freshness proof | Commit/order, mtime, source hash, report timestamp, or rerun command. | Stale output is selector evidence only. |
| Rollback clue | Revert source edit, rerun generator, or discard generated output. | Never require deleting unrelated dirty worktree changes. |

## Boundary Rules

1. Edit source under `src/` only when it is the owning authoring artifact.
2. Treat `dist/`, reports, snapshots, and installed folders as generated impact surfaces unless a maintainer says otherwise.
3. Map source to generator before claiming build, install, or runtime behavior changed.
4. If source ownership is unknown, stop planning or hand off to `repository-graph-analysis`.
