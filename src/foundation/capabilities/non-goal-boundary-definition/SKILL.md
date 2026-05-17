---
name: non-goal-boundary-definition
description: Defines in-scope and out-of-scope boundaries, version limits, anti-scope-creep controls, and assumptions that must not leak into implementation.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "06"
changeforge_version: 0.1.0
---

# Mission

**Protect implementation focus by making non-goals, version boundaries, exclusions, and deferred decisions explicit, testable, and enforceable** — ensuring that reviewers can identify unauthorized scope expansion, implementers know which adjacent work is explicitly out of scope, and no deferred decision leaks into current APIs, data schemas, permissions, or user-visible states without a conscious contract.

# When To Use

Use this capability when a change request: is at risk of expanding into adjacent workflows, redesigns, migrations, platform changes, UX refreshes, or policy changes; includes language like "while we're here, we should also…", "eventually this will need to support…", or "we might as well add the infrastructure for…"; defines a first version of a feature with implicit assumptions about future versions; sets boundaries between what is being built now versus what is deferred; or is being designed in a context where multiple stakeholders have different expectations about scope.

# Do Not Use When

Do not use this capability to: avoid required risk work (security, data integrity, compliance, accessibility) by labeling it a "non-goal"; suppress legitimate technical dependencies that must be resolved before coding begins (defer those via `requirement-clarification`, not non-goal definition); or defer decisions that fundamentally block the implementation from being correct or safe (a deferred auth design on a protected resource is not a non-goal — it is a blocker).

# Non-Negotiable Rules

- **Non-goals must be specific and testable as exclusions.** "We are not building a full admin portal" is not a non-goal — it cannot be checked. "We are not building user management (create, edit, deactivate users); only read-only display of existing user list is in scope for v1" is a non-goal — reviewers can verify no mutation endpoints exist and no user management UI appears in the implementation.
- **Version boundaries must state what the current release will and will not do — explicitly.** A `v1` boundary must define: what the feature does in v1, what it explicitly will NOT do in v1 (and is therefore excluded from v1 acceptance criteria), and what assumptions are forbidden (e.g., "v1 must not add a `subscription_tier` column to `users` table in anticipation of v2 billing features").
- **Deferred decisions must not introduce placeholder behavior in APIs, data models, permissions, or UI.** A non-goal excludes scope. It does not license adding empty endpoints, nullable columns, permission stubs, or hidden UI elements as "preparation for v2." Placeholder behavior creates surface area that is never cleaned up, may be accidentally exposed, and introduces untested paths. If a capability is not in scope, its surface area must not exist in the codebase.
- **Non-goals must not be used to bypass required security, data integrity, reliability, or compatibility work.** "Rate limiting is a non-goal for v1" is unacceptable if the endpoint is publicly accessible. "Input validation is a non-goal" is unacceptable for any endpoint that writes to a database. Required work that addresses OWASP Top 10, data correctness, or SLO obligations is not optional scope — it is a baseline requirement that non-goal definitions cannot remove.
- **Deferred scope must not contradict existing customer, legal, security, or platform commitments.** If a contract guarantees a feature by a date, if a regulation requires a control by a deadline, or if a platform SLA requires a behavior — these cannot be deferred by labeling them non-goals. Non-goal definitions must be reviewed against existing commitments before being accepted.
- **Acceptance criteria must include explicit "not present" checks for non-goals.** Every non-goal generates an exclusion check: "Verify that user management endpoints (POST/PUT/DELETE /users) do not exist." Without explicit exclusion checks in acceptance criteria, scope creep is invisible to QA and reviewers.

# Industry Benchmarks

Anchor against: **INVEST criteria (Bill Wake)** — Stories must be Independent, Negotiable, Valuable, Estimable, Small, Testable; "Negotiable" and "Testable" directly require scope boundaries to be explicit and verifiable. **RFC process (IETF)** — every RFC includes an explicit "Out of Scope" section that defines what the document does not address, preventing scope assumptions by implementers. **Product Management — Intercom "Shape Up" (Basecamp / Ryan Singer)** — "appetite" + "fixed time, variable scope" + explicit "rabbit holes" (things that look in-scope but must be avoided) — directly models non-goal boundary discipline. **Agile backlog slicing (Richard Lawrence "Humanizing Work")** — horizontal vs. vertical slice; explicit "we are only slicing this capability to [depth]; the rest is a separate backlog item." **TOGAF 9.2 Architecture Definition Document** — "Statement of Architecture Work" includes scope statement with explicit inclusions, exclusions, and constraints. **IEEE 830 Software Requirements Specification** — Section 1.5: "Scope of product"; Section 1.6: "Overview of non-functional requirements"; explicitly listing out-of-scope items is a standard SRS practice. **Google Design Docs** — every Google design document includes a "Non-Goals" section as a required heading; this practice is industry standard in engineering design documents. **OKR discipline (John Doerr "Measure What Matters")** — focus and key results only have meaning if the boundary of what is NOT being measured / achieved is explicit.

### Non-Goal Classification Matrix

| Category | Example In-Scope (v1) | Example Non-Goal (v1) | Risk if Not Stated |
| --- | --- | --- | --- |
| User management | Read-only user profile display | Create/edit/deactivate users | Engineers add management endpoints "while here" |
| Data migration | New feature persists new data | Migrating existing data to new schema | Migration added to v1, delaying launch |
| Internationalization | English-only UI | Multi-language support | Hardcoded strings; refactor required in v2 |
| Advanced search | Basic keyword filter | Full-text search, facets, saved searches | Full Elasticsearch integration attempted in v1 |
| API versioning | v1 endpoint | Backward compatibility with legacy API | Breaking change to legacy contract undetected |
| Performance optimization | Functional correctness | Sub-100ms P99 latency optimization | Premature optimization delays feature delivery |
| Platform migration | Feature built on current stack | Migration to new platform | Dual-platform code added speculatively |
| Accessibility | Keyboard navigable | Full WCAG 2.1 AA compliance | A11y left entirely for "later" (becomes never) |

### Non-Goal Boundary Definition Template

```
Feature: [Name of feature/change]
Version: v[N]
Date: [ISO date]
Owner: [Team/person responsible for this boundary]

IN SCOPE (v[N]):
  - [Specific behavior A: what it does, for which actors, in which context]
  - [Specific behavior B]

OUT OF SCOPE (v[N]) — Non-goals:
  - [Capability X]: NOT in v[N]. Deferred to v[N+1] backlog item #[ID].
    Reason: [time/complexity/dependency/priority]
    Forbidden assumption: [implementation MUST NOT add [Y] in anticipation of X]
  - [Capability Z]: NOT in v[N]. Will be assessed in Q[N] planning.

VERSION BOUNDARY:
  - v[N] contract: [What API shape, DB schema, permissions, UI are committed to]
  - Forbidden in v[N]: [Specific technical artifacts that must not exist]

DEFERRED DECISIONS:
  - [Decision D]: deferred to v[N+1]. Current implementation must not assume [assumption A or B].

ACCEPTANCE EXCLUSIONS (for QA):
  - Verify: [excluded endpoint] does NOT exist (returns 404 or is not defined in OpenAPI spec)
  - Verify: [excluded field] does NOT appear in response payload
  - Verify: [excluded UI element] is NOT rendered

ANTI-SCOPE-CREEP REVIEW CHECKLIST:
  [ ] Does any PR add endpoints, fields, or UI for out-of-scope capabilities?
  [ ] Does any DB migration add columns for future capabilities not in current scope?
  [ ] Does any change add permission checks or roles for future features?
  [ ] Does any change add feature flags for speculative future behavior?
```

### Scope Boundary Decision Tree

```
Is the proposed addition required for the in-scope feature to be:
  a) Functionally correct?
  b) Secure? (OWASP Top 10 controls, input validation, auth)
  c) Compliant with existing commitments? (contracts, regulations, SLA)
    ANY YES → NOT a non-goal; required work; must be in scope

Is it required for acceptable user experience for the defined user story?
  YES → In scope for v1
  NO  → Candidate for non-goal

Does deferring it break backward compatibility or create technical debt
that would cost more to fix in v2 than to include now?
  YES → Escalate: may not be deferrable
  NO  → Acceptable to defer; document as non-goal with explicit exclusion check

Does the current implementation need to "prepare" for it with placeholder code?
  YES → Block: placeholder code is not permitted for non-goals
         (if preparation is needed, the non-goal may be a dependency — escalate)
  NO  → Confirm: non-goal is clean; add acceptance exclusion check
```

# Selection Rules

Select this capability when: the primary need is **containing scope** and making exclusions explicit and testable. Route elsewhere when: **requirement-clarification** is primary (the unknown itself may block coding — the requirement is unclear, not merely out of scope); **task-dag-planner** is primary (approved scope must be sequenced into a task graph); **acceptance-standard-definition** is primary (defining what "done" means for in-scope items, not what is excluded).

# Risk Escalation Rules

Escalate when a proposed non-goal would: leave unsafe partial behavior (an in-scope mutation without input validation or authorization); violate backward compatibility without a migration plan; hide a required data migration that must precede v2; create a user-visible state with no defined behavior ("the button exists but does nothing in v1"); contradict a customer, legal, security, platform, or SLA commitment; or result in an implementation that cannot be extended to the v2 scope without a breaking change to the v1 API or data model.

# Critical Details

- **"We'll add it in v2" requires that v1 does not close the door on v2.** A non-goal means "not now." It does not mean "never." Before accepting a non-goal, verify that the v1 implementation does not create a structural blocker for the v2 capability. If v2 requires a multi-tenant data model and v1 is being built as single-tenant without tenant isolation, v2 will require a full data migration — that cost must be acknowledged, not hidden.
- **Non-goals that touch security or correctness require explicit justification.** Saying "rate limiting is a non-goal for this internal endpoint" is only acceptable if: (a) the endpoint is not publicly accessible; (b) there is a network-layer control (IP allowlist, VPC boundary); and (c) the business accepts the residual risk in writing. "Security feature X is a non-goal" must be justified, not assumed.
- **Empty endpoints, null fields, and placeholder permissions are scope violations.** If a feature is not in scope, its technical surface area must not exist. A placeholder `POST /admin/users` that returns `501 Not Implemented` is not a non-goal implementation — it is a security surface area and a test gap. Remove it entirely; add it only when the feature is actually in scope.
- **Non-goals interact with API versioning.** If v1 defines an API response shape, and v2 will add fields to that response, the v2 fields must not be included as `null` in the v1 response (they create implicit expectations and schema coupling). Use versioned API design: v2 is a new API version with the new fields; v1 response shape is immutable once released.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Non-goal: "Admin features" (no specific boundary) | Untestable; "admin features" is vague; reviewers cannot check | Non-goal: "User management CRUD (POST/PUT/DELETE /admin/users) — not in v1; these endpoints must not exist" |
| Nullable `subscription_tier` column added to `users` table "for v2" | Schema coupling to unreleased feature; DB migration required; field may be accidentally accessed | Remove column entirely from v1 schema; add in v2 migration when feature is in scope |
| Non-goal: "GDPR compliance" | GDPR is a legal obligation — cannot be a non-goal if PII is processed | Scope GDPR work into v1; it is not optional if PII is in scope |
| `POST /reports` returns 501 "coming soon" placeholder | Unimplemented endpoint is a security surface area | Remove endpoint entirely; add only in the sprint when reports feature is in scope |
| No exclusion checks in acceptance criteria | QA cannot verify non-goal was honored | Add explicit "verify X does NOT exist" checks to acceptance criteria |
| Non-goal deferred for 4 quarters without reassessment | Non-goals accumulate as permanent exclusions; system never becomes complete | Review deferred non-goals in quarterly planning; either promote to scope or close as permanent |

# Failure Modes

- "We're not building admin features in v1" is accepted as a non-goal without specifics — engineers add a user management modal "since the API was already there"; non-goal was too vague to enforce.
- GDPR right-to-erasure deferred as a non-goal — EU users request data deletion; legal cannot comply; regulatory fine.
- `nullable subscription_tier` column added to `users` table as "v2 preparation" — 18 months later, the v2 subscription feature is abandoned; column remains permanently nullable; new engineers treat it as a valid field and write code that silently branches on `null`.
- Non-goal boundary defined but no exclusion checks in acceptance criteria — QA tests only in-scope features; three out-of-scope endpoints are deployed to production because no test checked their absence.
- Deferred rate limiting on a "low-traffic internal endpoint" — endpoint exposed to partner API keys; partner misconfigures client; 50,000 requests/minute; service outage.
- v1 API design includes `nullable` fields reserved for v2 — v2 team treats nulls as "disabled"; third-party consumers treat nulls as "missing"; breaking behavior difference discovered at v2 launch.
- Non-goal: "No pagination in v1" — approved without a volume assumption — data grows to 50,000 records in 6 months; unparameterized query loads entire dataset; page load timeout; non-goal was not reviewed against growth projections.

# Output Contract

Return a scope boundary record with:

- `in_scope` (specific behaviors, actors, contexts, endpoints, UI elements, and data entities that are included in the current version)
- `out_of_scope` (specific non-goals with: what is excluded, deferred-to version/backlog-item, reason for deferral, forbidden placeholder artifacts)
- `version_boundary` (v1 contract: API shape, DB schema, permissions, UI committed; what is immutable once released; what must not change)
- `deferred_decisions` (decisions that cannot be made now; constraints current implementation must respect to not close the door on future decisions)
- `forbidden_assumptions` (specific technical artifacts — columns, endpoints, permissions, UI elements — that must not exist in the current implementation)
- `anti_scope_creep_checklist` (PR review checklist: check for out-of-scope endpoints, fields, migrations, permissions, feature flags)
- `acceptance_exclusions` (QA checks for each non-goal: "verify X does NOT exist / is NOT rendered / does NOT appear in response")
- `risk_acknowledgement` (for any deferred security/compliance/reliability work: explicit risk statement accepted by [owner] on [date])
- `escalation_triggers` (conditions that would require re-scoping: volume growth, regulatory change, customer commitment, dependency unblocked)

# Quality Gate

The scope boundary is complete only when:

1. Every non-goal is specific enough to be checked in a test or PR review (not vague categories).
2. Acceptance criteria include explicit exclusion checks for every non-goal.
3. Forbidden placeholder artifacts are listed (no nullable columns, stub endpoints, or reserved permission bits).
4. Deferred security, compliance, or reliability work is either justified with explicit risk acknowledgement or moved into scope.
5. v1 API and schema are designed to not block v2 non-goals from being implemented without breaking changes.
6. Every deferred decision has an explicit "must not assume X" constraint on the current implementation.
7. Non-goals are reviewed against existing commitments (customer, legal, security, platform SLA).
8. Risk acknowledgement is documented for any deferred OWASP Top 10 control or compliance requirement.

# Used By

- change-intake-compiler
- acceptance-criteria-builder
- task-dag-planner

# Handoff

Hand off to `requirement-clarification` for unknown requirements that block coding (not just deferred scope); `acceptance-criteria-builder` to write in-scope acceptance criteria with the exclusion checks derived from non-goals; `task-dag-planner` to sequence the in-scope work once boundaries are confirmed.

# Completion Criteria

The capability is complete when **every non-goal is stated as a specific, testable exclusion with a forbidden-artifacts list; acceptance criteria contain explicit "not present" verification for each non-goal; no deferred security or compliance work is silently excluded; and the v1 implementation is structurally compatible with v2 non-goals without breaking changes**.

# Used By

- change-intake-compiler
- task-dag-planner

# Handoff

Hand off to task-dag-planner for sequencing approved work or requirement-clarification when an exclusion may actually be a blocking decision.

# Completion Criteria

The capability is complete when scope boundaries are concrete enough to prevent future assumptions from silently entering the implementation.
