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
- **bug-fix**: handoff a verified cause so the fix targets the root, not a symptom.
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

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Local test or CI failure | Failing unit, integration, E2E, benchmark, linter, build, or pipeline step. | Smallest reproduction, command-path freshness, fixture/input diff, dependency and config changes. | Failing command, exit code, stack trace, current source, fixture/input, and first passing/failing boundary. | `quality-test-gate`, `repository-context-map`, `validation-broker` | Incident roles and customer comms unless user impact exists. |
| Production incident | Alert, customer report, SLO burn, rollback signal, data anomaly, or release regression. | Severity, timeline, change correlation, mitigation vs resolution, verified root cause. | Logs/metrics/traces, deploy/config/data timeline, affected users, rollback/mitigation signal, incident roles. | `reliability-observability-gate`, `delivery-release-gate`, `security-privacy-gate` when sensitive | Deep refactor before impact mitigation. |
| Repeated agent or repair failure | Same command, patch shape, diagnosis, or hypothesis failed twice. | Route repair, counter-evidence, learned facts, new diagnostic path, no third same-path retry. | Attempt ledger, shared failure signature, inspected output, changed route, next command or owner. | `agent-execution-discipline`, `execution-trajectory-analysis`, `project-memory-governance` | Retrying unchanged command or patch. |
| Data, security, or permission anomaly | Missing/corrupt records, auth failure, unexpected access, tenant leak, or privacy incident. | Trust boundary, same-pattern scan, blast radius, regulatory/security escalation, regression proof. | Sample records/events, authorization or data-flow path, denied cases, scope scan, fix validation and residual risk. | `security-privacy-gate`, `data-api-contract-changer`, `regression-testing` | Local-only closure without same-pattern scan. |

# Proactive Professional Triggers

- **Signal:** Diagnosis asserts root cause before the symptom is reproduced or tied to a current evidence chain. **Hidden risk:** plausible explanation drives the fix while a stale log, old memory note, or unrelated metric hides the real cause. **Required professional action:** require a symptom -> trigger -> root-cause evidence chain with counter-evidence before continuing the fix path. **Route to:** `failure-diagnosis`, `repository-context-map`, `validation-broker`. **Evidence required:** current failing command or incident signal, inspected files/logs/metrics, confirmed/refuted hypotheses, and not-reproducible rationale if applicable.
- **Signal:** The same command, hypothesis, patch shape, or incident query has failed twice. **Hidden risk:** a third same-path retry creates stale or wrong diagnostic state and may overwrite the useful failure signature. **Required professional action:** record route repair and choose a different diagnostic route before continuing. **Route to:** `agent-execution-discipline`, `execution-trajectory-analysis`, `project-memory-governance`. **Evidence required:** attempt ledger, shared signature, output inspected, new route, and next diagnostic command or owner.
- **Signal:** A local fix is proposed before scanning sibling call sites, tests, configs, routes, generated artifacts, or registry edges for the same failure pattern. **Hidden risk:** the visible occurrence is fixed while the same defect remains in another boundary. **Required professional action:** classify the same-pattern taxonomy and decide all-instance, subset, or local-only treatment. **Route to:** `repository-graph-analysis`, `change-impact-analyzer`, `regression-testing`. **Evidence required:** pattern signature, search scope, hits found, coverage decision, and regression command.
- **Signal:** Project memory, repository graph, generated report, or prior validation is used as proof after source, config, fixture, dependency, or command path changed. **Hidden risk:** stale context becomes current evidence and closes the wrong diagnosis. **Required professional action:** compare prior context against current source and post-edit validation, then document accepted and rejected claims before using it as proof. **Route to:** `project-memory-governance`, `repository-context-map`, `validation-broker`. **Evidence required:** freshness comparison, current-source read, accepted/rejected memory or graph claims, and validation freshness result.
- **Signal:** Handoff says fixed, verified, green, or ready without command, exit code, artifact/report path, and what the evidence proves or does not prove. **Hidden risk:** partial validation is inflated into unverified closure and the next owner may inherit wrong confidence. **Required professional action:** document an evidence inventory or mark the diagnosis partial/not verified. **Route to:** `validation-broker`, `quality-test-gate`, `plan-execution-consistency`. **Evidence required:** command, working directory, exit code or validator outcome, covered paths, uncovered paths, residual risk, and next gate.

# Industry Benchmarks

Anchor against evidence-first root cause methods (Five Whys, Fault Tree Analysis, Fishbone, STAMP/STPA), incident discipline from Google SRE and DORA, and observability evidence from OpenTelemetry, percentile latency analysis, SLO burn alerts, and structured logs. Keep `SKILL.md` focused on routing, triggers, evidence, and handoff; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed diagnostic templates, timeline reconstruction, hypothesis matrices, and incident response protocol.

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

- **Wrong root cause:** confirmation bias selects the first plausible cause; fix deployed; incident recurs in 2 weeks; second incident takes 4 hours longer because team believes original fix was correct.
- **Human-error closure:** engineer blamed; no process change; same misconfiguration occurs next quarter with different engineer.
- **Missing timeline:** triggering config change not identified; team diagnoses "mysterious intermittent issue" for 5 days; config rollback in 5 minutes would have resolved it immediately.
- **Wrong percentile:** P50 monitored only; P99 degradation affects 5,000 users for 3 hours; discovered when customer complaint volume escalates.
- **Vague prevention:** post-mortem action says "improve monitoring"; no owner; no due date; marked done after 3 weeks without implementation; same failure recurs.
- **Unproven production-only race:** team unable to reproduce; declares "unable to reproduce, probably fixed"; next race condition triggers data corruption.
- **Trigger-only diagnosis:** deploy blamed while root cause (query without index) remains; next non-related deploy triggers same pattern; second outage on different date.
- **Evidence cherry-picking:** hypothesis formed first; confirming logs extracted; disconfirming signals ignored; post-mortem report contains technically accurate but logically incomplete diagnosis.

# Reference Loading Policy

The `SKILL.md` body carries normal routing, trigger, evidence, and closure rules. Read [references/checklist.md](references/checklist.md) when the diagnosis is production-impacting, repeated after a failed hypothesis, customer/security/data relevant, or being used to justify a code change. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when a formal Five Whys chain, timeline, hypothesis matrix, incident command protocol, or postmortem structure is needed. Load [references/evidence-freshness.md](references/evidence-freshness.md) when repository graph, project memory, generated reports, prior command output, validation freshness, or execution trajectory is being used to support or close a diagnosis after code, config, fixture, dependency, or command-path changes. Use [examples/example-output.md](examples/example-output.md) only when the expected report shape is unclear. Do not load references for a single local test failure when the evidence chain, reproduction, and regression test are already obvious.

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
