---
name: language-idiom-enforcement
description: Use when implementation or review must ensure code follows the professional idioms of the chosen language across errors, types, resources, module boundaries, naming, concurrency, formatting, and standard-library preference.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "85"
changeforge_version: 0.1.0
---

# Mission

Ensure code follows the professional idioms of its chosen language across error handling, type modeling, resource management, module boundaries, naming, concurrency style, formatting, and standard-library preference. Treat idiomatic style as a correctness and maintainability constraint, not a cosmetic preference, because non-idiomatic code hides subtle runtime defects that pass review and fail in production.

# When To Use

Use when a language is already chosen and code is being written, reviewed, refactored, AI-generated, or migrated across language boundaries. Use whenever a code review touches error paths, resource lifecycles, concurrency primitives, public APIs, or module boundaries — these are where idiom violations cause real bugs.

# Do Not Use When

Do not use to enforce personal taste over project convention, produce syntax walkthroughs, or override intentional, documented, locally-justified deviations. Do not use when no language is chosen yet (use `language-runtime-selection` first).

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

# Selection Rules

Select when implementation quality depends on language-specific idioms. Always pair with the matching `<lang>-professional-usage` capability when Python, Go, TypeScript, Java/JVM, Rust, C/C++, Shell, or SQL is named. Pair with `ai-code-review-refactor` when AI-generated code is in scope.

# Risk Escalation Rules

- Escalate to `ai-code-review-refactor` for AI-generated or heavily refactored code blocks.
- Escalate to `quality-test-gate` when idiom-sensitive behavior (error paths, resource cleanup, concurrency primitives) lacks test evidence.
- Escalate to `language-testing-strategy` when test types matched to idiom violations (race tests, sanitizer runs, property tests) are missing.
- Escalate to `solution-optimality-evaluation` when an idiom choice conflicts with measured performance or simplicity and a tradeoff decision is required.
- Escalate to `security-privacy-gate` when an idiom violation maps to a CWE / OWASP risk (SQLi, command injection, deserialization, path traversal).
- Escalate to `language-performance-safety` when an idiom debate is rooted in hot-path or allocation behavior.

# Reference Loading Policy

- Load `references/checklist.md` when reviewing naming, file layout, comments, error handling, resource handling, imports/modules, public APIs, framework conventions, or AI-generated code for language idiom risk.
- Do not load the checklist for pure copy, documentation-only edits, or formatting-only changes that do not alter code semantics or public surface.
- When the matching `<lang>-professional-usage` capability is selected, load that language capability before applying generic idiom checks, then use this checklist only for cross-language idiom contamination and repository-convention evidence.

# Critical Details

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

Comments are part of professional language idiom. They must explain contract, intent, invariants, edge cases, and non-obvious reasoning. They must not restate obvious code.

Required comments:

1. Public / exported API comments
   - Every exported class, struct, interface, function, method, constant, variable, component, hook, module API, SDK API, and public type must have a language-standard doc comment.
   - The comment must follow the language convention:
     - Go: godoc starts with the exported identifier.
     - Rust: rustdoc `///`.
     - TypeScript: JSDoc for exported APIs.
     - Java/Kotlin: Javadoc/KDoc for public APIs.
     - Python: docstring for public modules/classes/functions.
     - C++: project-standard Doxygen or local convention.
   - The comment must describe behavior, contract, important parameters, return value, error/exception behavior, side effects, concurrency expectations, and non-trivial examples when appropriate.

2. Class / object comments
   - Required when the class/object owns state, lifecycle, invariants, external resources, concurrency, transactions, or domain rules.
   - The comment should explain responsibility and invariant, not list fields mechanically.

3. Function / method comments
   - Required for exported functions and methods.
   - Required for non-exported functions when behavior is non-trivial, reused across files, encodes a business rule, handles compatibility, performs retries, has concurrency behavior, mutates persistent state, or has surprising edge cases.
   - Not required for tiny private helpers when the name and local context are sufficient.

4. Test comments
   - Test names must express behavior.
   - Complex tests must explain the scenario, regression reason, edge case, or production bug being protected.
   - Fixtures and golden files must explain what contract they represent.
   - Do not add comments that merely repeat `Arrange / Act / Assert` unless the project convention requires it.

5. Inline comments inside function bodies
   - Use comments for critical logic only:
     - business rule authority;
     - compatibility branch;
     - state transition;
     - concurrency or locking reason;
     - idempotency or retry decision;
     - transaction boundary;
     - performance tradeoff;
     - external API quirk;
     - security-sensitive validation;
     - fallback behavior;
     - non-obvious algorithm step.
   - Avoid comments for obvious assignments, simple conditionals, basic loops, and direct function calls.

6. Comment minimalism
   - Prefer better naming and extraction over explanatory comments.
   - If a comment explains confusing code, first try to simplify or rename the code.
   - Delete stale, redundant, misleading, or decorative comments.
   - Do not generate banner comments, noise comments, or comments that narrate every line.

# Failure Modes

- **Cross-language idiom contamination** — Symptom: Go code with abstract factories and `interface{}` dispatch; Rust code with deep `Box<dyn Trait>` hierarchies mimicking Java. Cause: author fluent in different language. Detection: code review against language-specific style guide. Impact: maintainers fluent in the target language find code unreadable and bug-prone.
- **Type system trusted at boundary** — Symptom: production crash on malformed external input. Cause: TypeScript / Java / Rust type annotations assumed at the HTTP/queue/file boundary. Detection: missing validator (zod / jakarta-validation / serde with `#[serde(deny_unknown_fields)]`) at boundary. Impact: invariant breach, data corruption.
- **Unchecked AI hallucination** — Symptom: import of nonexistent module, call to invented function, mixed sync/async APIs. Cause: AI-generated code merged without idiom audit. Detection: type-check / import-check / library doc verification. Impact: build break or runtime crash at first use.
- **Resource leak from idiom violation** — Symptom: fd / goroutine / connection count grows monotonically. Cause: missing `defer`/`with`/try-with-resources/RAII. Detection: leak detector, fd-count metric. Impact: rolling OOM / connection exhaustion.
- **Shell quoting omission** — Symptom: script fails on filenames with spaces; worse, script executes attacker-controlled string. Cause: unquoted `$variable` expansions. Detection: ShellCheck SC2086, SC2046. Impact: data loss, command injection.
- **String-composed SQL** — Symptom: SQLi in code review. Cause: idiom violation (using string concatenation instead of parameterized query). Detection: linter / static analysis (semgrep, CodeQL). Impact: CWE-89 exposure.
- **Bare `except:` / `catch (Throwable)`** — Symptom: errors silently swallowed, debugging impossible. Cause: idiom violation. Detection: ruff E722 / sonar-rule. Impact: production silent-failure mode.
- **Sync-in-async call** — Symptom: event-loop stall in Python asyncio / Node.js. Cause: blocking call inside async context. Detection: event-loop lag metric, async-profiler. Impact: head-of-line blocking.

# Evidence Contract

Language idiom enforcement is complete only when the output includes:

- **Language surface**: language/runtime version detected and the idiom rule selected.
- **Repository convention**: local naming, file layout, error handling, test style, import/module pattern, and framework convention inspected.
- **Idiom decision**: what was changed to match the language/repository idiom and what was intentionally left unchanged.
- **Anti-pattern rejected**: copied style from another language, invented abstraction, framework-incorrect pattern, or repository-inconsistent naming.
- **Validation evidence**: formatter, linter, typecheck, test command, or explicit not-verified disclosure with reason.
- **What evidence proves**: the changed code follows the inspected language and repository conventions for the covered surface.
- **What evidence does not prove**: all project conventions, uninspected languages, runtime performance, or behavior outside the touched surface.
- **Residual risk**: remaining convention uncertainty, owner, and trigger for follow-up review.

# Output Contract

Return an **Idiom Review Report** containing:
- **Language(s) in scope** with version pin
- **Repository conventions** in effect (formatter, linter, test framework, naming) and their config locations
- **Idiom violations found** (file:line, violated idiom, severity, suggested fix) — categorized as Correctness / Maintainability / Security / Performance
- **Required rewrites** (must-fix before merge) with patch suggestion
- **Accepted exceptions** with documented reason, scope, owner, expiration
- **Tool-check status**: formatter pass/fail, linter pass/fail, type-checker pass/fail, security-static-analysis pass/fail — with command lines
- **AI-generated blocks**: identified, audited, verdict (accept / rewrite / reject)
- **Residual concerns** with owner and re-evaluation trigger

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

# Used By

backend-change-builder, frontend-change-builder, ai-code-review-refactor, quality-test-gate

# Handoff

- **Matching `<lang>-professional-usage` capability** for tool pins, language-specific deeper rules, and runtime-specific idioms.
- **`language-testing-strategy`** for tests matched to the language's failure modes.
- **`ai-code-review-refactor`** for residual AI-generated audit work.
- **`security-privacy-gate`** for idiom violations mapped to CWE / OWASP risks.
- **`solution-optimality-evaluation`** for idiom-vs-performance tradeoff resolution.

# Completion Criteria

Idiom review is complete when: formatter and linter pass with project config; idiomatic patterns are used for errors / resources / concurrency / boundaries / public APIs; any deviation is documented with owner, scope, and expiration; AI-generated blocks are explicitly audited; and a maintainer fluent in the language can read, test, and evolve the code without mentally translating foreign idioms.
