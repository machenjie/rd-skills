# Review Rubric

## Passing Standard

The implementation must satisfy the benchmark behavior, prove the secret and rollback rejection paths, and keep Helm release evidence reviewable from executable checks.

## Scoring

- 30 percent correctness for chart schema, rendering, and upgrade behavior.
- 25 percent safety for secret sourcing, rendered manifest review, and rollback boundaries.
- 20 percent test evidence that runs through the benchmark scripts.
- 15 percent maintainability of chart templates and values overlays.
- 10 percent documentation or operational evidence for future reviewers.

## Automatic Failure Conditions

- Keeping API tokens in values-prod.yaml.
- Skipping helm template validation.
- Using helm upgrade without atomic, wait, and timeout semantics.
- Treating Helm rollback as full system rollback.

## Reviewer Notes

Reward solutions that keep the chart deterministic while making rendered manifest evidence visible. Penalize broad rewrites that hide the Helm release signal or rely on manual inspection instead of executable checks.
