# Child Process Invocation And Completion

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

- POSIX `exec` and spawn variants distinguish exact executable paths from `PATH` search and pass argv and environment as explicit vectors. Waiting obtains and reaps status; sending a signal requests an action and is not completion evidence.
- Windows `CreateProcessW` separates application name from its command-line buffer. A null or ambiguous application name, inherited environment or current directory, and broad handle inheritance can change the selected program and authority.
- Define descendant ownership explicitly. POSIX process groups and Windows job objects are mechanisms only when the selected runtime creates and retains them correctly; terminating the direct child alone does not bound a process tree.
- Match timeout cleanup to the exact high-level runtime API.
- Do not project Python `run()` kill-and-wait behavior onto `Popen.communicate()` or another wrapper.

## Failure Rules

- Reject command strings assembled from untrusted data.
- Use direct structured arguments unless accepted behavior requires a shell.
- Drain both captured output streams concurrently or use the runtime's documented communication primitive before or while waiting.
- Preserve required partial stdout and stderr with bounded truncation metadata.
- Keep streams separate unless ordering loss from merging is accepted.
- Treat timeout, cancellation, and forced termination as unknown side-effect outcomes until the called program's durable effects are inspected or reconciled.
- After escalation, wait for the owned process or group to reach a terminal state and release resources; returning after a kill request is insufficient.

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
