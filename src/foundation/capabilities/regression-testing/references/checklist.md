# Regression Testing Checklist

- Link the test to a bug, incident, review finding, or escaped defect.
- Reproduce the original failure or a minimized equivalent.
- Confirm the test would fail before the fix when feasible.
- Choose the narrowest test level that would catch recurrence.
- Include triggering input, state, role, timing, dependency, or data condition.
- Document technical impossibility, residual risk, and compensating evidence when automation cannot be added.

## Level Selection

| Defect shape | Default level | Evidence focus |
| --- | --- | --- |
| Single deterministic function or rule | Unit | exact input/output or error that was wrong |
| Data state, ORM, query, cache, or migration | Integration | real boundary or faithful fake that exposes the original failure |
| Service-to-service interaction | Integration or component | provider response, retry, timeout, or contract condition |
| Auth, permission, tenant, or injection bug | Integration plus security review | abuse/denied path, no data leak, same-pattern scan |
| Browser rendering or JS event | E2E | user-visible trigger and durable side effect |
| Race, timing, or hardware condition | deterministic replay, chaos, or monitoring | reproducibility feasibility and residual risk |

## Regression Test Anatomy

Use this structure in the target test framework:

1. Defect comment: `Regression: BUG-1234 - concise defect summary - fixed in PR #567`.
2. Arrange: exact triggering input, state, role, feature flag, provider response, or timing sequence.
3. Act: call the narrowest public behavior boundary that would have exposed the defect.
4. Assert: post-fix behavior plus the pre-fix wrong result when helpful.
5. Evidence: command and branch/commit state showing red before fix and green after fix.

## Untestable Defect Record

When automation is genuinely infeasible, record:

```yaml
defect_id: "BUG-5678"
failure_trigger: "specific input/state/timing/dependency condition"
regression_test_feasibility: "infeasible"
reason: "why deterministic automated reproduction is not reliable"
rejected_options:
  - "replay/fake/stub/contract/chaos option considered and rejected"
residual_risk:
  likelihood: "low|medium|high"
  impact: "low|medium|high|critical"
compensating_controls:
  - "monitoring alert, manual regression step, chaos experiment, or runbook check"
owner: "team or role"
expiry_or_revisit_trigger: "date, incident threshold, or platform capability"
```
