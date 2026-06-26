# Example Output

```markdown
## Form Validation Contract

Mode selected:
- Side-effecting submit with async field validation and server error mapping.

Source evidence:
- Current invite form, invite API contract, backend validation schema, and existing component tests inspected.
- Repository graph showed a prior invite form pattern; accepted only after current schema and tests matched.
- No real browser screen-reader pass, production race/load test, or legal copy review verified in this planning pass.

Form:
- Invite user

Backend authority:
- Email format, uniqueness, domain allowlist, role eligibility, and tenant limit are enforced on submit.

Frontend UX validation:
- Email format is checked on blur.
- Role is required before submit.
- Domain warning is shown before submit but does not decide final acceptance.
- After the first submit attempt, edited fields revalidate as the user corrects them.

Async validation:
- Email uniqueness check is cancelled when the email changes.
- Stale async responses are ignored.
- Submit re-checks uniqueness through the server even if the preview passed.

Submit lifecycle:
- Submit disables the primary action while the request is in flight.
- Duplicate submit uses an idempotency key scoped to tenant, form instance, and email.
- Browser submission sends the configured CSRF token header.

Error mapping:
- Backend `violations[]` map to field messages.
- `409 email_taken` maps to the email field.
- Raw database or provider messages are never displayed.

Partial failure:
- If notification delivery fails after account creation, show created status and retry notification action.

Validation map:
- Frontend-bypass invalid email -> backend validation integration test.
- Stale async response -> component test with two email values and out-of-order responses.
- Duplicate submit -> idempotency test with same key.
- CSRF missing token -> denied mutation test.
- Backend `violations[]` -> field-level message test.
- Notification partial failure -> recovery-state test.

Handoff and limits:
- Hand off to input-validation for backend rule placement and frontend-testing for component/a11y assertions.
- This contract does not prove real browser assistive-tech output, production concurrency, payment/legal copy, or full E2E flow until those validators run.
```
