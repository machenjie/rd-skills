# Async Job Evidence Patterns

Use this reference when async job closure depends on repository graph, project memory, execution trajectory, validation freshness, tool permission boundaries, or production-scale evidence limits. Keep it focused on evidence and handoff shape, not as a second async job tutorial.

## Evidence Freshness Rules

- Treat repository graph, project memory, runbooks, dashboards, old incidents, generated reports, and prior validation as selectors until current source confirms the job topology.
- Mark evidence stale after edits to enqueue call sites, payload schema, idempotency store, worker code, scheduler or broker config, status model, retry policy, DLQ handling, runbook, dashboard, fixtures, generated reports, or validator commands.
- Accept a prior "job is safe" claim only when the current enqueue path, worker handler, status store, idempotency key, observability signal, and validation command still match.
- Re-run affected checks after final material edits or state the not-run limit, owner, and residual risk.

## Async Claim-To-Evidence Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Durable enqueue is atomic | Source state path, enqueue/outbox/CDC/recovery owner, rollback case, command, exit code, artifact/report path | The inspected path avoids committed state with missing work under the tested case | Every broker outage, crash timing, or production transaction anomaly is covered |
| Duplicate delivery is safe | Idempotency key, payload hash/conflict rule, duplicate fixture, command, exit code | The inspected logical job produces one durable effect for duplicate delivery | All downstream providers or manual replay paths are idempotent |
| Retry policy is bounded | Failure classes, backoff/jitter, max attempts, max wall-clock, terminal state, test/report | Retry exhaustion reaches an owned state for named failures | Production retry storm, quota exhaustion, or dependency-specific behavior is fully modeled |
| DLQ and replay are recoverable | DLQ fields, alert owner, retention, runbook, replay throttle, replay validation | Operators can triage and replay the inspected failure class safely | Full production backlog drain or every tenant/resource skew case is safe |
| Cancellation and compensation are safe | Safe points, committed side effects, compensator order, cancellation fixture, report path | The inspected cancellation path avoids new side effects or compensates committed ones | Arbitrary external side-effect timing or human interruption is covered |
| Deploy skew is compatible | Payload version, worker compatibility, workflow version/drain plan, replay test or not-run disclosure | In-flight work survives the inspected deploy/version path | All old payloads, long-running workflows, or rollback windows are proven |
| Observability is actionable | Metric/log/trace names, bounded labels, dashboard/runbook owner, alert threshold, artifact | The inspected job exposes the named diagnostic signal | The live alert will page correctly under every production incident |

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, report inspection, and Markdown validation | Read-only local shell action; cite paths and avoid full output dumps |
| Local validators, unit fixtures, benchmark/profile commands, and builds | State-mutating only for reports, caches, temp files, dist/build artifacts, or benchmark outputs; cite command, exit code, artifact path, sandbox, and cleanup |
| Queue/broker/database integration tests | Test-data action; record dataset, local or sandbox environment, cleanup, credential boundary, timeout, and redaction rule |
| Production telemetry, broker dashboard, DLQ replay, or live benchmark | High-risk data-reading or state-mutating action; require owner, bounded scope, timestamp, rollback/revert path, redaction, and retention limit |

## Handoff Evidence Shape

```yaml
async_job_evidence_closure:
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
  job_to_validation_map:
    - concern: ""
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
  residual_async_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
