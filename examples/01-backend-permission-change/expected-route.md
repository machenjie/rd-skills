# Expected Route

```yaml
scenario_id: backend-auth-idor
selected_skills:
  - change-forge-router
  - change-intake-compiler
  - backend-change-builder
  - data-api-contract-changer
  - security-privacy-gate
  - quality-test-gate
selected_capabilities:
  - permission-boundary-modeling
  - api-contract-design
  - version-compatibility
  - regression-testing
  - agent-execution-discipline
required_quality_gates:
  - requirement gate
  - API/data gate
  - security gate
  - test gate
  - execution discipline gate
review_owner: quality-test-gate
```

The backend owner handles validation, authorization, transaction, and error model decisions. The data/API owner checks response compatibility. The security gate owns object-level authorization and denied-path behavior.
