# Web Security Checklist

- Identify affected routes, endpoints, templates, cookies, redirects, uploads, and outbound requests.
- Review XSS and apply context-aware output encoding and content controls.
- Review CSRF for cookie-authenticated state-changing requests.
- Review SSRF for server-side URL fetches, webhooks, previews, and imports.
- Review SQL injection, command execution, and unsafe deserialization paths.
- Review open redirects and restrict redirect targets.
- Review upload size, type, storage, scanning, and serving controls.
- Review object-level access control for reads, writes, exports, and actions.
- Define tests or evidence for each applicable control.
