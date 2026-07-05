# Git Evidence Patterns

## Required Evidence

- Worktree state: branch, upstream, status, staged diff, unstaged diff, and untracked paths.
- Ref state: merge base, source branch, target branch, relevant tag, or reflog ref when needed.
- Conflict evidence: conflicted paths, ours/theirs/base inspection, source-of-truth decision, and generated policy.
- Validation evidence: command, exit code, and what changed path or behavior it covers.
- Rollback evidence: revert path, backup branch, reflog entry, or why rollback is not available.

## Tool Permission Boundary

Classify Git commands as read-only, local state-mutating, or remote state-mutating. Read-only commands include `status`, `diff`, `show`, `log`, and `merge-base`. Local state-mutating commands include `add`, `commit`, `merge`, `rebase`, `cherry-pick`, `reset`, `clean`, and worktree changes. Remote state-mutating commands include push, tag push, branch deletion, and force-with-lease.

## Handoff Shape

Use:

```
Git Professional Usage Record
- Operation:
- State inspected:
- Ownership boundary:
- Decision:
- Validation:
- Rollback:
- Residual risk:
```

## Blocking Conditions

Block completion when unrelated user changes would be staged or discarded, a generated artifact conflict lacks source authority, a destructive command lacks rollback notes, or remote history would be rewritten without branch ownership.
