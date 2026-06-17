# Expected Route

```yaml
selected_skills:
  - change-forge-router
  - data-api-contract-changer
  - delivery-release-gate
  - reliability-observability-gate
  - quality-test-gate
selected_capabilities:
  - data-migration-design
  - version-compatibility
  - consumer-impact-analysis
  - release-rollback
  - regression-testing
  - agent-execution-discipline
required_quality_gates:
  - API/data gate
  - delivery gate
  - reliability gate
  - test gate
  - execution discipline gate
review_owner: delivery-release-gate
```

The expected decision is to challenge the same-release removal and require expand-contract sequencing unless existing evidence proves mixed-version and rollback safety.
