# Form Validation Design Benchmarks And Patterns

Load this reference when validation authority, async checks, duplicate submission, error mapping, or accessible recovery changes. Do not load it for copy-only edits or a backend validator with no form behavior.

## Authority And Timing

| Rule | Client role | Authoritative boundary and proof |
| --- | --- | --- |
| Required, format, range, enum | Give timely, accessible feedback. | Server/trust-boundary allowlist plus missing/malformed/boundary bypass cases. |
| Cross-field or business rule | Preview only when it helps recovery. | Service/domain recomputation with positive and denied cases. |
| Authorization | Never decide privileged access from form/client state. | Server object/tenant/action check and no-side-effect denial. |
| Uniqueness/availability | Async preview may reduce failed submits. | Durable constraint/final server check plus concurrent conflict case. |
| Financial/legal calculation | Display an estimate only if labeled. | Server/domain calculation, currency/jurisdiction owner, and confirmation evidence. |

Choose on-change, blur, submit, or post-first-submit feedback from error cost, latency, accessibility, and local convention. Debounce is a workload control with a measured/product-owned value, not a universal interval. At submit, re-run the checks applicable to the submitted values and current scope, and preserve a clear server authority.

## Async And Submission Failure

- Bind an async check to field + exact value + relevant scope; cancel it when supported and ignore any response whose identity no longer matches current input. Recheck at submit because a preview can become stale.
- Model idle, validating, submitting, pending/accepted, durable success, recoverable error, partial/unknown outcome, and cancellation only when they can occur. A disabled button prevents clicks, not replay or duplicate clients.
- For a non-idempotent mutation, preserve one logical operation key across retry only when the server owns dedupe/result replay; otherwise do not imply that a timeout cancelled the operation.
- When ambient cookies authenticate a browser mutation, derive the applicable CSRF control from the current session and deployment model.
- Verify that missing, invalid, and cross-site requests fail without mutation.
- Persist sensitive drafts in browser storage after confirming an explicit product need and state-management-design plus security-privacy-gate ownership. Minimize fields, bind user/tenant scope, version migrations, set expiry, and prove purge on submit/cancel/expiry/logout or identity switch.
- Map field violations, cross-field or form errors, stale conflicts, session or permission denial, dependency failure, and unexpected responses to distinct safe recovery when the contract distinguishes them. Raw regex, schema, constraint, stack, and provider text stay hidden from users.
- Preserve non-sensitive input after recoverable failure; clear secrets and regulated fields according to current policy. Bulk/partial retry targets only the failed subset unless the server contract is atomic.

## Accessibility, Evidence, And Limits

Errors need a programmatic field/group association, textual identification beyond color, focus or summary behavior for failed submit, status announcement for async outcomes, and retained context. Automated scans do not prove focus order, announcement timing, comprehensible copy, or server rejection.

Inspect the current form, server validator/domain rule, API error schema, session/CSRF mechanism, stories/tests, and reuse conventions. Client tests cannot prove backend authority, live race timing, provider outcome, or duplicate protection; backend tests cannot prove keyboard/screen-reader recovery.

Reject client-only validation, accepting the last async response, regenerating an idempotency key on retry, and raw backend messages. Also reject one generic form error, cleared input after ordinary validation failure, and happy-path-only proof for a stateful submission.

Route backend rule authority to `input-validation`, `business-rule-extraction`, or `permission-boundary-modeling`; API/error/idempotency semantics to `frontend-api-integration`, `error-code-design`, or `idempotency-retry-design`; UI state to `interaction-state-modeling`; and executable form/accessibility proof to `frontend-testing` or `quality-test-gate`.
