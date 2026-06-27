# Web Security Benchmarks And Patterns

Use this reference when a web security review needs benchmark depth or graph-memory-execution coupling beyond the loaded `SKILL.md` body. Keep the review route-specific: cite only benchmarks and patterns that apply to the changed route, template, fetch, upload, query, redirect, cookie, header, or authorization boundary.

## Benchmark Anchors

- **OWASP Top 10 2021:** A01 Broken Access Control, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, and A10 SSRF are the usual web review anchors.
- **OWASP ASVS 4.0:** use V4 for access control, V5 for input validation and output encoding, V7 for error handling/logging, V10 for malicious code, V12 for files/resources, V13 for APIs, and V14 for configuration.
- **CWE mapping:** CWE-79 XSS, CWE-89 SQL Injection, CWE-352 CSRF, CWE-918 SSRF, CWE-22 Path Traversal, CWE-434 Unrestricted Upload, CWE-502 Insecure Deserialization, and CWE-601 Open Redirect.
- **Protocol/browser references:** CSP Level 3 for script, object, base URI, and frame ancestor controls; RFC 6265bis SameSite cookies for CSRF reduction; CORS and `Origin` semantics for browser trust-boundary checks.
- **OWASP cheat sheets:** XSS Prevention, SQL Injection Prevention, CSRF Prevention, SSRF Prevention, File Upload, Deserialization, and Logging cheat sheets are implementation anchors, not release evidence by themselves.

## Exploit To Control Matrix

| Exploit | Required Control | Evidence Pattern |
| --- | --- | --- |
| XSS | Context-specific output encoding before render; CSP as defense in depth | Hostile render fixture, template/source path, and header artifact |
| CSRF | `SameSite` cookie policy, CSRF token where cookies authorize state change, and `Origin` validation | Cross-origin denied test plus cookie/header capture |
| SSRF | Parse, canonicalize, allowlist, block private/link-local/metadata ranges, revalidate redirects | Metadata URL denied test, redirect test, and egress policy trace |
| SQL/command injection | Parameterized query or argv-based command construction with no shell interpolation | Raw-query/command scan, malicious fixture, and log showing bound parameters |
| Path traversal/upload abuse | Canonical path containment, content-signature MIME validation, size limit, isolated non-executable storage | Traversal/upload fixtures, storage permission artifact, and malware lifecycle note |
| IDOR/function auth | Authentication, role/function check, and object ownership predicate on every protected route | Cross-user denied tests for read/write/export/action endpoints |
| Open redirect | Canonical redirect target and exact allowlist; no prefix, substring, or userinfo bypass | External-target denial fixture and allowed-target matrix |
| Insecure deserialization | Avoid object graph deserialization from untrusted input; use safe schema-bound formats | Crafted payload rejection test and dependency/framework configuration proof |

## Graph Memory Execution Coupling

- **Repository graph:** enumerate reachable routes, resolvers, controllers, templates, middleware, upload/fetch helpers, query builders, and authorization predicates. Same-pattern scans must cover sibling entry points that share helper APIs or route conventions.
- **Project memory:** treat prior reviews, scanner reports, generated docs, framework defaults, and remembered controls as leads. Accept them only after the current source graph, middleware order, and test freshness match the claim.
- **Execution trajectory:** record the final commands, manual procedures, reports, exit codes, reviewed payloads, and stale-evidence limits. A scanner pass is not evidence for object ownership, SSRF redirect behavior, or context-specific output encoding unless it exercised those paths.
- **Validation broker handoff:** when a route cannot be executed locally, provide the blocked command or missing environment, the unverified exploit classes, a substitute manual review artifact, and the owner for follow-up evidence.

## Evidence Depth Patterns

- Prefer exploit-to-validation maps over broad statements: each applicable exploit class needs a route/source boundary, control, test or scan, result, and residual risk.
- Keep false positives explicit: when an exploit is not applicable, state the reason, such as bearer-token-only API for CSRF or no server-side URL fetch for SSRF.
- Record what evidence proves and does not prove. Unit tests can prove local validation behavior, while browser/header captures prove deployed header shape; neither proves sibling routes unless scanned or tested.
- Preserve efficiency by loading deeper peer capabilities only for the active boundary: `input-validation`, `permission-boundary-modeling`, `authentication-security`, `dependency-vulnerability-scanning`, or `threat-modeling`.
