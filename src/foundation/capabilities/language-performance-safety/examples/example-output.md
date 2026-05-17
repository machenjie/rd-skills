# Example Output

```markdown
## Runtime Safety Assessment

Language: Python
Hot Path: Async ingestion endpoint.
Risk: CPU-heavy parsing runs inside the event loop.
Mitigation: Move parsing to worker pool and bound input size.
Evidence: Async timeout test plus benchmark under representative payload.
Decision: Block until event-loop blocking is removed.
```
