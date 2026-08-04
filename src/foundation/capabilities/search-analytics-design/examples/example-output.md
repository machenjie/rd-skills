# Example Output

```markdown
## Search Design

Decision: Use search index for knowledge base articles because users need full-text
ranking, category filters, and language facets.

Source of Truth:
- articles table remains authoritative.
- Index stores title, body_summary, tags, language, visibility, and updated_at.

Freshness:
- Freshness objective is derived from article-update and permission-change
  consequences and measured from source change to query-visible state.
- UI may show stale results, but article detail rechecks current visibility before
  disclosure.

Reindex:
- Build new index version in parallel, compare counts by visibility, then switch alias.

Fallback:
- If search is down, provide category browse with reduced filtering.
```
