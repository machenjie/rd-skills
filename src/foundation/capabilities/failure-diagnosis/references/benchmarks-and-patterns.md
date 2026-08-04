# Failure Diagnosis Benchmarks And Patterns

Load this reference in diagnosis mode when a real symptom needs hypothesis testing, timeline reconstruction, or cause/contributor separation. Do not load it to implement a fix before the failure mechanism is verified or to impose incident ceremony on a non-incident defect.

## Causal Record

| Element | Required distinction |
| --- | --- |
| Symptom and impact | What users/operators observed, affected scope/cohort, start/end or current state, rate, and evidence timestamp. |
| Trigger | The deploy/config/data/traffic/dependency/action immediately preceding the symptom; correlation is not yet cause. |
| Cause | Mechanism necessary or sufficient to produce the symptom, backed by a prediction and confirming/refuting evidence. |
| Contributor | Condition that amplified probability, duration, scope, or recovery cost but did not alone create the failure. |
| Mitigation | Action that reduced current impact, with rollback/side-effect risk and recovery signal. |
| Resolution/prevention | Change that removes or contains the verified mechanism plus a falsifiable action owner and validation. |

Build a timeline from current deploy/config/infrastructure/dependency/schema/provider/alert/customer/metric/traffic evidence only where it can distinguish hypotheses. For every hypothesis state prediction if true, confirming evidence, refuting evidence, status, next discriminating check, freshness, and proof limit. Do not promote the first plausible or temporally correlated explanation.

## Incident And Repair Boundary

Load incident roles, severity/cadence, communications, status, and postmortem actions only for customer-impacting or production-critical events according to the current incident policy. Mitigation and resolution remain separate; restart, rollback, failover, cache clear, or capacity add may restore service without removing cause.

When the major-incident path is triggered, keep ownership distinct. The incident commander coordinates roles and the decision log. The technical lead owns diagnosis, mitigation options, and recovery confirmation. The communications lead owns status updates. Each postmortem or CAPA action names an owner, due date or revisit trigger, and verification evidence.

After verifying cause, scan sibling paths/fixtures only when the same mechanism can recur. A regression case should reproduce the original trigger or a faithful minimal mechanism before the repair when available, then pass after the final edit. If red-before-fix or production conditions are unavailable, disclose the limit.

## Proof Limits And Routes

Time correlation, logs, traces, metrics, local reproduction, and mitigation recovery each prove only their scoped observation. They do not by themselves prove causality, every contributor, production recovery durability, or that the root condition is removed.

Reject deploy-as-root-cause, “human error,” first-hypothesis closure, mitigation reported as final resolution, one-file repair without credible recurrence checks, and vague actions. Route telemetry, rollout, regression evidence, structural recurrence, and durable incident learning to their named specialist owners.
