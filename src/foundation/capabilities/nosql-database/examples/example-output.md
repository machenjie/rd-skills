# Example Output

```markdown
## NoSQL Storage Decision

Decision: Use a document read model for product catalog cards because the UI reads
complete cards by product id and can tolerate projection lag within the
consequence-derived freshness objective.

Access Patterns:
- Get product card by product_id.
- List cards by category_id and updated_at cursor.

Consistency:
- Source of truth remains relational product tables.
- Search/card projections may lag within that objective; freshness is measured
  from source change to query-visible state, and critical actions recheck source data.

Risks:
- Category hot spots are monitored through partition-level traffic, throttling,
  latency, and capacity signals available from the selected store.
- Projection drift is repaired by owned reconciliation triggered by drift evidence
  and targeted replay.
```
