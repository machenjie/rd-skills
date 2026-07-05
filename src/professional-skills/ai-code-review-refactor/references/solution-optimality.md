# Solution Optimality Self-Check — AI Code Review & Refactor

Compiled from foundation capability `solution-optimality-evaluation`. Apply when
reviewing AI-generated code that makes algorithmic choices, introduces data structures,
changes concurrency models, or claims performance improvements. Loaded on demand per the
skill's Reference Loading Policy.

**Three-Challenge Rule** — apply to every non-trivial AI-generated design decision:
1. **Why did the model choose this approach?** AI output optimizes for plausibility, not optimality. Explicitly reconstruct the choice rationale — if it cannot be stated, the choice needs justification from the reviewer.
2. **Is there a simpler sufficient implementation?** AI tends toward over-engineering (gratuitous factories, abstract base classes, generic handlers for a single use case). Ask: what is the minimum structure that satisfies the actual requirements?
3. **What is the strongest alternative, and why is the AI's choice preferred?** If the AI's approach cannot be defended against the simplest alternative with a concrete reason, it should be replaced.

**Algorithm and Performance Optimality Review** — verify each dimension for AI-generated code on non-trivial paths:

| Dimension | Required Review Question | AI-Specific Failure Mode |
|---|---|---|
| **CPU / Algorithm** | What is the time complexity of the generated algorithm? Did the AI choose the correct complexity class for the problem and data scale? Did a refactor change the complexity — for better or worse? | AI generates an O(n²) sort or nested loop where an O(n log n) or O(n) approach exists; refactor accidentally changes O(n log n) to O(n²) by removing a pre-sort step |
| **Memory** | Does the generated code allocate more objects per call than the original? Are AI-introduced collections or caches bounded? Does the AI-generated code hold references that prevent GC? | AI introduces a memoization cache without eviction bounds; AI-generated builder pattern allocates an intermediate object per call that was not present in the original |
| **Network** | Did the refactor change the number of I/O calls? Does AI-generated code introduce N+1 patterns that were absent before? | AI refactors a batched query into a per-item loop call; AI replaces a bulk API call with individual calls "for clarity" |
| **Disk** | Did the refactor change write patterns, log verbosity, or file I/O behavior? | AI adds debug logging inside a hot loop; AI introduces synchronous file writes where the original used async |
| **Locks / Contention** | Did the refactor introduce or remove thread-safety mechanisms? Does AI-generated concurrent code have hidden race conditions? | AI removes a lock "to simplify" code without understanding shared state; AI generates a double-checked locking pattern incorrectly |
| **TPS / QPS** | Did the refactor affect throughput? Are new AI-introduced blocking calls or synchronization points on the hot path? | AI converts an async operation to synchronous for "simplicity" — blocks the event loop or thread at high concurrency |
| **Concurrency** | Are AI-generated async patterns correct? Is there a potential goroutine/thread/promise leak in error paths? | AI generates `async` function with no error-path cleanup; generated goroutine is not bounded and leaks on repeated calls |
| **Response Latency** | Is there evidence that the AI-generated code meets the same or better latency profile as the original? | AI "simplifies" a query by adding a subquery that changes the query plan from index scan to sequential scan |
| **Cognitive Complexity** | Did the refactor decrease or increase cognitive complexity? A refactor that reduces cyclomatic complexity but increases nesting depth is not an improvement. | AI decomposes a flat function into 4 deeply nested helper functions — harder to follow the call chain than the original |

**AI-Specific Optimality Anti-Patterns to Reject:**
- **Premature generalization**: AI generates a plugin system, strategy pattern, or abstract factory for a single concrete use case. Reject unless ≥ 2 concrete implementations exist today.
- **Algorithm downgrade in refactor**: The AI "cleans up" code by removing a sort or deduplication step that was load-bearing for correctness or performance — the refactored version is O(n²) or incorrect.
- **Memoization without bounds**: AI adds `@lru_cache` or `useMemo` or `computedProperty` without specifying a max size. Unbounded memoization is a memory leak masquerading as an optimization.
- **Concurrency simplification that introduces races**: AI removes a lock or atomics "because the code looks simpler without it" — introduces a race condition that only manifests at high concurrency.
- **Over-verbose error handling that hides the real path**: AI wraps every line in a try/catch and returns `null` on error — the happy path is still correct but errors are silently swallowed and the cognitive complexity doubles.
