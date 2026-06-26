# Failure Diagnosis Benchmarks And Patterns

Use this reference when a real diagnosis needs detailed benchmark anchors, timeline templates, hypothesis matrices, incident command structure, or postmortem scaffolding. Keep `SKILL.md` focused on routing, proactive triggers, evidence contracts, and closure gates.

## Benchmark Anchors

- **Five Whys Technique**: ask why recursively up to five times to trace from symptom to root cause; document each why/because pair and stop when the answer is specific enough to change prevention.
- **Fault Tree Analysis**: top-down deductive reasoning for combinations of conditions that lead to one top-level failure; useful for complex multi-cause incidents.
- **Fishbone Diagram**: organize contributing factors across Machine, Method, Material, Measurement, Man, and Mother Nature categories during group postmortems.
- **STAMP/STPA**: constraint-based safety analysis for complex systems where inadequate control actions can create emergent failures.
- **Google SRE postmortem practice**: blameless postmortems, draft review windows, concrete action items, and rejection of "human error" as root cause.
- **DORA metrics**: change failure rate and mean time to recovery distinguish process failure from one-off defects.
- **OpenTelemetry**: distributed trace context, span correlation, and vendor-neutral logs/metrics/traces support cross-service diagnosis.
- **Percentile latency analysis**: P50/P95/P99 separation distinguishes systemic degradation from outliers, lock contention, cache misses, or tail-latency defects.
- **SLO burn-rate alerting**: multi-window burn-rate signals identify severity and urgency better than fixed error counts.
- **Structured logging**: JSON logs with trace id, span id, level, timestamp, service, and message make evidence searchable and correlatable.
- **Incident command protocol**: incident commander, technical lead, communications lead, and regular update cadence prevent conflicting parallel work.
- **Action Item Review**: recurring review verifies postmortem actions are completed and effective, not merely assigned.

## Five Whys Documented Chain

```text
Template - complete all fields:

Symptom:          What did users or monitors observe? Include timestamp, scope, and rate.
Trigger:          What event immediately preceded the failure? Deployment, config, data, traffic, or upstream change.

Why #1: [Symptom] occurred because [immediate cause]
  Evidence:       [log line, metric, trace, error message, or reproduction]
Why #2: [Immediate cause] occurred because [deeper cause]
  Evidence:       [specific evidence]
Why #3: [Deeper cause] occurred because [systemic condition]
  Evidence:       [specific evidence]
Why #4: [Systemic condition] exists because [process/design gap]
  Evidence:       [specific evidence]
Why #5: [Process/design gap] exists because [root cause]
  Evidence:       [specific evidence]

Root cause:       [Final why answer, specific enough to guide prevention]
Contributing:     [Conditions that amplified or accelerated impact]
Fix:              [Minimal change that eliminates root cause]
Prevention:       [Specific, verifiable action item with owner and due date]
```

## Timeline Reconstruction Checklist

Collect and correlate:

- Deployment timestamps: git commit, CI/CD run, rollout window, rollback point.
- Configuration changes: feature flags, environment variables, runtime modes, infrastructure as code.
- Infrastructure events: scaling, restarts, node replacement, region/zone events.
- Dependency changes: package lock updates, SDK updates, upstream API version changes.
- Database changes: schema migrations, index creation/drop, backfills, replication lag.
- External service changes: provider status, API shape, timeout/error pattern.
- Alert times: first alert, escalation, acknowledgement, silence, recovery.
- Customer report times: first report, affected cohort, support ticket volume.
- Metric inflection points: error rate, latency, queue lag, saturation, cache miss, pool wait.
- Traffic shifts: load spike, traffic migration, bot activity, tenant-specific surge.

Timeline format:

| Time UTC | Event type | Description | Evidence source |
| --- | --- | --- | --- |
| 14:00:00 | Deploy | v2.3.1 deployed to production | CI/CD run or deploy event |
| 14:03:15 | Alert | DB connection pool above threshold | Alert or metric query |
| 14:05:22 | Metric | Error rate crosses customer-impact threshold | Dashboard or query |
| 14:08:45 | Report | First customer complaint | Support ticket or customer report |

## Hypothesis Validation Matrix

| Hypothesis | Prediction if true | Confirming evidence | Refuting evidence | Status | Next diagnostic command |
| --- | --- | --- | --- | --- | --- |
| DB connection pool exhausted | Pool wait time increases and queries queue before error spike | `db.pool.wait_time` spike | Pool metrics remain below saturation | Confirmed/refuted/open | Inspect pool config and query trace |
| Config change reduced pool size | Runtime config differs from previous deploy | Current config shows lower max pool | Config unchanged from pre-deploy | Confirmed/refuted/open | Compare deploy config artifacts |
| Memory leak caused OOM | Heap/RSS grows monotonically before failure | Memory graph grows before alert | Memory stable until sudden event | Confirmed/refuted/open | Inspect heap profile or container OOM event |
| Upstream service degraded | Upstream latency or error rate increases before app errors | Client span duration spike | Upstream health and client metrics normal | Confirmed/refuted/open | Query upstream spans and status feed |

For agent-assisted failures, add `freshness`, `decision`, and `evidence_limit` columns. Evidence older than the latest code, config, fixture, dependency, generated report, or command-path change is stale unless revalidated or explicitly scoped.

## Incident Response Protocol

Use this protocol for customer-impacting or production-critical incidents before deep root-cause work:

- **Severity classification**: declare SEV0, SEV1, SEV2, or lower severity with customer impact, data impact, financial impact, and duration criteria.
- **Incident commander**: owns coordination, decision log, role assignment, escalation, and cadence.
- **Technical lead**: owns diagnosis, mitigation options, rollback recommendation, and resolution confirmation.
- **Communications lead**: owns internal updates, customer-facing updates, support handoff, and executive summary.
- **Mitigation decision**: distinguish immediate impact reduction from final resolution; record rollback, flag disable, capacity add, traffic shift, or manual workaround.
- **Customer communication cadence**: define update frequency, approved wording owner, affected audience, and support channel.
- **Status page update**: declare when public or private status page entry is required and who updates it.
- **Resolution confirmation**: name the metrics, customer signal, or validation that proves impact has ended.
- **Postmortem publication**: define draft owner, review meeting, publication audience, CAPA tracking, owner, due date, and verification evidence.

## Diagnostic Anti-Pattern Review

- A root cause statement names only the trigger: "the deploy caused it."
- The first hypothesis is treated as proven because some evidence matches it.
- "Human error" is accepted without identifying the system that allowed the error through.
- A mitigation such as restart, rollback, or cache clear is treated as final resolution.
- A local code fix closes without checking sibling code paths or fixtures with the same pattern.
- Validation passes on a new test but never proves the original symptom would have failed before the fix.
- Postmortem actions say "improve monitoring" or "add tests" without owner, date, signal, or verification command.
