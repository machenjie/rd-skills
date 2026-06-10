# Review Rubric

## Passing Standard

The solution passes when configuration is typed and validated, flags have lifecycle governance, runtime switches preserve invariants, and rollout plus cleanup are testable.

## Scoring

- 25 percent schema and validation: config types, defaults, secrets boundary, and fail-fast behavior are explicit.
- 25 percent feature flag lifecycle: owner, type, expiry, cleanup, kill switch, rollout, and rollback are present.
- 20 percent switch governance: mode and kind do not become hidden strategy systems.
- 20 percent test matrix: default, invalid, tenant, user, experiment, hot reload, and rollback cases are covered as relevant.
- 10 percent observability and docs: config state and changes are visible without leaking secrets.

## Automatic Failure Conditions

- Feature flag is permanent or unowned.
- Mode or kind switch bypasses domain or security invariants.
- Invalid config silently falls back with no safe degradation contract.
- Stringly typed config creates an implicit strategy system.

## Reviewer Notes

Prefer typed schemas and small explicit strategies. Penalize flags that are added to avoid making a product or domain decision.
