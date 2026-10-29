# Workspace, Build, and Git Modes

Select the mode that owns the requested repository behavior.

## Workspace and Build

- Fix the failing invocation, working directory, toolchain, dependency graph, and expected artifact.
- Compare local and CI inputs before changing configuration.
- Separate compiler configuration from runner provisioning and production rollout.
- Preserve the repository's manifest and lockfile authority.
- Inspect lifecycle scripts before invoking changed dependencies.
- Declare generated inputs, outputs, ordering, and cache keys at the owning build target.
- Validate a clean bootstrap and the smallest affected downstream target.
- A template consumer keeps its feature owner when initialization contracts remain unchanged.

## Git Collaboration

- Inspect HEAD, index, unstaged files, remotes, and operation state before mutation.
- Preserve user changes and identify a recoverable ref before rewriting authorized history.
- Resolve conflicts against intent and both consumers; regenerate derived files from the merged source.
- Recheck the resulting diff and affected behavior after rebase or conflict resolution.
- Keep local repair, remote push, external replies, and branch deletion within their separate authorization.
- Return the resulting refs, remaining changes, validation, and recovery route.

## Boundary Cases

| Request | Owner decision | Evidence |
|---|---|---|
| CI compilation config changes a generated-source dependency | Workspace/build | Clean build observes the declared generator output |
| Feature requires a package API migration | Existing feature owner | Migrated behavior and compatible consumer pass |
| Cloud runner capacity changes | Infrastructure | Runner definition and capacity assumptions |
| Rebase conflicts in generated output | Git collaboration | Source conflict resolved and output regenerated |
| Deployment promotion | Delivery | Release and rollback decision |
