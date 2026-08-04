---
name: file-storage-processing
description: "`analysis-agent`/`task-agent`/`review-agent`: use when uploads, object storage, streaming, MIME, scanning, access, retention, or cleanup changes; skip without file/storage impact."
---

# file-storage-processing

## Registry Trigger

**Use when**

- file upload object storage large file streaming MIME detection virus scanning signed URL media processing lifecycle retention cleanup

**Do not use when**

- no task-local file storage processing decision is required

## Skill Role

Protect access, resources, untrusted content, lifecycle, and cleanup across file and object storage without prescribing providers.

## High-Value Rules

- Classify file origin, active-content risk, size and archive exposure, expected consumers, and consequence before selecting extension, MIME, structural, malware, or isolation gates.
- Enforce tenant and object authorization at upload, download, processing, metadata, and delegated-access boundaries from authenticated server context.
- Select a bounded transfer mechanism from object distribution, memory budget, retry semantics, and provider limits.
- Validate declared type against an allowed content contract and independent content evidence when a mismatch can change execution, rendering, or parsing risk.
- Derive signed-access method, object scope, content bounds, expiry, and revocation response from the use case, data sensitivity, current policy, and exposure consequence.
- Define owned raw, quarantined, processed, retained, and deleted states, including abandoned transfers, failed processing, orphan detection, legal hold, and erasure conflicts where applicable.
- Isolate active or parser-exposed content, sanitize untrusted object keys and metadata, and select origin, download, and public-access controls from the actual rendering and execution boundary.

## Anti-Patterns

- Direct client upload still needs constrained issuance and server-side post-upload validation before the object becomes trusted or referenceable.
- Browser content type is advisory; polyglot, archive traversal, expansion, and parser risk require controls selected for the accepted formats.
- Processing isolation without bounded resources, credentials, network authority, and failure cleanup leaves the storage boundary exposed.
- Signed access may remain valid until expiry; incident handling needs a credible containment path for the chosen storage system.

## Stop Conditions

- Escalate to `security-privacy-gate` for regulated or executable content, public access, parser authority, or unresolved tenant isolation.
- Escalate to `delivery-release-gate` for storage policy, identity, encryption-key, or production lifecycle changes.
- Escalate when signed write access lacks object binding or an expiry and containment decision derived from current policy and exposure risk.
- Escalate to `reliability-observability-gate` when object distribution, throughput, processing, or cleanup can exceed measured resource and recovery bounds.
- Escalate legal-hold and erasure conflicts to the policy owner.

## Output Contract

- Return a file-storage decision: define classes, states, layout, access, scanning, transfer, processing, lifecycle, cleanup, observability, and tests

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Upload, transformation, sandbox, delivery, or retention controls need selection | Trusted repository files never cross an external boundary | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | File flows include quarantine, archives, signed URLs, or cleanup | No untrusted bytes or object-access path changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Storage safety needs fresh malicious fixtures, policies, or scanner reports | No access, processing, or lifecycle claim awaits proof | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
