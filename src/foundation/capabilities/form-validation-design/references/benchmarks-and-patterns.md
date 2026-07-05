# Form Validation Design Benchmarks And Patterns

Use this reference when form-validation-design output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, authority, evidence, output contract, and quality gates.

## Benchmark Anchors

- OWASP Input Validation Cheat Sheet and OWASP ASVS V5: server-side allowlist validation at trust boundaries.
- OWASP CSRF Prevention Cheat Sheet: SameSite, synchronizer token, and double-submit cookie controls for browser mutations.
- HTML Constraint Validation API: `required`, `pattern`, `min`, `max`, `minlength`, `maxlength`, `setCustomValidity`, `checkValidity`, and `ValidityState`.
- Schema validation libraries: Zod, Valibot, Yup, Joi, Pydantic v2 strict mode, and Jakarta Bean Validation.
- WCAG 2.2: 3.3.1 Error Identification, 3.3.2 Labels or Instructions, 3.3.3 Error Suggestion, and 3.3.4 Error Prevention.
- RFC 7807 and RFC 9457 Problem Details: stable problem shape and field-level violations.
- Idempotency-Key practice: stable key across retry and server deduplication window for non-idempotent mutations.
- AbortController and request-key comparison: cancel or ignore stale async field validation responses.
- Debounce pattern: commonly 300-500 ms for expensive async checks, usually after blur or after first submit attempt.
- Explicit state machines: idle, validating, submitting, success, error, and recovery states prevent impossible form behavior.

## Validation Authority Matrix

| Rule type | Frontend role | Backend role | Evidence |
| --- | --- | --- | --- |
| Required field | UX feedback only. | Mandatory rejection. | Backend schema/handler and bypass test. |
| Format, length, range, enum | UX feedback only. | Mandatory allowlist/range enforcement. | Boundary tests. |
| Cross-field rule | UX feedback only. | Mandatory recomputation. | Cross-field server test. |
| Business rule | Advisory only if shown. | Mandatory source of truth. | Service/domain test. |
| Authorization | Never authoritative. | Mandatory object/tenant check. | Denied-case test. |
| Uniqueness | Async preview. | Mandatory final check on submit. | Race/conflict test. |
| Financial or legal calculation | Never trusted. | Mandatory server calculation and confirmation. | Calculation and confirmation evidence. |
| Sensitive-field storage | Never localStorage/sessionStorage. | Store only allowed durable fields. | Storage inspection or not-verified limit. |

## Validation Timing Pattern

```text
onChange:
  - Character count, strength meter, or after-submit correction feedback.
  - Avoid full format validation while the user is still typing unless product policy requires it.

onBlur:
  - Common timing for required, format, length, and async availability preview.
  - Debounce before expensive async checks.

onSubmit:
  - Run all frontend checks again.
  - Re-run async uniqueness and authorization-dependent checks through the server.
  - Server remains final authority.

after first submit attempt:
  - Revalidate edited fields promptly so users can recover without repeated submit clicks.
```

## Async Validation Pattern

| Step | Required behavior | Evidence |
| --- | --- | --- |
| Trigger | Usually blur or after submit attempt; avoid keystroke spam. | Trigger rule in contract. |
| Debounce | Bound expensive checks, commonly 300-500 ms. | Timing decision or product exception. |
| Request key | Bind request to field name and value sent. | Request-key design. |
| Cancellation | Abort in-flight request when value changes when supported. | AbortController or equivalent. |
| Stale response | Accept only if current value still equals requested value. | Stale-response test. |
| Submit check | Re-check on submit even if preview passed. | Submit-time server validation. |
| Error mapping | Conflict or unavailable maps to the field, not generic form error. | 409/violations mapping test. |

## Submission State Machine

```text
idle
  -> validating
  -> submitting
  -> success | error | recovery
```

Rules:

- `validating` runs synchronous frontend checks and awaits needed async checks before submission.
- `submitting` disables or guards the submit action and sends the stable idempotency key for non-idempotent operations.
- `success` means durable server confirmation, not merely request accepted unless the product explicitly has an accepted/pending state.
- `error` preserves user input and maps validation, conflict, network, permission, and server failures to recoverable actions.
- `recovery` is required for partial success, bulk forms, and multi-step flows where retry scope matters.

## Error Mapping Pattern

| Backend signal | User mapping | Must not expose | Test |
| --- | --- | --- | --- |
| 400 with `violations[]` | Field-level messages near fields. | Raw regex, schema, stack traces. | Field mapping test. |
| 409 conflict | Field or form conflict with next action. | Internal constraint names. | Conflict test. |
| 403/401 | Permission or session recovery path. | Existence of unauthorized resource. | Denied state test. |
| 422 semantic failure | Specific business-rule message. | Implementation internals. | Semantic error test. |
| 5xx or network error | Generic retry/later message; preserve input. | Stack trace, SQL, provider payload. | Preservation/retry test. |
| Partial failure | Per-item succeeded/failed state and retry failed only. | All-or-nothing ambiguity. | Partial retry test. |

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current form, backend handler/schema, API error contract, tests, and stories were inspected. | Graph proximity is used as proof that validation or tests exist. |
| Project memory | Prior form pattern has owner, timestamp, unchanged source path, and matching framework/schema version. | Memory predates validation library, backend error contract, tenancy, or accessibility change. |
| Execution trajectory | Validation ran after the final material edit and covered changed form paths. | Evidence is stale, partial, or from a different form/framework. |
| Backend schema | Current server validator or contract is inspected. | Client DTO or form library rule is treated as backend proof. |
| Accessibility evidence | Error labels, focus, live-region/status behavior are inspected or tested. | Visual error copy alone is treated as screen-reader proof. |

## Review Questions

1. Which fields exist, and what business/security rule does each enforce?
2. Which rules are UX-only and which rules are server-authoritative?
3. Which async checks can return stale, and how is staleness rejected?
4. Which operation can duplicate side effects, and what is the idempotency scope?
5. Which CSRF/session mechanism protects browser-based mutations?
6. Which backend errors map to field, form, global, or recovery messages?
7. Which fields are preserved, and which sensitive fields must be cleared?
8. Which partial or multi-step failures can occur, and what can safely retry?
9. Which WCAG form criteria require explicit proof?
10. Which source, graph, memory, trajectory, browser, or backend evidence remains unverified?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| HTML `required` or form-library schema as the only validation. | Bypassed by non-browser clients. | Server validation for every rule. |
| Async availability check accepts last response received. | Stale response can mark a changed value valid. | Abort/ignore stale responses and re-check on submit. |
| Disabled button is the only duplicate-submit defense. | Retry, timeout, or multiple clients can still duplicate side effects. | Stable idempotency key plus server dedup. |
| Idempotency key regenerated on retry. | Server sees retry as a new mutation. | Reuse same key for the logical submission. |
| Raw backend message displayed. | Leaks schema/security internals and blocks recovery. | Map to safe field/form/global message. |
| Generic 400 error for field failures. | User cannot fix the correct field. | Use field path and actionable copy. |
| Clearing all input on validation failure. | Data loss and abandonment. | Preserve non-sensitive user input. |
| Bulk retry resubmits succeeded items. | Duplicates or conflicts. | Retry failed items only. |
| Project memory copied without current source check. | Stale pattern becomes new defect. | Inspect current source/tests/schema before reuse. |
