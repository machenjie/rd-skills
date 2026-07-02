---
name: phase-review-capsule
description: Produces and validates bounded independent review capsules for PDD, DDD, SDD, TDD, implementation, and closure reviews so subagents can review artifacts without raw prompts, transcripts, secrets, command output, or implementer self-approval leaking back into parent runtime state.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Phase Review Capsule

## Mission
Provide a bounded contract for independent phase review. The skill turns parent-approved summaries, artifact digests, source evidence summaries, and accepted constraints into a review capsule, and requires the reviewer to return only a structured `phase_review_result`.

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

## Non-Negotiable Rules
- The parent context may provide only `review_capsule` fields: bounded request summary, accepted constraints, bounded source evidence, artifact digest, and artifact summary.
- The reviewer must return only `phase_review_result`; raw reasoning and transcript text are not parent-state evidence.
- Implementer self-approval cannot pass a phase review.
- `pdd_reviewed`, `ddd_reviewed`, `sdd_reviewed`, and `tdd_reviewed` booleans
  are telemetry shortcuts only; closure proof requires ledger-backed reviewed
  phase status with an artifact digest and review ID, or `not_applicable` with a
  concrete reason.
- `fail`, `needs_user_choice`, and `insufficient_evidence` verdicts block the next phase.
- Every blocking finding must include `finding_id`, severity, evidence, required fix, and `blocks_next_stage`.
- Repair must cite the original `finding_id`; re-review must cite the same `finding_id` and pass.

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

## Mode Matrix
Select the review mode before creating or accepting review evidence.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| PDD/DDD/SDD/TDD phase review | `process_phase_ledger` has `review_pending` before DDD, SDD, TDD, or implementation. | Verify the phase gate, traceability matrix, artifact digest, blocker severity, and review owner separation. | `review_capsule`, matching `reviewed_artifact_digest`, `phase_review_result`, approved scope, validation map, residual risk, and next gate. | `development-process-orchestrator`, `quality-test-gate`, process phase gate | Skip implementation review until all required phase reviews pass. |
| Subagent review boundary | `SubagentStart` creates capsule context or parent asks a separate reviewer to inspect phase evidence. | Enforce trust boundary, allowed context, forbidden inputs, and parent reducer merge limits. | Capsule ID, bounded summaries, read-file digests, searched patterns, forbidden input list, returned `phase_review_result`, and transcript exclusion proof. | `agent-tool-permission-sandbox`, `security-privacy-gate`, subagent review gate | Do not merge raw subagent reasoning, raw prompt, or secrets. |
| Repair and re-review | `phase_review_findings` contains a blocking `finding_id` after a failed review. | Verify repair ownership, changed files, behavior preservation, validation freshness, and matching re-review verdict. | Original finding, `phase_repair_event`, `phase_rereview_event`, passing verdict, validation evidence, and what evidence does not prove. | `ai-code-review-refactor`, `quality-test-gate`, closure contract gate | Block closure until repair and re-review both match the finding ID. |
| Adapter-degraded review | Runtime lacks `PreToolUse`, `SubagentStop`, hard Stop, command outcome, or observable validation evidence. | Disclose unsupported enforcement, record degraded capability, and route to parent-context or CI proof. | Adapter capability matrix row, degraded check names, closure status, residual risk owner, validation report, and next gate. | `executor-adapter-protocol`, `delivery-release-gate`, stop closure gate | Do not claim full enforcement for unsupported adapter events. |

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

## Risk Escalation Rules
- Escalate to `security-privacy-gate` when evidence includes auth, permission, tenant, privacy, credential, or secret-adjacent surfaces.
- Escalate to `data-api-contract-changer` when review changes schema, API, serialization, or migration behavior.
- Escalate to `quality-test-gate` when traceability, test mapping, or validation freshness is weak.
- Escalate to `ai-code-review-refactor` when the implementation or review text was AI-generated.

## Critical Details
- `reviewed_artifact_digest` must match the artifact digest in the capsule or
  the current phase ledger.
- Score must be 4 or 5 for a passing phase review.
- Critical, high, or blocking findings prevent phase completion.
- The capsule must not contain raw prompt text, raw secrets, full command output, implementer self-approval, or unverified completion claims.

## Failure Modes
- Missing `phase_review_result` returns `insufficient_evidence`.
- Missing expected artifact digest from capsule or ledger records
  `insufficient_evidence`; stale artifact digest blocks review acceptance.
- Generic approval without files, behaviors, facts, and residual risk is not evidence.
- Copilot or unsupported runtimes must record degraded enforcement rather than claim SubagentStop enforcement.
- Raw prompt text, raw command output, secrets, environment variables, or full
  transcripts in a capsule are rejected or dropped before state merge.
- Review findings without repair events block closure.
- Repair events without passing re-review events tied to the same `finding_id`
  block closure.
- A passing verdict with score below 4, critical/high blocker, or digest
  mismatch is treated as failed review evidence.

## Reference Loading Policy
Start at `references/capabilities/index.md` only when a selected capability is needed. Load only the selected capability reference at the matching depth: L1 for quick review scope checks, L2 for phase contract details, L3 for security/data/API risk review, L4 for release or adapter enforcement risk, and L5 for regression or benchmark changes. Capability files follow `references/capabilities/<capability-id>-<capability-name>.md`; do not read all references by default.

## Output Contract
Return either a bounded capsule or a bounded review result. The output must be
directly mergeable by the parent reducer and must not require reading raw
reviewer reasoning.

```yaml
review_capsule:
  schema_version: 1
  capsule_id: sdd-capsule-1
  review_type: sdd
  user_request_summary: bounded summary only
  accepted_constraints: []
  source_evidence:
    read_files: []
    searched_patterns: []
  artifact_under_review:
    phase: sdd
    artifact_digest: sha256:...
    artifact_summary: bounded summary only
  allowed_context:
    - user_request_summary
    - accepted_constraints
    - source_evidence
    - artifact_under_review
  forbidden_inputs:
    - raw prompt
    - raw secrets
    - full command output
    - implementer self-approval
    - unverified completion claims
```

or:

```yaml
phase_review_result:
  schema_version: 1
  review_id: sdd-review-1
  phase: sdd
  reviewer_skill: phase-review-capsule
  owner_skill: development-process-orchestrator
  reviewed_artifact_digest: sha256:...
  verdict: pass
  score: 5
  findings: []
  approved_scope:
    files: []
    behaviors: []
    facts: []
  not_reviewed: []
  required_next_action:
    - proceed
  residual_risk: []
```

For every output, also state:

- **Return what evidence proves:** reviewed digest, approved phase facts, approved files, approved behaviors, and validation map.
- **Return what evidence does not prove:** uninspected consumers, unrun tests, unsupported adapter events, stale evidence, and scope exclusions.
- **Return boundaries inspected:** read files, searched patterns, artifact summary, owner skill, reviewer skill, and adapter capability facts.
- **Return behavior preservation evidence:** old behavior, changed files, compatibility risk, preservation tests, and remaining behavior gaps.
- **Return reuse / placement rationale:** existing owner, selected file/module, rejected locations, reuse candidates, and new-structure reason.
- **Return validation evidence:** command, result, freshness after final material edit, mapped acceptance/invariant/API/failure/logging coverage, and missing validation.
- **Return residual risk:** missing evidence, stale evidence, unsupported events, unreviewed scope, owner, and mitigation.
- **Return next gate:** proceed, repair, ask user, run validation, security review, API/data review, release gate, or no-next-gate rationale.

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
