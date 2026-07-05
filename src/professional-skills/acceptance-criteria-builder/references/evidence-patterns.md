# Acceptance Criteria Evidence Patterns

Use this reference when acceptance closure depends on proving that criteria are mapped to validation evidence, stakeholder sign-off is fresh, manual or audit evidence is bounded, and residual risk is explicit. Keep `SKILL.md` for selection and output rules; load this file only for concrete evidence closure.

## Evidence Map

- **Behavior criterion:** map criterion ID to actor, precondition, action, observable outcome, rejection condition, test level, validator or manual procedure, and owner.
- **Permission or security criterion:** map allowed and denied cases to access matrix row, audit/log expectation, abuse case, and security gate handoff when server-side denial is not verified.
- **Non-functional criterion:** map threshold to environment, percentile or duration, command/dashboard/report, pass/fail bound, and what production scale remains unproven.
- **Experiment criterion:** map primary metric, guardrail, exposure event, assignment unit, SRM check, decision owner, and rollback/rejection threshold.
- **Manual or stakeholder sign-off:** name reviewer, reviewed artifact, date or run path, scope accepted, and criteria not covered by sign-off.

## Validation Map

```yaml
acceptance_criteria_to_validation_map:
  criterion_id: ""
  requirement_source: ""
  validation:
    method: automated_test | contract_test | e2e | manual | audit | owner_review | residual_risk
    command_or_procedure: ""
    expected_pass: ""
    expected_reject: ""
  proves: []
  does_not_prove: []
  residual_risk_owner: ""
```

## Closure Checks

- Do not accept a criterion without a validator, test, manual procedure, audit path, owner review, or explicit residual risk.
- Treat stakeholder acceptance as stale when criteria, scope, non-goals, or validation evidence changed afterward.
- Separate criteria readiness from implementation correctness and release readiness.
- Name any production data, load, compliance, accessibility, security, or analytics evidence that was not inspected.
