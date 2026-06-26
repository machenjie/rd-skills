# Scenario Decomposition Benchmarks And Patterns

Use this reference when `scenario-decomposition` needs more detail than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, trigger, evidence, output, and quality gates; use this file for scenario discovery inputs, fault and recovery depth, graph/memory/trajectory coupling, operational readiness, and anti-pattern review.

## Benchmark Anchors

- ISTQB test design: equivalence classes, boundary values, decision tables, and state transitions prevent thin scenario sets.
- BDD and Gherkin: Given/When/Then maps directly to precondition, stimulus, and expected outcome.
- OWASP WSTG: abuse and misuse scenarios must include intentional hostile behavior, not only malformed input.
- Google SRE practice: operational scenarios need alert, diagnosis, rollback, and runbook evidence.
- DORA research: recovery and rollback readiness lowers change failure impact.
- IEEE test design traceability: every scenario should map to requirement and verification evidence.
- Chaos engineering practice: dependency failure, resource exhaustion, clock skew, and network partition are scenario inputs when relevant.
- Architecture smell review: when one scenario set crosses many unrelated modules, escalate ownership and boundary risk.

## Coverage Depth Matrix

| Category | Professional depth check | Required evidence | Typical handoff |
| --- | --- | --- | --- |
| Normal | Primary actor achieves the approved outcome under expected preconditions. | Integration or E2E baseline, requirement trace. | `acceptance-standard-definition` |
| Alternate | A valid actor/path achieves a different allowed outcome. | Role/path variant, branch predicate, test case. | `use-case-modeling`, `user-flow-modeling` |
| Edge | Boundary, empty, max, stale, first/last, zero, or unusual lifecycle state. | Boundary table, unit/integration case. | `quality-test-gate` |
| Failure | Dependency, validation, permission, concurrency, partial write, retry exhaustion, or contract rejection. | Fault row, preserved state, observable error, regression path. | `failure-diagnosis`, `transaction-consistency` |
| Abuse | Intentional misuse such as replay, enumeration, rate probing, hostile input, or privilege probing. | Abuse path, denial behavior, security test or residual risk. | `security-privacy-gate`, `threat-modeling` |
| Recovery | Retry, idempotent resubmission, undo, rollback, compensation, cleanup, or manual correction. | Idempotency/compensation rule, terminal state, validator. | `idempotency-retry-design`, `reliability-observability-gate` |
| Operational | Support diagnosis, monitoring, audit, backfill, incident handling, and release rollback. | Runbook step, alert/log/metric, owner, release criticality. | `reliability-observability-gate`, `delivery-release-gate` |

## Scenario Discovery Inputs

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Requirement or change brief | Current behavior, desired behavior, constraints, and non-goals are explicit. | Blocking unknowns remain unresolved or non-goals conflict with scenarios. |
| Use case | Actor, preconditions, trigger, paths, and postconditions are defined. | Multiple actor goals are merged or failure paths lack durable outcomes. |
| Current source and tests | Code, fixtures, tests, and docs confirm current behavior and regression baseline. | Source evidence is only inferred from names or stale comments. |
| Repository graph | Graph leads to current owners, callers, tests, route/job paths, and data edges that were inspected. | Graph proximity is treated as proof that all scenarios are covered. |
| Project memory | Memory names unchanged behavior and has enough freshness evidence to reuse. | Memory predates route, permission, domain, schema, or integration changes. |
| Execution trajectory | The validation or reproduction ran after the final relevant edit. | Output predates current code or covers only the happy path. |
| Incident/support signal | The signal maps to a reproducible current behavior, tenant, date range, and affected actor. | Signal is anecdotal, outdated, or cannot be tied to the current surface. |
| Observability/runbooks | Alerts, logs, dashboards, and operator steps are current and linked to the scenario. | Operational evidence is aspirational or says only "monitor manually." |

Strong outputs state which graph, memory, and trajectory inputs were accepted, rejected, or left unknown.

## Fault And Recovery Decision Tree

```text
Scenario has an external dependency, queue, webhook, job, import, export, payment, or notification:
  Can the dependency timeout, return an unexpected schema, reject the contract, or partially succeed?
    YES -> add separate failure scenarios with preserved state and observable error.
  Can the same stimulus be delivered or submitted more than once?
    YES -> add recovery scenario with idempotency key/source and duplicate outcome.
  Can a side effect complete before the primary workflow fails?
    YES -> add compensation, rollback, or manual correction scenario.
  Can an operator diagnose or repair the failure without code changes?
    NO -> add operational scenario and hand off to reliability/observability or release gate.

Scenario includes roles, tenants, ownership, support, admin, service account, or external caller:
  Is the path valid for the actor?
    YES -> model as alternate valid path.
    NO  -> model as permission-denied or abuse path with non-leaking outcome.
  Could the actor enumerate, replay, flood, or infer restricted data?
    YES -> add abuse scenario and security handoff.
```

## Review Checklist

- The matrix starts from approved requirement or use-case boundaries and preserves non-goals.
- All seven categories are present or explicitly deferred with owner and release decision.
- Every scenario has actor, precondition, stimulus, expected outcome, verification method, and criticality.
- Failure scenarios cover timeout, unexpected response, validation rejection, permission denial, concurrency conflict, partial write, retry exhaustion, and downstream rejection when applicable.
- Abuse scenarios describe intentional misuse, not just accidental invalid input.
- Recovery scenarios name idempotency, compensation, cleanup, rollback, or manual correction.
- Operational scenarios name diagnosis evidence, alert/log/metric, support action, backfill, and rollback path.
- Repository graph, project memory, and execution trajectory evidence are current-source confirmed or marked not verified.
- Every scenario maps to acceptance or validation evidence, or the gap has an owner and blocking status.
- Handoff boundaries prevent the matrix from silently becoming threat model, implementation design, or test execution proof.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Matrix contains success plus "invalid input" only. | Edge, failure, abuse, recovery, and operations become implementation guesses. | Apply the seven-category matrix with criticality and verification per row. |
| Abuse scenario is only malformed data. | Validation is mistaken for adversarial protection. | Add replay, enumeration, privilege probing, rate probing, or hostile-input scenario when relevant. |
| Recovery says "retry" without duplicate behavior. | Retry can double charge, duplicate records, or re-send notifications. | Name idempotency key/source, duplicate response, and terminal state. |
| Operational scenario says "support investigates." | No evidence, no runbook, and no owner for incident handling. | Define query/log/dashboard, support action, backfill/rollback step, and owner. |
| Project memory is copied as the scenario source. | Stale behavior and outdated permissions are preserved. | Confirm against current source, tests, docs, or registry evidence. |
| Release criticality is omitted. | Planning cannot distinguish blockers from accepted deferrals. | Classify each row as MUST-HANDLE, SHOULD-HANDLE, or DEFERRED with rationale. |
| Scenario handoff points to "engineering." | Downstream owner cannot act on the gap. | Name the precise capability or gate responsible for depth design or validation. |

## Handoff Boundaries

- Use `requirement-clarification` when decomposition exposes blocking scope, authority, data, security, or non-goal conflicts.
- Use `use-case-modeling` when actor-goal contracts, preconditions, or durable postconditions are still unclear.
- Use `acceptance-standard-definition` when scenarios are stable and need falsifiable done standards.
- Use `quality-test-gate` when scenarios need executable test-layer selection and verification evidence.
- Use `security-privacy-gate` or `threat-modeling` when abuse scenarios require adversarial depth.
- Use `idempotency-retry-design`, `transaction-consistency`, or `state-machine-modeling` when recovery scenarios imply duplicate prevention, compensation, or lifecycle legality.
- Use `reliability-observability-gate`, `delivery-release-gate`, or `change-documentation-gate` when operational scenarios imply alerts, runbooks, rollback, or release evidence.
