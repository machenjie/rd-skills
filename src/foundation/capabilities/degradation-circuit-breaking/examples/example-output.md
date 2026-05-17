# Example Output

```markdown
## Resilience Plan

Dependency: Recommendation service.
Core flow: Product detail page must load even when recommendations fail.

Behavior:
- Timeout recommendation call after 300 ms.
- Open circuit after 20 failures in 60 seconds.
- Show product page without recommendation rail while circuit is open.
- Half-open with 5 trial requests after 2 minutes.

Observability:
- Metric: recommendation_fallback_total.
- Alert when fallback rate exceeds 30 percent for 10 minutes.
```
