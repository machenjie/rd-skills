# Example Output

```markdown
## File Storage Design

Mode selected:
- Upload intake with media processing and lifecycle cleanup.

Source evidence:
- Current profile upload route, storage client, thumbnail worker, and cleanup job inspected.
- Repository memory of an existing quarantine prefix accepted after current bucket policy confirmation.
- No live cloud IAM/KMS, CDN invalidation, scanner signature freshness, or 1 GiB load test verified in this planning pass.

File class: user profile image

Limits:
- Max 5 MB.
- Allowed: JPEG, PNG, WebP by MIME and magic bytes.

Storage:
- Raw upload: private quarantine prefix.
- Processed output: private media prefix with CDN read through authenticated app route.

Access:
- User can upload only for own profile.
- Signed upload URL expires in 10 minutes and is bound to content type and size.

Processing:
- Virus scan before image transform.
- Strip EXIF metadata.
- Generate 256px and 1024px variants idempotently.
- Run image transform in isolated worker with no network egress, 512 MB memory cap, and 30 s timeout.

Cleanup:
- Delete quarantined failed uploads after 24 hours.
- Delete old variants when profile image changes.

Validation map:
- Cross-tenant download denied -> integration test.
- Signed upload URL scope and TTL -> policy unit test.
- EICAR, MIME mismatch, oversized upload -> malicious fixture tests.
- EXIF stripping -> image metadata assertion.
- Worker timeout and memory ceiling -> processing test or not-verified residual risk.
- Quarantine cleanup -> scheduled job test and storage-growth metric.

Handoff and limits:
- Hand off to security-privacy-gate for upload threat review and reliability-observability-gate for large-file and cleanup telemetry.
- This design does not prove real cloud effective policy, CDN deletion propagation, legal retention approval, or scanner availability until those validators run.
```
