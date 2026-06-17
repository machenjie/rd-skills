# Expected Route

```yaml
scenario_id: backend-auth-idor
selected_skills:
  - change-intake-compiler
  - change-impact-analyzer
  - backend-change-builder
  - security-privacy-gate
  - quality-test-gate
  - change-documentation-gate
selected_capabilities:
  - implementation-structure-design
  - permission-boundary-modeling
  - authentication-authorization
  - web-security
  - input-validation
  - regression-testing
  - logging-error-handling
required_quality_gates:
  - requirement gate
  - impact gate
  - implementation gate
  - security gate
  - test gate
  - documentation gate
review_owner: quality-test-gate
```

The backend owner handles validation, authorization, transaction, and error model decisions. The security gate owns object-level authorization and denied-path behavior. Documentation review keeps the endpoint behavior and error contract visible to consumers.
