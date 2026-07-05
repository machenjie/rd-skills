# Skill Efficacy Benchmark Evidence Patterns

Use this reference when closure depends on graph, memory, execution trajectory, validation freshness, generated reports, runtime profile output, privacy boundary, or proof limits. Keep it as an evidence map, not a second benchmark tutorial.

## Evidence Classification

| Evidence source | Use as | Reject as |
| --- | --- | --- |
| Current source diff | Treatment artifact and changed-path input. | Proof that behavior improved without a case. |
| Generated report | Structural evidence from the generating command. | Live agent performance or user productivity proof. |
| Repository graph | Selector for affected skills, references, registries, tests, reports, and runtime outputs. | Product intent or efficacy proof without current source. |
| Project memory | Lead to recurring failures, fragile skills, stale validation, or prior route disputes. | Current source truth without confirmation. |
| Execution trajectory | Order of edits, validations, failures, repairs, and re-runs. | Fresh evidence when validation predates final material edit. |
| Baseline artifact | Comparison point for old behavior. | A representative population unless sampling is defined. |
| Treatment artifact | Comparison point for changed behavior. | Proof of release safety without validators and caveats. |
| Validator output | Evidence for the validator's declared scope after final edit. | Evidence for unrun commands, external CI, or production behavior. |

## Freshness And Runtime Profile Map

| Changed item | Freshness trigger | Required validation evidence |
| --- | --- | --- |
| Capability or skill `SKILL.md` | Any body, trigger, output, evidence, or reference-loading change. | Body links, content size, professionalism eval, audit as applicable. |
| Bundled reference | New file, renamed file, Markdown link change, or deep reference added. | Body links, content size, build profile, runtime reference links. |
| Registry or routing rule | `used_by`, trigger, route_to, stage model, priority, or route manifest semantics change. | Registry validation, routing eval, routing coverage. |
| Hook/runtime support | Prompt template, state schema, script, adapter, or injected context changes. | Hook validation, build profiles, install validation. |
| Benchmark fixture or eval script | Case, expected output, validator logic, report schema, or promoted sample changes. | Fixture validator and matching eval command. |
| Generated report or dist output | Report/dist is regenerated or stale after source changes. | Source generator/eval/build command and install/runtime link validator. |

## Benchmark Closure Ledger

```yaml
skill_efficacy_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      source_or_report: ""
      finding: ""
      freshness: current|stale|not_verified
  baseline_treatment:
    same_task: true
    baseline_artifacts: []
    treatment_artifacts: []
    unavailable_baseline_reason: null
  metrics:
    routing_correctness: ""
    evidence_completeness: ""
    defect_catch: ""
    validation_freshness: ""
    over_routing: ""
    under_routing: ""
    token_overhead: not_collected
    turn_overhead: not_collected
  graph_memory_trajectory:
    accepted: []
    rejected_or_stale: []
    selector_limits: []
  changed_skill_to_validation:
    - changed_item: ""
      validator: ""
      outcome: passed|failed|stale|partial|not_run|not_verified
      proves: ""
      does_not_prove: ""
  privacy_boundary:
    retained_facts: []
    rejected_or_redacted: []
    redaction_rule: ""
  verdict:
    status: improved|regressed|no_change|unknown|not_enough_evidence
    structural_only: true
    claim_boundary: ""
  rollback_note: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```

## Graph, Memory, And Trajectory Reconciliation

- Accept graph evidence only after it points to current source, registry, generated artifact, report, or validator boundaries that were inspected.
- Accept project memory only as current evidence when date, owner, scope, and current-source confirmation are present.
- Mark validation stale when any material source, reference, registry, hook, fixture, report, build output, or owner decision changes after the command.
- Preserve repaired failures as evidence only when a later validator covers the failed scope.
- If a compaction or summary records prior validation, use it as a locator, then confirm the current log or rerun the command.

## Proof Limits

| Claim | Required wording |
| --- | --- |
| Static validator passed | "The validator passed for the checked fixture/report scope." |
| Score improved | "The score improved for the evaluator dimensions measured by this report." |
| Runtime references valid | "Built profile Markdown links are valid after build." |
| Agent behavior improved | Only allowed with representative agent-run evidence, sampling limits, and caveats. |
| Efficiency improved | Requires selected/skipped count plus token/turn overhead or `not_collected` caveat. |
| Safer closure | Requires negative baseline or forbidden behavior case caught by treatment. |

## Tool And Output Boundary

| Action | Boundary record |
| --- | --- |
| Local source/report inspection | Read-only local shell; cite bounded slices and avoid full output dumps. |
| Eval, validator, build, install checks | Local-write to reports, caches, dist, or temporary artifacts; cite command, exit code, log path, freshness. |
| Live benchmark or connector lookup | Requires explicit maintainer authorization, account/data boundary, redaction, and retention note. |
| Destructive cleanup or deploy | Out of scope for ordinary skill efficacy benchmarking; require owner approval and rollback path. |

## Handoff Rules

- Hand off as `not_enough_evidence` when baseline, treatment, metrics, validator, or caveat is missing.
- Hand off as `unknown` when evidence is valid but does not discriminate old and new behavior.
- Hand off as `improved` only when the treatment is better on the named metric and evidence limits are explicit.
- Always include rollback note, residual risk owner, and next gate when a benchmark supports release, docs, or further skill authoring.
