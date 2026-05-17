# Example Output

```markdown
## Form Validation Contract

Form:
- Invite user

Backend authority:
- Email format, uniqueness, domain allowlist, role eligibility, and tenant limit are enforced on submit.

Frontend UX validation:
- Email format is checked on blur.
- Role is required before submit.
- Domain warning is shown before submit but does not decide final acceptance.

Async validation:
- Email uniqueness check is cancelled when the email changes.
- Stale async responses are ignored.

Submit lifecycle:
- Submit disables the primary action while the request is in flight.
- Duplicate submit uses an idempotency key scoped to tenant and email.

Partial failure:
- If notification delivery fails after account creation, show created status and retry notification action.
```
