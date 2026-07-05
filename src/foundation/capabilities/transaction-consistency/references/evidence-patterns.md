# Transaction Consistency Evidence Patterns

Use this reference when transaction-consistency closure depends on repository graph, project memory, execution trajectory, validation freshness, same-pattern write-path scans, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second transaction design tutorial.

# Consistency Claim-To-Evidence Map

| Consistency claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Local invariant is protected atomically | Current handler/service/repository path, named invariant, tables or rows touched, transaction boundary, rollback case, and invariant test | The inspected write path protects the named invariant inside the declared local boundary | Alternate entry points, future migrations, or replica-read behavior are covered |
| Lost update is prevented | Version check, conditional update, row lock, serializable retry, or constraint plus concurrent writer fixture | The inspected concurrent writers cannot silently overwrite each other | Every datastore default, lock timeout, or production contention profile is proven |
| Write skew or phantom is prevented | Set/range invariant source, isolation choice or constraint, current query shape, and concurrent range/set fixture | The inspected set invariant survives representative concurrent transactions | All predicate-lock behavior, ORM-generated SQL variants, or query-plan drift is covered |
| Remote side effect is outside lock | Transaction timeline, source path for provider/event/cache/search/file call, commit boundary, and rollback or timeout fixture | The inspected side effect does not run while the declared DB lock is open | The external provider, broker, cache, or search index is available or exactly-once |
| Outbox/inbox path is durable | Source row and outbox row in one transaction, relay monitor, consumer idempotency key, duplicate replay case, and stuck-relay alert | The inspected local commit cannot publish without durable state or lose a committed publish intent | Broker delivery order, consumer availability, or every downstream side effect is proven |
| Saga can compensate | Persisted step log, compensation parameters written before each forward step, failure-at-each-step fixture, retry policy, and manual runbook owner | The inspected saga has enough durable information to compensate representative failures | Compensation will always succeed or external systems can be restored automatically |
| Reconciliation closes eventual drift | Drift query, freshness SLA, owner, remediation command, idempotent repair proof, and alert path | The inspected eventual-consistency gap is observable and has a repair route | Drift will be detected instantly or all production data distributions are covered |
| Memory or graph claim is current | Prior claim source, current source reread, same-pattern write-path scan, final command/report path, and freshness verdict | The accepted memory or graph still matches the inspected transaction topology | Future edits, undiscovered entry points, or production lock behavior are covered |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old incident notes, generated reports, previous reviews, and prior validation as selectors until current source and fresh validators confirm them.
- Accept a prior "transaction boundary is safe", "event publishes after commit", "consumer is idempotent", "reconciliation exists", or "deadlock was tested" claim only when current handlers, repositories, migrations, queue consumers, side-effect adapters, tests, and reports still match.
- Mark evidence stale after edits to transaction scopes, lock order, isolation level, repository methods, ORM callbacks, migrations, retry wrappers, event topics, outbox relays, consumers, compensation workers, fixtures, reports, build outputs, or validation commands.
- Record inspected and skipped boundaries: HTTP/API handlers, services, repositories, migrations, ORM hooks, queue producers, outbox/inbox relays, consumers, cache/search/file/payment/email adapters, reconciliation jobs, tests, logs, metrics, and runbooks.
- Map every final confidence claim to a current command, source path, fixture, report artifact, owner review, or explicit not-verified residual consistency risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, same-pattern write-path scan, report inspection, and markdown validation | Read-only local shell action; cite paths and searched patterns, avoid full output dumps |
| Local validators, tests, builds, synthetic concurrent fixtures, and generated reports | State-mutating only for reports, caches, temp files, dist/build artifacts, or local fixtures; cite command, exit code, artifact path, sandbox, and cleanup |
| Database, queue, cache, or provider sandbox proof command | Potentially state-mutating test action; record dataset, endpoint, credentials boundary, timeout, cleanup, rollback or reset path, and redaction rule |
| Production lock, event, reconciliation, or telemetry inspection | High-risk data-reading action; require owner, bounded query, timestamp, dataset, no-secret disclosure, and residual privacy/security limits |

# Handoff Evidence Shape

```yaml
transaction_consistency_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_artifact: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  invariant_to_evidence_map:
    - invariant: ""
      source_path_or_artifact: ""
      command_or_gate: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_consistency_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
