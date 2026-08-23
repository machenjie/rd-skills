# Logging Design Checklist

1. Trace the named operational question to one owning event boundary and consumer action.
2. Choose level, schema, fields, redaction, correlation, and sink from current policy.
3. Verify failure visibility, duplicate emission, cardinality, rate, retention, and sensitive-data behavior.
4. **Task mode:** apply the logging decision at the owning event boundary.
5. **Review mode:** judge every changed event path against safe-logging criteria.
6. Stop when event purpose, owner, or data classification is unproven.

## Detailed Verification And Handoff

- Select mode: no-log, diagnostic/error logging, security/access/audit logging, or hot-path signal design.
- Inspect current logger helpers, field names, trace context, redaction utilities, config sinks, and tests before adding or changing logs.
- Decide log type, owner layer, event boundary, level, structured fields, redaction, correlation, and cardinality controls.
- Separate audit, security, access, diagnostic, business event, integration, and lifecycle purposes.
- Block raw request body, raw webhook body, raw URL query, authorization header, cookie, token, password, signature, secret, and unapproved PII.
- Distinguish expected validation/404, retryable intermediate failure, fallback/degradation, and terminal failure levels.
- Prefer metrics, traces, sampling, aggregation, or DEBUG-only logs for hot paths.
- Map required fields, redaction, denial category, retry/fallback distinction, and trace propagation to tests or validation commands.
- Record current source, diff, and validation reuse only after current source confirms logger conventions.
- State what validation proves, what it does not prove, residual sink/retention/traffic risk, and recommended next step.
