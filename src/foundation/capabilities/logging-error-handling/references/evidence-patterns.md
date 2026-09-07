# Logging Error Evidence Patterns

- **Prove failure reconstruction and redaction.** Exercise representative normal, denied, retry, timeout, cancellation, partial, and unexpected paths, then verify correlation, terminal classification, sensitive-field handling, and proof limits.

Use this evidence-pattern only when redaction, correlation, audit, error-mapping, or freshness claims need proof beyond current fixtures and captures.

## Evidence Map

- **Client safety:** bind mapper, response fixture, stable code/type, correlation, and negative stack/SQL/class/provider/raw-exception assertions; name wrapper/proxy/client limits.
- **Sensitive fields:** bind call site, allowlist, representative log, and forbidden password/token/cookie/authorization/card/body/query assertions; name processor/dynamic-shape limits.
- **Correlation:** bind entry middleware, outbound injection, queue/job metadata, and captured trace/correlation; name untested hops/retries/collector config.
- **Expected failures:** bind taxonomy, level policy, fixtures, and alert outcome for validation, absence, conflict, denial and rate limit; name production routing/volume limits.
- **Audit handoff:** bind diagnostic boundary, accepted audit owner, required actor/action/resource/outcome, and unresolved integrity/retention/access/sink/durability.
- **Protected-record limit:** when its evidence is absent, do not claim the protected record exists.
- **Dependency/adapter:** bind timeout/5xx/auth/circuit class, attempt/final state, retryability, opaque client output, adapter translation, import search and safe fixtures; name provider/uninspected adapter limits.
- **Prior evidence:** bind source/date, current reread, same-pattern search, final-edit command/result and artifact; future edits and uninspected runtime remain limits.

## Freshness And Authority

Prior notes, reports, incidents, generated evidence and summaries are selectors until current source, tests, fixtures, policy and sinks confirm them. Record inspected/skipped boundaries and map each claim to current source, command, fixture, capture, report, owner or residual risk. Production queries/exports require authorized bounded redacted access; sink, retention, audit-export, deploy or rollback changes require authority, owner and recovery.
