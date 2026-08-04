# Logging Error Handling Checklist

- Define error categories: user, system, third-party, and security.
- Map each category to client-safe responses and internal diagnostics.
- Include correlation IDs or trace context across requests, jobs, and external calls.
- Define structured log fields and severity levels.
- Redact secrets, credentials, tokens, sensitive payloads, and unnecessary personal data.
- Avoid raw internal exceptions in client responses.
- Avoid noisy error logs for expected validation or denial outcomes.
- Identify security-relevant actions and denials, keep diagnostic events separate, and either consume an accepted audit contract or hand audit semantics, integrity, retention, access, sink, and durability to `logging-design-gate` or `security-privacy-gate`.
- Include retryability and dependency context for third-party and system failures.
- Add tests for error mapping, redaction, correlation propagation, and expected denial behavior.
