# Solution Optimality Evidence Patterns

Use this reference when closure depends on candidate-to-validation mapping, graph/memory/benchmark freshness, structural-vs-empirical proof limits, or changed-decision-to-validation evidence. Keep the main body for the decision contract; load this file only for concrete evidence closure.

## Claim To Evidence Map

| Claim | Minimum evidence | Does not prove |
| --- | --- | --- |
| Candidate comparison is real | Problem statement, at least two viable candidates, chosen rationale, strongest rejected alternative, and specific rejection cost. | The chosen approach is globally optimal. |
| Simpler path was considered | Delete/reuse/native/local-direct/new-abstraction ladder with selected and rejected options. | Future requirements will not justify a different shape. |
| Performance risk is bounded | Ten-dimension assessment, workload shape, hot/cold classification, budget or measurement plan, and not-run limits. | Production performance without representative benchmark/load evidence. |
| Graph or memory is fresh | Current source/config/report paths inspected, accepted/rejected memory claims, validation order after final edit. | Historical benchmark or generated report remains valid after future edits. |
| AI or refactor optimality is safe | Before/after behavior, complexity delta, hidden I/O/allocation/concurrency scan, hallucinated API check, changed-path validation. | Every maintainability risk is removed. |
| Deferral is controlled | Explicit threshold, owner, revisit signal, rollback or replacement clue, and residual risk accepted by owner. | The optimization can be ignored indefinitely. |

## Decision Validation Map

```yaml
changed_decision_to_validation_map:
  decision: ""
  chosen_candidate: ""
  rejected_candidates: []
  scale_assumption: ""
  validation:
    benchmark_or_command: ""
    covers:
      - complexity
      - resource_budget
      - behavior_preservation
      - reversibility
  does_not_prove: []
  deferral_threshold: ""
  residual_risk_owner: ""
```

## Closure Checks

- Do not claim production readiness from local fixture tests, stale reports, or a single benchmark without scope limits.
- Treat "best practice", "fast enough", "cleaner", and "we can optimize later" as claims requiring evidence or explicit deferral.
- Separate structural validators from empirical performance evidence.
- Rerun or downgrade validation if source, config, benchmark data, generated report, or workload assumptions changed after the evidence was captured.
