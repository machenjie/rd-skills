# L4 SaaS Feature Router Example

## Input
Add an admin-only usage limits feature for SaaS workspaces. Admins can set monthly seat and export limits, users see clear blocked states, and billing staff can audit limit changes.

## Routing Result

# ChangeForge Routing Result

## 1. Request Classification
- Change type: new feature, frontend change, backend change, API change, data model change, configuration change
- Complexity: L4 product-grade high-risk change
- Risk level: high
- Execution mode: plan
- Product area: workspace administration and billing operations
- Code area: frontend, backend, API, data, security, tests, docs
- Domain extension signals: payment/trading signal is possible because billing operations and entitlements are affected

## 2. Interpreted Change
- Current behavior: workspace usage limits are not configurable by admins or auditable by billing staff.
- Desired behavior: admins manage monthly seat/export limits, blocked users receive clear states, and billing staff can audit changes.
- User value: workspaces can enforce plan limits with transparent administration.
- Constraints: admin-only writes, audit trail required, billing staff read-only audit access.
- Non-goals: payment provider integration, invoice generation, plan pricing changes.

## 3. Missing Information
- Blocking: authoritative source for plan entitlements and whether billing staff are internal or tenant-scoped.
- Non-blocking: limit reset timezone and copy for blocked states.
- Assumptions: limits are enforced server-side and frontend only reflects the result.

## 4. Impact Areas
- Product behavior: limit management and blocked workflow
- UX: admin setting forms and user blocked states
- Domain: workspace, limit, entitlement, audit event
- API: admin limit endpoints and audit read API
- Data: limits and audit records
- Frontend: admin console and blocked states
- Backend: enforcement and audit
- Integration: billing data may be referenced but provider integration is not in scope
- Security: admin authorization and staff audit access
- Testing: unit, integration, contract, E2E, permission tests
- Reliability: enforcement must be consistent under concurrent usage
- Delivery: staged rollout and rollback
- Documentation: admin, API, operational audit notes

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | change-intake-compiler | Clarify authority and staff scope | feature request | structured change brief |
| 2 | change-impact-analyzer | High-risk multi-surface impact | change brief | impact model |
| 3 | acceptance-criteria-builder | Define admin, user, audit, and negative paths | impact model | acceptance criteria |
| 4 | experience-impact-modeler | Blocked states and admin workflow | acceptance criteria | UX state model |
| 5 | domain-impact-modeler | Entitlements, limits, audit, permissions | change brief | domain model |
| 6 | architecture-impact-reviewer | Enforce boundaries for entitlement checks | domain model | architecture decision |
| 7 | data-api-contract-changer | Limit and audit contracts | domain model | API/data plan |
| 8 | task-dag-planner | Sequence high-risk slices | contracts | task DAG |
| 9 | backend-change-builder | Server-side enforcement | DAG | backend implementation |
| 10 | frontend-change-builder | Admin and blocked UI | UX/API plan | frontend implementation |
| 11 | security-privacy-gate | Admin, staff, and audit authorization | implementation plan | security decision |
| 12 | reliability-observability-gate | Concurrent usage and observability | enforcement plan | reliability plan |
| 13 | quality-test-gate | Layered verification | acceptance criteria | evidence set |
| 14 | delivery-release-gate | Staged release and rollback | migration/config plan | release plan |
| 15 | change-documentation-gate | Admin and operational docs | final behavior | docs update |
| 16 | ai-code-review-refactor | Review generated or broad code changes | final diff | quality review |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |
| 03 | user-role-identification | Separate admin, user, and billing staff | change-intake-compiler | role inventory |
| 05 | acceptance-standard-definition | Make done verifiable | acceptance-criteria-builder | acceptance standard |
| 10 | interaction-state-modeling | Blocked, empty, error, success states | experience-impact-modeler | state matrix |
| 13 | business-rule-extraction | Extract entitlement and limit rules | domain-impact-modeler | rule catalog |
| 16 | permission-boundary-modeling | Admin and staff access control | domain-impact-modeler, security-privacy-gate | permission matrix |
| 19 | module-boundary-design | Keep entitlement enforcement centralized | architecture-impact-reviewer | boundary map |
| 25 | data-model-design | Store limits and audit events | data-api-contract-changer | data model |
| 26 | api-contract-design | Admin and audit API behavior | data-api-contract-changer | API contract |
| 42 | idempotency-retry-design | Avoid duplicate limit changes | backend-change-builder | idempotency plan |
| 48 | transaction-consistency | Enforce limits consistently | data-middleware-change-builder | transaction plan |
| 52 | threat-modeling | Model admin abuse and audit risk | security-privacy-gate | threat model |
| 58 | test-strategy | Layered risk-based tests | quality-test-gate | test plan |
| 62 | e2e-testing | Critical admin/user journey | quality-test-gate | E2E cases |
| 67 | concurrency-control | Prevent race-based limit bypass | reliability-observability-gate | concurrency plan |
| 69 | observability | Track limit enforcement and audit failures | reliability-observability-gate | metrics/logs |
| 75 | release-rollback | Staged rollout and rollback | delivery-release-gate | release plan |
| 78 | code-review | Review high-risk generated code | ai-code-review-refactor | review findings |
| 80 | documentation-generation | Update admin and operations docs | change-documentation-gate | documentation |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |
| payment-trading-extension | Billing staff audit and entitlement enforcement can affect subscription value | false entitlement, audit gaps, billing dispute | source of truth, audit plan, reconciliation decision |

## 8. Task DAG
- id: T1
- name: Clarify entitlement authority and roles
- skill: change-intake-compiler
- capabilities: 03
- depends_on: []
- files_or_artifacts: change brief
- acceptance: authority and role boundaries are explicit
- rollback_note: no code change

- id: T2
- name: Model UX, domain, architecture, and contracts
- skill: experience-impact-modeler, domain-impact-modeler, architecture-impact-reviewer, data-api-contract-changer
- capabilities: 10, 13, 16, 19, 25, 26
- depends_on: [T1]
- files_or_artifacts: UX states, domain rules, API/data contracts
- acceptance: limits are server-enforced and auditable
- rollback_note: revise before implementation

- id: T3
- name: Implement backend enforcement and audit
- skill: backend-change-builder
- capabilities: 42, 48
- depends_on: [T2]
- files_or_artifacts: services, repositories, audit events
- acceptance: enforcement and audit tests pass
- rollback_note: disable feature flag and revert server patch if needed

- id: T4
- name: Implement admin and blocked-state frontend
- skill: frontend-change-builder
- capabilities: 10
- depends_on: [T2]
- files_or_artifacts: admin pages, user blocked states
- acceptance: role-specific UX states pass tests
- rollback_note: hide UI behind feature flag

- id: T5
- name: Gate security, reliability, tests, release, docs, and review
- skill: security-privacy-gate, reliability-observability-gate, quality-test-gate, delivery-release-gate, change-documentation-gate, ai-code-review-refactor
- capabilities: 52, 58, 62, 67, 69, 75, 78, 80
- depends_on: [T3, T4]
- files_or_artifacts: evidence package
- acceptance: all gates pass with rollback and audit evidence
- rollback_note: documented staged rollback plan

## 9. Quality Gates
- requirement gate: change-intake-compiler
- impact gate: change-impact-analyzer
- domain gate: domain-impact-modeler and payment-trading-extension
- architecture gate: architecture-impact-reviewer
- API/data gate: data-api-contract-changer
- implementation gate: backend-change-builder, frontend-change-builder
- security gate: security-privacy-gate
- test gate: quality-test-gate
- reliability gate: reliability-observability-gate
- delivery gate: delivery-release-gate
- documentation gate: change-documentation-gate
- AI review gate: ai-code-review-refactor

## 10. Next Actions
- next skill calls: change-intake-compiler, change-impact-analyzer, acceptance-criteria-builder
- blocked/unblocked status: blocked on entitlement authority and role scope
- recommended execution mode: clarify then plan

## Selected Professional Skills
- change-intake-compiler
- change-impact-analyzer
- acceptance-criteria-builder
- experience-impact-modeler
- domain-impact-modeler
- architecture-impact-reviewer
- data-api-contract-changer
- task-dag-planner
- backend-change-builder
- frontend-change-builder
- security-privacy-gate
- reliability-observability-gate
- quality-test-gate
- delivery-release-gate
- change-documentation-gate
- ai-code-review-refactor

## Selected Capabilities
- 03 user-role-identification
- 05 acceptance-standard-definition
- 10 interaction-state-modeling
- 13 business-rule-extraction
- 16 permission-boundary-modeling
- 19 module-boundary-design
- 25 data-model-design
- 26 api-contract-design
- 42 idempotency-retry-design
- 48 transaction-consistency
- 52 threat-modeling
- 58 test-strategy
- 62 e2e-testing
- 67 concurrency-control
- 69 observability
- 75 release-rollback
- 78 code-review
- 80 documentation-generation

## Selected Extensions
- payment-trading-extension

## Task DAG
T1 -> T2 -> T3 and T4 -> T5

## Quality Gates
All gates except no separate external integration gate unless billing provider calls enter scope.
