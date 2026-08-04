# State Machine Modeling Evidence Patterns

Use this reference when state-machine closure depends on lifecycle graph freshness, transition-to-validation mapping, migration or rollback proof, side-effect commit evidence, stale prior evidence, or proof limits. Keep it as an evidence map, not another transition-design guide.

## Lifecycle Surface-To-Validation Map

| Lifecycle claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| State set is authoritative | Domain object path, persisted representation, state owner, terminal/failure states, and writer scan | Inspected lifecycle has one declared source of truth | Future writers or uninspected support tools cannot bypass it |
| Transition legality is enforced | Transition table, enforcement method, illegal-transition fixtures, and denied reason behavior | Named valid and invalid transitions are covered in inspected paths | All concurrent or migrated records are safe |
| Guard rules are current | Guard owner, source facts, actor authority, positive and negative tests or review artifact | Inspected guards match current source and rule owner | Full business-rule extraction or policy approval is complete |
| Side effects bind to committed state | Transaction/outbox/event boundary, idempotency key, duplicate handling, and failure test or review | Inspected side effects do not obviously run before durable transition | Downstream delivery, provider behavior, or all retries are proven |
| Migration/versioning is safe | Stored record counts or mapping, old/new state interpretation, rollback behavior, validation query | Changed state values have a declared compatibility path | Production distribution, every report, or all consumers are covered |
| Prior lifecycle evidence is fresh | Current paths, accepted/rejected prior task evidence and repository inspection delta, validator/report, and final-edit freshness | Reused transition model still matches inspected source | Later state, actor, event, or data edits remain covered |

## Evidence Quality Labels

- **Strong evidence**: current domain/writer/event/migration/test paths inspected, command or review artifact named, exit code or status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: diagram only, enum diff only, prior task evidence, happy-path transition test, or local search without writer/consumer coverage.
- **Missing evidence**: no transition table, no illegal-transition proof, no timeout/recovery proof, no side-effect commit boundary, no migration mapping, or no owner for unverified writers.
- **Invalid evidence**: side effect before commit, terminal state can mutate through ordinary path, stale lifecycle memory accepted as fact, or stored state renamed without rollback interpretation.

## Tool Permission Boundary

- Production repair transitions, data patches, replays, requeues, provider calls, and migrations require an authorized state scope, dry-run or staging proof, terminal stop condition, and rollback or compensation path.
- When an authorized repair mutates lifecycle state, preserve its source and target state, actor or policy authority, applicable replay or idempotency stance, and transitions the inspected repair path cannot reverse.

## Handoff Evidence Shape

```yaml
state_machine_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  lifecycle_surface_to_validation_map:
    - surface: ""
      risk: states | transition | guard | side_effect | migration | freshness
      validator_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
