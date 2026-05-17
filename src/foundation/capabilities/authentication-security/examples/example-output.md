# Example Output

```markdown
## Authentication Security Review

Flow: Browser session with refresh token rotation.

Token Lifecycle:
- Access token expires after 15 minutes.
- Refresh token rotates on each use and reuse revokes the session family.
- Logout revokes server-side refresh token record.

Session Controls:
- Session id rotates after login and MFA completion.
- Cookie is HttpOnly, Secure, SameSite=Lax, scoped to app domain.

Recovery:
- Password reset invalidates existing sessions for the account.

Tests:
- Reused refresh token is rejected and audited.
```
