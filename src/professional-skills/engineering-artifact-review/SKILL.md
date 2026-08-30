---
name: engineering-artifact-review
description: "Use `review-agent` for an ordinary Engineering Brief, Task Plan, acceptance, or contract artifact. Exclude high-risk design and release-readiness approval."
---

# Engineering Artifact Review

## Role

Support `review-agent` in assessing a concrete engineering artifact's
decisions, dependencies, failure boundaries, and evidence.

## When To Use

- ordinary Engineering Brief Task Plan acceptance or contract artifact needs independent review
- pre-implementation decision affects downstream tasks

## Do Not Use

- actual implementation diff review
- bounded implementation task with no separate decision artifact
- high-risk Engineering Brief specialist review
- release deployment or migration readiness approval

## Required Inputs

- observable acceptance and non-goals
- actual artifact and source evidence it cites
- decision, ownership, dependency, validation, and rollback boundaries

## Professional Decision Rules

- Verify every material claim against current source or explicit owner evidence.
- Check owner, invariants, reuse, public contracts, data, failure
  behavior, dependencies, validation, and rollback proportional to risk.
- Separate reviewed, unreviewed, and unverified scope.
- Report findings with severity, affected decision, downstream impact, and required action.

## High-Value Gotchas

- A complete template can still encode the wrong owner.
- A Task Plan without a safe first slice can prolong preparation indefinitely.
- Rollback prose is not an executable rollback path.

## Execution Checklist

1. Confirm the artifact, acceptance, owner, and review boundary.
2. Verify cited source and rejected alternatives.
3. Check downstream dependencies, collision risks, integration, and validation.
4. Check failure behavior, compatibility, rollback, and user-owned decisions.

## Stop / Escalation Conditions

- Stop when the artifact or its material source evidence is unavailable.
- High-risk Engineering Brief specialist verdicts are outside this Skill's authority; record that scope as unreviewed.
- Release, deployment, and migration readiness approval are outside this Skill's authority; do not issue a go/no-go verdict here.
- Escalate destructive, production, privileged, irreversible, security, privacy,
  money, or public-contract choices without authoritative decisions.

## Output Contract

- verdict and severity-ranked findings
- reviewed, unreviewed, and unverified scope
- owner, dependency, first-slice, validation, and rollback assessment
- downstream impact and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [review](references/review-checklist.md) | decision-checklist | ordinary pre-implementation artifact decisions have downstream impact | the task is implementation diff review, a bounded implementation task with no separate decision artifact, high-risk design, or release/deployment/migration readiness | review-agent | checklist-result, residual-risk |
