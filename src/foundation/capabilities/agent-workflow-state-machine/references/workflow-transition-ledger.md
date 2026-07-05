# Workflow Transition Ledger

Use this reference when multi-step work needs a concrete stage ledger, legal transition check, owner/reviewer map, validation freshness decision, adapter lifecycle reconciliation, trajectory review, repair/re-review tracking, or closure readiness package. The capability body remains the route-time contract; this file is loaded only for concrete workflow records.

# State Fields

| Field | Required evidence | Closure risk if missing |
| --- | --- | --- |
| `stage_id` | One canonical current stage. | Handoff can claim two incompatible states. |
| `entry_evidence` | Requirement status, source reads, route/stage manifest, validation signal, or owner input needed to enter. | Work may start from an illegal state. |
| `exit_criteria` | Evidence required before next transition. | Stage may close without proof. |
| `next_stage` | One allowed next stage or closed/blocked state. | Action owner cannot tell what to do next. |
| `transition_reason` | Why current evidence permits, blocks, or downgrades the transition. | Completion claim becomes unsupported. |
| `owner_skill` | Skill/capability responsible for action. | Repair or validation has no accountable owner. |
| `reviewer_skill` | Different skill/capability responsible for review or gate. | Self-approval can pass unnoticed. |
| `validation_freshness` | Command, outcome, scope, covered paths, later edits, freshness verdict. | Stale validation can be reported as current. |
| `repair_ledger` | Finding id, repair owner, changed files, re-review status, unresolved findings. | Review findings can disappear without closure. |
| `adapter_state` | Supported lifecycle fields, unsupported fields, fallback state, degradation note. | Runtime event gaps may be overclaimed. |
| `trajectory_state` | Ordered bounded events for read, plan, edit, test, review, repair, stop, handoff. | Event order defects are hidden. |
| `closure_package` | Route manifest, stage manifest, plan consistency, validation, residual risk, rollback note, next owner. | Handoff lacks audit-ready evidence. |

# Allowed Transition Matrix

| From | To | Minimum evidence |
| --- | --- | --- |
| request-intake | clarification | User request, missing information, assumptions, non-goals, risk surface. |
| clarification | repository-read | Clarified objective or explicit assumption, source boundary to inspect, route signal. |
| repository-read | planning | Current source/registry/docs/tests inspected, same-pattern scan when editing, graph freshness or direct-source fallback. |
| planning | coding | Accepted plan, owning surface, source-vs-generated boundary, TDD/eval/validation signal, permission/sandbox status. |
| coding | validation | Material edits complete for the pass, changed-path map, validator candidates. |
| validation | code-review | Parsed command outcome, covered/uncovered paths, freshness verdict, negative evidence preserved. |
| code-review | repair | Finding id, severity, affected path, reviewer scope, repair owner. |
| repair | validation | Repair diff, mapped validators, stale prior validation marked unusable. |
| validation | re-review | Fresh validation or disclosed not-verified status, repaired finding and changed files. |
| re-review | documentation-handoff | Targeted re-review result, unresolved findings, plan consistency, docs or no-docs decision. |
| documentation-handoff | release-readiness | Release/install/package impact, artifact state, rollback note, validation limits. |
| release-readiness | closed | Fresh validation for final material state, residual risk, rollback/restore note, next owner or none. |
| any non-closed stage | blocked | Blocking condition, failed/stale/not-run evidence, owner who can unblock, no repeated same-path retry. |

# Illegal Transition Examples

1. Request directly to implementation without clarification status, repository context, and validation signal.
2. Plan directly to closure without edited-path evidence, validation, review, and residual-risk statement.
3. Review to closure while findings remain unrepaired, unre-reviewed, or outside the approval scope.
4. Test pass to closure when later material edits made the pass stale.
5. Repair to closure without targeted re-review of the original finding and repaired diff.
6. Stop after two same-path failures without route repair, new evidence, or blocked handoff.
7. Adapter event to closure when the adapter does not support the lifecycle field being claimed.
8. Handoff without route/stage state, validation limit, residual risk, rollback note, and next owner.

# Entry and Exit Evidence

| Stage | Entry evidence | Exit evidence |
| --- | --- | --- |
| clarification | Request, ambiguity, assumptions, non-goals. | Clarified objective or assumption record plus risk surface. |
| repository-read | Target boundary and route signal. | Inspected source, registry/config/docs/tests, same-pattern scan, source-of-truth decision. |
| planning | Current context and owner surface. | Plan, rejected complexity, validation signal, next owner, review gate. |
| coding | Accepted plan and edit permission. | Changed files, diff scope, generated/source boundary, no unrelated churn note. |
| validation | Changed-path map and validator candidates. | Command outcome, scope, freshness, negative evidence, next validator if failed. |
| code-review | Final diff candidate and validation status. | Findings, approval scope, unresolved risk, repair owner when needed. |
| repair | Finding id and repair owner. | Repair diff, mapped validation, re-review request. |
| re-review | Repair diff and original finding. | Re-review result, uncovered diff areas, closure or next repair. |
| documentation-handoff | Validated boundary and docs impact. | Updated docs or no-doc rationale, validation limits, handoff target. |
| release-readiness | Artifact/install/package impact. | Build/install/release validation, rollback path, release residual risk. |
| closed | All required gates satisfied or explicitly not verified. | Final handoff with evidence, unknowns, validation limits, rollback note, residual risk. |
| blocked | Blocking condition and owner. | User/external answer, new evidence, changed route, or explicit blocked status. |

# Owner and Reviewer Separation

- The owner performs the action; the reviewer/gate evaluates it. They must be different skills or capabilities.
- A validation command can support review, but it is not an independent reviewer unless a review gate interprets scope and residual risk.
- A repair owner may be the original implementer, but the re-reviewer must be independent from the repair action.
- Approval scope must name files, behavior, finding ids, validators, and excluded areas.
- If no independent reviewer is available, closure status is `not verified` or `blocked`, not approved.

# Repair and Re-Review Ledger

| Ledger field | Required content |
| --- | --- |
| `finding_id` | Stable id or short finding label. |
| `severity` | Blocking, major, minor, or advisory. |
| `repair_owner` | Skill/capability responsible for the repair. |
| `repair_diff` | Files changed and behavior or content affected. |
| `post_repair_validation` | Command, outcome, freshness, or not-run rationale. |
| `re_reviewer` | Independent reviewer/gate. |
| `re_review_result` | Approved, still failing, partial, not verified, or blocked. |
| `uncovered_scope` | Diff, tests, generated outputs, docs, or release surface not re-reviewed. |

# Repeated Failure Stop Rule

1. Count attempts by same command, diagnosis, patch route, or validation failure class.
2. After two failures on the same path, record the failure class and current hypothesis.
3. Before a third attempt, require one of: verified cause, different route, stronger validator, broader graph/context read, maintainer input, or blocked handoff.
4. Do not relabel the same retry as repair unless new evidence changed the transition.

# Adapter, Trajectory, Graph, Memory, and Validation Coupling

| Evidence source | Can do | Cannot do |
| --- | --- | --- |
| Executor adapter | Provide supported lifecycle state, command class, permission/sandbox state, and missing-field limits. | Prove an unsupported lifecycle event or replace review. |
| Execution trajectory | Order read/plan/edit/test/review/repair/stop/handoff events and freshness. | Store raw prompts, secrets, environment variables, credentials, or full command output. |
| Repository graph | Identify source truth, affected tests, owners, generated artifacts, and graph freshness. | Replace current source inspection for behavior-critical claims. |
| Project memory | Widen scope, mark stale/fragile/repeated failures, and propose promotion. | Become source truth or silently mutate durable policy. |
| Validation broker | Parse command outcome, scope, negative evidence, and freshness. | Turn targeted or stale validation into full closure proof. |

# Output Template

```yaml
workflow_state_summary:
  mode_selected: stop/handoff closure
  boundaries_inspected:
    requirements: current
    source: [path/or/surface]
    registry_config_docs: [path/or/none]
    tests_evals_reports: [path/or/not-inspected]
    generated_install_outputs: [path/or/not-applicable]
    graph_memory_trajectory_adapter: current|stale|partial|not-used
    skipped_boundaries: [boundary with reason]
  workflow_state:
    current_stage: validation
    entry_evidence: [evidence]
    exit_criteria: [required evidence]
    prior_stage: coding
    next_stage: code-review
    legal_transition: allowed|blocked|not-verified
    stop_condition: none|two-failure-gate|blocked-owner
  owner_review_map:
    owner_skill: implementation-owner
    reviewer_skill: independent-reviewer
    independence: confirmed|not-verified
    approval_scope: [files/findings/behavior]
  validation_freshness:
    commands: [command and outcome summary]
    covered_paths: [paths]
    later_edits: [none|paths]
    status: current|stale|partial|failed|not-run|not-verified
  repair_rereview_ledger:
    findings: []
    unresolved_findings: []
  coupling:
    adapter_limits: [supported and unsupported lifecycle fields]
    trajectory_order: current|stale|partial|not-used
    graph_memory_verdict: accepted|rejected|stale|not-used
  closure_decision:
    status: ready|needs-read|needs-repair|needs-rereview|needs-validation|blocked
    evidence_limits: [limits]
    rollback_note: [reversal path]
    residual_risk: [risk]
    next_owner: [owner or none]
```
