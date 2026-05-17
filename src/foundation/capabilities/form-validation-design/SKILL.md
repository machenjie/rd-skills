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

# Non-Negotiable Rules

- **Backend validation is the only enforcement boundary.** Frontend validation may be bypassed via curl, browser devtools, native apps, or automated scripts. Every field rule, business constraint, and authorization check must be enforced in the backend regardless of what the frontend validates. Frontend validation = UX optimization only.
- **CSRF protection on every mutation form.** State-mutating form submissions (POST, PUT, PATCH, DELETE) must be protected against Cross-Site Request Forgery. Use: (1) `SameSite=Strict` or `SameSite=Lax` cookies for session tokens; (2) synchronizer token pattern (CSRF token in form/header + server-side verification); (3) double-submit cookie pattern as fallback. Do not rely on `Origin` or `Referer` header checking alone — they can be stripped by proxies.
- **Input validation uses allowlist, not blocklist.** Validate that input matches expected format (length, character set, type, range). Do not try to detect and strip dangerous input — allowlist what is valid; reject everything else. OWASP Input Validation Cheat Sheet: validate on the server using a validation library, not hand-rolled regex.
- **Idempotency key for every non-idempotent form submission.** Generate a UUID v4 idempotency key at form mount time. Include it in every submission request (header: `Idempotency-Key`). The server must deduplicate within a defined window (24 hours typical). This prevents duplicate charges, duplicate records, and duplicate side effects from network retries and double-clicks.
- **No stale async validation result accepted.** When a field triggers an async validation request (e.g., username availability check), the result must be invalidated if the field value changes after the request was issued. Use AbortController to cancel the in-flight request; accept only the response matching the current field value.
- **Validation errors must be field-precise and actionable.** Every error message must: name the specific field, state what was wrong (not just "invalid"), and state what is required. "Invalid input" is not an error message. WCAG 3.3.1: error messages must identify the item in error. WCAG 3.3.3: if known, provide a suggestion for correction.
- **Preserve user input across failures.** User-entered form data must not be discarded on validation error, network failure, or server error. Only discard on successful submission (unless the form is a one-time-use security operation). Preserve fields in component state; do not store sensitive data (passwords, payment details) in localStorage or sessionStorage.

# Industry Benchmarks

Anchor against: **OWASP Input Validation Cheat Sheet** — allowlist validation; server-side enforcement mandatory; centralized validation library; avoid client-side-only validation for security. **OWASP CSRF Prevention Cheat Sheet** — `SameSite` cookie attribute; synchronizer token pattern; double-submit cookie pattern. **HTML5 Constraint Validation API** — `required`, `pattern`, `min`/`max`, `minlength`/`maxlength`, `type` attributes; `setCustomValidity(message)`; `checkValidity()`, `reportValidity()`; `invalid` event; `ValidityState` object. **Schema Validation Libraries** — Zod (TypeScript; parse-then-use; branded types); Yup (JS; async validation; transform); Valibot (lightweight; modular); Joi (Node.js; enterprise; async rules); Pydantic v2 (Python; strict mode; BaseModel); Jakarta Bean Validation 3.0 (Java; `@NotNull`, `@Size`, `@Pattern`, `@Valid` cascade). **WCAG 2.2** — 3.3.1 Error Identification (required for A): identify and describe each error in text; 3.3.2 Labels or Instructions (required for A): provide labels and instructions for user input; 3.3.3 Error Suggestion (required for AA): suggest correction when error known; 3.3.4 Error Prevention (required for AA): for legal, financial, data-submission forms: provide reversibility, check, or confirmation. **RFC 7807 / RFC 9457** — Problem Details for HTTP APIs; use `violations` array for field-level errors: `{"violations":[{"field":"email","constraint":"format","message":"Must be a valid email","rejectedValue":"user@"}]}`. **Idempotency-Key header** (Stripe, Square API pattern; IETF draft-ietf-httpapi-idempotency-key-header) — UUID v4 generated at form mount; server deduplicates within 24h; response cached for duplicate requests. **AbortController** (Web API) — cancel in-flight fetch requests when field value changes; prevents stale async validation acceptance. **Debounce pattern** — 300–500ms debounce on async validation triggers; avoids excessive server requests during typing. **State machine pattern** — form submission lifecycle modeled as explicit states: `idle → validating → submitting → success | error → recovery`; prevents undefined intermediate behavior.

### Validation Authority Table

| Rule type | Enforce in frontend? | Enforce in backend? | Notes |
| --- | --- | --- | --- |
| Required field | ✅ UX only | ✅ Mandatory | Server rejects empty |
| Field format (email, phone, URL) | ✅ UX only | ✅ Mandatory | Server uses allowlist regex or library |
| Field length (min/max chars) | ✅ UX only | ✅ Mandatory | Prevent DoS; DB column size |
| Allowed character set | ✅ UX only | ✅ Mandatory | Allowlist chars; reject others |
| Cross-field rules (password confirm) | ✅ UX only | ✅ Mandatory | Server re-derives if state-dependent |
| Business rules (balance >= charge) | ❌ Not reliable | ✅ Mandatory | Client state may be stale |
| Authorization (user owns record) | ❌ Never only | ✅ Mandatory | Frontend can be spoofed |
| Uniqueness (username taken) | ✅ Async preview | ✅ Mandatory on submit | Race condition: final check at submit |
| Financial calculations | ❌ Not trusted | ✅ Mandatory | Never trust client-side totals |

### Validation Timing Rules

```
Per-field validation timing (choose per rule type):

  onChange: ONLY for password strength indicator, character count display
            Do NOT use for format validation — too aggressive during typing
  
  onBlur:   Format validation, required checks, length checks
            Standard timing for most field-level validation
            Re-validate on blur after the field was corrected following submit attempt
  
  onSubmit: Cross-field rules, async uniqueness, authorization-dependent rules
            All rules validated again on submit regardless of prior per-field state

  Async validation (username, email availability):
    1. Trigger onBlur (not onChange)
    2. Debounce 300ms before firing request
    3. Show loading indicator on field during request
    4. Cancel in-flight request with AbortController if field changes before response
    5. Accept response only if current field value matches the value that was sent
    6. Clear async result if field value changes after result was received
    7. Re-run async check on submit even if prior check passed (final authority = server)

  After first submit attempt:
    Switch to "validate on change" mode for fields the user edits
    Provide immediate feedback as user corrects errors
```

### Submission State Machine

```
States: idle | validating | submitting | success | error | recovery

idle:
  User fills form
  Per-field validation runs on blur

validating (triggered by submit click):
  Run all synchronous frontend validations
  Run pending async checks
  If validation fails → show field errors → return to idle (do not submit)
  If validation passes → transition to submitting

submitting:
  Disable submit button immediately (prevent double-click)
  Show loading state
  Send Idempotency-Key header (UUID v4 generated at form mount)
  Do NOT regenerate Idempotency-Key on network retry (same key = server dedup)

success:
  Clear form (only for create flows) or update form with confirmed server values
  Show success confirmation
  Idempotency-Key expires after success; generate new key on next form mount

error:
  Network error: show retry prompt; preserve form data; do NOT disable retry
  Server validation error (400): map violations[] to fields; preserve data; allow correction
  Server conflict (409): show specific conflict message; do NOT silently overwrite
  Server error (500): show generic error; preserve data; allow retry

recovery (partial failure in bulk forms):
  Show per-item status: succeeded N / failed M
  Allow retry of failed items only
  Do not re-submit succeeded items (idempotency + DX)
  Preserve item data for failed items; allow correction before retry
```

# Selection Rules

Select this capability when **form field validation contract and submission lifecycle** are the primary design concern. Adjacent routing:

- Prefer `dto-schema-design` when the primary concern is the shared data transfer schema between frontend and backend.
- Prefer `error-code-design` when designing the stable error code taxonomy returned by the backend.
- Prefer `idempotency-retry-design` when the primary concern is server-side deduplication implementation and retry policy.
- Prefer `frontend-api-integration` when the focus is the HTTP request/response lifecycle, loading states, and error handling in the frontend layer.
- Prefer `security-privacy-gate` for OWASP CSRF and injection security review.

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
- `tests` (bypass frontend validation test, double-submit test, stale async result test, CSRF protection test, partial failure recovery test, field preservation test)

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

# Used By

- frontend-change-builder
- quality-test-gate

# Handoff

Hand off to `dto-schema-design` for field type and schema contract; `error-code-design` for stable error code taxonomy; `idempotency-retry-design` for server-side deduplication implementation; `frontend-testing` for form validation test coverage; `security-privacy-gate` for CSRF and injection review.

# Completion Criteria

The capability is complete when **every field has a backend-enforced validation rule, every submission has idempotency protection and CSRF defense, every async check is race-condition-free, every validation error is field-precise and user-actionable, every partial failure is recoverable, and user input is preserved across all failure modes** — with no frontend-only enforcement boundaries and no generic error messages that leave users without a recovery path.
