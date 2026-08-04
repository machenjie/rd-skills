# De-Identification And Provider Controls

Use this reference when transformed data, analytics, public release, a service provider, or onward sharing changes the people who can link data to individuals.

Official pages in this reference were recorded as accessed on 2026-07-24.

## De-Identification Decision

Record:

- direct identifiers removed, transformed, tokenized, or retained
- quasi-identifiers and combinations that remain linkable
- external datasets and background knowledge available to each recipient
- release model, query boundary, access restrictions, and output controls
- utility requirement and measurable disclosure-risk threshold
- re-identification testing method, freshness, reviewer authority, and residual risk
- revocation, correction, deletion, and incident handling after release

Choose a transformation only when its evaluated risk and retained utility fit the named release model. Masking, hashing, pseudonyms, aggregation, and synthetic generation are techniques, not automatic proof that data is de-identified.

## Provider And Sharing Decision

Record:

- recipient and provider identities with accountable internal owners
- bounded purpose, data classes, fields, subjects, and transfer mechanism
- processing and storage regions with onward sharing or subprocessors
- provider access, support exports, telemetry, model training, and derived data
- retention, deletion propagation, backup expiry, correction, export, and exit
- incident notification, unavailable evidence, contract authority, and reassessment trigger

Stop transfer when a provider cannot state where the data goes, why it is processed, who can receive it, how deletion propagates, or how service exit removes continuing copies.

## Primary Sources

- [NIST SP 800-188: De-Identifying Government Datasets](https://csrc.nist.gov/pubs/sp/800/188/final)
- [NISTIR 8062: Privacy Engineering and Risk Management](https://www.nist.gov/publications/introduction-privacy-engineering-and-risk-management-federal-information-systems)
- [NIST Privacy Framework](https://www.nist.gov/privacy-framework/privacy-framework)

## Version And Inference Limits

NIST SP 800-188 is a September 2023 final publication written for United States government datasets. Its techniques and governance questions are useful engineering evidence but are not universal legal standards or product-specific approval.

NIST Privacy Framework Version 1.0 remained final when accessed; Version 1.1 was still an Initial Public Draft. Provider claims and contracts must be inspected in their current project context.

Do not infer that pseudonymization, hashing, aggregation, or synthetic data prevents re-identification. Do not infer that a provider certification, region selector, or contract clause proves actual runtime routing, deletion, subprocessors, or compliance.

## Required Record

- Return the release and recipient model, identifiers, linkage threats, selected transformation, and utility and risk evidence.
- Include provider flows and regions, onward-sharing and exit controls, supplied policy or legal authorities, unresolved facts, and proof limits.
