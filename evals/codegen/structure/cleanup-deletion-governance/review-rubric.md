# Review Rubric

## Passing Standard

The solution passes when deletion is governed by owner, condition, caller search, telemetry, tests, rollback, and cleanup tracking rather than blind removal or permanent retention.

## Scoring

- 25 percent removal governance: target, owner, condition, tracking issue, and residual risk are clear.
- 25 percent reference search: static, runtime, generated, reflection, package, and docs references are considered.
- 20 percent telemetry evidence: old behavior usage is measured before deletion.
- 20 percent test and rollback: tests cover removed and preserved behavior and rollback is possible.
- 10 percent cleanup completeness: flags, docs, config, and compatibility branches are removed together.

## Automatic Failure Conditions

- Feature flag, fallback, compatibility branch, or deprecated API remains permanently with no deletion path.
- Code is deleted without caller search.
- Runtime, generated, or reflection references are ignored.
- Behavior is removed without telemetry or rollback path.

## Reviewer Notes

Reward staged deletion and small cleanup PRs. Penalize additive-only fixes that leave stale branches and flags to accumulate.
