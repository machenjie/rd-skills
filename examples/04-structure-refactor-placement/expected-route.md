# Expected Route

## Path

Analyzed Work, because ownership and the complete same-pattern impact are not
known from the request.

## Analysis Assignment

- Profile: `analysis-agent`
- Primary Professional Skill: `architecture-impact-reviewer`
- Layer 3 Skills: `module-boundary-design`, `architecture-tradeoff-analysis`
- First Executable Slice: add characterization coverage for the three known
  calculation paths before extraction.

## Implementation Assignment

- Profile: `task-agent`
- Primary Professional Skill: `backend-change-builder`
- Constraint: prefer the owning order/domain module; do not create a generic
  shared utility without evidence that the calculation is domain-free
- Verify: targeted characterization and regression tests for every found path

## Independent Review

- Profile: `review-agent`
- Review Skill: `architecture-impact-reviewer`
- Boundary: actual diff, owner placement, dependency direction, same-pattern
  coverage, and rejected locations
