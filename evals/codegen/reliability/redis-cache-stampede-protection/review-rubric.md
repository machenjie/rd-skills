# Review Rubric

## Passing Standard

The implementation must satisfy the benchmark behavior, prove Redis outage and stampede rejection paths, and keep cache reliability evidence reviewable from executable checks.

## Scoring

- 30 percent correctness for single-flight refresh, TTL jitter, and fallback behavior.
- 25 percent safety for key scope, source-of-truth protection, and outage handling.
- 20 percent test evidence that runs through the benchmark scripts.
- 15 percent maintainability of the cache boundary and metrics.
- 10 percent documentation or operational evidence for future reviewers.

## Automatic Failure Conditions

- TTL-only mutable cache with no invalidation.
- Tenant or permission data missing from cache key.
- No metric for miss storm or hot key.
- Failing request path when Redis is unavailable without documented reason.

## Reviewer Notes

Reward solutions that keep the cache path small while making overload controls explicit. Penalize broad rewrites that remove the cache signal or rely on manual inspection instead of executable checks.
