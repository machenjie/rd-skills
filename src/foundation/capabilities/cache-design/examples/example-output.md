# Example Output

```markdown
## Cache Strategy

Source of Truth: relational account_settings table.

Cache Key:
- account_settings:v3:{account_id}
- Key is tenant scoped and does not include user-specific permissions.

Freshness:
- TTL 5 minutes with jitter.
- Invalidate on settings update by incrementing version and deleting old key.

Protection:
- Single-flight refresh for hot accounts.
- Negative cache missing account ids for 30 seconds.

Fallback:
- If cache is down, read source directly with rate-limited warnings.
```
