# Starter Repo

## Stack

Python 3.11 reference project with a small service boundary, domain logic module, and shell based benchmark scripts. The repo is intentionally minimal so benchmark implementations focus on behavior rather than framework setup.

## Initial State

The starter state models a backend endpoint fetches metadata from user supplied URLs for preview generation. The known gap is that the starter behavior trusts parsed hostnames and does not reject private network targets, so a passing solution must add the missing production rule and evidence.

## Files

- `README.md` documents the starting behavior and expected implementation boundaries.
- `app.py` exposes `fetch_preview(url, http_get, resolver, logger=None)` with
  injectable HTTP and resolver boundaries for deterministic benchmark tests.
- `setup.sh` validates that the starter repo can be prepared from a clean checkout.
- Implementation files may be added under the starter repo as needed by the benchmark.
- Tests may be added under `tests/` or another locally documented test location.

## Constraints

Keep the benchmark deterministic and runnable with local shell commands. Avoid external network dependencies, hidden services, or manual setup steps that would make the generated solution hard to review.
