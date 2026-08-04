# Message Queue Design Evidence Patterns

Use this reference when queue-design closure depends on validation freshness, duplicate/poison/replay evidence, prior claims, tool boundaries, or proof limits. Include only claims triggered by current semantics; omit untriggered claims or record accepted checks as `planned`/`not_run` with reason. Keep it as an evidence map, not a broker benchmark table.

## Queue-To-Validation Map

| Queue claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Producer durability is controlled | When publish atomicity changes: producer path, commit boundary, selected coupling mechanism, owner, and focused partial-failure proof | Inspected producer has an intentional publish durability model | All downstream consumers or broker outages are safe |
| Consumer duplicate behavior is controlled | When repeated effects are possible: effect identity/scope, selected idempotency or reconciliation, retention boundary, and focused duplicate proof | Inspected consumer handles the named duplicate window intentionally | External providers or replays beyond the inspected boundary are safe |
| Ack or offset commit is safe | When acknowledgement can race the effect: durable boundary, ack/delete/commit location, and relevant crash, batch, or rebalance proof | Inspected consumer avoids the named lost-work ordering failure | All rebalances or partial batch failures are proven |
| Failure policy terminates intentionally | Triggered failure classes, retry or no-retry choice, retry limits only when selected, terminal disposition, owner, and focused proof | Inspected failures reach the selected terminal outcome without silent looping or loss | Broker outage, saturation, or every poison payload is safe |
| Ordering scope is explicit | When stateful order matters: broker guarantee, key/group scope, hot-key risk, out-of-order behavior, and focused proof or residual | Inspected flow names the required ordering boundary | All workloads avoid skew or races |
| Lag and backpressure are observable | When lag/overload risk is triggered: relevant age/depth/terminal metrics, owned threshold/action, and existing dashboard or review evidence | Inspected queue risk has a detection and response path | Production alert routing or future traffic surges are handled |
| Replay is safe or blocked | When replay is supported or requested: replay class, side-effect safety, throttle/approval, owner, and focused test or runbook evidence | Inspected replay behavior is intentional for the named class | Disaster-scale replay or unknown consumers are safe |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, topology docs, runbooks, dashboards, and prior incidents as selectors until current producer/consumer code, broker config, schemas, tests, and execution results confirm them.
- Accept prior "consumer handles duplicates", "terminal routing exists", "lag alert works", or "broker config is safe" claims only when current source/config and validation still match.
- Mark evidence stale after edits to producer paths, consumer handlers, topic/queue config, schemas, retry/terminal settings, partition keys, dashboards, runbooks, tests, reports, or generated topology docs.
- Map each triggered claim and accepted check to current evidence. For checks not run, record `planned` or `not_run`, reason, owner, and residual risk instead of inventing command or artifact evidence.

## Tool Permission Boundary

- Live publish, scaling, broker configuration, replay, and redrive require an authorized topic or queue scope, stop condition, pause or rollback path, and payload redaction. Replay and redrive also require a bounded window and allowed message class.
- For live or simulated replay of a queue class supported or requested by the current design, record visibility or lease behavior, dedupe-window coverage, and ordering impact. The record also identifies downstream side effects not isolated by replay.

## Handoff Evidence Shape

```yaml
message_queue_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_queue_to_validation_map:
    - behavior_or_artifact: ""
      validator_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | planned | not_run
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox_and_state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner_and_next_gate: ""
```
