---
name: business-rule-extraction
description: Extracts business rules, policies, calculations, and invariants so they are not scattered across UI, controllers, SQL, scripts, or tests.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "13"
changeforge_version: 0.1.0
---

# Mission

Identify authoritative business rules, policies, calculations, invariants, and exceptions; **name a single owner and a single enforcement layer per rule**; and prevent inconsistent reimplementation across UI, controllers, services, SQL, jobs, scripts, imports, and tests — so that every entry point produces the same decision and the system can credibly answer "why was this allowed/denied?" with one source.

# When To Use

Use this capability when a change affects: eligibility, pricing, discounts, fees, taxes, commissions, refunds, credit limits, KYC/AML rules, age/region gating, license/feature entitlements, role-based or attribute-based permissions, lifecycle guards (state-machine transitions, cancellation windows, freeze rules), domain validation (uniqueness, mandatory combinations, mutually-exclusive sets), capacity limits, expiration rules, retention rules, compliance behavior, fraud rules, throttling business policy, SLAs and SLOs that materialize as customer-facing rules, or any logic where the regulator, finance, legal, product, or risk owner expects a stable, traceable answer.

# Do Not Use When

Do not use this capability to collect every implementation conditional without domain meaning. Defensive coding (`if user is None`), transport-format checks (`is_valid_email`), UI affordances (`disable button`), and storage constraints (`NOT NULL`) are not business rules unless they encode domain policy. Do not use it to force every small validation through a heavy domain abstraction or rule engine.

# Non-Negotiable Rules

- **Each rule has exactly one authoritative owner** (a person/role) and **exactly one authoritative enforcement layer** (the place that decides). Other layers may *preview* (UI hint), *defend* (DB constraint), or *audit* the same rule, but they do not *decide*.
- **The decision is enforced at every entry point**: UI, public API, internal API, batch jobs, import flows, admin tooling, replays, retries, scheduled tasks, migrations. UI-only enforcement is insufficient for any rule that affects money, eligibility, or compliance.
- **Rules are named.** A rule has a stable id (e.g. `RULE.PRICING.B2B-DISCOUNT-CASCADE`), a one-sentence statement, an owner, an effective date, and a versioning history. Code, tests, audit logs, and customer support refer to the same id.
- **Rules are testable in isolation** from transport, persistence, and UI; a unit test can pass an input set and assert the decision plus the *reason*.
- **Rules return reasons, not just booleans** (`Denied(rule=KYC.AGE-18, evidence=...)`). Audit, customer support, and regulator response require *why*.
- **Exceptions / overrides** are themselves rules: who may override, with what evidence, with what audit, with what expiry. Ad-hoc overrides become hidden authoritative behavior.
- **Precedence is explicit** when multiple rules apply (priority, specificity, ordered chain, or scoring). "Whichever code branch runs first" is not precedence.
- **Regulatory rules carry traceability**: rule id ↔ regulation/contract clause ↔ owner ↔ test ↔ audit log field.
- **Effective dating**: rules have `effective_from`, optionally `effective_to`, and historical decisions reproduce the rule version that was in force at decision time (not today's). Required for refunds, contracts, audits, and regulator inquiries.
- **No silent rules in SQL.** A `WHERE status NOT IN (...)` filter that determines who can be billed is a business rule; lift it to the named catalog and reference from the query.
- **No silent rules in tests.** A test that asserts "`charge=8.50`" without naming the pricing rule encodes the rule by accident; tests reference the rule id.
- **No copy-paste of policy across services**; share via a domain library, a rules service, or a generated decision artifact (DMN, JSON), with a single source.

# Industry Benchmarks

Anchor against: **DDD (Eric Evans, Vaughn Vernon)** — Policy, Specification, and Invariant patterns; aggregate-bounded invariants; ubiquitous language for rule names. **GoF Specification pattern** for composable predicates returning reasons. **DMN 1.4 (Decision Model and Notation, OMG)** — formal decision-table standard with hit policies (Unique, First, Priority, Collect) and FEEL expression language. **Camunda DMN, OpenRules, Drools, IBM ODM, GoRules** for rule-engine implementations. **Business Rules Group — Business Rules Manifesto** (rules are first-class, declarative, and motivated by business). **OMG SBVR** for natural-language semantic specification of rules. **Clean Architecture (Uncle Bob)** — entities and use cases hold enterprise/application policy; frameworks and DBs are details. **Hexagonal / Ports & Adapters** — domain rules live in the domain hexagon, adapters do not own policy. **Anti-Corruption Layer (ACL)** for translating external systems into domain language so rules are not contaminated. **Open Policy Agent (OPA / Rego)** and **Cedar (AWS)** for policy-as-code where the rule is authorization. **Event Sourcing + Decider pattern (Jérémie Chassaing)** for reproducible historical decisions. **Regulatory traceability matrix** practices from **ISO 9001 / IEC 62304 / FDA 21 CFR Part 11 / SOX ITGC** — every regulated rule traces to clause, control, and evidence. **NIST SP 800-53 control mapping** for security rules. **Decision-Centric Architecture / Decision Intelligence** literature.

### Rule-Type Classification

| Type | Definition | Typical home | Example |
| --- | --- | --- | --- |
| **Invariant** | Must always hold for a domain object | Aggregate root constructor / mutator | `Order.total >= 0`, `Subscription has exactly one active plan` |
| **Precondition** | Must hold before a state transition | Domain command handler | `Cannot ship order before payment captured` |
| **Derivation** | Computes a value from inputs | Pure domain function | `tax = base * rate(jurisdiction, category)` |
| **Eligibility / Policy** | Decides yes/no/which-tier from facts | Decision table or policy object | `B2B customer in EU with annual ≥ €100k → tier Gold` |
| **Authorization** | Decides who may act | OPA/Cedar/policy service | `Only finance role + step-up MFA may issue refund > $1000` |
| **Lifecycle / State machine** | Allowed transitions | State machine in aggregate | `Order: Draft→Placed→Paid→Shipped→Delivered (no skip)` |
| **Constraint** | Structural requirement | DB constraint **plus** domain enforcement | `Email unique per tenant` |
| **Compliance / Regulatory** | Mandated by external rule with traceability | Decision table + audit + retention | `KYC tier 2 required for transfers > €1000` (AMLD) |

### Rule Placement Decision Tree

```
Is the rule a domain decision (eligibility / policy / pricing / lifecycle)?
├─ Yes → Owns: domain layer.
│    Is it expressible as a decision table?
│    ├─ Yes → DMN table or equivalent (versioned, owned by business analyst). Tested by unit + tabular tests.
│    └─ No  → Domain object / Policy class returning a reasoned result.
│    Mirror in: UI (hint only), API (validation pre-check returning the same reasons), audit log.
│
├─ No, it's authorization who-may-do-what → routing to authentication-authorization (PEP/PDP).
├─ No, it's input shape / format → routing to input-validation.
├─ No, it's a structural data invariant → DB constraint **plus** domain enforcement (defense in depth).
└─ No, it's UI affordance only → component layer; do not call it a business rule.
```

### Rule-Engine vs Code Decision Matrix

| Factor | Code (domain objects) | Decision table (DMN/JSON) | Full rules engine (Drools/ODM) |
| --- | --- | --- | --- |
| Change frequency | Low–medium | Medium–high | High, business-authored |
| Authored by | Engineers | Analysts + engineers | Business analysts |
| Combinatorial complexity | Low–medium | High (tabular) | Very high (forward chaining) |
| Testability | Excellent | Excellent (tabular cases) | Harder (rule interaction) |
| Performance predictability | Excellent | Excellent | Variable |
| Auditability | Good (with reason objects) | Excellent (table + version) | Excellent if disciplined |
| Pick when | Stable policy, deep domain logic | Tabular eligibility / pricing matrices | Insurance underwriting, claims adjudication, broker logic |

# Selection Rules

Select this capability when the primary risk is **rule authority, consistency across entry points, and traceability**. Adjacent routing:

- Prefer `domain-object-identification` when ownership and aggregate boundaries are not yet known.
- Prefer `service-business-logic` (or `domain-logic-implementation`) when implementation placement and code structure is the question.
- Prefer `authentication-authorization` for who-may-do-what (authorization rules).
- Prefer `input-validation` for transport and shape validation.
- Prefer `data-modeling` / DB constraints for structural invariants — but **always pair with** domain enforcement for non-trivial rules.
- Use **with** `acceptance-standard-definition` so each rule has verifiable acceptance evidence.

# Risk Escalation Rules

Escalate when a rule affects: money (pricing, billing, refunds, settlement), eligibility (KYC, AML, sanctions, age, region, license), entitlement (feature access, plan tier), legal retention, regulated data (PII/PHI/PCI), audit history, fraud / risk controls, external commitments (contracts, SLAs), irreversible workflow transitions (cancel, settle, ship, close-of-books), or anything a regulator or auditor may demand reproducibility for. Escalate any rule with no named owner or with disagreement between product/finance/legal/risk on what the rule is.

# Critical Details

Rules have scope, authority, exceptions, precedence, and enforcement timing. Mishandling any of these is how policy quietly diverges. Apply these refinements:

- **Coverage of every mutation path.** A rule enforced in the HTTP handler but not in the import flow, the admin override, the migration script, the message-queue consumer, or the retry path will be violated by exactly those paths. Inventory entry points and prove coverage.
- **Replay safety / effective dating.** Replaying yesterday's events with today's rule produces wrong history. Either snapshot the *decision* (preferred for audit) or version the rule and resolve to the version that was in force.
- **Reasons over booleans.** `eligible: false` is not auditable; `eligible: false, reason: "KYC.TIER2-REQUIRED", evidence: {...}` is. Customer support, regulators, and post-incident analysis all need the *why*.
- **Override discipline.** Manual overrides are themselves rules. Without `who may override / under what conditions / what evidence / what audit / what expiry`, overrides become the real (undocumented) policy.
- **Precedence ambiguity.** When rule A says "give 10% discount" and rule B says "never discount this SKU", precedence must be declared. DMN hit policies (Priority, First, Collect) make this explicit; ad-hoc `if/elif` chains hide it.
- **Defense in depth ≠ duplication.** A unique-email rule may exist as: domain invariant (canonical), DB unique index (defense), UI inline-check (UX), API 4xx response (transport). All four are fine *if they reference one source*. Independent reimplementations are not.
- **Rules vs configuration.** Tax rate by jurisdiction is *configuration*; "tax = base × rate" is the rule. Confusing the two leads to either hard-coded data or under-tested logic.
- **Rule discovery.** Existing systems hide rules in: `WHERE` clauses, stored procedures, scheduled jobs, email templates, customer support macros, spreadsheets, and tribal knowledge. Extraction means *finding* them, not just *documenting* them.
- **Spreadsheet provenance.** Many real rules live in finance/operations spreadsheets. Treat as authoritative source until ported, with an explicit migration plan; do not silently re-derive.
- **Regulatory traceability matrix.** For each regulated rule: regulation clause → rule id → enforcement code path → audit log field → test case → owner. Auditors expect this matrix.
- **State-machine guards** are rules. `cancel_order` allowed only in `Placed` or `Paid` (not `Shipped`) is a rule, with reason and override discipline.
- **Event-time vs transaction-time.** "Eligible at the time the customer placed the order" ≠ "eligible now". Rules acting on historical events must use event-time facts (price at time of order, plan at time of usage) — not today's facts.
- **Idempotent rule application.** A retry must not re-discount, re-credit, re-grant. Rule application is paired with idempotency keys (see `idempotency-retry-design`).
- **Anti-corruption layer.** Rules that depend on external system data (e.g., partner risk score) must translate into the domain language at the boundary; otherwise external-vocabulary leakage corrupts the rule catalog.
- **Performance.** Rule engines may evaluate hundreds of rules per request; profile, cache decisions when inputs are stable, but *invalidate on rule version change*.
- **Rule deprecation.** Removing a rule is a release event with the same rigor as adding one — historical decisions still reference it; effective_to is mandatory; audit must remain explainable.

### Anti-examples

| Anti-pattern | Why it fails |
| --- | --- |
| Discount rule lives in the React component | API and import paths bypass it; refund support cannot explain pricing |
| Three controllers each compute `is_eligible` slightly differently | Customer in identical state gets different answers depending on path |
| Test asserts `total == 8.50` with no rule reference | When the rule changes, no one knows which test breaks why |
| `WHERE status NOT IN ('archived','frozen','...')` is the *only* place "billable" is defined | New code path queries differently and bills wrong customers |
| Operator can override eligibility via admin UI with no audit / no expiry | Override becomes the de-facto rule; regulator cannot reconstruct |
| Refund recomputed today using today's tax table for an order from last year | Wrong tax; audit fail |
| Rule "users < 18 cannot purchase" enforced in checkout but not in subscription renewal | Aging-out users continue purchasing through renewals |
| `if/elif` cascade silently determines precedence between competing promotions | Reordering for clarity changes business behavior |

# Failure Modes

- A rule is enforced in the UI but bypassed via API, job, import, admin override, retry, or migration paths.
- Multiple controllers/services duplicate a policy decision with subtle differences; same input → different outputs by route.
- Tests encode expected rule behavior without naming the rule, so rule changes break unrelated-looking tests.
- SQL `WHERE`/`JOIN` filters become the only authoritative definition of "active", "billable", "eligible", "visible".
- Exceptions handled as one-off `if` branches without owner, audit, expiry, or precedence — exception list silently grows.
- Replays / backfills / refunds use today's rule version against historical events → incorrect history and audit failure.
- Override capability exists with no audit, no two-person rule, no expiry → becomes the actual policy.
- Regulator asks "why did this customer get this decision on this date?" and the answer requires archaeology rather than a query.
- Spreadsheet held by finance is the real source of truth; engineering copy drifts each quarter.
- Rule engine adopted but rules become more, not less, scattered (engine + code + DB + UI all hold variants).
- Rule deprecated in code but still referenced by historical decisions → audit log has dangling rule ids.
- Decision returns boolean only; customer support cannot explain the denial; regulator complaint escalates.
- Pricing rule depends on a feature flag → effective rule depends on rollout state, not documented anywhere.

# Output Contract

Return a business rule catalog with, per rule:

- `rule_id` (stable, namespaced, e.g. `RULE.BILLING.LATE-FEE-WAIVER`)
- `statement` (one declarative sentence in business language)
- `type` (invariant / precondition / derivation / eligibility / authorization / lifecycle / constraint / compliance)
- `owner` (role/person; not "engineering")
- `enforcement_layer` (the single authoritative location)
- `defense_in_depth_layers` (UI hint, API pre-check, DB constraint, audit — each referencing the canonical source)
- `entry_points_covered` (UI, public API, internal API, jobs, imports, admin, replays, migrations — with proof)
- `inputs` (named facts / context required)
- `output_shape` (decision + reason code + evidence)
- `precedence` (if interacts with other rules; declared hit policy / priority)
- `exceptions_and_overrides` (who, when, with what evidence, audit, expiry)
- `effective_from` / `effective_to` and **versioning policy**
- `historical_decision_strategy` (snapshot decision vs replay-with-version)
- `regulatory_trace` (regulation clause, control id, audit field) — if applicable
- `tests` (unit + tabular cases + entry-point coverage tests + replay tests)
- `audit_log_fields` (rule_id, version, inputs hash, decision, reason)
- `examples` (positive, negative, edge, override)
- `deprecation_plan` (when applicable)

# Quality Gate

The catalog passes only when:

1. Every material rule has **one named owner and one named enforcement layer**.
2. Every rule has a **stable id, statement, type, inputs, output-with-reason, and tests**.
3. **All entry points** (UI, API, jobs, imports, admin, replays, migrations) are inventoried and proven to honor each rule (or explicitly exempted with justification).
4. **Exceptions and overrides** are themselves catalogued rules with audit, evidence, and expiry.
5. **Precedence** is declared whenever rules interact; no implicit ordering.
6. **Effective dating** allows historical decisions to be reproduced (or decisions are snapshotted).
7. **Regulated rules** carry traceability to clause, control, audit field, and test.
8. Tests cover positive, negative, edge, override, and historical-replay scenarios — and reference rule ids.
9. Audit log captures rule id + version + inputs + decision + reason for every regulated/financial decision.
10. No rule is encoded only in SQL filters, UI components, test fixtures, support macros, or spreadsheets without being lifted to the catalog.

# Used By

- domain-impact-modeler
- backend-change-builder

# Handoff

Hand off to `domain-logic-implementation` for code placement and structure; `authentication-authorization` for authorization rules and PEP/PDP separation; `acceptance-standard-definition` for rule acceptance evidence; `quality-test-gate` for invariant and tabular coverage; `data-modeling` for structural-invariant defense in depth; `idempotency-retry-design` for safe retry of rule application; `logging-error-handling` for rule audit logging; `compliance-regulatory-mapping` (where present) for regulatory traceability.

# Completion Criteria

The capability is complete when **every material business rule is named, owned, enforceable from one place, honored at every entry point, returns a reason rather than a boolean, is testable in isolation, is effective-dated for historical reproducibility, has explicit override and audit discipline, and — for regulated rules — traces to the clause it implements**. The system can credibly answer "who decided this, by which rule, in which version, on what evidence?" for any decision in scope.
