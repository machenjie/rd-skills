# Trajectory Handoff Closure Map

Use this reference when trajectory findings must become concrete validation, re-review, rollback, blocked-handoff, or next-owner decisions.

## Finding To Closure Map

| Finding | Required map | Closure rule |
| --- | --- | --- |
| Edit before read | Current source reread, source-of-truth decision, same-pattern scan, validator. | Cannot close until direct-source fallback and validation are current or residual risk is owned. |
| Repair after review | Finding id, repaired files, reviewer/gate, re-review result. | Review approval must postdate repair. |
| Stale validation | Command, covered paths, later edits, selected rerun or not-run gap. | Passing command cannot support final closure until rerun or downgraded. |
| Repeated failure | Attempt ledger, failure class, changed hypothesis, next diagnostic owner. | Third same-path retry is blocked. |
| Stale memory or graph | Accepted/rejected claims, current source reread, validation broker adequacy. | Prior context is selector-only until reconciled. |
| Fixture candidate | Privacy status, promotion owner, eval-authoring path, rollback. | Candidate is not durable policy or measured behavior evidence. |
| Unsupported adapter event | Unsupported channel, degraded evidence, exact verification fallback. | Closure language must name unsupported capability and residual risk. |

## Closure Decision Fields

```yaml
handoff:
  closure_decision: "ready|needs_source_reread|needs_repair|needs_re_review|needs_validation|needs_fixture_review|blocked|not_verified"
  owner_reviewer_route: ""
  validation_limits: []
  rollback_note: ""
  next_gate: ""
```

## Validator Mapping Rules

1. Map changed source, registry, hook runtime, generated artifact, report, package, and install-output paths to a validator or explicit no-validator rationale.
2. Escalate to full repository validation when trajectory findings cross registry, routing, hook runtime, generated artifact, package, or install boundaries.
3. Preserve negative evidence: failed, stale, partial, skipped, unsupported, and not-run results remain visible after later passes.
4. Re-run validators after the final material edit or mark the previous run stale.
5. State what the validation proves and what it does not prove before closure.

## Rollback And Residual Risk

- Rollback for skill-authoring trajectory changes is file-level revert plus regeneration of reports and build artifacts.
- Residual risk names unknown trajectory areas, omitted event families, stale evidence, unsupported adapter channels, and unpromoted fixture candidates.
- Handoff names the next owner rather than using generic completion language when any closure input is partial, stale, missing, or privacy-sensitive.
