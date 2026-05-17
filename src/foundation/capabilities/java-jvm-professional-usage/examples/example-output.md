# Example Output

```markdown
## JVM Usage Review

Transaction: Service method is called through Spring proxy and owns commit boundary.
Threading: Named bounded executor replaces common pool use.
Exceptions: Provider timeout maps to external dependency exception.
GC Risk: No new allocation-heavy loop on hot path.
Decision: Accept after transaction integration test.
```
