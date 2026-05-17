# Example Output

```markdown
## Threat Model

Change: Add customer document upload endpoint.

Assets:
- Customer documents, account identity, storage credentials, audit events.

Trust Boundaries:
- Browser to API.
- API to object storage.
- Worker to malware scanning service.

Abuse Cases:
- Upload executable content as a document.
- Access another account's document by changing id.
- Exhaust storage with oversized files.

Mitigations:
- Enforce ownership before upload and download.
- Validate type, size, extension, and content signature.
- Store with private ACL and scan before release.
- Alert on scan failures and abnormal upload volume.
```
