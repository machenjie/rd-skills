# Expected Route

```yaml
scenario_id: l4-db-migration-api-compat
selected_skills:
  - change-intake-compiler
  - change-impact-analyzer
  - architecture-impact-reviewer
  - data-api-contract-changer
  - data-middleware-change-builder
  - backend-change-builder
  - quality-test-gate
  - delivery-release-gate
  - reliability-observability-gate
  - change-documentation-gate
selected_capabilities:
  - implementation-structure-design
  - data-migration-design
  - relational-database
  - transaction-consistency
  - repository-persistence
  - api-contract-design
  - version-compatibility
  - integration-testing
  - release-rollback
  - observability
required_quality_gates:
  - requirement gate
  - impact gate
  - architecture gate
  - API/data gate
  - implementation gate
  - reliability gate
  - test gate
  - delivery gate
  - documentation gate
review_owner: delivery-release-gate
```

The expected decision is to challenge the same-release removal and require expand-contract sequencing unless existing evidence proves mixed-version and rollback safety.
