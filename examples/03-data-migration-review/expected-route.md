# Expected Route

## Path

Analyzed Work, because the proposed same-release removal affects
stored data, mixed-version compatibility, rollback, and unknown consumers.

## Analysis Assignment

- Profile: `analysis-agent`
- Primary Professional Skill: `delivery-release-gate`
- Layer 3 Skills: `release-rollback`, `version-compatibility`
- Required output: compatibility and rollback boundaries for the actual
  migration, plus the review scope; no implementation task is implied.

## Review Assignment

- Profile: `review-agent`
- Primary Professional Skill: `delivery-release-gate`
- Layer 3 Skills: `ci-cd`
- Review boundary: actual migration and application diff, old/new readers and
  writers, rollout order, rollback behavior, reconciliation, and validation

The expected finding is to require expand-contract sequencing unless current
source and executable mixed-version evidence prove same-release removal safe.
