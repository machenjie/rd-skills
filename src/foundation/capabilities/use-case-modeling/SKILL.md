---
name: use-case-modeling
description: Models use cases with actor, precondition, trigger, main path, alternate path, and postcondition for product-domain behavior.
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

# Non-Negotiable Rules

- **Name exactly one primary actor and one goal per use case.** A use case with two actors and two goals is two use cases. The primary actor is the one whose goal drives the interaction — the one whose goal is satisfied or frustrated at the end. System actors (external services, scheduled jobs, webhooks) are valid primary actors. "The user" is not a precise actor name — the actor must be named by role: "Customer," "Support Agent," "Payment Webhook," "Scheduled Report Job."
- **Define preconditions that must be true before the use case can begin.** Preconditions are not aspirational — they are enforced entry gates. If the precondition is violated, the use case does not begin and the actor is routed to an error or prerequisite fulfillment path. Examples: "User is authenticated and has verified email address"; "Subscription plan exists and is active"; "Invoice has status UNPAID and is not past the 90-day dispute window." Missing preconditions produce invalid entry paths where the system receives a request it is not designed to handle.
- **Define postconditions as durable state changes, emitted events, or externally observable outcomes — not as UI messages.** "The user sees a success message" is a UI implementation detail, not a postcondition. Postconditions must express what remains true in the system after the use case completes: "A subscription record exists in ACTIVE state for the customer and plan"; "A payment_succeeded event is published to the billing topic"; "The inventory count for product X is decremented by the ordered quantity." These postconditions are directly testable and drive acceptance criteria.
- **Every alternate path must resolve to a defined outcome — either achieving the primary actor's goal through a different path, or explicitly exiting with a named error state.** An alternate path that ends with "the user sees an error" is incomplete — it must specify: what state the system is left in, what data is preserved, whether the actor can retry, and what the recovery path is. Unspecified alternate path outcomes become the source of "the system is in an unexpected state" production incidents.
- **External systems that trigger behavior must be modeled as actors.** A payment webhook that triggers an order confirmation is an actor. A scheduled job that expires stale sessions is an actor. A CI/CD pipeline that triggers a deployment is an actor. Treating all triggers as implicit background behavior hides the trust boundary (does the payment webhook require authentication?), the precondition (must the order exist in PENDING state?), and the failure path (what if the webhook delivers duplicate events?).
- **Business rules referenced in the main path or alternate paths must be named and linked.** A use case that says "the system validates the order" is incomplete — it must name which business rules govern the validation: "validate per OrderValidationRule-001 (minimum order value $10), StockAvailabilityRule-003 (all items in stock), FraudCheckRule-007 (order score < 80)." This linkage enables traceability from use case to business rule to unit test.

# Industry Benchmarks

Anchor against: **Ivar Jacobson — Object-Oriented Software Engineering (1992)** — the originator of use case modeling; actor-goal abstraction; use case as behavioral contract; include/extend relationships. **Alistair Cockburn — Writing Effective Use Cases** — goal levels (sea level, kite, fish); fully-dressed use case template; primary/secondary actors; stakeholder interests; minimal guarantees. **UML Use Case Diagrams (ISO/IEC 19501)** — notation for actors, use cases, system boundary, include/extend/generalization relationships. **BDD (Behavior-Driven Development) — Gherkin (Cucumber)** — Given/When/Then structure maps directly to use case precondition/trigger/postcondition; scenarios derived from alternate paths. **IEEE Std 830 (SRS)** — use cases as functional requirements; traceability from requirement to test. **BABOK (Business Analysis Body of Knowledge)** — use case as a business analysis artifact; stakeholder identification; scope modeling. **Domain-Driven Design (Eric Evans)** — ubiquitous language; bounded context boundary maps to use case system boundary; domain events as postconditions.

### Fully-Dressed Use Case Template

```
Use Case ID: UC-014
Use Case Name: Customer Subscribes to Pro Plan
Primary Actor: Customer (authenticated)
Secondary Actors: Payment Gateway (Stripe), Email Service
Goal: Customer pays for and activates a Pro subscription that gives access to Pro features
Scope: Subscription Management bounded context

Stakeholder Interests:
  - Customer: wants to pay once and gain access immediately
  - Business: wants payment confirmed before granting access
  - Compliance: wants payment record retained for 7 years

Preconditions:
  - Customer is authenticated and email-verified
  - Customer does not already have an active Pro subscription
  - Pro plan exists and is available for purchase (not discontinued)
  - Payment method is on file OR customer provides one during the flow

Trigger: Customer clicks "Upgrade to Pro" and confirms the purchase

Main Success Path:
  1. System presents the Pro plan with price, features, and billing cycle
  2. Customer confirms payment with existing payment method (or adds new one)
  3. System creates a pending subscription record (state: PENDING)
  4. System charges the customer's payment method via Payment Gateway
  5. Payment Gateway returns success with transaction ID
  6. System transitions subscription to ACTIVE state; grants Pro entitlements
  7. System publishes subscription.activated event
  8. Email Service sends activation confirmation to customer

Alternate Paths:
  A. Customer adds a new payment method (at step 2):
     A1. Customer enters card details; system tokenizes via Payment Gateway
     A2. Token stored; flow continues at step 3
  B. Customer applies a discount coupon (at step 2):
     B1. System validates coupon (CouponValidationRule-009)
     B2. Price adjusted; customer confirms adjusted price; flow continues at step 3

Failure Paths:
  F1. Payment gateway returns DECLINED:
      - Subscription record moved to FAILED state
      - Customer notified with decline reason (per PaymentDeclineMessageRule-003)
      - Customer offered option to update payment method and retry
      - Retry allowed up to 3 times within 24 hours
  F2. Payment gateway timeout (> 10s):
      - Subscription record remains in PENDING state
      - Background job polls transaction status every 60s for up to 30min
      - If resolved: proceed as main path step 5–8
      - If unresolved after 30min: subscription moved to FAILED; support alert triggered
  F3. Email service unavailable:
      - Subscription activation completes; entitlements granted (not blocked by email)
      - Email delivery retried by Email Service with exponential backoff
      - Not a failure exit; email is a best-effort side effect

Postconditions (Success):
  - Subscription record exists in ACTIVE state for customer/plan combination
  - Pro entitlements are active (checked on every authenticated request)
  - Payment record exists with transaction ID and amount
  - subscription.activated event is published to billing topic
  - Activation email delivered or queued for delivery

Postconditions (Failure F1):
  - Subscription record exists in FAILED state
  - No payment charge has been applied
  - Customer can retry with new payment method

Business Rules Referenced:
  - CouponValidationRule-009
  - PaymentDeclineMessageRule-003
  - SubscriptionUniquenessRule-001 (only one active Pro subscription per customer)

Acceptance Trace: AC-042, AC-043, AC-044, AC-045 (failure paths)
```

# Selection Rules

Select this capability when **the primary question is actor-goal interaction design for a domain or product behavior**. Route to `user-flow-modeling` when UI navigation branches, multi-screen flow design, and browser navigation behavior are the primary concern. Route to `scenario-decomposition` when comprehensive path coverage across happy paths, edge cases, failures, and operational behaviors is needed. Route to `acceptance-standard-definition` when the use case is defined and the goal is writing testable acceptance criteria. Route to `state-machine-modeling` when the use case postconditions involve lifecycle state transitions.

# Risk Escalation Rules

Escalate when: an alternate path affects authorization (a different actor can reach a normally-restricted postcondition through the alternate path — potential privilege escalation); a failure path leaves the system in a partially committed state (payment charged but subscription not activated — requires idempotency and recovery design); a postcondition involves irreversible financial, legal, or compliance-relevant record creation (must verify that audit and retention requirements are met); a precondition references an external system availability check (what happens if that system is unavailable?); or a use case spans multiple bounded contexts (domain boundaries may conflict — escalate to `architecture-impact-reviewer`).

# Critical Details

- **Postconditions that describe UI state instead of durable system state produce untestable acceptance criteria.** "The user sees a success screen" cannot be verified by an automated integration test, a monitoring alert, or a business analyst reviewing the system state. "A ACTIVE subscription record exists in the database with the customer ID and plan ID" can be verified by every stakeholder. Always formulate postconditions as system state, emitted events, or external-system side effects — not as UI rendering outcomes.
- **Alternate paths are where most production incidents originate.** The main success path is typically well-tested. The alternate paths (coupon applied, payment method changed, plan downgraded, concurrent subscription attempts) are typically undertested. Each alternate path must be treated as a first-class path with its own postconditions, not as an exception handler.
- **Failure paths must specify state preservation.** A use case that says "if payment fails, show an error" has not specified: is the form data preserved so the customer does not have to re-enter it? Is the subscription record in FAILED or deleted? Can the customer retry immediately? Can support view the failed attempt? These questions become production support tickets if not answered in the design.
- **"Include" and "extend" relationships in use case diagrams must not hide business rules.** A use case that "includes" an authentication check without specifying what the authentication precondition is hides the rule. Every included use case must have its own preconditions, postconditions, and failure paths that are visible to the parent use case designer.

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

- Precondition for "no active subscription" not enforced: concurrent requests create duplicate subscriptions; customer charged twice.
- Alternate path for payment gateway timeout not modeled: subscriptions stuck in PENDING indefinitely; manual database fixes required.
- Postcondition specifies UI instead of system state: automated acceptance tests cannot verify the postcondition; bugs ship.
- External webhook actor not modeled: webhook endpoint has no authentication; malicious replay attack confirms fraudulent subscriptions.
- Failure path state preservation not specified: customer's cart is cleared on payment decline; customer must re-select items; high abandonment rate.

# Output Contract

Return a use case set with:

- `use_case_id` and `name`
- `primary_actor`, `secondary_actors`, `goal`, `scope`
- `stakeholder_interests`
- `preconditions` (enumerated and enforced gates)
- `trigger`
- `main_success_path` (numbered steps)
- `alternate_paths` (named, with postconditions)
- `failure_paths` (named, with system state, recovery, retry rules)
- `postconditions` (success and failure — system state, events, side effects)
- `business_rules_referenced` (linked by rule ID)
- `acceptance_trace` (acceptance criteria IDs derived from this use case)
- `risk_flags` (authorization, irreversibility, cross-context, availability)

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

# Used By

- domain-impact-modeler
- change-impact-analyzer

# Handoff

Hand off to `acceptance-standard-definition` for testable acceptance criteria; `state-machine-modeling` for postconditions involving lifecycle states; `scenario-decomposition` for comprehensive path coverage; `user-flow-modeling` for UI navigation design.

# Completion Criteria

The capability is complete when **actor goals, preconditions, all paths, and postconditions are specified with enough precision to drive acceptance criteria, implementation decisions, and test scenarios without requiring additional stakeholder clarification**.
