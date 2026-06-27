---
name: plan-execution-consistency
description: Reconciles planned actions with actual changed files, commands, validation, review scope, extra work, stale evidence, and residual risk before final handoff.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "122"
changeforge_version: 0.1.0
---

# Mission
Reconcile planned work, actual repository changes, validation evidence, review scope, repair state, graph/memory/trajectory signals, generated outputs, and final handoff claims before closure. The capability prevents silent scope drift, extra-file changes, stale validation, unreviewed repairs, generated-artifact mismatch, and completion claims that no longer match the final material state.

# When To Use
- Before final handoff after any non-trivial plan, task DAG, route manifest, edit, test, review, repair, documentation, build, install, release, or validation action.
- When files changed differ from planned files, validation ran before final edits, review scope is unclear, or a partial check may be reported as full validation.
- When repository graph, project memory, execution trajectory, validation broker, tool permission, or workflow state evidence affects closure.
- When generated reports, dist artifacts, install packages, registry entries, hook runtime support files, docs, or release artifacts must match source-of-truth and validation evidence.
- When an agent claims ready, done, fixed, validated, reviewed, released, installed, or blocked after material work.

# Do Not Use When
- The task is read-only and no plan-to-execution, validation, review, or closure comparison exists.
- A trivial single-file edit has matching plan/diff, fresh validation, no generated artifacts, no review repair, and no extra files.
- The work is intentionally abandoned and the handoff is explicitly blocked/not-done with no completion claim.
- The primary need is validation command selection, source graph extraction, memory projection, or trajectory reconstruction without a final reconciliation decision.

# Stage Fit
Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release, and handoff when closure depends on accepted plan evidence, changed paths, validation freshness, review scope, generated/source alignment, graph-memory-trajectory coupling, or final wording. At plan acceptance, record planned files/actions, owner/reviewer split, validation signal, non-goals, rollback expectation, and skipped surfaces before implementation starts. During coding, bug-fix, debugging, and refactoring, re-enter whenever source, registry, reference, report, generated artifact, package, install-output, documentation, fixture, review, or validation-input changes after a prior consistency check. During code-review, testing, release, and handoff, compare final diff, command ledger, review/repair state, graph/memory/trajectory claims, and final answer before allowing ready/done language.

# Non-Negotiable Rules
- Compare accepted plan, planned files/actions, actual changed files/actions, generated outputs, validation commands, review scope, and final handoff file list.
- Explain every extra, missing, renamed, generated, deleted, deferred, or abandoned file/action relative to the accepted plan.
- Re-run mapped validation after final material edits or disclose stale, partial, not-run, failed, or not-verified status.
- Match every changed behavior, public contract, registry route, source/dist boundary, generated artifact, or documentation claim to acceptance criteria, plan item, or explicit non-goal.
- Do not report targeted, lint-only, build-only, stale, or partial validation as full validation.
- Repair after review requires targeted re-review before approval can support closure.
- Graph, memory, trajectory, workflow, tool permission, and validation broker evidence can downgrade or widen closure, but they cannot replace current source and final diff inspection.
- Final handoff must disclose plan deviations, validation limits, review limits, unknowns, rollback note, residual risk, and next owner.

# Industry Benchmarks
Anchor against change control variance analysis, code review scope control, CI/test freshness discipline, generated artifact provenance, release readiness review, audit evidence integrity, incident handoff, and least-surprise closure. Keep the body focused on closure-time decisions; load the reference only when a concrete reconciliation table or handoff template is needed.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Plan-vs-diff reconciliation | Plan, task DAG, route, or stage manifest exists and files changed. | Match planned actions to final diff. | Planned items, actual files, variance status, rationale. | `repository-context-map` | Deep validation design unless a changed path lacks mapped evidence. |
| Validation freshness reconciliation | Commands ran before later edits or scope is partial. | Prevent stale or inflated proof. | Command ledger, covered paths, later edits, broker result. | `validation-broker`, `quality-test-gate` | New tests unless existing evidence is stale or insufficient. |
| Review/repair reconciliation | Review findings, repair edits, or approval scope exists. | Ensure final diff is reviewed. | Reviewer, findings, repaired files, re-review result. | `ai-code-review-refactor` | Broad refactor review when no repair or review-scope gap exists. |
| Generated/source reconciliation | Reports, dist, packages, docs, or install outputs changed. | Tie generated outputs to source and build command. | Source path, generated path, build command, runtime profile. | `repository-graph-analysis` | Runtime release approval unless deploy/package readiness is claimed. |
| Graph-memory-trajectory closure | Prior context, memory, graph, or execution order affects claim. | Accept, reject, or downgrade evidence before closure. | Freshness, accepted/rejected claims, closure consequence. | `project-memory-governance`, `execution-trajectory-analysis` | Full graph extraction when direct source/final diff answers the closure question. |
| Handoff decision | Final answer says ready/done/blocked/not verified. | Align final claim with evidence and risk. | Closure decision, unknowns, validation limits, rollback, next owner. | `agent-execution-discipline` | Extra process narration once evidence limits and next owner are explicit. |

# Selection Rules
- Select this capability for L2 or higher engineering work at final handoff, and for any work with a plan, route, task DAG, review, repair, validation, generated artifact, or release/install evidence.
- Select it when actual files differ from planned files, validation evidence predates final edits, review scope does not cover the final diff, or final handoff may overclaim.
- Select it with `quality-test-gate` and `validation-broker` when changed-code-to-test mapping, validator depth, parsed outcomes, or freshness decide closure.
- Select it with `repository-graph-analysis` when source-vs-generated boundaries, affected tests, registries, docs, build outputs, install outputs, or omitted graph edges affect plan/diff reconciliation.
- Select it with `project-memory-governance` and `execution-trajectory-analysis` when previous context, repeated failures, fragile files, compaction, command order, or repair order may be stale.
- Select it with `agent-workflow-state-machine` when legal stage transition, owner/reviewer split, repair/re-review, or closure state is ambiguous.
- Select it with `agent-tool-permission-sandbox` when unplanned tool actions, generated writes, destructive operations, external writes, or sandbox/approval limits affect final evidence.

# Technical Selection Criteria
Evaluate consistency by accepted plan source, plan freshness, actual changed paths, generated artifact provenance, changed behavior, acceptance mapping, route/stage manifest alignment, owner/reviewer split, review scope, repair/re-review state, command order, validation broker status, graph freshness, memory projection status, trajectory findings, source/dist boundary, docs/registry/release impact, tool permission record, rollback path, skipped work, and final claim. A closure decision is usable only as ready, needs validation, needs re-review, needs source reread, needs plan repair, blocked, not verified, or partial with named residual risk.

# Proactive Professional Triggers
- **Signal:** Final diff includes a file, generated artifact, report, registry entry, hook support file, package, or docs file not in the accepted plan. **Hidden risk:** scope drift bypasses review and validation. **Required professional action:** classify the variance, name rationale, route owner/reviewer, and map validation. **Route to:** `repository-context-map`, `validation-broker`. **Evidence required:** planned item, actual path, status, owner, validation impact.
- **Signal:** Validation passed before later source, registry, generated artifact, report, package, install-output, fixture, or documentation edits. **Hidden risk:** final state is reported as verified by stale evidence. **Required professional action:** rerun mapped validators or downgrade closure. **Route to:** `validation-broker`, `execution-trajectory-analysis`. **Evidence required:** command order, covered paths, later edits, freshness verdict.
- **Signal:** Review approval predates repair or does not name changed files. **Hidden risk:** stale approval covers the wrong or narrower diff. **Required professional action:** require targeted re-review or mark closure needs re-review. **Route to:** `ai-code-review-refactor`, `quality-test-gate`. **Evidence required:** reviewer, approval scope, repair file map, re-review command/output or report, re-review status.
- **Signal:** Memory, graph, or compaction summary is used as proof of current state. **Hidden risk:** stale selector evidence becomes source truth. **Required professional action:** verify and reconcile with current source, diff, reports, validation, and trajectory before accepting. **Route to:** `project-memory-governance`, `repository-graph-analysis`. **Evidence required:** accepted/rejected claims, direct-source fallback, diff map, validation output, closure consequence.
- **Signal:** Final response says done, ready, validated, no residual risk, or all tests passed after partial or targeted checks. **Hidden risk:** user receives a stronger claim than evidence supports. **Required professional action:** rewrite closure to evidence-limited status and name not-run/stale scope. **Route to:** `agent-execution-discipline`, `quality-test-gate`. **Evidence required:** exact commands, outcomes, proof limits, residual risk.
- **Signal:** Generated outputs or runtime install artifacts changed without source/build proof. **Hidden risk:** generated-only drift enters runtime packages. **Required professional action:** verify source-of-truth and rebuild/validate or mark not verified. **Route to:** `repository-graph-analysis`, `delivery-release-gate`. **Evidence required:** source file, generator/build command, generated freshness.

# Risk Escalation Rules
- Escalate when actual changed files include unplanned source, registry, hook runtime, release, migration, generated, package, install, security-sensitive, or cross-module artifacts.
- Escalate when validation is stale, failed, partial, not-run, unsupported, or lacks outcome/scope.
- Escalate when review approval does not cover the final diff or repair lacks re-review.
- Escalate when plan deviation changes user behavior, API/data contract, security posture, release behavior, docs obligations, runtime profile, or source/dist boundary.
- Escalate when memory, graph, adapter, or trajectory evidence is stale, low-confidence, unsupported, or contradicted by current source.
- Escalate when final handoff claims completion while unverified deviations, skipped work, or unknown generated artifacts remain.

# Critical Details
- Planned files are not a hard prison; legitimate expansion is allowed only with rationale, owner, review scope, and validation mapping.
- Generated files must be labeled generated or source-of-truth; closure must name source generator and build/install validator when relevant.
- Validation freshness is relative to the final material diff, not to the beginning of the turn or first green command.
- A successful lint, build, single test, targeted eval, or install check can be reported only as the specific evidence it provides.
- Plan consistency is not just file accounting. It reconciles requirement intent, planned actions, actual behavior, validation, review, docs/registry/release artifacts, graph/memory/trajectory freshness, and final words.
- A blocked or not-verified handoff can be consistent when it names missing work, owner, validation limit, rollback, and residual risk honestly.
- Load [references/consistency-reconciliation-matrix.md](references/consistency-reconciliation-matrix.md) for variance statuses, closure dimensions, and the handoff template.

# Failure Modes
- **Extra file drift:** The agent changes an unplanned helper, registry, generated artifact, or docs file and omits it from handoff.
- **Stale test pass:** Tests ran before a final source, registry, reference, report, package, or install-output edit, but closure says validation passed.
- **Partial validation inflation:** One targeted check, lint, or build is reported as full-suite or behavior proof.
- **Unreviewed repair:** A review finding is fixed after approval and never re-reviewed.
- **Spec drift:** The implementation satisfies an invented plan but misses the original requested behavior or non-goal.
- **Generated artifact mismatch:** A runtime output changes without source/build proof or source-vs-dist disclosure.
- **Memory or graph overclaim:** old context, graph, or compaction evidence is treated as current source truth.
- **Final-answer drift:** The final response omits residual risk, unknowns, failed commands, skipped validators, or changed-file variance.

# Reference Loading Policy
The `SKILL.md` body carries L1/L2 selection, gates, output, and closure rules. Load [references/consistency-reconciliation-matrix.md](references/consistency-reconciliation-matrix.md) when drafting a concrete consistency report, building a variance table, reconciling generated/source artifacts, comparing validation order, deciding repair/re-review status, or preparing final handoff. Do not add or load extra references for ordinary closure wording when the body can name the changed paths, validator result, proof limits, rollback note, and residual risk.

# Output Contract
Return a `plan_execution_consistency_report` with:
- `mode_selected` (plan-vs-diff reconciliation, validation freshness reconciliation, review/repair reconciliation, generated/source reconciliation, graph-memory-trajectory closure, or handoff decision).
- `boundaries_inspected` (request, accepted plan, route/stage manifests, source files, registries/config/docs, tests/evals, reports, generated artifacts, packages/install outputs, graph, memory, trajectory, tool-permission records, and skipped boundaries with reason).
- `plan_summary` (planned actions, planned files/artifacts, owner skill, reviewer skill, acceptance signal, validation command, non-goals, and rollback expectation).
- `actual_change_inventory` (changed, added, deleted, renamed, generated, docs, reports, packages, install outputs, commands, and final handoff file list).
- `variance_table` (each planned/actual item with status matched, extra, missing, renamed, generated, deferred, abandoned, or not verified; rationale; owner; review status; validation impact).
- `behavior_and_acceptance_map` (changed behavior, public contract, registry route, docs claim, or source/dist boundary mapped to requirement, acceptance criterion, explicit non-goal, or residual risk).
- `validation_freshness` (commands, outcomes, covered paths, uncovered paths, later edits, broker result, proof limits, stale/partial/not-run/failed/not-verified status, and rerun decision).
- `review_and_repair_scope` (reviewer, files reviewed, approval limits, findings, repair files, re-review status, unresolved findings, and uncovered diff areas).
- `graph_memory_trajectory_coupling` (accepted/rejected/stale graph or memory claims, trajectory order findings, workflow-state limits, adapter/tool permission limits, and closure consequence).
- `docs_registry_release_consistency` (docs, registries, generated outputs, runtime profiles, build/install/package outputs, rollback evidence, and validation status).
- `closure_decision` (ready, blocked, not verified, partial, needs validation, needs re-review, needs plan repair, or needs source reread), plus evidence limits, residual risk, next owner, and rollback note.

# Evidence Contract
Close consistency review only when these answers are concrete:
- **Basis:** accepted plan, changed boundary, route/stage signal, and why closure could drift.
- **Boundaries inspected:** request, accepted plan, source files, registry/config/docs, reports, generated outputs, tests, validation output, graph, memory, trajectory, review scope, tool permission, final diff, and skipped boundaries with reason.
- **Variance and behavior:** planned-vs-actual table, changed behavior/contract/docs mapping, generated/source status, skipped/deferred work, and non-goal reconciliation.
- **Freshness and review:** validation broker status, later edits, review scope, repair/re-review status, stale/partial/not-run limits, and negative evidence.
- **What evidence proves:** the inspected plan, final diff, command output, reports, generated artifacts, graph/memory/trajectory judgment, and review scope prove only the named closure decision for the changed paths and artifacts.
- **What evidence does not prove:** uninspected paths, skipped validators, stale external state, unavailable reviewers, unrun release/deploy behavior, hidden generated consumers, and future changes remain outside proof.
- **Closure:** final decision, evidence limit, rollback note, residual risk, next owner, and final handoff wording that does not exceed proof.

# Benchmark Coverage
This capability covers change variance analysis, review scope control, validation freshness, generated artifact provenance, source/dist boundary discipline, graph-memory-trajectory reconciliation, route/stage manifest alignment, repair re-review governance, residual-risk disclosure, and audit-ready final handoff.

# Routing Coverage
Routes from `change-forge-router`, `task-dag-planner`, `quality-test-gate`, `ai-code-review-refactor`, `delivery-release-gate`, `reliability-observability-gate`, `change-documentation-gate`, `skill-authoring-expert`, and `agent-execution-discipline` should arrive here when final evidence must reconcile accepted plan, final diff, validation, review, generated artifacts, docs/registry/release outputs, memory, graph, trajectory, or closure wording. Route away when the primary need is source graph extraction, validation command brokering, memory projection, or execution-order reconstruction without a closure reconciliation decision.

# Quality Gate
1. Accepted plan, actual changed files, generated outputs, commands, and final handoff file list are reconciled.
2. Extra, missing, renamed, generated, deleted, deferred, abandoned, or not-verified items have rationale, owner, review status, and validation impact.
3. Validation results are fresh for the final material diff or disclosed as stale, failed, partial, not-run, unsupported, or not verified.
4. Changed behavior, public contract, registry route, docs claim, or source/dist boundary maps to acceptance criteria, plan item, explicit non-goal, or residual risk.
5. Review scope covers the final diff, or targeted re-review is required before ready closure.
6. Partial validation, targeted checks, lint, build, install, or eval results are not reported as broader proof than they provide.
7. Generated artifacts, reports, packages, and install outputs map to source-of-truth and build/validation command when affected.
8. Graph, memory, trajectory, workflow, tool permission, and validation broker evidence are reconciled and downgraded when stale, unsupported, or low confidence.
9. Final handoff states inspected evidence, unknowns, validation limits, review limits, skipped work, rollback note, residual risk, and next owner.
10. Completion is not claimed while unresolved deviations, unre-reviewed repairs, failed/stale validation, or not-verified generated outputs remain.

# Used By
`change-forge-router`, `task-dag-planner`, `quality-test-gate`, `ai-code-review-refactor`, `delivery-release-gate`, `reliability-observability-gate`, `change-documentation-gate`, `skill-authoring-expert`, `agent-execution-discipline`.

# Handoff
Hand off the consistency report with final implementation, review, release, installation, documentation, skill-authoring, or blocked closure. If deviations, stale evidence, uncovered diff, generated-output mismatch, or unre-reviewed repairs remain, hand off to the owner skill, reviewer skill, validation owner, release owner, documentation owner, or maintainer with exact missing evidence and residual risk.

# Completion Criteria
The capability is complete when final closure accurately reconciles accepted plan, actual diff, generated outputs, validation freshness, review and repair scope, docs/registry/release artifacts, graph/memory/trajectory evidence, rollback, residual risk, and next gate without overstating completion or hiding scope drift.
