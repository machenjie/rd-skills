---
name: language-runtime-selection
description: Use when selecting or reviewing programming language and runtime choices against workload shape, type safety, concurrency, memory behavior, deployment model, ecosystem maturity, observability, security, lifecycle, and maintainability.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "84"
changeforge_version: 0.1.0
---

# Mission

Select or review programming language and runtime choices against workload shape, type-safety needs, concurrency and memory model, deployment topology, ecosystem and supply-chain posture, observability tooling, runtime lifecycle, hiring market, and long-term maintainability. Reject language choice based on familiarity, novelty, or trend; require evidence that the chosen runtime matches the workload's actual failure modes.

# Pinned Tooling Baseline

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

Use active vendor or community support policies as the runtime-selection baseline; reject EOL runtimes unless an explicit exception, migration owner, and retirement date are approved.

# When To Use

Use when language is not yet chosen, a new language is proposed in an existing system, runtime behavior materially affects correctness or latency, or a workload must be classified against CPU-bound, IO-bound, latency-sensitive, memory-sensitive, batch, interactive, embedded, edge, or contract-heavy constraints. Use whenever the choice will commit ≥ 1 team to operate the runtime for ≥ 1 year. Also use when repository graph, project memory, or execution traces show runtime drift, unsupported versions, stale benchmark assumptions, or unverified workload claims.

# Do Not Use When

Do not use for language lessons, syntax preference debates, religious wars, or migration enthusiasm absent workload evidence and operational ownership. Do not use for like-for-like minor version upgrades (use `package-dependency-management`).

# Stage Fit

- **Discovery / intake** — classify workload, ownership, existing approved runtimes, and hard constraints before candidate preference is accepted.
- **Design / architecture** — compare candidates using repo graph, project memory, runtime lifecycle, and workload evidence before stack selection is frozen.
- **Implementation / review** — verify selected language-specific rules, toolchain pins, tests, and runtime failure modes before code expands.
- **Release / operation** — re-check lifecycle, deployment shape, observability, and rollback cost before production commitment.

# Non-Negotiable Rules

- **Operational ownership precedes the decision.** A language without a named on-call owner is rejected regardless of technical merit.
- **Workload classification is mandatory.** State the workload as: CPU-bound / IO-bound / latency-sensitive / memory-sensitive / batch / interactive / streaming / embedded / edge / contract-heavy. The runtime must match the dominant axis.
- **Runtime behavior must be enumerated before commitment**: GC class (none / generational / concurrent / region-based), pause SLO impact, concurrency model (threads / coroutines / event-loop / actor / CSP), exception model, FFI cost, startup time (cold-start budget), binary/image size, package manager integrity model, observability tooling (profiler, tracer, heap-dump, allocator-stats), debugger availability in production.
- **Existing-runtime preference is the default.** Adding a new language costs ≥ 1 engineer-FTE-year of operational overhead (CI lanes, deploy pipeline, vulnerability scanner integration, on-call training, knowledge spread). Justify the addition against that cost.
- **Hiring-market check is mandatory.** ≥ 100 addressable candidates locally, or in-house upskilling plan with named timeline. Esoteric / academic / single-vendor languages require explicit acceptance.
- **Boundary validation is not replaced by compile-time types.** Type systems prevent internal mistakes; external inputs (HTTP, queue, file, FFI) still require runtime validation regardless of language.
- **Runtime lifecycle horizon ≥ 3 years.** Vendor or community support roadmap, LTS schedule, breaking-change cadence must be published and credible. Pre-1.0 runtimes for production-critical work require explicit risk acceptance and exit plan.
- **Current evidence is mandatory.** Cite repository graph signals, project memory or prior decision records with dates, workload measurements or SLOs, runtime support policy, and executable validation; missing evidence blocks approval.

# Industry Benchmarks

- **ThoughtWorks Tech Radar** for language maturity (Adopt / Trial / Assess / Hold).
- **TIOBE / StackOverflow Developer Survey / RedMonk** for hiring-market signal.
- **Google SRE Workbook — Production Readiness** for runtime observability and debugging requirements.
- **NIST SSDF (SP 800-218)**, **OWASP SAMM**, **OpenSSF Scorecard**, **SLSA** for ecosystem/supply-chain posture.
- **Amdahl's Law** and **Little's Law** for concurrency-model selection under measured workload.
- **Language LTS schedules**: use current official vendor/community support policies for Node.js, Python, Java/OpenJDK, Go, Rust MSRV/stable cadence, .NET, and any proposed runtime; do not rely on stale embedded version claims.
- **Production incident learnings**: GC pause incidents (JVM/Go/.NET), event-loop blocking (Node.js/Python asyncio), GIL contention (CPython), cold-start incidents (JVM/AWS Lambda), thread-leak / fd-leak / coroutine-leak.

# Selection Rules

Select when language or runtime is an open decision. Pair with `technology-stack-selection` for the broader stack, with the matching `<lang>-professional-usage` capability once a language is named, and with `language-performance-safety` when the workload is latency- or memory-critical.

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for runtime selection:

- **Signal:** a new language, runtime, package manager, build lane, or deploy artifact appears in the repository graph.
  **Hidden risk:** hidden scanner gaps, missing deploy invariants, inconsistent incident tooling, and polyglot drift add support burden nobody owns.
  **Required professional action:** compare against approved runtimes, quantify operational tax, name owner, and reject novelty without workload proof.
  **Route to:** `language-runtime-selection`, `technology-stack-selection`, `package-dependency-management`, and `delivery-release-gate`.
  **Evidence required:** graph paths, existing runtime inventory, owner, deploy/build lane diff, and rejected simpler path.
- **Signal:** project memory, old ADRs, generated summaries, or benchmark notes are reused to justify a runtime decision.
  **Hidden risk:** stale memory can preserve unsupported versions or workload assumptions that no longer match current traffic, SLOs, or deployment topology.
  **Required professional action:** treat memory as a lead only, compare with current repository graph and execution evidence, and record accepted/rejected assumptions.
  **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability.
  **Evidence required:** memory source date, current support policy report, graph diff, benchmark command or report, and explicit unknowns.
- **Signal:** SLOs mention p95/p99 latency, cold start, memory ceiling, throughput, concurrency, streaming, embedded, edge, FFI, GC, event-loop, or unsafe/native behavior.
  **Hidden risk:** runtime reputation can hide scheduler, GC, event-loop, allocator, or FFI failure modes until production load.
  **Required professional action:** classify workload, map each candidate to runtime behavior, and require workload-shaped validation before approval.
  **Route to:** `language-performance-safety`, `reliability-observability-gate`, `validation-broker`, and this capability.
  **Evidence required:** SLO, measured or planned harness, runtime behavior table, profiling command, and residual risk.
- **Signal:** a candidate depends on weak ownership, scarce hiring availability, unsupported versions, supply-chain exceptions, or unfamiliar incident tooling.
  **Hidden risk:** missing patch, debug, observability, or staffing owner can leave the team unable to repair incidents.
  **Required professional action:** block or defer until ownership, lifecycle horizon, supply-chain posture, and incident tooling are proven.
  **Route to:** `security-privacy-gate`, `reliability-observability-gate`, `package-dependency-management`, and this capability.
  **Evidence required:** owner acceptance, hiring/upskilling plan, official support policy, package integrity evidence, and on-call debug procedure.
- **Signal:** generated clients, SDKs, public APIs, FFI, queues, file formats, or cross-language boundaries are part of the runtime decision.
  **Hidden risk:** compile-time types in one language can mask runtime boundary validation, serialization drift, or consumer breakage.
  **Required professional action:** require boundary validation, contract tests, selected language-specific usage rules, and migration/rollback evidence.
  **Route to:** `language-testing-strategy`, `contract-testing`, `sdk-library-contract-design`, and the matching `<lang>-professional-usage`.
  **Evidence required:** boundary inventory, schema/runtime validation location, contract test command, consumer impact, and rollback path.

# Reference Loading Policy

The `SKILL.md` body carries normal routing, trigger, evidence, and closure rules. Load [references/checklist.md](references/checklist.md) when selecting, reviewing, or rejecting a runtime. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when a workload-fit matrix, runtime behavior comparison, decision rubric, validation map, or anti-pattern review is needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) only when closure depends on current repository graph, project memory, execution trajectory, lifecycle/support-policy freshness, source-to-validation mapping, tool permission boundaries, or residual-risk wording. Use [examples/example-output.md](examples/example-output.md) only when the expected decision-record shape is unclear.

Do not load references for pure routing or when the language is already mandated and no runtime fit, lifecycle, or validation question remains. Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` only when runtime fit depends on current codebase signals, prior decisions, or executable proof. Pair with the selected `<lang>-professional-usage`, `language-testing-strategy`, `language-performance-safety`, and relevant domain extension only when code, tests, or domain runtime constraints will change.

# Risk Escalation Rules

- Escalate to `delivery-release-gate` when deployment shape changes (binary → container, JVM → native image, monolith → multi-runtime).
- Escalate to `reliability-observability-gate` when runtime GC / scheduler / event-loop behavior may breach an SLO.
- Escalate to `security-privacy-gate` for ecosystem supply-chain risk, package-manager weakness, install-script side effects, or license incompatibility.
- Escalate to `low-level-systems-extension` for unsafe / FFI / native interop / embedded constraints.
- Escalate to `language-performance-safety` once a language is chosen, for hot-path / allocation / blocking analysis.
- Escalate to `solution-optimality-evaluation` when workload measurements contradict the runtime's reputation (e.g., "Go is fast enough" without p99 evidence under target load).

# Critical Details

- **Runtime tradeoffs are operational tradeoffs.** Each runtime hides a different production failure mode: JVM hides cold start and GC pauses; Node.js hides event-loop blocking; Python hides GIL contention; Go hides goroutine leaks and STW GC at high allocation rate; Rust hides compile-time cost and async-runtime selection complexity; C++ hides UB and memory-safety bugs.
- **GC pause SLO mapping.** If product SLO is p99.9 < 50 ms, GC pause budget is typically < 10 ms. JVM G1 default may exceed; ZGC / Shenandoah / Go's concurrent GC fit better. Hard real-time / sub-ms requires no-GC (Rust / C++).
- **Cold-start budget.** Serverless / on-demand instance spin-up has language-specific floors: Go ~5-50 ms, Node.js ~50-200 ms, Python ~100-500 ms, JVM ~500-3000 ms (without native image), .NET AOT ~50-200 ms. If cold start matters, runtime is a primary decision driver, not an afterthought.
- **FFI cost.** Calling C from Python ~ free with C extension; from Go ~50-200 ns per CGO call; from Java ~10-100 ns with JNI / Project Panama. If FFI is on the hot path, the runtime choice changes.
- **Observability availability in production.** Can you take a heap dump, attach a profiler, run a flight recorder, or get an allocation trace without rebuilding? JVM yes (JFR, async-profiler), Go yes (pprof endpoint), Node.js partial, Python partial (py-spy / memray). For runtimes where you can't observe production, choose a different runtime or invest in custom telemetry up front.
- **Polyglot tax**: each additional production language adds CI lanes, deploy templates, vulnerability scanner integration, on-call playbooks, security review workflows, and on-call training. Two languages should serve the product's full lifetime unless the polyglot cost is explicitly justified.

# Failure Modes

- **Familiarity over fit** — Symptom: Python chosen for a 100k-RPS latency-critical service because the team knows Python. Cause: workload classification skipped. Impact: GIL + GC missed SLOs, rewrite under pressure.
- **Event-loop blocking** — Symptom: Node.js / Python asyncio service stalls under CPU-heavy or sync IO call. Cause: blocking work on the event loop. Detection: event-loop lag metric, p99 latency cliff. Impact: head-of-line blocking, customer-visible latency.
- **Goroutine / thread / task leak** — Symptom: memory and fd count grow over time, OOM after hours/days. Cause: missing cancellation/context propagation. Detection: pprof / heap profile / fd count metric. Impact: rolling restarts mask root cause.
- **GC pause SLO breach** — Symptom: p99.9 latency spikes correlated with GC. Cause: GC algorithm not matched to allocation rate / SLO. Detection: GC log + allocation-rate metric. Impact: SLA penalty, customer churn.
- **Cold-start exceeds budget** — Symptom: JVM serverless function timed out on cold invocation. Cause: runtime cold-start budget not considered. Impact: failed launch / unstable autoscaling.
- **Type system trusted at boundary** — Symptom: production crash from malformed JSON. Cause: TypeScript / Java types assumed instead of validating runtime input. Impact: invariant breach, data corruption.
- **Runtime nobody can debug** — Symptom: 2 AM incident, no one on-call knows how to take a heap dump / attach profiler / read GC log. Cause: ownership and tooling not validated pre-launch. Impact: MTTR multi-hour.
- **Polyglot creep** — Symptom: 5 production languages, 5 CI lanes, no one fluent in all 5. Cause: language added per service without polyglot budget. Impact: bus factor 1 per service, security patching gaps.

# Output Contract

Return a **`language_runtime_decision_record`** containing:
- **Workload classification** on dominant axis (and secondary axes)
- **Hard constraints** (latency SLO, memory budget, cold-start budget, deployment target, regulatory)
- **Candidate runtimes** (≥ 2) with workload-fit-matrix mapping
- **Runtime behavior table** per candidate: GC class & pause SLO, concurrency model, exception model, FFI cost, cold-start floor, binary/image size, observability tooling
- **Lifecycle horizon** per candidate: LTS schedule, breaking-change cadence, EOL date
- **Supply-chain posture**: OpenSSF Scorecard for standard ecosystem, package-manager integrity, license
- **Hiring market** estimate and upskilling plan if needed
- **Graph / memory / execution validation**: repository runtimes, toolchains, deploy targets, and prior decisions inspected; workload evidence and executable checks identified
- **Runtime-to-validation map**: each candidate mapped to required build, test, benchmark, security, and observability checks
- **Selected runtime** with rubric trace
- **Rejected alternatives** each with specific disqualifying constraint
- **Operational ownership** (named team, on-call coverage)
- **Exit cost** estimate (engineer-quarters to migrate away)
- **Open risks** with named owners and re-evaluation triggers
- **Evidence limits**: missing measurements, stale support assumptions, unsupported tooling, or owner gaps

# Quality Gate

1. Workload classified on at least the dominant axis; runtime fit cited against the matrix.
2. Runtime behavior table completed for every candidate (no "unknown" cells without an explicit investigation plan).
3. ≥ 2 alternatives evaluated; rejected ones cite specific disqualifying constraint.
4. Operational ownership named and accepted in writing.
5. Hiring-market check passed or upskilling plan with timeline approved.
6. Lifecycle horizon ≥ 3 years with published roadmap.
7. Supply-chain posture verified (Scorecard ≥ 5).
8. Cold-start, GC pause, and concurrency-model fit are answered against product SLOs, not stated as generic reputation.
9. Repository graph inspected for existing runtimes, toolchains, build lanes, deploy targets, generated clients, and cross-language boundaries.
10. Project memory or prior decision records checked for owner, date, workload match, and stale assumptions.
11. Runtime-to-validation map includes executable build/test/benchmark/security/observability checks for the selected runtime and major rejected alternatives.
12. Matching language-specific usage and testing capabilities selected when implementation will follow the decision.
13. EOL, migration, rollback, and exit-cost evidence recorded for any new or unsupported runtime.

# Evidence Contract

Close a runtime decision only when these answers are concrete and current:

- **Basis:** workload axis, hard constraints, approved-runtime inventory, official support policy, and why runtime choice is open or being reviewed.
- **Boundaries inspected:** repository runtime graph, package managers, build lanes, deploy artifacts, generated clients, cross-language boundaries, docs/ADRs, project memory dates, execution traces, and skipped boundaries with reasons.
- **Professional judgment:** selected runtime, rejected alternatives, existing-runtime sufficiency, operational owner, lifecycle horizon, supply-chain posture, hiring/upskilling plan, exit cost, and why novelty or familiarity is not deciding the outcome.
- **Validation evidence:** command, test, validator, benchmark, profile, security scan, observability check, report, or artifact path; working directory; exit code or explicit not-run status; freshness after final source/config/report edits.
- **What evidence proves:** workload fit, lifecycle support, build/test/toolchain viability, benchmark or profile coverage, security/supply-chain posture, or deployment compatibility for the inspected scope.
- **What evidence does not prove:** unmeasured production tail latency, uninspected downstream consumers, future hiring market, unsupported platforms, stale benchmark assumptions, or unrelated runtime behavior.
- **Residual risk and handoff:** remaining unknowns, owner, re-evaluation trigger, rollback or exit path, and next gate (`language-performance-safety`, `language-testing-strategy`, `package-dependency-management`, `security-privacy-gate`, or `reliability-observability-gate`).

Do not approve a runtime decision from preference, reputation, or old benchmark memory. If evidence is unavailable, return a deferred decision with the smallest next proof step.

# Validation Evidence Requirements

For every accepted runtime decision, map the decision to executable evidence:

- **Repository graph validation:** command or report proving current runtimes, package managers, toolchains, build lanes, deploy artifacts, generated clients, and cross-language boundaries inspected.
- **Lifecycle validation:** official support-policy source and date checked; EOL, LTS, MSRV/stable cadence, or vendor support horizon recorded.
- **Workload validation:** benchmark, profile, load test, representative harness, or explicit measurement plan tied to latency, throughput, memory, cold start, GC pause, concurrency, FFI, or boundary-validation risk.
- **Security and supply-chain validation:** package-manager integrity, OpenSSF/SLSA/Scorecard or equivalent review, dependency scan, license posture, and install-script side-effect risk when ecosystem choice matters.
- **Operational validation:** owner acceptance, on-call debug procedure, observability tooling, incident diagnostic command, and rollback/exit-cost estimate.
- **Freshness validation:** validation command or report must run after the final material source, registry, generated report, or build-profile edit; stale evidence is partial, not approval.

# Benchmark Coverage

Treat public surveys, maturity radars, and benchmark posts as weak signals. They may screen candidates, but approval requires workload-shaped evidence from the target system or a representative harness, plus lifecycle and operability checks.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `technology-stack-selection`, matching `<lang>-professional-usage`, `language-testing-strategy`, `language-performance-safety`, `package-dependency-management`, `reliability-observability-gate`, and domain extensions for low-level, AI/data, mobile, payment, or edge constraints.

# Used By

architecture-impact-reviewer, backend-change-builder, frontend-change-builder, low-level-systems-extension, ai-code-review-refactor, delivery-release-gate

# Handoff

- **Matching `<lang>-professional-usage` capability** once the language is named — for implementation rules, idioms, tooling pins.
- **`language-performance-safety`** for hot-path / allocation / blocking analysis.
- **`reliability-observability-gate`** for unresolved runtime operations risk.
- **`package-dependency-management`** for ecosystem and supply-chain governance.
- **`technology-stack-selection`** if the runtime choice forces a stack reconsideration.

# Completion Criteria

Language choice is complete when it is traceable to: a classified workload, an enumerated runtime-behavior table, named operational ownership, a viable hiring market, a published lifecycle horizon, a verified supply-chain posture, and a calculated exit cost. Decisions that rest on "the team prefers it" or "it's faster" without measurement are deferred, not approved.
