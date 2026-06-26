# Memory Validation Promotion Gates

Use this reference when an accepted memory signal must change validation depth, review scope, owner response, rollback, or human promotion. The main body owns the gate; this file keeps the detailed mapping small and explicit.

## Memory To Validation Map

| Accepted signal | Required validator or review | What evidence proves | What evidence does not prove |
| --- | --- | --- | --- |
| Repeat failure | New hypothesis plus targeted validator or blocked handoff. | The next attempt differs from the failed path. | The root cause is fixed unless current validation passes. |
| Fragile file | Source reread, same-pattern scan, affected test/build/eval mapping. | The current edit considered known fragility. | Uninspected callers, owners, or generated outputs are safe. |
| Stale context | Direct source refresh and validation freshness check. | Prior evidence was accepted, rejected, or downgraded. | Old reports remain valid after later edits. |
| Validation gap | `validation-broker` depth selection and negative-evidence ledger. | The gap has a current validator or residual owner. | A targeted pass is full regression coverage. |
| Review follow-up | Targeted re-review after repair. | The repaired diff matches the review concern. | Other review findings were resolved unless inspected. |
| Promotion candidate | Maintainer decision, placement rationale, privacy review, and full repository validators. | Durable source update is approved for the named artifact. | Memory may mutate policy automatically. |

## Promotion Gate

1. Current source confirms the repeated pattern, fragile boundary, stale-context failure, validation gap, or review follow-up.
2. The proposed durable artifact has an owner, placement rationale, source-vs-dist decision, and rejected-location note.
3. The source update has tests, validators, eval fixtures, or review checks appropriate to risk.
4. The memory record excludes raw prompts, secrets, personal data, environment variables, credentials, private archives, and full command output.
5. A maintainer explicitly approves, defers, or rejects promotion.
6. The handoff states rollback path, validation limit, residual risk, and next owner for unpromoted memory.

## Closure Template

```yaml
memory_validation_promotion:
  accepted_signal: ""
  validator_or_review: ""
  current_outcome: "passed|failed|stale|partial|not_run|not_verified"
  owner_response: "none|requested|received|deferred"
  promotion_decision: "none|proposed|approved|rejected"
  what_evidence_proves: []
  what_evidence_does_not_prove: []
  rollback_note: ""
  residual_risk: []
  next_owner: ""
```
