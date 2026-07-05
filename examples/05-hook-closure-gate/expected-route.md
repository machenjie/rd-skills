# Expected Route

```yaml
scenario_id: completion-evidence-unverified-fix
selected_skills:
  - backend-change-builder
  - quality-test-gate
selected_capabilities:
  - implementation-structure-design
  - regression-testing
  - agent-execution-discipline
required_quality_gates:
  - implementation gate
  - test gate
  - execution discipline gate
review_owner: quality-test-gate
```

The hook is a warning-only guardrail. It does not replace `change-forge-router`; the repair starts by routing the dependency update and collecting missing evidence.
