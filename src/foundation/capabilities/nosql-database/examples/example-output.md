# Example Output

```markdown
## NoSQL Storage Decision

Decision: Use a document read model for product catalog cards because the UI reads
complete cards by product id and tolerates 60 seconds of freshness lag.

Access Patterns:
- Get product card by product_id.
- List cards by category_id and updated_at cursor.

Consistency:
- Source of truth remains relational product tables.
- Search/card projections may lag up to 60 seconds and show "updating" state.

Risks:
- Category hot spots are monitored by read and write units.
- Projection drift is repaired by nightly reconciliation and targeted replay.
```
