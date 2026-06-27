---
name: algorithm-data-structure-selection
description: Selects algorithms and data structures from input scale, access pattern, time and space complexity, memory budget, streaming needs, skew, and benchmark evidence; use to avoid unbounded load-all and accidental O(n squared) implementations.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "109"
changeforge_version: 0.1.0
---

# Mission

Choose algorithms and data structures that match the real problem shape, expected and worst-case input scale, memory budget, access pattern, and operational constraints.

# When To Use

Use when code filters, joins, deduplicates, groups, sorts, ranks, searches, paginates, streams, chunks, traverses graphs, maintains caches, processes batches, or handles unbounded user, file, table, event, or API inputs.

Use when nested scans, load-all processing, top-K, prefix/range queries, hot keys, skew, approximate answers, online processing, or performance-sensitive paths are present.

# Do Not Use When

Do not use to over-optimize tiny bounded inputs where N is known, stable, and documented.

Do not replace a clear simple solution with a complex structure unless input scale, access pattern, or benchmark evidence justifies it.

# Stage Fit

Use during design when the implementation shape is still selectable, during coding when a loop, collection, query result, renderer, or batch path is being written, during review when code has already chosen a structure, and during testing when scale, worst-case, memory, or benchmark evidence must prove the choice. Repository graph, project memory, previous incidents, or prior profiling can suggest risk, but current source, caller paths, input ownership, and fresh validation decide the actual algorithm contract.

# Non-Negotiable Rules

- No algorithm choice without expected input size and worst-case behavior.
- No load-all when streaming or chunking is required by memory budget.
- No nested scan without bounded N or explicit complexity acceptance.
- Data structure must match access pattern.
- Memory budget must be explicit for unbounded inputs.
- Sorting, grouping, and top-K must justify complexity.
- Algorithmic optimization must be validated by test or benchmark when performance-sensitive.
- Repository graph or memory evidence cannot substitute for current-source scale evidence.
- Do not add indexes, caches, probabilistic structures, concurrency, or dependencies as "performance fixes" without a rejected simpler alternative and a validation plan.

# Industry Benchmarks

Anchor against Knuth algorithm analysis, CLRS data structure selection, database query planning principles, streaming processing practice, external sort and chunked processing, probabilistic data structures such as Bloom filters, cache eviction policies such as LRU/LFU, and benchmark-before-optimization discipline. Use [references/checklist.md](references/checklist.md) for quick selection checks, [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for complexity matrices and decision patterns, and [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on graph/memory/execution freshness, benchmark scope, or evidence limits.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Route or skip |
| --- | --- | --- | --- | --- |
| Local bounded collection | Small list, set, map, or sort with documented max size. | Keep the simplest readable structure. | Bound on N, access pattern, reason optimization is not needed. | Skip profiling unless a hot-path claim exists. |
| Hot path or large collection | Request path, rendering path, batch, worker, or repeated loop with large N. | Complexity, allocation, cache locality, and benchmark evidence. | Caller frequency, input size/distribution, time/space estimate, benchmark/profile or not-run rationale. | Route to `language-performance-safety` or `profiling` when measurement is needed. |
| Unbounded or external input | File, API page, DB result, event stream, queue, user payload, or generated data with no trusted max. | Streaming, chunking, pagination, backpressure, and rejection thresholds. | Item/byte ceiling, batch size, cursor/order semantics, memory estimate, oversize behavior. | Route to `reliability-observability-gate` when SLO, queue lag, or cost is affected. |
| Join, dedupe, grouping, or lookup | Nested scan, membership checks, joins, aggregation, top-K, prefix/range query. | Match data structure to access pattern. | Candidate table, selected structure, collision/identity/order semantics, rejected alternatives. | Route to `data-middleware-change-builder` when a DB/search/index owns the access path. |
| Skewed or adversarial input | Hot key, graph cycle, pathological sort/hash case, hostile size/count, or approximate answer. | Worst-case behavior, exactness, and abuse resistance. | Skew assumption, worst-case complexity, false-positive/exactness decision, mitigation. | Route to `security-privacy-gate` when input can cause DoS. |

# Selection Rules

Select this capability when the main risk is computational complexity or data access pattern. Use `solution-optimality-evaluation` for broader tradeoff review, `profiling` for measured bottlenecks, `language-performance-safety` for runtime allocation and IO implications, and `data-middleware-change-builder` when indexes, SQL plans, queues, search, or storage engines own the performance shape.

Keep ownership narrow. This capability selects the algorithm, structure, input bound, and complexity contract. It does not own database index design, cache eviction policy, retry/backpressure mechanics, runtime allocator tuning, UI virtualization mechanics, or distributed processing architecture; hand those surfaces off after the algorithm decision names the boundary.

# Risk Escalation Rules

Escalate to `reliability-observability-gate` when the algorithm affects SLOs, batch windows, queue lag, memory pressure, or cost. Escalate to `bigdata-product-extension` for distributed stream or batch jobs. Escalate to `security-privacy-gate` when adversarial input can trigger pathological complexity.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, mode selection, output, and gates. Use inline-only mode for L1/L2 bounded local choices where the output contract for time, space, memory, and rejected alternatives is enough. Read `references/checklist.md` when drafting or reviewing a concrete algorithm/data-structure decision. Read `references/benchmarks-and-patterns.md` for L3+ work, production-scale inputs, hot paths, unbounded load-all processing, unclear complexity, memory-budget risk, candidate comparison, or benchmark/profile interpretation. Read `references/evidence-patterns.md` when closure depends on accepted or rejected graph/memory claims, validation freshness, tool permission boundaries, benchmark scope, or what scale evidence proves versus what it does not prove. Do not load deep references for L1/L2 local changes where input size is bounded and the inline output contract is enough.

# Critical Details

- Map/list/set/heap/queue/deque/tree/trie/graph/Bloom filter/LRU/LFU/interval tree/segment tree choices must name the access pattern they optimize.
- Top-K usually prefers heap or selection over full sort when K is much smaller than N.
- Dedupe usually prefers set/hash index, but memory budget and collision/identity semantics must be clear.
- Grouping requires memory bound, spill strategy, or chunking plan for unbounded keys.
- Sorting requires stable ordering decision and O(n log n) or external sort rationale.
- Streaming beats load-all when input is unbounded, file-like, paged, or exceeds memory.
- Pagination and chunking need batch size, cursor/offset semantics, ordering, and retry behavior.
- Hot key and skew can dominate average complexity; name skew mitigation when distribution is uneven.
- Graph traversal requires BFS/DFS choice, visited set, cycle handling, and maximum frontier memory.
- Prefix/range queries require trie, ordered map/tree, index, or database range support.
- Probabilistic structures require false-positive rate and exactness acceptance.
- Online processing consumes inputs incrementally; offline processing can sort/index globally.
- Database-backed access should prefer query plans, indexes, cursors, or search engines when they own the scalable structure; do not duplicate a database index in application memory without a lifecycle and memory reason.
- UI collection work must account for render cost, virtualization, memoization, and stable keys; algorithmic speed is incomplete if the render path still blocks interaction.
- Parallelism only helps when partitioning is safe and coordination cost is smaller than saved work; estimate sequential fraction before adding workers.
- External sort, spill, checkpointing, and resumable chunks are normal solutions for inputs larger than memory, not exceptional complexity.
- Stable ordering is a contract when pagination, replay, dedupe, or user-visible ranking depends on repeatable results.

# Proactive Professional Triggers

- **Signal:** code loads all records, pages, files, events, or API results before filtering or grouping. **Hidden risk:** memory and latency fail at production volume. **Required professional action:** choose streaming, chunking, pagination, spill, or explicit rejection. **Route to:** `algorithm-data-structure-selection`, `language-performance-safety`. **Evidence required:** item/byte cap, batch size, ordering, and memory estimate.
- **Signal:** nested loops compare two collections, run membership checks on lists, or join data outside the database. **Hidden risk:** accidental O(n squared) work. **Required professional action:** evaluate hash index, set, sort-merge, database join, or bounded nested scan. **Route to:** `algorithm-data-structure-selection`, `solution-optimality-evaluation`. **Evidence required:** N and M, selected structure, complexity, and simpler alternative.
- **Signal:** full sort is used for first page, top-K, rank, or "latest N". **Hidden risk:** unnecessary O(n log n) work and memory. **Required professional action:** evaluate heap, selection, index-backed order, cursor, or bounded partial sort. **Route to:** `algorithm-data-structure-selection`, `test-strategy`. **Evidence required:** K versus N, ordering stability, memory bound, and benchmark or edge-case test.
- **Signal:** grouping, cache, map, or index key cardinality is unknown. **Hidden risk:** unbounded key growth, hot keys, memory leak, or partition skew. **Required professional action:** define key cardinality, eviction/spill/chunking, hot-key mitigation, or rejection threshold. **Route to:** `algorithm-data-structure-selection`, `cache-design`. **Evidence required:** expected distribution, worst case, and owner for residual skew.
- **Signal:** graph traversal, dependency walk, tree recursion, or route expansion lacks a visited set or frontier cap. **Hidden risk:** cycle, exponential expansion, or stack/memory failure. **Required professional action:** choose BFS/DFS/priority traversal with cycle handling and frontier bounds. **Route to:** `algorithm-data-structure-selection`, `regression-testing`. **Evidence required:** max nodes/edges/depth, cycle behavior, visited-set memory, and traversal test.
- **Signal:** optimization claim comes from intuition, project memory, or micro input tests only. **Hidden risk:** stale assumption closes the wrong performance gate. **Required professional action:** confirm current caller and production-like scale, or state not verified. **Route to:** `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** repository graph path, test/benchmark command, freshness, and limits.
- **Signal:** probabilistic, approximate, parallel, or concurrent structure is proposed. **Hidden risk:** exactness drift, race, nondeterminism, or operational complexity. **Required professional action:** prove exact/approximate acceptance, concurrency safety, and fallback. **Route to:** `algorithm-data-structure-selection`, `concurrency-control`. **Evidence required:** false-positive rate, determinism requirement, stress/benchmark plan, rejected exact alternative.
- **Signal:** application code mirrors database, search, cache, or queue state into an in-memory map/set/list for every request or worker tick. **Hidden risk:** stale data, memory leak, wrong ownership, and duplicated index behavior outside the source of truth. **Required professional action:** inspect storage owner, compare query/index/cache alternatives, and prove lifecycle plus memory bound before accepting the in-memory structure. **Route to:** `indexing-query-optimization`, `cache-design`. **Evidence required:** caller path, source-of-truth owner, item/byte estimate, validation command, and residual stale-data owner.
- **Signal:** stable ordering for pagination, replay, dedupe, or user-visible ranking depends on unordered map/set iteration or a sort without deterministic tie-breakers. **Hidden risk:** duplicate pages, missing records, inconsistent ranking, and silent replay drift. **Required professional action:** inspect the ordering contract, require deterministic tie-breaker fields, and verify fixture or golden ordering. **Route to:** `algorithm-data-structure-selection`, `regression-testing`. **Evidence required:** ordering contract, tie-breaker field, fixture path, validation command, exit code, and residual ordering owner.
- **Signal:** benchmark or profile evidence uses a tiny fixture, random data without skew, or a command run before the final source edit. **Hidden risk:** stale or unverified evidence hides production memory, latency, hot-key, or skew failure. **Required professional action:** compare the workload matrix with the current caller, rerun affected commands after the final edit, or document the not-run limit. **Route to:** `profiling`, `validation-broker`. **Evidence required:** workload matrix, command, exit code, report path, and what the evidence does not prove.

# Execution Coupling

- **Repository graph:** inspect the caller, input origin, fan-in/fan-out, data owner, and test owner before accepting scale assumptions. A utility loop in isolation is not enough evidence if the caller passes unbounded data.
- **Project memory:** use prior incidents, reports, and historical comments only as leads. Accept them only after current source, current registry/routing, telemetry, or explicit not-verified disclosure confirms freshness.
- **Execution path:** map the selected algorithm to a validation command or artifact: unit edge cases for bounded logic, benchmark/profile for hot paths, load/stress for concurrency, query plan for database-backed access, and fixture/golden tests for stable ordering.
- **Plan consistency:** if the implementation changes after benchmark or validation, re-run affected checks or mark evidence stale. Do not report a smoke, lint, or small fixture pass as scale proof.

# Failure Modes

- **Load-all memory failure:** implementation reads millions of records into memory because the unit test used 20 records and no byte ceiling existed.
- **Nested-scan blowup:** two large collections are compared with nested loops when a map, set, sort-merge, or storage index would bound work.
- **Full-sort top-K waste:** code sorts an entire list to return the first page, latest N, or top 20 items.
- **Unbounded grouping growth:** grouping keys are user-, tenant-, event-, or file-derived with no cardinality, spill, chunking, or rejection strategy.
- **Hot-path list membership:** repeated membership checks use a list in a request, render, worker, or batch path where a set/map is required.
- **Traversal explosion:** graph/tree/dependency traversal lacks visited set, depth cap, frontier cap, or stable ordering.
- **Approximation drift:** probabilistic or approximate structure is added without false-positive rate, exactness acceptance, or fallback.
- **Cache masks complexity:** cache hides an O(n squared) path without eviction, source-of-truth, invalidation, or cold-cache behavior.
- **Parallelism increases contention:** workers are added to a mostly sequential or shared-state pipeline and raise coordination cost.
- **Stale small-input memory:** project memory says "this list is small" while the current caller now accepts paged, external, or generated data.

# Output Contract

Return an Algorithm/Data Structure Decision:

- Mode selected: trigger signal, selected mode, and skipped heavier mode with reason.
- Boundaries inspected: caller path, input origin, data owner, storage/runtime owner, tests, repository graph, and project memory accepted or rejected.
- Problem shape: operation type, data lifecycle, caller frequency, and correctness constraints.
- Input scale: expected N, worst-case N, distribution, bounded/unbounded status, trusted count source, and adversarial shape.
- Candidate approaches: approach table with time complexity, space complexity, memory estimate, exactness, ordering, and operational tradeoff.
- Selected structure: chosen data structure or algorithm and why it matches the access pattern.
- Complexity decision: average case, worst case, adversarial/skew behavior, accepted threshold, and simpler alternative decision.
- Memory budget: item count, byte estimate, allocation/growth cap, spill/rejection behavior.
- Flow control: streaming, chunking, pagination, cursor, checkpoint, and backpressure decision.
- Correctness semantics: stable ordering, identity/collision semantics, approximate versus exact decision, and determinism requirements.
- Rejected alternatives: simpler clear solution, database/index option, cache option, and parallel option accepted or rejected with reason.
- Validation evidence: test, benchmark, profile, query plan, load/stress, validator command, exit code, report artifact, or explicit not-run rationale with owner.
- Evidence proof: what evidence proves for this scale decision and what evidence does not prove about production tail, skew, memory pressure, or unrelated callers.
- Handoff boundaries: profiling, language runtime, database/index, cache, reliability, security, frontend rendering, or distributed processing next gate.
- Residual scale risk: remaining unknown, threshold that reopens the decision, and owner.

# Evidence Contract

Close the decision only when it names the production-scale N, input distribution, caller path, bounded or unbounded status, trusted size source, complexity and memory estimates, benchmark or not-run rationale for hot paths, tests for edge/worst cases, graph and memory freshness, validation command or validator result, exit code when a command ran, report or artifact path when produced, what evidence proves, what evidence does not prove, evidence limits, behavior preservation for existing callers, residual risk owner, and the next gate or handoff for storage/runtime/security/reliability concerns. If any of these facts are unknown, state the unknown and the conservative bound used instead of silently accepting the algorithm.

# Quality Gate

1. Complexity is stated.
2. Worst-case behavior is stated.
3. Memory bound is stated.
4. Unbounded input is streamed, chunked, paginated, or explicitly rejected.
5. Data structure fits access pattern.
6. Sorting, grouping, dedupe, top-K, graph, prefix, or range query choice is justified.
7. Benchmark or profile evidence exists for hot paths.
8. Simpler alternative is considered and accepted or rejected with reason.
9. Caller path, input origin, and owner boundary are inspected or marked not verified.
10. Project memory or prior performance claims are freshness-scoped against current source.
11. Stable ordering, identity, collision, and exactness semantics are declared when they affect correctness.
12. Skew, hot key, adversarial input, and graph cycle risks are handled or explicitly accepted.
13. Validation evidence is fresh after the final material edit and matches the scale risk being claimed.
14. Handoff is made when storage, runtime allocation, cache, concurrency, security, UI rendering, or distributed execution owns the remaining risk.

# Used By

- backend-change-builder
- frontend-change-builder
- data-middleware-change-builder
- reliability-observability-gate
- ai-code-review-refactor
- quality-test-gate
- architecture-impact-reviewer

# Handoff

Hand off to `solution-optimality-evaluation` for broader alternatives, `profiling` for measurement, `language-performance-safety` for allocation/runtime risks, `indexing-query-optimization` for database-backed access, `cache-design` for eviction, and `bigdata-product-extension` for distributed processing.

# Completion Criteria

The capability is complete when the implementation has a scale-aware algorithm decision, the selected structure matches access patterns, unbounded inputs are bounded by streaming/chunking/pagination, complexity and memory are explicit, and performance-sensitive choices have test or benchmark evidence.
