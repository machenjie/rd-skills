# Expected Route

## Path

Independent Review, because the user explicitly requests review of an existing
migration. The reviewer inspects the actual change and compatibility evidence;
there is no separate Analysis prerequisite and no implementation assignment.
A specific unresolved question may justify deeper Analysis, but missing evidence
must also be reported as a limit of the review.

## Review Assignment

- Profile: `review-agent`
- Primary Professional Skill: `delivery-release-gate`
- Layer 3 Skills: `release-rollback`, `version-compatibility`
- Review boundary: actual migration and application diff, old/new readers and
  writers, rollout order, rollback behavior, and supplied validation

If old application versions still use the removed column, identify the concrete
failure and require compatible sequencing. Do not assume every rename is unsafe:
current source and mixed-version evidence determine the finding. Return required
changes and missing proof; the review-only request does not authorize repair or
production execution.
