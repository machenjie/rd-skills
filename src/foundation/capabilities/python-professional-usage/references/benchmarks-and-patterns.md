# Python Professional Usage Benchmarks And Patterns

Use this reference when Python work needs deeper detail than the root `SKILL.md` should carry: tooling/version decisions, graph/memory/execution reuse, validation matrices, async/GIL/runtime patterns, packaging evidence, security-sensitive scripting, or anti-pattern review.

## Tooling And Runtime Evidence Matrix

| Surface | Inspect | Validation Evidence | Common False Proof |
| --- | --- | --- | --- |
| Runtime version | `.python-version`, `pyproject.toml`, CI image, Dockerfile, lock metadata. | `python --version`, CI matrix, runtime policy exception. | Developer laptop version only. |
| Formatting/linting | `[tool.ruff]`, generated file excludes, noqa policy. | `ruff check` and `ruff format --check` with project config. | Running ruff on one file while changed packages are skipped. |
| Typing | public APIs, `Any`, dynamic imports, generated clients, pydantic models. | `mypy --strict` or pyright strict plus justified ignores. | Type hints without a type-checker run. |
| Packaging | `pyproject.toml`, lockfile, editable installs, import layout. | Frozen install command and import smoke test. | Unpinned `pip install` or ad hoc virtualenv success. |
| Tests | pytest config, fixtures, async mode, monkeypatch scope. | Focused pytest plus broader validator mapped by changed paths. | Happy-path test or local green run before final edit. |
| Security | deserialization, subprocess, SQL, path handling, secrets in logs. | `bandit`, `pip-audit` or `osv-scanner`, and hostile-input tests. | Static scan without reviewing untrusted boundaries. |

## Graph, Memory, And Execution Coupling

- Use repository graph to find Python package roots, config files, tests, generated clients, scripts, import entrypoints, and CI commands.
- Treat project memory as a selector for fragile modules, prior tool decisions, or known failing fixtures; confirm every claim against current files and validation output.
- Use execution trajectory to decide whether lint/type/test/security evidence ran after the final Python, config, lockfile, fixture, or generated-artifact edit.
- Downgrade stale notebook output, old CI logs, previous benchmark runs, and copied examples to residual risk unless their timestamp, scope, and unchanged graph boundary are explicit.
- Prefer source and configured commands over prose conventions when evidence conflicts.

## Async, GIL, And Runtime Pattern Checks

| Pattern | Professional Decision | Evidence |
| --- | --- | --- |
| Sync IO in async handler | Use async client or bounded `to_thread`; set timeout and cancellation behavior. | Event-loop lag, cancellation test, or explicit not-verified disclosure. |
| CPU-bound thread pool | Use process pool, native/vectorized path, or keep serial if hot-path evidence is absent. | Profile, CPU utilization, benchmark, and GIL rationale. |
| Broad `asyncio.gather` fan-out | Bound fan-out with semaphore/task group; preserve cancellation and partial-failure semantics. | Oversized-input test, timeout behavior, and error aggregation check. |
| Module-level mutable state | Move to dependency injection, contextvars, or explicit lifecycle owner. | Test-order/randomized run, worker/process behavior review. |
| Resource lifecycle | Use context managers and close files, sessions, responses, cursors, temp dirs, and locks on all paths. | Cleanup test, leak check, or code review artifact. |

## Python Validation Command Map

| Claim | Minimum Evidence | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| Type boundaries are safe | strict mypy/pyright and runtime validators at external boundaries. | Inspected internal types and boundary validators align. | Hostile production payloads outside tested fixtures. |
| Environment is reproducible | frozen lockfile install in CI or equivalent local clean env. | The selected environment can install deterministically. | Future resolver behavior or untested optional extras. |
| Async path is non-blocking | static scan plus lag/cancellation/profile evidence where risk exists. | Inspected path avoids known blocking calls or bounds them. | Every scheduler interleaving or production p99. |
| Fixtures are isolated | pytest with relevant fixture scope and cleanup checks. | Selected tests do not leak state in the checked run. | All suite orders or uninspected shared fixtures. |
| Script is safe to rerun | dry-run output, idempotency guard, rollback/compensation plan. | The scripted action has a bounded no-op/preview and rerun story. | Live production side effects unless executed in target environment. |

## Anti-Patterns To Reject

- Treating type hints as runtime validation for HTTP, queue, CLI, file, dataframe, or SDK input.
- Adding `# type: ignore`, `Any`, `cast`, or broad `dict[str, Any]` without owner, scope, and expiration.
- Running package installers or lockfile updates without frozen/reproducible install evidence.
- Testing private helpers while public CLI/API/service behavior remains unverified.
- Using notebooks or one-off scripts as production data repair without dry-run, idempotency, redaction, and rollback.
- Calling `pickle`, unsafe YAML loaders, shell strings, or string-built SQL on untrusted input.
- Approving async code without checking sync libraries, cancellation, timeout, and fan-out bounds.
