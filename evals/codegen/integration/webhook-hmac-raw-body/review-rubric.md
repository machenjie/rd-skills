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

- Verifying HMAC over JSON reserialization instead of raw body bytes.
- Accepting unsigned callbacks when configuration is missing.
- Running business handlers before signature verification succeeds.
- Logging webhook secrets or full signatures.

## Reviewer Notes

Reward solutions that keep the change narrowly scoped while making the important risk visible in tests. Penalize broad rewrites that remove the benchmark signal or rely on manual reviewer inspection instead of executable evidence.
