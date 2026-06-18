---
name: failure-diagnosis
description: Diagnoses failures from evidence by separating symptom, trigger, root cause, contributing factors, fix, and regression prevention.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "81"
changeforge_version: 0.1.0
---

# Mission

Diagnose failures from **observable evidence** so that fixes target verified root causes, not plausible-sounding guesses — and so prevention measures are specific enough to measurably reduce recurrence probability rather than providing comfort with no operational change.

# When To Use

Use this capability when diagnosing: production incidents (P0–P3), failing automated tests (unit, integration, E2E), CI/CD pipeline failures, performance regressions (latency, throughput, error rate), integration failures with third-party services, data anomalies (unexpected records, missing data, calculation errors), memory leaks, deadlocks or contention, and security-related anomalies (unexpected traffic, auth failures, data access patterns).

Use it for agent-assisted diagnosis whenever an agent blames environment, flakiness, user setup, or background processes without inspecting evidence.

# Do Not Use When

Do not use this capability for preventive architecture reviews (use `architecture-impact-reviewer`), performance capacity planning (use `performance-budgeting` and `reliability-observability-gate`), or dependency risk assessment before upgrade (use `dependency-vulnerability-scanning`). Do not diagnose the same failure twice without first confirming the first diagnosis was correct — re-diagnosis without new evidence compounds confusion.

# Stage Fit

Owns debugging-diagnosis; also supports release-delivery and incident triage. Per-stage focus:

- **debugging-diagnosis**: evidence first; symptom/root-cause/contributing-factor split; eliminated hypotheses; verified cause.
- **bug-fix**: hand off a verified cause so the fix targets the root, not a symptom.
- **release-delivery**: triage regressions and incidents against rollout and rollback signals.

# Non-Negotiable Rules

- **Evidence first; hypothesis second.** Never start with a hypothesis and look for evidence to support it. Start with evidence (logs, metrics, traces, error messages, timeline of events) and derive hypotheses that are consistent with all evidence. Confirmation bias is the leading cause of wrong diagnosis.
- **Separate symptom, trigger, root cause, contributing factors.** These are different things: *symptom* (what the user or monitor observed: "500 errors increasing"); *trigger* (the immediate event: "config change deployed at 14:03"); *root cause* (the condition that made the trigger cause failure: "max DB connection pool set to 5 after config change"); *contributing factors* (conditions that amplified impact: "connection pool exhaustion at 40% load, not 100%"). A fix that addresses only the trigger will recur.
- **Hypotheses must be falsifiable.** Every hypothesis must have: a specific prediction ("if this hypothesis is correct, metric X should show pattern Y"), a test or evidence that would confirm it, and a test or evidence that would refute it. A hypothesis that cannot be refuted by any evidence is not a hypothesis — it's a guess.
- **The smallest fix that addresses root cause.** Resist the impulse to refactor, rearchitect, or broadly "improve" the system during incident response. The fix must be the minimal correct change that eliminates the root cause or its pathway. Improvements belong in follow-up work after the blameless post-mortem.
- **Reproduction is required for diagnosis completion.** A failure is not considered diagnosed until it can be reproduced in a controlled environment OR a specific, documented evidence chain explains precisely why it occurred and why controlled reproduction is not feasible (e.g., race condition that requires specific production traffic pattern). "We think we know what it was" is not sufficient.
- **Hypothesis elimination table required.** Diagnosis must list confirmed, refuted, and still-open hypotheses with prediction, confirming evidence, refuting evidence, status, freshness, and next diagnostic command. Single-hypothesis diagnosis is not enough for non-trivial failures.
- **Minimum reproduction before fix.** Before code mutation, define the smallest failing input, fixture, command, request, timeline, or evidence chain that reproduces the symptom or proves why controlled reproduction is infeasible.
- **Environment blame is rejected without evidence.** "Environment", "flaky", "cache", "network", or "user setup" can be accepted only after repository, configuration, dependency, data, command, and runtime-path evidence has been checked.
- **Failed-fix history is part of diagnosis.** Record attempted fixes, command/output, shared failure signature, what was learned, and why the next route is different after two failed attempts.
- **Change-failure correlation is mandatory first step.** For every production failure, the first investigative step is: what changed in the last 24–48 hours? Deployments, configuration changes, infrastructure changes, dependency upgrades, database migrations, upstream service changes. DORA change failure rate: > 15% change failure rate is a signal the change process needs review.
- **Post-mortem action items must be specific and verifiable.** Action items in post-mortems must have: owner, due date, specific outcome (not "improve monitoring" but "add alert for DB connection pool utilization > 80% with 2-minute sustained threshold"), and a verification test. Vague action items are not action items.
- **Incident command roles must be explicit during customer-impacting incidents.** A SEV0/SEV1/SEV2 incident without an incident commander, technical lead, communications lead, mitigation owner, and customer communication cadence will drift into parallel, conflicting work.
- **Agent diagnosis must carry execution discipline.** A diagnosis produced by an agent must identify inspected evidence, tested hypotheses, verified cause, counter-evidence, and validation result before it can drive a fix.

# Industry Benchmarks

Anchor against: **Five Whys Technique** (Toyota Production System, Ohno, 1978) — ask "why" recursively up to 5 times to trace from symptom to root cause; limit to 5 iterations to prevent over-analysis; document each Why/Because pair. **Fault Tree Analysis (FTA)** — top-down deductive reasoning; models how combinations of conditions (AND/OR gates) lead to a top-level failure event; suited for complex multi-cause failures; IEC 61025 standard. **Fishbone Diagram (Ishikawa, 1968)** — 6M categories: Machine, Method, Material, Measurement, Man, Mother Nature; visual organization of contributing factors; useful for brainstorming in group post-mortems. **STAMP/STPA** (Systems-Theoretic Accident Model and Processes; Leveson, MIT) — constraint-based safety analysis; models inadequate control actions; suited for safety-critical and complex emergent failures. **Google SRE Book** (Beyer et al., O'Reilly) — Ch. 15 Postmortem Culture: blameless post-mortem; 5-day draft review window; action items with owners and due dates; avoid "human error" as root cause. **DORA Metrics** (Forsgren et al., Accelerate) — change failure rate and mean time to recovery (MTTR) as key signals; high-performing teams: MTTR < 1 hour, change failure rate < 5%. **OpenTelemetry** (CNCF) — distributed trace context: `traceparent` W3C header; `traceId` (128-bit), `spanId` (64-bit); Jaeger, Zipkin, Honeycomb, Grafana Tempo for trace visualization. **P50/P95/P99 Latency Analysis** — percentile histograms distinguish outlier failures from systemic degradation; P99 spike with flat P50 = outlier; P50 degrading = systemic. **SLO Burn Rate Alerts** (Google SRE Workbook, Ch. 5) — multi-window burn rate: fast burn (2% budget in 1h = page), slow burn (10% budget in 6h = ticket); burn rate as leading severity indicator. **Structured Logging** — JSON-formatted logs with `traceId`, `spanId`, `level`, `timestamp`, `service`, `message`; correlation by `traceId` across services; avoid string concatenation logs. **Paging War Room Protocol** — incident commander role; separate investigation and communication tracks; status updates every 15 minutes during active P0. **AIR (Action Item Review)** — monthly review of post-mortem action items; verify completion and effectiveness; close items with test evidence.

### Five Whys Documented Chain

```
Template — complete all fields:

Symptom:          What did users or monitors observe? (specific, with timestamps)
Trigger:          What event immediately preceded the failure? (deployment, config, upstream change)

Why #1: [Symptom] occurred because [immediate cause]
  Evidence:       [log line, metric, trace, or error message]
Why #2: [Immediate cause] occurred because [deeper cause]
  Evidence:       [specific evidence]
Why #3: [Deeper cause] occurred because [systemic condition]
  Evidence:       [specific evidence]
Why #4: [Systemic condition] exists because [process/design gap]
  Evidence:       [specific evidence]
Why #5 (if applicable): [Process/design gap] exists because [root cause]
  Evidence:       [specific evidence]

Root cause:       [Final Why answer — specific enough to guide prevention]
Contributing:     [Conditions that amplified or accelerated impact]
Fix:              [Minimal change that eliminates root cause]
Prevention:       [Specific, verifiable action item with owner and due date]
```

### Timeline Reconstruction Checklist

```
Collect and correlate:
  □ Deployment timestamps (git commit, CI/CD pipeline completion)
  □ Configuration changes (feature flags, env vars, infrastructure as code)
  □ Infrastructure changes (scaling events, restarts, node replacements)
  □ Dependency upgrades (lock file changes, package updates)
  □ Database migrations (schema changes, index operations)
  □ Upstream/downstream service changes (API version, response shape)
  □ Alert firing times (first alert, escalation times)
  □ Customer report times (first report, volume increase)
  □ Metric inflection points (when did error rate / latency / lag start changing?)
  □ Traffic pattern changes (increased load, traffic shift, bot activity)

Timeline format:
  HH:MM:SS UTC | Event type | Description | Source (log/metric/deploy)
  14:00:00 UTC | Deploy     | v2.3.1 deployed to prod | GitHub Actions run #1234
  14:03:15 UTC | Alert      | DB connection pool > 90% | PagerDuty alert #5678
  14:05:22 UTC | Metric     | Error rate crosses 5%   | Datadog dashboard
  14:08:45 UTC | Report     | First customer complaint | Zendesk ticket #9012
```

### Hypothesis Validation Matrix

| Hypothesis | Prediction (if true) | Confirming evidence | Refuting evidence | Status |
| --- | --- | --- | --- | --- |
| DB connection pool exhausted | DB pool wait time > 0; queries queued | `db.pool.wait_time` spike at 14:03 | Pool metrics show < 50% utilization | ✅ CONFIRMED |
| Config change reduced pool size | Pool `max_connections` = 5 in config | `app.config.db.pool.max` = 5 post-deploy | Config unchanged from pre-deploy | (fill in) |
| Memory leak causing OOM | Heap/RSS growing monotonically pre-failure | Memory graph trending up 2h before alert | Memory stable; sudden spike at event | (fill in) |
| Upstream service degraded | Upstream latency increase precedes errors | `http.client.duration` upstream spike | Upstream health check green | (fill in) |

For agent-assisted failures, extend this into an elimination table with `next_diagnostic_command`, `freshness`, and `decision` columns. Evidence older than the latest code, config, fixture, dependency, or command-path change is stale unless re-validated or explicitly scoped.

## Incident Response Protocol

Use this protocol for customer-impacting or production-critical incidents before deep root-cause work:

- **Severity classification**: declare SEV0, SEV1, SEV2, or lower severity with customer impact, data impact, financial impact, and duration criteria.
- **Incident commander**: owns coordination, decision log, role assignment, escalation, and cadence.
- **Technical lead**: owns diagnosis, mitigation options, rollback recommendation, and resolution confirmation.
- **Communications lead**: owns internal updates, customer-facing updates, support handoff, and executive summary.
- **Mitigation decision**: distinguish immediate impact reduction from final resolution; record rollback, disable flag, capacity add, traffic shift, or manual workaround decisions.
- **Customer communication cadence**: define update frequency, approved wording owner, affected audience, and support channel.
- **Status page update**: declare when public or private status page entry is required and who updates it.
- **Resolution confirmation**: name the metrics, customer signal, or validation that proves impact has ended.
- **Postmortem publication**: define draft owner, review meeting, publication audience, CAPA tracking, and due dates.

# Selection Rules

Select this capability as a diagnostic framework that cuts across all technical domains. Pair with domain-specific capabilities when diagnosis reveals the root cause domain:

- Pair with `reliability-observability-gate` for production SLO/burn rate signal analysis.
- Pair with `concurrency-control` when diagnosis points to race conditions, deadlocks, or lost update anomalies.
- Pair with `cache-design` when diagnosis points to stale data, cache miss, or cache invalidation failure.
- Pair with `event-driven-architecture` when diagnosis points to consumer lag, DLQ accumulation, or poison messages.
- Pair with `ci-cd` when diagnosis is of a CI/CD pipeline failure or flaky test.

# Risk Escalation Rules

Escalate diagnosis to senior engineers or incident commander when: the failure has a financial, regulatory, customer-facing, security, or safety impact; root cause is not identified within the first hour of a P0/P1 or SEV0/SEV1 incident; the timeline reconstruction reveals a data integrity anomaly (records missing or corrupted); multiple independent hypotheses are confirmed with conflicting evidence; the failure mode is novel and not covered by existing runbooks; legal, compliance, security, or privacy escalation may be required; a post-mortem action item owner is not available.

Escalate to `agent-execution-discipline` when an agent repeats the same diagnostic route twice, skips counter-evidence, or attempts to close a diagnosis without evidence inventory and closure package.

Escalate to `repository-context-map` when the diagnosis lacks owning surface, caller/callee flow, related tests, configs/docs, and same-pattern scope. Escalate to `plan-execution-consistency` when attempted fixes or validation evidence drift from the accepted diagnostic plan.

# Critical Details

Most incorrect diagnoses come from stopping at the trigger rather than the root cause, or from generating a hypothesis before gathering evidence. Precision failures:

- **Stopping at the trigger.** "The deploy caused the outage" is a trigger, not a root cause. The deploy would not have caused an outage if the pool configuration had been validated pre-deploy, and the pool would not have been misconfigured if the configuration change review process included a mandatory diff check. Fix the review process, not just the config.
- **P50/P95/P99 confusion.** P50 is flat (median response time = 150ms); P99 is spiking (slow requests = 8s). This is a small fraction of requests hitting extreme latency — outlier behavior (e.g., GC pause, lock contention on specific key, cold cache on specific shard). Treating as systemic will not fix the outlier. Investigate P99 specifically.
- **"Human error" as root cause.** An engineer misconfigured a parameter. Root cause = human error. Action item: "be more careful." This is not useful. Human error is a symptom of a system that allowed the error to reach production. The real root causes: no validation of the config value type, no pre-deploy canary phase, no automated test that would have failed with this configuration.
- **Correlation ≠ causation.** CPU utilization increased during the incident. A new background job also started at the same time. The assumption: background job caused CPU spike. Evidence: background job CPU usage = 2%. The real cause: a different query started doing a full table scan due to a dropped index. Always quantify correlation strength before accepting causal hypothesis.
- **Unverifiable reproduction.** "We fixed it; it hasn't happened again; that proves the fix was right." This is not reproduction or verification. If the fix cannot be verified by a test that would fail before and pass after, the confidence in the fix is uncertain.
- **Same-pattern taxonomy.** A failure pattern must be classified before a local fix closes: input validation, permission, mapping, state transition, concurrency, cache, queue, retry/idempotency, dependency lifecycle, configuration, migration, generated artifact, or test harness. Scan the matching taxonomy scope before declaring the defect local-only.
- **Next diagnostic command.** Every open hypothesis names the next command, file read, fixture, log query, metric query, trace lookup, or reproduction step that would confirm or refute it.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Hypothesis before evidence | Cherry-picks logs that confirm theory; misses real root cause |
| "Human error" as root cause | Action item: "be careful"; recurrence rate unchanged |
| Stops at trigger (deploy broke it) | Root cause (missing validation) left unfixed; next deploy breaks it again |
| Fixes symptom only (restart the service) | Service restarts every 4 hours; root cause (memory leak) unaddressed |
| Post-mortem action: "improve observability" | No specific metric, alert, or threshold; never implemented; marked done |
| Diagnosis complete without reproduction | Fix uncertain; problem recurs 3 weeks later |
| Only P50 checked in performance incident | P99 degradation missed; 1% of users experiencing 10s latency |
| Single hypothesis tested | Alternative root cause (upstream degradation) not considered; wrong fix shipped |

# Failure Modes

- Wrong root cause identified due to confirmation bias; fix deployed; incident recurs in 2 weeks; second incident takes 4 hours longer because team believes original fix was correct.
- "Human error" as root cause; engineer blamed; no process change; same misconfiguration occurs next quarter with different engineer.
- Timeline not reconstructed; triggering config change not identified; team diagnoses "mysterious intermittent issue" for 5 days; config rollback in 5 minutes would have resolved it immediately.
- P50 monitored only; P99 degradation affects 5,000 users for 3 hours; discovered when customer complaint volume escalates.
- Post-mortem action items vague ("improve monitoring"); no owner; no due date; marked done after 3 weeks without implementation; same failure recurs.
- Production-only race condition; team unable to reproduce; declares "unable to reproduce, probably fixed"; next race condition triggers data corruption.
- Stopped at trigger (deploy); root cause (query without index) left in place; next non-related deploy triggers same pattern; second outage on different date.
- Evidence gathered only after hypothesis formed; confirming logs extracted; disconfirming signals ignored; post-mortem report contains technically accurate but logically incomplete diagnosis.

# Reference Loading Policy

Read `references/checklist.md` when the diagnosis is production-impacting, repeated after a failed hypothesis, customer/security/data relevant, or being used to justify a code change. Do not load it for a single local test failure when the evidence chain, reproduction, and regression test are already obvious.

# Output Contract

Return a failure diagnosis report with:

- `incident_id` (date + service + brief description)
- `severity` (SEV0/SEV1/SEV2/lower; classification rationale and declared time)
- `incident_roles` (incident commander, technical lead, communications lead, support/legal/security/compliance escalations if needed)
- `symptom` (observable failure: user impact, monitor alert, error type, rate, duration)
- `trigger` (immediate precipitating event with timestamp)
- `timeline` (chronological list: timestamp, event type, description, source)
- `customer_comms` (customer-facing update cadence, status page entry, support handoff, and last update)
- `hypotheses` (list, each with: statement, prediction, confirming evidence, refuting evidence, status)
- `hypothesis_elimination_table` (confirmed/refuted/open hypotheses, prediction, confirming/refuting evidence, freshness, next diagnostic command, decision)
- `minimum_reproduction` (smallest input, fixture, command, request, timeline, or reason controlled reproduction is infeasible)
- `failed_fix_history` (attempts, commands/output, shared failure signature, learned facts, route change)
- `same_pattern_taxonomy` (pattern class, scope scanned, related occurrences, local/broad decision)
- `root_cause` (specific, verifiable statement; the Why chain)
- `contributing_factors` (conditions that amplified impact)
- `fix` (minimal code/config/infra change; PR link or description)
- `mitigation_vs_resolution` (impact-reducing actions taken now vs. final defect removal)
- `reproduction` (test case or reproduction steps; or documented reason reproduction is infeasible)
- `prevention` (action items each with: owner, due date, specific observable outcome, verification test)
- `postmortem_actions` (review meeting, publication audience, CAPA tracking item, owner, due date, verification evidence)
- `process_gaps` (what in the development, review, deployment, or monitoring process allowed this root cause to exist)
- `open_questions` (unresolved aspects; owner; investigation timeline)
- `false_hypotheses` (hypotheses considered and rejected; reason rejected)
- `execution_discipline` (commands or artifacts inspected, route repair after repeated failure, validation result, residual risk, and handoff boundary)

# Evidence Contract

Close diagnosis only when the output states the evidence boundary: observed symptom, timeline, hypotheses tested, counter-evidence, verified cause, minimal fix target, behavior preservation expectation, validation command, what that validation proves, what it does not prove, residual recurrence risk, and next gate. A diagnosis without counter-evidence or without a not-reproducible rationale is not strong enough to drive a fix.

# Quality Gate

The diagnosis is complete only when:

1. Evidence timeline reconstructed with timestamps from logs, metrics, traces, and change history.
2. ≥ 1 confirmed hypothesis with specific confirming and refuting evidence analysis.
3. Root cause stated at the level of a specific condition, not a trigger or action.
4. Trigger, root cause, and contributing factors explicitly separated.
5. Symptom → Root cause chain documented (Five Whys or equivalent).
6. Fix is minimal and directly targets root cause; not a broad refactor.
7. Reproduction test defined; or formal explanation why production-only.
8. All post-mortem action items have owner, due date, and verifiable outcome.
9. Process gaps identified — why was root cause able to reach production?
10. False hypotheses documented with rejection evidence.
11. Minimum reproduction or formal not-reproducible evidence chain is present before the fix is accepted.
12. Environment, flake, cache, network, or user-setup blame has specific evidence ruling out code, config, dependency, data, command, and runtime-path causes.
13. Failed-fix history records attempted fixes, failure signatures, learned facts, and route changes after repeated attempts.
14. Same-pattern taxonomy and scope scan are documented for local fixes.
15. Open hypotheses name the next diagnostic command or evidence lookup.
16. Customer-impacting incidents include severity, incident roles, mitigation decision, customer communication cadence, and status page decision.
17. CAPA/postmortem actions are tracked with owner, due date, and verification evidence.
18. Agent-assisted diagnosis includes evidence inventory, counter-evidence, no third same-path retry, and closure package.

# Used By

- reliability-observability-gate
- ai-code-review-refactor

# Handoff

Hand off the post-mortem action items to the owning teams; prevention measures to `ci-cd` (for pipeline guards), `reliability-observability-gate` (for alerting), and `code-review` (for code-level prevention). Hand incident report, customer advisory, status page entry, postmortem summary, and corrective action tracking to `change-documentation-gate`. Hand rollback, mitigation, and release sequencing gaps to `delivery-release-gate`. Hand legal, compliance, or security escalation to `security-privacy-gate`. Hand open questions to `architecture-impact-reviewer` when the root cause reveals a systemic architectural weakness.

Hand off to `agent-execution-discipline` when the diagnosis lacks evidence, route repair, validation result, residual risk, or handoff boundary.

# Completion Criteria

The capability is complete when **the root cause is specific and verifiable, the timeline is reconstructed from evidence, incident severity and roles are explicit when customer impact exists, the fix directly targets root cause with minimal scope, reproduction is confirmed or formally justified, customer communication is accounted for, and every prevention/postmortem action item is concrete, owned, time-bound, and verifiable** — with no "human error" as root cause, no post-mortem actions without owners, and no fix accepted as correct without reproduction or equivalent evidence chain.
