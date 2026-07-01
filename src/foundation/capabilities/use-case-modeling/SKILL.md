---
name: use-case-modeling
description: Models actor-goal use cases with source-confirmed preconditions, triggers, paths, guarantees, postconditions, acceptance trace, graph/memory/execution evidence, validation handoff, and boundary rules for product-domain behavior.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "15"
changeforge_version: 0.1.0
---

# Mission

**Define actor-centered use cases that capture the behavioral guarantees a system makes to its actors** — specifying preconditions, triggers, main paths, alternate paths, failure paths, and postconditions with enough precision that acceptance criteria can be derived directly from the use case, implementation decisions can be validated against actor goals, and downstream capabilities (state machine modeling, API contract design, test scenario decomposition) have an unambiguous behavioral specification to work from.

# When To Use

Use this capability when: a change introduces a new user-facing or system-to-system interaction that has not been formally defined; a change extends an existing interaction by adding new actors, new alternate paths, new failure paths, or new postconditions; a business stakeholder has described a feature at the goal level ("users should be able to subscribe to a plan") and the interaction design must bridge from goal to behavioral specification; a change affects authorization logic, external integrations, or irreversible side effects that require explicit precondition and postcondition documentation; or acceptance criteria are being written and the underlying use case structure is needed to ensure complete coverage.

# Do Not Use When

Do not use this capability for: low-level code execution sequences (method A calls method B calls method C — this is a sequence diagram, not a use case); minor UI interactions that are entirely contained within a single screen and have no domain side effect (hover tooltip, accordion expand — use `interaction-state-modeling`); when the complete behavioral design is already captured in acceptance criteria and the use case would be a verbatim restatement.

# Stage Fit

Owns product-domain behavior-contract discovery before acceptance criteria, implementation placement, state-machine design, API contract design, and test scenario decomposition. During code-review, testing, and release handoff, it checks whether a diff changed an actor goal, entry gate, trigger, path, external actor, durable outcome, side effect, or recovery promise without updating the use case and acceptance trace. Repository search, graph, project memory, and execution trajectory can locate existing behavior, but current source, tests, docs, or registry evidence must confirm the use case before the output treats it as authoritative.

# Non-Negotiable Rules

- **Name exactly one primary actor and one goal per use case.** A use case with two actors and two goals is two use cases. The primary actor is the one whose goal drives the interaction — the one whose goal is satisfied or frustrated at the end. System actors (external services, scheduled jobs, webhooks) are valid primary actors. "The user" is not a precise actor name — the actor must be named by role: "Customer," "Support Agent," "Payment Webhook," "Scheduled Report Job."
- **Define preconditions that must be true before the use case can begin.** Preconditions are not aspirational — they are enforced entry gates. If the precondition is violated, the use case does not begin and the actor is routed to an error or prerequisite fulfillment path. Examples: "User is authenticated and has verified email address"; "Subscription plan exists and is active"; "Invoice has status UNPAID and is not past the 90-day dispute window." Missing preconditions produce invalid entry paths where the system receives a request it is not designed to handle.
- **Define postconditions as durable state changes, emitted events, or externally observable outcomes — not as UI messages.** "The user sees a success message" is a UI implementation detail, not a postcondition. Postconditions must express what remains true in the system after the use case completes: "A subscription record exists in ACTIVE state for the customer and plan"; "A payment_succeeded event is published to the billing topic"; "The inventory count for product X is decremented by the ordered quantity." These postconditions are directly testable and drive acceptance criteria.
- **Every alternate path must resolve to a defined outcome — either achieving the primary actor's goal through a different path, or explicitly exiting with a named error state.** An alternate path that ends with "the user sees an error" is incomplete — it must specify: what state the system is left in, what data is preserved, whether the actor can retry, and what the recovery path is. Unspecified alternate path outcomes become the source of "the system is in an unexpected state" production incidents.
- **External systems that trigger behavior must be modeled as actors.** A payment webhook that triggers an order confirmation is an actor. A scheduled job that expires stale sessions is an actor. A CI/CD pipeline that triggers a deployment is an actor. Treating all triggers as implicit background behavior hides the trust boundary (does the payment webhook require authentication?), the precondition (must the order exist in PENDING state?), and the failure path (what if the webhook delivers duplicate events?).
- **Business rules referenced in the main path or alternate paths must be named and linked.** A use case that says "the system validates the order" is incomplete — it must name which business rules govern the validation: "validate per OrderValidationRule-001 (minimum order value $10), StockAvailabilityRule-003 (all items in stock), FraudCheckRule-007 (order score < 80)." This linkage enables traceability from use case to business rule to unit test.
- **Guarantee level must be explicit.** State the minimal guarantee when the actor goal is not achieved, the success guarantee when it is achieved, and the owner of any recovery path. A use case without guarantees is only a story outline.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New actor-goal contract | Feature or requirement names an actor goal but not the behavior contract. | Turn goal language into one actor, one trigger, enforced entry gates, paths, and durable guarantees. | Actor/goal boundary, scope, preconditions, trigger, main and alternate paths, success and minimal guarantees. | `requirement-structuring`, `acceptance-standard-definition` | UI navigation or component states until the behavior contract is stable. |
| Existing behavior extension | A change adds an alternate path, new actor, new side effect, or changed postcondition to an existing use case. | Preserve existing guarantees while making the changed path explicit and testable. | Current source/test/doc evidence, execution trajectory or diff evidence, changed path, compatibility and regression risk. | `repository-context-map`, `scenario-decomposition`, `quality-test-gate` | Treating project memory or prior output as current behavior without source confirmation. |
| System/external actor | Webhook, scheduled job, queue consumer, integration, or automation starts behavior. | Model trust boundary, idempotency, duplicate delivery, availability, and recovery as actor-facing behavior. | Actor identity, authentication/precondition, idempotency rule, retry/duplicate outcome, durable state or event. | `permission-boundary-modeling`, `domain-event-modeling`, `integration-change-builder` | Hiding background work inside the main path as "system does X." |
| Failure or partial-commit path | Payment, inventory, export, import, legal record, or async work can partially succeed. | Name preserved state, compensation, retry window, support/audit visibility, and terminal outcome. | Failure-state table, recovery owner, irreversible side effects, audit/event impact, acceptance trace. | `state-machine-modeling`, `transaction-consistency`, `domain-event-modeling` | Generic "show error" exits. |
| Cross-context or authorization-sensitive | Use case crosses modules, tenants, roles, bounded contexts, or ownership scopes. | Keep actor permissions, object ownership, and context boundaries visible in the behavior contract. | Subject/resource/action/scope, context owner, handoff boundary, denied path, audit expectation. | `permission-boundary-modeling`, `architecture-impact-reviewer`, `domain-object-identification` | Collapsing multiple roles or bounded contexts into "user." |

# Industry Benchmarks

Anchor against: **Ivar Jacobson — Object-Oriented Software Engineering (1992)** for actor-goal abstraction and use case as behavioral contract; **Alistair Cockburn — Writing Effective Use Cases** for goal levels, fully dressed use cases, stakeholder interests, and minimal guarantees; **UML Use Case Diagrams (ISO/IEC 19501)** for actor/system-boundary notation; **BDD/Gherkin** for Given/When/Then scenario traceability; **IEEE Std 830** and **BABOK** for requirement/test traceability and stakeholder analysis; and **Domain-Driven Design** for ubiquitous language, bounded context boundaries, and domain events as postconditions. Load the fully dressed template reference only when drafting a complete use case or reviewing whether an output has enough professional detail.

# Selection Rules

Select this capability when **the primary question is actor-goal interaction design for a domain or product behavior**. Route to `user-flow-modeling` when UI navigation branches, multi-screen flow design, and browser navigation behavior are the primary concern. Route to `scenario-decomposition` when comprehensive path coverage across happy paths, edge cases, failures, and operational behaviors is needed. Route to `acceptance-standard-definition` when the use case is defined and the goal is writing testable acceptance criteria. Route to `state-machine-modeling` when the use case postconditions involve lifecycle state transitions.

# Risk Escalation Rules

Escalate when: an alternate path affects authorization (a different actor can reach a normally-restricted postcondition through the alternate path — potential privilege escalation); a failure path leaves the system in a partially committed state (payment charged but subscription not activated — requires idempotency and recovery design); a postcondition involves irreversible financial, legal, or compliance-relevant record creation (must verify that audit and retention requirements are met); a precondition references an external system availability check (what happens if that system is unavailable?); or a use case spans multiple bounded contexts (domain boundaries may conflict — escalate to `architecture-impact-reviewer`).

# Proactive Professional Triggers

- **Signal:** A request says an actor "can," "should be able to," or "needs to" do something but omits enforced preconditions and durable postconditions. **Hidden risk:** acceptance criteria validate UI reachability while the domain guarantee remains undefined. **Required professional action:** produce a use case contract before implementation or tests. **Route to:** `use-case-modeling`, `acceptance-standard-definition`. **Evidence required:** actor/goal boundary, entry gates, trigger, success guarantee, minimal guarantee, and acceptance trace.
- **Signal:** One story contains multiple roles, system actors, or actor goals. **Hidden risk:** alternate paths become unrelated use cases and permissions or tests miss role-specific outcomes. **Required professional action:** split by primary actor and goal, then link shared included behavior explicitly. **Route to:** `user-role-identification`, `permission-boundary-modeling`. **Evidence required:** decomposed use case list, shared behavior, rejected combined scope, and role-specific denied paths.
- **Signal:** A webhook, scheduled job, queue consumer, import, or integration initiates the behavior. **Hidden risk:** trust boundary, idempotency, duplicate delivery, timeout, and replay behavior are absent from the product contract. **Required professional action:** model the external or system actor and name authentication, duplicate, retry, and terminal outcomes. **Route to:** `domain-event-modeling`, `integration-change-builder`. **Evidence required:** actor identity, precondition, idempotency key or duplicate rule, failure state, and recovery owner.
- **Signal:** An alternate or failure path ends with "show error," "retry later," or "support will handle it." **Hidden risk:** partial state, lost input, audit gaps, or unrecoverable stuck records are left unspecified. **Required professional action:** define state preservation, retry window, recovery owner, audit visibility, and terminal postcondition. **Route to:** `state-machine-modeling`, `quality-test-gate`. **Evidence required:** failure postcondition, preserved data, retry/compensation rule, support or operator visibility, and test case.
- **Signal:** A prior project memory note, repository graph edge, or execution trajectory suggests the use case already exists.
  **Hidden risk:** stale memory or graph proximity is treated as semantic proof and the changed behavior is under-specified.
  **Required professional action:** verify current source, tests, docs, or registry entries and document accepted/rejected evidence before reusing the use case.
  **Route to:** `repository-context-map`, `repository-graph-analysis`, `execution-trajectory-analysis`.
  **Evidence required:** inspected paths, freshness report, matching behavior, mismatches, validation command, and evidence limits.

# Critical Details

- **Postconditions that describe UI state instead of durable system state produce untestable acceptance criteria.** "The user sees a success screen" cannot be verified by an automated integration test, a monitoring alert, or a business analyst reviewing the system state. "A ACTIVE subscription record exists in the database with the customer ID and plan ID" can be verified by every stakeholder. Always formulate postconditions as system state, emitted events, or external-system side effects — not as UI rendering outcomes.
- **Alternate paths are where most production incidents originate.** The main success path is typically well-tested. The alternate paths (coupon applied, payment method changed, plan downgraded, concurrent subscription attempts) are typically undertested. Each alternate path must be treated as a first-class path with its own postconditions, not as an exception handler.
- **Failure paths must specify state preservation.** A use case that says "if payment fails, show an error" has not specified: is the form data preserved so the customer does not have to re-enter it? Is the subscription record in FAILED or deleted? Can the customer retry immediately? Can support view the failed attempt? These questions become production support tickets if not answered in the design.
- **"Include" and "extend" relationships in use case diagrams must not hide business rules.** A use case that "includes" an authentication check without specifying what the authentication precondition is hides the rule. Every included use case must have its own preconditions, postconditions, and failure paths that are visible to the parent use case designer.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 actor-goal modeling rules and the output contract. Use inline-only mode for routing and small wording decisions; load a deep reference only when the current use-case claim needs more detail:

- **L1/L2 checklist closure:** load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete use case, when path coverage or guarantees are uncertain, or before implementation/test planning depends on the use case.
- **L3 fully dressed template:** load [references/fully-dressed-template.md](references/fully-dressed-template.md) when a complete Cockburn-style template is needed or when reviewing whether a use case has enough professional detail.
- **Evidence closure:** load [references/evidence-patterns.md](references/evidence-patterns.md) when the use case depends on repository graph, project memory, execution trajectory, source freshness, validation command output, tool permission boundary, or a changed-use-case-to-acceptance map.
- **Shape example:** use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear.
- **Anti-bloat rule:** do not load these references for pure routing decisions, trivial wording work, full scenario matrices, UI flow design, or implementation placement when the output contract and quality gate are enough.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Postcondition: "User sees success message" | Untestable; does not describe system state; acceptance criteria cannot be derived | Postcondition: "Subscription record in ACTIVE state; entitlements activated; event published" |
| Precondition: "User is logged in" (vague) | Missing: email verified? account not suspended? plan not already active? | Enumerate all gates: "Authenticated; email verified; no active Pro subscription; account not suspended" |
| Alternate path: "If coupon invalid, show error" | Missing: what state is preserved? can user proceed without coupon? is coupon consumed? | Explicit: form data preserved; error message specifies reason; user can submit without coupon |
| External actor (payment webhook) treated as implicit background | Trust boundary not drawn; no authentication requirement stated; idempotency not designed | Model as secondary actor with precondition: "webhook authenticated via HMAC signature"; idempotency: "duplicate webhook ignored if subscription already ACTIVE" |
| Use case describes 3 actor goals in one | Two alternate paths are actually separate use cases with different actors | Decompose: UC-014a (new customer subscribes), UC-014b (existing customer upgrades), UC-014c (team admin subscribes for team) |
| Failure path F2 (timeout) not modeled | Payment gateway timeout produces stuck PENDING subscriptions; no recovery path; support tickets | Model F2 with explicit PENDING state, background polling job, 30-min resolution window, FAILED fallback |

# Failure Modes

- **Missing enforced precondition:** "no active subscription" is listed but not enforced; concurrent requests create duplicate subscriptions and the customer is charged twice.
- **Unmodeled timeout alternate path:** payment gateway timeout leaves subscriptions in PENDING indefinitely; manual database fixes become the recovery path.
- **UI-only postcondition:** postcondition says "success screen shown" instead of durable system state; automated acceptance tests cannot verify the guarantee and bugs ship.
- **Implicit external actor:** payment webhook is treated as background work; authentication, duplicate delivery, replay, and terminal state are never designed.
- **No state preservation rule:** payment decline clears the customer's cart; the actor cannot retry without re-entering data, causing avoidable abandonment.
- **Merged actor goals:** customer purchase, support override, and scheduled expiry are modeled as one use case; permission denial and audit outcomes disappear.
- **Stale memory accepted as proof:** an old project note or graph edge says a use case exists, but current source or tests changed the precondition and acceptance trace is wrong.
- **No minimal guarantee:** a partial failure creates an order, sends email, and then fails payment; nobody can tell what the system promises after the actor goal is not achieved.

# Output Contract

Return a use case set with:

- `mode_selected` (new actor-goal contract / existing behavior extension / system-external actor / failure-partial-commit / cross-context-authorization-sensitive)
- `actor_goal_boundary` (one primary actor, one actor goal, rejected actors/goals, and decomposition decision)
- `source_evidence` (current source/tests/docs/registry inspected; memory/graph/execution trajectory evidence used and freshness limits)
- `boundaries_inspected` (actor, system boundary, context owner, permissions, external actors, durable state, emitted events, side effects, tests, docs, and skipped boundaries with reason)
- `use_case_id` and `name`
- `primary_actor`, `secondary_actors`, `goal`, `scope`
- `stakeholder_interests`
- `guarantee_level` (minimal guarantee, success guarantee, recovery owner, and unsupported guarantee)
- `preconditions` (enumerated and enforced gates)
- `trigger`
- `main_success_path` (numbered steps)
- `alternate_paths` (named, with postconditions)
- `failure_paths` (named, with system state, recovery, retry rules)
- `postconditions` (success and failure — system state, events, side effects)
- `business_rules_referenced` (linked by rule ID)
- `acceptance_trace` (acceptance criteria IDs derived from this use case)
- `validation_evidence` (test, validator, command, exit code, report, or artifact that will prove the use case contract before implementation handoff)
- `risk_flags` (authorization, irreversibility, cross-context, availability)
- `handoff_boundaries` (rules, permissions, lifecycle states, events, API contracts, UI flow, or tests that require another capability)
- `unresolved_decisions` (owner, blocking status, and validation needed)

# Evidence Contract

Close a use-case-modeling change only when the output names:

- **Boundaries inspected:** actor/goal, system boundary, bounded context, permission or tenant scope, external actors, durable state, emitted events, side effects, current source/tests/docs, and skipped boundaries with reason.
- **Validation evidence:** test, validator, command, exit code, report, artifact, or explicit not-verified disclosure that proves the use case contract is ready for acceptance or implementation handoff.
- **What evidence proves:** the selected actor-goal boundary, enforced entry gates, current-source confirmation for memory/graph/execution evidence, success guarantee, minimal guarantee, and acceptance/test trace.
- **What evidence does not prove:** uninspected production behavior, unavailable stakeholders, downstream consumer acceptance, live external-system behavior, or implementation correctness before the next gate runs.
- **Residual risk and handoff:** unresolved decision, owner, blocking status, validation needed, evidence limits, and next gate owner. A generic feature narrative or UI-only scenario is not sufficient evidence.

# Benchmark Coverage

Behavior improvement should be validated structurally: baseline weak use cases usually merge actors, omit entry gates, treat UI messages as postconditions, hide external actors, or leave failure paths as generic errors; improved outputs must name mode, actor goal, enforced preconditions, durable path outcomes, guarantees, risk flags, acceptance trace, and handoff boundaries. Token overhead is acceptable only while this capability stays narrower than full scenario decomposition, UI flow modeling, or implementation design.

# Routing Coverage

Route here when the primary work is actor-goal behavior specification. Guard against over-routing by handing off when the primary work is UI navigation (`user-flow-modeling`), exhaustive test matrix generation (`scenario-decomposition`), already-defined acceptance wording (`acceptance-standard-definition`), lifecycle legality (`state-machine-modeling`), rule authority (`business-rule-extraction`), permission matrix design (`permission-boundary-modeling`), durable event contract (`domain-event-modeling`), or implementation placement (`implementation-structure-design`).

# Quality Gate

The use case set is complete only when:

1. Every use case has exactly one primary actor and one goal.
2. All preconditions are enumerated entry gates, not aspirational statements.
3. All postconditions describe durable system state, events, or side effects — not UI messages.
4. All alternate paths have explicit postconditions and recovery options.
5. All failure paths specify system state preservation and retry rules.
6. All external system actors have authentication and idempotency preconditions.
7. All business rules referenced in paths are named and linked.
8. Acceptance criteria can be derived directly from postconditions.
9. Risk flags are raised for authorization, irreversibility, cross-context, and availability concerns.
10. The use case is precise enough that a developer can implement it and a tester can verify it without additional clarification.
11. Selected mode, actor-goal boundary, and rejected combined scopes are explicit.
12. Memory, repository graph, and execution trajectory evidence are source-confirmed or clearly marked as not verified.
13. Handoff boundaries are named for rules, permissions, states, events, API contracts, UI flow, and tests instead of being fully modeled here.
14. Unresolved decisions have owners, blocking status, and validation evidence needed before implementation.
15. The output states what validation evidence, validator, command, report, or artifact will prove the use case contract before acceptance or implementation work claims readiness.
16. Residual risk, evidence limits, and next gate are explicit when current source, stakeholder input, external-system behavior, or test evidence is missing.

# Used By

- domain-impact-modeler
- change-impact-analyzer

# Handoff

Hand off to `acceptance-standard-definition` for testable acceptance criteria; `state-machine-modeling` for postconditions involving lifecycle states; `scenario-decomposition` for comprehensive path coverage; `user-flow-modeling` for UI navigation design.

# Completion Criteria

The capability is complete when **actor goals, preconditions, all paths, and postconditions are specified with enough precision to drive acceptance criteria, implementation decisions, and test scenarios without requiring additional stakeholder clarification**.
