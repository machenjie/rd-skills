---
name: java-jvm-professional-usage
description: Use when writing or reviewing Java, Kotlin, or JVM backend systems with focus on transactions, Spring proxy behavior, bounded executors or virtual threads, ORM/JPA boundaries, GC and memory, exception taxonomy, dependency injection lifecycle, type modeling, graph/memory freshness, and validation evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "90"
changeforge_version: 0.1.0
---

# Mission

Enforce professional Java / Kotlin / JVM usage for backend services and enterprise systems: transaction-boundary correctness, Spring proxy-aware design, bounded thread pools (virtual threads where appropriate), GC and allocation discipline, exception taxonomy, dependency-injection lifecycle, type modeling, and observability. Reject Spring ceremony that does not protect a real domain, transaction, or runtime risk.

# Pinned Tooling Baseline (Java / JVM)

Pinned JVM versions are review baselines, not permanent mandates. If a JDK, Spring, Kotlin, build, or analysis pin is EOL, unsupported, superseded, or conflicts with the target platform policy, record the project rule and refresh this capability before using the pin for new product work.

- **JDK**: Project-approved vendor LTS baseline, normally JDK 25 or JDK 21. JDK 25 reached GA on 2025-09-16; JDK 21 remains acceptable where the platform policy has not moved. JDK 17 is legacy-maintenance only. **Java 8 and 11 require explicit vendor support plus migration plan for new work.**
- **Build**: Maven ≥ 3.9 with `maven-enforcer-plugin` (`requireMavenVersion`, `dependencyConvergence`), or Gradle ≥ 8.7 with version catalogs (`libs.versions.toml`) and dependency lockfile (`--write-locks` → `gradle.lockfile`).
- **Spring (when used)**: Spring Boot 4.1+ for new Boot 4 trains when compatible; Spring Boot 3.5+ acceptable for maintained 3.x apps. Boot 2.x / Spring Framework 5.x are EOL for OSS — require commercial support and migration plan to remain.
- **Kotlin (when used)**: ≥ 2.0; `kotlinx.coroutines` ≥ 1.8 for async; explicit-API mode for libraries.
- **Formatter / linter**: `spotless` with `palantir-java-format` or `google-java-format`; `error-prone` + `nullaway` (or JSpecify annotations + Checker Framework where strictness warranted); for Kotlin: `ktlint` + `detekt`.
- **Static analysis**: `spotbugs` + `find-sec-bugs` plugin; PMD for legacy.
- **Test framework**: JUnit Jupiter ≥ 5.10; AssertJ for assertions; Mockito ≥ 5; **Testcontainers** for integration tests against real engines (Postgres, Kafka, etc.); `ArchUnit` for architecture-rule enforcement.
- **Concurrency testing**: `jcstress` for low-level concurrency primitives.
- **Vulnerability scanning**: `mvn org.owasp:dependency-check-maven` or `gradle dependencyCheck`, or `osv-scanner` / Snyk in CI.
- **Observability**: `Micrometer` + OpenTelemetry; `slf4j` + Logback (or Log4j2) with JSON layout for services; **JFR (JDK Flight Recorder)** + `async-profiler` for production profiling.
- **GC**: G1 (default, throughput-balanced), **ZGC** (Java 21 generational, sub-ms pauses, large heaps), Shenandoah (low-pause alternative). Choose per latency SLO; document choice and tuning.

# When To Use

Use when Java / Kotlin / JVM code is added, reviewed, refactored, AI-generated, or selected for backend services, enterprise workflows, batch jobs, integration systems, or libraries. Trigger this capability when a `@Transactional`, `@Async`, executor, scheduler, virtual thread, Reactor/R2DBC boundary, exception class, ORM entity, Jackson mapper, dependency BOM, or DI scope is introduced or changed. Treat repository graph and project-memory claims as stale until current source, build files, tests, and generated artifacts confirm them.

# Do Not Use When

Do not spend context on Java syntax tutoring. Do not add Spring annotations, DDD ceremony, or hexagonal-architecture layering unless it protects a named transaction, domain, lifecycle, or runtime risk.

# Stage Fit

Use this capability during JVM implementation planning, coding, bug-fix, code-review, refactoring, testing, and runtime-evidence review. Per-stage focus:

- **coding**: null safety, immutability, exception model, executor/thread lifecycle, equals/hashCode contract.
- **debugging-diagnosis**: thread/connection-pool exhaustion, deadlock, GC pause / memory leak, swallowed exception.
- **code-review**: over-abstraction and DI/DDD ceremony, mutable shared state, resource leak without try-with-resources.
- **refactoring**: package/module boundary, public API and serialization compatibility, transaction boundary.
- **testing**: JUnit with concurrency, contract tests, injected clock for deterministic time.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Transaction and proxy review | `@Transactional`, `@Async`, self call, private/final method, propagation/isolation change. | Prove the call crosses the right Spring proxy and rollback semantics match the domain operation. | Bean call path, rollback test, propagation/isolation statement, skipped proxy paths. | `transaction-consistency`, `quality-test-gate` | Generic Spring layering advice. |
| Executor and virtual-thread review | Executor, scheduler, `CompletableFuture`, parallel stream, virtual thread, Reactor bridge. | Bound concurrency, queueing, shutdown, rejection, interruption, and pinning risk. | Executor inventory, queue/rejection policy, JFR pinning or not-run reason. | `concurrency-control`, `language-performance-safety` | Sequential-only validation. |
| ORM and model-boundary review | JPA entity, lazy collection, DTO mapper, Jackson config, repository query. | Keep persistence models out of API shape and detect N+1 / lazy leakage before release. | Entity/DTO boundary, fetch plan, query count or Testcontainers result. | `model-boundary-mapping`, `data-middleware-change-builder` | Controller happy-path proof only. |
| Runtime observability review | GC/SLO claim, container heap, allocation hot path, Micrometer/OTel/logging change. | Match JVM ergonomics to service SLO and make failures diagnosable. | Heap flags, GC/JFR evidence, metric/log field list, residual runtime risk. | `reliability-observability-gate`, `observability` | Local unit tests as performance proof. |
| Dependency and validation review | BOM upgrade, Log4j/Jackson/Hibernate/Spring upgrade, build plugin, generated client. | Preserve dependency provenance, security posture, generated boundary, and validation freshness. | Dependency scan, lock/BOM diff, changed-path validator map, tool permission record. | `package-dependency-management`, `validation-broker` | Trusting transitive upgrades. |

# Non-Negotiable Rules

- **Spring `@Transactional` boundaries respect proxy semantics.** Self-invocation (`this.txMethod()`) bypasses the proxy and the transaction. Either inject self via `ApplicationContext` / `@Lazy` self-injection, or restructure to call the proxied bean. **AspectJ weaving** is the alternative if self-invocation is unavoidable.
- **Thread pools are explicit, bounded, and named.** `Executors.newFixedThreadPool(n, namedFactory)` or `ThreadPoolExecutor` with explicit core / max / queue. Never `Executors.newCachedThreadPool()` (unbounded thread creation) or `newSingleThreadExecutor` with unbounded queue.
- **Virtual threads (Java 21 JEP 444) for IO-bound concurrency**: `Executors.newVirtualThreadPerTaskExecutor()`. Do **not** use virtual threads for CPU-bound work; do **not** pool virtual threads; avoid pinning to platform threads (no `synchronized` around blocking calls — use `ReentrantLock`).
- **Blocking IO does not consume unbounded request threads.** Reactive (Project Reactor / Mutiny / coroutines) or virtual threads at the IO boundary.
- **Exception taxonomy is explicit**: distinguish (a) business / domain exceptions (recoverable, mapped to 4xx), (b) infrastructure exceptions (transient, retryable), (c) programming errors (unchecked, fail fast). Never catch and swallow.
- **GC behavior matched to SLO.** If p99.9 latency budget is tight (< 50ms), use ZGC; if throughput is the goal, G1 is fine; document the choice with reasoning.
- **No anemic services that pass through to repository** — if a service method is `return repo.findById(id)`, the layer is rejected. Equally: no over-engineered DDD ceremony for CRUD modules. Match modeling depth to domain complexity.
- **ORM entities never returned from controllers.** DTO / response model is separate; lazy-loading boundaries respected; N+1 queries detected (Hibernate `org.hibernate.SQL` log + `@DynamicUpdate` + `JOIN FETCH` discipline).
- **DI lifecycle explicit.** Prototype-scope beans into singleton-scope beans is the classic leak; use `ObjectProvider<T>` or `Provider<T>` for runtime resolution.
- **Logging via slf4j with structured fields**; secrets never logged; MDC for correlation IDs.

# Industry Benchmarks

- **Effective Java** (Bloch, 3rd ed.) — the floor for Java idioms.
- **Java Concurrency in Practice** (Goetz) — still authoritative for JMM and bounded executors.
- **JEP-defined modern Java**: JEP 444 (virtual threads), JEP 453 (structured concurrency, preview → incubator), JEP 466 (scoped values), JEP 439 (generational ZGC).
- **Spring transaction documentation** — proxy mechanisms (CGLIB vs JDK), propagation, isolation, rollback rules.
- **JVM ergonomics / GC tuning**: Oracle GC tuning guide, Microsoft OpenJDK GC docs (for Azul / Microsoft Build of OpenJDK), Aleksey Shipilëv's GC notes.
- **OWASP Top 10 (web) / OWASP Java Security cheat sheets**; **CWE Top 25** mapping to JVM (deserialization — CVE-2021-44228 Log4Shell; SSRF; XXE).
- **SLF4J / Logback / Log4j2 structured logging**; **Micrometer + OpenTelemetry** for metrics/traces.
- **ArchUnit** for layered-architecture enforcement; **JFR / async-profiler / JMC** for profiling.

# Selection Rules

Select when Java / Kotlin / JVM / Spring / transactions / executors / GC / ORM / enterprise service boundaries appear. Pair with `transaction-consistency`, `concurrency-control`, `language-performance-safety`, `language-testing-strategy`, `package-dependency-management`, `validation-broker`, and `reliability-observability-gate` when commands or reports must be mapped to changed paths. Skip only for formatter-only, comment-only, or generated-output refreshes with no JVM behavior, public API, dependency, runtime, graph, memory, or validation impact.

# Proactive Professional Triggers
- **Signal:** `@Transactional`, `@Async`, cache, scheduled, or event listener logic is invoked through `this`, a private/final method, or a direct constructor-created instance. **Hidden risk:** proxy advice is skipped, so rollback, async dispatch, caching, security, or event behavior silently differs from annotations. **Required professional action:** trace the bean caller/callee path and require integration proof at the annotated boundary. **Route to:** `transaction-consistency`, `quality-test-gate`. **Evidence required:** current-source bean path, proxy crossing decision, rollback/async/caching test output, and skipped memory claims.
- **Signal:** an executor, scheduler, parallel stream, `CompletableFuture`, virtual-thread executor, or Reactor bridge appears without queue, rejection, timeout, shutdown, or pinning evidence. **Hidden risk:** unbounded work, carrier-thread pinning, lost exceptions, or stuck shutdown appears only under load. **Required professional action:** inventory concurrency ownership and prove bounds or disclose runtime risk. **Route to:** `concurrency-control`, `language-performance-safety`. **Evidence required:** executor table, queue/rejection/shutdown policy, JFR `JdkVirtualThreadPinned` or not-run reason, and residual owner.
- **Signal:** JPA entities, lazy collections, generated mappers, Jackson polymorphic settings, or repository queries cross controller/API/event boundaries. **Hidden risk:** N+1 queries, lazy-load exceptions, RCE-prone deserialization, or persistence shape leaks into public contracts. **Required professional action:** separate DTO/model ownership and test query/fetch behavior at the real persistence boundary. **Route to:** `model-boundary-mapping`, `data-middleware-change-builder`, `security-privacy-gate`. **Evidence required:** entity/DTO boundary, query-count or Testcontainers output, Jackson allowlist decision, and consumer compatibility note.
- **Signal:** GC, heap, native memory, allocation, p99 latency, container memory, or "virtual threads improve throughput" is claimed without runtime evidence. **Hidden risk:** local tests pass while production hits pause cliffs, OOM kills, carrier starvation, or allocation-rate saturation. **Required professional action:** route runtime evidence before accepting the performance claim. **Route to:** `language-performance-safety`, `reliability-observability-gate`, `observability`. **Evidence required:** JFR/GC log or benchmark command, heap flags, Micrometer/OTel metric names, and what remains unproven.
- **Signal:** Spring Boot, Jackson, Hibernate, Netty, Log4j/Logback, Kotlin, Maven/Gradle plugin, BOM, or generated client changes without lock, CVE, and compatibility review. **Hidden risk:** transitive CVE, binary/source incompatibility, annotation processor drift, or generated contract breakage. **Required professional action:** review dependency graph and validation freshness before handoff. **Route to:** `package-dependency-management`, `security-privacy-gate`, `validation-broker`. **Evidence required:** BOM/lock diff, dependency-check or OSV result, generated artifact check, and accepted-risk owner.
- **Signal:** repository graph, project memory, prior incident notes, or another agent says a JVM path is safe, unused, already tested, or low risk without current source confirmation. **Hidden risk:** stale context misses reflection, generated code, Spring auto-configuration, test slice exclusions, or changed CI commands. **Required professional action:** confirm graph/memory claims against current files and validation records before closure. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `agent-execution-discipline`. **Evidence required:** inspected paths, accepted/rejected memory, fresh command or not-run disclosure, and unknown boundary list.

# Risk Escalation Rules

- Escalate to `transaction-consistency` for transaction-correctness questions (propagation, isolation, rollback rules, two-phase commit).
- Escalate to `reliability-observability-gate` for GC pause budget, thread-pool sizing, async runtime SLO risk.
- Escalate to `language-performance-safety` for hot-path allocation, GC pressure, JFR profile review.
- Escalate to `concurrency-control` for lock scope, memory ordering, JMM-sensitive primitives.
- Escalate to `security-privacy-gate` for deserialization (Java Serialization, Jackson polymorphic types), Log4Shell-class library risk, XXE, SSRF.
- Escalate to `package-dependency-management` for major dependency upgrades, BOM management.

# Critical Details

- **Spring proxy self-invocation pitfall** (the most common Spring transaction bug). Example: `class S { @Transactional void a() { ... } void b() { a(); } }` — calling `s.b()` runs `a()` **without** the transaction because `b()` calls `this.a()`, bypassing the proxy. Fixes: (1) inject self-bean via `@Lazy private S self;` then `self.a()`; (2) split into two beans; (3) AspectJ load-time weaving.
- **Virtual thread pinning**: a virtual thread inside a `synchronized` block holding a blocking call (DB / network) **pins** to its carrier thread, defeating the scheduler. Use `java.util.concurrent.locks.ReentrantLock` instead of `synchronized` around blocking work.
- **`Executors.newCachedThreadPool()`** creates unbounded threads — OOM under load spike. **`Executors.newFixedThreadPool(n)`** uses an unbounded `LinkedBlockingQueue` — OOM via backlog. Use `ThreadPoolExecutor` with bounded queue + `RejectedExecutionHandler` (caller-runs / abort with logging).
- **JPA / Hibernate N+1**: a parent entity with lazy collection accessed in a loop generates N queries. Detect with Hibernate SQL log + `@org.hibernate.annotations.FetchProfile` or `JOIN FETCH` in JPQL or entity-graph hint.
- **`@Async` on the same bean** without proxy = no async (same self-invocation issue).
- **`OffsetDateTime` / `Instant`** for timestamps; never `java.util.Date` (mutable, not timezone-clear) for new code; never `LocalDateTime` for an instant (no timezone).
- **Jackson polymorphic deserialization** (`@JsonTypeInfo` + default typing) is an RCE class — disable global default typing; allow-list known types.
- **Log4Shell pattern**: any user-controlled string reaching `log.info("... {}", userInput)` was vulnerable in Log4j 2.x < 2.17. Lesson: parameterized logging is required and JNDI lookup must be disabled in any logger.
- **`Optional` is a return type, not a field type, not a parameter type.** Per Brian Goetz's guidance.
- **`record` (Java 16+)** for immutable data carriers (DTOs, value objects). Pattern matching for switch (Java 21+) for exhaustive type dispatch.
- **GC tuning**: `-XX:+UseZGC -XX:+ZGenerational` (Java 21) for low pause; `-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError` in containers; **never** rely on default heap sizing in containers — size explicitly.
- **DI singleton-prototype leak**: a `@Scope("prototype")` bean autowired into a singleton receives one instance and reuses it. Use `ObjectProvider<T>` or `Provider<T>` for per-call instantiation.

# Failure Modes

- **Self-invocation no-tx** — Symptom: changes that should rollback get committed. Cause: `this.txMethod()` bypasses proxy. Detection: Spring transactional integration test with simulated exception. Impact: data corruption.
- **`newCachedThreadPool` OOM** — Symptom: thread count explodes under load. Cause: unbounded executor. Detection: bounded executor mandate; thread-count metric. Impact: outage.
- **Virtual thread pinning** — Symptom: virtual-thread throughput collapses under load. Cause: `synchronized` around blocking IO. Detection: JFR JdkVirtualThreadPinned event. Impact: latency cliff.
- **N+1 query** — Symptom: page load fires 100s of DB queries. Cause: lazy collection accessed in loop. Detection: Hibernate SQL log; `JpaSystemTest`; APM trace. Impact: latency, DB load.
- **Polymorphic deserialization RCE** — Symptom: arbitrary code execution via Jackson default typing. Cause: `enableDefaultTyping()`. Detection: code review + dependency-check. Impact: RCE.
- **GC pause SLO breach** — Symptom: p99.9 latency spike correlated with GC log. Cause: G1 under high allocation rate or insufficient heap. Detection: GC log + allocation-rate metric. Impact: SLA breach.
- **`@Async` on same bean** — Symptom: method runs synchronously despite annotation. Cause: self-invocation. Detection: same as `@Transactional` testing. Impact: thread-blocking, missed deadlines.
- **Logging unparameterized** — Symptom: Log4Shell-class CVE exposure or PII in logs. Cause: `log.info("..." + userInput)`. Detection: lint + parameterized-logging rule. Impact: RCE / privacy incident.
- **Container heap default** — Symptom: pod OOM-killed at fraction of memory limit. Cause: JVM defaults to 25% of host memory; container limit ignored without `-XX:+UseContainerSupport` + `-XX:MaxRAMPercentage`. Detection: heap-vs-limit metric. Impact: restart loop.
- **Anemic / over-engineered service** — Symptom: 5 layers, each delegating; or 30-line service with 6 patterns. Cause: ceremony unmoored from domain complexity. Detection: code review against domain complexity. Impact: maintenance cost without benefit.

# Reference Loading Policy

Load [references/checklist.md](references/checklist.md) when Java/JVM changes touch nullability, exceptions, executors/thread pools, transactions/resources, equality/hashCode, blocking calls, heap/GC pressure, framework lifecycle, ORM boundaries, dependency graph, or validation freshness. Use [examples/example-output.md](examples/example-output.md) only when the review shape is unclear. Do not load references for a trivial formatter-only or local test-name change.

# Output Contract

Return a **JVM Usage Review** containing:
- **Mode selected**: transaction/proxy, executor/virtual-thread, ORM/model-boundary, runtime observability, or dependency/validation, with trigger signal
- **Boundaries inspected**: Java/Kotlin packages, Spring beans, generated code, build files, tests, configs, ORM mappings, public APIs, and skipped boundaries with reason
- **JDK version**, vendor, support status; **Kotlin version** if applicable
- **Tooling pins**: build tool + version, lock plugin, formatter, static analysis, test framework
- **Spring Boot version** (if applicable) and lifecycle status
- **Transaction-boundary analysis**: self-invocation risks, propagation, isolation, rollback rules
- **Thread-pool inventory**: each executor with bound, queue type, rejection policy, name
- **Virtual-thread usage**: pinning risks; locks vs `synchronized` audit
- **Exception taxonomy**: business / infra / programming distinctions; HTTP mapping
- **JPA / ORM**: lazy boundaries, N+1 risks, DTO separation, entity-vs-DTO discipline
- **GC choice + tuning**: algorithm, heap config, container ergonomics, expected pause distribution vs SLO
- **DI lifecycle**: scope correctness; prototype-into-singleton audit
- **Observability**: structured logging via slf4j; Micrometer + OTel; JFR / async-profiler available in prod
- **Security**: deserialization audit (Jackson, native serialization); dependency-check / OSV results
- **Tests**: JUnit 5 + AssertJ; Testcontainers for integration; ArchUnit for architecture rules; jcstress for low-level concurrency
- **Graph/memory/execution coupling**: repository graph and project-memory claims accepted, rejected, stale, or not verified; validation freshness after final JVM edit
- **JVM validation evidence**: literal command, exit code, validator/report/artifact path, and the transaction, runtime, dependency, or boundary claim the output proves or leaves unproven
- **Tool permission boundary**: Maven/Gradle/test/build/profile/dependency-scan/generated-artifact command class, sandbox/approval state, write scope, and secret-output redaction rule
- **Accepted JVM deviations** with owner, scope, expiration, and cleanup trigger

# Evidence Contract

A Java/JVM change is professionally complete only when the output includes:

- **Nullability and immutability**: nullable inputs/outputs, defensive copies, immutable value objects.
- **Exception model**: checked/unchecked decision, typed domain exceptions, no swallowed exceptions.
- **Thread/executor lifecycle**: executor ownership, shutdown, timeout, queue bounds, and interruption behavior.
- **Equality/hashCode/ordering**: value object equality and collection behavior if changed.
- **Transaction/resource cleanup**: try-with-resources, connection/session lifecycle, transaction boundaries.
- **JVM runtime risk**: heap, GC pressure, blocking calls, thread pool saturation when relevant.
- **Validation evidence**: JUnit, Spring integration rollback test, Testcontainers, ArchUnit, Error Prone / SpotBugs, dependency scan, JFR / GC log, validator, or not-verified disclosure with command, exit code, output summary, and report/artifact path.
- **What evidence proves in JVM review**: the inspected transaction, lifecycle, dependency, runtime, or test-boundary risk is covered for the named path.
- **What evidence does not prove in JVM review**: production heap shape, every thread interleaving, every Spring auto-configuration path, third-party service behavior, or platform-specific tuning unless separately measured.
- **Graph and memory freshness**: current source, generated artifacts, build files, configs, and prior project-memory claims confirmed or rejected before closure.
- **Residual JVM risk**: untested proxy/runtime/platform/dependency path, owner, and next gate.

# Quality Gate

1. JDK follows the project-approved supported vendor LTS baseline, normally 25 or 21; 17 only with legacy-maintenance exception; vendor + version recorded.
2. Build is reproducible with locked dependencies; dependency-check / OSV green or triaged.
3. Every `@Transactional` boundary verified against self-invocation; tests prove rollback on exception.
4. Every executor is bounded (core, max, queue, rejection); no `newCachedThreadPool` / unbounded queue.
5. Virtual-thread code paths audited for pinning (`synchronized` around blocking work flagged).
6. Exception taxonomy distinguishes business / infrastructure / programming; HTTP mapping documented.
7. JPA boundaries: no entity in controller; N+1 absent (verified via Hibernate SQL log or APM trace).
8. GC algorithm chosen and tuned for latency SLO; container heap sized explicitly.
9. Logging structured + parameterized; no string-concat user input into log message; no PII / secrets in logs.
10. spotless + error-prone + spotbugs green; ArchUnit rules pass.
11. Validation report maps each changed JVM path to command, exit code, covered risk, stale/not-run targets, and residual owner.
12. Tool permission/sandbox record exists for Maven, Gradle, Testcontainers, dependency scan, profiling, generated-client, or artifact-writing commands.

# Used By

backend-change-builder, data-middleware-change-builder, reliability-observability-gate, quality-test-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`transaction-consistency`** for transaction-correctness, propagation, isolation, two-phase.
- **`language-performance-safety`** for hot-path allocation, GC, JFR profile.
- **`concurrency-control`** for JMM, lock scope, jcstress design.
- **`package-dependency-management`** for dependency upgrades, BOM, vulnerability response.
- **`reliability-observability-gate`** for production SLO risk.
- **`security-privacy-gate`** for deserialization, logging, Log4Shell-class risk.

# Completion Criteria

Review is complete when: the JDK baseline is supported by the project vendor policy; transactions / executors / virtual threads / exception taxonomy / JPA / GC / DI are each answered explicitly; security and dependency baselines are green or triaged; graph and project-memory claims are current-source confirmed; observability is in place; validation commands and exit codes are recorded; tests prove transactional and concurrent behavior where relevant; and any accepted JVM deviation has owner, scope, expiration, and cleanup trigger.
