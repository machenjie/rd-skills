# L5 Web3 Payment AI Risk Router Example

## Input
Launch a checkout assistant that uses an LLM to explain token-gated subscription options, accepts card payment, and mints an access NFT after confirmed payment. It must handle webhook retries, failed mints, and prompt injection attempts.

## Routing Result

# ChangeForge Routing Result

## 1. Request Classification
- Change type: new feature, integration change, security fix, API change, data model change, backend change, frontend change, reliability improvement
- Complexity: L5 regulated/financial/Web3/AI/migration/production-critical
- Risk level: critical
- Execution mode: plan
- Product area: checkout, subscription entitlement, token-gated access
- Code area: frontend, backend, API, data, integration, security, reliability, delivery, docs
- Domain extension signals: Web3, AI, payment/trading

## 2. Interpreted Change
- Current behavior: no AI-assisted token-gated checkout with payment-confirmed NFT minting.
- Desired behavior: users receive safe AI guidance, pay by card, and receive NFT access only after authoritative payment confirmation and successful mint handling.
- User value: easier subscription selection and reliable token-gated access.
- Constraints: payment confirmation is authoritative, NFT mint failures are recoverable, AI cannot perform unsafe actions, retries are idempotent.
- Non-goals: custody of user private keys, trading marketplace, tax calculation beyond existing provider behavior.

## 3. Missing Information
- Blocking: payment provider, chain/network, custody model, NFT contract ownership, AI model/tool permissions, refund policy for failed mints.
- Non-blocking: assistant tone and analytics event names.
- Assumptions: minting is server-orchestrated after payment confirmation and user wallet signature does not expose private keys.

## 4. Impact Areas
- Product behavior: checkout, entitlement, NFT mint lifecycle
- UX: assistant guidance, payment states, wallet states, pending/failed/retry states
- Domain: subscription, payment, entitlement, mint, access token, refund/recovery
- API: checkout, webhook, assistant, mint status, entitlement APIs
- Data: payment state, mint state, audit, retry, reconciliation
- Frontend: checkout assistant, wallet connection, status UI
- Backend: payment webhook, AI orchestration, mint workflow, entitlement
- Integration: payment provider, LLM provider, blockchain network
- Security: prompt injection, webhook signature, wallet, permissions, secrets
- Testing: unit, integration, contract, E2E, replay, adversarial AI evals
- Reliability: idempotency, retries, circuit breaking, observability, recovery
- Delivery: feature flags, staged rollout, rollback, incident runbook
- Documentation: user, API, operational, security, recovery docs

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | change-intake-compiler | Critical unknowns must be resolved | request | structured brief |
| 2 | change-impact-analyzer | Cross-domain blast radius | brief | impact model |
| 3 | acceptance-criteria-builder | Define payment, AI, Web3, recovery acceptance | impact model | acceptance criteria |
| 4 | experience-impact-modeler | Checkout and failure-state UX | acceptance | UX state model |
| 5 | domain-impact-modeler | Payment, entitlement, mint state machines | brief | domain model |
| 6 | architecture-impact-reviewer | AI, payment, and mint orchestration boundaries | domain model | architecture decision |
| 7 | data-api-contract-changer | Contracts, schemas, webhooks, status APIs | architecture | API/data plan |
| 8 | integration-change-builder | Payment, LLM, and chain integration risks | contracts | integration plan |
| 9 | data-middleware-change-builder | State, queues, idempotency, reconciliation | domain/API plan | data middleware plan |
| 10 | task-dag-planner | Safe sequencing and rollback | all plans | task DAG |
| 11 | backend-change-builder | Core orchestration implementation | DAG | backend implementation |
| 12 | frontend-change-builder | Checkout assistant UI | UX/API plan | frontend implementation |
| 13 | security-privacy-gate | Prompt injection, webhook, wallet, secret, auth risks | implementation plan | security decision |
| 14 | reliability-observability-gate | Retry, failure, circuit breaker, monitoring | integration plan | reliability plan |
| 15 | quality-test-gate | Layered and adversarial tests | acceptance | evidence set |
| 16 | delivery-release-gate | Production rollout and rollback | release artifacts | release decision |
| 17 | ai-code-review-refactor | Review AI-assisted implementation risks | diff | code review findings |
| 18 | change-documentation-gate | User, API, runbook, recovery docs | final behavior | docs update |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |
| 01 | requirement-clarification | Resolve critical domain unknowns | change-intake-compiler | blocking answers |
| 04 | scenario-decomposition | Cover success, failure, abuse, recovery | acceptance-criteria-builder | scenario set |
| 10 | interaction-state-modeling | Payment, wallet, mint, AI states | experience-impact-modeler | state matrix |
| 14 | state-machine-modeling | Payment and mint lifecycles | domain-impact-modeler | transition table |
| 16 | permission-boundary-modeling | User, admin, system, provider permissions | domain-impact-modeler, security-privacy-gate | permission matrix |
| 17 | domain-event-modeling | Payment confirmed and mint events | integration-change-builder, data-middleware-change-builder | event catalog |
| 22 | event-driven-architecture | Async payment-to-mint flow | architecture-impact-reviewer | event architecture |
| 25 | data-model-design | Persist payment, mint, entitlement state | data-api-contract-changer | data model |
| 26 | api-contract-design | Checkout, assistant, webhook, status APIs | data-api-contract-changer | API contracts |
| 30 | data-migration-design | Add critical tables safely | data-api-contract-changer | migration plan |
| 42 | idempotency-retry-design | Prevent duplicate charges and duplicate mints | backend-change-builder, integration-change-builder | idempotency plan |
| 48 | transaction-consistency | Preserve entitlement invariants | data-middleware-change-builder | consistency plan |
| 50 | message-queue-design | Queue mint and reconciliation jobs | data-middleware-change-builder | queue plan |
| 52 | threat-modeling | Model AI, payment, Web3 threats | security-privacy-gate | threat model |
| 53 | input-validation | Validate checkout and assistant inputs | security-privacy-gate, backend-change-builder | validation rules |
| 56 | secret-configuration-security | Protect provider keys and webhook secrets | security-privacy-gate | secret handling plan |
| 58 | test-strategy | Critical layered test strategy | quality-test-gate | test matrix |
| 60 | integration-testing | Provider, queue, chain boundary tests | quality-test-gate | integration tests |
| 61 | contract-testing | Webhook and API compatibility | quality-test-gate | contract tests |
| 62 | e2e-testing | Critical checkout journey | quality-test-gate | E2E test |
| 64 | regression-testing | Preserve failed mint and retry behavior | quality-test-gate | regression tests |
| 65 | performance-budgeting | Bound assistant and checkout latency | reliability-observability-gate | performance budget |
| 68 | degradation-circuit-breaking | Handle LLM, provider, and chain outage | reliability-observability-gate | degradation plan |
| 69 | observability | Trace checkout through payment and mint | reliability-observability-gate | logs, metrics, traces |
| 70 | backup-recovery | Recover entitlement and audit data | reliability-observability-gate | recovery plan |
| 75 | release-rollback | Stage rollout and define stop conditions | delivery-release-gate | rollback plan |
| 78 | code-review | Review high-risk AI-assisted code | ai-code-review-refactor | review findings |
| 80 | documentation-generation | User, API, security, runbook docs | change-documentation-gate | docs package |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |
| ai-product-extension | LLM assistant, prompt injection, tool permission, generated guidance | hallucination, unsafe advice, data leakage, prompt injection | AI boundary, evals, fallback, monitoring |
| payment-trading-extension | Card payment, subscription entitlement, reconciliation | duplicate charge, false entitlement, refund gap | source of truth, idempotency, reconciliation, audit |
| web3-product-extension | NFT minting, wallet, chain confirmation | failed mint, replay, reorg, wrong network | chain state model, confirmation policy, recovery path |

## 8. Task DAG
- id: T1
- name: Resolve critical product and domain unknowns
- skill: change-intake-compiler
- capabilities: 01, 04
- depends_on: []
- files_or_artifacts: change brief and scenario set
- acceptance: provider, chain, custody, AI permission, and refund questions answered
- rollback_note: no code change

- id: T2
- name: Model experience, domain, architecture, contracts, and extensions
- skill: experience-impact-modeler, domain-impact-modeler, architecture-impact-reviewer, data-api-contract-changer
- capabilities: 10, 14, 16, 17, 22, 25, 26, 30
- depends_on: [T1]
- files_or_artifacts: state models, API/data contracts, architecture decision
- acceptance: payment-confirmed mint flow and recovery states are explicit
- rollback_note: revise plans before implementation

- id: T3
- name: Design integration and data middleware reliability
- skill: integration-change-builder, data-middleware-change-builder
- capabilities: 42, 48, 50
- depends_on: [T2]
- files_or_artifacts: webhook, queue, reconciliation, retry design
- acceptance: duplicate events cannot duplicate charge or mint
- rollback_note: disable workers and feature flag if release stops

- id: T4
- name: Implement backend orchestration and frontend checkout
- skill: backend-change-builder, frontend-change-builder
- capabilities: 42, 53
- depends_on: [T3]
- files_or_artifacts: checkout APIs, assistant UI, mint status UI
- acceptance: happy, failed payment, failed mint, retry, and injection cases pass
- rollback_note: feature flag disables assistant and mint launch

- id: T5
- name: Gate security, reliability, tests, delivery, review, and docs
- skill: security-privacy-gate, reliability-observability-gate, quality-test-gate, delivery-release-gate, ai-code-review-refactor, change-documentation-gate
- capabilities: 52, 56, 58, 60, 61, 62, 64, 65, 68, 69, 70, 75, 78, 80
- depends_on: [T4]
- files_or_artifacts: evidence package, runbook, docs
- acceptance: all critical gates pass with stop conditions and rollback
- rollback_note: documented incident and rollback plan

## 9. Quality Gates
- requirement gate: change-intake-compiler
- impact gate: change-impact-analyzer
- domain gate: domain-impact-modeler plus AI, payment/trading, and Web3 extensions
- architecture gate: architecture-impact-reviewer
- API/data gate: data-api-contract-changer
- implementation gate: backend-change-builder, frontend-change-builder, integration-change-builder, data-middleware-change-builder
- security gate: security-privacy-gate
- test gate: quality-test-gate
- reliability gate: reliability-observability-gate
- delivery gate: delivery-release-gate
- documentation gate: change-documentation-gate
- AI review gate: ai-code-review-refactor

## 10. Next Actions
- next skill calls: change-intake-compiler, change-impact-analyzer, acceptance-criteria-builder
- blocked/unblocked status: blocked on provider, chain, custody, AI permission, and refund policy
- recommended execution mode: clarify and plan before implementation

## Selected Professional Skills
- change-intake-compiler
- change-impact-analyzer
- acceptance-criteria-builder
- experience-impact-modeler
- domain-impact-modeler
- architecture-impact-reviewer
- data-api-contract-changer
- integration-change-builder
- data-middleware-change-builder
- task-dag-planner
- backend-change-builder
- frontend-change-builder
- security-privacy-gate
- reliability-observability-gate
- quality-test-gate
- delivery-release-gate
- ai-code-review-refactor
- change-documentation-gate

## Selected Capabilities
- 01 requirement-clarification
- 04 scenario-decomposition
- 10 interaction-state-modeling
- 14 state-machine-modeling
- 16 permission-boundary-modeling
- 17 domain-event-modeling
- 22 event-driven-architecture
- 25 data-model-design
- 26 api-contract-design
- 30 data-migration-design
- 42 idempotency-retry-design
- 48 transaction-consistency
- 50 message-queue-design
- 52 threat-modeling
- 53 input-validation
- 56 secret-configuration-security
- 58 test-strategy
- 60 integration-testing
- 61 contract-testing
- 62 e2e-testing
- 64 regression-testing
- 65 performance-budgeting
- 68 degradation-circuit-breaking
- 69 observability
- 70 backup-recovery
- 75 release-rollback
- 78 code-review
- 80 documentation-generation

## Selected Extensions
- ai-product-extension
- payment-trading-extension
- web3-product-extension

## Task DAG
T1 -> T2 -> T3 -> T4 -> T5

## Quality Gates
All quality gates are required.
