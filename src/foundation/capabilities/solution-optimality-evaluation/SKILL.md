---
name: solution-optimality-evaluation
description: Requires every implementation decision to be explicitly challenged for justification, alternatives, and optimality across algorithm complexity, code architecture, ten performance dimensions (CPU, memory, network, disk, locks, TPS/QPS, parallelism, concurrency, latency, rendering), code quality, and system properties before the approach is locked.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "82"
changeforge_version: 0.1.0
---

# Mission

Prevent premature lock-in on suboptimal design by requiring every significant implementation decision to pass a structured self-challenge before it is accepted. This capability enforces three questions before any approach is finalized: Why this way? Is this the simplest sufficient design? What is the strongest better alternative and why is it rejected? The answer must be backed by current evidence across algorithm complexity, resource use, maintainability, reversibility, graph/memory freshness, and validation trajectory.

# When To Use

Use this capability when: a new algorithm, data structure, or processing strategy is being selected; a significant design decision affects performance, scalability, or maintainability; a builder or reviewer skill must assess the optimality of proposed or existing code; a performance-sensitive path (hot path, critical user flow, batch job, rendering path) is being designed or modified; code is being accepted that will be maintained by others for years; or a change creates resource consumption patterns whose magnitude is unknown or unverified.

# Do Not Use When

Do not use this capability for: trivial one-liner mechanical fixes with no design decision surface; pure cosmetic formatting or style changes; documentation edits; configuration values specified by an external requirement; or early throw-away prototypes explicitly scoped to prove feasibility only (must be re-evaluated before any prototype enters production code paths).

# Boundary And Source Truth

This capability owns decision challenge evidence, not implementation ownership for every specialist domain. It decides whether a proposed approach is justified enough to proceed, whether a simpler/reused/deleted approach should replace it, and which specialist gate must supply missing evidence. Source truth is the current code, current registry/config, representative benchmark/profile/load output, current repository graph slice, current project memory reconciliation, and validation that ran after the final material edit. Memory, generated reports, historical benchmarks, context packs, and prior summaries are selectors only until current source and validation confirm them.

# Stage Fit

- **Requirement / intake**: restate the decision question as a problem, not a proposed solution; name non-goals, constraints, and production-scale input assumptions before candidate generation.
- **Architecture / design**: compare candidate boundaries, data structures, dependency choices, reversibility, and deletion/reuse options before topology or API shape is locked.
- **Implementation / review**: challenge AI-generated or first-working code for over-engineering, algorithm downgrade, hidden I/O, allocation, concurrency, and cognitive complexity before approval.
- **Testing / release**: verify benchmark/profile/load evidence, validation freshness, deferral thresholds, owner, rollback, and residual risk before the choice is treated as production-ready.

# Non-Negotiable Rules

- **The three-challenge rule**: Before locking any significant design decision, explicitly answer: (1) Why is this the right approach for this specific problem and context? (2) Is this the simplest design that satisfies all current requirements without speculation? (3) What is the strongest alternative, and why is it rejected with a specific, concrete reason? If none of these questions can be answered, the decision is not ready to implement.
- **Deletion/reuse challenge**: Before optimizing or expanding a solution, ask whether the correct answer is to delete code, reuse existing code, use a standard-library or native platform feature, shrink scope, or keep a local direct implementation. A more elaborate solution is not optimal when a simpler current option satisfies the same requirement and safety gates.
- **Measure before optimizing; never optimize by intuition alone**: A hypothesis that "this is slow" is the beginning of investigation, not the end. Profile first. The bottleneck revealed by measurement frequently differs from the initial hypothesis. Optimizing the wrong layer wastes time and introduces new defects.
- **Hot path analysis precedes optimization**: Identify whether the code being evaluated is on the critical path (called thousands of times per second) or the cold path (called once per day). Optimization effort must be proportional to frequency and production impact — premature optimization of cold paths reduces readability without meaningful benefit.
- **The deferred optimization trap is a production incident waiting to happen**: "We can optimize it later" is an escalation signal, not an acceptable resolution. If the current approach is known to be unacceptable at production scale, it must be fixed or the condition must be explicitly documented (the exact threshold at which it becomes unacceptable and who owns the remediation).
- **Worst-case and average-case are both required**: Stating that an algorithm is O(n log n) average-case is insufficient if the pathological input (sorted data, adversarial input, full cache miss, cold start) produces O(n²) or worse. Define the expected input distribution and the worst-case behavior explicitly.
- **All ten performance dimensions must be explicitly evaluated or declared N/A with a one-line rationale for every builder skill output**: Skipping a dimension is not an option. A dimension marked N/A without rationale is treated as skipped and the output is incomplete.
- **Cognitive complexity is a first-class engineering constraint**: Code that requires 30 minutes to understand on first read will be misread under incident pressure. If an implementation is clever, it must be justified against a simpler alternative. Cognitive complexity ≤ 15 per function is the professional standard (SonarSource definition); functions above 25 must be decomposed.
- **Reversibility must be stated explicitly**: Is this decision reversible without data migration, customer impact, or downtime? Irreversible decisions require explicit acknowledgment and a higher bar of justification evidence.
- **Graph, memory, and execution evidence are never proof by themselves**: repository graph, project memory, prior validation, generated reports, and old benchmark notes can widen the review scope, but current source inspection and post-edit validation must confirm every behavior-critical claim.

# Industry Benchmarks

Use [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when the main body is not enough. The reference carries the deeper benchmark anchors, self-challenge framework, ten-dimension matrix, data-locality notes, back-pressure patterns, fan-out tail-latency math, cache-stampede review, hot-key detection, pool sizing, GC/allocation checks, cognitive complexity thresholds, reversibility classes, testability, security-surface, and cost-awareness details.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Algorithm / data structure decision | New scan, join, rank, dedupe, graph traversal, search, cache, index, or collection strategy. | Choose by input size, distribution, complexity, memory, and simplest sufficient structure. | Candidate set, O-time/space, N/M bounds, rejected alternatives, benchmark/profile need. | `algorithm-data-structure-selection`, `profiling` |
| Architecture / abstraction decision | New service, adapter, plugin point, framework, dependency, or reusable abstraction. | Prevent speculative generality and irreversible boundary cost. | Current use cases, deleted/reused option, dependency direction, reversibility, owner. | `architecture-impact-reviewer`, `implementation-structure-design` |
| Performance / resource decision | Hot path, batch, rendering path, worker, pool, queue, fan-out, or resource budget changes. | Bind design to latency, throughput, memory, cost, and saturation evidence. | Budget, workload shape, representative measurement or planned gate, residual unknowns. | `performance-budgeting`, `reliability-observability-gate` |
| AI review / refactor decision | AI-generated code, automated refactor, or "cleaner" rewrite changes structure or complexity. | Detect plausibility bias, algorithm downgrade, over-abstraction, hidden I/O, and stale tests. | Before/after behavior, complexity delta, strongest simpler alternative, changed-path validation. | `ai-code-review-refactor`, `quality-test-gate` |
| Evidence freshness decision | Graph, memory, old benchmark, prior summary, or validation pass influences approval. | Reconcile selector evidence with current source and command order. | Accepted/rejected memory, graph freshness, validation-after-final-edit status. | `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` |
| Skill / evaluation decision | Capability, skill, reference, routing, or benchmark changes claim better professionalism or efficiency. | Preserve depth while controlling reference budget and structural-only claims. | Baseline score/audit, treatment diff, selected/skipped references, validation limits. | `skill-efficacy-benchmark`, `skill-authoring-expert` |

# Selection Rules

Apply this capability when an implementation choice is non-trivial and the stakes are non-trivial: production traffic, data integrity, security, cost, user experience, operational load, or multi-year maintainability. The three-challenge rule applies to builder and reviewer outputs. The ten-dimension checklist applies when the change touches performance-sensitive paths, resource allocation, external I/O, concurrency, rendering, or high-volume data. Use it as a precision gate: broad enough to catch hidden design debt, narrow enough to avoid turning every small edit into an architecture review.

# Proactive Professional Triggers

- **Signal:** the first working solution is accepted without candidates, scale assumptions, or rejected alternatives. **Hidden risk:** plausible code becomes production policy before the tradeoff is understood. **Required professional action:** require a decision question, at least two viable approaches, and a specific rejection reason. **Route to:** `solution-optimality-evaluation`, `ai-code-review-refactor`. **Evidence required:** candidate set, chosen rationale, rejected option, validation plan.
- **Signal:** code scans, joins, sorts, groups, caches, ranks, paginates, fans out, or traverses data without expected input distribution. **Hidden risk:** tests pass on tiny fixtures while production hits O(n squared), OOM, hot-key, or tail-latency failure. **Required professional action:** establish N/M bounds, complexity, memory, and representative benchmark/profile need. **Route to:** `algorithm-data-structure-selection`, `performance-budgeting`. **Evidence required:** production-shape input, complexity report, budget, benchmark/profile command or not-run limit.
- **Signal:** AI-generated code introduces abstractions, helpers, generic handlers, memoization, concurrency, or error wrappers. **Hidden risk:** AI optimizes for plausibility and symmetry, not the minimum safe structure. **Required professional action:** apply the three-challenge rule and deletion/reuse challenge before approving the generated shape. **Route to:** `ai-code-review-refactor`, `code-clarity-maintainability`. **Evidence required:** before/after complexity, simpler sufficient implementation, hallucinated API scan, tests.
- **Signal:** a design is defended by "fast enough", "best practice", "standard pattern", "we can optimize later", or historical memory. **Hidden risk:** authority, reputation, or stale memory replaces current evidence. **Required professional action:** require current graph/source confirmation, measurement or budget, and a deferral threshold with owner. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** source/read scope, accepted/rejected memory, validation freshness, owner.
- **Signal:** a new dependency, service boundary, queue, cache, plugin layer, or data migration is introduced for one concrete use case. **Hidden risk:** reversibility and operational cost are hidden by local elegance. **Required professional action:** compare delete/reuse/local direct implementation, classify reversibility, and name rollback or exit cost. **Route to:** `architecture-impact-reviewer`, `technology-stack-selection`, `release-rollback`. **Evidence required:** current use cases, cheaper alternative, reversibility class, owner.
- **Signal:** validation, benchmark output, generated report, or review approval predates a later implementation edit. **Hidden risk:** closure certifies a version that is no longer the shipped content. **Required professional action:** rerun mapped validators or mark evidence stale/partial. **Route to:** `execution-trajectory-analysis`, `quality-test-gate`. **Evidence required:** command order, changed files, covered paths, rerun result or residual risk.

# Reference Loading Policy

- **L1 default:** use this `SKILL.md` for trigger selection, three-challenge framing, output shape, and quality gates.
- **L2 decision work:** load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when drafting the ten-dimension matrix, evaluating performance/resource tradeoffs, or checking advanced failure patterns.
- **L3 specialist coupling:** pair only the selected specialist capabilities: `algorithm-data-structure-selection`, `performance-budgeting`, `profiling`, `language-performance-safety`, `concurrency-control`, `reliability-observability-gate`, `architecture-impact-reviewer`, `security-privacy-gate`, or `quality-test-gate`.
- **L4 evidence coupling:** pair with `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when graph, memory, generated reports, old benchmarks, or validation order influence approval.
- **Anti-bloat rule:** do not load every performance, language, database, reliability, or architecture reference. Select only references required to answer the current decision and state skipped high-cost references with a reason.

# Risk Escalation Rules

- Escalate to `algorithm-data-structure-selection` when the core decision is data shape, complexity class, lookup/join strategy, indexing, caching structure, traversal, or streaming/chunking.
- Escalate to `profiling` when a performance dimension evaluation identifies an unknown bottleneck that cannot be assessed without measurement data from representative load.
- Escalate to `performance-budgeting` when no latency, throughput, or resource budget exists for the component being designed, and one must be established before the evaluation can be completed.
- Escalate to `language-performance-safety` when allocation, GC, event loop blocking, FFI/native boundary, runtime pool, lock behavior, or language-specific resource lifecycle decides the choice.
- Escalate to `architecture-impact-reviewer` when the optimality evaluation reveals that the best approach requires a structural change to the system architecture (new boundary, new service, dependency direction change).
- Escalate to `data-middleware-change-builder` when database query patterns, indexing strategies, lock contention, or storage engine behavior require expert evaluation.
- Escalate to `reliability-observability-gate` when the evaluated change affects SLI/SLO-bound production paths.
- Escalate to `security-privacy-gate` when the chosen approach expands input, output, dependency, command, file, prompt, data, authorization, or secret surface.
- Escalate to `validation-broker` or `quality-test-gate` when the decision cannot be closed without a changed-path-to-validator map, representative benchmark, load/profile command, or stale-validation repair.
- Escalate when cognitive complexity analysis reveals code that cannot be safely maintained — refactoring is required before handoff.

# Critical Details

- The most common optimality failure is not choosing a bad algorithm — it is failing to ask the question at all. The default is to accept the first working approach. This capability makes "first working" an insufficient standard.
- O(n²) algorithms in production code are not theoretical concerns: 10,000 items → 100M operations; 100,000 items → 10B operations. Always identify the production-scale input size before accepting an algorithm.
- The ten performance dimensions are not independent. Optimizing for CPU may increase memory (memoization trades memory for CPU cycles). Optimizing for throughput may increase latency variance (batching reduces per-unit CPU at the cost of higher average latency). Explicitly document the tradeoff accepted.
- Fan-out tail latency is the most consistently underestimated production problem. Engineers test a single downstream call, measure P99=50ms, and declare performance acceptable — without modeling that 10 parallel calls at P99=50ms each creates an aggregate tail latency problem affecting a significant percentage of all requests.
- Deferred optimizations accumulate interest. Each "we'll fix it later" increases the cost of the fix as surrounding code grows, tests multiply, and the pattern is copied. Professional discipline: fix it now or document the threshold at which it must be fixed with a named owner.
- The strongest rejected alternative must be specific enough that a reviewer can disagree with it. "Existing helper", "database join", "streaming iterator", "feature flag", or "delete the abstraction" is useful; "other approach" is not.
- A benchmark that uses dev data, a single local run, or stale generated reports can identify a risk, but it cannot prove production readiness without scope and evidence limits.

# Failure Modes

- **Algorithm accepted on first-pass plausibility**: A correct O(n²) sort accepted because it "works in tests" — tests use 10 records; production has 10 million.
- **Performance dimensions skipped**: Latency and throughput were checked; memory was not — the new batch job causes OOM in its first production run.
- **Deferred optimization never revisited**: "We'll optimize when it becomes a problem" — the problem arrives at 2 AM during peak traffic, not during a planned engineering sprint.
- **Fan-out tail latency not modeled**: A feature calls 12 downstream services; P99 was measured per-service but not for the aggregate response.
- **Thundering herd on cache invalidation**: Cache was cleared on deploy; all 800 concurrent users hit the database simultaneously; the database ran out of connections.
- **Cognitive complexity exceeded**: A "clever" bitwise-and-ternary implementation reduced CPU by 3% but required a 45-minute onboarding session — maintainers copied it incorrectly in the next sprint.
- **GC pressure invisible in development**: Per-request object allocation looked fine locally; at 2,000 RPS, GC pause spikes appeared as 200ms P99 spikes visible only in production load testing.
- **Irreversible decision without acknowledgment**: A destructive schema migration was applied; a rollback was triggered for an unrelated reason; the dropped column data was permanently lost.
- **Hot key undetected**: A new feature hashed all new users to the same Kafka partition; one partition's consumer was the bottleneck for the entire pipeline.
- **False sharing in concurrent counter**: Two independent counters placed adjacently in a struct caused cache-line thrashing at 200 concurrent threads — performance degraded worse than a single-threaded baseline.
- **Selector overclaim**: project memory, old graph output, or a prior benchmark is reported as proof even though source and validation changed later.
- **Over-engineered abstraction accepted**: a generic plugin/factory/adapter layer is added for one use case; the future use case never arrives, but every maintainer pays the complexity cost.

# Output Contract

Return an optimality evaluation that includes:
- **Mode selected**: algorithm/data structure, architecture/abstraction, performance/resource, AI review/refactor, evidence freshness, or skill/evaluation decision, with trigger signal.
- **Decision boundary**: problem statement, non-goals, constraints, source-of-truth files, affected path, hot/cold path classification, and skipped boundaries with reasons.
- **Graph / memory / execution coupling**: current graph evidence, accepted/rejected project memory, validation order, stale evidence, and direct-source fallback.
- **Three-challenge answers**: (1) Why this approach — specific evidence. (2) Is it the simplest sufficient design — yes/no with rationale. (3) Strongest alternative rejected — name it, state the specific cost.
- **Deletion/reuse answer**: delete, reuse, stdlib/native, existing dependency, local direct code, or new implementation decision, with the specific reason the simpler option is accepted or rejected.
- **Candidate comparison**: at least two viable approaches, ideally three for material decisions, with complexity, memory, I/O, reversibility, and ownership tradeoffs.
- **Ten-dimension assessment**: For each dimension: rating (✓ Satisfactory / ⚠ Risk / ✗ Unacceptable / N/A with one-line rationale), key evidence, and any required action.
- **Additional considerations applied**: Which (if any) of the additional professional considerations apply and the finding.
- **Budget and measurement status**: latency, throughput, memory, cost, query, rendering, queue, pool, or worker budget used; benchmark/profile/load evidence run or planned.
- **Cognitive complexity assessment**: ≤ 15 per function (pass) / > 15 and ≤ 25 (note decomposition opportunity) / > 25 (decomposition required before handoff).
- **Reversibility classification**: Reversible / Conditionally reversible / Irreversible — with one-line rationale.
- **Optimization deferral log**: If any dimension is accepted as "not optimal but currently acceptable," document the threshold condition and named owner for revisit.
- **Validation map and evidence limits**: validator, benchmark, profile, load, review, or build evidence tied to changed paths; what each proves and what remains unproven.
- **Handoff**: next specialist gate, owner, rollback clue, residual risk, and the condition that would reopen the decision.

# Evidence Contract

Close an optimality evaluation only when these answers are concrete:
- **Basis**: the selected mode, decision question, stakes, constraints, candidate set, and why optimality review is required.
- **Current evidence**: source files, registry/config/docs, graph slice, memory signals, prior benchmark/report, validation output, and skipped boundaries inspected with freshness status.
- **Challenge and tradeoff**: three-challenge answers, deletion/reuse decision, strongest rejected alternative, complexity/resource tradeoff, cognitive complexity, and reversibility.
- **Validation and measurement**: commands, benchmarks, profiles, load checks, static analysis, tests, or explicit not-run limits, each tied to changed paths and run after final material edits when used for closure.
- **Judgment and handoff**: accepted design, rejected design, deferral threshold and owner, evidence limits, rollback note, residual risk, and next gate.

# Quality Gate

1. All three challenge questions are answered with specific evidence, not assertions.
2. All ten performance dimensions are evaluated or declared N/A with a one-line rationale.
3. At least one alternative approach is explicitly named and rejected with a specific cost reason.
4. Cognitive complexity of the chosen implementation is ≤ 15 per function, or a decomposition plan is specified for functions exceeding 25.
5. Reversibility classification is stated.
6. Any accepted "deferred optimization" has a documented threshold condition and a named owner for revisit.
7. Delete/reuse/standard-library/native-platform/local-direct implementation was considered before adding abstraction, dependency, cache, queue, service, plugin, or framework structure.
8. Production-scale input, workload, or data distribution is stated, or the missing scale evidence blocks/defers approval.
9. Graph, memory, generated reports, old benchmarks, and prior validation are reconciled with current source and command order before they influence approval.
10. Validation evidence covers the final material diff, or stale/partial/not-run status is explicit with residual risk.
11. Performance, reliability, security, data, architecture, and language specialist gates are selected or intentionally skipped with reasons.
12. Reference loading is bounded to selected risks and does not dump unrelated performance or language material into context.
13. Evidence limits prevent broad claims such as live production readiness, universal agent behavior improvement, or real-world performance gain without representative evidence.

# Benchmark Coverage

This capability covers algorithmic complexity, resource budgets, candidate comparison, AI-generated design review, cognitive complexity, reversibility, system properties, graph/memory/trajectory freshness, and validation-after-final-edit discipline. It does not by itself prove live production performance, user productivity, or long-term maintainability without representative runtime, review, and ownership evidence.

# Routing Coverage

Routes from `backend-change-builder`, `frontend-change-builder`, `data-api-contract-changer`, `data-middleware-change-builder`, `integration-change-builder`, `architecture-impact-reviewer`, `reliability-observability-gate`, `change-impact-analyzer`, `ai-code-review-refactor`, `quality-test-gate`, and `change-forge-router` should arrive here when implementation choices, alternatives, complexity, performance dimensions, simplicity, reversibility, or stale evidence decide whether a design is acceptable.

# Used By

backend-change-builder, frontend-change-builder, data-api-contract-changer, data-middleware-change-builder, integration-change-builder, ai-code-review-refactor, architecture-impact-reviewer, reliability-observability-gate, change-impact-analyzer

# Handoff

- **profiling** — when measurement under representative load is needed to answer performance dimension questions.
- **performance-budgeting** — when budgets are undefined and must be established before evaluation proceeds.
- **architecture-impact-reviewer** — when the evaluation reveals a required structural change.
- **data-middleware-change-builder** — when database-layer performance analysis (query plans, index design, lock contention) requires depth beyond this capability's scope.

# Completion Criteria

The evaluation is complete when: all three challenge questions have justified answers with specific evidence; all ten performance dimensions have been assessed with evidence or declared N/A with rationale; the cognitive complexity is within bounds or a decomposition is proposed for out-of-bounds functions; the reversibility classification is stated; and any accepted deferred optimizations have a documented threshold condition.
