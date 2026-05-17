# Example Output

```markdown
## Documentation Update Plan

Audience:
- API consumers and on-call operators.

Docs to update:
- README configuration section.
- API reference for POST /exports.
- Release notes for export eligibility change.

Source evidence:
- src/routes/exports.py
- docs/openapi.yaml
- tests/integration/test_exports.py

Required updates:
- New 409 error example for active export conflict.
- Environment variable EXPORT_MAX_ROWS with default and limit.
- Rollback note that queued exports keep old eligibility snapshot.

Verification:
- Compare docs examples against OpenAPI schema and integration tests.
```
