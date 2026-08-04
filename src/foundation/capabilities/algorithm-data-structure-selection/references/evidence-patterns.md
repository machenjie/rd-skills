# Algorithm Data Structure Evidence Patterns

Use this reference when closure depends on repository inspection, prior task evidence, observable action sequence, validation freshness, benchmark scope, tool permission boundaries, or production-scale evidence limits. Keep it as an evidence map, not a second algorithm tutorial.

## Scale Claim-To-Evidence Map

| Scale claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Input bound is trusted | Caller path, input owner, schema/API/file/event/page source, expected N, worst-case N, and reopen trigger | The inspected path has a declared size contract | Future callers, malformed producers, or production distribution shifts are covered |
| Selected structure matches access pattern | Operation type, selected structure, candidate alternatives, complexity, memory estimate, and rejected simpler option | The inspected choice fits the named local access pattern | Runtime allocator, database plan, cache invalidation, or UI rendering is optimal |
| Unbounded input is controlled | Stream/chunk/page/spill/reject decision, item/byte ceiling, ordering/cursor semantics, and oversize behavior | The inspected path avoids load-all growth under the declared limit | Production tail latency, queue lag, or every retry/checkpoint path is safe |
| Hot path is measured | Representative workload, benchmark/profile command, final source version, exit code, report path, and baseline comparison | The inspected code was measured for the named workload | All traffic mixes, hardware, dependency latency, or future data skew are covered |
| Stable ordering is preserved | Tie-breaker, deterministic key, pagination/replay/dedupe fixture, and owner of ordering contract | The inspected output order remains repeatable for the named case | Every client, locale, database collation, or distributed merge ordering is proven |
| Approximation is accepted | Error bound, false-positive/negative behavior, fallback, owner approval, and monitoring or regression test | The inspected approximate structure has a declared correctness envelope | Business acceptance cannot change or every edge case remains acceptable |
| Graph traversal is bounded | Max nodes/edges/depth, visited set, cycle fixture, frontier memory estimate, and traversal command | The inspected traversal terminates and caps memory for representative worst cases | Arbitrary production graphs, pathological fan-out, or concurrent mutation are safe |
| Prior task or source evidence claim is current | Prior claim source, current source reread, caller graph scan, final validation command, and freshness verdict | The accepted memory/graph lead still matches the inspected algorithm topology | Future edits, hidden dynamic callers, or production telemetry are covered |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old benchmarks, prior incidents, profiling reports, and generated docs as discovery inputs until current source and fresh validators confirm them.
- Accept a prior scale or ownership claim only while current callers, input sources, tests, reports, and ownership still match. Examples include "N is small", "caller is bounded", "benchmark passed", "DB owns the index", "cache makes it fast", and "graph has no cycles".
- Mark evidence stale after edits to caller paths, input contracts, data structures, sorting/grouping keys, pagination/cursor semantics, fixtures, benchmarks, generated data, reports, build outputs, or validation commands.
- Record inspected and skipped boundaries: caller path, input source, storage owner, cache owner, runtime owner, UI render path, graph traversal owner, benchmark workload, fixture/golden data, and release/runtime gates.
- For each final scale-confidence claim, cite a current command, representative benchmark or profile, query plan, test path, source path, or owner review. Otherwise, mark the claim unverified and name the residual scale risk and unexercised production skew.

- If local database/query-plan or large-fixture benchmark, record dataset, generated-input source, cleanup, credential boundary, timeout, and redaction rule.
- If production telemetry, profiling artifact, billing export, database plan, or controlled production-scale benchmark, require owner, bounded scope, timestamp, redaction, retention limit, and not-unit-test residual risk.
