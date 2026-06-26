# File Storage Processing Benchmarks And Patterns

Use this reference when file-storage-processing output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, evidence, output contract, and quality gates.

## Tooling And Provider Baselines

Pinned versions and provider limits are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update the capability before relying on it for new product work.

- Object storage SDKs: AWS SDK v3 (`@aws-sdk/client-s3` >= 3.600, `boto3` >= 1.34, `aws-sdk-go-v2` >= 1.30); Google Cloud Storage client >= 2.x; Azure SDK `@azure/storage-blob` >= 12.x.
- Multipart thresholds for S3: minimum part size 5 MiB, maximum part size 5 GiB, maximum 10,000 parts, maximum object 5 TiB; abort incomplete uploads with `AbortIncompleteMultipartUpload`, commonly at 7 days.
- Signed URL TTL: write URLs default <= 15 minutes; read URLs default <= 60 minutes; never exceed provider hard limits or product policy.
- Content sniffing: `libmagic` (`file --mime-type`), npm `mime-types`, or Python `python-magic`; never trust the browser `Content-Type` header alone.
- Malware scanning: ClamAV 1.x with daily `freshclam`, AWS GuardDuty Malware Protection, Cloudmersive, Sophos, or another approved managed scanner.
- Image and media processing: `sharp`/libvips, Pillow with `PIL.Image.MAX_IMAGE_PIXELS`, hardened ImageMagick 7 `policy.xml`, and ffmpeg 6+ in a sandbox for untrusted media.
- Archive handling: `zipfile`/`libarchive` with explicit max entries, max ratio, max output size, and path/symlink rejection.
- Hashing: SHA-256 for security/integrity; xxHash or equivalent only for non-security deduplication.
- Encryption: SSE-KMS for S3, CMEK for GCS, CMK for Azure, TLS 1.2+ in transit.
- Lifecycle and cost tiering: Intelligent-Tiering, Standard-IA, Coldline, Glacier/Archive, and provider lifecycle rules instead of application-loop deletion where possible.

## Benchmark Anchors

- OWASP File Upload Cheat Sheet and OWASP ASVS V12 File and Resources.
- CWE-434 Unrestricted Upload, CWE-22 Path Traversal, CWE-409 Decompression Bomb, CWE-918 SSRF.
- AWS S3 Security Best Practices, GCS Bucket Lock and Object Versioning, Azure Blob Immutable Storage.
- RFC 7233 range requests for resumable downloads and tus.io v1 for resumable client uploads.
- ImageMagick ImageTragick hardening guidance and media parser sandboxing practice.
- ClamAV daemon production deployment, signature freshness, and managed malware scanning.
- ISO/IEC 27040 Storage Security and NIST SP 800-209 Storage Infrastructure Security.

## Threat And Control Matrix

| Threat | Weak signal | Required control | Evidence |
| --- | --- | --- | --- |
| Malware distribution | File available before scan. | Quarantine until clean scan; EICAR regression. | State transition test and scanner freshness. |
| Type confusion / polyglot | Extension or `Content-Type` only. | Magic-byte and structural validation against allowlist. | Mismatch rejection test. |
| Zip-slip traversal | Archive path joins target directly. | Realpath prefix check, symlink rejection, entry cap. | Traversal fixture test. |
| Decompression bomb | No output-byte or ratio cap. | Stream with byte counter and compression ratio cap. | Bomb fixture aborts within bound. |
| Cross-tenant access | Object key or URL lacks tenant binding. | Server-generated key under tenant/resource namespace and authz check. | Denied tenant test. |
| Broad signed URL | Wildcard prefix, long TTL, unbound method. | Single key, method, TTL, content-type/length bounds. | URL policy assertion. |
| Metadata leak | EXIF/GPS/author fields preserved by default. | Strip sensitive metadata before serving derivatives. | EXIF stripping test. |
| Processor RCE | Media parser runs with credentials/network. | Sandbox, no network egress, memory/CPU/time cap. | Sandbox policy and timeout test. |
| CDN stale deletion | Private content cached by URL only. | Auth-keyed cache, signed URL/cookie, invalidation or short TTL. | Delete-to-404 SLA test or accepted limit. |
| Orphan cost leak | Failed/quarantined/multipart objects unowned. | Lifecycle rule and cleanup job with metrics. | Cleanup validation and storage-growth metric. |

## File State Machine Pattern

```text
requested
  -> uploading
  -> uploaded
  -> validating
  -> scanning
  -> quarantined | rejected | scanned
  -> processing
  -> processed
  -> available
  -> expired | deleted
```

Rules:

- No reader can access `uploaded`, `validating`, `scanning`, `quarantined`, or `rejected` states.
- `available` requires validation, scan, authorization metadata, retention class, and observability tags.
- `deleted` must define object deletion, derivative deletion, CDN behavior, audit event, and backup/legal-hold residual risk.
- Failed transitions must be idempotent and clean up temp objects, temp files, worker claims, and derived outputs.

## Resource Budget Matrix

| Surface | Budget to define | Required evidence |
| --- | --- | --- |
| Upload request | Max file size, request timeout, memory ceiling, temp disk cap. | Large-file test or not-verified limit. |
| Multipart upload | Part size, max parts, abort window, retry policy. | Multipart policy and abandoned-upload cleanup. |
| Processing worker | CPU, memory, wall time, parallelism, queue depth. | Sandbox caps and queue/worker metric. |
| Archive extraction | Max entries, max uncompressed bytes, max ratio, max nesting. | Malicious archive fixtures. |
| Image processing | Max pixels, max dimensions, metadata policy, transform timeout. | Image bomb and EXIF tests. |
| Download | Range support, response timeout, cache policy, auth check. | Authorized/denied/range behavior tests. |
| Cleanup | Retention duration, deletion SLA, retry/DLQ, orphan scan cadence. | Cleanup run evidence and metric. |

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current routes, storage clients, bucket policy, processors, scanners, cleanup jobs, and tests were inspected. | Graph proximity is used as proof that validation or cleanup exists. |
| Project memory | Prior bucket, scanner, or CDN behavior has owner, timestamp, and unchanged source path. | Memory predates tenant model, provider SDK, policy, scanner, or lifecycle change. |
| Execution trajectory | Validation ran after the final material edit and covered changed storage paths. | Evidence is stale, partial, or from a different environment/provider. |
| Cloud policy | Effective policy or provider config is inspected. | Code intent is treated as proof of public access, IAM, or KMS posture. |
| Scanner status | Signature freshness and failure behavior are known. | Scanner is assumed healthy because a service name exists. |

## Review Questions

1. Which file classes exist, and why is each allowed?
2. Which actors can upload, download, process, delete, issue URLs, or read metadata?
3. Which trust boundaries does the file cross?
4. Which state first becomes referenceable to users?
5. Which malicious fixtures prove validation and scanning?
6. Which object prefix, bucket, and key strategy prevents enumeration and collision?
7. Which lifecycle rule handles abandoned multipart, failed transform, quarantine, expired export, and deleted owner?
8. Which processor runs with no network, no credentials, bounded memory, and timeout?
9. Which storage growth, scan latency, processing failure, and access anomaly metrics are emitted?
10. Which evidence remains unverified in real cloud/CDN/scanner/legal environments?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Scan after making the object available. | Malware can be downloaded before detection. | Quarantine until validation and clean scan complete. |
| User filename becomes object key. | Enables traversal-like confusion, enumeration, and tenant collision. | Generate server-side key with tenant/resource namespace and UUID/hash. |
| Public bucket plus "unguessable" names. | Obscurity is not authorization. | Block public access and issue scoped URLs through authorized service path. |
| `request.body.read()` for uploads. | Buffers untrusted file in memory and OOMs under large input. | Stream and enforce byte ceilings. |
| Archive extraction without realpath check. | Zip-slip writes outside target directory. | Canonicalize paths and reject traversal/symlink entries. |
| Media processor in app process with credentials. | Parser exploit becomes application compromise. | Run isolated worker/container with no network and least privilege. |
| Cleanup only in application code. | Failed jobs and abandoned uploads persist. | Provider lifecycle rule plus owned cleanup/reconciliation job. |
| CDN caches private object by URL only. | Deleted or unauthorized content can remain visible. | Signed URLs/cookies, auth-keyed cache, short TTL/invalidation, and residual risk statement. |
