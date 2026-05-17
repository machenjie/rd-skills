# Example Output

```markdown
## File Storage Design

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

Cleanup:
- Delete quarantined failed uploads after 24 hours.
- Delete old variants when profile image changes.
```
