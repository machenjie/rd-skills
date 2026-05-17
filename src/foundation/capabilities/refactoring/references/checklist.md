# Refactoring Checklist

- State the structural problem and target improvement.
- Define observable behavior that must not change.
- Identify public contracts, schema, config, metrics, and integration boundaries.
- Add characterization tests for risky or poorly understood behavior.
- Split movement into small reviewable steps.
- Avoid mixing formatting churn with logic movement.
- Verify behavior after risky steps.
- Record rollback notes and any explicit behavior-change exclusions.
