---
name: file-storage-processing
description: Designs file upload, object storage, large file handling, streaming, MIME detection, virus scanning, lifecycle, retention, access control, signed URLs, media processing, and cleanup.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "99"
changeforge_version: 0.1.0
---

# Mission

Design safe file and object-storage flows that handle uploads, downloads, streaming, scanning, metadata, access control, lifecycle, retention, media processing, and cleanup without exposing users, infrastructure, or data integrity to avoidable risk.

# Tooling Baseline

Use current, project-approved storage SDKs, content sniffers, malware scanners, image/media processors, archive readers, hashing, encryption, lifecycle, and cleanup mechanisms. Treat pinned versions and provider limits as review baselines, not permanent recommendations; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed SDK, multipart, signed-URL, media-processing, archive, encryption, and lifecycle baselines when drafting or reviewing a concrete design.

# When To Use

Use this capability when a change touches file uploads, object storage buckets, signed URLs, media/image/video processing, large files, streaming transfer, multipart upload, MIME/type validation, virus scanning, object metadata, retention, lifecycle policies, cleanup jobs, user-generated files, backups, exports, imports, or file download authorization.

# Do Not Use When

Do not use this capability for database-only binary fields with no file lifecycle or access-control behavior. Do not use it instead of `web-security` for broad browser threats, `input-validation` for generic request validation, `backup-recovery` for disaster recovery, or `data-middleware-change-builder` for implementation ownership.

# Stage Fit

Use during experience-definition, implementation-planning, coding, review, and release-readiness when files cross trust, tenant, storage, processing, or lifecycle boundaries. In planning, define the file classes, state machine, storage layout, access-control path, scanning path, transfer strategy, and cleanup ownership before implementation. In coding/review, reject stale assumptions from project memory or repository graph unless current source, storage policy, tests, and validation output confirm them. Hand off when the primary question is generic validation, browser exploit class, service implementation, storage pipeline implementation, production observability, or disaster recovery.

# Non-Negotiable Rules

- Treat uploaded files as untrusted until size, extension, declared MIME, magic-byte, archive-structure, and malware-scan gates all pass.
- Enforce per-tenant authorization on every upload, download, processing action, signed-URL issuance, and metadata read.
- Stream uploads and downloads; never buffer an entire user file into application memory; use multipart upload above the configured threshold (typically 8-16 MiB).
- Validate declared MIME against `libmagic` magic-byte sniff and against an allowlist; reject mismatches.
- Issue signed URLs with the minimum scope: single object key, single HTTP method, bounded `Content-Length`, bounded `Content-Type`, and TTL ≤ documented maximum.
- Define lifecycle for raw, processed, quarantined, and deleted states; orphan and abandoned multipart cleanup must be owned.
- Strip EXIF, GPS, author, comments, and embedded thumbnails from images and documents served back to users unless retention is an explicit product requirement.
- Serve user-uploaded content from a separate origin (sandbox domain) with `Content-Disposition: attachment` for non-image types and `X-Content-Type-Options: nosniff`.
- Never let object keys derive directly from user input without sanitization; namespace by tenant ID and use a server-generated UUID or content hash.
- Use bucket policies that deny public access by default (`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets` for S3).

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Upload intake | New or changed user upload, direct-to-storage upload, import, attachment, or object metadata path. | File class, trust boundary, validation, scan-before-available, tenant ownership. | Source route, file limits, MIME/magic/scan gates, authz matrix. | `security-privacy-gate`, `input-validation` | Media transforms unless present. |
| Signed URL and download access | Presigned URL, CDN, range download, export, private media, or object metadata read. | Scope URLs by key/method/TTL/content bounds and preserve tenant access checks. | URL policy, actor/object matrix, cache headers, revocation/containment. | `web-security`, `permission-boundary-modeling` | Public bucket access. |
| Large file or streaming transfer | Multipart, resumable, range, > configured memory budget, high throughput, or client retry. | Streaming, backpressure, cancellation, retry, memory ceiling, partial cleanup. | Size/throughput budget, memory ceiling, multipart/resume state, load test or not-verified limit. | `language-performance-safety`, `reliability-observability-gate` | Buffer-all handlers. |
| Media/archive processing | Image/video/document transform, archive unpack, OCR, thumbnail, transcoding, or metadata strip. | Sandbox untrusted parsers, cap resources, block zip-slip/bombs, strip sensitive metadata. | Processor sandbox, no-network rule, caps, malicious fixture tests. | `threat-modeling`, `quality-test-gate` | In-process parser trust. |
| Lifecycle, retention, and cleanup | Retention, legal hold, deletion, quarantine, abandoned multipart, orphan derivatives, or CDN purge. | Own every terminal state and cleanup path with audit and observability. | State owner, retention policy, cleanup job, deletion SLA, metric/alert. | `backup-recovery`, `delivery-release-gate` when release-bound | Application loop deletion without lifecycle policy. |
| Storage policy or encryption | Bucket policy, KMS/CMEK/CMK, object lock/versioning, account public access, or cross-account grants. | Least privilege, encryption, effective policy, rollback/containment. | Policy diff, key owner, public-access proof, rollback path. | `security-privacy-gate`, `delivery-release-gate` | Treating provider defaults as proof. |

# Industry Benchmarks

Anchor against OWASP File Upload Cheat Sheet, OWASP ASVS V12, CWE-434, CWE-22, CWE-409, CWE-918, cloud object-storage security guidance, RFC 7233 range requests, tus.io resumable uploads, hardened media processor guidance, malware-scanning operations, storage security standards, and provider lifecycle controls. Keep this body focused on routing, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed tooling baselines, threat matrices, resource budgets, malicious fixture catalog, and provider policy patterns.

# Selection Rules

Select this capability when the primary risk is file lifecycle, object storage, signed URL access, or media processing. Pair with `security-privacy-gate` for upload abuse and data exposure, `backend-change-builder` for service logic, `frontend-change-builder` for client upload UX, `data-middleware-change-builder` for storage and processing pipelines, and `reliability-observability-gate` for large-file performance and cleanup observability.

# Proactive Professional Triggers

- **Signal:** upload or import path trusts extension, browser `Content-Type`, filename, object key, archive path, or client-declared size. **Hidden risk:** malware, type confusion, path traversal, decompression bomb, or tenant collision reaches storage. **Required professional action:** require server-side size, magic-byte, allowlist, archive-structure, and scan-before-publish gates. **Route to:** `input-validation`, `threat-modeling`. **Evidence required:** malicious fixture test, rejected mismatch, state transition proof.
- **Signal:** signed URL, CDN URL, public bucket, or object key is generated without actor/object authorization evidence. **Hidden risk:** cross-tenant read/write, unrevocable broad access, or private content caching. **Required professional action:** scope URL and cache policy to actor, object, method, TTL, content bounds, and containment path. **Route to:** `security-privacy-gate`, `web-security`. **Evidence required:** denied tenant test, TTL/scope assertion, cache-header proof.
- **Signal:** handler buffers whole files, processes media inline, extracts archives without caps, or runs converters with network/credential access. **Hidden risk:** OOM, RCE, disk exhaustion, credential exfiltration, or shared pool starvation. **Required professional action:** require streaming, sandbox, resource caps, timeout, cancellation, and no-network execution. **Route to:** `language-performance-safety`, `reliability-observability-gate`. **Evidence required:** memory ceiling, timeout kill, malicious fixture/fuzz result.
- **Signal:** quarantine, failed transform, deleted owner, expired export, or abandoned multipart cleanup is unspecified. **Hidden risk:** stale private data, legal erasure failure, storage cost leak, or user-visible deleted content. **Required professional action:** define lifecycle states and cleanup owner with metrics. **Route to:** `backup-recovery`, `observability`. **Evidence required:** retention/deletion matrix, cleanup command/job, metric, residual backup/CDN limit.
- **Signal:** repository graph or project memory says a bucket, processor, scanner, or cleanup job already exists. **Hidden risk:** stale storage topology or old validator path hides changed tenancy, policy, or SDK behavior. **Required professional action:** current-source-confirm storage policy, call sites, tests, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when files include PII, regulated data (PCI / HIPAA / GDPR), executables, scripts, or are publicly downloadable.
- Escalate to `delivery-release-gate` when bucket policy, IAM, or KMS key changes are required.
- Escalate to critical when a signed URL can grant write access to a production bucket without a TTL ≤ 15 min and object-key binding.
- Escalate to `reliability-observability-gate` when expected single-object size exceeds 1 GiB or expected throughput exceeds 1 GiB/s.
- Escalate to legal / compliance when retention has a legal-hold or right-to-erasure obligation that conflicts with backup retention.

# Critical Details

- Direct browser-to-S3 upload still requires server-side issuance of a presigned POST policy (with `Content-Length-Range`, `Content-Type` starts-with, key prefix) and a post-upload validation step before the object becomes referenceable.
- Content-Type from the browser is advisory; sniff with `libmagic` and reject if it disagrees with the allowlist. Polyglot files (e.g., GIFAR) require deeper structural validation.
- Zip-slip: every entry must be validated such that `os.path.realpath(join(target, entry))` starts with `realpath(target)`; reject symlinks; cap entries (e.g., 10 000), cap total uncompressed size (e.g., 1 GiB), cap compression ratio (e.g., 100x).
- Decompression bombs: stream-decompress with output-byte counter; abort on cap.
- Image processors load arbitrary parsers; isolate them in a separate process / container with seccomp, no network egress, no credentials, low memory cap, and a short timeout (`SIGKILL` after e.g. 30 s).
- Presigned URLs cannot be revoked individually before expiry; rotate the signing key, change the object key, or apply a deny bucket policy if compromise is suspected.
- Cleanup must handle: abandoned multipart uploads (lifecycle `AbortIncompleteMultipartUpload`), quarantined files, failed transforms, soft-deleted owners, expired exports, and orphan thumbnails.
- Downloads must set `Content-Disposition: attachment; filename*=UTF-8''<encoded>` for untrusted file names, `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store` for tenant content, and never `Access-Control-Allow-Origin: *` for credentialed responses.
- Object keys: namespace as `<tenant>/<resource>/<uuid-or-sha256>` to prevent enumeration and cross-tenant collision; do not include user-controlled filename in the key.
- CDN caching: key on auth context or use signed cookies / signed URLs; never cache private content keyed only on URL.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 file-storage selection, risk, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete upload, download, storage layout, scanning, processing, retention, cleanup, or signed-URL design. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed tool baselines, provider limits, malicious fixture patterns, sandbox/resource caps, URL/cache policy, lifecycle matrices, or graph/memory/trajectory checks are needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

# Failure Modes

- Symptom: malware download links served to other users.
  Cause: file extension allowlist only; no magic-byte check; no scan gate before object becomes referenceable.
  Detection: integration test uploads EICAR test string and asserts quarantine; CI lint requires scan-before-publish state transition.
  Impact: distribution of malware via trusted domain, takedown / SOC incident.
- Symptom: bucket exposed publicly.
  Cause: signed URL with 7-day TTL or wildcard prefix; or bucket policy allowed `s3:GetObject` to `*`.
  Detection: AWS Config rule `s3-bucket-public-read-prohibited`; presigned-URL TTL lint.
  Impact: data exfiltration, compliance breach.
- Symptom: photo upload leaks GPS coordinates.
  Cause: EXIF metadata not stripped before serving processed image.
  Detection: unit test asserts EXIF orientation only is preserved and GPS/Maker tags are stripped.
  Impact: user-location disclosure, GDPR incident.
- Symptom: service OOM during large upload.
  Cause: handler reads entire request into memory (`request.body.read()`); no streaming multipart.
  Detection: load test with 1 GiB upload; memory ceiling assertion.
  Impact: pod restart loop, ingestion outage.
- Symptom: malicious zip exhausts disk.
  Cause: no decompression-ratio or output-size cap.
  Detection: fuzz with 42.zip / nested zip bomb; assert abort within bound.
  Impact: disk exhaustion, node failure.
- Symptom: storage bill spike.
  Cause: abandoned multipart uploads accumulate; no lifecycle rule.
  Detection: weekly metric on incomplete-multipart-upload bytes; lifecycle policy review.
  Impact: 10-100x cost overrun.
- Symptom: deleted file still served via CDN.
  Cause: CDN cache TTL exceeds deletion latency; no invalidation on delete.
  Detection: integration test deletes object and asserts CDN 404 within SLA, or signed-URL based access bypassing CDN cache.
  Impact: failure to honor deletion / right-to-erasure.
- Symptom: ImageMagick RCE.
  Cause: default `policy.xml` allows MVG/MSL/HTTPS coders on untrusted input.
  Detection: pin hardened policy; CVE scan; sandbox exec.
  Impact: full host compromise.

# Output Contract

Return a file storage and processing design with:

- `mode_selected` (upload intake / signed URL and download access / large file or streaming transfer / media-archive processing / lifecycle-retention-cleanup / storage policy-encryption)
- `source_evidence` (current upload/download routes, object storage policy, bucket/container config, processors, scanners, cleanup jobs, tests, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused storage, processor, scanner, cleanup, or policy assumption)
- `file_classes`: allowed extensions, max size, declared business purpose, retention class, privacy class, virus-scan requirement
- `state_machine`: requested → uploading → uploaded → scanning → quarantined / scanned → processing → processed → available → expired → deleted, with transition owners
- `storage_layout`: buckets/containers per environment, prefix scheme, raw / processed / quarantine separation, encryption (SSE-KMS / CMEK / CMK), versioning, object-lock
- `access_control`: actors, IAM policy snippets, tenant scoping rule, presigned-URL scope (key, method, content-type, length, TTL), revocation/containment plan
- `validation_scanning`: declared-MIME vs magic-byte check, size enforcement, archive structural limits, decompression caps, malware scan engine and signature freshness
- `transfer_strategy`: direct browser upload via presigned POST/PUT or multipart, threshold for multipart, resumable protocol if any, retry/backoff, range download support
- `processing_pipeline`: transforms, sandbox technology, resource caps, idempotency key, retry policy, dead-letter destination, max processing latency
- `lifecycle_cleanup`: retention by class, legal-hold rules, soft vs hard delete, abandoned-multipart cleanup, orphan-derivative cleanup, audit log
- `observability`: scan latency, scan failure rate, processing failure rate, storage growth by tenant, presigned-URL issuance rate, 4xx/5xx by operation, access anomalies
- `performance_safety`: streaming memory ceiling, temp disk cap, worker/pool/concurrency bounds, cancellation, timeout, and backpressure behavior
- `security_threats`: abuse cases for malware, traversal, polyglot, metadata leakage, public exposure, cross-tenant access, and signed-URL compromise
- `changed_file_storage_to_validation_map`: each file class, state transition, storage policy, URL scope, scan gate, processor, lifecycle rule, and cleanup path mapped to validator/test or residual risk
- `handoff_boundaries`: what belongs to input validation, web security, backend implementation, storage pipeline, reliability, backup/recovery, delivery, or legal/compliance review
- `tests`: authorization matrix, presigned-URL scope tests, malicious fixtures (EICAR, zip bomb, polyglot, oversized, traversal), streaming memory ceiling, cleanup verification, EXIF stripping verification
- `evidence_limits`: what was not inspected or not run: real buckets, IAM/KMS effective policy, CDN invalidation, scanner signatures, large-file load, physical media corpus, or legal retention approval

# Evidence Contract

Close a file-storage-processing design only when the output names selected mode, current source evidence inspected, graph/memory/trajectory reuse judgment, file classes, state machine, access controls, scan gates, transfer strategy, processor sandbox, lifecycle cleanup, observability, changed-file-storage-to-validation map, handoff boundaries, residual risk, and evidence limits. A generic "validate uploads" or "store in S3" statement is not sufficient evidence.

# Benchmark Coverage

Improved file-storage designs reject common weak patterns: extension-only allowlists, public buckets, broad signed URLs, buffer-all handlers, scan-after-publish, in-process media parsers with credentials, archive extraction without caps, user-derived object keys, no orphan cleanup, CDN deletion gaps, and stale graph/memory claims about buckets or scanners. Detailed provider limits, tooling baselines, malicious fixture catalog, and resource matrices belong in references so this body stays efficient.

# Routing Coverage

Route here when file lifecycle, object storage, upload/download access, scanning, signed URLs, media/archive processing, retention, or cleanup is primary. Hand off when the primary concern is generic request validation (`input-validation`), browser exploit class (`web-security`), service implementation (`backend-change-builder`), storage/queue/search implementation (`data-middleware-change-builder`), production SLO/telemetry (`reliability-observability-gate`), or disaster recovery (`backup-recovery`).

# Quality Gate

1. No file becomes available to any reader before passing magic-byte validation and malware scan; this is asserted by an integration test using EICAR.
2. Every download path checks per-tenant authorization; cross-tenant access test returns 403/404.
3. Presigned URLs have TTL ≤ 60 min (read) / 15 min (write), are bound to a single object key and method, and enforce `Content-Length-Range`.
4. Streaming upload of a 1 GiB file completes without resident memory exceeding the configured ceiling (e.g., 256 MiB).
5. Archive intake rejects zip-slip, > 10 000 entries, > 100x compression ratio, > configured uncompressed size; fuzz tests cover at least 5 malicious fixtures.
6. Image / media processing runs in a sandbox with no network egress and is killed at the timeout; ImageTragick coders are disabled.
7. EXIF / GPS / author metadata is stripped on served derivatives unless explicit product opt-in.
8. Lifecycle rules abort incomplete multipart uploads within 7 days; orphan cleanup job runs and emits a metric.
9. Bucket public access is blocked at the account level; CI fails if a bucket lacks block-public-access settings.
10. Deletion propagates to CDN within the documented SLA, asserted by integration test.
11. Selected mode, source evidence, and graph/memory/trajectory reuse judgment are explicit.
12. Every file class, state transition, URL scope, scan gate, processor, lifecycle rule, cleanup path, and storage policy maps to validation evidence or named residual risk.
13. Streaming, temp disk, worker/pool, timeout, cancellation, and backpressure limits are defined for large files or processing pipelines.
14. Handoff boundaries and evidence limits are explicit so design evidence is not over-claimed as implementation, real cloud policy proof, legal retention approval, or production load validation.

# Used By

- backend-change-builder
- security-privacy-gate
- data-middleware-change-builder
- reliability-observability-gate
- frontend-change-builder

# Handoff

Hand off to `security-privacy-gate` for upload threat review, `input-validation` for request constraints, `web-security` for browser download and content handling, `backend-change-builder` for service implementation, `data-middleware-change-builder` for object storage and processing pipelines, and `reliability-observability-gate` for large-file performance and operational signals.

# Completion Criteria

The capability is complete when file intake, storage, processing, access, retention, deletion, and cleanup are explicit, observable, testable, and safe under malicious content, large payloads, partial failures, and cross-tenant access attempts.
