---
name: requirement-structuring
description: Structures raw change input into a professional change brief covering behavior, trigger, actor, scope, non-goals, constraints, acceptance signals, and test traceability.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "02"
changeforge_version: 0.1.0
---

# Mission

**Transform confirmed requirement facts into a stable, implementation-neutral change brief** that describes current behavior, desired behavior, trigger, actor, scope, non-goals, constraints, acceptance signals, and test traceability — giving every downstream capability (design, planning, implementation, testing) a single authoritative source of truth that can be traced end-to-end from requirement to verified outcome.

# When To Use

Use this capability when: a request is unambiguous and clarified (all blocking unknowns are resolved — see `requirement-clarification`) but still needs professional structure before design or implementation begins; an incoming requirement is expressed as a code change ("change this function") rather than a behavior change ("users should be able to do X"); a new feature, bug fix, or behavior change needs a test traceability matrix before the implementation starts; or a change spans multiple surfaces (API, frontend, database, configuration) and a single structured brief is needed to coordinate all implementers.

# Do Not Use When

Do not use this capability to: resolve unresolved authority questions (use `requirement-clarification` first); expand scope beyond the confirmed request ("while we're here, we could also…"); encode implementation tasks before behavior has been described; or produce implementation-specific designs (architecture, schema, API contract — those follow from the structured brief, they are not part of it).

# Non-Negotiable Rules

- **Describe current behavior as observable system behavior, not as speculation or source code description.** "The API returns 200 with an empty array" is an observable behavior. "The service calls `findAll()` and returns the result" is a code description — it says nothing about observable behavior. Rule: current behavior must be described as: what input → what output / side effect / state change, for which actor, under which precondition. If current behavior is unknown, that is a blocking unknown that must be resolved (via `requirement-clarification`) before structuring.
- **Describe desired behavior as the outcome the user or system needs, before naming implementation.** "Users should be able to cancel a pending order and receive a refund" is a desired behavior. "Add a DELETE /api/orders/:id endpoint" is an implementation choice. The implementation must follow from the behavior — not the other way around. Rule: desired behavior is written as: [Actor] can/must/must not [perform action / observe outcome] [when/given precondition]. Implementation choices belong in design, not in the requirement brief.
- **Non-goals must be explicit and specific.** Vague non-goals like "out of scope for this sprint" are not useful. Specific non-goals prevent scope creep: "Does NOT change the subscription billing cycle" is specific and prevents a developer from interpreting "cancel order" as implying subscription cancellation. Rule: every non-goal must be specific enough that an implementer cannot accidentally implement it while building the in-scope work.
- **Every meaningful requirement must trace to at least one verification artifact.** Verification artifact types: unit test (specific function/method behavior), integration test (cross-layer behavior), contract test (API consumer compatibility), E2E test (end-to-end user flow), migration test (data integrity after schema change), manual review artifact (accessibility audit, security review, compliance sign-off), observability signal (metric emitted, log entry, alert firing). A requirement with no verification path is not implementable — it has no done signal.
- **Constraints must be binding, not informative.** A constraint is not "we should try to keep response time reasonable." A constraint is "p99 response time must be ≤ 200ms under the production load baseline (measured in staging)." Constraints in the brief bind the implementation. If a constraint cannot be bound to a measurable criterion, it should not be listed as a constraint — it should be listed as a risk or noted as a quality concern for the quality gate.
- **Scope must include affected surfaces and explicit exclusions.** "In scope: the order cancellation API endpoint, the order status state machine, the refund initiation trigger. Out of scope: refund processing, subscription management, notification delivery." If a surface is not explicitly named in-scope or out-of-scope and an implementer touches it, the brief has failed to bound the change.

# Industry Benchmarks

Anchor against: **IEEE Std 830 / ISO/IEC/IEEE 29148 (Systems and Software Requirements Engineering)** — requirements shall be: complete, consistent, unambiguous, verifiable, traceable, and feasible. **Behavior-Driven Development (BDD) / Gherkin syntax** — Given/When/Then format explicitly separates precondition (Given), trigger (When), and expected outcome (Then); widely adopted as a requirement verification bridge between product and engineering. **Acceptance Test-Driven Development (ATDD)** — acceptance tests are written before implementation begins; the structured brief defines the acceptance test preconditions. **INVEST criteria (Bill Wake, 2003)** — Independent, Negotiable, Valuable, Estimable, Small, Testable; a requirement that fails any INVEST criterion needs restructuring before implementation. **SAFe / Agile requirement models** — Feature → Acceptance Criteria → Test Scenario traceability; sprint ready criteria. **ISO/IEC 25010 (SQuaRE)** — quality characteristics as constraint inputs: functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, portability.

### Requirement Brief Template

```
Change Brief: [Change ID or title]
Author: [Name]
Date: [Date]
Status: [Draft / Reviewed / Approved]

Summary:
  One sentence describing what changes and why.

Current Behavior (observable):
  [Actor/System] currently [does X] when [precondition/trigger].
  Example: "When a customer submits a cancellation request for a pending order,
  the API returns 200 with no action taken. The order status is unchanged."

Desired Behavior (outcome-first):
  [Actor] should be able to [achieve outcome] when [precondition].
  Example: "A customer should be able to cancel a pending order and have the
  order status set to 'cancelled' and a refund initiated within 60 seconds."

Trigger: [What initiates the behavior: user action, event, schedule, API call]
Actor: [Who initiates: authenticated customer, admin user, system scheduler]

In-Scope Work (explicit surface list):
  - Order cancellation API endpoint: POST /api/orders/:id/cancel
  - Order status state machine: PENDING → CANCELLED transition
  - Refund initiation trigger (NOT refund processing)

Non-Goals (specific exclusions):
  - Does NOT change subscription cancellation behavior
  - Does NOT process the refund (refund processor is a separate service)
  - Does NOT send cancellation notification (notification service is separate)
  - Does NOT allow cancellation of orders in SHIPPED or DELIVERED status

Constraints (binding, measurable):
  - p99 response time ≤ 200ms at production load baseline
  - Must be backward-compatible with existing API consumers (no field removal)
  - Cancellation is idempotent: POST /cancel on an already-cancelled order returns 200
  - Regulatory: refund must be initiated within 60 seconds of cancellation (payment SLA)

Assumptions (approved):
  - [Safe engineering assumption: source]
  - [Stakeholder assumption: stated by, verified or unverified]

Dependencies:
  - Refund service API: provides POST /refunds endpoint (version 2.1 contract)
  - Feature flag: order-cancellation-enabled (default: disabled; enable per tenant)

Acceptance Signals (must be verifiable):
  - A pending order can be cancelled by the order owner
  - A non-pending order (SHIPPED, DELIVERED) returns 422 with error code ORDER_NOT_CANCELLABLE
  - Cancellation is idempotent (second POST returns 200 with same response)
  - Refund initiation is triggered within 60 seconds (observable via audit log)
  - Admin users can cancel any order regardless of status

Requirement-to-Test Traceability:
  Requirement                    | Verification Type    | Test ID / Description
  --------------------------------|----------------------|----------------------------------
  Owner can cancel pending order | Integration test     | OrderCancellationTest#ownerCancels
  Non-pending returns 422        | Unit test            | OrderStateMachineTest#invalidTransition
  Idempotent cancellation        | Integration test     | OrderCancellationTest#idempotent
  Refund triggered within 60s    | Integration test     | RefundTriggerTest#withinSLA
  Admin can cancel any order     | Integration test     | OrderCancellationTest#adminOverride
  p99 ≤ 200ms                    | Performance test     | k6 cancellation load test
```

### BDD Acceptance Scenario Template

```
Feature: Order Cancellation

  Scenario: Customer cancels a pending order
    Given a customer has a pending order with ID "order-123"
    And the order was placed less than 24 hours ago
    When the customer submits a cancellation request
    Then the order status changes to "cancelled"
    And a refund is initiated within 60 seconds
    And the cancellation response includes the updated order status

  Scenario: Customer attempts to cancel a shipped order
    Given a customer has an order with ID "order-456" in status "shipped"
    When the customer submits a cancellation request
    Then the response status is 422
    And the error code is "ORDER_NOT_CANCELLABLE"
    And the order status is unchanged

  Scenario: Idempotent cancellation
    Given a customer has already cancelled order "order-789"
    When the customer submits a second cancellation request
    Then the response status is 200
    And the order status remains "cancelled"
```

# Selection Rules

Select this capability when **known requirement facts need professional structure before implementation begins**. Route elsewhere when: `requirement-clarification` is primary (open questions must be resolved before structuring); `acceptance-standard-definition` is primary (the behavior is known, but what "done" looks like needs precision); `use-case-modeling` is primary (a complex multi-actor workflow needs path-level decomposition — single actor + single flow briefs may be insufficient); `scenario-decomposition` is primary (a large brief needs to be decomposed into independently implementable scenarios for task planning).

# Risk Escalation Rules

Escalate when: the structured brief reveals conflicting desired behaviors (two acceptance criteria contradict each other — requires product authority resolution before design begins); a constraint cannot be expressed as a measurable criterion (vague performance or compliance constraint — requires clarification from the constraint owner); the brief exposes a dependency on an external contract, partner API, or legal agreement that has not been confirmed (requires confirmation before the brief is approved); the scope boundary is disputed between teams (two teams claim ownership of the same surface — requires architecture or product resolution); or the change has backward-compatibility implications for existing API consumers that were not stated in the original request.

# Critical Details

- **The brief is the traceability anchor, not a specification document.** It does not describe implementation. It describes what must be true after implementation. Every subsequent artifact (API design, database schema, test cases, release plan) should be traceable to the brief. If a test cannot be traced to a requirement in the brief, the test is either testing internal implementation (acceptable but not traced) or testing something out of scope (requires brief amendment).
- **Current behavior description prevents regression.** If current behavior is not documented, future implementers cannot distinguish "this changed intentionally" from "this regressed accidentally." The current behavior description serves as the baseline for regression test design.
- **Test traceability matrix is written before implementation, not after.** Writing the traceability matrix after implementation means it maps to what was built, not to what was required. Writing it before ensures all requirements have a verification path and that any unverifiable requirement is identified before anyone builds it.
- **"Done" is defined by the acceptance signals, not by the implementation task list.** A change is done when the acceptance signals are verifiably met, not when the implementation tasks are checked off. A developer who completes all tasks but the acceptance signals are not met has not delivered the requirement.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Current behavior: "The function currently calls findById" | Describes code, not observable behavior; useless for regression detection | "The API returns 404 when the order ID does not exist" |
| Desired behavior: "Add a DELETE /api/orders/:id endpoint" | Describes implementation, not outcome; forces implementation choice before design | "A customer should be able to cancel a pending order and receive a confirmation" |
| Non-goal: "Out of scope for this sprint" | Time-bound, not behavior-bound; next sprint can add anything without brief amendment | "Does NOT change notification delivery" (behavior-specific exclusion) |
| Constraint: "Response should be fast" | Not measurable; cannot be a done criterion; rubber-stamped | "p99 ≤ 200ms at production load baseline (measured in staging with k6)" |
| Acceptance signal: "It works correctly" | Not verifiable; depends on subjective judgment | Specific Given/When/Then scenario with observable outcome |
| No test traceability column | Requirement exists but no verification path; "done" is undefined | Traceability matrix: requirement → verification type → test ID |

# Failure Modes

- Brief describes implementation ("add the endpoint") instead of behavior; team implements the endpoint but misses the state machine transition — order can be cancelled but status does not change.
- Current behavior not documented; refactoring changes behavior; no regression test baseline; regression discovered in production.
- Non-goals are vague; developer adds notification delivery "while in there"; notification service is not ready; release delayed.
- Constraint is unmeasurable; 800ms response time shipped; stakeholder reports "it's too slow"; no agreed baseline to dispute against.
- Test traceability not written before implementation; 40% of acceptance criteria have no automated test; discovered at quality-test-gate review.
- Brief approved without backward-compatibility constraint; field removed from API response; existing consumer breaks; emergency rollback.

# Output Contract

Return a structured change brief with:

- `summary` (one sentence: what changes and why)
- `current_behavior` (observable: actor → precondition → output/state, per affected surface)
- `desired_behavior` (outcome-first: [actor] can/must [achieve outcome] [when precondition])
- `trigger` (what initiates the behavior)
- `actor` (who initiates: role, authentication state)
- `in_scope_work` (explicit surface list with named components)
- `non_goals` (specific exclusions, behavior-bound)
- `constraints` (binding, measurable criteria per constraint)
- `assumptions` (safe engineering + explicit stakeholder, sourced)
- `dependencies` (external services, contracts, feature flags)
- `acceptance_signals` (verifiable Given/When/Then scenarios)
- `requirement_test_traceability` (per requirement: verification type, test ID/description)

# Quality Gate

The structured brief is complete only when:

1. Current behavior is described as observable behavior, not code description.
2. Desired behavior is described as outcome, not implementation choice.
3. Every non-goal is specific enough to prevent unintentional scope expansion.
4. Every constraint is measurable and bound to a criterion.
5. Acceptance signals are written as verifiable scenarios (Given/When/Then).
6. Every meaningful requirement has at least one verification path.
7. In-scope work explicitly names all affected surfaces.
8. Non-goals explicitly exclude adjacent surfaces that could be ambiguous.
9. No blocking unknown remains unresolved.
10. The brief is approved by the requirement authority before design begins.

# Used By

- change-intake-compiler

# Handoff

Hand off to `scenario-decomposition` to break the brief into independently implementable tasks; `acceptance-standard-definition` to sharpen the done criteria; `task-dag-planner` for task sequencing and dependency planning; or the relevant domain professional skill (backend-change-builder, frontend-change-builder, etc.) when the brief is ready for implementation planning.

# Completion Criteria

The capability is complete when **the raw request is transformed into a bounded, traceable change brief where every requirement has a verification path, every non-goal is behavior-specific, every constraint is measurable, and the brief is approved before design or implementation begins**.
