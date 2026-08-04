# Node.js Process, Modules, And Resources Contracts

**Load when:** Process exit, signals, child processes, Worker threads, ESM/CommonJS, package exports, module cache identity, or active-resource ownership changes.

**Do not load when:** Process, module, and resource lifecycles remain unchanged and focused consumer and teardown evidence already settles them.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `decision-record`, `proof-limit`

## One Decision

Select one lifecycle and module contract that preserves terminal outcomes, consumer compatibility, cache identity, and owned-resource teardown.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Process terminal state | Natural drain or explicit exit, exit code, fatal-error policy, synchronous finalization, and supervisor handoff | `process.exit()` truncates pending output or cleanup |
| Signal | Supported platforms, installed handlers, default behavior, repeated signal, deadline, and forced termination | A handler suppresses default exit without completing shutdown |
| Child process | Spawn API, shell use, arguments, stdio flow, timeout/signal, IPC, exit/close, and descendant policy | Buffered stdio deadlocks or parent completion orphans a child |
| Worker | CPU rationale, pool owner, queue bound, clone/transfer/share contract, message errors, and termination | Per-request Workers amplify load or transferred data is reused |
| Module mode | `type`, extension, import/require entrypoint, resolution, side effects, cycles, and top-level await | Supported consumers execute different initialization paths |
| Package exports | Public subpaths, conditions, target Node.js versions, and compatibility baseline | Adding `exports` hides a previously reachable entrypoint |
| Cache identity | CommonJS resolved filename, ESM URL identity, query/fragment use, and singleton expectation | One logical module initializes more than once |
| Active resources | Owner, close/destroy/terminate order, failure cleanup, diagnostic baseline, or explicit detached liveness owner and lifetime | `unref()` is mistaken for teardown while the resource remains active without an accountable owner |

## Verification

- Exercise natural drain, configured signals, repeated termination, fatal error, and forced-shutdown deadline.
- Exercise child spawn failure, stdout/stderr saturation, timeout, abort, nonzero exit, IPC closure, and cleanup.
- Exercise Worker message failure, transfer ownership, queue saturation, termination, and parent shutdown.
- Load every supported ESM/CommonJS export and subpath, including a cycle or cache-sensitive path when reachable.
- Compare active-resource information before setup and after teardown while accounting for the test harness.
- For deliberately detached or unreferenced resources in scope, prove the named liveness owner, bounded lifetime, shutdown/reacquisition path, and terminal result separately from cleanup.

## Primary Sources

- [Node.js process documentation](https://nodejs.org/api/process.html)
- [Node.js child process documentation](https://nodejs.org/api/child_process.html)
- [Node.js Worker threads documentation](https://nodejs.org/api/worker_threads.html)
- [Node.js CommonJS modules documentation](https://nodejs.org/api/modules.html)
- [Node.js ECMAScript modules documentation](https://nodejs.org/api/esm.html)
- [Node.js packages documentation](https://nodejs.org/api/packages.html)

Official Node.js pages were accessed on 2026-07-26.

## Proof Limits

Lifecycle and consumer tests prove only the exercised Node.js versions, flags, platforms, entrypoints, signals, and teardown paths. Active-resource information is diagnostic rather than proof of absence, and no local test proves production supervision, descendant cleanup, or compatibility for untested consumers.
