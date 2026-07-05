---
name: language-idiom-enforcement
description: "Use this capability when a selected owner skill needs focused rules for implementation or review must ensure code follows the professional idioms of the chosen language across errors, types, resources, module boundaries, naming, concurrency, formatting, and standard-library preference. Do not use it as a standalone owner for broader implementation, review, release, or documentation work."
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "85"
changeforge_version: 0.1.0
metadata:
  changeforge.skill_type: foundation-capability
  changeforge.capability_group: technology-selection
---

# Mission

Ensure code follows the professional idioms of its chosen language across error handling, type modeling, resource management, module boundaries, naming, concurrency style, formatting, and standard-library preference. Treat idiomatic style as a correctness and maintainability constraint, not a cosmetic preference, because non-idiomatic code hides subtle runtime defects that pass review and fail in production.

# Capability Boundary

`language-idiom-enforcement` returns a narrow `technology-selection` decision fragment to backend-change-builder, frontend-change-builder, ai-code-review-refactor, quality-test-gate. It returns to the owner as a fragment, never acts as a top-level workflow, and does not replace the selected professional owner, expand the task, decide unrelated architecture or release scope, or close ordinary engineering work by itself.

# Load When
Use when a language is already chosen and code is being written, reviewed, refactored, AI-generated, or migrated across language boundaries. Use whenever a code review touches error paths, resource lifecycles, concurrency primitives, public APIs, or module boundaries — these are where idiom violations cause real bugs.

# Do Not Load When
Do not use to enforce personal taste over project convention, produce syntax walkthroughs, or override intentional, documented, locally-justified deviations. Do not use when no language is chosen yet (use `language-runtime-selection` first).

# Used By / Owner Skill Compatibility
backend-change-builder, frontend-change-builder, ai-code-review-refactor, quality-test-gate

# Required Input Fragment

For `language-idiom-enforcement`, the owner skill must provide task intent, affected surface, current and desired behavior, relevant constraints, selected stage or mode, validation target, and material data/API/security/release boundaries. If that input is missing, return a missing-input fragment instead of guessing.

# Non-Negotiable Rules

- **Do not write one language in another language's style.** Java-style factories in Go, Python-style duck typing in Rust, callback pyramids in modern async TypeScript — these are correctness risks, not stylistic preferences.
- **Formatter and linter are enforced in CI, not negotiated per PR.** The repository's formatter + linter configuration is the source of truth. Local formatter disagreements are resolved by updating config, not by `// nolint` annotations.
- **AI-generated code is treated as suspect** until idiom-checked. AI tools hallucinate APIs, invent library functions, mix language styles, and produce non-idiomatic patterns at high frequency. Required: every AI-generated block is read for idiom violations and verified against actual library docs before merge.
- **External boundaries require runtime validation regardless of static typing.** TypeScript / Java / Rust types prevent internal mistakes; HTTP request bodies, queue messages, file contents, and FFI inputs still need validation at the boundary.
- **Standard-library preference is the default.** Pulling a third-party dependency to replace 10 lines of standard-library code is a supply-chain cost without offsetting benefit.
- **Local repository conventions override generic style guides** when they exist and are documented. The repository's existing patterns (consistency) outrank generic-blog "best practice" (novelty).
- **Public API surface follows language conventions strictly** (naming, error type, nullability, generic constraints, doc-comment format). Internal code has more latitude; public surface does not.

# Industry Benchmarks

- **Effective <Language>** series: *Effective Java* (Bloch), *Effective Modern C++* (Meyers), *Effective Go* (golang.org/doc/effective_go), *Effective TypeScript* (Vanderkam), *Fluent Python* (Ramalho), *Programming Rust* (Blandy/Orendorff).
- **Official style guides**: PEP 8 + PEP 484 + PEP 257 (Python), Google Java Style, Google C++ Style, Rustfmt + Clippy defaults, gofmt + Effective Go, TSC strict + typescript-eslint, Shell — Google Shell Style + ShellCheck, SQL — SQL Style Guide (Holywell) + project-pinned dialect rules.
- **Formatter/linter pins** (current stable as of Q4 2024 / Q1 2025): ruff ≥ 0.5 + mypy ≥ 1.10 (Python); gofmt + staticcheck + golangci-lint v1.60+ + govet (Go); rustfmt + clippy with `pedantic` group (Rust); typescript-eslint v8 + prettier 3 (TS); google-java-format + Spotless + ErrorProne (Java); clang-format 18 + clang-tidy 18 with cppcoreguidelines-* (C++); shfmt + ShellCheck 0.10 (Shell); sqlfluff 3+ (SQL).
- **Secure coding standards**: CERT secure coding (C/C++/Java), OWASP secure coding for the chosen language, SEI CERT Coding Standards.
- **CWE Top 25** and language-specific weakness mappings — many CWEs map directly to idiom violations (CWE-476 null deref → Optional/Result idioms; CWE-89 SQLi → parameterized-query idiom; CWE-78 OS command injection → no shell-string composition).

# Decision Rules
For `language-idiom-enforcement`, when input/evidence is missing, closure is blocking.
Escalate or return to the owner when the boundary is non-owned.

Select when implementation quality depends on language-specific idioms. Always pair with the matching `<lang>-professional-usage` capability when Python, Go, TypeScript, Java/JVM, Rust, C/C++, Shell, or SQL is named. Pair with `ai-code-review-refactor` when AI-generated code is in scope.

If language/runtime version, repository convention, changed surface, or validation target is missing, return a missing-input fragment; idiom approval is blocking until local convention and tool evidence are known. Escalate to owner or L4/L5 gate when idiom evidence would decide public API compatibility, security-sensitive boundary behavior, concurrency safety, or generated/AI code acceptance.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Public API idiom | Export, SDK, CLI flag, package boundary, generated type, or public error/result surface changes. | Language-native naming, visibility, doc comments, nullability, error/result model, and compatibility. | Local public examples, changed signature, consumer impact, formatter/linter/typecheck output. | `consumer-impact-analysis`, matching `<lang>-professional-usage` | Private local helper with no exported surface. |
| Runtime boundary idiom | HTTP, queue, file, DB row, env var, FFI, or deserialized payload enters typed code. | Do not trust static types at runtime boundaries; require native validators and negative fixtures. | Validator location, malformed fixture, denied/invalid test, what types do not prove. | `input-validation`, `contract-testing`, `security-privacy-gate` | Pure in-memory refactor with no external input. |
| Lifecycle/concurrency idiom | Resource, cancellation, transaction, lock, stream, worker, async task, or timer is acquired. | Cleanup at acquisition boundary, cancellation propagation, race/leak safety, and runtime-native concurrency. | Owner, cleanup path, race/leak/cancel command, exit code, residual interleaving risk. | `language-performance-safety`, `concurrency-control`, `quality-test-gate` | Formatting-only or naming-only change. |
| AI/migration idiom | AI-generated or migrated code mixes language styles, invented APIs, sync/async models, or test helpers. | Verify symbols against installed versions and rewrite to target-language idiom. | Symbol/import search, compiler/typecheck/lint output, behavior test, convention uncertainty. | `ai-code-review-refactor`, `code-review`, `language-testing-strategy` | Human-written code that already follows local idioms. |

# Proactive Professional Triggers

- **Signal:** public API, export, package/module boundary, SDK surface, CLI flag, or generated type is added or renamed without checking local naming, visibility, doc-comment, nullability, and error-result conventions. **Hidden risk:** consumers get a stable-looking API that is non-idiomatic, hard to evolve, or semver-breaking in that language. **Required professional action:** inspect existing public surfaces before accepting the name or signature. **Route to:** `implementation-structure-design`, `sdk-library-contract-design`, matching `<lang>-professional-usage`. **Evidence required:** local convention examples, rejected naming/signature options, consumer impact, and formatter/linter/typecheck output or not-verified disclosure.
- **Signal:** HTTP body, queue message, file, env var, CLI arg, generated client type, database row, FFI input, or deserialized payload is trusted because the chosen language has static types or type hints. **Hidden risk:** runtime boundary drift bypasses the type system and turns an idiom decision into validation, data corruption, or security failure. **Required professional action:** require language-native boundary validation and negative fixtures. **Route to:** `input-validation`, `contract-testing`, `security-privacy-gate`, matching `<lang>-professional-usage`. **Evidence required:** validator location, malformed fixture, denied/invalid test output, and what static typing does not prove.
- **Signal:** resource, cancellation, concurrency, transaction, stream, cursor, timer, lock, or worker lifecycle uses a pattern copied from another language instead of the target runtime idiom. **Hidden risk:** leaks, deadlocks, blocked event loops, unclosed handles, or lost cancellation survive formatter and happy-path tests. **Required professional action:** map ownership and cleanup at the acquisition boundary. **Route to:** `language-performance-safety`, `concurrency-control`, `quality-test-gate`. **Evidence required:** lifecycle owner, cleanup path on success/error/cancel, race/leak/cancellation command, exit code, and residual interleaving risk.
- **Signal:** a dependency, framework wrapper, helper, factory, adapter, or abstraction is introduced for behavior the standard library or local convention already covers. **Hidden risk:** supply-chain cost, API hallucination, and shared utility pollution are disguised as idiomatic code. **Required professional action:** scan local reuse candidates and compare the standard-library path before accepting the abstraction. **Route to:** `package-dependency-management`, `implementation-structure-design`, `minimal-correct-implementation`. **Evidence required:** reuse scan output, standard-library alternative, dependency/license/security report, placement rationale, and rejected over-abstraction.
- **Signal:** AI-generated or migrated code mixes sync/async styles, exception/result models, casing, package layout, test helper exports, or library calls across languages. **Hidden risk:** code passes superficial review while maintainers must mentally translate foreign idioms and hallucinated APIs. **Required professional action:** verify symbols against installed versions and rewrite to the target-language idiom before merge. **Route to:** `ai-code-review-refactor`, `code-review`, `language-testing-strategy`. **Evidence required:** symbol/import search, compiler/typecheck/lint output, public behavior test, and remaining convention uncertainty.

# Risk Escalation Rules

- Escalate to `ai-code-review-refactor` for AI-generated or heavily refactored code blocks.
- Escalate to `quality-test-gate` when idiom-sensitive behavior (error paths, resource cleanup, concurrency primitives) lacks test evidence.
- Escalate to `language-testing-strategy` when test types matched to idiom violations (race tests, sanitizer runs, property tests) are missing.
- Escalate to `solution-optimality-evaluation` when an idiom choice conflicts with measured performance or simplicity and a tradeoff decision is required.
- Escalate to `security-privacy-gate` when an idiom violation maps to a CWE / OWASP risk (SQLi, command injection, deserialization, path traversal).
- Escalate to `language-performance-safety` when an idiom debate is rooted in hot-path or allocation behavior.

# Critical Gotchas
## Naming Discipline

- Use project-local naming conventions before generic style guides.
- Public names must follow the language's public API convention strictly.
- Private/internal names may be shorter only when scope is tiny and meaning is obvious.
- Boolean names must read as predicates in the language's convention.
- Collection names must express element meaning and cardinality.
- Names must not encode temporary implementation details such as `new`, `old`, `tmp`, `final`, or `fixed`.

- **Error handling idiom is per-language**:
  - Go: explicit `if err != nil` return; wrap with `fmt.Errorf("...: %w", err)`; sentinel + `errors.Is/As`.
  - Rust: `Result<T, E>` + `?`; `thiserror` for libraries, `anyhow` for binaries; no `unwrap()` outside tests and `main`.
  - Java: checked vs runtime distinction; never swallow exceptions; chain causes; prefer specific over `Exception`.
  - Python: narrow `except` clauses; never bare `except:`; use `raise X from Y` to preserve chain; custom exception hierarchies.
  - TypeScript: discriminated-union result types or thrown `Error` subclasses; never `throw` non-Error values; `unknown` in `catch` clauses.
  - C++: exceptions vs `std::expected<T,E>` (C++23); RAII for cleanup; no raw `new`/`delete`.
- **Resource management idiom**:
  - Go: `defer` at acquisition site, paired immediately.
  - Rust: RAII via `Drop`; ownership/borrowing prevents leak.
  - Python: `with` blocks / context managers, `contextlib.ExitStack` for dynamic sets.
  - TypeScript: `try/finally`, or `using` (TS 5.2+ explicit-resource-management).
  - Java: try-with-resources for any `AutoCloseable`.
  - C++: RAII via `std::unique_ptr` / `std::shared_ptr` / custom scope guards.
- **Concurrency primitive idiom**:
  - Go: channels + goroutines + `context.Context` propagated through every API boundary.
  - Rust: `tokio` tasks with cancellation tokens; `Arc<Mutex<T>>` only when message-passing is impractical.
  - Java 21+: virtual threads via `Executors.newVirtualThreadPerTaskExecutor()`; structured concurrency where available.
  - Python: `asyncio` with structured concurrency (`asyncio.TaskGroup` in 3.11+); never mix sync blocking calls into async without `to_thread`.
  - Node.js: native promises + `AbortController`; never the callback-pyramid pattern.
- **Type-modeling idiom**: prefer making invalid states unrepresentable (newtype wrappers, discriminated unions, exhaustive matching) over runtime guards. Use sealed/closed types where the language supports them (Rust enums, Kotlin sealed classes, TS unions, Java sealed interfaces).
- **Public API discipline**: every public function/class has a doc comment in the language's standard format (rustdoc / godoc / JSDoc / Javadoc / docstring) with parameter contracts, error/exception conditions, and at least one example for non-trivial APIs.
- **Naming**: follow the language's convention strictly (camelCase / snake_case / PascalCase per language defaults); never mix conventions within one file.

## Comment Quality Discipline

Comments are part of language idiom when they define a contract, invariant, edge case, or risk. They are noise when they narrate obvious syntax. Use the detailed checklist only when the review touches exported APIs, object lifecycle, test fixtures, or complex inline reasoning.

Required comment surfaces:
- **Exported/public APIs:** use the language-standard doc format and state behavior, parameters, return value, error/exception/result contract, side effects, concurrency expectations, and examples when non-trivial.
- **Stateful classes/objects:** explain responsibility, lifecycle owner, invariant, external resource, transaction, concurrency, or domain rule; do not list fields mechanically.
- **Non-exported functions:** comment only when reused across files, business-critical, compatibility-sensitive, retrying, concurrent, persistent-state-mutating, or surprising.
- **Tests and fixtures:** test names express behavior; comments explain regression reason, edge case, production bug, or fixture/golden contract.
- **Inline comments:** reserve for business rule authority, compatibility branch, state transition, lock/concurrency reason, idempotency/retry decision, transaction boundary, performance tradeoff, external API quirk, security validation, fallback, or non-obvious algorithm step.

Reject stale, redundant, decorative, banner, line-by-line, and "Arrange / Act / Assert" comments unless the repository convention explicitly requires them. Prefer renaming or simplifying code before adding explanatory comments.

# Anti-Patterns
- **Wrong: generic style guide over local convention.** Consequence: code is "best practice" in isolation but inconsistent with the repository. Detect it when no local examples, formatter/linter config, or existing module pattern was inspected; replacement is local-convention evidence plus a documented exception when needed.
- **Wrong: static type approval at runtime boundaries.** Consequence: external payloads, generated clients, files, or queue messages bypass validation and corrupt state. Detect it when no validator and malformed fixture exist at the boundary; replacement is language-native runtime validation and negative tests.
- **Wrong: imported idiom from another language.** Consequence: maintainers must mentally translate factories, exceptions, callbacks, traits, async, or resource cleanup. Detect it when the pattern conflicts with the target runtime's standard error, lifecycle, or concurrency idiom; replacement is the matching language capability plus current tool output.

# Reference Loading Policy

- Load `references/checklist.md` when reviewing naming, file layout, comments, error handling, resource handling, imports/modules, public APIs, framework conventions, or AI-generated code for language idiom risk.
- Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on convention evidence, validation freshness, graph/memory/trajectory claims, AI-generated symbol verification, tool permission boundaries, or changed-idiom-to-validation mapping.
- Do not load the checklist for pure copy, documentation-only edits, or formatting-only changes that do not alter code semantics or public surface.
- When the matching `<lang>-professional-usage` capability is selected, load that language capability before applying generic idiom checks, then use this checklist only for cross-language idiom contamination and repository-convention evidence.

# Failure Modes

- **Cross-language idiom contamination** — Symptom: Go code with abstract factories and `interface{}` dispatch; Rust code with deep `Box<dyn Trait>` hierarchies mimicking Java. Cause: author fluent in different language. Detection: code review against language-specific style guide. Impact: maintainers fluent in the target language find code unreadable and bug-prone.
- **Type system trusted at boundary** — Symptom: production crash on malformed external input. Cause: TypeScript / Java / Rust type annotations assumed at the HTTP/queue/file boundary. Detection: missing validator (zod / jakarta-validation / serde with `#[serde(deny_unknown_fields)]`) at boundary. Impact: invariant breach, data corruption.
- **Unchecked AI hallucination** — Symptom: import of nonexistent module, call to invented function, mixed sync/async APIs. Cause: AI-generated code merged without idiom audit. Detection: type-check / import-check / library doc verification. Impact: build break or runtime crash at first use.
- **Resource leak from idiom violation** — Symptom: fd / goroutine / connection count grows monotonically. Cause: missing `defer`/`with`/try-with-resources/RAII. Detection: leak detector, fd-count metric. Impact: rolling OOM / connection exhaustion.
- **Shell quoting omission** — Symptom: script fails on filenames with spaces; worse, script executes attacker-controlled string. Cause: unquoted `$variable` expansions. Detection: ShellCheck SC2086, SC2046. Impact: data loss, command injection.
- **String-composed SQL** — Symptom: SQLi in code review. Cause: idiom violation (using string concatenation instead of parameterized query). Detection: linter / static analysis (semgrep, CodeQL). Impact: CWE-89 exposure.
- **Bare `except:` / `catch (Throwable)`** — Symptom: errors silently swallowed, debugging impossible. Cause: idiom violation. Detection: ruff E722 / sonar-rule. Impact: production silent-failure mode.
- **Sync-in-async call** — Symptom: event-loop stall in Python asyncio / Node.js. Cause: blocking call inside async context. Detection: event-loop lag metric, async-profiler. Impact: head-of-line blocking.

# Output Fragment
Return an **Idiom Review Report** containing:
- **Selected mode / professional decision / inspected boundaries / evidence collected / evidence limits / validation status / residual risk / next gate or next owner**
- **Language(s) in scope** with version pin
- **Repository conventions** in effect (formatter, linter, test framework, naming) and their config locations
- **Idiom violations found** (file:line, violated idiom, severity, suggested fix) — categorized as Correctness / Maintainability / Security / Performance
- **Required rewrites** (must-fix before merge) with patch suggestion
- **Accepted exceptions** with documented reason, scope, owner, expiration
- **Tool-check status**: formatter pass/fail, linter pass/fail, type-checker pass/fail, security-static-analysis pass/fail — with command lines
- **AI-generated blocks**: identified, audited, verdict (accept / rewrite / reject)
- **Validation freshness**: final material edit, command timestamp, stale/not-run checks, and what the tool output does not prove
- **Gate decision**: approved / blocked / conditionally approved, with required next gate
- **Residual concerns** with owner and re-evaluation trigger

# Evidence Requirement
Language idiom enforcement is complete only when the output includes:

- **Evidence status**: strong evidence names current source, local convention examples, formatter/linter/typecheck/test command output, and freshness; missing evidence or invalid evidence blocks closure.
- **Language surface**: language/runtime version detected and the idiom rule selected.
- **Repository convention**: local naming, file layout, error handling, test style, import/module pattern, and framework convention inspected.
- **Idiom decision**: what was changed to match the language/repository idiom and what was intentionally left unchanged.
- **Anti-pattern rejected**: copied style from another language, invented abstraction, framework-incorrect pattern, or repository-inconsistent naming.
- **Validation evidence**: formatter, linter, typecheck, test command, or explicit not-verified disclosure with reason.
- **What evidence proves**: the changed code follows the inspected language and repository conventions for the covered surface.
- **What evidence does not prove**: all project conventions, uninspected languages, runtime performance, or behavior outside the touched surface.
- **Residual risk**: remaining convention uncertainty, owner, and trigger for follow-up review.

Classify evidence as strong evidence, weak evidence, missing evidence, or invalid evidence. Strong evidence must be fresh after the final idiom-affecting edit and must name command or artifact, exit code or review status, inspected language surface, and what the result does not prove.

# Quality Gate

1. Repository formatter and linter pass with project config — no `// nolint` / `# noqa` / `// eslint-disable` without inline justification + owner + expiration.
2. Public API surface follows language naming, error type, and doc-comment conventions.
3. Error handling, resource management, and concurrency primitives use the language's idiomatic mechanisms (no cross-language style).
4. External boundaries (HTTP / queue / file / FFI) have runtime validation; type system is not the sole guard.
5. AI-generated blocks (if any) are explicitly audited; hallucinated APIs corrected.
6. Security-relevant idioms (parameterized queries, escaped shell args, safe deserialization, path-traversal guards) verified.
7. Local repository conventions take precedence; any deviation from project convention has explicit justification.
8. Exported/public APIs have language-standard doc comments.
9. Important non-exported complex logic has concise intent comments.
10. Tests with non-trivial scenarios document the scenario or regression being protected.
11. Inline comments explain why, contract, invariant, edge case, compatibility, or risk — not obvious syntax.
12. Redundant, stale, decorative, or line-by-line comments are rejected.

# Return To Owner Skill
- **Matching `<lang>-professional-usage` capability** for tool pins, language-specific deeper rules, and runtime-specific idioms.
- **`language-testing-strategy`** for tests matched to the language's failure modes.
- **`ai-code-review-refactor`** for residual AI-generated audit work.
- **`security-privacy-gate`** for idiom violations mapped to CWE / OWASP risks.
- **`solution-optimality-evaluation`** for idiom-vs-performance tradeoff resolution.

# Completion Criteria

Idiom review is complete when: formatter and linter pass with project config; idiomatic patterns are used for errors / resources / concurrency / boundaries / public APIs; any deviation is documented with owner, scope, and expiration; AI-generated blocks are explicitly audited; and a maintainer fluent in the language can read, test, and evolve the code without mentally translating foreign idioms.
