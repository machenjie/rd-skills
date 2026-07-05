# Git Benchmarks And Patterns

## Benchmarks

- Git official documentation for merge, rebase, pathspec, reflog, worktree, and push semantics.
- Pro Git for branch graph, conflict resolution, rebasing, and recovery patterns.
- Trunk-based development for small changes, short-lived branches, and protected mainline.
- OpenSSF Scorecard for branch protection, review, and signed-release hygiene.
- Repository-local generated-artifact policy for protobuf, OpenAPI, GraphQL, ORM clients, vendored outputs, and lockfiles.

## Pattern Matrix

| Surface | Required pattern | Rejected shortcut |
| --- | --- | --- |
| Dirty worktree | Inspect status and diff before mutation | Assume all changes are agent-owned |
| Conflict | Read ours, theirs, base, and source authority | Accept all ours/theirs without behavior review |
| Generated output | Regenerate or run drift check | Hand-edit generated files without policy |
| Rebase/cherry-pick | Replay with affected validation | Treat clean apply as proof |
| Force push | Use branch ownership plus force-with-lease | Plain force push to shared branch |
| Recovery | Reflog or backup ref identified | "Undo later" with no ref |

## Generated Artifact Authority

Record whether the source spec, checked-in generated output, or external generator is authoritative. If source is authoritative, regenerate and verify drift. If output is authoritative, explain why no generator is available and what review replaces regeneration.

## Conflict Resolution Evidence

Conflict decisions should cite behavior preserved, source side chosen, generated side regenerated, same-pattern scan, validation command, and residual risk. A conflict that touches auth, data contracts, migrations, build graph, or release config should route to the owning professional gate.
