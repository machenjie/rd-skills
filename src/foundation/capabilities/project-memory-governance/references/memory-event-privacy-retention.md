# Memory Event Privacy Retention

Use this reference when a project memory event must be recorded, rejected, redacted, or expired. The `SKILL.md` body owns routing and closure; this file keeps low-frequency field and privacy rules out of the main context.

## Event Record Minimum

| Field | Required evidence | Reject or redact when |
| --- | --- | --- |
| `event_id` | Stable id or deterministic id seed for one bounded observation. | It depends on raw prompt text, full logs, or secret-bearing values. |
| `event_kind` | Repeat failure, fragile path, stale context, validation gap, review follow-up, graph drift, or promotion candidate. | It names a personal archive, broad corpus, or unrelated user content category. |
| `bounded_target` | Repository path, capability id, skill id, registry key, report family, or generated artifact family. | It points at a home-directory crawl, external archive mapping, private archive, or runtime corpus. |
| `source_anchor` | Current source, registry, test, report, generated source-of-truth, or owner evidence that must be checked. | It claims memory alone proves current behavior. |
| `attempt_signature` | Command class, patch path, validator class, or route family needed to detect repeated same-path attempts. | It captures full command arguments, environment values, tokens, or private data. |
| `privacy_boundary` | Public repo fact, project-local bounded fact, sensitive-excluded, promotion-forbidden, or owner-approved promotion. | The event would retain raw prompt, credential, secret, personal data, or full output. |
| `retention_policy` | Keep bounded event, expire after closure, promote then close, or do not store. | Retention is unbounded or unrelated to risk, validation, review, or promotion. |

## Exclusion Rules

- Store the fact that sensitive material was excluded, not the sensitive value.
- Prefer command class and outcome over raw command output.
- Prefer path family and failure class over full transcript.
- Mark an event `promotion-forbidden` when it can help current closure but would be unsafe as durable policy.
- Mark an event `do-not-store` when redaction would remove the evidence needed to make it useful.

## Retention Decision

| Decision | Use when | Next action |
| --- | --- | --- |
| Keep bounded event | The event changes graph scope, validation, trajectory review, or fragile-file handling. | Reconcile with current source before use. |
| Expire after closure | The event helps only this handoff and should not influence future work. | Mention residual risk, then drop from future projection. |
| Promote then close | Maintainer approved a durable doc, test, registry, skill, or eval fixture. | Update source through normal review and validation. |
| Do not store | Privacy, relevance, or provenance is unsafe. | Use direct source evidence or owner handoff instead. |

## Evidence Limit

A retained event proves only that a bounded observation existed in a prior lifecycle. It does not prove current source behavior, owner approval, validation freshness, generated artifact freshness, or that excluded events are irrelevant.
