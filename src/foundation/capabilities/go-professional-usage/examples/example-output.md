# Example Output

```markdown
## Go Usage Review

Context: Request context reaches repository and outbound HTTP client.
Goroutines: Worker exits on context cancellation and closes result channel.
Error Handling: `%w` preserves provider timeout root cause.
Tests: Table tests cover validation; race detector required for cache update.
Decision: Accept after race test passes.
```
