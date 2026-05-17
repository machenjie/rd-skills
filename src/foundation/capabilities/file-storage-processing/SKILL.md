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

# Pinned Tooling Baseline

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- Object storage SDKs: AWS SDK v3 (`@aws-sdk/client-s3` ≥ 3.600, `boto3` ≥ 1.34, `aws-sdk-go-v2` ≥ 1.30); Google Cloud Storage client ≥ 2.x; Azure SDK `@azure/storage-blob` ≥ 12.x.
- Multipart thresholds (S3): part size minimum 5 MiB, maximum 5 GiB, max 10 000 parts, max object 5 TiB; abort incomplete uploads with `AbortIncompleteMultipartUpload` lifecycle rule (recommended 7 days).
- Presigned URL TTL: ≤ 15 min for write, ≤ 60 min for read by default; never > 7 days (SigV4 hard limit).
- Content sniffing: `libmagic` (`file --mime-type`), `mime-types` npm or Python `python-magic`; never trust `Content-Type` header alone.
- Malware scanning: ClamAV ≥ 1.x with `freshclam` daily; or AWS GuardDuty Malware Protection / Cloudmersive / Sophos managed scan.
- Image / media processing: `sharp` (libvips) for Node, `Pillow` ≥ 10 for Python (with `PIL.Image.MAX_IMAGE_PIXELS` set), `ImageMagick` ≥ 7 with policy.xml hardened, `ffmpeg` ≥ 6 run under seccomp / firejail / gVisor for untrusted media.
- Archive safety: `python-zipfile38` or `libarchive` with explicit max entries, max ratio, max output size; reject path entries containing `..`, absolute paths, or symlinks (zip-slip).
- Hashing: SHA-256 for integrity; xxHash for non-security dedup.
- Encryption: SSE-KMS (S3), CMEK (GCS), CMK (Azure); TLS 1.2+ in transit.
- Lifecycle / cost tier: Intelligent-Tiering or Standard-IA / Coldline after 30-90 days; Glacier / Archive after 180+; deletion via lifecycle, not application loop.

# When To Use

Use this capability when a change touches file uploads, object storage buckets, signed URLs, media/image/video processing, large files, streaming transfer, multipart upload, MIME/type validation, virus scanning, object metadata, retention, lifecycle policies, cleanup jobs, user-generated files, backups, exports, imports, or file download authorization.

# Do Not Use When

Do not use this capability for database-only binary fields with no file lifecycle or access-control behavior. Do not use it instead of `web-security` for broad browser threats, `input-validation` for generic request validation, `backup-recovery` for disaster recovery, or `data-middleware-change-builder` for implementation ownership.

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

# Industry Benchmarks

- OWASP File Upload Cheat Sheet (2024) and OWASP ASVS v4.0.3 V12 File and Resources.
- CWE-434 Unrestricted Upload, CWE-22 Path Traversal, CWE-409 Decompression Bomb, CWE-918 SSRF (signed URL fetch).
- AWS S3 Security Best Practices, GCS Bucket Lock and Object Versioning, Azure Blob Immutable Storage.
- RFC 7233 Range requests for resumable downloads; tus.io v1 resumable upload protocol for resumable client uploads.
- ImageMagick `policy.xml` hardening guidance (CVE-2016-3714 ImageTragick).
- ClamAV daemon (`clamd`) production deployment; signature freshness via `freshclam`.
- Common Crawl / Wayback file-type distribution as realistic fuzz corpus.
- ISO/IEC 27040 Storage Security, NIST SP 800-209 Storage Infrastructure Security.

# Selection Rules

Select this capability when the primary risk is file lifecycle, object storage, signed URL access, or media processing. Pair with `security-privacy-gate` for upload abuse and data exposure, `backend-change-builder` for service logic, `frontend-change-builder` for client upload UX, `data-middleware-change-builder` for storage and processing pipelines, and `reliability-observability-gate` for large-file performance and cleanup observability.

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

- `file_classes`: allowed extensions, max size, declared business purpose, retention class, privacy class, virus-scan requirement
- `state_machine`: requested → uploading → uploaded → scanning → quarantined / scanned → processing → processed → available → expired → deleted, with transition owners
- `storage_layout`: buckets/containers per environment, prefix scheme, raw / processed / quarantine separation, encryption (SSE-KMS / CMEK / CMK), versioning, object-lock
- `access_control`: actors, IAM policy snippets, tenant scoping rule, presigned-URL scope (key, method, content-type, length, TTL), revocation/containment plan
- `validation_scanning`: declared-MIME vs magic-byte check, size enforcement, archive structural limits, decompression caps, malware scan engine and signature freshness
- `transfer_strategy`: direct browser upload via presigned POST/PUT or multipart, threshold for multipart, resumable protocol if any, retry/backoff, range download support
- `processing_pipeline`: transforms, sandbox technology, resource caps, idempotency key, retry policy, dead-letter destination, max processing latency
- `lifecycle_cleanup`: retention by class, legal-hold rules, soft vs hard delete, abandoned-multipart cleanup, orphan-derivative cleanup, audit log
- `observability`: scan latency, scan failure rate, processing failure rate, storage growth by tenant, presigned-URL issuance rate, 4xx/5xx by operation, access anomalies
- `tests`: authorization matrix, presigned-URL scope tests, malicious fixtures (EICAR, zip bomb, polyglot, oversized, traversal), streaming memory ceiling, cleanup verification, EXIF stripping verification

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
