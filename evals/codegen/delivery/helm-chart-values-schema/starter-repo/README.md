# Starter Repo

## Stack

Minimal Helm chart reference project with shell based benchmark scripts. The repo is intentionally small so benchmark implementations focus on chart validation, values safety, and release evidence rather than cluster setup.

## Initial State

The starter state models a service chart with unsafe production values and incomplete release checks. The known gap is that the chart can be promoted without schema validation, rendered manifest validation, or a clear secret sourcing path.

## Files

- `README.md` documents the starting behavior and expected implementation boundaries.
- `setup.sh` validates that the starter repo can be prepared from a clean checkout.
- Implementation files may be added under the starter repo as needed by the benchmark.
- Tests may be added under `tests/` or another locally documented test location.

## Constraints

Keep the benchmark deterministic and runnable with local shell commands. Avoid external clusters, network dependencies, or manual setup steps that would make the generated solution hard to review.
