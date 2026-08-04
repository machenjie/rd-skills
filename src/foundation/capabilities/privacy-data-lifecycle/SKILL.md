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

Define engineering data-flow inventory, purpose boundaries, minimization, lifecycle controls, individual-facing operations, telemetry, de-identification risk, and third-party handling. Inform accountable privacy and legal decisions without giving legal advice or claiming compliance.

## High-Value Rules

- **Classify data by meaning and flow.** Name direct, derived, inferred, linked, and sensitive elements with subjects, producers, consumers, stores, regions, and accountable owners.
- **Bind processing to an accepted purpose.** Reject collection, derivation, sharing, or retention that lacks a necessary product or operational outcome and authorized policy source.
- **Reject unnecessary representation.** Bound fields, precision, granularity, frequency, population, access, and lifetime across primary data, telemetry, exports, and support artifacts.
- **Apply lifecycle policy to every reachable copy.** Cover caches, indexes, logs, queues, analytics, replicas, archives, and backups with deletion propagation and non-resurrection behavior.
- **Make export, correction, and deletion observable.** Define identity binding, scope, asynchronous progress, partial failure, completion evidence, and unavailable-copy disclosure.
- **Constrain third-party and regional handling.** Record provider purpose, data classes, location, onward sharing, retention, deletion, incident, and exit obligations before transfer.
- **Treat telemetry as data processing.** Remove unnecessary identifiers and payloads before collection instead of relying on sampling, access restriction, or later redaction.
- **Evaluate de-identification against linkage.** Name direct and quasi-identifiers, recipient knowledge, release model, utility tradeoff, and re-identification testing before reducing controls.

## Anti-Patterns

- Call data anonymous because obvious names were removed while stable identifiers or joinable attributes remain.
- Report deletion complete when searchable, queued, exported, provider-held, or restorable backup copies remain unexplained.
- Copy production events into logs, analytics, tests, or support tools and rely on access control as minimization.

## Stop Conditions

Stop when data meaning, purpose authority, retention source, deletion reachability, provider flow, region, or re-identification risk is unknown. Route legal obligations and compliance conclusions to accountable counsel or privacy governance.

## Output Contract

- privacy engineering decision with data inventory classification purpose minimization retention deletion map individual-facing operations telemetry de-identification provider regional handling authority gaps evidence and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [data lifecycle controls](references/data-lifecycle-controls.md) | targeted | Collection purpose retention deletion backup export correction telemetry or regional handling crosses several stores | One bounded data flow already has an accepted purpose and complete lifecycle contract | analysis-agent, task-agent, review-agent | decision-record, residual-risk |
| [de identification and provider controls](references/de-identification-and-provider-controls.md) | targeted | De-identification linkage sharing provider or release-model choices remain open | No transformed or third-party data leaves the existing controlled boundary | analysis-agent, task-agent, review-agent | selected-approach, proof-limit |
