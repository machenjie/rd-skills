# Logging Design Checklist

- Select mode: no-log, diagnostic/error logging, security/access/audit logging, or hot-path signal design.
- Inspect current logger helpers, field names, trace context, redaction utilities, config sinks, and tests before adding or changing logs.
- Decide log type, owner layer, event boundary, level, structured fields, redaction, correlation, and cardinality controls.
- Separate audit, security, access, diagnostic, business event, integration, and lifecycle purposes.
- Block raw request body, raw webhook body, raw URL query, authorization header, cookie, token, password, signature, secret, and unapproved PII.
- Distinguish expected validation/404, retryable intermediate failure, fallback/degradation, and terminal failure levels.
- Prefer metrics, traces, sampling, aggregation, or DEBUG-only logs for hot paths.
- Map required fields, redaction, denial category, retry/fallback distinction, and trace propagation to tests or validation commands.
- Record graph, memory, and execution trajectory reuse only after current source confirms logger conventions.
- State what validation proves, what it does not prove, residual sink/retention/traffic risk, and next gate.
