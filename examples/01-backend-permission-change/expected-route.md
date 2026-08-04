# Expected Route

## Path

Analyzed Work, because tenant authorization and invoice access cross a security
boundary.

## Analysis Assignment

- Profile: `analysis-agent`
- Primary Professional Skill: `security-privacy-gate`
- Layer 3 Skills: `permission-boundary-modeling`, `threat-modeling`
- First Executable Slice: add an observable denied-cross-organization regression
  case at the existing invoice endpoint owner.

## Implementation Assignment

- Profile: `task-agent`
- Primary Professional Skill: `backend-change-builder`
- Allowed scope: the invoice endpoint owner and its adjacent tests
- Verify: the targeted allowed/denied backend tests

## Independent Review

- Profile: `review-agent`
- Review Skill: `security-privacy-gate`
- Boundary: actual diff, every changed file, tenant ownership enforcement,
  response compatibility, and denied-path coverage
