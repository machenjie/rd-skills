# Starter Repo

## Stack

Python 3.11 reference project with a small Kafka consumer boundary and shell based benchmark scripts. The repo is intentionally minimal so benchmark implementations focus on delivery semantics rather than broker setup.

## Initial State

The starter state models a Kafka consumer group that can accumulate lag and block a partition on poison messages. The known gap is that offset commits, retries, DLQ handling, and replay evidence are not safe for at-least-once processing.

## Files

- `README.md` documents the starting behavior and expected implementation boundaries.
- `setup.sh` validates that the starter repo can be prepared from a clean checkout.
- Implementation files may be added under the starter repo as needed by the benchmark.
- Tests may be added under `tests/` or another locally documented test location.

## Constraints

Keep the benchmark deterministic and runnable with local shell commands. Avoid external Kafka, network dependencies, or manual setup steps that would make the generated solution hard to review.
