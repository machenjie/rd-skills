# Authentication Security Checklist

- Identify identity provider, credential types, sessions, cookies, access tokens, and refresh tokens.
- Define issuance, expiration, refresh, rotation, revocation, and logout behavior.
- Prevent session fixation by rotating identifiers after login and privilege changes.
- Configure cookie HttpOnly, Secure, SameSite, path, domain, and lifetime settings.
- Define MFA, step-up, and account recovery controls for high-risk actions.
- Confirm credential and token storage uses approved secure mechanisms.
- Ensure secrets, tokens, and reset links are not logged or placed in URLs.
- Test replay, refresh reuse, logout, revocation, recovery, and privilege changes.
