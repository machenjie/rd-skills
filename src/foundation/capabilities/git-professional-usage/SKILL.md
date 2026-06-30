---
name: git-professional-usage
description: Use when Git worktree, branch, merge, rebase, conflict, generated file, submodule, sparse checkout, history rewrite, commit hygiene, or recovery behavior needs evidence-backed professional handling.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "130"
changeforge_version: 0.1.0
---

# Mission

Keep Git usage evidence-driven, reversible, and respectful of existing work. Treat the worktree, index, branch graph, generated artifacts, and remote refs as production state: no destructive command, conflict resolution, force push, generated-file edit, or recovery action is acceptable without current evidence, ownership boundaries, and rollback notes.

# When To Use

Use when a task touches merge, rebase, cherry-pick, revert, reset, conflict resolution, branch creation, worktree setup, submodules, sparse checkout, generated files, lockfiles, vendored outputs, local dirty state, force push, release tag, bisect, patch application, commit splitting, or any workflow where user changes could be overwritten.

# Do Not Use When

Do not use for ordinary repository reading, a simple README typo, or normal final-status reporting where no Git operation, conflict, history, generated artifact, or worktree-state decision is being made. Do not use to install source content or to treat Git history as a substitute for current source inspection.

# Non-Negotiable Rules

- Inspect `git status --short`, current branch, and relevant diff before any state-mutating Git command.
- Never discard, overwrite, or stage unrelated user changes without explicit instruction.
- Do not resolve conflicts from memory. Inspect both sides, the common base when needed, generated-source authority, and downstream tests.
- Destructive commands such as `reset --hard`, `checkout --`, branch deletion, clean, force push, and reflog recovery require a rollback note and explicit target.
- Generated files require an authority decision: source spec, generator, checked-in output, lockfile, or vendored artifact. Do not edit generated output by hand unless the repository policy says it is authoritative.
- Commit hygiene requires a small, reviewable, test-backed diff and a message that states behavior, not vague activity.
- Submodule and sparse-checkout changes require pinned revisions, affected-path evidence, and release impact.
- Force-with-lease is the ceiling for shared-branch rewriting; plain force push is rejected unless a maintainer explicitly owns the remote.
- Reverts are preferred over history rewriting for published branches unless the branch ownership and review policy allow rewriting.
- Conflict resolution must include a same-pattern scan when the conflict reveals a generated/source drift or recurring merge shape.

# Industry Benchmarks

Anchor decisions against Pro Git branch/rebase/reflog guidance, Git official documentation for merge strategies and pathspecs, trunk-based development discipline, release engineering guidance for signed tags and protected branches, OpenSSF Scorecard branch-protection expectations, and common generated-artifact policies for OpenAPI, protobuf, GraphQL, ORM clients, lockfiles, and vendored code.

# Selection Rules

Select this capability when Git state or history is part of the risk, not merely because a repository exists. Pair with `repository-context-map` when source ownership is unclear, `validation-broker` when affected tests must be selected from changed paths, `plan-execution-consistency` when actual diff must be reconciled against a plan, and `agent-tool-permission-sandbox` for destructive or remote-mutating Git commands.

# Risk Escalation Rules

Escalate to `delivery-release-gate` for release tags, protected branches, deployment branches, or branch rewrites that can affect production. Escalate to `security-privacy-gate` if commits, diffs, reflog, or patch files may expose secrets. Escalate to `architecture-impact-reviewer` when conflicts reveal ownership drift across generated/source boundaries or module dependency direction. Escalate to `quality-test-gate` when conflict resolution or cherry-pick behavior lacks validation evidence.

# Critical Details

- **Worktree state is input evidence.** Record dirty paths, staged paths, untracked files, branch, upstream, and conflict markers before choosing an action.
- **Conflict resolution is design work.** Resolve by preserving current behavior, source-of-truth contracts, generated policy, and consumer compatibility; do not just pick "ours" or "theirs".
- **Generated artifacts need policy.** For protobuf, OpenAPI, GraphQL, ORM, lockfiles, and build outputs, identify whether source or generated output is authoritative and run the generator or drift check when required.
- **Rebase and cherry-pick replay old assumptions.** Re-run tests that map to the replayed change and scan for same-pattern conflicts.
- **Reflog is recovery evidence.** Before risky operations, know the prior ref or create a lightweight backup branch if the local policy allows it.
- **Commit boundaries are review boundaries.** Split unrelated changes and keep generated artifacts with their source change when the repository expects them together.
- **Remote mutation changes other people's state.** Push, force-with-lease, tag mutation, and branch deletion need branch ownership and rollback communication.

# Failure Modes

- **User work overwritten:** a reset or checkout removes unrelated local edits because status was not inspected.
- **Generated-source drift:** conflict is resolved in generated code but the source `.proto`, OpenAPI spec, or schema remains stale.
- **Wrong side chosen:** `ours` or `theirs` is applied without inspecting behavior, silently dropping a security or compatibility fix.
- **History rewrite surprise:** force push removes commits another collaborator based work on.
- **Dirty index commit:** unrelated staged files are included because the index was not reviewed.
- **Submodule drift:** parent repo points to a commit that is unavailable, unreviewed, or incompatible with the release branch.
- **Patch applies cleanly but behavior regresses:** cherry-pick compiles but misses nearby API, schema, or generated-output changes from the original branch.
- **Secret persistence:** a secret removed from the working tree remains in commits, tags, or patches.

# Output Contract

Return a Git Professional Usage Record with:

- `operation` (merge, rebase, cherry-pick, conflict resolution, revert, reset, branch, worktree, submodule, commit, tag, push, recovery)
- `state_inspected` (branch, upstream, status, staged/unstaged/untracked paths, conflict paths, relevant refs)
- `ownership_boundary` (user changes, generated files, source files, submodules, protected branches, remote refs)
- `decision_record` (chosen action, alternatives rejected, why it preserves behavior and ownership)
- `generated_artifact_policy` (source authority, generator command, drift check, committed/ignored output)
- `safety_controls` (backup ref, force-with-lease, dry run, explicit pathspec, no-destructive-action note)
- `validation_commands` (diff, tests, generator, lint, or not-run disclosure mapped to changed paths)
- `rollback_note` (reflog ref, revert command, backup branch, or why rollback is not available)
- `handoff_summary` (changed refs/files, residual risk, next owner)

# Quality Gate

1. Current branch, upstream, status, staged diff, unstaged diff, and untracked risk are inspected before state mutation.
2. User-owned changes are preserved or explicitly excluded from the operation.
3. Conflict resolution cites both sides and source-of-truth policy.
4. Generated artifacts are regenerated or intentionally left alone with policy evidence.
5. Destructive or remote-mutating commands have rollback notes and explicit targets.
6. Commit boundaries are reviewable and exclude unrelated changes.
7. Validation evidence maps to the resolved files and replayed changes.
8. Residual risk names untested conflict paths, generated drift, remote coordination, or release impact.

# Used By

development-process-orchestrator, quality-test-gate, ai-code-review-refactor, delivery-release-gate, change-documentation-gate

# Handoff

Hand off to `repository-context-map` for source ownership, `validation-broker` for changed-path validation selection, `delivery-release-gate` for protected branch or release ref changes, `security-privacy-gate` for secret-in-history risk, and `ai-code-review-refactor` for conflict-resolution review.

# Completion Criteria

Git work is complete when the worktree/index/ref state was inspected, unrelated user changes were preserved, generated/source authority was respected, risky commands had rollback notes, conflict or replay behavior was validated, and the handoff names exactly what remains unproven.
