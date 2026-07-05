---
name: phase-review-capsule
description: "Use this skill when implementing, reviewing, planning, or validating product or code changes that need bounded independent review capsules for PDD, DDD, SDD, TDD, implementation, or closure reviews without raw prompts, transcripts, secrets, command output, or implementer self-approval."
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
metadata:
  changeforge.profile: recommended
  changeforge.skill_type: professional
---

# Phase Review Capsule

## Mission
Provide a bounded contract for independent phase review. The skill turns parent-approved summaries, artifact digests, source evidence summaries, and accepted constraints into a review capsule, and requires the reviewer to return only a structured `phase_review_result`.

## Stage Ownership

`phase-review-capsule` owns or reviews only the stage slices where its declared surface changes the next engineering decision. It hands off adjacent API, security/privacy, data middleware, reliability, release, documentation, or domain-extension work to the selected owner or gate instead of acting as a catch-all.

## Stage Fit

Use this skill as a cross-stage review gate, not as the active implementation stage. The current stage remains the artifact stage: PDD in requirement-intake, DDD and SDD in architecture-design or implementation-planning, TDD in testing, implementation review in code-review, and closure review in documentation-handoff. `phase-review-capsule` only constructs or validates bounded review evidence for that stage, then hands repair back to the artifact owner and re-review back to an independent reviewer.

For debugging-diagnosis, use this skill only when the diagnosis artifact itself needs independent review; root-cause discovery still belongs to `failure-diagnosis`. For release-delivery, use it only when release evidence depends on an already-created phase review result; rollout, rollback, and CI proof remain owned by `delivery-release-gate`.

## When To Use
- A PDD, DDD, SDD, TDD, implementation, or closure artifact needs independent review.
- A subagent, reviewer agent, or separate context is asked to review phase evidence.
- Parent runtime state needs review proof without importing raw reviewer reasoning.
- A review failure must create repair and re-review evidence tied to a finding ID.

## Do Not Use When
- The task is trivial and does not require formal phase evidence.
- The requester wants implementation, not review.
- The only available context is raw prompt text, raw command output, secrets, or full transcripts.
- The reviewer cannot return a structured `phase_review_result`.

## Adjacent Skill Conflict Resolution

For `phase-review-capsule`, keep this skill primary only when bounded independent review capsules for PDD, DDD, SDD, TDD, implementation, or closure need to be produced or validated. Hand API/schema compatibility to `data-api-contract-changer`, storage/query/migration concerns to `data-middleware-change-builder`, security/privacy decisions to `security-privacy-gate`, reliability/observability decisions to `reliability-observability-gate`, release/rollback readiness to `delivery-release-gate`, and documentation contract updates to `change-documentation-gate`. Domain extensions add risk-specific addenda after the primary owner is selected; record skipped plausible owners when the routing choice affects handoff or validation.

## Required Context / Missing Information Policy

Before `phase-review-capsule` plans or closes work, collect current behavior, desired behavior, non-goals, affected surface, owner module, validation signal, existing conventions, and material data/API/security/release boundaries. Ask or block only when the missing fact can change public contract, data model, authorization, tenant behavior, migration/rollback, irreversible operation, or domain semantics; otherwise proceed with explicit reversible assumptions.

## Critical Gotchas

- `phase-review-capsule` must inspect the owning source, tests, configs, docs, and generated-artifact boundaries before planning material engineering work.
- `phase-review-capsule` must select only risk-changing references, capabilities, gates, or domain extensions; do not load nearby material because it exists.
- `phase-review-capsule` must close with fresh validation evidence, evidence limits, residual risk, and next owner or gate when work remains.

## Non-Negotiable Rules
- The parent context may provide only `review_capsule` fields: bounded request summary, accepted constraints, bounded source evidence, artifact digest, and artifact summary.
- The reviewer must return only `phase_review_result`; raw reasoning and transcript text are not parent-state evidence.
- Implementer self-approval cannot pass a phase review.
- `process_phase_ledger_seen`, `pdd_reviewed`, `ddd_reviewed`, `sdd_reviewed`,
  and `tdd_reviewed` booleans are telemetry shortcuts only; closure proof
  requires a latest ledger-backed phase status with an artifact digest and
  review ID, or `not_applicable` with a concrete reason.
- TDD review verifies the test plan, acceptance-to-tests mapping,
  invariant-to-tests mapping, failure-mode tests, validation commands, and what
  tests do not prove. It must not require post-implementation command execution;
  execution freshness is closure evidence.
- `fail`, `needs_user_choice`, and `insufficient_evidence` verdicts block the next phase.
- Every blocking finding must include `finding_id`, severity, evidence, required fix, and `blocks_next_stage`.
- Repair must cite the original `finding_id`; re-review must cite the same `finding_id` and pass.

### Task Implementation Review

Task implementation review uses ordinary text before any internal capsule evidence is derived. Review against two gates:

1. **Spec Compliance**: every acceptance criterion implemented, no extra behavior added, requested behavior understood, non-goals preserved.
2. **Code Quality**: structure, names, tests, error handling, reuse/placement, and planned-file boundaries are sound.

The review output must name reviewed files/scope, findings by Critical / Important / Minor severity, required next action, residual risk, and any unreviewed scope. A response that only says "looks good" is not review evidence.

## Industry Benchmarks
- NIST SSDF review evidence discipline: independent verification and bounded evidence for release decisions.
- Google Engineering Practices: reviewer scope, concrete findings, and explicit residual risk.
- OWASP Code Review Guide: security review must avoid untrusted hidden context and self-approval.
- ISO/IEC/IEEE 29148 requirements traceability: review decisions must connect artifacts, constraints, and verification evidence.

## Technical Selection Criteria
- Use this skill when review context must cross an agent boundary.
- Use direct in-parent review only when no subagent or separate reviewer is available.
- Require a digest for the artifact under review before claiming freshness.
- Prefer a different reviewer skill from the owner skill.

## Mode Selection
Select the review mode before creating or accepting review evidence.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| PDD/DDD/SDD/TDD phase review | `process_phase_ledger` has `review_pending` before DDD, SDD, TDD, or implementation. | Verify the phase gate, traceability matrix, artifact digest, blocker severity, and review owner separation. | `review_capsule`, matching `reviewed_artifact_digest`, `phase_review_result`, approved scope, validation map, residual risk, and next gate. | `development-process-orchestrator`, `quality-test-gate`, process phase gate | Skip implementation review until all required phase reviews pass. |
| Subagent review boundary | `SubagentStart` creates capsule context or parent asks a separate reviewer to inspect phase evidence. | Enforce trust boundary, allowed context, forbidden inputs, and parent reducer merge limits. | Capsule ID, bounded summaries, read-file digests, searched patterns, forbidden input list, returned `phase_review_result`, and transcript exclusion proof. | `agent-tool-permission-sandbox`, `security-privacy-gate`, subagent review gate | Do not merge raw subagent reasoning, raw prompt, or secrets. |
| Repair and re-review | `phase_review_findings` contains a blocking `finding_id` after a failed review. | Verify repair ownership, changed files, behavior preservation, validation freshness, and matching re-review verdict. | Original finding, `phase_repair_event`, `phase_rereview_event`, passing verdict, validation evidence, and what evidence does not prove. | `ai-code-review-refactor`, `quality-test-gate`, closure contract gate | Block closure until repair and re-review both match the finding ID. |
| Adapter-degraded review | Runtime lacks `PreToolUse`, `SubagentStop`, hard Stop, command outcome, or observable validation evidence. | Disclose unsupported enforcement, record degraded capability, and route to parent-context or CI proof. | Adapter capability matrix row, degraded check names, closure status, residual risk owner, validation report, and next gate. | `executor-adapter-protocol`, `delivery-release-gate`, stop closure gate | Do not claim full enforcement for unsupported adapter events. |
| Closure readiness review | Final closure depends on phase review records, artifact freshness, or repair proof. | Confirm every required phase has strong provenance, matching digest, no open blockers, and validation freshness after the final material edit. | Latest ledger-backed review status, digest match, review source, approved scope, repair/re-review map, validation evidence, proof limits, rollback note, and residual risk owner. | `agent-execution-discipline`, `plan-execution-consistency`, `quality-test-gate` | Do not treat final handoff `phase_reviews` prose as strong review evidence. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A phase is marked reviewed from final prose, owner notes, or a reminder hook.
  **Hidden risk:** silent unreviewed phase mutates wrong code because advisory text becomes false implementation readiness.
  **Required professional action:** require an independent `phase_review_result` with matching digest and approved scope before the next gate.
  **Route to:** `development-process-orchestrator`, `ai-code-review-refactor`.
  **Evidence required:** review ID, reviewer skill different from owner skill, verdict, score, digest match, approved files/behaviors/facts, and residual risk owner.
- **Signal:** A review result says "looks good" without files, behaviors, facts, or not-reviewed scope.
  **Hidden risk:** missing approved scope hides untested behavior and uninspected acceptance paths.
  **Required professional action:** block phase acceptance and require a bounded review result before the next gate.
  **Route to:** `quality-test-gate`, `agent-execution-discipline`.
  **Evidence required:** approved scope, boundaries inspected, validation map, what evidence proves, and what evidence does not prove.
- **Signal:** An SDD review touches public API, security, data, migration, payment, or rollback choices with no resolved option evidence.
  **Hidden risk:** material design choice is silently assumed and can break consumers, leak data, or make rollback unsafe.
  **Required professional action:** block SDD review until source/user/reuse evidence resolves the choice.
  **Route to:** `data-api-contract-changer`, `security-privacy-gate`.
  **Evidence required:** design decision point, rejected alternatives, selected option, validation evidence, residual risk, and next gate.
- **Signal:** A repair is claimed after a failed review but no re-review names the same finding ID.
  **Hidden risk:** fixed code bypasses independent review and stale validation can be used for closure.
  **Required professional action:** require repair and re-review records tied to the original finding.
  **Route to:** `ai-code-review-refactor`, `quality-test-gate`.
  **Evidence required:** finding ID, changed files, behavior preservation, validation evidence after repair, and passing re-review verdict.
- **Signal:** Copilot or a generic adapter lacks the event needed for hard enforcement.
  **Hidden risk:** unsupported runtime capability creates an unverified closure claim and missing hard block.
  **Required professional action:** record degraded enforcement and require parent-context review result or CI validation.
  **Route to:** `executor-adapter-protocol`, `delivery-release-gate`.
  **Evidence required:** adapter capability matrix row, degraded check, closure status, residual risk owner, and next gate.

## Risk Escalation
- Escalate to `security-privacy-gate` when evidence includes auth, permission, tenant, privacy, credential, or secret-adjacent surfaces.
- Escalate to `data-api-contract-changer` when review changes schema, API, serialization, or migration behavior.
- Escalate to `quality-test-gate` when traceability, test mapping, or validation freshness is weak.
- Escalate to `ai-code-review-refactor` when the implementation or review text was AI-generated.

## Critical Details
- `reviewed_artifact_digest` must match the artifact digest in the capsule or
  the current phase ledger.
- Passing phase review must include strong provenance: `review_source` in
  `subagent_review_gate`, `parent_independent_review_gate`, or `ci_review_gate`;
  `expected_artifact_digest`; `review_context_strength: strong`; and
  `reviewer_boundary` of `subagent`, `parent_context`, or `ci`.
- ClosureContract consumes the same strong review semantics as
  `phase_review_passes(..., require_strong_source=True)`; score below 4,
  `reviewer_skill == owner_skill`, empty approved scope, missing expected
  digest, digest mismatch, or critical/high/`blocks_next_stage` findings cannot
  pass.
- Final handoff `phase_reviews` are weak disclosure only and cannot advance a
  phase.
- If no real artifact digest exists, create `process_phase_artifact` first and
  obtain its digest before review; do not synthesize a digest that can pass.
- Implementation review is a separate result type. It must cover actual changed
  files and reviewed diff digest; final handoff prose cannot satisfy it.
- Score must be 4 or 5 for a passing phase review.
- Critical, high, or blocking findings prevent phase completion.
- Timestamp-only `reports/*.json` or `reports/*.md` diffs are not review
  evidence and should not be submitted.
- The capsule must not contain raw prompt text, raw secrets, full command output, implementer self-approval, or unverified completion claims.

## Failure Modes
Each failure mode must name condition or symptom, consequence or impact,
detection signal, prevention or repair, and required evidence. Otherwise,
return residual review, digest, provenance, or repair-risk to the owner.

- **Missing review result:** Missing `phase_review_result` returns `insufficient_evidence`.
- **Missing expected digest:** Missing expected artifact digest from capsule or ledger records
  `insufficient_evidence`; stale artifact digest blocks review acceptance.
- **Generic approval:** Generic approval without files, behaviors, facts, and residual risk is not evidence.
- **Unsupported adapter:** Copilot or unsupported runtimes must record degraded enforcement rather than claim SubagentStop enforcement.
- **Forbidden capsule input:** Raw prompt text, raw command output, secrets, environment variables, or full
  transcripts in a capsule are rejected or dropped before state merge.
- **Unrepaired finding:** Review findings without repair events block closure.
- **Unreviewed repair:** Repair events without passing re-review events tied to the same `finding_id`
  block closure.
- **Weak passing verdict:** A passing verdict with score below 4, critical/high blocker, or digest
  mismatch is treated as failed review evidence.

## Anti-Patterns
- **Self-approved capsule**: owner skill reviews its own artifact or omits reviewer boundary; detect by matching owner/reviewer or missing review source; repair by requiring independent review.
- **Digest theater**: result cites a digest that is absent, stale, or mismatched; detect by comparing expected and reviewed artifact digests; repair by recreating the artifact and rerunning review.
- **Unrepaired findings**: review findings exist without repair and passing re-review tied to the same `finding_id`; detect by missing repair events; repair before phase closure.

## Reference Loading Policy
Do not load every reference by default. For L1 `phase-review-capsule` work, use this body for ordinary capsule construction, review-result validation, repair/re-review checks, and handoff.

For L2, L3, L4, and L5 `phase-review-capsule` work, read `references/capabilities/index.md` only to locate selected capability references; load selected files at `references/capabilities/<capability-id>-<capability-name>.md`, then add adjacent skill or domain references only when route risk requires them.

When changing runtime behavior in this repository, inspect the owning review-capsule normalization, process-phase validation, subagent review gate, closure contract, review-capsule tests, and process-phase tests directly before planning. Validate with `scripts/validate-review-capsules.py`, `scripts/validate-process-phase-ledger.py`, and the matching runtime-governance test modules. When changing stage routing or documentation, inspect the stage model registry, Engineering Stage Model doc, and professionalism coverage audit.

## Execution Procedure

For `phase-review-capsule`: confirm activation and role; classify missing context; inspect relevant source/test/config/doc evidence; select mode, complexity, risk, and minimal references; execute or review only the owned surface; validate with concrete commands, diffs, tests, evals, or not-run limits; route repair through the owner; hand off with residual risk and next gate.

## Output Contract
Return either a bounded capsule or a bounded review result. The output must be
directly mergeable by the parent reducer and must not require reading raw
reviewer reasoning.

`review_capsule` fields: schema version, capsule id, review type, bounded user request summary, accepted constraints, source evidence, artifact phase, artifact digest, artifact summary, allowed context, and forbidden inputs.

`phase_review_result` fields: schema version, review id, phase, reviewer skill, owner skill, reviewed artifact digest, review source, capsule id, expected digest, context strength, reviewer boundary, verdict, score, findings, approved scope, not reviewed scope, required next action, and residual risk.

For every output, also state:

- **Return mode selected:** capsule, review, repair, or blocked, with trigger signal.
- **Return what evidence proves:** reviewed digest, approved phase facts, approved files, approved behaviors, and validation map.
- **Return what evidence does not prove:** uninspected consumers, unrun tests, unsupported adapter events, stale evidence, and scope exclusions.
- **Return boundaries inspected:** read files, searched patterns, artifact summary, owner skill, reviewer skill, and adapter capability facts.
- **Return behavior preservation evidence:** old behavior, changed files, compatibility risk, preservation tests, and remaining behavior gaps.
- **Return reuse / placement rationale:** existing owner, selected file/module, rejected locations, reuse candidates, and new-structure reason.
- **Return validation evidence:** command, result, freshness after final material edit, mapped acceptance/invariant/API/failure/logging coverage, and missing validation.
- **Return residual risk:** missing evidence, stale evidence, unsupported events, unreviewed scope, owner, and mitigation.
- **Return next gate:** proceed, repair, ask user, run validation, security review, API/data review, release gate, or no-next-gate rationale.
- **Return reducer merge safety:** bounded fields that parent state may merge, forbidden raw material excluded, unsupported proof downgraded, and any rejected capsule fields.

## Evidence Contract
Review evidence must be source-backed and bounded.

- **What evidence proves:** the reviewed artifact digest, phase-specific fields,
  approved files, approved behaviors, approved facts, and validation evidence
  covered by the review.
- **What evidence does not prove:** uninspected consumers, unrun validations,
  stale fixtures, unsupported adapter events, and behaviors outside the approved
  scope.
- **Boundaries inspected:** capsule source evidence, read files, searched
  patterns, artifact summary, accepted constraints, owner skill, reviewer skill,
  and adapter capability facts.
- **Validation evidence:** command, result, freshness after final material edit,
  and mapping to PDD acceptance, DDD invariants, SDD public API, failure modes,
  logging/security decisions, or accepted residual risk.
- **Behavior preservation:** old behavior, compatibility risk, changed files,
  tests or constraints preserving old behavior, and residual behavior gaps.
- **Reuse / placement rationale:** existing owner, selected file/module,
  rejected locations, reuse candidates, and why new structure is necessary.
- **Residual risk:** missing evidence, stale evidence, unsupported events,
  unreviewed scope, owner, and mitigation.
- **Next gate:** proceed, repair, ask user, run validation, security review,
  API/data review, release gate, or explicit no-next-gate rationale.

## Quality Gate
- Capsule fields are bounded and sanitized.
- Review result has a verdict, score, digest, reviewer skill, owner skill, and approved scope.
- Blocking findings have repair instructions and finding IDs.
- Unsupported adapter events are disclosed as degraded evidence.
- Output includes what evidence proves, what evidence does not prove,
  boundaries inspected, validation evidence, residual risk, and next gate.

## Handoff
Report the review type, artifact digest, verdict, score, finding IDs, approved scope, unreviewed scope, required next action, and residual risk. Do not hand off raw transcript or raw reviewer reasoning.

## Completion Criteria
- A passing review has `verdict: pass`, `score >= 4`, matching digest, and no critical/high/blocking findings.
- A failing review records repair requirements.
- A repaired finding has a matching re-review result.
- Parent runtime state receives only bounded capsule and review result records.
