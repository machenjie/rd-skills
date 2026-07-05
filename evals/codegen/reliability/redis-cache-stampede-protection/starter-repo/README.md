# Starter Repo

## Stack

Python 3.11 reference project with a small cache boundary and shell based benchmark scripts. The repo is intentionally minimal so benchmark implementations focus on Redis behavior rather than framework setup.

## Initial State

The starter state models a read path with Redis product-detail caching. The known gap is that hot key expiration can trigger a cache miss storm and Redis outage behavior is not explicitly degraded or observable.

## Files

- `README.md` documents the starting behavior and expected implementation boundaries.
- `setup.sh` validates that the starter repo can be prepared from a clean checkout.
- Implementation files may be added under the starter repo as needed by the benchmark.
- Tests may be added under `tests/` or another locally documented test location.

## Constraints

Keep the benchmark deterministic and runnable with local shell commands. Avoid external Redis, network dependencies, or manual setup steps that would make the generated solution hard to review.
