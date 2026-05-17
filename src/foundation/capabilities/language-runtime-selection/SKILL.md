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

Use when language is not yet chosen, a new language is proposed in an existing system, runtime behavior materially affects correctness or latency, or a workload must be classified against CPU-bound, IO-bound, latency-sensitive, memory-sensitive, batch, interactive, embedded, edge, or contract-heavy constraints. Use whenever the choice will commit ≥ 1 team to operate the runtime for ≥ 1 year.

# Do Not Use When

Do not use for language lessons, syntax preference debates, religious wars, or migration enthusiasm absent workload evidence and operational ownership. Do not use for like-for-like minor version upgrades (use `package-dependency-management`).

# Non-Negotiable Rules

- **Operational ownership precedes the decision.** A language without a named on-call owner is rejected regardless of technical merit.
- **Workload classification is mandatory.** State the workload as: CPU-bound / IO-bound / latency-sensitive / memory-sensitive / batch / interactive / streaming / embedded / edge / contract-heavy. The runtime must match the dominant axis.
- **Runtime behavior must be enumerated before commitment**: GC class (none / generational / concurrent / region-based), pause SLO impact, concurrency model (threads / coroutines / event-loop / actor / CSP), exception model, FFI cost, startup time (cold-start budget), binary/image size, package manager integrity model, observability tooling (profiler, tracer, heap-dump, allocator-stats), debugger availability in production.
- **Existing-runtime preference is the default.** Adding a new language costs ≥ 1 engineer-FTE-year of operational overhead (CI lanes, deploy pipeline, vulnerability scanner integration, on-call training, knowledge spread). Justify the addition against that cost.
- **Hiring-market check is mandatory.** ≥ 100 addressable candidates locally, or in-house upskilling plan with named timeline. Esoteric / academic / single-vendor languages require explicit acceptance.
- **Boundary validation is not replaced by compile-time types.** Type systems prevent internal mistakes; external inputs (HTTP, queue, file, FFI) still require runtime validation regardless of language.
- **Runtime lifecycle horizon ≥ 3 years.** Vendor or community support roadmap, LTS schedule, breaking-change cadence must be published and credible. Pre-1.0 runtimes for production-critical work require explicit risk acceptance and exit plan.

# Industry Benchmarks

- **ThoughtWorks Tech Radar** for language maturity (Adopt / Trial / Assess / Hold).
- **TIOBE / StackOverflow Developer Survey / RedMonk** for hiring-market signal.
- **Google SRE Workbook — Production Readiness** for runtime observability and debugging requirements.
- **NIST SSDF (SP 800-218)**, **OWASP SAMM**, **OpenSSF Scorecard**, **SLSA** for ecosystem/supply-chain posture.
- **Amdahl's Law** and **Little's Law** for concurrency-model selection under measured workload.
- **Language LTS schedules**: Node.js (even-numbered LTS, 30-month support), Python (5-year support per PEP 602), Java (Oracle/OpenJDK LTS cadence: 21 current LTS through 2031), Go (last 2 minor versions supported), Rust (6-week stable cadence, no LTS — pin to specific stable + MSRV policy), .NET (even-numbered LTS, 3-year support).
- **Production incident learnings**: GC pause incidents (JVM/Go/.NET), event-loop blocking (Node.js/Python asyncio), GIL contention (CPython), cold-start incidents (JVM/AWS Lambda), thread-leak / fd-leak / coroutine-leak.

# Selection Rules

Select when language or runtime is an open decision. Pair with `technology-stack-selection` for the broader stack, with the matching `<lang>-professional-usage` capability once a language is named, and with `language-performance-safety` when the workload is latency- or memory-critical.

### Workload → Runtime Fit Matrix (starting point, not destiny)

```
Workload axis              | Strong fits                              | Risk fits
---------------------------|------------------------------------------|---------------------------
CPU-bound (numeric, ML)    | C++20/23, Rust 2021, Go 1.22, Java 21    | Python (needs C extensions, GIL)
IO-bound (high-fanout RPC) | Go 1.22, Rust+tokio, Java 21 (virtual    | Node.js (single-thread CPU
                           | threads), Node.js 20 LTS                 | risk for mixed workloads)
Latency-sensitive (p99 ms) | Rust, C++, Go (with GC tuning), Java     | Node.js (event-loop block),
  hard <10ms                | with ZGC, no-GC runtimes                 | Python (GIL+GC)
Memory-sensitive / embedded| Rust, C++, Zig                           | GC runtimes (heap floor)
Batch / data pipeline      | Python 3.12+, Scala/Java 21, Go, Rust    | Node.js (lib gap for ETL)
Interactive (web frontend) | TypeScript 5.4+ strict                   | Plain JS (loss of safety)
Contract-heavy (SDK/IDL)   | TypeScript, Rust, Go, Java               | Dynamic languages (drift risk)
Scripts / glue / CI        | Bash ≥4 + ShellCheck, Python 3.11+       | Compiled languages (overhead)
Systems / kernel / driver  | C, C++23, Rust 2021                      | GC languages (latency/footprint)
Edge / cold-start critical | Go, Rust, JS (V8 isolate)                | JVM, .NET (cold start)
```

### Decision Rubric

```
1. Workload classified on dominant axis (above matrix).
2. Existing approved runtime sufficient? (preferred unless workload fit is poor or hard
   constraint forces change).
3. Runtime behavior enumerated (GC, concurrency, exceptions, FFI, startup, binary size,
   observability) — answer each before approval.
4. Operational ownership named and accepted.
5. Hiring market ≥ 100 candidates or in-house upskilling plan with timeline.
6. Lifecycle horizon ≥ 3 years with published roadmap / LTS.
7. Supply-chain posture verified (OpenSSF Scorecard ≥ 5 for the runtime + standard ecosystem).
8. Exit cost (rewrite to alternative) estimated.
```

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

Return a **Language/Runtime Decision Record** containing:
- **Workload classification** on dominant axis (and secondary axes)
- **Hard constraints** (latency SLO, memory budget, cold-start budget, deployment target, regulatory)
- **Candidate runtimes** (≥ 2) with workload-fit-matrix mapping
- **Runtime behavior table** per candidate: GC class & pause SLO, concurrency model, exception model, FFI cost, cold-start floor, binary/image size, observability tooling
- **Lifecycle horizon** per candidate: LTS schedule, breaking-change cadence, EOL date
- **Supply-chain posture**: OpenSSF Scorecard for standard ecosystem, package-manager integrity, license
- **Hiring market** estimate and upskilling plan if needed
- **Selected runtime** with rubric trace
- **Rejected alternatives** each with specific disqualifying constraint
- **Operational ownership** (named team, on-call coverage)
- **Exit cost** estimate (engineer-quarters to migrate away)
- **Open risks** with named owners and re-evaluation triggers

# Quality Gate

1. Workload classified on at least the dominant axis; runtime fit cited against the matrix.
2. Runtime behavior table completed for every candidate (no "unknown" cells without an explicit investigation plan).
3. ≥ 2 alternatives evaluated; rejected ones cite specific disqualifying constraint.
4. Operational ownership named and accepted in writing.
5. Hiring-market check passed or upskilling plan with timeline approved.
6. Lifecycle horizon ≥ 3 years with published roadmap.
7. Supply-chain posture verified (Scorecard ≥ 5).
8. Cold-start, GC pause, and concurrency-model fit are answered against product SLOs, not stated as generic reputation.

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
