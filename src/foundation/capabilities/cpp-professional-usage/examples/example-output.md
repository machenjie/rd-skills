# Example Output

```markdown
## Native Code Review

Ownership: File descriptor wrapped in RAII handle.
UB: Removed unchecked pointer arithmetic.
ABI: No public struct layout change.
Thread Safety: Atomic ordering documented for counter.
Checks: ASan, UBSan, unit tests.
Decision: Accept after sanitizer CI passes.
```
