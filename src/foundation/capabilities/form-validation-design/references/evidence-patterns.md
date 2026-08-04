# Form Validation Design Evidence Patterns

Use this reference when form-validation closure depends on validation freshness, backend-authority proof, async or duplicate-submit evidence, prior source or task evidence claims, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second form checklist.

## Form-Claim-To-Validation Map

| Form claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| For each changed form rule whose bypass could breach a trust boundary, authorization decision, business invariant, durable-state constraint, or public contract, identify the backend schema, handler, or policy that enforces it and label presentation-only or interaction-only rules as frontend-owned. | Field list, backend schema/handler path, bypass or denied-case test, and frontend UX-only note | Inspected rules are enforced outside the browser | All API clients or future fields remain covered |
| Frontend timing is safe | Change/blur/submit timing, rule authority, field preservation, and test or review artifact | The inspected form gives recoverable UX feedback | Backend authority or assistive technology behavior is fully proven |
| Async validation avoids stale success | Request key, debounce, cancellation or ignore rule, submit-time recheck, and delayed-response test | Older async responses cannot validate the current value in tested path | Provider race behavior or all latency distributions are covered |
| Duplicate submit is controlled | Idempotency key scope, server dedupe expectation, UI in-flight state, retry behavior, and duplicate-submit test | Inspected logical submission is protected from obvious duplicates | Server dedupe implementation is correct unless separately verified |
| CSRF/session protection is present | Session mechanism, CSRF method, token placement, denied or review evidence, and security owner | Inspected browser mutation has a declared CSRF control | XSS, full threat model, or deployed cookie policy is proven |
| Backend errors are safely mapped | Problem details or violations shape, field/form/global map, internal-message suppression, and test | Inspected errors become actionable safe messages | Legal copy, localization, or all backend exception paths are approved |
| Partial failure is recoverable | Per-item status, retry scope, idempotency scope, preservation rule, and partial-failure test | Inspected multi-item flow avoids duplicate retry of successes | All provider rollback or compensating actions are proven |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old form patterns, stories, screenshots, and prior validations as selectors until current form, backend schema, API error contract, tests, and validation output confirm them.
- Accept prior "form library covers validation", "backend errors already map", "idempotency exists", or "CSRF handled globally" claims only when current source and tests still match the changed form.
- Mark evidence stale after edits to field rules, backend schema, API error shape, async check, submit state, idempotency key, CSRF mechanism, tests, stories, reports, or generated artifacts.
- For each final-handoff claim about a field rule, async check, submit transition, backend error, applicable CSRF or idempotency control, or partial-failure path, name supporting evidence. Evidence is a command, test, report, owner review, or explicit not-run residual risk.

- If live form submission, payment/auth/admin mutation, or production config change, record environment, owner approval, stop condition, rollback plan, and redaction rule.
- If production telemetry or session/security review, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.
