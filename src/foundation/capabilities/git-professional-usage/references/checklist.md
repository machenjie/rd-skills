# Git Professional Usage Checklist

- Identify the operation: read-only inspection, merge, rebase, cherry-pick, conflict resolution, stash, reset, revert, clean, branch, commit, tag, push, recovery, submodule, or sparse checkout.
- Record worktree and ref state: branch, upstream, `git status --short`, staged diff, unstaged diff, untracked files, conflicted paths, relevant refs, merge base, tag, or reflog entry.
- Separate ownership boundaries: user-owned changes, agent-owned changes, staged vs unstaged work, generated files, source files, submodules, protected branches, remote refs, and release tags.
- Classify command permission before execution: read-only, local state-mutating, remote state-mutating, destructive, or recovery command; name target path/ref and rollback path.
- Resolve conflicts from evidence: inspect ours/theirs/base or source authority, generated policy, behavior preserved, same-pattern scan, and validator mapped to resolved paths.
- Review generated artifact policy: source spec, generator command, generated output, lockfile or vendored artifact authority, drift check, and committed/ignored decision.
- Review commit hygiene: staged diff only, unrelated changes excluded, commit split boundaries, branch naming convention, commit message behavior/risk statement, and signature/tag expectations when relevant.
- Review remote/release safety: branch ownership, protected branch policy, force-with-lease ceiling, signed tag status, tag mutation owner, rollback communication, and downstream release impact.
- Validate with the smallest command, test, generator, diff, or report that can fail for the changed Git boundary, then state what it proves and does not prove.
- Treat repository graph, project memory, old diffs, previous command output, branch summaries, and old CI logs as selectors only until current worktree/ref/source evidence confirms them.
