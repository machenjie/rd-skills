# L2 Login API Router Example

## Input
Change the login API so locked accounts return a stable error code and the frontend can show the existing locked-account message. Include tests.

## Routing Result

# ChangeForge Routing Result

## 1. Request Classification
- Change type: API change, backend change, frontend change, test generation
- Complexity: L2 single-module change with API contract touch
- Risk level: medium
- Execution mode: analyze then implement
- Product area: authentication
- Code area: API, backend, frontend, tests
- Domain extension signals: none

## 2. Interpreted Change
- Current behavior: locked account login failures are not represented by a stable client-visible code.
- Desired behavior: locked accounts return a stable error code that maps to the existing frontend message.
- User value: users receive clear recovery guidance and clients can handle the condition reliably.
- Constraints: do not alter credential validation semantics or unlock policy.
- Non-goals: new account recovery flow, new lockout rules, new UI copy.

## 3. Missing Information
- Blocking: current error model and whether clients already depend on the old response.
- Non-blocking: analytics event naming.
- Assumptions: the locked-account state already exists server-side.

## 4. Impact Areas
- Product behavior: clearer locked-account failure behavior
- UX: existing message displayed through stable code mapping
- Domain: authentication state
- API: login error contract
- Data: no model change expected
- Frontend: error mapping
- Backend: login handler/service
- Integration: client compatibility
- Security: authentication behavior must not reveal extra account information
- Testing: API, frontend, regression
- Reliability: none beyond normal error handling
- Delivery: standard release
- Documentation: API error notes

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | change-intake-compiler | Confirm contract and non-goals | request and current behavior | bounded change brief |
| 2 | data-api-contract-changer | Stable error code changes client contract | login error behavior | API error contract |
| 3 | backend-change-builder | Server must emit the code correctly | API contract | backend implementation |
| 4 | frontend-change-builder | Client maps code to existing message | error contract | frontend mapping |
| 5 | security-privacy-gate | Auth error behavior can leak account state | proposed error behavior | security pass/fail |
| 6 | quality-test-gate | Contract and regression tests required | acceptance and code changes | test evidence |
| 7 | change-documentation-gate | API error contract changed | final behavior | docs update |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |
| 01 | requirement-clarification | Confirm compatibility and lockout semantics | change-intake-compiler | blocking questions resolved |
| 26 | api-contract-design | Define login error response | data-api-contract-changer | stable error code contract |
| 28 | error-code-design | Make error actionable and safe | data-api-contract-changer | error catalog entry |
| 41 | authentication-authorization | Keep auth behavior correct | backend-change-builder | auth-safe implementation plan |
| 55 | authentication-security | Prevent account enumeration regression | security-privacy-gate | auth security review |
| 61 | contract-testing | Protect client-visible API behavior | quality-test-gate | API contract test |
| 64 | regression-testing | Preserve locked-account defect behavior | quality-test-gate | regression coverage |
| 80 | documentation-generation | Update API docs | change-documentation-gate | docs patch |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |
| None | Auth is core security, not a separate domain extension trigger | None | None |

## 8. Task DAG
- id: T1
- name: Confirm locked-account contract constraints
- skill: change-intake-compiler
- capabilities: 01
- depends_on: []
- files_or_artifacts: change brief
- acceptance: compatibility and non-goals are explicit
- rollback_note: no code change

- id: T2
- name: Define login error contract
- skill: data-api-contract-changer
- capabilities: 26, 28
- depends_on: [T1]
- files_or_artifacts: API contract/docs
- acceptance: stable locked-account code is specified
- rollback_note: revert contract before implementation if rejected

- id: T3
- name: Implement server and client handling
- skill: backend-change-builder, frontend-change-builder
- capabilities: 41
- depends_on: [T2]
- files_or_artifacts: login handler, client error mapping
- acceptance: locked accounts produce and display the expected result
- rollback_note: revert implementation behind contract change

- id: T4
- name: Verify security, tests, and docs
- skill: security-privacy-gate, quality-test-gate, change-documentation-gate
- capabilities: 55, 61, 64, 80
- depends_on: [T3]
- files_or_artifacts: tests and docs
- acceptance: security review passes and tests cover contract
- rollback_note: revert docs and tests with implementation

## 9. Quality Gates
- requirement gate: change-intake-compiler
- impact gate: skipped, L2 scope is bounded after contract check
- domain gate: skipped
- architecture gate: skipped
- API/data gate: data-api-contract-changer
- implementation gate: backend-change-builder, frontend-change-builder
- security gate: security-privacy-gate
- test gate: quality-test-gate
- reliability gate: skipped
- delivery gate: skipped
- documentation gate: change-documentation-gate
- AI review gate: skipped

## 10. Next Actions
- next skill calls: change-intake-compiler, then data-api-contract-changer
- blocked/unblocked status: blocked on current contract compatibility
- recommended execution mode: clarify then implement

## Selected Professional Skills
- change-intake-compiler
- data-api-contract-changer
- backend-change-builder
- frontend-change-builder
- security-privacy-gate
- quality-test-gate
- change-documentation-gate

## Selected Capabilities
- 01 requirement-clarification
- 26 api-contract-design
- 28 error-code-design
- 41 authentication-authorization
- 55 authentication-security
- 61 contract-testing
- 64 regression-testing
- 80 documentation-generation

## Selected Extensions
- None

## Task DAG
T1 -> T2 -> T3 -> T4

## Quality Gates
Requirement, API/data, implementation, security, test, and documentation gates.
