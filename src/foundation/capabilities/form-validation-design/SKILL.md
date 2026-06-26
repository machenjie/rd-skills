---
name: form-validation-design
description: Designs form validation with mandatory backend enforcement, frontend UX validation, async checks, duplicate-submit protection, and partial-failure recovery.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "34"
changeforge_version: 0.1.0
---

# Mission

Design form validation and submission behavior where **backend enforcement is absolute, frontend validation is a user-experience accelerator (never the security boundary), every submission is protected against duplication, every validation failure is field-precise and recoverable, and async validation eliminates race conditions** — so that both security and UX correctness are maintained across all clients, networks, and retry scenarios.

# When To Use

Use this capability when a change: adds a new form with field rules and submission behavior; modifies validation rules for existing fields; introduces async field checks (username availability, email format verification, IBAN validation); adds duplicate-submit protection; designs partial-failure recovery for bulk or multi-step forms; maps backend validation errors to field-level messages; or adds multi-step/wizard form flows with state persistence across steps.

# Do Not Use When

Do not use this capability to document form library configuration (React Hook Form, Formik) or UI component API usage — that is framework implementation, not form design. Do not use it for API input validation on endpoints that are not user-facing forms — use `dto-schema-design` and `controller-api-implementation` for those.

# Stage Fit

Use during experience-definition, implementation-planning, coding, review, and testing when a user-facing form has validation rules, async checks, submission side effects, duplicate-submit risk, partial failure, or recoverable backend errors. In planning, define authority, timing, state machine, security controls, error mapping, and test obligations before implementation. In coding/review, reject stale project-memory or repository-graph claims unless current source, schemas, tests, and validation output confirm the form contract. Hand off when the primary question is generic API schema, server controller implementation, request lifecycle/caching, full frontend test strategy, or security review.

# Non-Negotiable Rules

- **Backend validation is the only enforcement boundary.** Frontend validation may be bypassed via curl, browser devtools, native apps, or automated scripts. Every field rule, business constraint, and authorization check must be enforced in the backend regardless of what the frontend validates. Frontend validation = UX optimization only.
- **CSRF protection on every mutation form.** State-mutating form submissions (POST, PUT, PATCH, DELETE) must be protected against Cross-Site Request Forgery. Use: (1) `SameSite=Strict` or `SameSite=Lax` cookies for session tokens; (2) synchronizer token pattern (CSRF token in form/header + server-side verification); (3) double-submit cookie pattern as fallback. Do not rely on `Origin` or `Referer` header checking alone — they can be stripped by proxies.
- **Input validation uses allowlist, not blocklist.** Validate that input matches expected format (length, character set, type, range). Do not try to detect and strip dangerous input — allowlist what is valid; reject everything else. OWASP Input Validation Cheat Sheet: validate on the server using a validation library, not hand-rolled regex.
- **Idempotency key for every non-idempotent form submission.** Generate a UUID v4 idempotency key at form mount time. Include it in every submission request (header: `Idempotency-Key`). The server must deduplicate within a defined window (24 hours typical). This prevents duplicate charges, duplicate records, and duplicate side effects from network retries and double-clicks.
- **No stale async validation result accepted.** When a field triggers an async validation request (e.g., username availability check), the result must be invalidated if the field value changes after the request was issued. Use AbortController to cancel the in-flight request; accept only the response matching the current field value.
- **Validation errors must be field-precise and actionable.** Every error message must: name the specific field, state what was wrong (not just "invalid"), and state what is required. "Invalid input" is not an error message. WCAG 3.3.1: error messages must identify the item in error. WCAG 3.3.3: if known, provide a suggestion for correction.
- **Preserve user input across failures.** User-entered form data must not be discarded on validation error, network failure, or server error. Only discard on successful submission (unless the form is a one-time-use security operation). Preserve fields in component state; do not store sensitive data (passwords, payment details) in localStorage or sessionStorage.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Basic field contract | New or changed fields, required/optional rules, format, length, enum, range, or copy. | Backend authority, frontend UX timing, field-level errors, preservation. | Field list, backend schema/handler, timing rule, error map. | `input-validation`, `dto-schema-design` | Form library how-to. |
| Async field validation | Username/email availability, external verification, duplicate checks, or slow validation. | Cancellation, stale-result rejection, re-check on submit, rate/load limits. | Request key, AbortController/ignore policy, debounce, final server check. | `frontend-api-integration`, `interaction-state-modeling` | onChange request spam. |
| Side-effecting submit | Create/update/delete/pay/invite/import, irreversible action, or expensive mutation. | Idempotency, duplicate-submit defense, CSRF, backend dedup, durable outcome. | Idempotency key, CSRF method, state machine, retry policy, denied duplicate test. | `security-privacy-gate`, `idempotency-retry-design` | Button disable as only defense. |
| Server error mapping | Backend `violations[]`, problem details, conflict, authz, partial failure, or internal error. | Field/form/global mapping, safe user copy, preserved input, recovery action. | Error taxonomy, field path map, internal-message suppression, recovery state. | `error-code-design`, `interaction-state-modeling` | Raw backend messages. |
| Multi-step or bulk form | Wizard, draft, import, multi-item edit, partial success, resumable flow. | Step persistence, per-item status, retry failed only, no duplicate side effects. | Step state, item status map, retry scope, idempotency scope, cleanup owner. | `user-flow-modeling`, `frontend-testing` | All-or-nothing generic failure. |
| Security-sensitive form | Auth, MFA, account recovery, payment, admin, PII, destructive, or legal/financial submission. | Treat form as trust boundary; require server enforcement, CSRF, anti-enumeration, privacy. | Actor/data classification, abuse case, denied test, evidence limits. | `threat-modeling`, `security-privacy-gate` | Client-side assurance claims. |

# Industry Benchmarks

Anchor against OWASP Input Validation and CSRF guidance, HTML Constraint Validation API, mature schema validation libraries, WCAG 2.2 form criteria, RFC 7807/RFC 9457 Problem Details, idempotency-key practice, AbortController cancellation, debounce patterns, and explicit submission state machines. Keep this body focused on routing, authority, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed benchmark anchors, authority/timing matrices, state machine patterns, library baselines, graph/memory/trajectory coupling, and anti-patterns.

# Selection Rules

Select this capability when **form field validation contract and submission lifecycle** are the primary design concern. Adjacent routing:

- Prefer `dto-schema-design` when the primary concern is the shared data transfer schema between frontend and backend.
- Prefer `error-code-design` when designing the stable error code taxonomy returned by the backend.
- Prefer `idempotency-retry-design` when the primary concern is server-side deduplication implementation and retry policy.
- Prefer `frontend-api-integration` when the focus is the HTTP request/response lifecycle, loading states, and error handling in the frontend layer.
- Prefer `security-privacy-gate` for OWASP CSRF and injection security review.

# Proactive Professional Triggers

- **Signal:** validation is described as "frontend handles it", HTML attributes only, form-library rules only, or mobile/API clients are ignored. **Hidden risk:** invalid, unauthorized, or malicious data bypasses the UI and corrupts server state. **Required professional action:** require backend enforcement per rule and field. **Route to:** `input-validation`, `security-privacy-gate`. **Evidence required:** backend rule map and bypass test.
- **Signal:** async uniqueness or external validation accepts whichever response returns last. **Hidden risk:** stale valid state lets the user submit an unavailable or unauthorized value. **Required professional action:** require request key, cancellation/ignore policy, debounce, and final server re-check on submit. **Route to:** `frontend-api-integration`, `interaction-state-modeling`. **Evidence required:** stale-response test and submit-time conflict mapping.
- **Signal:** side-effecting submit relies only on disabled button, spinner, or client debounce. **Hidden risk:** double-click, retry, timeout, or back/forward navigation creates duplicate records or charges. **Required professional action:** require idempotency key, stable retry key, backend dedup window, and UI in-flight state. **Route to:** `idempotency-retry-design`, `quality-test-gate`. **Evidence required:** duplicate-submit test and retry evidence.
- **Signal:** backend validation errors are raw strings, stack traces, database messages, or unmapped problem details. **Hidden risk:** users cannot recover, accessibility fails, or internal schema/security details leak. **Required professional action:** define safe field/form/global error mapping and message ownership. **Route to:** `error-code-design`, `security-privacy-gate`. **Evidence required:** violations-to-field map and internal-error suppression test.
- **Signal:** multi-step, draft, or bulk form has no per-step/item state, preservation rule, or retry scope. **Hidden risk:** user data loss, duplicate side effects, or partial success hidden behind generic failure. **Required professional action:** define state persistence, per-item result, retry failed only, and idempotency scope. **Route to:** `user-flow-modeling`, `frontend-testing`. **Evidence required:** partial failure scenario and recovery test.
- **Signal:** repository graph, project memory, or prior agent trajectory says a form pattern already exists. **Hidden risk:** stale schema, old validation library, or previous repair path is copied into a new form. **Required professional action:** current-source-confirm fields, schema, tests, stories, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit.

# Risk Escalation Rules

Escalate when: the form performs a financial transaction, account deletion, or other irreversible operation (WCAG 3.3.4 Error Prevention required); the form handles authentication credentials (password, MFA, recovery codes); the form submits to a third-party payment processor (PCI DSS scope); the form can create duplicate records that are difficult to reconcile; or partial failure leaves the backend in an inconsistent state (e.g., order created but payment not captured).

# Critical Details

Every form is a security boundary. Precision failures:

- **Frontend-only validation bypassed.** Mobile app does not render the web form; developer hits the API directly with invalid `birthDate` value. Backend lacks validation; invalid date stored; calculation error in age-dependent pricing 3 months later. Backend validation is not optional even when frontend validation "covers it."
- **Stale async validation accepted.** User types `alice` (available). Request sent. User changes to `alice_smith`. First response arrives: `alice` available. Field marked valid. User submits `alice_smith` — which is not available. Server rejects with 409. Both requests should have been managed: cancel first on field change; re-check `alice_smith` on blur and on submit.
- **Double-submit creates duplicate charge.** User clicks "Pay $99" on slow connection. UI does not disable button. User clicks again. Two requests sent. Server processes both. No idempotency key. Two charges. Idempotency key + button disable + server-side dedup prevents this.
- **CSRF token missing on financial form.** A malicious site embeds `<form action="https://yourbank.com/transfer" method="POST">` in an iframe. The user's session cookie is sent by the browser. Without CSRF protection the transfer executes. `SameSite=Strict` cookie + synchronizer CSRF token prevents this.
- **Bulk form partial failure silent.** User uploads 100 line items. 80 succeed, 20 fail. Form shows generic "submission failed." User retries all 100. 80 duplicates created (if no idempotency), or 80 get 409 conflicts. Show per-item results; retry only failed items.
- **Error message exposes internal details.** Backend returns `{"error": "UNIQUE constraint failed: users.email"}`. Frontend displays this raw message to user. Exposes schema information. Map internal errors to user-facing messages: "This email is already registered."

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `required` HTML attribute as only validation | Bypassed by removing attribute in devtools; server accepts empty value |
| Async username check fires on every keystroke | 26 requests for "alice_smith" typed at normal speed; rate limit triggered |
| New Idempotency-Key generated on each network retry | Server sees different key each time; treats retry as new submission; duplicate charge |
| CSRF token skipped "because we use JWT" | JWT in Authorization header is XSS-vulnerable; CSRF still possible via cookie-based auth |
| Form cleared on validation error | User must re-enter all fields; rage-quit UX |
| Server returns raw DB error | `Column 'email' cannot be null`; schema leaked to user |
| Submit button re-enabled immediately after click | Double-click window still exists; protection only if server dedup present |
| Generic "Something went wrong" on 400 | User cannot identify which field to fix; support ticket created |

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 form validation selection, authority, evidence, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete form contract, submission lifecycle, validation timing, async check, or error mapping. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, timing/state matrices, library baselines, accessibility criteria, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording edits where the output contract and quality gate are enough.

# Failure Modes

- Frontend-only email format check bypassed; invalid email stored in DB; marketing email sending failure; CSV export breaks.
- Stale username availability check passes; submit accepted by frontend; server returns 409 conflict; user shown generic error with no field mapping; can't tell which field to fix.
- Double submit on slow connection creates two orders; customer charged twice; refund process required; reputation damage.
- CSRF attack transfers $500 from user account via malicious link; no CSRF token on banking form.
- Partial bulk import: 500 rows, 50 failed; no per-row status shown; user re-uploads all 500; 450 duplicates created.
- Password field cleared on failed login; user retyped password 5 times due to CapsLock; frustration; account lockout triggered.
- Internal SQL error message displayed to user; schema information disclosed; security finding in pentest.
- Multi-step wizard state lost on back-navigation; user must re-enter step 1 data; abandons checkout.

# Output Contract

Return a form validation contract with:

- `mode_selected` (basic field contract / async field validation / side-effecting submit / server error mapping / multi-step-bulk form / security-sensitive form)
- `source_evidence` (current form code, backend schema/handler, API error contract, tests, stories, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused form, schema, validator, error mapping, or test pattern)
- `fields` (name, type, required, validation rules, async check, error messages per constraint)
- `validation_authority` (per field: frontend-only / both / backend-only; reason)
- `validation_timing` (per field: onChange / onBlur / onSubmit / async; conditions)
- `async_checks` (trigger, debounce delay, AbortController usage, stale-result handling, re-check on submit)
- `submit_lifecycle` (state machine: idle → validating → submitting → success/error/recovery)
- `idempotency_key` (generation point; header name; server dedup window; behavior on retry)
- `csrf_protection` (method: SameSite cookie / synchronizer token / double-submit cookie; token placement)
- `duplicate_submit_defense` (button disable, loading state, idempotency key, server dedup)
- `error_mapping` (backend violations[] → field names; user-facing messages; never expose internal errors)
- `partial_failure_behavior` (per-item status; retry scope; data preservation)
- `field_preservation` (what is kept on error; what is cleared; sensitive field policy)
- `accessibility` (WCAG 3.3.1 error identification; 3.3.2 labels; 3.3.3 suggestions; 3.3.4 error prevention)
- `security_threats` (frontend bypass, CSRF, mass assignment, enumeration, duplicate side effect, sensitive field retention, raw error disclosure)
- `changed_form_to_validation_map` (each field, rule, async check, submit state, backend error, CSRF/idempotency control, and partial failure path mapped to validator/test or residual risk)
- `handoff_boundaries` (what belongs to API schema, backend validation, error taxonomy, frontend API integration, security review, frontend testing, or product/legal review)
- `tests` (bypass frontend validation test, double-submit test, stale async result test, CSRF protection test, partial failure recovery test, field preservation test)
- `evidence_limits` (what was not inspected or not run: real backend handlers, API schema, browser assistive tech, production race behavior, payment provider, legal copy, or full E2E flow)

# Evidence Contract

Close a form-validation-design output only when it names selected mode, current source evidence inspected, graph/memory/trajectory reuse judgment, backend authority for every rule, timing, async stale-result policy, submit state machine, CSRF/idempotency controls, error mapping, field preservation, accessibility, changed-form-to-validation map, handoff boundaries, residual risk, and evidence limits. A generic "validate the form" or "use client and server validation" statement is not sufficient evidence.

# Benchmark Coverage

Improved form validation contracts reject common weak patterns: frontend-only validation, onChange async request spam, stale async acceptance, disabled-button-only duplicate protection, regenerated idempotency keys on retry, raw backend error display, generic 400 messages, lost input after failure, inaccessible errors, and stale repository-memory claims about existing form patterns. Detailed benchmark anchors, authority/timing matrices, library baselines, and state patterns belong in references so the body stays efficient.

# Routing Coverage

Route here when form field authority, validation timing, async checks, submission state, duplicate-submit defense, backend error mapping, partial failure, or field preservation is primary. Hand off when the primary concern is generic trust-boundary validation (`input-validation`), DTO/schema shape (`dto-schema-design`), backend controller implementation (`controller-api-implementation`), HTTP lifecycle/caching (`frontend-api-integration`), frontend test plan (`frontend-testing`), or broad security review (`security-privacy-gate`).

# Quality Gate

The form design is complete only when:

1. Every field validation rule has a declared backend enforcement mechanism.
2. CSRF protection method specified and consistent with session mechanism.
3. Idempotency key strategy defined (generation point, header, server dedup window).
4. Async validation handles: debounce, AbortController cancellation, stale-result invalidation, re-check on submit.
5. Submit lifecycle state machine covers: validating, submitting, success, error, recovery states.
6. Double-submit defense covers: button disable + idempotency key (both required).
7. Backend error mapping defined: `violations[]` → field-level messages; internal details not exposed.
8. Partial failure behavior defined for any bulk or multi-item form.
9. WCAG 3.3.1–3.3.4 requirements addressed for applicable form types.
10. Test matrix covers: backend bypass attempt, double-submit, stale async, CSRF, partial failure.
11. Selected mode, source evidence, and graph/memory/trajectory reuse judgment are explicit.
12. Every field rule, async check, submit transition, backend error mapping, CSRF/idempotency control, and partial failure path maps to validation evidence or named residual risk.
13. Handoff boundaries and evidence limits are explicit so form-design evidence is not over-claimed as backend implementation, real browser/a11y validation, legal approval, or production race proof.

# Used By

- frontend-change-builder
- quality-test-gate

# Handoff

Hand off to `dto-schema-design` for field type and schema contract; `error-code-design` for stable error code taxonomy; `idempotency-retry-design` for server-side deduplication implementation; `frontend-testing` for form validation test coverage; `security-privacy-gate` for CSRF and injection review.

# Completion Criteria

The capability is complete when **every field has a backend-enforced validation rule, every submission has idempotency protection and CSRF defense, every async check is race-condition-free, every validation error is field-precise and user-actionable, every partial failure is recoverable, and user input is preserved across all failure modes** — with no frontend-only enforcement boundaries and no generic error messages that leave users without a recovery path.
