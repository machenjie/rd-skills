# Benchmark Prompt

## Task

Implement a focused change that reviews and improves a PySpark aggregation job affected by skewed shuffle, large partitions, and unclear cost and freshness guardrails.

## Context

The starter repo represents a Databricks-style Spark job that aggregates large data and fails when a few keys dominate shuffle volume. The implementation should make the skew mitigation and promotion evidence clear without needing a real Spark cluster.

## Requirements

- Identify skewed key behavior and mitigate it through an appropriate Spark strategy.
- Justify shuffle partition count, output file size, and compaction behavior.
- Gate promotion on data quality checks.
- Define job duration, freshness, scan volume, and cost metrics.

## Constraints

- Do not use `repartition(1)` for production output.
- Do not use blind `cache()` without reuse evidence.
- Do not replace the benchmark with documentation-only output.
- Avoid any network dependency; scripts must run locally from the starter repo.

## Deliverables

- Source changes in the starter repo that implement the requested Spark job behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
