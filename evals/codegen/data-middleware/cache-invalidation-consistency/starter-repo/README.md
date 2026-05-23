# Starter Repo

## Stack

Python 3.11 reference project with a small service boundary, domain logic module, and shell based benchmark scripts. The repo is intentionally minimal so benchmark implementations focus on behavior rather than framework setup.

## Initial State

The starter state models a service stores account settings in SQL and caches read models for low latency reads. The known gap is that the starter behavior updates the database but leaves stale cache entries until TTL expiry, so a passing solution must add the missing production rule and evidence.

## Files

- `README.md` documents the starting behavior and expected implementation boundaries.
- `setup.sh` validates that the starter repo can be prepared from a clean checkout.
- Implementation files may be added under the starter repo as needed by the benchmark.
- Tests may be added under `tests/` or another locally documented test location.

## Constraints

Keep the benchmark deterministic and runnable with local shell commands. Avoid external network dependencies, hidden services, or manual setup steps that would make the generated solution hard to review.
