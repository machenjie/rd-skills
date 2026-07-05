# Review Rubric

## Passing Standard

The implementation must satisfy the benchmark behavior, prove skew and cost rejection paths, and keep Spark reliability evidence reviewable from executable checks.

## Scoring

- 30 percent correctness for skew mitigation, partitioning, and compaction behavior.
- 25 percent safety for cost, freshness, and data quality promotion gates.
- 20 percent test evidence that runs through the benchmark scripts.
- 15 percent maintainability of the job boundary and tuning notes.
- 10 percent documentation or operational evidence for future reviewers.

## Automatic Failure Conditions

- repartition(1) for production output.
- Blind cache() without reuse evidence.
- Full table scan with no partition filter or cost approval.
- No data freshness or job duration metric.

## Reviewer Notes

Reward solutions that make the Spark tuning decision evidence-backed and reversible. Penalize broad rewrites that remove the data job signal or rely on manual inspection instead of executable checks.
