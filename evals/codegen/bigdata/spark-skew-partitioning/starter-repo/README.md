# Starter Repo

## Stack

Python 3.11 reference project that models a PySpark job boundary with shell based benchmark scripts. The repo is intentionally minimal so benchmark implementations focus on distributed data behavior rather than Spark cluster setup.

## Initial State

The starter state models an aggregation job affected by skewed shuffle and large partitions. The known gap is that partitioning, compaction, data quality, freshness, and cost controls are not explicitly reviewed.

## Files

- `README.md` documents the starting behavior and expected implementation boundaries.
- `setup.sh` validates that the starter repo can be prepared from a clean checkout.
- Implementation files may be added under the starter repo as needed by the benchmark.
- Tests may be added under `tests/` or another locally documented test location.

## Constraints

Keep the benchmark deterministic and runnable with local shell commands. Avoid external Spark clusters, network dependencies, or manual setup steps that would make the generated solution hard to review.
