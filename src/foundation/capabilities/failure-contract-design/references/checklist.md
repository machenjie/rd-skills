# Failure Contract Design Checklist

- Name each changed semantic boundary, including any controller, service, domain, repository, adapter, provider, job, consumer, UI/client, or generated contract that translates or exposes failure meaning.
- For each material changed failure state, record its project-owned category and preserve distinctions that alter retry, disclosure, rollback, observability, or ownership. Categories include validation, permission, not-found, conflict, timeout, cancellation, dependency, retryable, terminal, degraded, partial, poison-message, and internal.
- Map raw source failure to local type, safe external representation, internal cause representation, caller decision, and responsible boundary.
- Confirm user-visible output is safe: no stack, SQL, path, token, key, provider body, tenant hint, PII, prompt, or tool output.
- Preserve internal cause, boundary context, correlation or trace ID, and redacted diagnostic fields.
- Distinguish timeout, cancellation, unknown write outcome, retryable transient failure, permanent rejection, and terminal domain failure.
- For partial or degraded outcomes, name completed effects, missing or stale data, externally visible meaning, and the specialist owner of recovery or degradation policy.
- Classify retryable, terminal, cancellation, timeout, and unknown outcomes without designing keys, deduplication, backoff, queue disposition, or replay in this Skill.
- Map each changed failure state to negative tests, validators, review evidence, freshness, skipped paths, and residual risk.
- Hand off public error compatibility, logging and observability, retry mechanics, queue disposition, effect recovery, security review, release approval, or documentation to the named owner.
