# Expected Route

## Path

Task implementation and targeted validation, followed by the requested independent
security Review of caller-controlled invoice access. A security boundary alone
does not require a separate Analysis stage: the Task first inspects the current
policy and consumers. If authorization semantics remain unresolved, request
Analysis of that specific question before the dependent edit.

## Task Assignment

- Profile: `task-agent`
- Primary Professional Skill: `backend-change-builder`
- Layer 3 Skills: none
- Allowed scope: the invoice endpoint owner and its adjacent tests
- Verify: targeted allowed-admin, denied-non-admin, and denied-cross-organization
  backend tests, plus API response compatibility

## Independent Review

- Profile: `review-agent`
- Review Skill: `security-privacy-gate`
- Layer 3 Skills: `permission-boundary-modeling`, `threat-modeling`
- Reason: the user requests independent judgment of whether invoice identifiers
  can bypass tenant ownership enforcement
- Boundary: actual diff, every changed file, tenant ownership enforcement,
  response compatibility, and denied-path coverage

An ordinary defect within the established authorization rule returns to the
original Task for repair, self-check, and fresh targeted validation, then done.
Re-review is needed only for an unresolved required judgment or a new material
question introduced by the repair.
