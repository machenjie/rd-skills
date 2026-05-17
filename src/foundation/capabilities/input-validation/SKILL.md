---
name: input-validation
description: Designs server-enforced validation for type, length, format, range, allowlist, ownership, and semantic constraints because client validation is insufficient.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "53"
changeforge_version: 0.1.0
---

# Mission

Define **server-enforced validation at every trust boundary** so malformed, hostile, unauthorized, or semantically invalid input is rejected before it can corrupt state, bypass authorization, or trigger unsafe processing — with allowlist-first design, canonicalization before security decisions, and safe error responses that help legitimate clients without exposing bypass paths.

# When To Use

Use this capability when a change accepts: HTTP request bodies, query parameters, path parameters, headers; file uploads; webhook payloads (signed or unsigned); form submissions; CLI arguments; environment configuration; AI tool call inputs; or any payload crossing a trust boundary from an external actor. Also required when adding new fields to existing endpoints that carry security or state-change meaning.

# Do Not Use When

Do not use this capability to validate internal in-process function call arguments in already-trusted contexts — that is type safety, not input validation. Do not rely on client-side validation alone; it is UI convenience only and provides zero security guarantee.

# Non-Negotiable Rules

- **Validate at the server trust boundary, not only the client.** Frontend validation is user experience assistance. The server must independently enforce all constraints because any client can be bypassed. No exception.
- **Allowlist is mandatory for string formats.** Define what is permitted (pattern, character set, max length). Attempting to blocklist dangerous characters is an arms race — encoding variants, Unicode normalization, and context-specific escaping defeat blocklists. Allowlist-first (OWASP ASVS V5.1.2).
- **Canonicalize before validating security-sensitive input.** URL-decode, Unicode-normalize (NFC), and trim input before checking against security patterns. `%2F` → `/`, `../` → path traversal; `\u202e` → bidirectional override. Validate against the canonical form. (OWASP ASVS V5.3.1).
- **Reject unknown fields — do not silently ignore them.** Mass assignment (also called over-posting) occurs when an unvalidated field maps to a privileged property (e.g., `role`, `isAdmin`, `price`). Either use an explicit allowlist of accepted fields (DTO schema), or reject requests containing extra fields. (CWE-915).
- **Validate identifiers for existence, ownership, and tenant scope.** A syntactically valid UUID `user_id` can belong to a different tenant. Every resource identifier must be checked: does it exist? does it belong to the authenticated caller or their tenant? is it in a permitted state? (OWASP ASVS V4.2.1 — IDOR).
- **File uploads require content-type validation beyond MIME header.** The `Content-Type` header is attacker-controlled. Validate file content using magic bytes (file signature). Restrict file size. Reject executable file types unless the use case requires them. Scan with antivirus for user-facing upload features. (OWASP ASVS V12.1).
- **Webhook payloads require signature verification before processing.** Never trust webhook payload content before verifying the HMAC signature using a constant-time comparison. (OWASP ASVS V1.5.3; Stripe signature verification; GitHub webhook secret).
- **Error responses must not expose validation bypass hints.** "Invalid email format" is safe. "Email must match regex `^[a-zA-Z0-9._%+\-]+@..."` teaches the attacker the exact pattern boundary. Return normalized error codes with human-readable messages appropriate for the error's sensitivity level. (OWASP ASVS V8.1.2).

# Industry Benchmarks

Anchor against: **OWASP ASVS V5 — Validation, Sanitization and Encoding** (Application Security Verification Standard): V5.1 Input Validation Requirements; V5.2 Sanitization Requirements; V5.3 Output Encoding/Escaping Requirements; V5.4 Memory/String/Unmanaged Code; V5.5 Deserialization Prevention. **OWASP Top 10:2021 A03 — Injection**: SQL injection, XSS, SSTI, LDAP injection, OS command injection; all preventable with allowlist validation and parameterized queries. **CWE-20** (Improper Input Validation) — #6 in CWE Top 25 Most Dangerous Software Weaknesses. **CWE-915** (Improperly Controlled Modification of Object Prototype / Mass Assignment). **CWE-434** (Unrestricted Upload of File with Dangerous Type). **Pydantic v2** (Python) — field validators, strict mode, model_validator for cross-field constraints; JSON schema generation. **Zod** (TypeScript/JavaScript) — schema-first; parse-don't-validate; `z.object({}).strict()` rejects extra fields; `z.string().regex().max()`; `superRefine` for async validation. **Joi** (Node.js) — `Joi.object().options({ allowUnknown: false })`; `Joi.string().alphanum().max(50)`. **Bean Validation (Jakarta)** — `@NotNull`, `@Size(max=255)`, `@Pattern(regexp=...)`, `@Valid` for nested; `@Validated` at controller. **express-validator** — middleware chain; `body('email').isEmail().normalizeEmail()`; `validationResult(req)`. **RFC 7807** — Problem Details for HTTP APIs: `type`, `title`, `status`, `detail`, `instance`; return validation errors as structured problem detail. **OWASP File Upload Cheat Sheet** — magic byte validation; filename sanitization; size limits; storage outside web root. **GitHub webhook signature verification** — `X-Hub-Signature-256`: `HMAC-SHA256(secret, body)`; constant-time comparison to prevent timing attacks.

### Validation Layer Responsibility Matrix

| Layer | What to validate | Example tools | What NOT to do here |
| --- | --- | --- | --- |
| API Controller / Route | Schema shape, type, required fields, max length, format, unknown fields | Zod, Pydantic, Bean Validation | Business rules, ownership, state transitions |
| Application Service | Ownership (does this resource belong to the caller?), tenant scope, state transition legality | Custom guard, repository lookup | HTTP transport concerns, response formatting |
| Domain Model | Business invariants, value object constraints, lifecycle rules | Value object constructors, domain exceptions | Persistence, HTTP, external I/O |
| Infrastructure | File magic bytes, webhook HMAC, external payload schemas | python-magic, crypto.timingSafeEqual | Business rules, user-facing error formatting |

### Validation Constraint Taxonomy

```
Every field at a trust boundary must declare:

Type:
  string | number | boolean | array | object | date | uuid | enum

Structural constraints:
  minLength / maxLength (strings)
  minimum / maximum (numbers)
  minItems / maxItems (arrays)
  required / optional / nullable

Format constraints (use allowlist regex):
  email:      /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/
  uuid:       /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  ISO 8601:   /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/
  slug:       /^[a-z0-9]+(?:-[a-z0-9]+)*$/ + maxLength: 63
  filename:   /^[a-zA-Z0-9_\-\.]+$/ + no path separators + maxLength: 255

Business constraints (Application Service):
  EXISTS: resource with this id exists
  OWNED: resource belongs to caller's tenant / account
  STATE: current state permits this transition
  QUOTA: caller has not exceeded rate limit or resource quota

Security-critical constraints:
  No path traversal (canonicalize → check against allowed base path)
  No null bytes (\x00) in string fields
  No control characters (strip or reject \r\n in header-like values)
  File type: magic bytes match ALLOWED_TYPES list (not Content-Type header)
  Webhook: HMAC-SHA256(secret, raw_body) == timingSafeEqual(header_sig)
```

### Anti-examples: Injection via Input Validation Failure

| Attack class | Missing validation | Prevention |
| --- | --- | --- |
| SQL injection | `WHERE name = '${input}'` (string concat) | Parameterized queries (never input in SQL string); validate type/format |
| XSS (stored) | `<div>{userContent}</div>` (unescaped) | Output encoding at render; allowlist HTML tags if rich text needed |
| Path traversal | `fs.readFile(dir + input)` | Canonicalize; confirm path within allowed base using `path.resolve()` |
| SSTI | `render(template_string=input)` | Never accept template strings from user input; use static templates only |
| Mass assignment | `User.update(req.body)` | Use DTO allowlist; reject unknown fields; never spread raw request body |
| File polyglot | `.jpg` file with PHP code in EXIF | Magic byte check; do not serve uploaded files with execution privileges |
| IDOR | `/api/orders/{id}` without ownership check | Validate `order.tenant_id == caller.tenant_id` before returning |

# Selection Rules

Select this capability when **trust boundary enforcement, schema validation, and security constraint design** are the primary concern. Adjacent routing:

- Prefer `web-security` when the primary concern is exploit-class attack surface review (injection, XSS, CSRF, SSRF at a system level).
- Prefer `api-contract-design` when the primary concern is external request/response contract design (OpenAPI schema, versioning).
- Prefer `dto-schema-design` when the primary concern is internal DTO shape and field naming conventions.
- Prefer `authentication-authorization` when the primary concern is identity verification and access control decisions.
- Prefer `form-validation-design` when the primary concern is frontend form UX validation timing and user feedback.

# Risk Escalation Rules

Escalate when input can affect: financial amounts or pricing; permission grants or role assignments; tenant or account scope boundaries; file system paths or command execution; SQL, template, or script construction; external API calls with user-controlled parameters; configuration values that alter system behavior; or privileged automation inputs (AI tool call parameters, webhook triggers, CI/CD pipeline inputs).

# Critical Details

Input validation is the first and most cost-effective line of defense across the entire OWASP Top 10. Precision failures:

- **Blocklist defeat via encoding.** Blocklisting `<script>` to prevent XSS. Attacker sends `%3Cscript%3E` or `\u003cscript\u003e`. URL decode or Unicode normalize first, then validate. Blocklists are always incomplete — use allowlists.
- **MIME type spoofing for file uploads.** File upload endpoint checks `Content-Type: image/jpeg`. Attacker sends a PHP webshell with `Content-Type: image/jpeg`. Content-Type is set by the client and cannot be trusted. Read the first 16 bytes (magic bytes): JPEG = `FF D8 FF`; PNG = `89 50 4E 47`. Reject anything that does not match the magic bytes for the allowed type list.
- **IDOR via missing ownership check.** GET `/api/invoices/12345` — invoice 12345 belongs to tenant B. Caller is authenticated as tenant A. API checks only "is authenticated" but not "is this your invoice." Returns tenant B's financial data. Fix: validate `invoice.tenant_id == request.user.tenant_id` in the application service, not the controller.
- **Mass assignment via ORM.** `user.update(request.body)` with an ORM that maps all body fields to model fields. Body includes `{"role": "admin"}`. ORM sets `user.role = "admin"`. Fix: use explicit DTO with only permitted fields; never pass raw request body to ORM update.
- **Webhook without signature verification.** Webhook endpoint at `/webhooks/payment` processes payload directly. Attacker sends a forged payment success event. System grants access without a real payment. Fix: verify `HMAC-SHA256(secret, raw_body)` using `crypto.timingSafeEqual()` before parsing payload.

# Failure Modes

- Frontend blocks invalid email format; API bypassed directly via curl; invalid email stored in database; downstream system fails.
- File upload accepts `.jpg` extension; magic bytes not checked; PHP webshell uploaded; remote code execution.
- IDOR: authenticated user queries another tenant's invoice via `/api/invoices/{id}`; ownership check missing; data breach.
- Mass assignment: PUT `/users/me` with `{"role":"admin"}` in body; ORM maps all fields; privilege escalation.
- Webhook endpoint processes forged payment success event; signature verification absent; user granted paid features without payment.
- SQL injection via unvalidated search parameter; string concatenation into query; full table dump.
- Path traversal: `GET /files?name=../../etc/passwd`; filename not canonicalized; file system contents leaked.
- Validation error response leaks regex pattern; attacker learns exact allowlist boundary; crafts valid-but-malicious input.

# Output Contract

Return an input validation contract with:

- `input_sources` (request body, query params, path params, headers, files, webhooks; trust level of each)
- `schema` (per field: type, required/optional, constraints: minLength, maxLength, pattern, enum, range)
- `unknown_field_handling` (reject with 400 / strip silently; rationale)
- `canonicalization` (URL decode, Unicode NFC normalize, trim; sequence: before validation)
- `ownership_checks` (identifier → existence check; → ownership check: field, relation, tenant binding)
- `state_transition_guards` (current state → permitted transitions; enforcement layer: application service)
- `file_validation` (allowed MIME types + magic bytes; max size; filename sanitization; storage location)
- `webhook_signature` (algorithm: HMAC-SHA256; header; comparison: timingSafeEqual; rejection on mismatch)
- `error_contract` (HTTP status; RFC 7807 problem detail; field path; message; what is NOT included in message)
- `security_constraints` (no path traversal; no null bytes; no control chars; injection-class rules)
- `tests` (valid input accepted; each constraint violation rejected; ownership failure; mass assignment attempt; file type spoof; webhook signature tamper)

# Quality Gate

The validation contract is complete only when:

1. Every input field has declared type, constraints, and allowlist format where applicable.
2. Unknown/extra fields are explicitly rejected (not silently accepted).
3. All input is canonicalized before security-sensitive pattern checks.
4. Ownership and tenant scope check defined for every resource identifier.
5. State transition guard defined for every status-changing operation.
6. File uploads validated via magic bytes, not Content-Type header alone.
7. Webhook payloads validated via HMAC signature with constant-time comparison.
8. Error responses return normalized codes — not regex patterns, stack traces, or internal field names.
9. Tests include: constraint boundary cases, ownership failures, mass assignment attempts, injection payloads, file type spoofs.
10. Validation enforced at server trust boundary; no "client validates so server skips" documentation.

# Used By

- security-privacy-gate
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `web-security` for system-level injection and exploit surface review; `api-contract-design` for OpenAPI schema contract and versioning; `authentication-authorization` for identity and access control; `form-validation-design` for frontend validation UX timing; `quality-test-gate` for test coverage gate.

# Completion Criteria

The capability is complete when **every field at every trust boundary has declared type, format, and business constraints; security-critical inputs are canonicalized before validation; identifiers are checked for ownership and scope; and no input validation concern is deferred to the client alone**.
