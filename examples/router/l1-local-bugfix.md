# L1 Local Bugfix Router Example

## Input
Fix a local date formatting bug in the order summary component. The API returns the right timestamp, but the UI renders one day early for UTC dates. Add a regression test.

## Routing Result

# ChangeForge Routing Result

## 1. Request Classification
- Change type: bug fix, frontend change, test generation
- Complexity: L1 isolated local change
- Risk level: low
- Execution mode: implement
- Product area: order summary
- Code area: frontend, tests
- Domain extension signals: none

## 2. Interpreted Change
- Current behavior: UTC timestamps can render as the previous local date.
- Desired behavior: order dates render consistently for UTC timestamps.
- User value: users see the correct order date.
- Constraints: keep API contract unchanged.
- Non-goals: redesign order summary, change backend date storage, alter timezone policy.

## 3. Missing Information
- Blocking: target component and existing date helper location if not discoverable.
- Non-blocking: supported locale list.
- Assumptions: existing formatter can be fixed without changing external contracts.

## 4. Impact Areas
- Product behavior: order date display only
- UX: minor visible correction
- Domain: none
- API: none
- Data: none
- Frontend: date formatting helper and component
- Backend: none
- Integration: none
- Security: none
- Testing: regression test required
- Reliability: none
- Delivery: standard change
- Documentation: skipped, behavior is unchanged except defect correction

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | frontend-change-builder | Local frontend bug surface | bug description and affected UI | corrected component/helper |
| 2 | quality-test-gate | Regression evidence required | UTC date case | passing targeted regression test |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |
| 36 | frontend-testing | Verify visible date behavior | frontend-change-builder, quality-test-gate | focused frontend regression case |
| 64 | regression-testing | Preserve historical defect coverage | quality-test-gate | failing-before, passing-after test |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |
| None | No domain-specific trigger | None | None |

## 8. Task DAG
- id: T1
- name: Reproduce UTC date defect
- skill: frontend-change-builder
- capabilities: 36, 64
- depends_on: []
- files_or_artifacts: order summary component/test
- acceptance: UTC date displays expected calendar date
- rollback_note: revert formatter/component patch

- id: T2
- name: Add regression test and fix formatter
- skill: quality-test-gate
- capabilities: 36, 64
- depends_on: [T1]
- files_or_artifacts: frontend test file and date helper
- acceptance: regression test fails before fix and passes after fix
- rollback_note: revert test and implementation together

## 9. Quality Gates
- requirement gate: skipped, request is clear
- impact gate: skipped, isolated local change
- domain gate: skipped
- architecture gate: skipped
- API/data gate: skipped
- implementation gate: frontend-change-builder
- security gate: skipped
- test gate: quality-test-gate
- reliability gate: skipped
- delivery gate: skipped
- documentation gate: skipped
- AI review gate: skipped

## 10. Next Actions
- next skill calls: frontend-change-builder, quality-test-gate
- blocked/unblocked status: unblocked
- recommended execution mode: implement

## Selected Professional Skills
- frontend-change-builder
- quality-test-gate

## Selected Capabilities
- 36 frontend-testing
- 64 regression-testing

## Selected Extensions
- None

## Task DAG
T1 -> T2

## Quality Gates
Implementation and test gates only.
