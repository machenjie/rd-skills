# Frontend Security Closure Gates

Use this Reference only for the named frontend-security-closure-gates decision.

## Decision Rules

- Review user and API content rendering, token storage, third-party scripts, CSP, and browser storage at their owning trust boundary.
- Keep authorization server-enforced.
- Sanitize unsafe HTML.
- Apply the security owner's credential-storage decision, including sensitivity, exposure, scope, expiry, and purge proof.
- Prevent sensitive data from leaking through the DOM or logs.
- Reject UI guards as authorization proof.
- For `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, or markdown, identify the final sink and interpretation boundary.
- Prove safe construction, contextual encoding, or inert rendering where it prevents hostile interpretation.
- Where untrusted content is interpreted as markup, prove the applicable sanitizer and URL policy.
- Exercise malicious content against the chosen mechanism, including URL bypasses where URLs are accepted.

Return the security gate decision, denied-path validation, and residual exposure.
