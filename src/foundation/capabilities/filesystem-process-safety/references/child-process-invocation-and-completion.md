# Child Process Invocation And Completion

- Execute the selected program directly with structured argv. Define lookup, environment, working directory, inherited resources, stdio, completion, cancellation, and reconciliation.

**Load when:** Executable selection, argv, environment, working directory, inherited resources, standard streams, exit, timeout, cancellation, descendants, cleanup, or result certainty can change the decision.

**Do not load when:** No direct child-process execution contract changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `proof-limit`, `residual-risk`

Official sources were accessed on 2026-07-26.

## One Decision

Bind program identity and structured inputs to bounded, observable completion. Shell execution belongs to `shell-cli-professional-usage`.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Program identity | Select an exact path or documented lookup policy; record expected program identity | Current directory, `PATH`, extension, quoting, or platform parsing selects another program |
| Arguments and environment | Pass structured argv and explicit environment for deterministic behavior | User text becomes command syntax or ambient variables change behavior |
| Working directory | Use the operation’s controlled working directory | Relative paths resolve in an unintended location |
| Inherited resources | Allowlist standard streams and required descriptors or handles; close others | Unrelated handles, locks, sockets, or pipes prevent cleanup |
| Standard streams | Define stdin closure, binary or text encoding, output caps, redaction, and concurrent stdout/stderr draining | Full pipes deadlock, decoding loses evidence, or unbounded capture exhausts memory |
| Completion | Wait and reap; distinguish spawn failure, normal/signaled/forced exit, partial output, and program-specific exit meanings | Startup or one output line is mistaken for completion |
| Timeout and cancellation | Define deadline, graceful request, escalation, descendant scope, final wait, and late-result handling | A child or descendant remains active after return |
| Result reconciliation and cleanup | After termination, reconcile durable effects before retry; release process, pipe, job, and group resources | Timeout or cancellation duplicates effects or leaves an unknown result unowned |

## Platform Constraints

- POSIX path search, argv and environment vectors, signals, and wait/reap differ from Windows application-name, command-line, environment, current-directory, and handle inheritance rules.
- Bind descendants through a runtime-supported process group or job when the current operation owns them.
- Match termination, final wait, and cleanup to the exact wrapper; direct-child termination alone is not completion.

## Failure Rules

- Preserve direct argv, concurrent stream draining, bounded output, separate-stream evidence, terminal wait, and resource release.
- When timeout, cancellation, or forced termination leaves effects unknown, reconcile the result before retry.
- Preserve spawn, stream, exit, timeout, cleanup, and reconciliation failures as distinct outcomes.

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

These sources do not establish repository wrappers, program versions, platform argument conversion, exit meanings, descendant integration, external effects, or resource limits. Exercise structured edge cases, missing programs, stream saturation, nonzero exits, timeout escalation, cancellation races, descendants, cleanup, and result reconciliation for the changed path.
