---
name: requirement-clarification
description: Clarifies product-change requirements by separating blocking unknowns, non-blocking unknowns, assumptions, and safe assumptions before implementation begins.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "01"
changeforge_version: 0.1.0
---

# Mission

**Convert ambiguous change input into a decision-ready clarification record that classifies every unresolved question as blocking or non-blocking, names safe vs. explicit assumptions, and states whether implementation may proceed** — preventing teams from encoding hidden decisions into code when the right answer requires product, domain, security, legal, or operations authority.

# When To Use

Use this capability when: a request lacks enough specificity about desired behavior, current behavior, actors, acceptance criteria, data ownership, authorization model, or deployment constraints for a professional implementation path to begin; an incoming request contains conflicting signals (stakeholder A says X, stakeholder B says Y); a request touches an authorization boundary, data retention policy, financial flow, irreversible workflow, or compliance obligation and the expected behavior is unstated; or a "quick fix" request appears simple on the surface but has ambiguous edge cases that could affect data integrity, security, or user-visible behavior.

# Do Not Use When

Do not use this capability to: rewrite already-clear and well-scoped requirements (proceed to `requirement-structuring`); teach stakeholders how to write requirements (not a coaching tool); resolve domain authority questions unilaterally (the clarification record surfaces the question — it does not answer it for the authority owner); or delay implementation indefinitely on non-blocking unknowns (non-blocking unknowns must be isolated and deferred, not used as a gate).

# Non-Negotiable Rules

- **Classify every unresolved question as blocking or non-blocking before any implementation begins.** A blocking unknown is one whose answer could change: the data model, the API contract, the authorization boundary, the migration approach, the state machine, or the rollback plan. An unknown is non-blocking only if the implementation can be fully isolated from the unknown behind a configuration value, feature flag, copy change, instrumentation hook, or a clearly bounded follow-up work item. The default for any authorization, financial, compliance, or irreversibility unknown is blocking.
- **"We'll figure it out later" is not a non-blocking classification.** A question becomes non-blocking only when the safe default is explicit ("if unanswered, we implement X, which is reversible because Y") and that default is approved by the requester. An unanswered question that silently determines behavior is a hidden decision — it is blocking, even if the team wants to proceed.
- **Treat these categories as automatically blocking:** (1) Who owns this data and can read/write it? (authorization boundary); (2) What happens to existing data when this change deploys? (migration, backward compatibility); (3) What is the behavior when the user does X and system does Y concurrently? (concurrent state); (4) Is this reversible? What is the rollback if it is wrong? (irreversibility); (5) Does this change a payment, subscription, or financial record? (financial flow); (6) Does this create, modify, or delete a record that cannot be recreated? (data loss); (7) Does this change have a legal, regulatory, or compliance implication? (legal/compliance).
- **Separate four types of assumptions explicitly:** (A) Safe engineering assumptions — reversible, conventional in the existing system, testable, and not product-authority questions (e.g., "use snake_case for new columns, consistent with existing schema"). (B) Explicit stakeholder assumptions — things the stakeholder stated but are not verified against current system behavior (e.g., "stakeholder says users can only have one active subscription, but we have not verified this in production data"). (C) Unsafe assumptions rejected — things that would be convenient to assume but carry unacceptable risk (e.g., "assuming no user currently has NULL in this field before adding NOT NULL constraint"). (D) Required authority responses — questions that require a product, legal, security, or operations owner to answer before coding can proceed.
- **State the minimum safe implementation scope if coding may proceed with non-blocking unknowns.** "Proceed on X, defer Y" is not useful without bounding X precisely. The minimum safe scope states: exactly which parts of the request can be implemented without resolving the non-blocking unknowns, and exactly which parts must wait. This prevents scope creep where a developer implements Y "while they're in there" before the authority question for Y is answered.
- **Do not silently encode answers to blocking questions in implementation choices.** If the question "who can delete this record?" is blocking, the implementation must not proceed with a default choice like "only admins can delete" without that choice being explicitly approved. An implementation that embeds an unapproved authorization decision is a security risk, even if the developer's guess is reasonable. Blocking unknowns must surface as explicit decisions, not as implementation-time guesses.

# Industry Benchmarks

Anchor against: **IEEE Std 830 (Software Requirements Specifications)** — completeness, consistency, unambiguity, verifiability, and traceability as quality attributes for requirements. **Agile Definition of Ready (DoR)** — a story is "ready" when: acceptance criteria are defined, dependencies are identified, the team understands enough to estimate, and no blocking questions remain. A story that is not "ready" should not be pulled into a sprint. **RFC process (IETF)** — requirements expressed as MUST / SHOULD / MAY / MUST NOT / SHOULD NOT (RFC 2119); distinguishes normative from informative. **OWASP Application Security Verification Standard (ASVS)** — security requirements are as binding as functional requirements; authorization model must be explicit before implementation. **Product Discovery best practices (Continuous Discovery Habits, Teresa Torres)** — distinguish between "known knowns" (verified facts), "known unknowns" (identified gaps), and "unknown unknowns" (gaps not yet surfaced). The clarification process turns unknown unknowns into known unknowns.

### Blocking vs. Non-Blocking Classification Decision Tree

```
Is this unknown about authorization, financial flow, data loss, or compliance?
  YES → BLOCKING (requires authority response before coding)
  NO  → Continue

Could implementing a default answer invalidate the data model, API contract,
migration plan, or rollback plan?
  YES → BLOCKING
  NO  → Continue

Can the implementation be fully isolated from this unknown behind a
configuration value, feature flag, or clearly bounded follow-up?
  YES → NON-BLOCKING (with explicit safe default documented and approved)
  NO  → BLOCKING

Is the safe default reversible, conventional, testable, and not a
product-authority question?
  YES → Safe Engineering Assumption (proceed with documentation)
  NO  → BLOCKING (requires explicit approval of the default)
```

### Clarification Record Template

```
Request Summary: [1-2 sentence description of what is being requested]

Known Facts (verified against current system):
  - [Fact 1: source]
  - [Fact 2: source]

Blocking Unknowns (coding MUST NOT start until resolved):
  ID  | Question                      | Category       | Owner           | Decision Needed
  BU1 | Who can delete a payment?     | Authorization  | Product + Legal | Must approve user/admin/both
  BU2 | What happens to in-flight     | Migration/      | Engineering +   | Define behavior for orders
      | orders when status enum adds  | Backward compat | Product         | in state not in new enum
      | new value?                    |                |                 |

Non-Blocking Unknowns (can defer; isolated behind config/flag/follow-up):
  ID  | Question               | Safe Default        | Isolation Method    | Follow-up Owner
  NU1 | Exact error copy text  | [placeholder text]  | Copy key in i18n    | Product / UX
  NU2 | Sorting order for list | By created_at DESC  | Config param        | Product

Safe Engineering Assumptions (reversible, conventional, approved):
  - Use snake_case column names, consistent with existing schema
  - Return 404 for not-found (not 403), consistent with existing API

Explicit Stakeholder Assumptions (stated but not verified):
  - Stakeholder says "users can only have one active subscription" — not verified in production data

Unsafe Assumptions Rejected:
  - NOT assuming no NULLs in email column before adding NOT NULL constraint
    (must verify: SELECT COUNT(*) FROM users WHERE email IS NULL)

Proceed / Block Decision:
  STATUS: [BLOCK until BU1 and BU2 resolved] / [PROCEED on scope below]

Minimum Safe Coding Scope (if PROCEED):
  Can implement now: [specific work items that do not depend on blocking unknowns]
  Must wait: [specific work items that depend on BU1 or BU2]

Required Owner Responses:
  BU1 → [Owner name] by [date]
  BU2 → [Owner name] by [date]
```

# Selection Rules

Select this capability when **the primary problem is whether enough is known to proceed, or whether hidden decisions are embedded in an ambiguous request**. Route elsewhere when: the request is clear and well-scoped but needs professional structure (use `requirement-structuring`); the behavior is known but the done signal is weak (use `acceptance-standard-definition`); the authorization model needs detailed design (use `authentication-authorization`); the migration approach needs design (use `data-migration-design`).

# Risk Escalation Rules

Escalate immediately (do not attempt to classify as non-blocking) when: the unknown could cause data loss for existing user records (schema migration with potential data truncation or NULL introduction); the unknown involves a payment, subscription charge, or financial ledger record; the unknown involves a GDPR / CCPA / HIPAA / SOX compliance obligation that is unstated or unclear; the unknown involves an authorization model that currently exists in production and the change could expand access; or the unknown involves an external contract (partner API, legal agreement, SLA) that the implementation team does not have authority to interpret unilaterally.

# Critical Details

- **The most dangerous unknowns are the ones the team does not know they have.** A request for "add a delete button to the user profile page" contains at least five unspoken questions: Who can delete? (authorization) What happens to the user's data? (data retention/GDPR) Is this a soft delete or hard delete? (reversibility) What happens to related records? (referential integrity / cascade behavior) Is there a confirmation step? (UX/accidental deletion prevention). A clarification record surfaces these questions before implementation, not after.
- **Explicit stakeholder statements are not verified facts.** If a stakeholder says "users can only have one active subscription," this is a stakeholder assumption until verified by a database query. Implementing a uniqueness constraint based on an unverified stakeholder claim, without a query to confirm no existing violations, can cause a migration failure in production. Verify before constraining.
- **The clarification record is the handoff artifact between ambiguity and implementation.** It is not a meeting summary, not an email thread, not a verbal agreement. It is a written record that names every assumption, every blocking question, every deferred non-blocking question, and the approved minimum safe scope. It is referenced by the implementation PR, the test plan, and the release plan.
- **Non-blocking unknowns must be tracked as follow-up work items, not forgotten.** A non-blocking unknown that is deferred indefinitely becomes a hidden decision. The follow-up owner and expected resolution date must be recorded. If the follow-up is not resolved before the feature ships, the safe default becomes permanent — which may not be what the stakeholder intended.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Developer assumes "only admins can delete" without asking | Unauthorized authorization decision; may be wrong; security finding if too permissive or UX failure if too restrictive | Classify as blocking; request explicit product + security decision |
| "We'll figure out the migration behavior later" | Migration deployed without clear behavior for existing records; production data inconsistency | Classify migration behavior as blocking; define before deploying schema change |
| Non-blocking unknown "copy text" leaks into API response key name | Developer names the API field `errorMessage` based on placeholder copy; copy changes require API version change | Isolate copy in i18n key; API field name is a code decision independent of copy |
| Stakeholder says "no user has multiple subscriptions" → NOT NULL constraint added without verification | Production migration fails: 47 users have NULL subscriptions; rollback required | Run `SELECT COUNT(*) FROM subscriptions WHERE user_id IS NULL` before classifying as safe |
| Clarification record is an informal chat message | Not traceable; not referenced in PR; assumptions forgotten; disputed 3 months later | Written clarification record in the issue/ticket/PR with explicit blocking classification |
| All unknowns classified as non-blocking to avoid blocking the sprint | Blocking authorization question deferred; developer implements default; security review finds privilege escalation 6 weeks later | Strict application of blocking classification rules; authorization is always blocking |

# Failure Modes

- Authorization question classified as non-blocking; developer implements "admin-only" default; product intended "owner + admin"; wrong users blocked from their own data for 3 weeks.
- Migration behavior deferred as non-blocking; schema deployed; existing NULL records cause application errors at runtime; emergency migration required.
- Safe engineering assumption about column naming conflicts with an existing convention in a partner system that reads the column directly; breaking change discovered after deployment.
- Clarification record never written; verbal agreements about scope; three months later, dispute about what was agreed; no record to reference.
- Non-blocking unknown (display copy) allowed to influence API field naming; copy changes require API version bump.
- Financial flow question ("what happens to the charge if the order is cancelled mid-payment?") treated as non-blocking; developer implements no-op; financial records inconsistent; reconciliation failure.

# Output Contract

Return a clarification record with:

- `request_summary` (1-2 sentence neutral description of the request)
- `known_facts` (verified facts about current system behavior; source for each)
- `blocking_unknowns` (per unknown: ID, question, category, owner, decision needed)
- `non_blocking_unknowns` (per unknown: ID, question, safe default, isolation method, follow-up owner and date)
- `safe_engineering_assumptions` (reversible, conventional, testable, not authority questions)
- `explicit_stakeholder_assumptions` (stated by stakeholder; not yet verified against system)
- `unsafe_assumptions_rejected` (assumptions that would be convenient but carry unacceptable risk)
- `proceed_block_decision` (BLOCK / PROCEED; justification)
- `minimum_safe_coding_scope` (if PROCEED: exactly what can be implemented; what must wait)
- `required_owner_responses` (per blocking unknown: owner, expected date)

# Quality Gate

The clarification record is complete only when:

1. Every unresolved question is classified as blocking or non-blocking with explicit reasoning.
2. Authorization, financial, compliance, data-loss, and irreversibility unknowns are all classified blocking.
3. Non-blocking unknowns have a documented safe default that is approved and reversible.
4. Explicit stakeholder assumptions are separated from verified facts.
5. Unsafe assumptions are explicitly rejected with reasoning.
6. The proceed/block decision is unambiguous.
7. If proceeding: the minimum safe coding scope is bounded precisely.
8. Each blocking unknown has a named owner and expected resolution date.
9. The record is written (not verbal); traceable to the implementation PR and release record.
10. Non-blocking unknowns have a follow-up owner and will not be silently forgotten.

# Used By

- change-intake-compiler

# Handoff

Hand off to `requirement-structuring` once all blocking unknowns are resolved and coding may proceed; to `authentication-authorization` when the clarification surfaces an unresolved authorization model question; to the owning professional gate (security-privacy-gate, reliability-observability-gate, delivery-release-gate) when a blocking unknown concerns that gate's domain.

# Completion Criteria

The capability is complete when **ambiguity is fully classified, risk-bearing unknowns are blocked with named owners, safe assumptions are explicitly documented and approved, and the implementation path is either authorized with a bounded scope or deliberately paused with a resolution plan**.
