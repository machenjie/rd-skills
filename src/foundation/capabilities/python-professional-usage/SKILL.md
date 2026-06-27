---
name: python-professional-usage
description: Use when writing or reviewing professional Python for services, scripts, automation, data or AI tooling, or libraries with focus on type boundaries, runtime validation, packaging, virtual environments, pytest fixtures, async boundaries, GIL limits, and reproducibility.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "92"
changeforge_version: 0.1.0
---

# Mission

Enforce professional Python usage — typing discipline, runtime validation, async/sync boundary safety, packaging, reproducible environments, pytest hygiene, GIL-aware concurrency, and idempotent operational scripts — against pinned tooling and a measured runtime. Reject ad-hoc Python that runs once on a developer's laptop and fails in CI or production.

# Pinned Tooling Baseline (Python)

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- **Runtime**: Python ≥ 3.11 (3.12 preferred). 3.10 acceptable only if a hard dependency requires it; document the exception. **3.8 / 3.9 are EOL/EOL-imminent and rejected for new work.**
- **Formatter / linter**: `ruff` ≥ 0.5 (replaces black + isort + flake8 + pyupgrade + pydocstyle); configured via `[tool.ruff]` in `pyproject.toml`.
- **Type checker**: `mypy` ≥ 1.10 with `--strict` (or pyright `strict`). `Any` requires inline justification.
- **Runtime validation**: `pydantic` v2 (or `msgspec` / `attrs` + cattrs) at every external boundary.
- **Test runner**: `pytest` ≥ 8 with `pytest-asyncio` ≥ 0.23 (mode = strict) or `anyio` for cross-runtime tests.
- **Coverage**: `coverage` ≥ 7 with `branch = true`; mutation testing via `mutmut` or `cosmic-ray` on critical modules.
- **Packaging**: `pyproject.toml` (PEP 621) only — no `setup.py` for new work; build backend = `hatchling` / `setuptools` / `pdm-backend`.
- **Environment manager**: `uv` (preferred) or `poetry` ≥ 1.8 or `pip-tools`. Lockfile mandatory (`uv.lock` / `poetry.lock` / `requirements.txt` with `--generate-hashes`).
- **CI install**: `uv sync --frozen` / `poetry install --no-update` / `pip install --require-hashes -r requirements.txt`. Plain `pip install <pkg>` in CI is rejected.
- **Security**: `pip-audit` and/or `osv-scanner` in CI; `bandit` for static security checks on services.

# When To Use

Use when Python services, async APIs, scripts, automation, data/AI pipelines, libraries, or pytest tests are added or reviewed. Use whenever a Python environment is created, locked, or upgraded; whenever an external boundary (HTTP request, queue message, CLI argument, file content) crosses into Python code.

# Do Not Use When

Do not use for syntax lessons. Do not use to bless ad-hoc scripts that mutate production state without dry-run / idempotency / rollback. Do not use to justify staying on EOL Python.

# Stage Fit

Launched in coding, bug-fix, debugging, code-review, refactoring, testing, release-readiness, and final handoff. Per-stage focus:

- **coding**: type hints, runtime validation, packaging, async/sync boundary, context manager.
- **debugging-diagnosis**: blocking call in async, fixture leakage, import side effects, GIL/concurrency.
- **code-review**: dynamic boundary validation, mutable defaults, broad `except`.
- **refactoring**: module/package boundary, public `__all__` surface, dependency-injection seams.
- **testing**: pytest fixtures, monkeypatch boundaries, deterministic data.
- **release / handoff**: validation freshness, lockfile/tooling evidence, graph/memory/execution reuse judgment, residual runtime risk, and next gate.

# Non-Negotiable Rules

- **Type hints protect module boundaries.** Public functions and class methods are fully annotated. `mypy --strict` (or pyright strict) passes in CI. `Any` is justified inline with `# type: ignore[reason]` or replaced with `object` / `unknown`-pattern `TypeVar`.
- **External boundaries are validated at runtime.** HTTP request bodies, queue messages, file contents, CLI args, env vars: pass through pydantic v2 / msgspec / Click types. Type hints alone are not runtime validation.
- **Asyncio event loop is never blocked.** No sync IO (requests, sync DB driver, file IO, `time.sleep`) in async code; use `asyncio.to_thread` / `anyio.to_thread.run_sync` for sync calls; instrument `loop.slow_callback_duration`.
- **GIL-aware concurrency**: CPU-bound parallelism uses `concurrent.futures.ProcessPoolExecutor` or `multiprocessing`, not threads. IO-bound parallelism uses `asyncio` (preferred) or threads. Free-threaded CPython 3.13t (PEP 703) is experimental — do not depend on it in production yet.
- **Pytest fixtures are isolated and deterministic.** Module-scoped DB / network fixtures must clean up; randomness seeded; time mocked (`freezegun` / `time-machine`); no test depends on test ordering. `pytest -p no:randomly` baseline + opt-in random ordering for new code.
- **Packaging is reproducible.** `pyproject.toml` only; lockfile + hashes mandatory for applications; CI install via frozen lockfile.
- **Scripts that touch production are idempotent and support `--dry-run`.** A re-run after partial failure must not duplicate, double-charge, or corrupt. Use checksums / idempotency keys / upsert-with-condition.
- **Logging via `logging` module with structured fields** (JSON or `structlog`); never `print()` in services; secrets never logged.
- **Exception handling**: no bare `except:`; narrow exception classes; chain causes with `raise X(...) from err`.
- **Python claims require current repository and execution evidence.** Project memory, old CI output, prior `mypy`/`ruff`/`pytest` runs, generated summaries, or package-lock assumptions are only discovery inputs until current `pyproject.toml`, lockfile, imports, tests, generated artifacts, and validation output confirm them after the final material edit.
- **Python tool runs that can mutate files or expose data need permission and output boundaries.** Formatters, codemods, package installers, lockfile updates, notebook/data scripts, migration scripts, and production-affecting CLIs must record tool/action class, permission state, sandbox or dry-run boundary, rollback/revert path, and redaction rule before execution.

# Industry Benchmarks

- **PEP 8 / 257 / 484 / 561 / 585 / 604 / 612 / 695 / 696** for style, docstrings, typing, runtime-checkable types, generics, type-parameter syntax.
- **PEP 668** (externally-managed environments), **PEP 621** (pyproject metadata), **PEP 723** (inline script metadata for single-file scripts).
- **PEP 703** (no-GIL CPython, experimental in 3.13t) / **PEP 734** (per-interpreter GIL).
- **CPython performance work**: Faster CPython (3.11+), specialization (PEP 659), JIT preview (3.13+).
- **`uv` (Astral)** as the modern packaging and resolver standard; `ruff` as the consolidated lint/format tool.
- **OWASP Python Security**, CWE-89 / 78 / 502 / 22 (SQLi, command injection, deserialization, path traversal) anti-patterns and their idiomatic fixes.
- **DORA**, **Twelve-Factor App** principles for Python services.

# Selection Rules

Select when Python services, libraries, scripts, automation, data pipelines, AI tooling, package metadata, or pytest tests are part of the request. Pair with `language-idiom-enforcement`, `language-testing-strategy`, `language-performance-safety`, and `package-dependency-management`.

# Proactive Professional Triggers

- **Signal:** A Python file, test, notebook, script, CLI, worker, package config, or generated client is edited based on repository graph proximity, project memory, prior CI output, or execution trajectory. **Hidden risk:** stale imports, tool versions, lockfiles, generated artifacts, or validation runs are treated as current proof. **Required professional action:** inspect current source, `pyproject.toml`, lockfile, tests, and generated artifacts before reuse, then rerun or downgrade stale validation. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`, and this capability. **Evidence required:** inspected paths, accepted/rejected reuse, command/report path, exit code or manual artifact, freshness limit, and residual risk owner.
- **Signal:** HTTP body, queue message, CLI arg, env var, file content, pandas/CSV row, notebook cell output, model payload, or external SDK response enters Python code without runtime validation. **Hidden risk:** type hints and dataframe schemas are mistaken for runtime guards, causing malformed input, data corruption, or unsafe deserialization. **Required professional action:** require pydantic v2/msgspec/Click/typed parser or equivalent validation at the boundary plus negative fixtures. **Route to:** `language-idiom-enforcement`, `quality-test-gate`, and `security-privacy-gate` when untrusted input is involved. **Evidence required:** boundary list, validator location, invalid-input test, and what static typing does not prove.
- **Signal:** Async Python code calls sync IO, CPU-heavy work, blocking SDKs, `time.sleep`, sync DB clients, or broad `gather` fan-out. **Hidden risk:** event-loop blocking, cancellation leaks, thread-pool exhaustion, or GIL contention survives unit tests and appears as p99 latency failure. **Required professional action:** classify async/sync boundary, move work to bounded executor or async client, and require lag/cancellation/load evidence or a not-verified disclosure. **Route to:** `language-performance-safety`, `concurrency-control`, and `quality-test-gate`. **Evidence required:** call site, executor/async choice, cancellation/timeout test, profile or lag command, and residual runtime risk.
- **Signal:** Python tooling, dependency, lockfile, formatter, type checker, test runner, package metadata, import path, or environment manager changes. **Hidden risk:** local success hides CI drift, dependency confusion, non-reproducible installs, or package import breakage. **Required professional action:** verify frozen install path, lockfile freshness, package metadata, import surface, and dependency/security scan proportional to risk. **Route to:** `package-dependency-management`, `validation-broker`, and this capability. **Evidence required:** config paths, lockfile state, install command, type/lint/test/security command, and what the command does not prove.
- **Signal:** A Python script, notebook, migration, data repair, filesystem operation, subprocess call, or automation can mutate external state, write broad paths, run shell commands, or process sensitive data. **Hidden risk:** a "simple script" becomes non-idempotent, non-repeatable, or leaks secrets/PII through prints, logs, notebooks, reports, or stack traces. **Required professional action:** require `--dry-run`, idempotency key/checksum/upsert guard, narrow path scope, safe subprocess argv, redaction, and rollback or compensation. **Route to:** `agent-tool-permission-sandbox`, `security-privacy-gate`, `quality-test-gate`, and this capability. **Evidence required:** command/action class, permission state, dry-run output, rollback path, redaction rule, and rerun-safety test or residual risk.

# Risk Escalation Rules

- Escalate to `language-performance-safety` for asyncio event-loop blocking, GIL contention, allocation pressure, or hot-path memory churn.
- Escalate to `package-dependency-management` for new dependencies, lockfile / environment changes, or CVE response.
- Escalate to `quality-test-gate` for fixture / integration / hostile-input test evidence.
- Escalate to `security-privacy-gate` for deserialization (`pickle` / `yaml.load`) risk, SQL injection, command injection, secrets handling.
- Escalate to `reliability-observability-gate` for async-runtime production SLO risk.

# Critical Details

- **Type hints ≠ runtime safety.** `def f(x: int)` does not reject `f("hello")` at runtime. Validators (pydantic v2 / msgspec / dataclasses + cattrs) convert + reject at the boundary; type hints provide static guarantees only inside the validated zone.
- **Pydantic v2 vs v1**: v2 is C-extension Rust-backed; ~5-50× faster than v1. New projects pin pydantic ≥ 2.5; migration from v1 is non-trivial (validators, config, serializers all changed).
- **`asyncio.TaskGroup` (3.11+)** is the structured-concurrency primitive; cancellation propagates correctly. Prefer over bare `asyncio.gather` for new code.
- **`async def` boundary**: a single sync call (e.g., `requests.get`, `psycopg2.execute` without async, `time.sleep`) inside async code blocks the entire event loop. Use `aiohttp` / `httpx` (async mode) / `asyncpg` / `aiomysql` / `asyncio.sleep`. If sync is unavoidable, wrap in `asyncio.to_thread`.
- **GIL impact**: in CPython 3.12 and earlier, threads share one interpreter lock; CPU-bound parallelism does not scale across threads. Use `ProcessPoolExecutor` for CPU-bound work, `ThreadPoolExecutor` for blocking IO (or move to async). PEP 703 free-threaded build (3.13t) is experimental — not production-grade as of 3.13.
- **Mutable default arguments**: `def f(items=[])` is a CWE-class bug — the list is shared across calls. Use `None` + sentinel.
- **`dict.get()` vs `dict[k]`**: explicit choice; don't silently swallow KeyError with `.get()` when the key is required.
- **Logging in libraries**: use `logging.getLogger(__name__)`; library code must not call `logging.basicConfig()`.
- **Singleton / module-state pitfalls**: module-level mutable state shared across tests and across uvicorn workers; prefer dependency injection or `contextvars`.
- **Deserialization is a security boundary.** `pickle.load`, `yaml.load` (without `SafeLoader`), `eval`, `exec` are RCE primitives. Use `json` / `yaml.safe_load` / pydantic.
- **Subprocess**: `subprocess.run([...], shell=False)` with a list, never `shell=True` with a composed string; if shell is required, `shlex.quote`.

# Failure Modes

- **Unvalidated boundary** — Symptom: 500 on malformed JSON. Cause: type hint trusted at HTTP boundary. Detection: pydantic / msgspec at every entrypoint. Impact: outage on hostile input.
- **Async blocked** — Symptom: event-loop lag, p99 latency cliff. Cause: sync IO inside async path. Detection: `loop.slow_callback_duration` metric; py-spy profile. Impact: head-of-line blocking.
- **Fixture leak** — Symptom: test passes alone, fails in suite. Cause: module-scoped fixture without cleanup; shared mutable state. Detection: `pytest --randomly`. Impact: test suite unreliable.
- **Non-idempotent operational script** — Symptom: rerun after partial failure duplicates rows / double-sends emails. Cause: no idempotency key / no upsert with condition. Detection: chaos rerun test. Impact: data corruption.
- **Unpinned environment** — Symptom: works on laptop, fails in CI. Cause: requirements.txt without lockfile/hashes. Detection: lockfile mandate in CI. Impact: non-reproducible.
- **Mutable default arg** — Symptom: list/dict accumulates across calls. Cause: `def f(x=[])`. Detection: ruff B006. Impact: cross-request data leak.
- **`pickle` / `yaml.load` RCE** — Symptom: deserialization of attacker-controlled bytes. Cause: unsafe deserializer. Detection: bandit B301/B506. Impact: RCE.
- **`subprocess(shell=True, <user_str>)`** — Symptom: command injection. Cause: shell composition. Detection: bandit B602/B605. Impact: RCE.
- **EOL Python** — Symptom: CVE without upstream patch. Cause: pinned to 3.8/3.9. Detection: runtime lifecycle audit. Impact: forced upgrade under deadline.
- **GIL on CPU-bound threads** — Symptom: no speedup from `ThreadPoolExecutor` on CPU work. Cause: GIL. Detection: profile shows single-core utilization. Impact: latency / throughput floor.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 Python selection, rules, output, and gates. Read [references/checklist.md](references/checklist.md) when Python changes touch async/sync boundaries, IO/API validation, resource lifecycle, shared mutable state, imports/packaging, pytest fixtures, monkeypatching, or runtime typing gaps. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when tooling/version selection, validation matrices, graph/memory/execution reuse, async/GIL/runtime patterns, packaging evidence, or anti-pattern depth is needed. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for a trivial local script copy edit.

# Output Contract

Return a **Python Usage Review** containing:
- **Python version** in use; deprecation/EOL status
- **Tooling pins**: ruff / mypy / pytest / pydantic / packaging tool versions (from `pyproject.toml`)
- **Type-boundary status**: `mypy --strict` result; `Any` instances with justification
- **Runtime validation coverage**: every external boundary listed with its validator
- **Async/sync risks**: blocking calls in async paths; event-loop lag instrumentation; GIL impact on CPU-bound work
- **Concurrency model**: asyncio / threads / processes / multiprocessing with rationale
- **Packaging & environment**: `pyproject.toml` + lockfile present? CI install command reproducible?
- **Test fixture safety**: isolation, randomness seeding, time mocking, ordering independence
- **Script idempotency**: `--dry-run` present? idempotency key / upsert / rollback path?
- **Security**: bandit clean? pip-audit clean? deserialization / subprocess / SQL parametrization audited?
- **Logging**: structured + no secrets?
- **source_evidence**: current Python files, `pyproject.toml`, lockfile, imports, repository graph, project memory, execution trajectory, generated artifacts, CI/test history, and freshness limits
- **validation_commands**: ruff, mypy/pyright, pytest, coverage/mutation, bandit/pip-audit/osv, lockfile/install, async/profile/manual-review command; validator/tool; artifact/report path; output/exit code or manual result; changed Python scope; freshness after final edit
- **changed_python_to_validation_map**: each type/runtime boundary, async/sync choice, dependency/tooling decision, fixture/script/security/runtime-risk decision mapped to validator, test, review, or residual risk
- **Accepted exceptions** with owner / scope / expiration

# Evidence Contract

A Python change is professionally complete only when the output includes:

- **Type/runtime boundary**: type hints, runtime validation where data crosses IO/API boundaries, and `Any`/dynamic typing justification.
- **Async/sync boundary**: no blocking IO inside event loop, cancellation behavior, timeout handling.
- **Resource lifecycle**: context managers for files, sockets, sessions, locks, and temporary resources.
- **Mutable/default state**: no unsafe mutable defaults, shared globals, or test-order coupling.
- **Packaging/import boundary**: module placement, dependency direction, import side effects.
- **Test evidence**: pytest fixture ownership, monkeypatch scope, and async test behavior when applicable.
- **What evidence proves**: the inspected Python runtime and boundary risk is covered.
- **What evidence does not prove**: production load, all interpreter versions, external dependency behavior, or cross-language clients.
- **Residual risk**: untested runtime behavior, owner, and next gate.

Close a Python usage review only when it names selected mode, Python/runtime/tooling scope, current source evidence inspected, boundaries inspected, graph/memory/execution reuse judgment, type/runtime validation boundary, async/sync and GIL decision, packaging/import boundary, fixture/script safety, changed-Python-to-validation map, validation evidence, behavior preservation, residual risk, and next gate. State what evidence proves, what evidence does not prove, reuse and placement rationale for repository graph/project memory/execution trajectory claims, and validation freshness after the final material edit. A local `pytest` pass does not prove type safety, packaging reproducibility, security scan status, or production event-loop behavior unless those surfaces were actually validated.

# Quality Gate

1. Python version ≥ 3.11 (or documented exception); not EOL.
2. `ruff check` + `ruff format --check` + `mypy --strict` (or pyright strict) pass in CI.
3. Every external boundary has runtime validation (pydantic v2 / msgspec / equivalent).
4. Async code path has no sync blocking call; event-loop lag instrumented.
5. Pytest suite passes with `--randomly` and `-p no:cacheprovider`; coverage ≥ 80% line + mutation score ≥ 60% on critical modules.
6. Lockfile present and CI installs with frozen lockfile + hashes.
7. `bandit -ll` and `pip-audit` (or `osv-scanner`) green or triaged.
8. Operational scripts have `--dry-run` and idempotency mechanism.
9. Repository graph, project memory, and execution trajectory evidence are current-source confirmed or explicitly marked stale/not verified.
10. Validation commands or manual review procedures record validator/tool, report/artifact, output and exit code or manual result, changed scope, freshness, what evidence proves, and what evidence does not prove.

# Used By

backend-change-builder, ai-product-extension, bigdata-product-extension, quality-test-gate, delivery-release-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`package-dependency-management`** for new dependency / lockfile / environment risk.
- **`language-performance-safety`** for asyncio blocking, GIL, allocation pressure.
- **`quality-test-gate`** for fixture / integration / mutation-test evidence.
- **`security-privacy-gate`** for deserialization, injection, secrets risk.
- **`reliability-observability-gate`** for production async runtime SLO concerns.

# Completion Criteria

Review is complete when: tooling pins are verified; type-boundary + runtime-validation coverage are explicit; async/GIL risks are answered; environment is reproducible; tests are isolated and meaningful; operational scripts are idempotent with dry-run; and security baseline (bandit + pip-audit) is green or triaged with owner.
