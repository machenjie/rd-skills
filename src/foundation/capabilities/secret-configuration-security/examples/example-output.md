# Example Output

```markdown
## Secret and Configuration Review

Change: Add payment provider API key.

Storage:
- Store production key in secret manager under payments/provider_api_key.
- CI receives only test key scoped to sandbox account.

Exposure Controls:
- Key is read by backend only and is not prefixed for frontend bundling.
- Authorization headers are redacted in logs and traces.
- Docs use PROVIDER_API_KEY placeholder only.

Rotation:
- Deploy support for key version v2, validate health check, then revoke v1.

Config Risk:
- Missing key fails startup in production.
```
