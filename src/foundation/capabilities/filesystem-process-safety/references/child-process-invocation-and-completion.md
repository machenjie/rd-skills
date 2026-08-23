# Child Process Invocation And Completion

- Execute a selected program directly with structured argv. Make lookup, environment, working directory, credential, and inherited-resource policy explicit; route shell semantics elsewhere.

**Load when:** Executable selection, argv, environment, working directory, inherited resources, standard streams, exit, timeout, cancellation, descendants, cleanup, or result certainty can change the decision.

**Do not load when:** No direct child-process execution contract changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `proof-limit`, `residual-risk`

Official sources were accessed on 2026-07-26.

## One Decision

Select one direct-process contract that binds program identity and inputs to a bounded, observable completion result. Treat shell execution as a different contract owned by `shell-cli-professional-usage`.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Program identity | Select exact path or documented lookup policy, trusted search directories, and expected binary identity | Current directory, `PATH`, extension, quoting, or platform parsing selects another executable |
| Arguments and environment | Pass structured argv and an explicit required environment; classify secrets and locale or encoding inputs | User text becomes command syntax or ambient variables change behavior or leak authority |
| Working directory and authority | Set a controlled directory, credentials, permissions, and sandbox only from current requirements | The child reads or writes relative paths in an unintended location or inherits excess privilege |
| Inherited resources | Allowlist standard streams and required descriptors or handles; close everything else | The child retains a secret file, socket, token, lock, or pipe and prevents cleanup |
| Standard streams | Define stdin closure, binary or text encoding, output caps, redaction, and concurrent stdout/stderr draining | A full pipe deadlocks execution, decoding loses evidence, or unbounded capture exhausts memory |
| Completion | Wait and reap; map spawn failure, normal exit, signaled or forced exit, partial output, and program-specific exit meanings | Start success or one output line is reported as completed work |
| Timeout and cancellation | Define deadline, graceful request, escalation, descendant scope, final wait, and late-result handling | The caller returns while a child or descendant remains active |
| Side effects and cleanup | Reconcile durable effects before retry; close process, thread, pipe, and job/group resources on success, error, cancellation, and timeout paths | Timeout or cancellation duplicates effects or leaves an unknown result unowned |

## Platform Constraints

- POSIX path search, argv/environment vectors, signals and wait/reap differ from Windows application-name, command-line, environment/current-directory, and handle inheritance rules.
- Bound descendants only through runtime-supported process-group/job ownership, and match timeout cleanup to the exact wrapper; direct-child termination alone is insufficient.
- Do not project one wrapper's kill-and-wait contract onto another.

## Failure Rules

- Enforce the table's direct-argument, stream-draining, bounded-output, separate-stream, terminal-wait, and resource-release decisions.
- Timeout, cancellation, or forced termination leaves side effects unknown until durable effects are inspected or reconciled; never retry blindly.

## Primary Sources

- [POSIX `exec` functions](https://pubs.opengroup.org/onlinepubs/9799919799/functions/exec.html)
- [POSIX `posix_spawn()` and `posix_spawnp()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/posix_spawn.html)
- [POSIX `wait()` and `waitpid()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/wait.html)
- [POSIX `kill()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/kill.html)
- [Microsoft `CreateProcessW`](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)
- [Microsoft creating processes](https://learn.microsoft.com/en-us/windows/win32/procthread/creating-processes)
- [Microsoft job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- [Python subprocess management](https://docs.python.org/3/library/subprocess.html)

## Proof Limits

These sources do not establish the repository's runtime wrapper, executable version, platform argument conversion, or environment policy. They also do not establish process-tree integration, target program exit meanings, external side effects, or production resource limits. Representative tests need to exercise hostile arguments, missing executables, environment isolation, output saturation, nonzero and signaled exits, timeout escalation, cancellation races, descendants, cleanup, and reconciliation relevant to the changed path.
