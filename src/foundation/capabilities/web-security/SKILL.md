---
name: web-security
description: Reviews web changes for XSS, CSRF, SSRF, SQL injection, RCE, open redirect, insecure deserialization, upload abuse, and broken access control.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "54"
changeforge_version: 0.1.0
---

# Mission

**Systematically review every web-facing change for the full taxonomy of exploit classes** — XSS, CSRF, SSRF, SQL injection, command injection, path traversal, open redirect, insecure deserialization, upload abuse, broken object-level authorization, and broken function-level authorization — ensuring that browser trust boundaries, server-side request risk, unsafe execution paths, and access control gaps are eliminated by design-time security controls rather than discovered through penetration testing or production incidents.

# When To Use

Use this capability when a change: adds or modifies web routes, REST or GraphQL APIs, URL parameters, or query string handling; renders user-controlled content to HTML, email, PDF, or other output formats; handles file uploads, file downloads, or file storage; performs server-side HTTP requests, URL fetches, or webhook outbound calls; adds or modifies cookie settings, CORS configuration, or `Content-Security-Policy` headers; constructs database queries, shell commands, file paths, or LDAP queries with any user-controlled input; adds or modifies redirect or forward behavior; deserializes untrusted data (JSON, XML, YAML, pickle, Java serialization); or modifies access control checks, authorization predicates, or permission gates.

# Do Not Use When

Do not use this capability to: replace `threat-modeling` for high-risk product changes that require full STRIDE analysis and adversarial scenario planning; replace `input-validation` for defining comprehensive boundary validation contracts; replace `authentication-security` for authentication lifecycle and session management design; or replace `permission-boundary-modeling` for object-level authorization enforcement design. This capability is the web exploit class review — route to those peers for deeper design.

# Stage Fit

Use during planning when new routes, browser controls, uploads, redirects, server-side fetches, templates, or protected object actions are introduced. Use during coding and review when exploit controls, framework defaults, middleware, headers, cookies, query construction, or file/fetch paths change. Use during testing and release when hostile payloads, IDOR cases, scan results, prior memory, repository graph-discovered entry points, or validation freshness decide whether release is blocked.

# Non-Negotiable Rules

- **Treat all user-controlled input as hostile until proven otherwise.** "User-controlled" includes: URL path parameters, query string values, HTTP headers (`Referer`, `X-Forwarded-For`, `Origin`, `Content-Type`), request body fields, file names, file content, cookie values, OAuth parameters, and any value that originates from a client. Sanitization or encoding is not an excuse for trusting unvalidated input — validation must occur at the system boundary before processing.
- **Context-aware output encoding is required for every context where user data is rendered.** The correct encoding is context-specific: HTML entity encoding for HTML body content; JavaScript string escaping for inline JS; attribute encoding for HTML attributes; URL encoding for URL parameters; CSS escaping for inline styles. A single "sanitize HTML" function does not cover all contexts. The wrong encoding for the rendering context is still an XSS vulnerability.
- **Authorization must be enforced server-side for every protected read, write, export, and action.** Client-side UI hiding (not showing a button, disabling an input, omitting a field from the response) is not authorization. Every API endpoint must independently verify: (a) is this request authenticated? (b) does the authenticated actor have the required role or permission? (c) does the authenticated actor own or have access to the specific object being requested? Checking (a) and (b) without (c) is IDOR (Insecure Direct Object Reference) — the most common access control vulnerability.
- **Server-side URL fetches require an allowlist of permitted destinations.** Any feature that fetches a URL constructed from user input (webhook configuration, URL preview, import from URL, image proxy) is SSRF-capable. Required controls: (a) parse and canonicalize scheme, host, port, and resolved addresses before fetching; (b) enforce exact allowlist matching for permitted domains or IP ranges, not prefix checks; (c) block loopback, RFC 1918 private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), link-local range (169.254.0.0/16), and metadata endpoints (AWS/GCP `169.254.169.254`); (d) use an egress proxy with domain enforcement where available; (e) revalidate every redirect destination before following; (f) fail closed on parse, DNS, redirect, and timeout failures; and (g) return/log reason codes without raw URL userinfo, query, fragment, token, key, signature, or secret values.
- **Parameterized queries are the only acceptable defense against SQL injection.** String concatenation into SQL queries — even with escaping — is insufficient because escaping functions have encoding edge cases and context-specific behavior. Use prepared statements with bound parameters in every database call. ORM query builders are acceptable only when verified that they emit parameterized queries and do not have raw-query escape hatches that are being used. No exceptions for "admin-only" endpoints — privilege does not change injection risk.
- **File uploads require: type validation, size limit, storage isolation, and malware scanning.** Required controls per upload endpoint: (a) validate MIME type from file content (not from `Content-Type` header or file extension — these are attacker-controlled); (b) enforce size limits at the HTTP layer, not after reading the full body; (c) store uploaded files in isolated storage outside the web root, with no execute permissions; (d) generate server-side storage keys — never use the original filename as the storage key or path; (e) scan for malware in the background before making the file accessible.
- **CSRF protection is required for all state-changing endpoints that use cookie-based sessions.** Modern `SameSite=Strict` or `SameSite=Lax` cookies reduce (but do not eliminate) CSRF risk. Required: `SameSite` attribute set on all session cookies; CSRF token validation for state-changing requests on endpoints with `SameSite=None` cookies; `Origin` header validation as secondary defense. APIs that use only `Authorization: Bearer` tokens (not cookies) are not CSRF-vulnerable — do not add CSRF tokens to stateless JWT APIs.
- **Current source evidence is mandatory.** Cite affected routes, handlers, templates, middleware, headers, cookies, fetch/upload code paths, authorization predicates, tests, scan results, repository graph, project memory with dates, and validation freshness. Treat old security memory as a lead until current source and exploit evidence confirm it.

# Industry Benchmarks

Anchor against: **OWASP Top 10 (2021)** — A01: Broken Access Control; A02: Cryptographic Failures; A03: Injection; A05: Security Misconfiguration; A06: Vulnerable Components; A07: Identification and Authentication Failures; A10: Server-Side Request Forgery. **OWASP ASVS (Application Security Verification Standard) v4.0** — V4 (Access Control), V5 (Validation), V13 (API), V14 (Config). **CWE-79 (XSS)**, **CWE-89 (SQL Injection)**, **CWE-352 (CSRF)**, **CWE-918 (SSRF)**, **CWE-22 (Path Traversal)**, **CWE-502 (Insecure Deserialization)**, **CWE-434 (Unrestricted Upload)**. **Content Security Policy Level 3 (W3C)** — `script-src`, `object-src`, `base-uri`, `frame-ancestors` directives for XSS mitigation. **SameSite Cookie attribute (RFC 6265bis)** — CSRF mitigation via `Strict`/`Lax`. **RFC 7231 / RFC 7235** — HTTP `Origin` header; `401` vs `403` semantics. **OWASP Cheat Sheet Series** — XSS Prevention, SQL Injection Prevention, CSRF Prevention, SSRF Prevention, File Upload, Deserialization cheat sheets.

# Web Exploit Class Review Matrix

| Exploit Class | Entry Vector | Server-Side Control | Client-Side / Browser Control | Test Evidence Required |
| --- | --- | --- | --- | --- |
| Stored XSS | User input persisted to DB, rendered in HTML | Context-aware output encoding; CSP `script-src` | CSP header; `HttpOnly` on session cookies | Inject `<script>alert(1)</script>`; verify rendered as text |
| Reflected XSS | URL param / query string rendered in response | Input not reflected without encoding; CSP | CSP header | Verify `?q=<img onerror=...>` is entity-encoded in output |
| CSRF | Cookie-session state-changing request forged | `SameSite` cookie; CSRF token validation | N/A | Send cross-origin POST; verify 403 |
| SQL Injection | User input in DB query | Parameterized query / prepared statement | N/A | `'; DROP TABLE --` in param; verify no DB error; verify log shows bound param |
| SSRF | User-controlled URL fetched server-side | URL allowlist; RFC 1918 block; no redirect follow | N/A | Submit `http://169.254.169.254/latest/meta-data/`; verify blocked |
| Path Traversal | User-controlled file path | Canonicalize path; validate within allowed root | N/A | Submit `../../etc/passwd`; verify 400/403 |
| Open Redirect | User-controlled redirect target | Allowlist of permitted redirect destinations | N/A | Submit `?next=https://evil.com`; verify blocked or sanitized |
| Upload Abuse | Malicious file content / name | MIME validation from content; size limit; storage outside web root | N/A | Upload `.php` renamed as `.jpg`; verify content-type check fails |
| Insecure Deserialization | Deserialized payload executes code | Never deserialize untrusted input to object graph; use safe formats | N/A | Submit crafted gadget chain payload; verify rejected |
| IDOR (Broken Object Auth) | Direct object reference via ID | Object-level ownership check on every read/write | N/A | Access another user's object by changing ID; verify 403/404 |
| Broken Function Auth | Direct API call without role | Function-level role check server-side | N/A | Call admin endpoint without admin role; verify 403 |

# SSRF Defense Decision Tree

```
Does this feature accept a URL from user input?
  NO → Not SSRF-capable; standard input validation applies
  YES →
    1. Parse the URL server-side before any fetch
       Is the scheme http or https? NO → Reject (block file://, gopher://, ftp://)
    2. Resolve the hostname to IP address BEFORE connecting
       Is it RFC 1918 private? (10.x, 172.16-31.x, 192.168.x) → Reject
       Is it link-local? (169.254.x.x — cloud metadata range) → Reject
       Is it loopback? (127.x.x.x, ::1) → Reject
    3. Is the resolved IP in the DNS allowlist?
       NO → Reject
       YES → Allow fetch; enforce timeout (max 5s); max response size limit
    4. Does the response contain a redirect?
       Redirect destination on allowlist? NO → Stop; do not follow
       YES → Validate destination IP again (re-validate, not cached)
    5. Log: reason code, allow/deny decision, requesting user ID, and normalized host/address only; never raw userinfo, query, fragment, token, key, signature, or secret values
```

# Selection Rules

Select this capability when **the primary risk is a web exploit class (XSS, CSRF, SSRF, injection, upload abuse, access control)** for a specific change. Route to `input-validation` for comprehensive boundary validation contract design. Route to `authentication-security` for session lifecycle, token management, and MFA. Route to `threat-modeling` for full adversarial scenario analysis of high-risk features. Route to `permission-boundary-modeling` for object-level and function-level authorization enforcement design. Route to `secret-configuration-security` for secret exposure risk.

# Proactive Professional Triggers

- **Signal:** route, resolver, controller, template, email/PDF rendering, Markdown/HTML rendering, redirect, upload, download, or server-side fetch code changes without a web exploit review. **Hidden risk:** XSS, CSRF, SSRF, open redirect, upload abuse, or object authorization gaps can enter through a non-obvious browser or HTTP boundary. **Required professional action:** enumerate affected entry points, classify exploit classes, and require hostile-case evidence before approval. **Route to:** `web-security`, `input-validation`, `permission-boundary-modeling`, and `quality-test-gate`. **Evidence required:** affected route/template/fetch/upload paths, exploit-class checklist, denied cases, and command or manual proof.
- **Signal:** project memory, old security review, scanner output, framework default, or generated docs claim a web control already exists. **Hidden risk:** stale memory can miss new routes, changed middleware ordering, disabled escaping, new cookie mode, or generated route drift. **Required professional action:** compare memory with current repository graph, source paths, middleware order, and test freshness before accepting the claim. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability. **Evidence required:** memory source/date, current graph delta, accepted/rejected claim, and stale evidence limit.
- **Signal:** user-controlled URL, path, filename, HTML/Markdown, query fragment, redirect target, cookie, header, or object ID reaches fetch, render, query, storage, or authorization code. **Hidden risk:** canonicalization gaps, context-mismatched encoding, SSRF, traversal, injection, IDOR, or unsafe diagnostics can survive normal happy-path tests. **Required professional action:** validate before use, encode for the exact sink, enforce object ownership, redact diagnostics, and add malicious payload evidence. **Route to:** `input-validation`, `threat-modeling`, `permission-boundary-modeling`, and `security-privacy-gate`. **Evidence required:** sink map, canonicalization/encoding rule, deny-before-use proof, safe log/error sample, and residual risk.
- **Signal:** cookie, CORS, CSP, CSRF, HSTS, frame, referrer, cache, or browser security header behavior changes. **Hidden risk:** a single misconfigured header can widen session theft, clickjacking, cross-origin access, or cached sensitive response exposure. **Required professional action:** classify browser trust boundary, preserve old protections, and test the new header/cookie behavior. **Route to:** `authentication-security`, `frontend-change-builder`, `backend-change-builder`, and this capability. **Evidence required:** before/after header or cookie diff, browser/client impact, security test, and rollback path.
- **Signal:** security fixes change only one route, one template, one query, one upload endpoint, or one redirect path. **Hidden risk:** same-pattern vulnerabilities remain in sibling endpoints or framework helpers. **Required professional action:** run same-pattern scan and regression map before closure. **Route to:** `agent-execution-discipline`, `regression-testing`, `security-privacy-gate`, and this capability. **Evidence required:** searched patterns, related occurrences, fixed/skipped rationale, regression test, and remaining owner.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 exploit-class routing, non-negotiable controls, triggers, and output requirements. Load [references/checklist.md](references/checklist.md) when reviewing concrete routes, templates, cookies, redirects, uploads, fetches, queries, or authorization checks. Use [examples/example-output.md](examples/example-output.md) only when the expected web security review shape is unclear. Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when source reachability, stale security memory, same-pattern scans, or test freshness determine approval. Route to deeper peer capabilities only for the selected primary boundary; do not load unrelated security references for a local exploit-class review.

# Risk Escalation Rules

Escalate to `security-privacy-gate` when: a change introduces server-side URL fetching without an egress allowlist (SSRF risk requiring architecture review); a change handles file uploads with server-side execution possible (RCE risk — requires security review before release); a change uses raw query string construction in database access (SQL injection risk — must block release until parameterized); an authentication or session change bypasses MFA or extends session lifetime without re-authentication for privileged actions; or an access control change removes or weakens an authorization check for a privileged endpoint.

# Critical Details

- **IDOR is the most under-reviewed access control vulnerability.** Developers routinely implement role checks (is the user an admin?) but miss object ownership checks (is this order owned by the requesting user?). Every endpoint that returns or modifies an object referenced by ID must explicitly verify that the authenticated user has permission for that specific object — not just the endpoint in general. The test for IDOR is: change the object ID in the request to another user's object; verify the response is 403 or 404, not the other user's data.
- **XSS in one context doesn't mean XSS is prevented in all contexts.** A template engine that auto-escapes HTML body content may not escape HTML attributes, JavaScript blocks, CSS properties, or URL parameters. A change that adds user content to a new rendering context (e.g., "we now include the user's display name in a `data-` attribute") may introduce XSS even if HTML body rendering is already protected. Every new rendering context requires a context-specific encoding review.
- **`Content-Security-Policy` is a defense-in-depth control, not a primary XSS defense.** CSP reduces the impact of successful XSS (e.g., prevents inline script execution) but does not prevent stored XSS from being injected. Output encoding is the primary control. CSP is a secondary mitigation layer. `unsafe-inline` in CSP script-src defeats the XSS mitigation entirely — do not use it. Use nonces or hashes for legitimate inline scripts.
- **File upload storage path generation must never be derived from the original filename.** The original filename is attacker-controlled. `path.join('/uploads', userFilename)` enables path traversal (`../../../etc/cron.d/attack`). Generate a UUID as the storage key server-side; store the original filename separately as metadata for display purposes only.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `{{ user.displayName }}` in Jinja2 with `autoescape=False` | Stored XSS: any `<script>` in display name executes in every visitor's browser | Enable `autoescape=True` globally; or use `{{ user.displayName \| e }}` per field |
| `SELECT * FROM orders WHERE id = '` + orderId + `'` | SQL injection: `orderId = "1' OR '1'='1"` returns all orders | `SELECT * FROM orders WHERE id = ?` with bound parameter |
| Server fetches user-provided webhook URL with no IP validation | SSRF: `http://169.254.169.254/latest/meta-data/iam/` leaks AWS credentials | URL allowlist; RFC 1918 block; block link-local; re-validate after DNS resolution |
| Admin endpoint checks `isLoggedIn` but not `isAdmin` | Function-level broken auth: any authenticated user can call admin action | `if (!user.isAuthenticated || !user.hasRole('admin')) return 403` |
| `/api/orders/:id` returns order without verifying ownership | IDOR: `GET /api/orders/12345` returns any user's order | `WHERE id = :id AND user_id = :authenticatedUserId` |
| File stored as `/uploads/${req.file.originalname}` | Path traversal + filename collision + storage predictability | `const storageKey = uuid(); store with metadata: { originalName, storageKey }` |
| CSP header: `script-src 'unsafe-inline'` | XSS mitigation defeated; any injected inline script executes | Use nonces: `script-src 'nonce-{random}'`; regenerate per request |

# Failure Modes

- Stored XSS in user display name field executes in admin dashboard; admin session hijacked.
- SSRF webhook feature fetches cloud metadata endpoint; AWS credentials exfiltrated via webhook response.
- SQL injection in search endpoint: `' UNION SELECT password FROM users --`; credentials exfiltrated.
- IDOR: changing `/api/orders/123` to `/api/orders/456` returns another customer's order and payment method.
- File upload: `.php` file renamed as `.jpg` passes MIME check; served from web root; remote code execution.
- Open redirect: `?next=https://evil.com` used in phishing campaign to harvest credentials after fake SSO.
- CSRF: bank transfer endpoint lacks `SameSite` + CSRF token; attacker iframe triggers transfer from victim's session.

# Output Contract

Return a web security review with:

- `mode_selected` (route/API review, rendering/XSS review, browser-control review, upload/download review, server-side fetch/SSRF review, injection/deserialization review, authorization/IDOR review, or bug-fix regression)
- `affected_routes` (endpoint paths and HTTP methods)
- `boundaries_inspected` (routes, handlers, templates/renderers, middleware, headers, cookies, CORS/CSP/CSRF config, redirects, uploads/downloads, fetches, queries, auth predicates, tests/scans, repository graph, project memory, and skipped boundaries with reason)
- `trust_boundaries` (where user-controlled data enters the system and which sink it reaches)
- `source_evidence` (current files, caller graph, framework defaults, middleware order, scanner output, prior review memory, test fixtures, and freshness)
- `exploit_class_checklist` (per exploit: applicable yes/no; control applied; test evidence)
- `authorization_checks` (per endpoint: authentication check; role check; object ownership check)
- `cookie_header_controls` (session cookie attributes; CSP directive; CORS policy)
- `upload_or_fetch_controls` (if applicable: MIME validation; size limit; storage strategy; SSRF defense)
- `query_construction_review` (parameterized confirmation for all DB/LDAP queries)
- `exploit_to_validation_map` (each applicable exploit class mapped to automated test, scanner, manual verification, same-pattern scan, or residual risk)
- `graph_memory_execution_validation` (accepted/rejected project memory, graph-discovered entry points, executed commands, stale evidence, and not-verified disclosures)
- `residual_risks` (unmitigated risks with justification)
- `release_blockers` (critical findings that must be remediated before release)
- `test_evidence_commands` (commands or test cases for each applicable exploit class)
- `evidence_limits` (what tests/scans/manual review prove, what environments/browsers/routes/payloads remain unproven, and who owns the residual risk)

# Quality Gate

The review is complete only when:

1. Mode, inspected boundaries, source evidence, graph-memory-execution validation, and evidence limits are recorded.
2. Every applicable exploit class has a documented control.
3. All database queries use parameterized statements — no string concatenation in queries.
4. Object-level ownership checks are verified for all endpoints that return or modify objects by ID.
5. File upload endpoints have content-based MIME validation, size limits, and isolated storage paths.
6. Server-side URL fetch endpoints have IP allowlisting and cloud metadata range blocking.
7. Session cookies have `HttpOnly`, `Secure`, and `SameSite` attributes appropriate to the session sensitivity.
8. CSP header does not contain `unsafe-inline` for `script-src`.
9. Test evidence exists for every applicable exploit class (automated test or manual verification record).
10. Same-pattern scan covers sibling routes/templates/queries/uploads/fetches when a concrete vulnerability or fix is present.
11. Security evidence is fresh after the final route, middleware, template, header, upload/fetch, query, or auth predicate change.
12. Residual risks are documented with explicit acceptance or escalation decision.
13. No release blocker is left open without a remediation plan and a follow-up ticket.

# Evidence Contract

Close a web security review only when the answer cites current source boundaries, exploit-class applicability, control placement, validation commands or manual proof, what evidence proves, what it does not prove, residual risk, and next gate. A scanner pass alone does not prove object-level authorization, context-specific encoding, SSRF redirect handling, upload lifecycle, or cookie/header behavior; missing current source inspection or stale memory blocks approval.

# Benchmark Coverage

OWASP, ASVS, CWE, CSP, SameSite, and cheat-sheet benchmarks calibrate risk and controls. Approval still requires route-specific evidence from the target code path: hostile payload tests, denied authorization cases, header/cookie inspection, same-pattern scan, or explicit not-verified disclosure with owner.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `input-validation`, `authentication-security`, `permission-boundary-modeling`, `threat-modeling`, `secret-configuration-security`, `dependency-vulnerability-scanning`, `frontend-testing`, `backend-change-builder`, `frontend-change-builder`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker`.

# Used By

- security-privacy-gate
- frontend-change-builder
- backend-change-builder

# Handoff

Hand off to `input-validation` for comprehensive boundary validation; `authentication-security` for session controls and MFA; `permission-boundary-modeling` for object-level authorization enforcement; `secret-configuration-security` for secret and credential exposure risk; `threat-modeling` for adversarial scenario analysis.

# Completion Criteria

The capability is complete when **every web exploit class applicable to the change has a documented server-side control and test evidence, every protected endpoint enforces object-level authorization, and no release blocker remains unresolved**.
