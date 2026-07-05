# Example Output

```markdown
## Performance Budget

Scenario: Project search with 50,000 records.

Budgets:
- API p95 latency under 250 ms in staging load test.
- Database query count at 1 query per search request.
- Response payload under 80 KB for first page.
- Frontend search route JS increase under 15 KB gzip.

Release gate:
- Block release if p95 exceeds threshold by more than 10 percent.
- Exception owner: search service lead, expires after next sprint.
```
