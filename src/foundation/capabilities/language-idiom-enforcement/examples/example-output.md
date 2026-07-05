# Example Output

```markdown
## Idiom Review

Language: Go
Finding: Error is wrapped with context and `%w`; context is propagated to DB call.
Risk: A helper defines an interface before any consumer needs variation.
Action: Remove premature interface and keep concrete dependency.
Checks: gofmt, go vet, targeted tests.
Decision: Accept after interface cleanup.
```
