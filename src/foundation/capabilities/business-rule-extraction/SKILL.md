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

Also use this capability when repository graph evidence, project memory, execution traces, tests, SQL, scripts, jobs, support macros, spreadsheets, or generated artifacts show the same domain decision being copied, hidden, disputed, stale, or enforced inconsistently across entry points.

# Do Not Use When

Do not use this capability to collect every implementation conditional without domain meaning. Defensive coding (`if user is None`), transport-format checks (`is_valid_email`), UI affordances (`disable button`), and storage constraints (`NOT NULL`) are not business rules unless they encode domain policy. Do not use it to force every small validation through a heavy domain abstraction or rule engine.

# Stage Fit

- **Planning:** extract candidate rules, owners, entry points, historical meaning, exceptions, and evidence before implementation chooses a placement.
- **Read/review / code-review:** inspect current code, SQL, tests, jobs, scripts, docs, support flows, spreadsheets, and prior decisions before declaring the authoritative rule.
- **Edit/implementation / coding:** keep one enforcement layer authoritative while allowing UI hints, DB constraints, audit logs, and API pre-checks to reference the same source.
- **Test/release:** require rule-id-based unit/tabular tests, entry-point coverage, historical replay evidence, audit fields, and owner acceptance for release-blocking rules.
- **Debugging / repair/regression:** turn the verified inconsistent decision into a named rule, scan same-pattern branches, and add regression evidence that the decision is now consistent.
- **Handoff:** close only with current source, graph, memory, execution, validation freshness, owner, and residual-risk evidence for the rule catalog.

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
- **No rule authority claim is valid without current evidence.** Prior memory, old diagrams, support knowledge, or historical tickets are leads only until current repository graph, execution evidence, rule owners, tests, audit fields, or authoritative external artifacts confirm the rule and its enforcement.

# Industry Benchmarks

Anchor against DDD policy/specification/invariant patterns, DMN 1.4 decision tables and hit policies, Business Rules Manifesto/SBVR semantic rule discipline, Clean/Hexagonal Architecture for policy placement, OPA/Rego and Cedar when the rule is authorization policy, event sourcing/decider patterns for reproducible history, and regulated traceability matrices where clauses, controls, tests, audit fields, and owners must align. Keep this body focused on rule authority, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for evidence matrices, rule-authority decision tables, graph/memory/execution coupling, validation mapping, and anti-pattern review.

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

### Placement And Implementation Decision

- Domain eligibility, pricing, lifecycle, and calculation rules belong in the domain model, policy object, decision table, or rule service that owns the decision; UI/API/DB/audit layers reference that source.
- Authorization rules route to `authentication-authorization` for PEP/PDP separation; input shape routes to `input-validation`; structural invariants pair domain enforcement with DB constraints; UI affordances stay in UI and are not business rules.
- Prefer code/domain objects for stable policy, decision tables for tabular policy with analyst review, and a full rules engine only for genuinely high-volume/high-change rule interaction where engine governance is worth the overhead.
- External system facts must be translated through an anti-corruption layer before rule evaluation; historical decisions must snapshot the decision or resolve the rule version effective at event time.

# Selection Rules

Select this capability when the primary risk is **rule authority, consistency across entry points, and traceability**. Adjacent routing:

- Prefer `domain-object-identification` when ownership and aggregate boundaries are not yet known.
- Prefer `service-business-logic` (or `domain-logic-implementation`) when implementation placement and code structure is the question.
- Prefer `authentication-authorization` for who-may-do-what (authorization rules).
- Prefer `input-validation` for transport and shape validation.
- Prefer `data-model-design` / DB constraints for structural invariants — but **always pair with** domain enforcement for non-trivial rules.
- Use **with** `acceptance-standard-definition` so each rule has verifiable acceptance evidence.
- Use **with** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when rule extraction depends on current graph reachability, stale prior decisions, command output, or validation freshness.
- Use **with** `business-semantic-control-plane` when rule evidence must enter a Business Semantic Pack with source-backed `FACT` records, memory/graph selector limits, selected/skipped references, and rule-to-validation mapping.

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for business-rule extraction:

- **Signal:** the same eligibility, pricing, lifecycle, entitlement, compliance, fraud, retention, capacity, refund, or calculation decision appears in multiple UI/controller/service/SQL/job/script/test/support paths. **Hidden risk:** identical facts produce different business decisions by entry point. **Required professional action:** name the rule, owner, authoritative enforcement layer, previews/defenses, and entry-point coverage. **Route to:** `business-rule-extraction`, `repository-graph-analysis`, and `quality-test-gate`. **Evidence required:** graph paths, duplicate decision sites, selected authority, and rule-id-based validation.
- **Signal:** a rule is hidden in SQL filters, stored procedures, spreadsheets, feature flags, support macros, test fixtures, import scripts, or admin tools. **Hidden risk:** the real policy can drift outside the rule catalog and evade review. **Required professional action:** lift the rule into the catalog, preserve provenance, and define migration or synchronization evidence. **Route to:** this capability plus `project-memory-governance` and `validation-broker`. **Evidence required:** source artifact, owner confirmation, freshness, migration plan, and not-verified gaps.
- **Signal:** a rule affects money, regulated eligibility, audit history, contractual SLA, legal retention, entitlement, fraud/risk, state transition, or irreversible operation. **Hidden risk:** unversioned or ownerless decisions become unreproducible during audit, dispute, or incident review. **Required professional action:** require effective dating, reason codes, audit fields, test cases, owner acceptance, and residual-risk sign-off. **Route to:** `domain-impact-modeler`, `security-privacy-gate` when regulated, and this capability. **Evidence required:** rule version, regulation/contract trace, audit field, test, owner, and release blocker.
- **Signal:** exceptions, overrides, precedence, or temporary rollout behavior are mentioned without expiry, audit, priority, or rule id. **Hidden risk:** exceptions become the actual hidden rule and precedence changes through branch order. **Required professional action:** catalog the exception as a rule, define precedence/hit policy, expiry, and audit. **Route to:** `state-machine-modeling`, `acceptance-standard-definition`, and this capability. **Evidence required:** exception owner, precedence table, override evidence, expiry, and regression case.
- **Signal:** project memory, old requirements, generated summaries, or previous tests are reused to assert the rule. **Hidden risk:** stale memory can certify a rule that current code, data, or operations no longer enforce. **Required professional action:** compare memory against current graph and execution evidence, then record accepted/rejected assumptions. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `plan-execution-consistency`, and this capability. **Evidence required:** source date, graph delta, current validation, and explicit unknowns.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing or a quick rule-authority review when no concrete rule catalog or implementation handoff is needed.
- **L2:** Load `references/checklist.md` for any real rule catalog, domain review, bug repair, audit preparation, or implementation plan involving rule authority, owner, entry point, exception, or evidence.
- **L3:** Load `examples/example-output.md` when producing a user-facing rule catalog, evaluation fixture, or structured handoff table.
- **L4:** Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when rule authority, duplicate decision sites, graph/memory/execution reuse, decision-table shape, audit traceability, historical replay, or rule-to-validation mapping needs deeper detail.
- **L4/L5:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the rule source depends on current code reachability, prior decisions, external artifacts, command output, tests, or audit evidence.
- **L5:** Pair with security, payment/trading, big-data, reliability, delivery, or compliance gates only when the selected rules touch those domain surfaces; do not load unrelated domain references for ordinary domain policy extraction.

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

- **Entry-point bypass:** A rule is enforced in the UI but bypassed via API, job, import, admin override, retry, or migration paths.
- **Duplicate authority:** Multiple controllers/services duplicate a policy decision with subtle differences; same input → different outputs by route.
- **Test-hidden policy:** Tests encode expected rule behavior without naming the rule, so rule changes break unrelated-looking tests.
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
- Rule hidden in SQL, controller, mapper, or test fixture is changed but not cataloged with rule id, owner, enforcement layer, and changed-path validation.

# Output Contract

Return `business_rule_catalog` with, per rule:

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
- `graph_memory_execution_validation` (rule source paths/artifacts inspected, project-memory claims accepted or rejected, command/test evidence, validation freshness, and unknowns)
- `business_semantic_rule_record` when BSP is selected: rule id, owner, enforcement layer, reason codes, entry points, effective dating, evidence class, selected/skipped references, and residual semantic risk
- `rule_to_validation_map` (rule id -> owner approval, implementation/enforcement location, entry-point checks, test/audit evidence, release blocker, and next gate)
- `evidence_limits` (uninspected entry points, stale external artifacts, unavailable rule owners, missing historical data, and residual uncertainty owner/date)

## BSP.business_rules Write Contract

When BSP is selected, each material rule must be writable to `BSP.business_rules` with:

- `rule_id`, statement, `owner`, and `authoritative_enforcement_layer`
- `authoritative_enforcement_paths` for non-manual and decided enforcement
- `preview_paths`, `defense_paths`, and audit paths when those layers exist
- non-empty `reason_codes`, inputs, outputs, precedence, exceptions, and non-empty entry points
- effective dating, historical decision strategy, and audit requirements when applicable
- tests, golden cases, owner review, or explicit residual risk
- evidence class, source paths or refs, and `validation_map` entries for claim-to-proof mapping

Rule extraction consumes BSP task intent, vocabulary, objects, workflows, `validation_map`, and `context_control` when present. Missing owner, enforcement layer, `reason_codes`, or entry points blocks rule closure unless the BSP records an explicit `OPEN_QUESTION` plus residual risk and owner handoff; graph and memory may select candidate rules but cannot create a BSP `FACT`.

# Evidence Contract

Acceptable evidence includes current source paths, SQL/stored procedures, route/job/import/admin/script inventories, tests, generated artifacts, support macros, spreadsheets or external rule sources, owner confirmation, audit/log schemas, rule-version data, replay evidence, and validation command output. Project memory and old requirements may guide discovery, but they cannot close a rule unless their date, source, and unchanged graph boundary are stated. Every cataloged rule must state what the evidence proves, what it does not prove, and which owner accepts any remaining ambiguity.

Close a business-rule extraction only when the handoff names boundaries inspected, current rule-source evidence, graph paths accepted or rejected, project-memory freshness, execution/validation commands, entry-point coverage, owner approval, stale or uninspected artifacts, what the rule evidence proves, what it does not prove, residual risk, and the next gate. If validation ran before the final rule/source/catalog edit, treat it as stale.

# Benchmark Coverage

Use DDD policy/specification/invariant patterns for owner and placement, DMN/SBVR for tabular or semantic rule expression, Clean/Hexagonal Architecture for adapter-vs-domain separation, OPA/Cedar for authorization policy routing, event-sourced decider practice for historical reproducibility, and regulated traceability matrices for audit-critical rules. Benchmark references must change placement, expression format, evidence, traceability, or validation depth; do not cite a framework as decoration.

# Routing Coverage

- Pair with `domain-object-identification`, `state-machine-modeling`, and `use-case-modeling` when the rule owner, aggregate boundary, lifecycle guard, or actor scenario is unclear.
- Pair with `authentication-authorization`, `input-validation`, and `data-model-design` when a candidate rule is actually authorization, input shape, or structural data enforcement.
- Pair with `acceptance-standard-definition`, `quality-test-gate`, and `validation-broker` when rule acceptance, entry-point coverage, tabular tests, replay tests, or validation freshness are needed.
- Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `plan-execution-consistency` whenever the rule catalog depends on current graph reachability, prior decisions, command evidence, or plan-to-evidence alignment.
- Pair with specialist domain gates only for selected rules that touch payments, regulated data, analytics/backfill, reliability, release, or security review surfaces.

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
11. Repository graph coverage includes every touched UI/API/service/domain/SQL/job/import/admin/script/test/support path or explicitly marks the path unavailable.
12. Project memory, prior tickets, generated summaries, spreadsheets, and external rule sources are dated, scope-checked, and rejected as proof when stale.
13. Every material rule appears in `rule_to_validation_map` with owner approval, implementation location, entry-point evidence, test/audit evidence, and release-blocking status.
14. Rule deprecation or precedence changes include historical decision compatibility and rollback or audit-retention evidence.
15. Business Semantic Pack rule claims classify memory and graph as selectors only unless current source, owner review, or validation evidence confirms the rule.
16. A non-manual, decided BSP rule has at least one authoritative enforcement path; missing paths block closure unless the rule is downgraded to owner review or residual risk.

# Used By

- domain-impact-modeler
- backend-change-builder

# Handoff

Hand off to `domain-logic-implementation` for code placement and structure; `authentication-authorization` for authorization rules and PEP/PDP separation; `acceptance-standard-definition` for rule acceptance evidence; `quality-test-gate` for invariant and tabular coverage; `data-model-design` for structural-invariant defense in depth; `idempotency-retry-design` for safe retry of rule application; `logging-error-handling` for rule audit logging; `security-privacy-gate` for regulatory traceability.

# Completion Criteria

The capability is complete when **every material business rule is named, owned, enforceable from one place, honored at every entry point, returns a reason rather than a boolean, is testable in isolation, is effective-dated for historical reproducibility, has explicit override and audit discipline, and — for regulated rules — traces to the clause it implements**. The system can credibly answer "who decided this, by which rule, in which version, on what evidence?" for any decision in scope.
