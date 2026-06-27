---
name: test-strategy
description: Select risk-based verification levels by change type, impacted surface, acceptance criteria, failure consequence, and release risk; use when deciding unit, integration, contract, E2E, migration, rollback, regression, performance, security, or manual evidence and when omitted test levels need residual-risk justification.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "58"
changeforge_version: 0.1.0
---

# Mission

Select the minimum sufficient verification strategy for a change: which test levels must prove which changed behaviors, which negative paths are release-blocking, which test levels can be omitted with explicit residual risk, and which validation commands produce closure evidence. The capability links acceptance criteria, repository graph, changed paths, risk surfaces, validation broker output, and release gates so teams neither over-test low-risk work nor ship high-risk work with coverage theater.

# When To Use

Use when a change requires verification planning and the right level is not self-evident:

- New or changed user journey, API, schema, migration, job, integration, auth/session, permission, payment, tenant, data-export, public contract, or behavioral rule.
- Unknown or weak previous coverage for the changed area.
- Bug fix needing regression protection, refactor needing behavior-preservation evidence, or release requiring named validation gates.
- Omission of unit, integration, contract, E2E, migration, rollback, performance, security, or manual verification needs technical justification.
- Validation Broker, affected-test selection, CI gates, or generated artifacts must map changed paths to runnable evidence.

# Do Not Use When

- The task is writing a specific test after the strategy is already decided; use `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, or `regression-testing`.
- The primary question is fixture design, test data privacy, or cleanup; use `test-data-management`.
- The change is a typo, static copy update, or no-behavior edit with an obvious single validation command.
- The work is post-release monitoring or SLO alert design; use `observability` or `reliability-observability-gate`.

# Stage Fit

- **read / intake:** map current behavior, desired behavior, acceptance criteria, changed paths, coverage baseline, and risk surfaces before choosing test levels.
- **planning:** select unit/integration/contract/E2E/migration/performance/security/manual evidence and name omitted levels with residual risk.
- **coding / refactoring:** keep public behavior and old behavior protected while implementation changes.
- **testing / validation:** run mapped commands, classify stale/partial results, and preserve what each command proves and does not prove.
- **release / handoff:** state release-blocking results, skipped coverage, residual risk owner, and next test capability.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| New behavior strategy | Feature, endpoint, flow, schema, job, integration, model, or rule | Map material risks to the cheapest reliable test level | acceptance IDs, changed behavior, level map, pass criteria | `quality-test-gate`, `acceptance-standard-definition` | Skip broad E2E matrix for local logic |
| Bug-fix regression | Verified defect, incident, failing test, or historical bug | Prove recurrence is blocked and scan related paths | repro, regression test, same-pattern scope, old/new behavior | `regression-testing`, `agent-execution-discipline` | Skip snapshot-only proof |
| Contract or migration | API/event/schema/client/migration/rollback changes | Preserve consumers, generated clients, and data integrity | contract/migration command, compatibility case, rollback result | `contract-testing`, `data-migration-design` | Skip unit-only proof |
| Security or permission | auth, tenant, PII, payment, export, input boundary | Require denied, abuse, negative, and OWASP-aligned cases | role/object matrix, denied test, security review evidence | `security-privacy-gate`, `permission-boundary-modeling` | Skip happy-path-only release |
| Minimal validation | L1 low-risk edit or local refactor with known coverage | Choose the cheapest check that can fail for the real risk | risk rating, runnable command, evidence limits | `validation-broker`, `minimal-correct-implementation` | Skip for money/auth/migration/public API risk |

# Non-Negotiable Rules

1. **Risk selects depth:** test levels are chosen by change type, impacted surface, failure consequence, and release risk, not team habit or framework availability.
2. **High-risk changes are layered:** auth, payment, migration, tenant isolation, public API, irreversible data, and security-sensitive changes need more than one evidence level.
3. **Fast lower-level tests prove local logic:** calculations, validation rules, permissions, state transitions, and mappers should not rely on E2E tests as primary coverage.
4. **Negative paths are first-class:** denial, invalid input, conflict, timeout, retry, rollback, migration failure, duplicate submit, partial failure, and provider failure are required when affected.
5. **Omissions are explicit:** each omitted level names technical reason, residual risk, compensating evidence, owner, and release consequence.
6. **Every test traces to behavior:** each required test maps to acceptance criterion, changed code path, public contract, regression, or named risk.
7. **Coverage percentage is not safety evidence:** aggregate coverage can hide untested permission, rollback, failure, and contract paths.
8. **Validation freshness matters:** source, fixture, generated input, config, migration, or report edits after a run make related evidence stale.
9. **Broker output is a closure input:** changed-path recommendations, command level, outcome, freshness, and coverage mismatch must be accepted, repaired, or disclosed.

# Industry Benchmarks

Use the Test Pyramid, Testing Trophy, Google Testing Blog guidance against excessive E2E, DORA change-failure evidence, OWASP ASVS/API Security tests, ISO/IEC 25010 quality characteristics, ISTQB test design techniques, and Pact-style consumer-driven contract testing as calibration points. Keep deep matrices in [references/checklist.md](references/checklist.md) only when the change is high-risk, cross-layer, or an omission needs review.

# Selection Rules

Select this capability when verification depth is unresolved. Route to level-specific capabilities after the strategy is chosen: `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`, `performance-budgeting`, `backup-recovery`, and `test-data-management`. Pair with `validation-broker` for changed-path command selection, `security-privacy-gate` for auth/PII/security evidence, and `delivery-release-gate` when results block rollout.

Skip when local convention already dictates the only meaningful check and no risk surface or omitted level needs a decision; state the skip reason if the change is non-trivial.

# Risk Escalation Rules

- Escalate to `quality-test-gate` when evidence is missing, stale, partial, flaky, or mismatched to changed paths.
- Escalate to `security-privacy-gate` when auth, permissions, tenant isolation, PII, secrets, uploads, payment, or abuse paths require adversarial tests.
- Escalate to `data-api-contract-changer` and `contract-testing` when public API, DTO, schema, event, generated client, SDK, or consumer compatibility changes.
- Escalate to `delivery-release-gate`, `data-migration-design`, and `backup-recovery` when migration, rollback, backfill, destructive data change, or rollout sequencing is in scope.
- Escalate to `performance-budgeting` and `reliability-observability-gate` when throughput, latency, capacity, concurrency, or SLO risk decides release safety.
- Escalate to `agent-execution-discipline` when an agent claims tests are enough without command, exit code, behavior map, or residual risk.

# Proactive Professional Triggers

- **Signal:** A high-risk change proposes only unit tests, only E2E tests, or an unspecified verification task.
  **Hidden risk:** missing permission, contract, rollback, or failure-path coverage can ship while one green layer creates false confidence.
  **Required professional action:** require layered verification, compare cheaper and heavier levels, and verify each level maps to the risk it proves before implementation or release.
  **Route to:** `quality-test-gate`, `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`.
  **Evidence required:** risk-to-test matrix, changed behavior map, required command, exit code or not-run disclosure, and residual risk owner.
- **Signal:** Unit, integration, contract, E2E, migration, security, or performance testing is omitted with no technical rationale.
  **Hidden risk:** unverified behavior is silently reclassified as unnecessary coverage.
  **Required professional action:** block closure until omission has technical reason, compensating evidence, residual risk, and owner.
  **Route to:** `validation-broker`, `agent-execution-discipline`, `delivery-release-gate`.
  **Evidence required:** omitted-level record, compensating command/report, sign-off owner, release consequence, and what evidence does not prove.
- **Signal:** Bug fix or refactor lacks reproduction, characterization, or old-behavior protection.
  **Hidden risk:** the original defect or hidden behavior change can recur despite a clean diff.
  **Required professional action:** require regression or characterization evidence and scan same-pattern locations when the fix is local.
  **Route to:** `regression-testing`, `ai-code-review-refactor`, `agent-execution-discipline`.
  **Evidence required:** repro or characterization test, old/new behavior result, same-pattern scan, and validation output.
- **Signal:** API, event, generated client, SDK, schema, or migration change is covered only by local logic tests.
  **Hidden risk:** consumers or production data break while local code remains green.
  **Required professional action:** require contract, generated-client, forward/rollback, or compatibility evidence before release.
  **Route to:** `contract-testing`, `data-api-contract-changer`, `backup-recovery`.
  **Evidence required:** consumer/contract map, schema or migration command, rollback result, compatibility fixture, and residual data risk.
- **Signal:** Validation evidence predates final source, fixture, config, migration, generated artifact, or report changes.
  **Hidden risk:** stale green output is reported as current test confidence and missing reruns can hide changed-path coverage gaps.
  **Required professional action:** verify freshness, rerun mapped validators, or mark the strategy partial/not verified with next command and owner.
  **Route to:** `validation-broker`, `quality-test-gate`, `plan-execution-consistency`.
  **Evidence required:** changed paths, command freshness, report/artifact path, exit code, coverage alignment, and stale-check disclosure.

# Critical Details

- **Layer responsibility:** unit proves local rules and edge cases; integration proves real boundary behavior; contract proves consumer-visible compatibility; E2E proves critical journeys; migration proves forward/rollback/data integrity; performance proves measured budgets; security proves abuse and denial cases.
- **Negative case ownership:** every affected denial, invalid input, duplicate, timeout, conflict, partial failure, provider error, rollback, and permission branch has a test or residual-risk record.
- **Migration realism:** migration tests need representative schema/data shape, sanitized when production-derived, not only a clean database.
- **E2E restraint:** E2E confirms orchestration; it is not a substitute for branch matrices, permission matrices, contract examples, or migration rollback proof.
- **Manual verification:** manual evidence is allowed only with exact steps, expected result, artifact, owner, and reason automation is not currently feasible.
- **Flaky or skipped tests:** classify signature, owner, blocked risk, quarantine/remediation, and whether the missing signal blocks release.
- **Test data:** fixtures must be owned, isolated, synthetic/anonymized, and sufficient for the assertion; delegate deep fixture design to `test-data-management`.

# Reference Loading Policy

The body carries layer selection, risk, evidence, and closure rules. Load [references/checklist.md](references/checklist.md) when the change is high-risk, cross-layer, security-sensitive, migration/release-sensitive, has omitted levels, or needs a compact operator checklist. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when benchmark-backed layer selection, omission review, affected-test strategy, mutation-style assertion quality, or anti-pattern detail is needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, artifact/report evidence, or a changed-code-to-test map. Use [examples/example-output.md](examples/example-output.md) only when sample output shape is needed.

# Failure Modes

- **Coverage theater:** aggregate line coverage is reported while critical behavior, denial, rollback, or contract paths are untested.
- **Happy-path-only strategy:** payment, auth, export, migration, or integration failure paths are omitted.
- **E2E inversion:** slow browser/system tests become the only protection for local business rules.
- **Unit-only contract change:** API, event, SDK, or generated client breaks downstream consumers.
- **Clean-schema migration test:** production-like schema, data, constraints, and rollback are never exercised.
- **Omitted level without owner:** skipped coverage has no technical reason, compensating evidence, or residual-risk owner.
- **Stale green run:** source or generated inputs change after validation, but old output is treated as current.
- **Flaky gate ignored:** retried or skipped tests hide a real risk signal.

# Evidence Contract

Test strategy closes only when these answers are concrete:

- **Basis:** change type, impacted surfaces, acceptance criteria, failure consequence, and risk rating.
- **Boundaries inspected:** changed paths, public contracts, existing coverage, fixtures, generated artifacts, migrations, CI gates, validation broker output, and skipped areas.
- **Risk-to-test mapping:** each material risk mapped to level, behavior, command, pass criteria, owner, and release consequence.
- **Omitted-level rationale:** technical reason, residual risk, compensating evidence, sign-off owner, and what remains unproven.
- **Validation evidence:** literal command, working directory, exit code, report or artifact, freshness after latest edit, and coverage alignment.
- **What evidence proves:** exact behavior, contract, migration, journey, regression, or release gate covered.
- **What evidence does not prove:** skipped levels, external consumers, production data shape, scale, browser/runtime variance, flaky signals, or untested abuse paths.
- **Residual risk and next gate:** accepted gap, owner, threshold that reopens review, and target capability.

# Output Contract

Return a **Test Strategy** with:

- **Mode selected:** new behavior, bug-fix regression, contract/migration, security/permission, or minimal validation.
- **Change and impact:** changed behavior, surfaces, public contracts, data/schema/migration, integrations, and release risk.
- **Risk rating:** low/medium/high/critical with failure consequence.
- **Required test levels:** unit, integration, contract, E2E, migration, regression, performance, security, manual; each with behavior, cases, owner, acceptance trace, and command.
- **Negative and boundary coverage:** denied, invalid, rollback, timeout, conflict, duplicate, partial failure, permission, and regression cases.
- **Changed-code-to-test map:** changed path or contract -> behavior/risk -> test level -> command/artifact -> owner -> stale/not-run status.
- **Omitted levels:** technical reason, residual risk, compensating evidence, sign-off owner, and release consequence.
- **Validation broker plan:** changed paths, command level, stale checks, skipped full validators, and freshness expectation.
- **Decision:** approved, blocked, not verified, release-gated, or handoff required.
- **Residual risk and next gate:** accepted gap, owner, command, and routed capability.

# Quality Gate

1. Risk rating is justified by change type, impacted surface, and failure consequence.
2. Every selected test level names the behavior and risk it proves.
3. Every test maps to acceptance criteria, changed path, public contract, regression, or named risk.
4. High-risk paths include negative, permission, rollback, migration, failure, and abuse cases when affected.
5. Omitted levels have technical reason, residual risk, compensating evidence, and owner.
6. E2E is not the only coverage for complex local logic.
7. Contract/API/schema/event changes include consumer or compatibility evidence.
8. Migration/data changes include forward, rollback, and data-integrity evidence.
9. Release-blocking criteria and CI/validator commands are named.
10. Validation evidence is fresh after final material edits and states what it proves and does not prove.

# Used By

Used by `quality-test-gate` and `task-dag-planner`.

# Handoff

- `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, and `regression-testing` for level-specific design.
- `performance-budgeting`, `security-privacy-gate`, `backup-recovery`, and `test-data-management` when performance, security, recovery, or fixture depth owns the next decision.
- `validation-broker`, `plan-execution-consistency`, and `agent-execution-discipline` when command freshness, changed-path coverage, or closure evidence is unresolved.

# Completion Criteria

The strategy is complete when verification depth is proportionate to risk, every material risk maps to executable evidence or an owned residual risk, high-risk changes have layered verification, omissions are justified, validation is fresh, and the next test capability can act without guessing what must pass before release.
