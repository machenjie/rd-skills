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
- **Accepted exceptions** with owner / scope / expiration

# Quality Gate

1. Python version ≥ 3.11 (or documented exception); not EOL.
2. `ruff check` + `ruff format --check` + `mypy --strict` (or pyright strict) pass in CI.
3. Every external boundary has runtime validation (pydantic v2 / msgspec / equivalent).
4. Async code path has no sync blocking call; event-loop lag instrumented.
5. Pytest suite passes with `--randomly` and `-p no:cacheprovider`; coverage ≥ 80% line + mutation score ≥ 60% on critical modules.
6. Lockfile present and CI installs with frozen lockfile + hashes.
7. `bandit -ll` and `pip-audit` (or `osv-scanner`) green or triaged.
8. Operational scripts have `--dry-run` and idempotency mechanism.

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
