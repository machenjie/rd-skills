# File Storage Processing Benchmarks And Patterns

Load this reference when untrusted upload, object access, file transformation, archive/media parsing, signed delivery, cleanup, or retention changes. Do not load it for trusted repository files with no user or external boundary.

## Threat And State Contract

| Risk | Conditional control | Required proof |
| --- | --- | --- |
| Type confusion/polyglot | For an untrusted format admitted by the current business contract, allowlist accepted types and validate magic/structure; treat extension and caller Content-Type as discovery hints. | Mismatch, malformed, and allowed-type fixtures. |
| Malware/untrusted content | Quarantine until the current scanning policy permits availability; define scanner unavailable/stale-signature behavior. | State transition, known test artifact, and fail-open/closed decision. |
| Traversal/symlink/archive bomb | Canonical path containment, symlink policy, and bounded entries/nesting/output bytes/ratio. | Traversal, symlink, compression, and oversize fixtures. |
| Parser/processor exploit | Isolated worker with least privilege and bounded network, credentials, CPU, memory, disk, and wall time. | Sandbox/effective policy plus timeout/resource failure. |
| Cross-tenant/enumeration | Server-generated scoped object identity and server authorization for metadata, bytes, derivatives, URLs, and deletion. | Wrong-tenant/owner and guessed-key cases. |
| Broad delivery URL/cache | Bind object, method, actor/scope, expiry, content constraints, and cache behavior to current risk/policy. | Policy assertion, revoked/deleted access, and CDN residual limit. |
| Metadata/privacy leak | Minimize/strip EXIF, GPS, author, names, and embedded content according to classification. | Before/after metadata fixture and approved exceptions. |
| Orphan/retention leak | Provider lifecycle plus owned reconciliation for multipart, temp, quarantine, failed derivatives, expiry, deletion, and legal hold. | Prefix/state scan, cleanup metric, retry/terminal owner. |

Model applicable requested → uploading → uploaded → validating/scanning → quarantined/rejected/approved → processing → available → expired/deleted states. No reader reaches pre-approved bytes. Failed/retried transitions are idempotent and clean temporary files, object parts, claims, and derivatives. Deletion defines primary bytes, derivatives, CDN, search/index references, audit, backup/legal-hold limits, and user-visible timing.

## Resource And Provider Boundaries

Set file, request, memory, temp disk, part, archive, pixel/dimension, output, duration, parallelism, queue, range/download, and cleanup budgets only for applicable surfaces. Values come from current product risk, observed distribution, infrastructure capacity, and current provider/library documentation—not pinned universal SDK versions, TTLs, part sizes, or scanner products.

Hashing, encryption, signed delivery, versioning/immutability, retention tiering, and malware tooling are selected from integrity, confidentiality, compliance, dedupe, and recovery requirements. A cryptographic hash is required only when security/integrity semantics depend on it; fast hashes may serve non-security dedupe with collision handling.

## Evidence And Proof Limits

Inspect current routes, storage policy/client, bucket/container config, processors, scanner, queues, cleanup/lifecycle, CDN, and tests. Local fixtures do not prove effective cloud IAM, KMS, CDN purge, scanner freshness, provider hard limits, production parser isolation, restore, or legal-hold behavior. Name the unverified environment and owner.

Reject public-by-obscurity storage, user filenames as authoritative keys, whole-body buffering without a bound, and scan-after-availability. Also reject app-process parsing with broad credentials or network access and cleanup that omits failure paths. Reject signed URLs or caches that outlive authorization without accepted policy.

Route object/tenant authorization to `permission-boundary-modeling`, worker/retry lifecycle to `async-job-design`, cloud policy/privacy to `security-privacy-gate`, resource limits to `performance-budgeting`, deletion/retention migration to `data-migration-design` or `delivery-release-gate`, and operational signals/recovery to `reliability-observability-gate`.
