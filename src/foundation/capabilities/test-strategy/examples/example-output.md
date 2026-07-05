# Example Output

```markdown
## Test Strategy

Change: Add account export API.
Risk: High because it exposes customer-owned data and a new API contract.

Required levels:
- Unit: export eligibility rules, field filtering, and permission checks.
- Integration: API request through repository with database fixture and denied role.
- Contract: response schema, error codes, pagination, and backward compatibility examples.
- E2E: admin exports one account and receives a downloadable file.
- Regression: guard previous permission bypass on archived accounts.

Omitted:
- Load test deferred because export is async and capped; verify queue depth metric instead.
```
