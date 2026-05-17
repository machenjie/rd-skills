---
name: acceptance-standard-definition
description: Defines verifiable completion standards and rejects vague acceptance language that cannot be tested, reviewed, or observed.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "05"
changeforge_version: 0.1.0
---

# Mission

Convert desired behavior into objective done standards that can be proven by tests, review evidence, observability signals, or named-stakeholder acceptance — and reject any criterion that cannot be falsified by evidence.

# When To Use

Use this capability when acceptance criteria are missing, subjective, too broad, unverifiable, expressed as quality adjectives ("works well", "better UX", "fast", "secure", "robust", "intuitive"), or when "done" is owned by no one. Also use when a change touches regulated behavior (payments, PII, accessibility, safety) where evidence is mandatory regardless of stakeholder preference.

# Do Not Use When

Do not use this capability to approve implementation scope, invent product requirements, redesign the feature, or replace specialist review for security, privacy, legal, performance, or accessibility obligations. Do not use it to author test cases — it authors the *standard* the tests must satisfy.

# Non-Negotiable Rules

- Reject vague criteria unless translated into observable outcomes with an evidence type.
- Every acceptance standard must name **condition (Given) · action (When) · expected result (Then) · evidence**.
- Include negative, permission-denied, error, regression, and operational-recovery criteria proportional to risk.
- Define who can accept subjective product judgment if objective evidence is insufficient, and require their sign-off in writing.
- Do not mark a criterion complete without a verification artifact (test id, log query, screenshot, signed approval, metric link).
- Non-functional claims (performance, security, accessibility, reliability) must reference a measured threshold, a named control, or a recognized standard — never a qualitative adjective alone.
- Every criterion must trace to a scenario id or requirement id; orphan criteria are rejected.

# Industry Benchmarks

Anchor standards in: ISO/IEC/IEEE 29148 (requirements engineering, testable requirements), behavior-driven acceptance (Gherkin Given/When/Then), Definition of Done (Scrum Guide), INVEST criteria for user stories, ATDD/Specification-by-Example (Adzic), Consumer-Driven Contracts (Pact), WCAG 2.2 AA conformance for accessibility, Google SRE SLI/SLO discipline for reliability NFRs, OWASP ASVS Level 1+ for security acceptance, ISO/IEC 25010 quality model (functional suitability, reliability, performance efficiency, usability, security, compatibility, maintainability, portability), and release evidence / audit-trail practices (SOX, SOC 2, FDA 21 CFR 11 where regulated).

### Evidence-Type Selection Matrix

| Claim type | Required evidence | Standard reference |
| --- | --- | --- |
| Functional behavior | Automated test (unit/integration/E2E) with assertion on observable output | ISO/IEC/IEEE 29119 |
| Latency / throughput | k6/JMeter/Gatling report against named percentile (p50/p95/p99) and load profile | Google SRE Workbook |
| Availability | SLO burn-rate alert + 28-day error budget snapshot | Google SRE |
| Accessibility | axe-core / Lighthouse + manual keyboard + screen-reader transcript | WCAG 2.2 AA |
| Security control | OWASP ASVS test id + scanner report + manual verification when ASVS L2+ | OWASP ASVS |
| Privacy | DPIA reference + data-flow diagram + retention-test query | GDPR Art. 35 |
| Visual / UX subjective | Named approver sign-off + design-system token diff + recorded review | Nielsen heuristics |
| Data migration | Pre/post row counts, checksum, sample diff, rollback rehearsal log | DAMA-DMBOK |
| Money / inventory | Double-entry reconciliation + idempotency test + audit log query | accounting standards |

# Selection Rules

Select this capability when the key gap is **proving completion**. Adjacent routing:

- Prefer `scenario-decomposition` when behavior paths themselves are incomplete (criteria cannot exist before scenarios do).
- Prefer `requirement-structuring` when the request is not yet organized into goals, constraints, deliverables.
- Prefer `non-goal-boundary-definition` when the gap is *what is excluded*, not *how to prove inclusion*.
- Prefer `test-strategy` when the question is *which test layers and tools*, not *what counts as done*.
- Prefer `performance-budgeting` when the missing piece is a defensible numeric threshold.
- Use **with** `quality-test-gate` (this capability sets the bar; the gate enforces it).

# Risk Escalation Rules

Escalate when acceptance depends on: unresolved performance/availability metrics, regulated claims (payment, medical, safety, financial reporting), security controls without an owner, customer-contractual SLAs, data-migration validation that cannot be rehearsed in production-like data, external partner contracts, irreversible side effects (mass email, billing, deletes), or manual subjective judgment with no accountable approver. Escalate to product owner for scope conflicts, to architecture for cross-system criteria, to security/privacy gate for regulated controls, to SRE for reliability thresholds.

# Critical Details

A strong standard can fail. That is the test. If a criterion cannot describe a state of the world in which it would be considered **not met**, it is not a standard — it is a wish. Apply these refinements:

- **Tolerance and units.** "Fast" → "p95 server response ≤ 300 ms at 200 RPS sustained 10 min on production-like data". "Available" → "99.9% monthly success ratio across the named SLI, measured at the load balancer".
- **Scope qualifier.** Name the scenario, dataset size, browser/device matrix, tenant tier, network condition, and concurrency under which the result must hold. Numbers without scope are unverifiable.
- **Falsifiability.** Each criterion must have an explicit *unacceptable result* alongside the expected result. A criterion that only describes success masks regression risk.
- **Evidence locality.** Evidence must be reproducible by a reviewer without privileged access to the author's machine. Cite test ids, dashboards, run logs, or commit SHAs.
- **Permission and negative paths.** For every authenticated action, define the denied-actor, missing-scope, expired-token, and tenant-isolation criteria.
- **Operational acceptance.** For any production change: rollback criterion, on-call runbook update, dashboard update, alert update, log/metric emission. A feature is not "done" if operating it on a Saturday at 02:00 is undefined.
- **Subjectivity ledger.** Where subjective judgment is unavoidable (visual polish, copy tone), record the *single named approver*, the review artifact, and the decision date. Avoid committee acceptance.
- **Regression criteria.** Name the existing scenarios that must continue to pass. Silence on regression is a defect of the standard, not the implementation.
- **Tolerance for flake.** For non-deterministic systems, define statistical thresholds (e.g., "≥ 99% of 1000 runs"), not a single pass.

### Vague → Verifiable Rewrite Examples

| Vague (reject) | Verifiable (accept) |
| --- | --- |
| "Page loads fast" | "LCP ≤ 2.5 s at p75 on simulated Slow 4G + mid-tier mobile, measured by Lighthouse CI on the staging URL" |
| "Login is secure" | "Meets OWASP ASVS v4 §2.1, §2.2, §3.2, §3.3; brute-force test triggers lockout after 5 failures within 5 min; verified by test id `AUTH-SEC-014`" |
| "Better UX" | "Task completion rate for `create-order` rises from 78% to ≥ 88% on 30 moderated sessions; SUS score ≥ 75; approved by design lead `@name`" |
| "No regressions" | "All scenarios tagged `@checkout` and `@billing` continue to pass in CI run `release-candidate`" |
| "Handle errors gracefully" | "On 5xx from `POST /orders`, UI shows error toast `ORDER_CREATE_FAILED`, preserves form input, logs `correlation_id`, emits `order.create.error` metric; verified by test id `FE-ORD-022`" |

# Failure Modes

- Criteria restate the requirement ("the user can log in") without defining evidence or boundary conditions.
- Acceptance covers the success path but not denials, validation failures, partial outages, or regressions.
- A manual reviewer is named without decision authority, checklist, or a deadline — acceptance stalls.
- Non-functional claims ("fast", "secure", "scalable") have no metric, threshold, or named control.
- Criteria are implementation-prescriptive ("use Redis cache") instead of behavior-prescriptive, blocking valid alternative designs.
- "Tested" is treated as evidence — without the test id and assertion it is unverifiable.
- Subjective sign-off is delegated to a group, producing diffusion of responsibility and indefinite acceptance.
- Operational acceptance (alerts, dashboards, runbooks, rollback) is omitted, treating production as someone else's problem.
- Regression scope is undefined, so any later defect is contested as "out of scope".
- Performance criteria omit load profile, dataset size, or percentile — making the number meaningless.

# Output Contract

Return an acceptance standard set where each criterion contains:

- `criterion_id` (stable, traceable)
- `trace` → scenario id and/or requirement id
- `given` (precondition / system + data state)
- `when` (trigger action with actor and inputs)
- `then` (expected observable result with tolerance and units)
- `not_then` (explicit unacceptable result)
- `evidence_type` (test id, dashboard, log query, signed review, scanner report)
- `evidence_owner` (named individual or rotation)
- `accepter` (who can mark this met when subjective)
- `release_blocking` (yes/no with justification)
- `regression_scope` (named scenarios/tags that must continue to pass)
- `applicable_scope` (env, dataset, load, browser/device, tenant tier)

Group criteria by: functional, negative/permission, error/recovery, NFR (performance, reliability, security, privacy, accessibility), operational (rollback, observability, runbook), regression.

# Quality Gate

The standards are complete only when:

1. Every criterion is independently verifiable by a reviewer without insider context.
2. Every vague phrase has been replaced with a measurable threshold or explicitly recorded as rejected.
3. Every non-functional claim cites a benchmark or numeric threshold with scope.
4. Negative, permission, error, and operational criteria exist proportional to risk.
5. Every criterion has a named owner and a release-blocking decision.
6. Regression scope is named, not implied.

If any of (1)–(6) fail, return the standard set as `incomplete` with the specific gap; do not pass partial standards downstream.

# Used By

- acceptance-criteria-builder
- quality-test-gate

# Handoff

Hand off to `quality-test-gate` for test strategy and execution evidence; `experience-impact-modeler` for UX acceptance evidence and approver assignment; `security-privacy-gate` for regulated security/privacy acceptance; `reliability-observability-gate` for SLO/SLI/alert acceptance; `performance-budgeting` when thresholds need defensible numbers; `delivery-release-gate` when acceptance must gate rollout/rollback.

# Completion Criteria

The capability is complete when "done" is measurable, reviewable, traceable, and falsifiable — and when a reviewer who has never met the author can determine, from artifacts alone, whether each criterion is met, not met, or pending. Subjective impressions are eliminated or explicitly delegated to a named approver with a recorded decision.
