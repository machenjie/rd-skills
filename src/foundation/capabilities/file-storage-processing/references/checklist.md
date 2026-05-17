# File Storage Processing Checklist

- Define allowed file classes, size limits, business purpose, retention, and privacy class.
- Define object storage layout for raw, processed, quarantine, rejected, and deleted states.
- Enforce authorization on upload, download, metadata, processing, and signed URL creation.
- Validate size, extension, MIME, magic bytes, archive structure, and content policy.
- Define malware scanning, metadata stripping, and quarantine behavior.
- Scope signed URLs by method, object key, expiry, content type, and size where supported.
- Define direct upload, multipart upload, streaming, retry, and resume behavior.
- Define lifecycle, legal hold, deletion, abandoned upload cleanup, and orphan cleanup.
- Add tests for unauthorized access, malicious files, oversized files, failed scans, metadata stripping, and cleanup.
