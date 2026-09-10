# Failure Contract Design Checklist

- Represent partial and degraded outcomes explicitly so callers can distinguish completed effects, unavailable data, stale data, and work that still needs specialist-owned recovery.
- Name each changed controller, service, domain, repository, adapter, provider, job, consumer, UI/client, and generated boundary that translates or exposes failure meaning.
- Classify validation, permission, not-found, conflict, timeout, cancellation, dependency, retryable, terminal, degraded, partial, poison-message, and internal states without designing routed retry or queue mechanics.
- Map raw source failure to local type, safe external representation, authorized internal cause, caller decision, and responsible boundary.
- Exclude stack, SQL, path, token, key, provider body, tenant/resource-existence hint, PII, prompt, and tool output; retain redacted boundary and correlation evidence.
- Distinguish timeout, cancellation, unknown write outcome, transient retryable failure, permanent rejection, and terminal domain failure.
- For partial/degraded outcomes, name completed and incomplete effects, missing/stale data, external meaning, and recovery/degradation owner.
- Map each changed state to negative tests, validators, freshness, skipped paths, proof limits, and residual risk.
- Hand off public compatibility, diagnostics/observability, retry, queue disposition, effect recovery, security, release, and documentation to their named owners.
