---
name: acceptance-criteria-builder
description: Builds professional, verifiable acceptance criteria for product and code changes, including happy paths, negative paths, edge cases, permission cases, regression cases, and product-level verification evidence.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Acceptance Criteria Builder

## Mission
Transform ambiguous change intent into a complete, testable, behaviorally precise set of acceptance criteria — covering every actor, trigger, state, edge case, error path, and non-functional requirement — so that implementation, review, and verification share a single unambiguous contract with no hidden assumptions.

## When To Use
- A change request, user story, bug fix, or task needs explicit acceptance conditions before design or coding begins.
- Existing criteria only describe happy paths and lack edge cases, error states, or non-functional thresholds.
- A release gate, quality gate, security review, or architecture review requires documented behavioral scope.
- Disputed or ambiguous requirements need decomposition into independently verifiable criteria.
- Cross-team handoffs require a behavioral contract rather than prose intent.
- A product experiment, A/B test, analytics instrumentation, or metric-driven rollout needs decision criteria, guardrails, and rejection conditions.

## Do Not Use When
- Acceptance conditions are already written, verifiable, and formally accepted by all responsible stakeholders.
- The change is a purely internal refactor with zero behavioral impact on users, operators, or dependents.
- The request is exploratory research or spike work with no deliverable behavioral outcome.

## Non-Negotiable Rules
- Every criterion must be independently verifiable — no cluster criteria that bundle unrelated behaviors.
- Cover happy path, all named edge cases, error states, constraint violations, and non-functional requirements as first-class criteria, not footnotes.
- Never embed implementation details (class names, SQL queries, algorithm choices) — specify **what** must be true, not **how** it is achieved.
- Rejection conditions and partial-success states belong in the criteria set, not in comments.
- Actors must be explicit — every criterion names who initiates the action or who is affected.
- Preconditions and postconditions are mandatory for stateful behaviors.
- Non-functional criteria (latency, availability, throughput, accessibility, compliance) must have measurable thresholds, not vague adjectives like "fast" or "accessible."
- Experiment criteria must define primary metric, guardrail metrics, exposure event, assignment unit, decision threshold, and rollback/rejection criteria before launch.
- Each criterion must reference a verification method: automated test type, structured manual step, or audit log review.
- Never invent requirements to fill gaps — open questions must be surfaced as explicit placeholders.
- Criteria must remain stable during implementation; scope changes require explicit revision and re-acceptance.

## Industry Benchmarks
- **BDD / Gherkin (Cucumber, Behave, SpecFlow)**: `Given / When / Then` pattern — actor-based, observable behavioral language. The industry standard for behavioral specification.
- **IEEE 830 / ISO/IEC 29148**: Software requirements specification quality attributes — completeness, consistency, verifiability, traceability, unambiguity.
- **INVEST Principle**: Each criterion should be Independent, Negotiable, Valuable, Estimable, Small, and Testable.
- **SMART Non-Functional Criteria**: Specific, Measurable, Achievable, Relevant, Time-bound — applied to latency, throughput, and availability thresholds.
- **WCAG 2.1 AA**: Accessibility acceptance criteria for user-interface changes reference specific WCAG success criteria numbers.
- **OWASP ASVS Level 2**: Security-relevant behaviors require verifiable acceptance criteria with explicit denial paths and audit events.
- **Risk-Based Testing (ISO/IEC/IEEE 29119)**: Prioritize criteria by failure impact and likelihood — high-risk behaviors require explicit negative criteria.

### Selection Matrix: Criterion Format by Behavior Type

| Behavior Type | Preferred Format | Required Additions |
|---|---|---|
| User workflow | Given/When/Then | Actor, precondition, postcondition |
| API contract | Request/Response pair | Status codes, schema, error codes |
| Business rule | Rule statement + boundary table | Boundary values, NULL, overflow |
| Performance | Measurable threshold | Percentile, load level, environment |
| Security / Authorization | Access control matrix row | Denied case, audit event |
| Accessibility | WCAG checkpoint reference | Assistive technology test steps |
| Data migration | Before/After state | Rollback condition |
| Background/async | Expected eventual state | Max latency before failure |
| Experiment / A/B test | Metric contract + rejection rule | Primary metric, guardrails, exposure event, assignment unit |

## Technical Selection Criteria
Assess every criterion candidate against:
- **Behavioral precision**: Is the expected outcome unambiguous and observer-independent?
- **Edge case coverage**: Are boundary values, zero/null/empty, concurrent actor, and overflow cases represented?
- **Error state coverage**: Are error codes, fallback behaviors, and user-visible error messages specified?
- **Non-functional requirements**: Are latency, availability, security, accessibility, and compliance thresholds measurable?
- **Testability**: Can a test be written today without additional specification?
- **Actor clarity**: Is the initiating role or system explicit and unambiguous?
- **Traceability**: Does each criterion map to a requirement, issue ID, or stakeholder decision?
- **Independence**: Can the criterion be verified in isolation?
- **Experiment validity**: Does the criterion specify exposure logging, assignment stability, sample ratio mismatch rejection, primary metric threshold, and guardrail rollback?

## Experiment Acceptance Criteria

Experiment criteria must be written before implementation or launch:

- **Experiment acceptance criteria**: Given assignment eligibility, when a user is exposed, then assignment, experience variant, and exposure event are recorded consistently.
- **Metric threshold**: Primary metric, expected direction, minimum detectable effect or practical threshold, decision window, and owner.
- **Guardrail failure rejection criteria**: latency, error rate, revenue, retention, accessibility, safety, support, or data-quality regression thresholds that reject rollout even if the primary metric improves.
- **Exposure event**: event name, schema, de-duplication rule, compatibility with existing taxonomy, and verification query.
- **Assignment unit**: user/account/tenant/device/session and stability requirement across devices and sessions.
- **Sample ratio mismatch**: rejection threshold and investigation owner when observed allocation differs from planned allocation.

### Decision Tree: What Depth Is Required?

```
Is behavior user-facing or contract-affecting?
├── Yes → Full Given/When/Then + error state + accessibility criterion
└── No → Is behavior stateful or data-mutating?
    ├── Yes → Precondition + postcondition + rollback condition
    └── No → Is there a performance, security, or compliance risk?
        ├── Yes → Measurable threshold + verification method
        └── No → Minimal behavioral statement is sufficient
```

## Risk Escalation Rules
- Escalate when criteria require PII-bearing data or production-only conditions that cannot be replicated in test.
- Escalate when criteria involve regulatory compliance (GDPR, SOC 2, PCI-DSS, HIPAA) and need compliance team acceptance.
- Escalate when criteria are disputed between stakeholders — do not resolve disputes silently.
- Escalate when a non-functional threshold requires load testing, benchmarking, or external security assessment.
- Escalate when proposed criteria conflict with another active change to the same contract or system boundary.
- Escalate when an experiment has no primary metric, no guardrails, no exposure event, unstable assignment unit, or no rule for sample ratio mismatch.

## Critical Details
- Gherkin structure requires **Given** (precondition), **When** (action/event), **Then** (observable outcome), **And/But** (extensions) — all four elements when the behavior is stateful.
- Always write the **rejection criterion** alongside each acceptance criterion — define what observable failure looks like, not just success.
- Boundary value analysis: for every numeric or date range, write criteria at the minimum, maximum, just-inside, and just-outside values.
- For async or eventually-consistent behaviors, specify the maximum allowable wait time before the criterion is considered failed.
- Accessibility criteria must reference WCAG success criteria numbers (e.g., WCAG 2.1 SC 1.4.3 Contrast Minimum) and name the assistive technology test.
- Performance criteria must name the measurement percentile and load level (e.g., p99 < 500 ms at 1,000 RPS sustained for 60 s).
- Multi-step flows require a criterion per step plus an end-to-end flow criterion — do not collapse steps.
- Empty, loading, error, and disabled UI states each require their own criterion when the displayed behavior changes.
- For data changes: specify the exact Before state and expected After state in the criterion body.
- Permission boundary: every sensitive operation needs both an authorized path criterion and an unauthorized path criterion.

### Anti-Examples

| Bad Criterion | Problem | Corrected Form |
|---|---|---|
| "The login button works correctly" | Vague, untestable | "Given valid credentials, When submitted, Then a session token is issued and the user is redirected to /dashboard within 2 s" |
| "System is fast" | No threshold or context | "p99 response time < 300 ms at 500 concurrent users over 60 s sustained load" |
| "Only admins can access" | No denial path specified | "Given a non-admin token, When GET /admin/users is called, Then 403 Forbidden with error code AUTH_INSUFFICIENT_ROLE is returned" |
| "Handles errors gracefully" | No observable behavior defined | "When upstream returns 503, Then UI shows 'Service unavailable, try again in a moment' and logs ERROR with correlation trace ID" |
| "Uses Redis for caching" | Implementation detail, not behavior | "Subsequent reads of the same resource within the TTL window respond within 50 ms" |

## Failure Modes
- **Vague language defers disputes**: Terms like "correctly", "smoothly", "appropriately" mean different things to different reviewers — disputes surface at release.
- **Implementation coupling**: Criteria referencing class names, SQL, or cache keys break with every refactor and obscure intent.
- **Missing error states**: Features ship that only work on the happy path; errors produce broken or confusing user experiences.
- **Missing edge cases**: Boundary conditions cause production incidents — null input crashes, empty states display garbage, large inputs break.
- **Non-functional omission**: Performance, accessibility, and security criteria are absent — features pass QA then fail in production or in compliance audits.
- **Unstated actors**: Criteria without a named initiating role can be "satisfied" by the wrong user type.
- **No rejection criterion**: QA passes partial implementations because no one specified what observable failure looks like.
- **Silent resolution of open questions**: Open questions are quietly resolved by the implementer, creating hidden scope decisions that accumulate as technical debt.
- **Untraceable criteria**: Review cannot determine which requirement each criterion satisfies; traceability gaps fail change management audits.
- **Collapsed multi-step criteria**: One criterion tests multiple behaviors — partial failure has no isolated root cause and blocks diagnosis.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a structured acceptance criteria document with:
- **Criteria set**: Each criterion assigned an ID, actor, precondition, action, expected outcome, and verification method (unit / integration / E2E / manual / audit).
- **Rejection criteria**: Observable failure condition for each behavioral criterion.
- **Non-functional criteria table**: Latency, availability, accessibility, security — each with measurable threshold and test reference.
- **Experiment criteria**: Primary metric, guardrail metrics, exposure event, assignment unit, sample ratio mismatch rule, decision memo owner, and rollback/rejection threshold.
- **Open questions list**: Unanswered scope questions that block finalization, with proposed owner and deadline.
- **Traceability map**: Each criterion ID → source requirement ID or change request section.
- **Coverage summary**: Happy path, edge cases, error states, non-functional — confirmed covered or explicitly deferred with rationale.

## Quality Gate
1. Every criterion has a named actor, precondition, action, and observable expected outcome.
2. Every criterion has a defined verification method — no criterion left as "TBD."
3. Error states are represented: at minimum — invalid input, upstream failure, unauthorized access.
4. At least one performance threshold exists for every user-facing or high-volume path.
5. Accessibility criteria exist for every UI-affecting change, with WCAG reference numbers.
6. No criterion embeds an implementation detail.
7. All boundary values have explicit criteria at minimum, maximum, just-inside, and just-outside.
8. Rejection criteria exist for every behavioral criterion.
9. Open questions are listed — none resolved silently by the criteria author.
10. Criteria have been formally reviewed and accepted by the responsible stakeholder.
11. Experiment criteria include primary metric, guardrails, exposure event, assignment unit, decision threshold, and rejection criteria.

## Handoff
- **task-dag-planner** — to sequence implementation tasks against the accepted criteria set.
- **quality-test-gate** — to map criteria to test obligations, coverage types, and evidence.
- **security-privacy-gate** — when security or privacy acceptance criteria require threat model review.
- **experience-impact-modeler** — when accessibility or UX state coverage needs validation.
- **bigdata-product-extension** — when experiment criteria depend on analytics event taxonomy, funnel/cohort definitions, dashboard migration, or warehouse data quality.
- **architecture-impact-reviewer** — when criteria reveal contract or boundary changes not yet architecturally reviewed.

## Completion Criteria
The change has a complete, formally accepted acceptance criteria set where every criterion is independently testable, every actor is explicit, every error state is covered, all non-functional thresholds are measurable, no open question is silently resolved, rejection criteria exist for every behavioral criterion, and the set has been accepted by the responsible stakeholders before implementation begins.
