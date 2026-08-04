# Transaction Consistency Evidence Patterns

Use this reference when transaction closure depends on current source, prior claims, validation freshness, same-pattern scans, tool boundaries, or production limits. Include only claims and anomaly/failure paths triggered by the named invariant; mark accepted unexecuted checks `planned`/`not_run` with reason. Keep it as an evidence map.

## Consistency Claim-To-Evidence Map

| Consistency claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Local invariant is protected atomically | Current handler/service/repository path, named invariant, tables or rows touched, transaction boundary, rollback case, and invariant test | The inspected write path protects the named invariant inside the declared local boundary | Alternate entry points, future migrations, or replica-read behavior are covered |
| Lost update is prevented | When writers can collide: selected conflict mechanism plus current source and focused concurrent-writer proof | The inspected concurrent writers cannot silently overwrite each other | Every datastore default, lock timeout, or production contention profile is proven |
| Write skew or phantom is prevented | When a set/range invariant exists: invariant source, actual datastore/query behavior, selected control, and focused concurrent proof | The inspected set invariant survives representative concurrent transactions | All predicate-lock behavior, ORM SQL variants, or query-plan drift is covered |
| Remote side-effect ordering is justified | Transaction timeline, invariant, external protocol, lock/latency evidence, failure window, and held-lock or post-commit recovery proof | The inspected ordering has an explicit atomicity and recovery rationale | Provider availability, exactly-once effects, or production contention is proven |
| Outbox/inbox path is durable | Source row and outbox row in one transaction, relay monitor, consumer idempotency key, duplicate replay case, and stuck-relay alert | The inspected local commit cannot publish without durable state or lose a committed publish intent | Broker delivery order, consumer availability, or every downstream side effect is proven |
| Saga can compensate | Persisted step log, compensation parameters written before each forward step, failure-at-each-step fixture, retry policy, and manual runbook owner | The inspected saga has enough durable information to compensate representative failures | Compensation will always succeed or external systems can be restored automatically |
| Reconciliation closes eventual drift | Drift query, freshness SLA, owner, remediation command, idempotent repair proof, and alert path | The inspected eventual-consistency gap is observable and has a repair route | Drift will be detected instantly or all production data distributions are covered |
| Prior task or source evidence claim is current | Prior claim source, current source reread, same-pattern write-path scan, final command/report path, and freshness verdict | The accepted prior task or source evidence still matches the inspected transaction topology | Future edits, undiscovered entry points, or production lock behavior are covered |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old incident notes, generated reports, previous reviews, and prior validation as selectors until current source and role-permitted evidence confirm them.
- Accept a prior consistency claim only while current handlers, repositories, migrations, queue consumers, side-effect adapters, tests, and reports still match. Examples include "transaction boundary is safe", "event publishes after commit", "consumer is idempotent", "reconciliation exists", and "deadlock was tested".
- Mark evidence stale after edits to transaction scopes, lock order, isolation level, repository methods, ORM callbacks, migrations, retry wrappers, event topics, outbox relays, consumers, or compensation workers. The same rule covers fixtures, reports, build outputs, and validation commands.
- Record inspected and skipped boundaries: HTTP/API handlers, services, repositories, migrations, ORM hooks, queue producers, outbox/inbox relays, consumers, cache/search/file/payment/email adapters, reconciliation jobs, tests, logs, metrics, and runbooks.
- Map each triggered claim to current source or existing artifacts and, when a permitted check ran, its fresh result. Otherwise record `planned`/`not_run`, reason, owner, and residual consistency risk.

## Tool Permission Boundary

- Database, queue, cache, provider, and production consistency probes require an authorized transaction or message scope, timeout, stop condition, rollback or reset path, and sensitive-value redaction.
- For an authorized consistency probe used to support an ordering claim, retain the observed commit/ack/side-effect sequence and identify crash windows, retry boundaries, and external effects outside the probe's rollback boundary.

## Handoff Evidence Shape

```yaml
transaction_consistency_evidence:
  profile: analysis-agent | task-agent
  inspected_boundaries:
    - boundary: ""
      evidence_and_freshness: ""
  prior_claims:
    - claim: ""
      verdict_and_evidence: ""
  invariant_to_validation:
    - invariant: ""
      status: planned | ran | not_run
      evidence_or_reason: ""
      proves_and_limits: ""
  mutation:
    action_or_none: ""
    authority_cleanup_redaction: ""
  residual_risk:
    - risk: ""
      owner_or_gate: ""
```
