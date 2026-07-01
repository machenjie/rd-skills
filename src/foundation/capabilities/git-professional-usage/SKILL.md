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

Use when a task touches merge, rebase, cherry-pick, revert, reset, stash, conflict resolution, branch creation or naming, worktree setup, submodules, sparse checkout, generated files, lockfiles, vendored outputs, local dirty state, staged vs. unstaged diff review, force push, signed tags, release tag mutation, bisect failure isolation, patch application, commit message format, commit splitting, or any workflow where user changes could be overwritten.

# Do Not Use When

Do not use for ordinary repository reading, a simple README typo, or normal final-status reporting where no Git operation, conflict, history, generated artifact, or worktree-state decision is being made. Do not use to install source content or to treat Git history as a substitute for current source inspection.

# Stage Fit

Use during planning, debugging, implementation, code-review, testing, release, and incident-repair stages when Git state, branch history, index contents, generated artifacts, remote refs, or recovery evidence can affect correctness, reviewability, ownership, or rollback. Re-enter after merge, rebase, cherry-pick, conflict resolution, stash, reset, revert, commit split, generated-file, submodule, sparse-checkout, branch, tag, push, or recovery decisions. Skip for read-only repository inspection where no worktree, index, ref, history, generated artifact, or ownership decision is being made.

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

# Proactive Professional Triggers

- **Signal:** A Git operation is proposed while status, branch, upstream, staged diff, unstaged diff, or untracked files are unknown.
  **Hidden risk:** unrelated user work is staged, overwritten, lost, or treated as agent-owned for the wrong operation.
  **Required professional action:** inspect current worktree/index/ref state and state ownership boundaries before mutation.
  **Route to:** `repository-context-map`, `agent-tool-permission-sandbox`.
  **Evidence required:** branch/upstream, `git status --short`, staged diff, unstaged diff, untracked summary, and excluded unrelated paths.
- **Signal:** A merge, rebase, cherry-pick, or conflict is resolved by accepting `ours`, `theirs`, a generated file, or a memory-based answer.
  **Hidden risk:** source authority, behavior, security fix, or compatibility change is silently dropped.
  **Required professional action:** inspect both sides and the source-of-truth artifact, then map validation to the resolved paths.
  **Route to:** `repository-graph-analysis`, `validation-broker`, `quality-test-gate`.
  **Evidence required:** conflicted paths, ours/theirs/base or source authority, chosen behavior, same-pattern scan, and validator output or not-run owner.
- **Signal:** `reset`, `checkout --`, `clean`, branch deletion, tag mutation, force push, force-with-lease, reflog recovery, or stash is suggested as a cleanup shortcut.
  **Hidden risk:** local or remote state changes become irreversible or affect collaborators.
  **Required professional action:** classify command permission, target ref/path, branch ownership, rollback ref, and safer alternative.
  **Route to:** `agent-tool-permission-sandbox`, `delivery-release-gate`.
  **Evidence required:** command class, exact target, backup/ref/reflog path, lease or ownership proof, and rollback/communication note.
- **Signal:** Commit hygiene, staged changes, generated output, lockfiles, vendored files, submodules, sparse checkout, or release tags are included without source/generated policy and review boundaries.
  **Hidden risk:** review diff mixes unrelated work or publishes derived artifacts inconsistent with source.
  **Required professional action:** split review boundaries and keep generated artifacts with their authority decision.
  **Route to:** `build-tool-professional-usage`, `plan-execution-consistency`.
  **Evidence required:** source/generator/output policy, staged vs unstaged review, commit split rationale, and release/tag impact.
- **Signal:** Commits, diffs, patches, reflog entries, generated files, or review artifacts include tokens, keys, credentials, private URLs, or secret-like values.
  **Hidden risk:** removing the working-tree value does not remove a secret leak from history, artifacts, logs, or remote refs.
  **Required professional action:** route secret review, preserve evidence safely, and plan rotation/history handling before publishing or cleanup.
  **Route to:** `security-privacy-gate`, `secret-configuration-security`.
  **Evidence required:** redacted finding path, affected refs/artifacts, secret-scan or manual review result, rotation owner, and residual exposure.
- **Signal:** Repository graph, project memory, old CI logs, previous diffs, branch summaries, or historical command output are reused after ref, index, generated artifact, or conflict changes.
  **Hidden risk:** stale graph or execution trajectory certifies the wrong worktree state.
  **Required professional action:** verify memory, graph, and trajectory as selectors, rerun selected status/diff/ref reads, and mark stale evidence rejected.
  **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`.
  **Evidence required:** accepted/rejected memory, graph freshness, changed refs/paths, rerun command, exit code, and report/artifact path.

# Mode Matrix

| Mode | Trigger | Required evidence |
| --- | --- | --- |
| Worktree/index protection | Dirty state, staging, commit split, stash, or cleanup | Branch/upstream, status, staged/unstaged/untracked summary, ownership boundary, excluded paths |
| Conflict or replay | Merge, rebase, cherry-pick, conflict marker, generated conflict | Ours/theirs/base or source authority, same-pattern scan, changed-path validation |
| Destructive or recovery | Reset, clean, checkout, reflog, backup branch, branch deletion | Command class, exact target, backup/ref, rollback note, safer alternative |
| Remote or release ref | Push, force-with-lease, protected branch, signed tag, release tag | Branch/tag ownership, lease/protection policy, communication, release impact |
| Generated/submodule boundary | Generated file, lockfile, vendored output, submodule, sparse checkout | Source/generated authority, generator or drift check, pinned revision, consumer impact |

# Critical Details

- **Worktree state is input evidence.** Record dirty paths, staged paths, untracked files, branch, upstream, and conflict markers before choosing an action.
- **Conflict resolution is design work.** Resolve by preserving current behavior, source-of-truth contracts, generated policy, and consumer compatibility; do not just pick "ours" or "theirs".
- **Generated artifacts need policy.** For protobuf, OpenAPI, GraphQL, ORM, lockfiles, and build outputs, identify whether source or generated output is authoritative and run the generator or drift check when required.
- **Rebase and cherry-pick replay old assumptions.** Re-run tests that map to the replayed change and scan for same-pattern conflicts.
- **Reflog is recovery evidence.** Before risky operations, know the prior ref or create a lightweight backup branch if the local policy allows it.
- **Commit boundaries are review boundaries.** Split unrelated changes and keep generated artifacts with their source change when the repository expects them together.
- **Remote mutation changes other people's state.** Push, force-with-lease, tag mutation, and branch deletion need branch ownership and rollback communication.
- **Stash is not a backup plan by itself.** Stash only after status and diff review; name what is included, whether untracked files are included, and how the stash will be reapplied or dropped.
- **Branch names and commit messages are release evidence.** Branch names should follow repository convention and issue/release scope. Commit messages should state behavior and risk, not vague activity.
- **Staged and unstaged diffs are separate review surfaces.** Review both before committing, rebasing, splitting commits, or resolving conflicts so unrelated user changes do not leak into the operation.
- **Release tag mutation is a release event.** Signed tags, tag deletion, retagging, and release-branch rewrites require ownership, verification, and rollback/communication evidence.
- **Bisect isolates a failure, not a fix.** A bisect result needs the tested command, known good/bad refs, skipped refs, and same-pattern follow-up before diagnosis closes.

# Failure Modes

- **User work overwritten:** a reset or checkout removes unrelated local edits because status was not inspected.
- **Generated-source drift:** conflict is resolved in generated code but the source `.proto`, OpenAPI spec, or schema remains stale.
- **Wrong side chosen:** `ours` or `theirs` is applied without inspecting behavior, silently dropping a security or compatibility fix.
- **History rewrite surprise:** force push removes commits another collaborator based work on.
- **Dirty index commit:** unrelated staged files are included because the index was not reviewed.
- **Submodule drift:** parent repo points to a commit that is unavailable, unreviewed, or incompatible with the release branch.
- **Patch applies cleanly but behavior regresses:** cherry-pick compiles but misses nearby API, schema, or generated-output changes from the original branch.
- **Secret persistence:** a secret removed from the working tree remains in commits, tags, or patches.

# Anti-Rationalization Table

| Rationalization | Hidden Risk | Required Correction |
|---|---|---|
| "It is just a small reset." | Unrelated user work or staged changes are lost. | Inspect status and diffs, target explicit paths/refs, and record rollback. |
| "The conflict looks obvious." | Behavior, generated authority, or a security fix is silently dropped. | Inspect both sides, source authority, and validation before resolving. |
| "Generated files can be fixed by hand." | Source and generated artifacts drift. | Regenerate or document why checked-in output is authoritative. |
| "Force push is fine because it is my branch." | Collaborator refs or review state are rewritten. | Verify branch ownership, use force-with-lease, and record recovery. |
| "Tests are not needed after rebase." | Replay changes compile but behavior regresses. | Run changed-path validation or state the unverified residual risk. |

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, risk, and output-contract rules.

Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete Git Professional Usage Record, conflict/rebase/cherry-pick handoff, destructive-command review, commit hygiene review, release-tag review, or recovery checklist.
Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when conflict resolution, generated/source authority, history rewrite, release tag, bisect, stash, or commit hygiene needs deeper benchmark support.
Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff must prove worktree/ref evidence, rollback notes, conflict-resolution evidence, or release-tag safety.
Do not load references for ordinary repository reads, final status summaries, or low-risk typo/docs edits with no Git state decision.
References are just-in-time support, not default-loaded encyclopedia content.

# Output Contract

Return a Git Professional Usage Record with:

- `operation` (merge, rebase, cherry-pick, conflict resolution, revert, reset, branch, worktree, submodule, commit, tag, push, recovery)
- `state_inspected` (branch, upstream, status, staged/unstaged/untracked paths, conflict paths, relevant refs)
- `ownership_boundary` (user changes, generated files, source files, submodules, protected branches, remote refs)
- `decision_record` (chosen action, alternatives rejected, why it preserves behavior and ownership)
- `generated_artifact_policy` (source authority, generator command, drift check, committed/ignored output)
- `diff_review` (staged diff, unstaged diff, untracked risk, and unrelated-change exclusions)
- `stash_policy` (included paths, untracked handling, apply/drop plan, and why stash is safer than alternatives)
- `branch_commit_contract` (branch naming convention, commit message format, commit split boundaries)
- `release_tag_contract` (signed tag status, tag mutation owner, protected release ref impact)
- `bisect_record` (good/bad refs, command, skipped refs, isolated failure, follow-up validation)
- `safety_controls` (backup ref, force-with-lease, dry run, explicit pathspec, no-destructive-action note)
- `validation_commands` (diff, tests, generator, lint, or not-run disclosure mapped to changed paths)
- `validation_freshness` (commands or validators rerun after the final material worktree, index, conflict, generated artifact, or ref edit; stale output rejected or named)
- `what_evidence_proves` and `what_evidence_does_not_prove` (covered paths, refs, generated policy, branch ownership, validation scope, and limits)
- `tool_permission_boundary` (read-only vs local state-mutating vs remote state-mutating Git command, sandbox, target, and rollback)
- `memory_graph_execution_record` (repository graph, project memory, old diff, branch summary, previous command output, or trajectory evidence accepted, rejected, stale, partial, or not used)
- `rollback_note` (reflog ref, revert command, backup branch, or why rollback is not available)
- `handoff_summary` (changed refs/files, residual risk, next owner)

# Evidence Contract

Close a Git Professional Usage Record only when these answers are concrete: **boundaries inspected** across branch, upstream, status, staged diff, unstaged diff, untracked files, relevant refs, generated artifacts, submodules, protected branches, remote refs, and release tags when in scope; direct status/diff/ref/config/validator evidence accepted or rejected; repository graph, project memory, old CI logs, branch summaries, previous diffs, and execution trajectory used only as selectors unless rerun against current worktree/ref state; validation evidence names command/test/validator/report/artifact, output summary, exit code or not-run status, and freshness after the final material edit; what evidence proves and does not prove for paths, refs, generated drift, branch ownership, remote coordination, and release impact; reuse and placement rationale for new branches, commits, generated artifacts, backups, stashes, tags, or recovery paths; behavior preservation, rollback or communication path, residual risk owner, and next gate.

# Quality Gate

1. Current branch, upstream, status, staged diff, unstaged diff, and untracked risk are inspected before state mutation.
2. User-owned changes are preserved or explicitly excluded from the operation.
3. Conflict resolution cites both sides and source-of-truth policy.
4. Generated artifacts are regenerated or intentionally left alone with policy evidence.
5. Destructive or remote-mutating commands have rollback notes and explicit targets.
6. Stash, backup branch, branch naming, commit message, and commit splitting decisions match repository convention and preserve unrelated work.
7. Staged and unstaged diffs are reviewed before commits, rebases, splits, resets, and conflict resolution.
8. Signed tags, release tag mutation, force-with-lease, and bisect results include ownership, verification, and rollback notes.
9. Validation evidence maps to the resolved files and replayed changes.
10. Tool permission boundary is explicit for read-only, local state-mutating, and remote state-mutating Git commands.
11. Graph, memory, previous diffs, old logs, branch summaries, and prior command output are freshness-checked and cannot substitute for current worktree/ref evidence.
12. Residual risk names untested conflict paths, generated drift, user-owned dirty state, remote coordination, protected branch policy, or release impact.

# Used By

development-process-orchestrator, quality-test-gate, ai-code-review-refactor, delivery-release-gate, change-documentation-gate

# Handoff

Hand off to `repository-context-map` for source ownership, `validation-broker` for changed-path validation selection, `delivery-release-gate` for protected branch or release ref changes, `security-privacy-gate` for secret-in-history risk, and `ai-code-review-refactor` for conflict-resolution review.

# Completion Criteria

Git work is complete when the worktree/index/ref state was inspected, unrelated user changes were preserved, generated/source authority was respected, risky commands had rollback notes, conflict or replay behavior was validated, and the handoff names exactly what remains unproven.
