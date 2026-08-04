# Routing Examples

Each task has one path, one primary Professional Skill, zero to a few triggered Layer 3 Skills, and one Review Skill.

## Local Frontend Bug

Request: fix a null label in one known settings component, with an existing component test.

- Path: Direct Task.
- Primary: `frontend-change-builder`.
- Optional Layer 3: `frontend-testing` if behavior changes.
- Review: `ai-code-review-refactor`.
- Stop: owner, scope, or verification is not actually known.

## Login API Field

Request: add MFA enrollment status to a login response.

- Path: Analyzed Work because authentication and a public contract are involved.
- Analysis primary: `engineering-change-analysis`; select `api-contract-design` or `version-compatibility` only as triggered Layer 3 guidance. Use `data-api-contract-changer` as an analysis primary only for an explicit narrow artifact whose accepted Brief already supplies prerequisites.
- First slice: characterize the existing response and compatibility tests.
- Task primary: `backend-change-builder`.
- Triggered Layer 3: API contract, authentication/authorization, contract testing, version compatibility.
- Review: security-oriented review plus combined diff review when risk warrants it.

## Checkout Form States

Request: add validation, submitting, and failed-save states to an address form.

- Path: Direct only if the component owner, state acceptance, and targeted test are explicit; otherwise Analysis.
- Primary: `frontend-change-builder`.
- Triggered Layer 3: form validation, interaction state, accessibility/design-system rules as applicable.
- Review: `ai-code-review-refactor` or an experience-focused review assignment.

## Database Migration and API Compatibility

Request: split a field without breaking existing clients.

- Path: Analyzed Work.
- Analysis primary: `data-api-contract-changer`.
- First slice: map readers/writers and prove an expand/contract compatibility seam.
- Task DAG: schema expansion, dual read/write application change, backfill, contract cleanup, release sequencing when these are genuinely separate.
- Write policy: serialize shared migration and schema surfaces.
- Review: data, reliability, and release perspectives on the combined diff.

## High-Risk Payment Authorization

Request: authorize wallet-based subscription payments through an AI-assisted flow.

- Path: Analyzed Work with an explicit user-owned approval/authority boundary.
- Analysis primary: `security-privacy-gate` or `domain-impact-modeler`, based on the dominant decision.
- Triggered Layer 3: threat modeling, permission boundaries, idempotency, transaction consistency, payment and wallet domain rules.
- Review: separate security, payment, reliability, and release review assignments as justified by concrete risk.
- Stop: unclear human authorization, key custody, irreversible transfer, reconciliation, or production authority.

## Completion Claim Without Evidence

Request: a fix is reported done, but no current validation result exists.

- Path: Validation or Repair.
- Primary: `quality-test-gate`.
- Action: inspect the current diff, select targeted validation, and run it after the latest material edit.
- Review: actual changed files and proof limits.
- Output: commands, results, unverified scope, residual risk, and next step.

## Repeated Failure

Request: the same attempted fix failed twice.

- Path: Diagnosis through analysis.
- Primary: `engineering-change-analysis`.
- Required output: verified cause or explicitly eliminated hypotheses, same-pattern scan, and a new evidence-driven executable slice.
- Stop: do not repeat the same path without new evidence.
