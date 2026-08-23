# Frontend Security Closure Gates

Use this Reference only for the named frontend-security-closure-gates decision.

## Decision Rules

- Review user and API content rendering, token storage, third-party scripts, CSP, and browser storage at their owning trust boundary.
- Keep authorization server-enforced, sanitize unsafe HTML, keep tokens out of browser storage, and prevent sensitive data from leaking through the DOM or logs.
- Reject UI guards as authorization proof and reject `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, or markdown rendering without sanitizer proof and a malicious-content fixture.

Return the security gate decision, denied-path validation, and residual exposure.
