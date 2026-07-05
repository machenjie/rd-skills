# File Storage Processing Checklist

- Select mode: upload intake, signed URL/download, large-file streaming, media/archive processing, lifecycle cleanup, or storage policy/encryption.
- Inspect current upload/download routes, storage policy, processors, scanners, cleanup jobs, tests, repository graph, project memory, and validation freshness.
- Record graph/memory/trajectory assumptions only when current source and validation confirm them.
- Define allowed file classes, size limits, business purpose, retention, and privacy class.
- Define object storage layout for raw, processed, quarantine, rejected, and deleted states.
- Enforce authorization on upload, download, metadata, processing, and signed URL creation.
- Validate size, extension, MIME, magic bytes, archive structure, and content policy.
- Define malware scanning, metadata stripping, and quarantine behavior.
- Scope signed URLs by method, object key, expiry, content type, and size where supported.
- Define direct upload, multipart upload, streaming, retry, and resume behavior.
- Define memory, temp disk, worker/pool, timeout, cancellation, and backpressure bounds for large-file or processing paths.
- Define lifecycle, legal hold, deletion, abandoned upload cleanup, and orphan cleanup.
- Map every file class, state transition, URL scope, scan gate, processor, lifecycle rule, cleanup path, and storage policy to validation evidence or residual risk.
- Add tests for unauthorized access, malicious files, oversized files, failed scans, metadata stripping, streaming memory ceiling, sandbox timeout, and cleanup.
- Name handoff boundaries and evidence limits so design output is not over-claimed as implementation, real cloud policy proof, legal retention approval, or production load validation.
- Record command/tool or manual review procedure, artifact/report path, exit code or manual result, inspected output, freshness after final edit, what the evidence proves, what it does not prove, rollback/containment path, and next handoff owner.
