# Privacy Data Lifecycle Controls

Use this reference when a data flow crosses several processing stages, stores, individual-facing operations, providers, or regions.

Official pages in this reference were recorded as accessed on 2026-07-24.

## Lifecycle Record

| Stage | Required facts | Decision test |
|---|---|---|
| Collect | Data element, subject, source, notice or authority, purpose, necessity, and optionality | Reject fields or precision not required for the accepted outcome |
| Derive | Inputs, inference, confidence, affected subject, reuse, and sensitivity | Classify the derived value independently of its inputs |
| Use | Actor, operation, purpose, decision impact, and access boundary | Prevent secondary use without a compatible accepted purpose |
| Observe | Event purpose, fields, identifiers, sampling, access, and incident value | Minimize telemetry before emission |
| Store | System of record, cache, index, replica, queue, log, archive, and region | Give each copy a purpose, owner, access, and lifetime |
| Share | Recipient, purpose, fields, region, onward transfer, and return or deletion | Transfer only the bounded representation needed by the recipient |
| Export or correct | Request identity, scope, format, provenance, conflict, and progress | Produce an observable complete or explicitly partial outcome |
| Delete | Trigger, target copies, propagation, verification, exceptions, and completion | Prevent active use and name delayed or unavailable copies |
| Backup | Inclusion, expiry, restore access, deletion boundary, and replay handling | Prevent restored backups from silently resurrecting deleted active data |
| Retire | Provider exit, archive disposition, key and account closure, and evidence owner | Leave no unowned operational copy or ongoing feed |

## Engineering Rules

- Build the inventory from current source, schemas, configuration, telemetry definitions, provider contracts, and data-flow evidence rather than labels alone.
- Preserve the distinction between privacy risk to individuals and unauthorized-system-activity risk; security controls can support privacy without completing it.
- Represent deletion, export, and correction as owned asynchronous workflows when copies cannot change atomically.
- Mark legal basis, retention mandate, regional restriction, exception, and approval as supplied authority instead of interpreting law.
- Treat generated, inferred, aggregated, and telemetry data as in scope when linkage or decisions can affect a person.

## Primary Sources

- [NIST Privacy Framework](https://www.nist.gov/privacy-framework/privacy-framework)
- [NISTIR 8062: Privacy Engineering and Risk Management](https://www.nist.gov/publications/introduction-privacy-engineering-and-risk-management-federal-information-systems)
- [NIST relationship between cybersecurity and privacy](https://www.nccoe.nist.gov/relationship-between-cybersecurity-and-privacy)

## Version And Inference Limits

NIST Privacy Framework Version 1.0, published January 2020, remained the final framework version when accessed. NIST Privacy Framework 1.1 was an Initial Public Draft, not a final replacement.

NISTIR 8062 is federal privacy-engineering guidance from 2017. These voluntary and governmental sources do not establish the organization's policy, contract, jurisdiction, retention period, legal basis, or compliance status.

Do not infer that encryption, access control, or deletion from the primary store completes privacy lifecycle obligations. Do not infer legal permission from a technical purpose or data inventory.

## Required Record

Return a source-backed inventory, purpose and minimization decisions, copy and region map, retention and deletion behavior, backup boundary, export and correction status, telemetry handling, authoritative policy gaps, evidence freshness, and residual owners.
