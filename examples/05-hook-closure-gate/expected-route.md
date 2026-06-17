# Expected Route

```yaml
scenario_id: completion-evidence-unverified-fix
selected_skills:
  - change-forge-router
  - quality-test-gate
  - security-privacy-gate
  - ai-code-review-refactor
selected_capabilities:
  - package-dependency-management
  - regression-testing
  - code-review
  - agent-execution-discipline
required_quality_gates:
  - security gate
  - test gate
  - execution discipline gate
review_owner: quality-test-gate
```

The hook is a warning-only guardrail. It does not replace `change-forge-router`; the repair starts by routing the dependency update and collecting missing evidence.
