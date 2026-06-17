# Expected Route

```yaml
scenario_id: implementation-structure-shared-utils-pollution
selected_skills:
  - architecture-impact-reviewer
  - backend-change-builder
  - quality-test-gate
selected_capabilities:
  - implementation-structure-design
  - module-boundary-design
  - business-rule-extraction
  - unit-testing
required_quality_gates:
  - architecture gate
  - implementation gate
  - test gate
review_owner: architecture-impact-reviewer
```

The route must force a placement decision: reuse an existing domain/order module if present, avoid shared utility dumping, and scan all same-pattern calculation copies before changing one path.
