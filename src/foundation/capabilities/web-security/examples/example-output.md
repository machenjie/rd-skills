# Example Output

```markdown
## Web Security Review

Change: Add profile avatar upload and public profile page.

Relevant Risks:
- Upload abuse, stored XSS through filename, broken access control.

Controls:
- Require authenticated user and ownership check before upload.
- Limit file size to 2 MB and allowlist jpeg and png content signatures.
- Store outside executable path and serve through image proxy.
- HTML-encode display name and filename in profile template.

Tests:
- User cannot upload avatar for another account.
- SVG and oversized files are rejected.
```
