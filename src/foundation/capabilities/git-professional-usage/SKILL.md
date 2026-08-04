---
name: git-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when merges, rebases, conflicts, history rewrite, generated files, or recovery need evidence; skip when Git is irrelevant."
---

# git-professional-usage

## Registry Trigger

**Use when**

- git merge rebase cherry-pick conflict worktree index branch upstream reflog reset revert stash force-with-lease tag signed tag release tag submodule sparse checkout generated file conflict dirty worktree
- generated-output, source-authority, ours, theirs, merge-base, conflict-marker, unrelated-staged-changes, unstaged-diff, staged-diff, user-changes, overwrite, rollback, ref, protected-branch, history-rewrite, backup-branch, branch-naming, commit-message, commit-splitting, bisect, failure-isolation

**Do not use when**

- task concerns no version-control behavior or history decision

## Skill Role

Define worktree/index evidence, change ownership, semantic conflict resolution, history-mutation limits, generated/nested repository handling, recovery, and version-control proof. Exclude code correctness and administration.

## High-Value Rules

- **Inspect repository state before mutation.** Resolve current branch or detached state, upstream, worktree and index changes, conflicts, nested repositories, sparse scope, ignored or generated files, and ownership of pre-existing edits.
- **Preserve unrelated user work.** Limit staging, cleanup, restoration, and conflict resolution to proven task-owned paths, and stop when ownership cannot be established safely.
- **Resolve conflicts by semantic authority.** Resolve source ownership through merge-base comparison, source-owned regeneration, and combined-behavior validation.
- **Bind history mutation to shared authority.** Determine published/protected/reviewed/tagged/consumed ref state, including exact remote ref, expected object ID, separately observed stable lease basis, and concurrent/server-policy proof limits for force updates.
- **Keep commits behaviorally coherent.** Separate generated churn, movement, refactoring, behavior, migration, and cleanup where combining them would hide causality, review, recovery, or bisection evidence.
- **Handle nested and generated surfaces explicitly.** Preserve submodule or workspace identity, source-to-output lineage, executable bits, renames, case behavior, and platform-sensitive metadata.
- **Create a recoverable evidence trail.** Record pre-mutation identity, intended ref changes, conflict decisions, validation, and available recovery references without exposing unrelated diff content.

## Anti-Patterns

- Discard, overwrite, stage, or rewrite changes whose ownership and scope are not proven.
- Resolve generated-file conflicts by hand while leaving the authoritative source or generator inconsistent.
- Force shared history or collapse unrelated changes because the resulting tree appears correct locally.

## Stop Conditions

Escalate when work ownership is ambiguous, shared or protected history lacks authority, conflict semantics are unknown, or generated source authority is unknown. Also escalate when nested repository state is inconsistent or consequential mutation lacks recovery evidence. Stop a force update when the remote tip advanced or the lease basis may have refreshed independently.

## Output Contract

- version-control decision with repository state, ownership boundary, semantic conflict resolution, bounded history mutation, coherent change grouping, generated and nested handling, recovery evidence, and residual risks

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Merge, rebase, recovery, generated-authority, or conflict strategies need calibration | Only read-only worktree inspection is required | review-agent, analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Git work affects conflicts, destructive state, remotes, or generated files | No repository state mutation is authorized | review-agent, analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Safety claims need current worktree, refs, validation, and rollback evidence | No Git mutation or recovery claim needs proof | review-agent, analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
