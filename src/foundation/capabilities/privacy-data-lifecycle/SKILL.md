---
name: privacy-data-lifecycle
description: "`analysis-agent`/`task-agent`/`review-agent`: use when personal-data purpose, retention, deletion, sharing, telemetry, or provider handling changes; skip legal-only work."
---

# privacy-data-lifecycle

## Registry Trigger

**Use when**

- A system changes what personal or sensitive data it collects, derives, stores, observes, retains, deletes, exports, corrects, shares, de-identifies, or places with a provider or region.

**Do not use when**

- No personal or sensitive data handling changes, or the task is limited to authentication, secret storage, cryptographic mechanism, legal interpretation, or one client platform's local-data API.

## Skill Role

Own engineering data-flow purpose, minimization, lifecycle, individual operations, telemetry, de-identification, and provider/region handling; exclude legal conclusions.

## High-Value Rules

- Map accepted flow through meaning, purpose, and minimization.
- Bound copies, telemetry, individual operations, regions, providers, and de-identification.
- Load only the named Reference for an active lifecycle, provider, or de-identification decision.

## Anti-Patterns

- Privacy closure inferred from controls or unexplained linkable copies.

## Stop Conditions

- Stop on unknown meaning, purpose authority, retention, deletion reachability, provider/region flow, or re-identification risk.
- Route legal/compliance conclusions to accountable governance.

## Output Contract

- privacy engineering decision with data inventory classification purpose minimization retention deletion map individual-facing operations telemetry de-identification provider regional handling authority gaps evidence and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [data lifecycle controls](references/data-lifecycle-controls.md) | targeted | Collection purpose retention deletion backup export correction telemetry or regional handling crosses several stores | One bounded data flow already has an accepted purpose and complete lifecycle contract | analysis-agent, task-agent, review-agent | decision-record, residual-risk |
| [de identification and provider controls](references/de-identification-and-provider-controls.md) | targeted | De-identification linkage sharing provider or release-model choices remain open | No transformed or third-party data leaves the existing controlled boundary | analysis-agent, task-agent, review-agent | selected-approach, proof-limit |
