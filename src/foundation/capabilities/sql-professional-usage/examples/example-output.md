# Example Output

```markdown
## SQL Review

Query: Paginated customer invoice list.
Injection: All filters parameterized.
Plan: Uses tenant_id and created_at composite index; no full scan at expected volume.
Pagination: Keyset pagination by created_at and id.
Semantics: UTC timestamps; NULL paid_at handled explicitly.
Decision: Accept after integration test with boundary rows.
```
