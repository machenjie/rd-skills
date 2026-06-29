# Review Rubric

## Passing Standard

The solution must make transaction, event, and cache ordering explicit and prove
no downstream side effect occurs if commit fails.

## Scoring

- 35 percent source-of-truth ordering correctness.
- 25 percent failure-path tests.
- 20 percent side-effect flow evidence.
- 10 percent idempotency/rollback preservation.
- 10 percent placement restraint.

## Automatic Failure Conditions

- Publishing events before commit.
- Updating cache from uncommitted state.
- Reporting completion without commit-failure ordering tests.
- Moving ordering logic into a generic helper without owner proof.

## Reviewer Notes

Strong answers state the exact order of database commit, event publication, and
cache mutation, then prove it with tests.

