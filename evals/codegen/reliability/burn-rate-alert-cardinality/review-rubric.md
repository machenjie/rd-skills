# Review Rubric

## Passing Standard

The implementation must satisfy the benchmark behavior, prove the negative path, and keep the relevant ChangeForge quality gates reviewable from executable evidence.

## Scoring

- 30 percent correctness for the primary behavior and required edge cases.
- 25 percent safety for denial, rollback, compatibility, or permission boundaries.
- 20 percent test evidence that runs through the benchmark scripts.
- 15 percent maintainability of the boundary touched by the change.
- 10 percent documentation or operational evidence for future reviewers.

## Automatic Failure Conditions

- Using user id or raw URL path as alert labels.
- Paging on a single short window without sustained burn evidence.
- Alerting on request volume alone instead of error budget burn.
- Shipping alerts without dashboard or runbook links.

## Reviewer Notes

Reward solutions that keep the change narrowly scoped while making the important risk visible in tests. Penalize broad rewrites that remove the benchmark signal or rely on manual reviewer inspection instead of executable evidence.
