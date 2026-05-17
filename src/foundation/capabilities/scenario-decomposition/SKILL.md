---
name: scenario-decomposition
description: Decomposes a change into normal, failure, edge, abuse, recovery, and operational scenarios for implementation and verification planning.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "04"
changeforge_version: 0.1.0
---

# Mission

**Decompose a confirmed requirement into a complete scenario matrix** — covering normal paths, alternate paths, edge conditions, failure/fault scenarios, abuse and misuse scenarios, recovery paths, and operational support scenarios — so that implementers cannot build only the happy path while leaving unexamined risks to be discovered in production, and so that every scenario has an actor, precondition, stimulus, expected outcome, verification method, and release criticality classification.

# When To Use

Use this capability when: a structured requirement brief exists but scenario coverage needs to be explicitly mapped before planning begins; a change touches a state machine, workflow, or multi-step process where partial completion is possible; a behavior has authorization, concurrent access, external dependency, or data integrity dimensions that a single happy path does not cover; a prior incident revealed that a failure case was not anticipated; or the quality gate requires a scenario matrix as a planning artifact before implementation tasks are scheduled.

# Do Not Use When

Do not use this capability to: enumerate every possible combinatorial permutation of inputs (it is not exhaustive mutation testing — focus on distinct risk categories); substitute for `acceptance-standard-definition` (scenario decomposition maps coverage, acceptance standards define done signals); replace threat modeling for adversarial scenarios (abuse scenarios identified here should be handed off to `threat-modeling` for depth analysis); or expand scope beyond the approved requirement (non-goals in the requirement brief bound the scenario space).

# Non-Negotiable Rules

- **Scenario categories are not optional.** Every scenario matrix must contain at minimum: (1) Normal / happy path; (2) Alternate valid path (valid input, different branch — e.g., admin vs. regular user, different payment method); (3) Edge condition (boundary values, empty collections, first/last record, maximum limit, zero-balance); (4) Failure / fault scenario (dependency timeout, validation rejection, permission denied, concurrency conflict, partial write); (5) Abuse / misuse scenario (intentional invalid input, replay, enumeration, rate-limit probing — not just accidental wrong input); (6) Recovery scenario (retry, idempotent re-submission, undo, rollback, compensating action); (7) Operational scenario (support diagnosis, monitoring trigger, manual correction, backfill, rollback, incident response visibility).
- **Every scenario must name all five fields:** (1) Actor — who or what initiates; (2) Precondition — system state before the scenario begins; (3) Stimulus — the specific input or event; (4) Expected outcome — the observable result (response, state change, emitted event, error code); (5) Verification method — unit test, integration test, contract test, E2E test, audit log check, monitoring alert, manual procedure. A scenario without a verification method is not implementable as a done criterion.
- **Failure scenarios must include all relevant fault types for the workflow.** At minimum evaluate: external dependency timeout, external dependency returning unexpected schema, validation rejection at each input boundary, permission denied at each authorization check, concurrency conflict (two actors modifying the same resource simultaneously), partial write (write to store A succeeded, write to store B failed), retry exhaustion (all retries consumed before success), downstream contract rejection (external system rejects the message format).
- **Release criticality must be classified for every scenario.** Classification: MUST-HANDLE (unhandled scenario blocks release — data loss, security, financial impact), SHOULD-HANDLE (unhandled scenario degrades quality but does not block release — with documented risk acceptance), DEFERRED (explicitly out of scope, named owner and follow-up). An unmarked scenario is not a planning artifact — it is ambiguity.
- **Abuse scenarios are intentional misuse, not just invalid input.** An invalid email address in a form field is an edge condition. A bot submitting 10,000 invalid email addresses per second to enumerate valid accounts is an abuse scenario. The distinction matters: edge conditions are handled by validation; abuse scenarios require rate limiting, CAPTCHA, account lockout, or monitoring alerts. Confusing the two leads to validation-only defenses against adversarial behavior.
- **Non-goals from the requirement brief bound the scenario space.** A non-goal of "Does NOT handle subscription cancellation" means no scenario for subscription cancellation should appear in this matrix. If a scenario appears to be required but is listed as a non-goal, escalate to the requirement owner before including it.

# Industry Benchmarks

Anchor against: **ISTQB Test Design Techniques** — equivalence partitioning (group inputs with same expected behavior), boundary value analysis (test at and near boundaries), decision table testing (all input combinations for multi-condition logic), state transition testing (every state and transition in a state machine). **BDD / Gherkin** (Cucumber, SpecFlow) — Given/When/Then format maps directly to precondition/stimulus/expected outcome; scenario outlines for parametric coverage. **OWASP Testing Guide (WSTG)** — misuse and abuse scenarios for authentication, authorization, input validation, session management. **Google Site Reliability Engineering** — operational scenarios including toil identification, runbook coverage, alert firing, and rollback verification. **DORA Research** — change failure rate is reduced when pre-deployment scenario coverage explicitly includes rollback and recovery paths. **IEEE Std 829 (Software Test Documentation)** — test design specification; traceability from requirement to test case. **Chaos Engineering principles (Chaos Monkey, Gremlin)** — fault injection scenarios: dependency failure, resource exhaustion, clock skew, network partition. **Martin Fowler — Feature Envy / Shotgun Surgery smells** — when scenario decomposition reveals that a single change requires modifications to many unrelated modules, escalate as an architecture smell.

### Scenario Category Classification Matrix

| Category | Example Trigger | Failure Risk if Omitted | Verification Method |
| --- | --- | --- | --- |
| Normal path | User submits valid form | None (but needed as regression baseline) | Integration test |
| Alternate valid path | Admin vs. regular user; empty cart vs. full cart | Wrong behavior for a valid user class discovered in production | Integration test per path |
| Edge condition | Empty collection, max-length input, zero-balance, first/last record | Off-by-one; empty state display broken; truncation | Unit + integration test |
| Failure / fault | Dependency timeout; partial write; concurrency conflict | Silent data loss; inconsistent state; user confusion | Integration test; chaos/fault injection |
| Abuse / misuse | Replay attack; account enumeration; mass assignment | Security vulnerability; account takeover; data leak | Security test; penetration test |
| Recovery | Retry after timeout; idempotent resubmission; rollback trigger | Duplicate records; double-charge; stuck workflow | Integration test; idempotency test |
| Operational | Support diagnosis query; backfill trigger; rollback procedure | Unobservable production failure; no runbook; untriggerable alert | Runbook exercise; monitoring test |

### Scenario Record Template

```
Scenario: [Unique ID — e.g., SC-042]
Category: [Normal | Alternate | Edge | Failure | Abuse | Recovery | Operational]
Actor: [authenticated customer | admin | scheduler | external webhook | support operator]
Precondition: [System state before scenario — e.g., "User has pending order; payment service is degraded"]
Stimulus: [Specific input/event — e.g., "User submits cancel request for order ID abc-123"]
Expected Outcome:
  - Response/output: [e.g., HTTP 503 with error code PAYMENT_SERVICE_UNAVAILABLE]
  - State change: [e.g., Order status unchanged; cancellation deferred to retry queue]
  - Emitted event: [e.g., order.cancellation.deferred event on cancellation-events topic]
  - Side effects: [e.g., No refund initiated; user notified via email within 5 min]
Verification Method: [Integration test: OrderCancellationTest#paymentServiceDegraded]
Release Criticality: [MUST-HANDLE | SHOULD-HANDLE | DEFERRED]
Notes: [Idempotent? Compensation needed? Rollback path?]
```

# Selection Rules

Select this capability when **a requirement needs path coverage across behavior categories before planning and implementation begin**. Route elsewhere when: `use-case-modeling` is primary (a single actor goal needs detailed flow design with decision points); `acceptance-standard-definition` is primary (done criteria need to be sharpened for already-identified scenarios); `threat-modeling` is primary (abuse scenarios identified here need depth analysis for adversarial path mapping); `interaction-state-modeling` is primary (UI states and transitions need decomposition independent of backend scenarios).

# Risk Escalation Rules

Escalate when: any scenario exposes an irreversible side effect without a defined rollback or compensation path (MUST-HANDLE by default); an abuse scenario indicates that the feature can be weaponized against other users (rate limiting, enumeration, SSRF — escalate to `security-privacy-gate`); a failure scenario reveals that partial writes can occur across multiple data stores without a compensating transaction (escalate to `data-model-design` and `idempotency-retry-design`); a recovery scenario requires manual operator intervention with no runbook (escalate to `reliability-observability-gate`); or the operational scenario matrix is entirely empty for a workflow that can fail after initiating external side effects.

# Critical Details

- **The operational scenario category is consistently the most omitted.** Teams focus on happy path, alternate paths, and edge conditions during development — and discover operational scenarios (how do I diagnose this in production? how do I backfill records that were missed during the outage? how do I trigger a rollback for just this tenant?) only after a production incident. Writing operational scenarios before implementation forces runbook and observability planning while the engineer who built the feature is still available.
- **Recovery scenarios expose idempotency requirements.** If a retry of the same stimulus must produce the same outcome as the first attempt (idempotent behavior), that is a design constraint that must be identified in the scenario matrix and handed to `idempotency-retry-design` before implementation. If recovery scenarios reveal that the workflow is not idempotent and cannot be made idempotent, that is a MUST-HANDLE architectural constraint.
- **Abuse scenarios are not the same as validation edge cases.** A 10,001-character string in a name field is an edge condition: the correct response is a 400 validation error. A bot systematically submitting 10,001-character strings against every text field to probe for injection vulnerabilities is an abuse scenario: the correct response involves rate limiting, IP banning, WAF rules, and anomaly detection — not just input validation.
- **Scenario decomposition is the boundary check for the requirement brief.** If decomposition produces scenarios that conflict with non-goals in the brief, or requires behavior not described in the desired behavior, the brief has an unresolved scope question. Stop decomposition and escalate to `requirement-clarification`.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Scenario matrix contains only happy path and "invalid input" | Edge, failure, abuse, recovery, and operational categories entirely absent; production discovers them | Apply all 7 category rows; each category must have at least one scenario |
| "Retry on failure" listed without idempotency spec | Retry produces duplicates: double charge, duplicate record, duplicate notification | Identify idempotency requirement; hand off to idempotency-retry-design before implementation |
| Abuse scenario: "user submits invalid data" | Describes validation edge case, not intentional misuse | Abuse scenario: "attacker submits crafted input to enumerate valid account IDs via timing difference" |
| Recovery scenario: "ask engineering" | No runbook; no observable state; unsupported in production | Operational scenario: "support queries order_cancellation_audit table with operator SQL procedure" |
| Release criticality unmarked | Planning cannot prioritize; developer ships without knowing which gaps are blockers | Every scenario must have MUST-HANDLE / SHOULD-HANDLE / DEFERRED |
| Non-goal scope ignored; subscription scenario added | Scope creep; stakeholder dispute; unplanned work in sprint | Reject scenario; escalate if the behavior is actually needed |

# Failure Modes

- Happy-path-only implementation: 6 of 7 scenario categories absent from matrix; failure and abuse scenarios discovered in production.
- Retry implemented without idempotency check: 2,000 duplicate charges in production; rollback requires manual data correction.
- Operational scenarios omitted: production incident has no runbook; 4-hour MTTR instead of 30 minutes.
- Abuse scenario classified as edge condition: account enumeration via response timing is "handled" by input validation — timing side channel remains.
- Recovery scenario requires rollback that was never designed: partial write leaves data in inconsistent state; no compensation transaction defined.
- Scenario with irreversible side effect (email sent) classified as DEFERRED: user receives email during incident; emails cannot be unsent.

# Output Contract

Return a scenario matrix with per scenario:

- `scenario_id` (unique identifier)
- `category` (Normal / Alternate / Edge / Failure / Abuse / Recovery / Operational)
- `actor` (who or what initiates)
- `precondition` (system state before)
- `stimulus` (specific input or event)
- `expected_outcome` (response, state change, emitted event, side effects)
- `verification_method` (test type and test ID/description)
- `release_criticality` (MUST-HANDLE / SHOULD-HANDLE / DEFERRED)
- `design_handoff` (which capability needs to receive this scenario for depth design)

# Quality Gate

The scenario matrix is complete only when:

1. All 7 scenario categories are represented with at least one scenario each.
2. Every scenario has all 5 fields: actor, precondition, stimulus, expected outcome, verification method.
3. Every scenario has a release criticality classification.
4. All failure scenarios cover dependency timeout, permission denied, concurrency conflict, and partial write (where applicable).
5. Abuse scenarios are intentional misuse — not just validation edge cases.
6. Recovery scenarios identify idempotency requirements.
7. Operational scenarios cover diagnosis, backfill, rollback, and alert triggering.
8. Non-goals from the requirement brief are not violated by any scenario.
9. MUST-HANDLE scenarios that lack implementation plans are escalated before sprint planning.
10. Design handoff targets are named for scenarios requiring depth analysis.

# Used By

- change-intake-compiler
- acceptance-criteria-builder

# Handoff

Hand off to `acceptance-standard-definition` for done criteria per scenario; `quality-test-gate` for test selection and coverage planning; `reliability-observability-gate` for recovery and operational scenario gaps; `idempotency-retry-design` for recovery scenarios with retry requirements; `threat-modeling` for abuse scenarios requiring depth adversarial analysis.

# Completion Criteria

The capability is complete when **the scenario matrix covers all 7 categories with classified release criticality, every scenario is verifiable, happy-path-only implementation is structurally prevented, and all design handoff targets for MUST-HANDLE scenarios are named before implementation planning begins**.
