# Example Output

```markdown
## Search Design

Decision: Use search index for knowledge base articles because users need full-text
ranking, category filters, and language facets.

Source of Truth:
- articles table remains authoritative.
- Index stores title, body_summary, tags, language, visibility, and updated_at.

Freshness:
- Target index freshness under 2 minutes.
- UI can show stale results but article detail rechecks source visibility.

Reindex:
- Build new index version in parallel, compare counts by visibility, then switch alias.

Fallback:
- If search is down, provide category browse with reduced filtering.
```
