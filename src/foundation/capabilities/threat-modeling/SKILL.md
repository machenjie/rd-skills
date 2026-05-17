---
name: threat-modeling
description: Requires explicit threat models for high-risk changes by identifying assets, actors, boundaries, entry points, abuse cases, mitigations, and residual risk.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "52"
changeforge_version: 0.1.0
---

# Mission

**Identify security and abuse risks before implementation by constructing an explicit threat model that enumerates assets, actors (legitimate and adversarial), trust boundaries, entry points, data flows, abuse cases, mitigations, and residual risk** — so that every high-impact threat has a concrete implemented control, test, and monitoring signal, rather than a design note that gets implemented "later" and never does.

# When To Use

Use this capability when: a change adds a new public API endpoint, authentication mechanism, authorization rule, file upload handler, payment integration, or external service integration; a change accesses, stores, transmits, or processes sensitive data (PII, payment card data, credentials, health records, financial transactions); a change introduces administrative actions, tenant management, privilege escalation paths, or cross-tenant data access; a change modifies infrastructure boundaries (new VPC, new DNS record, new CDN configuration, new IAM policy); or an architecture review has flagged a security concern that must be formally modeled before the change proceeds.

# Do Not Use When

Do not use this capability as a substitute for implementing concrete security controls — a threat model that lists mitigations without implemented code, configuration, and tests is a paper document, not a defense. Do not use for purely cosmetic changes or internal refactors that do not touch trust boundaries, data access, or behavioral authorization logic.

# Non-Negotiable Rules

- **Enumerate assets explicitly.** An asset is any value the system must protect: user data (names, emails, addresses, health records), credentials (passwords, API keys, session tokens, OAuth codes), financial data (card numbers, bank accounts, transaction records), business confidential records (pricing, trade secrets, source code), system integrity (code execution, configuration, cryptographic keys). Every asset must have a classification: what category of data, who owns it, what regulation applies (GDPR, PCI-DSS, HIPAA, SOC 2).
- **Model both external attackers and legitimate users abusing allowed workflows.** A threat model that covers only "an external attacker tries to break in" misses the most common real-world incidents: a legitimate user who discovers that changing a URL parameter exposes another user's order; an internal employee who downloads all customer records because there is no rate limit or export audit; a partner API key that is shared across environments and inadvertently has production access. Insider threats and authorization abuse cases must be explicitly modeled.
- **Trust boundaries must be drawn at every layer where assumptions change.** A trust boundary exists wherever data moves from a less-trusted to a more-trusted context, or vice versa. Required boundaries to draw: (1) browser/mobile client → API gateway (public internet — no trust); (2) API gateway → backend service (internal network — partial trust, but validate input); (3) backend service → database (application layer — trust, but principle of least privilege); (4) backend service → third-party API (external — validate responses, handle failures); (5) admin UI → admin API (elevated privilege boundary — require re-authentication). Any call that crosses a trust boundary must be validated, authenticated, and authorized.
- **Every abuse case must map to a concrete mitigation with owner, implementation location, test, and monitoring signal.** A threat listed as "attacker may brute-force the login form" with mitigation "add rate limiting" is incomplete unless it specifies: which rate limiting implementation (e.g., token bucket at the API gateway layer, limit 10 attempts per 15 minutes per IP + per account), how it is configured (fail-open vs. fail-closed), how it is tested (automated test that simulates 11 rapid attempts and asserts 429 response), and what alert fires when the rate limit is triggered in production.
- **Residual risks must be accepted explicitly with owner, rationale, review date, and escalation trigger.** A risk that is accepted silently — by shipping without addressing it — is a liability. Every residual risk must have: the threat it represents, the likelihood and impact rating, the reason it is accepted (mitigating control is proportionate; threat is out-of-scope for the current change; compensating control exists elsewhere), the owner who accepted it (role, not individual), and a review date (residual risk acceptance expires; it must be re-evaluated if the threat landscape changes).
- **High-impact threats must have verification evidence before merge or release.** A "Critical" severity threat with a listed mitigation has zero value if the mitigation has not been implemented and tested. The threat model must track: mitigation status (designed/implemented/tested/monitoring deployed), the specific test that proves the control works (test ID or test case description), and the monitoring signal that will detect exploitation attempts in production.

# Industry Benchmarks

Anchor against: **STRIDE (Microsoft)** — Spoofing identity, Tampering with data, Repudiation, Information disclosure, Denial of service, Elevation of privilege — systematic threat enumeration per component and data flow. **PASTA (Process for Attack Simulation and Threat Analysis)** — risk-centric; business impact → technical risk mapping; attacker motivation analysis. **OWASP Threat Modeling Cheat Sheet** — asset identification, trust zones, data flow diagrams, abuse cases, STRIDE per element. **OWASP Top 10 (2021)** — A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A04 Insecure Design, A05 Security Misconfiguration, A06 Vulnerable Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A09 Security Logging and Monitoring Failures, A10 SSRF. **OWASP ASVS (Application Security Verification Standard)** — L1/L2/L3 verification requirements for authentication, session, access control, input validation, cryptography. **NIST SP 800-30 (Risk Assessment)** — likelihood × impact threat rating methodology. **CWE/CVSS** — vulnerability scoring and categorization. **Microsoft SDL (Security Development Lifecycle)** — threat model as required artifact in design phase. **GDPR Article 32 and 35 (DPIA)** — Data Protection Impact Assessment for high-risk processing; systematic description of processing; necessity and proportionality assessment; risk management.

### STRIDE Threat Enumeration Matrix

| Threat Category | STRIDE Code | Examples for Web/API Systems | Default Mitigation Direction |
| --- | --- | --- | --- |
| Spoofing | S | Forged JWT/session token; credential theft; API key impersonation | Authentication (JWT signature verification, MFA, short-lived tokens) |
| Tampering | T | SQL injection; mass assignment; CSRF; parameter manipulation | Input validation; parameterized queries; CSRF tokens; HMAC integrity |
| Repudiation | R | No audit log for admin action; log deletion by attacker | Immutable audit log; tamper-evident logging; digital signature for critical actions |
| Information Disclosure | I | IDOR (insecure direct object reference); verbose error messages; API returning excess fields | Authorization checks per resource; minimal error disclosure; field-level filtering |
| Denial of Service | D | Brute force; resource exhaustion; ReDoS; large file upload | Rate limiting; input size limits; regex safety; resource quotas |
| Elevation of Privilege | E | Horizontal privilege escalation (user A sees user B's data); vertical escalation (user becomes admin) | RBAC enforcement; ownership checks; re-authentication for privilege operations |

### Threat Model Record Template

```yaml
threat_id: "TM-007"
component: "File Upload API — POST /api/v1/documents"
threat_category: "Tampering + Elevation of Privilege"
threat_description: >
  An authenticated user uploads a file with a .php extension renamed as .pdf.
  The file is stored in a public S3 bucket accessible without authentication.
  If the server renders files from the bucket path, the PHP file may execute
  server-side or be served to other users as a malicious download.
actor: "Authenticated user (malicious)"
entry_point: "POST /api/v1/documents — multipart form upload"
assets_at_risk:
  - "Server-side code execution (system integrity)"
  - "Other users' browsers (malicious download delivery)"
trust_boundary_crossed: "Client → File Storage (public bucket)"
likelihood: "High"  # authenticated users have access; no extension filtering
impact: "Critical"  # code execution or malware distribution
mitigation:
  - control: "File type validation using magic bytes (not extension alone)"
    implementation: "src/uploads/validators/mime-validator.ts"
    status: "implemented"
    test: "T-089: upload .php renamed as .pdf; assert 422; assert file not stored"
  - control: "Store uploads in private bucket; serve via signed URLs with 1h expiry"
    implementation: "infra/s3-policy.tf — BucketPublicAccessBlock"
    status: "implemented"
    test: "T-090: assert unauthenticated GET on S3 URL returns 403"
  - control: "Strip executable permissions; store with .bin extension regardless of original"
    implementation: "src/uploads/processors/sanitizer.ts"
    status: "in-progress"
    test: "T-091: pending"
monitoring:
  - "Alert: upload request with executable MIME type → PagerDuty P1"
  - "Alert: S3 bucket ACL changed to public → CloudTrail → SNS"
residual_risk: "Low — after all three controls implemented"
residual_risk_owner: "security-lead"
residual_risk_review_date: "2025-01-01"
```

# Selection Rules

Select this capability when **the security risk shape of a change is unclear or known to be high impact**. Route to `web-security` for specific browser exploit classes (XSS, CSRF, CSP, clickjacking); `authentication-security` for identity lifecycle hardening (MFA, token rotation, account takeover); `input-validation` for boundary validation design; `secret-configuration-security` for secret exposure risk; `permission-boundary-modeling` for authorization model design.

# Risk Escalation Rules

Escalate immediately when: a threat is rated Critical (high likelihood × high impact) and no mitigation is implemented or planned; a threat can expose regulated personal data (GDPR Article 83 penalties); a threat can affect multiple tenants in a multi-tenant system (blast radius is all tenants); a threat involves a cryptographic failure (broken algorithm, key exposure, certificate misconfiguration); a threat enables server-side code execution or infrastructure privilege escalation; or a DPIA (Data Protection Impact Assessment) is required by GDPR Article 35 (new processing of biometric data, large-scale monitoring, systematic profiling).

# Critical Details

- **The most dangerous gap in threat modeling: missing insider and abuse-of-trust threats.** The assumption that threat actors are always external attackers misses: a customer support agent who can search all customer records without audit logging; a developer who can read production database credentials from the CI/CD system; a batch job with an overly broad IAM role that can access unrelated S3 buckets. Insider threat modeling requires examining every "trusted" actor that has elevated access and verifying that access is audited, minimal, time-bounded, and monitored.
- **Trust boundary crossings are where most injection vulnerabilities originate.** SQL injection, command injection, LDAP injection, XPath injection, and SSRF all originate at a trust boundary crossing where attacker-controlled input is used in a context (SQL query, shell command, network request) without proper validation or parameterization. Every trust boundary crossing must have explicit input validation design, and the design must specify the validation technique (parameterized queries — not input sanitization — for SQL; allowlist for network targets — not URL validation — for SSRF).
- **Threat model must be updated when the design changes.** A threat model completed at the start of a feature that is then significantly redesigned may no longer reflect the actual trust boundaries and attack surfaces. The threat model is a living artifact — it must be revised when: a new integration is added; a new actor is introduced; a new data flow crosses a trust boundary; or a "temporary" workaround becomes permanent.
- **Mitigations without tests do not exist.** A rate limiting control that is designed but not tested may be incorrectly configured (limit is 1000 per second instead of 10 per 15 minutes); may be applied to the wrong endpoint; or may be bypassed by a different request path. Every Critical and High severity mitigation must have a passing automated test before the threat is considered mitigated.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Threat model lists "encrypt sensitive data" without specifying algorithm, key management, or scope | Implemented with MD5 (broken); no key rotation; encrypts only 3 of 10 sensitive fields | Specify: AES-256-GCM; key stored in Vault; rotation every 90 days; field list explicit |
| Admin endpoint added with auth check: "users must be logged in" | Any authenticated user can invoke admin action (missing role/permission check) | RBAC check: `requireRole('admin')`; audit log on every call; re-auth for destructive actions |
| IDOR not modeled because "users are expected to know their own IDs" | User A discovers that changing `?orderId=123` to `?orderId=124` returns User B's order | Ownership check: `assert order.userId === request.user.id` before every resource return |
| Residual risk accepted as "we'll fix it in the next sprint" with no owner or date | Risk never reviewed; becomes permanent; discovered in penetration test 18 months later | Formal acceptance: owner = security-lead; review date = 30 days; JIRA ticket filed |
| Trust boundary not drawn at backend → third-party API | Third-party API returns malicious payload that is directly rendered in UI (XSS via API) | Validate and sanitize third-party API responses; treat as untrusted input |
| Threat model completed at design phase; not updated after architecture change | New file upload endpoint added; no threat model for upload attack surface | Threat model updated on each PR that adds entry points or trust boundary crossings |

# Failure Modes

- IDOR in new API endpoint: user ID in URL parameter not checked against session; data leak to any authenticated user.
- Admin action added with authentication but no authorization: any user can invoke admin endpoint.
- File upload without MIME validation: malicious file uploaded; served to other users.
- Rate limiting designed but not configured correctly: 10,000 brute-force attempts succeed overnight.
- JWT secret committed to repository: all sessions can be forged; all users compromised.
- SSRF via user-supplied URL: attacker reads AWS metadata endpoint; obtains EC2 instance credentials.

# Output Contract

Return a threat model with:

- `assets` (name, classification, owner, applicable regulation)
- `actors` (external attacker / insider / legitimate user abusing workflow / automated system)
- `trust_boundaries` (every boundary with incoming/outgoing trust levels)
- `entry_points` (every API endpoint, file upload, webhook, admin action, third-party callback)
- `data_flows` (data flow diagram with trust boundary crossings marked)
- `threats` (per threat: STRIDE category, description, actor, entry point, assets at risk, likelihood, impact, CVSS score if applicable)
- `mitigations` (per threat: control, implementation location, status, test ID)
- `monitoring` (per threat: detection signal, alert, incident response)
- `residual_risks` (per accepted risk: rationale, owner, review date, escalation trigger)
- `verification_evidence` (per Critical/High threat: test ID, passing status, monitoring deployed)

# Quality Gate

The threat model is complete only when:

1. All assets are classified with applicable regulation.
2. Both external attacker and insider/abuse-of-trust actors are modeled.
3. Every trust boundary is drawn and all crossings have validation design.
4. All threats have STRIDE category, likelihood, and impact rating.
5. All Critical and High threats have an implemented, tested mitigation.
6. All mitigations have test IDs with passing status.
7. All production entry points have a monitoring/detection signal.
8. All residual risks have owner, rationale, and review date.
9. DPIA flag is set if GDPR Article 35 processing applies.
10. Threat model is current with the final design (updated after any architecture change).

# Used By

- security-privacy-gate
- architecture-impact-reviewer

# Handoff

Hand off to `web-security` for browser exploit classes; `authentication-security` for identity lifecycle hardening; `input-validation` for boundary validation design; `secret-configuration-security` for secret exposure; `permission-boundary-modeling` for authorization model; `dependency-vulnerability-scanning` for third-party risk.

# Completion Criteria

The capability is complete when **every high-impact threat has a concrete implemented and tested mitigation or a formally accepted residual risk with owner and review date — and no Critical severity threat is accepted without explicit security-lead sign-off**.
