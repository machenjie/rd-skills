# Example Output

# ChangeForge Routing Result

## 1. Request Classification
- Change type: bug fix, backend change, test generation
- Complexity: L2 single-module change
- Risk level: medium
- Execution mode: implement
- Product area: account access
- Code area: backend, API, tests
- Domain extension signals: none

## 2. Interpreted Change
- Current behavior: unauthorized users can receive an ambiguous account-resource response.
- Desired behavior: unauthorized access returns the stable forbidden response without leaking resource details.
- User value: users receive predictable errors and protected resources remain private.
- Constraints: keep existing endpoint shape and client compatibility.
- Non-goals: redesign account permissions, add new roles, change authentication.

## 3. Missing Information
- Blocking: current permission rule and expected forbidden error code.
- Non-blocking: audit log wording.
- Assumptions: existing auth identity is available to the handler.

## 4. Impact Areas
- Product behavior: account resource access
- UX: existing error handling
- Domain: account ownership rule
- API: forbidden error behavior
- Data: none
- Frontend: none
- Backend: permission check
- Integration: none
- Security: object-level authorization
- Testing: permission regression
- Reliability: none
- Delivery: standard release
- Documentation: API error note if behavior was previously documented differently

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | change-intake-compiler | Confirm exact permission and error behavior | raw request | bounded change brief |
| 2 | backend-change-builder | Fix the authorization behavior | change brief | backend patch |
| 3 | security-privacy-gate | Object-level permission risk is present | backend plan | security decision |
| 4 | quality-test-gate | Regression evidence is required | fixed behavior | passing permission tests |
| 5 | change-documentation-gate | API error note may need alignment | final behavior | doc decision or update |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |
| 01 | requirement-clarification | Resolve exact forbidden behavior | change-intake-compiler | blocking questions or assumptions |
| 16 | permission-boundary-modeling | Model subject-resource-action ownership | security-privacy-gate, backend-change-builder | permission matrix |
| 41 | authentication-authorization | Keep authn and authz separate | backend-change-builder | authorization plan |
| 54 | web-security | Check broken access control risk | security-privacy-gate | security findings |
| 64 | regression-testing | Prevent recurrence | quality-test-gate | regression test |
| 80 | documentation-generation | Update API notes if needed | change-documentation-gate | documentation outcome |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |
| None | No domain extension signal is present | None | None |

## 8. Task DAG
Each task:
- id: T1
- name: Confirm forbidden response and ownership rule
- skill: change-intake-compiler
- capabilities: 01, 16
- depends_on: []
- files_or_artifacts: change brief
- acceptance: rule and response are explicit
- rollback_note: no code change

- id: T2
- name: Patch backend permission check
- skill: backend-change-builder
- capabilities: 41
- depends_on: [T1]
- files_or_artifacts: handler/service tests
- acceptance: unauthorized access returns forbidden without details
- rollback_note: revert backend patch

- id: T3
- name: Gate security, tests, and docs
- skill: security-privacy-gate, quality-test-gate, change-documentation-gate
- capabilities: 54, 64, 80
- depends_on: [T2]
- files_or_artifacts: security notes, regression tests, doc update
- acceptance: permission review passes and tests cover the defect
- rollback_note: revert documentation with behavior if rolled back

## 9. Quality Gates
- requirement gate: change-intake-compiler
- impact gate: skipped, single-module scope is clear after intake
- domain gate: permission-boundary-modeling via security and backend skills
- architecture gate: skipped
- API/data gate: skipped unless error code changes
- implementation gate: backend-change-builder
- security gate: security-privacy-gate
- test gate: quality-test-gate
- reliability gate: skipped
- delivery gate: skipped
- documentation gate: change-documentation-gate
- AI review gate: skipped

## 10. Next Actions
- next skill calls: change-intake-compiler, then backend-change-builder
- blocked/unblocked status: blocked on expected forbidden response
- recommended execution mode: clarify then implement
