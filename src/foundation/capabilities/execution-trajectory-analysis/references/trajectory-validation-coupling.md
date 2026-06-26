# Trajectory Validation Coupling

Use this reference when a multi-step execution path needs event schema, lifecycle transition rules, validation freshness, graph/memory coupling, repair re-review gates, or fixture-candidate governance. The `SKILL.md` body remains the route-time contract; this reference is loaded only for concrete trajectory records or reviews.

## Event Schema

| Field | Meaning | Boundary |
| --- | --- | --- |
| `event_id` | Stable local id in event order. | No raw prompt, log, or full output. |
| `stage` | Read, plan, edit, review, repair, validation, build, release, compaction, stop, or handoff. | Use stage label, not hidden reasoning. |
| `artifact` | Bounded path, path family, report, registry, generated artifact, command class, or fixture candidate. | Avoid unrelated files and personal data. |
| `action_class` | Read, search, patch, format, test, eval, build, install-check, review, handoff, or permission check. | Summarize only. |
| `owner_skill` | Skill or capability responsible for the action. | Use names, not private rationale. |
| `reviewer_skill` | Reviewer/gate required after repair or risk escalation. | Empty only when no review obligation exists. |
| `outcome` | Passed, failed, partial, stale, not-run, not-verified, candidate, or blocked. | Include evidence limit. |
| `order` | Timestamp, command sequence, or relative position. | Must be enough to compare with later edits. |
| `privacy_class` | Public repo fact, bounded runtime fact, sensitive-excluded, or promotion-candidate. | Sensitive material is excluded. |

## Lifecycle Transition Rules

| Transition | Allowed When | Defect Signal | Repair |
| --- | --- | --- | --- |
| Read -> Plan | Source, registry, docs, or reports relevant to target were inspected. | Plan relies on stale memory or graph only. | Reread current source and update route. |
| Plan -> Edit | Plan names target boundary, owner, validation idea, and risk gates. | Edit touches unplanned surface. | Record placement rationale and refresh graph/plan. |
| Edit -> Validation | Validator maps to changed path and risk surface. | Command is guessed or unrelated. | Route to `validation-broker`. |
| Review -> Repair | Finding id and changed files are named. | Repair not tied to finding. | Reconstruct ledger and re-review. |
| Repair -> Review | Repaired diff is inspected by reviewer/gate. | Approval predates repair. | Run targeted re-review before closure. |
| Validation -> Handoff | Command ran after final material edit and covers changed paths. | Pass predates later edit or is partial. | Rerun, downgrade, or disclose residual risk. |
| Failure -> Retry | Cause or hypothesis changed after first failure. | Same command/path attempted twice unchanged. | Route diagnosis or blocked handoff before third attempt. |
| Candidate -> Promotion | Privacy review and maintainer/eval authoring approval exist. | Candidate reported as measured evidence. | Mark candidate only and defer promotion. |

## Freshness Matrix

| Situation | Status | Required Action |
| --- | --- | --- |
| Validation after final material edit and covers changed paths. | Current. | Can support closure with evidence limits. |
| Validation before later source, registry, hook runtime, generated artifact, report, benchmark, package, or install-output edit. | Stale. | Rerun mapped validator or disclose not verified. |
| Validation covers lint/typecheck while behavior, registry, routing, or install behavior changed. | Partial. | Add relevant unit, integration, eval, build, or install check. |
| Validation fails and the same command is retried twice unchanged. | Repeated failure. | Route to diagnosis or change approach before another retry. |
| Validation unavailable because adapter or connector lacks evidence channel. | Degraded. | State unsupported channel and exact verification command. |
| Review approval predates repair. | Stale review. | Re-review repaired diff or downgrade closure. |
| Graph, memory, or compaction summary predates later edits. | Stale context. | Refresh, reread source, or treat as selector-only. |

## Coupling Rules

1. Memory repeat-failure signals raise the minimum trajectory review depth for the same path, command, diagnosis, or failure class.
2. Repository graph freshness gates whether edit-before-read is acceptable; stale or missing graph evidence requires direct source reread or graph refresh.
3. Validation broker results determine whether command outcomes are relevant to final changed paths and risk surfaces.
4. Review repair records are incomplete until the reviewer or designated gate inspects the repaired diff.
5. Fixture candidates remain candidate evidence until privacy review and explicit eval authoring promote them.
6. Compaction summaries can preserve bounded trajectory facts, but cannot replace final source diff, validation freshness, or reviewer evidence.
7. Generated artifacts, reports, and install outputs are evidence only when their source and build/validation command are named.
8. Closure advice must downgrade when any coupled evidence is stale, partial, not-run, not-verified, or privacy-sensitive.

## Changed Trajectory To Validation Map

| Trajectory Item | Map To | Closure Rule |
| --- | --- | --- |
| Source edit | Direct/affected validator or explicit no-validator rationale. | No full-pass claim from unrelated command. |
| Registry or routing edit | Registry validator, routing eval, and affected skill/body-link checks. | Require full suite if route-level behavior changes. |
| Hook runtime or adapter edit | Hook validator, runtime reference link check, and install/build check. | Do not install source directly. |
| Generated artifact or report | Source generator and build/eval command that produced it. | Generated-only edit cannot close. |
| Review repair | Re-review command or reviewer/gate inspection. | Approval must postdate repair. |
| Repeated failure | Diagnosis route or blocked handoff. | Third same-path retry is not closure evidence. |
| Fixture candidate | Privacy review and eval authoring path. | Candidate is not measured behavior evidence. |

## Privacy And Fixture Governance

- Retain bounded facts: stage, path family, command class, result status, owner/reviewer skill, order, and evidence limit.
- Exclude raw prompts, secrets, personal data, environment variables, credentials, access tokens, and full command output.
- Treat local runtime facts as private until explicitly promoted by a maintainer.
- Candidate fixtures must name the reviewed failure pattern, excluded sensitive material, proposed eval location, promotion owner, and rollback path.
- A candidate can inform review depth immediately, but cannot become durable skill policy without explicit authoring review.

## Output Template

```yaml
execution_trajectory_analysis:
  mode_selected: validation_freshness_gate
  boundaries_inspected:
    source: []
    registry_or_config: []
    reports_or_generated: []
    validation_output: []
    graph_memory_review: []
    skipped_with_reason: []
  trajectory_events:
    - event_id: e1
      stage: read
      artifact: src/path
      action_class: read
      owner_skill: repository-context-map
      reviewer_skill: null
      outcome: current
      order: before_edit
      privacy_class: public_repo_fact
  findings_and_repair_ledger:
    illegal_transitions: []
    repair_re_review: []
    repeated_failures: []
    closure_gaps: []
  validation_freshness_timeline:
    - command: python3 scripts/validate-skills.py
      covered_paths: []
      outcome: passed
      later_edits: []
      freshness: current
      evidence_limit: targeted_or_full_scope
  graph_memory_validation_coupling:
    accepted: []
    rejected_or_stale: []
    closure_consequence: ready
  changed_trajectory_to_validation_map: []
  closure_advice: ready
  evidence_limits: []
  residual_risk: []
  rollback_note: revert the capability SKILL.md/reference changes and rerun validators
```
