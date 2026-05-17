# L3 API Data Change Router Example

## Input
Add saved search folders. Users can create folders, move saved searches into them, and list searches by folder. Keep existing saved-search APIs compatible.

## Routing Result

# ChangeForge Routing Result

## 1. Request Classification
- Change type: new feature, API change, data model change, backend change, frontend change
- Complexity: L3 multi-module product change
- Risk level: medium
- Execution mode: plan then implement
- Product area: saved search management
- Code area: frontend, backend, API, data, tests, docs
- Domain extension signals: none

## 2. Interpreted Change
- Current behavior: saved searches are flat.
- Desired behavior: users can organize saved searches into folders while old APIs remain compatible.
- User value: easier organization and retrieval of saved searches.
- Constraints: preserve existing list behavior and clients.
- Non-goals: sharing folders, nested folders, team permissions, search engine changes.

## 3. Missing Information
- Blocking: folder ownership model and maximum nesting decision.
- Non-blocking: default folder naming and empty-state copy.
- Assumptions: one-level user-owned folders are sufficient for first release.

## 4. Impact Areas
- Product behavior: saved-search organization
- UX: folder create, move, empty, and list states
- Domain: folder ownership and saved-search membership
- API: create/list/move folder endpoints or compatible extensions
- Data: new folder model and saved-search association
- Frontend: management UI and API integration
- Backend: services, validation, authorization
- Integration: none
- Security: user ownership checks
- Testing: unit, integration, contract, frontend
- Reliability: migration and query performance
- Delivery: migration rollout
- Documentation: API and user-facing notes

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | change-intake-compiler | Bound folders and non-goals | feature request | structured change brief |
| 2 | change-impact-analyzer | Multi-surface impact | change brief | impact matrix |
| 3 | acceptance-criteria-builder | Define testable folder behavior | impact matrix | acceptance criteria |
| 4 | domain-impact-modeler | Ownership and membership rules | accepted scope | domain model |
| 5 | data-api-contract-changer | New data and compatible APIs | domain model | data/API contract |
| 6 | task-dag-planner | Migration and implementation sequencing | contracts | reviewable DAG |
| 7 | backend-change-builder | Backend behavior | DAG and contracts | backend implementation |
| 8 | frontend-change-builder | UI behavior | API contract | frontend implementation |
| 9 | quality-test-gate | Layered verification | acceptance criteria | test evidence |
| 10 | delivery-release-gate | Migration rollout | data/API plan | release plan |
| 11 | change-documentation-gate | API and behavior docs | final behavior | documentation update |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |
| 02 | requirement-structuring | Convert broad feature into bounded scope | change-intake-compiler | structured brief |
| 06 | non-goal-boundary-definition | Prevent nested folders and sharing creep | change-intake-compiler | non-goal list |
| 12 | domain-object-identification | Identify folder and saved-search relationship | domain-impact-modeler | domain inventory |
| 16 | permission-boundary-modeling | Enforce user ownership | domain-impact-modeler, backend-change-builder | permission matrix |
| 25 | data-model-design | Model folder storage | data-api-contract-changer | data model |
| 26 | api-contract-design | Preserve existing API compatibility | data-api-contract-changer | API contract |
| 29 | version-compatibility | Avoid breaking existing clients | data-api-contract-changer | compatibility plan |
| 30 | data-migration-design | Add data safely | data-api-contract-changer, delivery-release-gate | migration plan |
| 35 | frontend-api-integration | Wire UI to folder APIs | frontend-change-builder | client integration plan |
| 58 | test-strategy | Choose layered tests | quality-test-gate | test matrix |
| 61 | contract-testing | Preserve API compatibility | quality-test-gate | contract tests |
| 75 | release-rollback | Roll out migration safely | delivery-release-gate | rollback plan |
| 80 | documentation-generation | Update docs | change-documentation-gate | docs update |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |
| None | No specialized domain signal | None | None |

## 8. Task DAG
- id: T1
- name: Compile scope and acceptance
- skill: change-intake-compiler, acceptance-criteria-builder
- capabilities: 02, 06
- depends_on: []
- files_or_artifacts: change brief, acceptance criteria
- acceptance: one-level folders and non-goals are explicit
- rollback_note: no code change

- id: T2
- name: Model domain, data, and API compatibility
- skill: domain-impact-modeler, data-api-contract-changer
- capabilities: 12, 16, 25, 26, 29, 30
- depends_on: [T1]
- files_or_artifacts: domain model, migration, API contract
- acceptance: existing clients remain compatible
- rollback_note: reject or revise contract before implementation

- id: T3
- name: Implement backend and migration
- skill: backend-change-builder
- capabilities: 16, 30
- depends_on: [T2]
- files_or_artifacts: services, repositories, migration
- acceptance: ownership checks and folder operations pass tests
- rollback_note: use migration rollback or forward fix plan

- id: T4
- name: Implement frontend folder workflow
- skill: frontend-change-builder
- capabilities: 35
- depends_on: [T2]
- files_or_artifacts: folder UI, API client
- acceptance: create, move, list, empty, and error states work
- rollback_note: hide UI if backend rollout is stopped

- id: T5
- name: Verify, release, and document
- skill: quality-test-gate, delivery-release-gate, change-documentation-gate
- capabilities: 58, 61, 75, 80
- depends_on: [T3, T4]
- files_or_artifacts: tests, release plan, docs
- acceptance: migration and compatibility evidence are complete
- rollback_note: release rollback references migration plan

## 9. Quality Gates
- requirement gate: change-intake-compiler
- impact gate: change-impact-analyzer
- domain gate: domain-impact-modeler
- architecture gate: skipped, no boundary change expected
- API/data gate: data-api-contract-changer
- implementation gate: backend-change-builder, frontend-change-builder
- security gate: covered by permission capability; escalate if multi-user sharing appears
- test gate: quality-test-gate
- reliability gate: skipped unless query performance degrades
- delivery gate: delivery-release-gate
- documentation gate: change-documentation-gate
- AI review gate: skipped

## 10. Next Actions
- next skill calls: change-intake-compiler, change-impact-analyzer, acceptance-criteria-builder
- blocked/unblocked status: blocked on folder ownership and nesting decision
- recommended execution mode: clarify then plan

## Selected Professional Skills
- change-intake-compiler
- change-impact-analyzer
- acceptance-criteria-builder
- domain-impact-modeler
- data-api-contract-changer
- task-dag-planner
- backend-change-builder
- frontend-change-builder
- quality-test-gate
- delivery-release-gate
- change-documentation-gate

## Selected Capabilities
- 02 requirement-structuring
- 06 non-goal-boundary-definition
- 12 domain-object-identification
- 16 permission-boundary-modeling
- 25 data-model-design
- 26 api-contract-design
- 29 version-compatibility
- 30 data-migration-design
- 35 frontend-api-integration
- 58 test-strategy
- 61 contract-testing
- 75 release-rollback
- 80 documentation-generation

## Selected Extensions
- None

## Task DAG
T1 -> T2 -> T3 and T4 -> T5

## Quality Gates
Requirement, impact, domain, API/data, implementation, test, delivery, and documentation gates.
