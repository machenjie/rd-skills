---
name: linux-systems-professional-usage
description: Use when Linux systemd, process, file descriptor, permissions, cgroup, namespace, signal, package, kernel, container host, filesystem, or operational runtime behavior needs evidence-backed handling.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "132"
changeforge_version: 0.1.0
---

# Mission

Make Linux runtime changes safe under real process, permission, filesystem, cgroup, namespace, signal, service-manager, and host constraints. Treat Linux behavior as observable system state, not a guess from application code or container assumptions.

# When To Use

Use when a change touches systemd units, service lifecycle, process supervision, signals, daemons, file descriptors, sockets, permissions, users/groups, capabilities, seccomp, cgroups, namespaces, `/proc`, `/sys`, ulimits, kernel parameters, package/service install scripts, container host behavior, cron/timers, log/journald integration, DNS resolver behavior, filesystem mounts, temp directories, or Linux-only production incidents.

# Do Not Use When

Do not use for ordinary application code that merely runs on Linux without relying on OS-specific behavior. Do not duplicate low-level memory, ABI, or driver analysis owned by `low-level-systems-extension`; use this capability for operational Linux runtime and service behavior.

# Stage Fit

Use during planning, debugging, implementation, code-review, testing, release, and incident-repair stages when Linux runtime, service-manager, process, filesystem, cgroup, container-host, permission, resolver, or package behavior can change correctness, availability, security, rollback, or operability. Re-enter after systemd unit, package script, container runtime, cgroup/ulimit, environment file, signal/shutdown, resolver, mount/path/permission, logging, hardening, or privileged-command edits. Skip for ordinary application changes where no Linux-specific runtime dependency, service behavior, host policy, or operational command boundary changes.

# Non-Negotiable Rules

- Verify target environment: distro, kernel, init system, container/runtime, architecture, filesystem, user, cgroup version, namespace boundaries, and package manager when relevant.
- systemd units require explicit `User`, `Group`, `WorkingDirectory`, `EnvironmentFile`, restart policy, timeout policy, resource limits, hardening options, and logging behavior.
- Signal handling must be defined for shutdown, reload, child process cleanup, and timeout escalation.
- File paths, permissions, ownership, umask, temp files, sockets, and PID files must be explicit and safe under concurrent start/restart.
- Container behavior is not host behavior: PID 1, cgroups, DNS, mounts, capabilities, seccomp, and filesystem persistence must be verified in the actual runtime.
- Never diagnose as "environment issue" without command evidence from the target or a representative environment.
- Resource limits require observed or budgeted CPU, memory, fd, process, disk, inode, and network bounds.
- Logs must go to the configured sink with redaction: journald, stdout/stderr, syslog, or file rotation policy.
- Package/service scripts must be idempotent, restart-safe, and rollback-aware.
- Security hardening must preserve required behavior while minimizing privileges: no root service by default, no broad capabilities, no world-writable state.

# Industry Benchmarks

Anchor decisions against systemd service and sandboxing documentation, Linux man-pages for signals, procfs, capabilities, namespaces, cgroups, file permissions, and limits, CIS Linux Benchmarks, container runtime security guidance, FHS path conventions, journald/syslog logging practice, and SRE guidance for graceful shutdown and resource saturation.

# Selection Rules

Select when Linux runtime semantics, not generic code structure, decide correctness or operability. Pair with `reliability-observability-gate` for service SLOs and saturation, `security-privacy-gate` for capabilities and privilege boundaries, `delivery-release-gate` for package/service rollout, `shell-cli-professional-usage` for scripts, and `containerization` when container image/runtime behavior is primary.

# Risk Escalation Rules

Escalate to `security-privacy-gate` for root services, Linux capabilities, writable directories, setuid/setgid, secret files, seccomp, or public sockets. Escalate to `reliability-observability-gate` for restart loops, resource exhaustion, signal shutdown, or host-level saturation. Escalate to `delivery-release-gate` for package manager, systemd rollout, or kernel/sysctl changes. Escalate to `low-level-systems-extension` for kernel, driver, ABI, native memory, or syscall implementation work.

# Proactive Professional Triggers

- **Signal:** A Linux incident is called an "environment issue" or is diagnosed from only application logs. **Hidden risk:** the host/container/service boundary, resolver, cgroup, or permission layer is stale or unverified. **Required professional action:** capture target or representative environment evidence before repair. **Route to:** `reliability-observability-gate`, `observability`. **Evidence required:** distro/kernel/init/runtime, unit or process state, relevant log slice, command output, and residual untested host or runtime.
- **Signal:** A service, unit, package script, or container runtime change touches `User`, `Group`, `WorkingDirectory`, `EnvironmentFile`, `Restart`, `TimeoutStopSec`, `Limit*`, capabilities, seccomp, read/write paths, or log sinks without a contract. **Hidden risk:** privilege, secret exposure, restart-loop, shutdown, or filesystem behavior changes outside application tests. **Required professional action:** record the service/process/filesystem contract and rollback path. **Route to:** `delivery-release-gate`, `security-privacy-gate`. **Evidence required:** config artifact, before/after runtime boundary, validation command, rollback step, and owner.
- **Signal:** OOM, fd exhaustion, restart loops, resolver failures, tmpfs/mount issues, or permission errors are fixed by raising limits, chmod/chown, root, cleanup, or restart only. **Hidden risk:** symptom masking leaves saturation, leakage, or incorrect ownership in production. **Required professional action:** identify the emitting Linux layer and prove the new limit or permission is bounded and observable. **Route to:** `reliability-observability-gate`, `security-privacy-gate`. **Evidence required:** observed signal, limit/path owner, command output, alert/log path, and what remains unproven under load.
- **Signal:** A state-mutating Linux command is proposed: `systemctl restart`, package install/remove, `sysctl`, `chmod`, `chown`, mount, kill, cleanup, or privileged shell. **Hidden risk:** validation mutates host state, deletes evidence, breaks another service, or escalates privilege without rollback. **Required professional action:** classify tool permission, sandbox, dry-run, approval, and rollback before execution. **Route to:** `agent-tool-permission-sandbox`, `security-privacy-gate`. **Evidence required:** command class, write paths, privilege level, expected state change, rollback or cleanup path, and not-run status when blocked.
- **Signal:** Repository graph, project memory, old incident notes, previous command output, or historical runbooks are reused after unit/runtime/container/env/cgroup/path edits. **Hidden risk:** stale memory or execution evidence certifies the wrong runtime boundary. **Required professional action:** treat memory, graph, and trajectory as selectors, rerun selected source reads or probes, and mark stale evidence rejected. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected memory, changed paths, graph freshness, rerun command, exit code, and report or artifact path.

# Critical Details

- **PID 1 matters.** A process running as PID 1 in a container needs signal forwarding and child reaping, or shutdown hangs and zombies accumulate.
- **cgroup version changes evidence.** CPU/memory accounting, OOM behavior, and pressure signals differ across cgroup v1/v2 and container runtimes.
- **systemd restart policy can hide crashes.** Restart loops need backoff, `StartLimit*`, health readiness, and clear failure logs.
- **File descriptor and process limits fail late.** Set and observe `LimitNOFILE`, thread/process counts, socket backlog, and ephemeral port usage.
- **Environment files are contracts.** Missing or malformed env files should fail clearly; secrets should not appear in unit files or logs.
- **Filesystem semantics differ.** Overlayfs, bind mounts, tmpfs, read-only rootfs, SELinux/AppArmor labels, and NFS locks affect runtime behavior.
- **DNS and resolver behavior are runtime inputs.** `/etc/resolv.conf`, systemd-resolved, search domains, and ndots can change latency and failure mode.
- **Logs are diagnostic surface.** Journald unit logs, stdout/stderr, and file rotation must map to alert and incident workflows.
- **Resolver chain needs file and service evidence.** `/etc/hosts`, `/etc/resolv.conf`, systemd-resolved status, search domains, and `ndots` decide whether a DNS issue is local override, resolver config, split DNS, or upstream failure.
- **Privilege changes need a boundary record.** `sudo`, root services, Linux capabilities, privileged ports, setuid/setgid, and socket ownership must state why lower privilege is insufficient and how rollback restores least privilege.
- **Log rotation is part of runtime safety.** File logs need logrotate ownership, retention, compression, permissions, and disk-full behavior; journald-only services need journal retention expectations.
- **Security modules can change filesystem and process behavior.** SELinux/AppArmor labels, profiles, denials, and audit logs must be checked when permissions look correct but access fails.

# Failure Modes

- **systemd restart loop:** service crashes repeatedly but appears "active" between restarts; alert misses user impact.
- **Wrong user or path:** unit starts as root or from the wrong working directory, creating root-owned files the app later cannot write.
- **Container PID 1 shutdown gap:** SIGTERM is not handled; deployment waits until SIGKILL and loses in-flight work.
- **cgroup memory OOM:** process is killed by cgroup limit while host memory looks healthy.
- **fd exhaustion:** high connection count hits `ulimit -n`; app reports random network failures.
- **Writable secret leakage:** env file or socket directory is world-readable.
- **tmpfs persistence assumption:** restart loses state written under `/tmp` or ephemeral container filesystem.
- **Resolver latency:** DNS search path or ndots causes slow external lookups and request timeout.
- **Package script non-idempotence:** postinstall restarts or rewrites config unexpectedly during upgrade.

# Anti-Rationalization Table

| Rationalization | Hidden Risk | Required Correction |
|---|---|---|
| "It is just an environment issue." | Root cause remains unverified and repeats in production. | Capture target environment commands and isolate the failing layer. |
| "Run it as root to fix permissions." | Least privilege is bypassed and files become root-owned. | Fix ownership/capabilities or document a bounded privileged boundary. |
| "systemctl active means healthy." | Restart loops or readiness failures are hidden. | Inspect status, logs, restart counters, and health/readiness signals. |
| "Container limits are the same as host limits." | cgroup, namespace, DNS, PID 1, or mount behavior differs. | Verify inside the actual runtime boundary. |
| "Clear /tmp or logs to free space." | State or audit evidence is deleted and the growth cause remains. | Identify owner, retention, and rollback before cleanup. |

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, risk, and output-contract rules.

Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete Linux Systems Usage Record, incident handoff, package/service rollout, privileged-command review, or runtime checklist.
Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when systemd, DNS resolver, cgroup, privilege, filesystem, logging, package, or container-host behavior needs deeper operating-system benchmark support.
Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff needs command evidence patterns for resolver traces, privileged command risk, rollback, logs, process state, or host/container boundary proof.
Do not load references for ordinary application code that has no Linux-specific runtime dependency or for metadata-only documentation edits.
References are just-in-time support, not default-loaded encyclopedia content.

# Output Contract

Return a Linux Systems Usage Record with:

- `runtime_surface` (systemd, container host, process, filesystem, cgroup, namespace, package, network resolver, log sink)
- `environment_evidence` (distro, kernel, init, runtime, cgroup, user, filesystem, package manager)
- `service_contract` (unit settings, user/group, working directory, env files, restart/timeout, hardening, resource limits)
- `process_contract` (signals, child cleanup, PID files, sockets, readiness, graceful shutdown)
- `filesystem_permission_contract` (paths, ownership, umask, temp, mounts, secrets, rotation)
- `dns_resolution_trace` (`/etc/hosts`, `/etc/resolv.conf`, systemd-resolved, search domain, ndots, resolver command output)
- `privileged_command_risk_record` (sudo/root/capability/privileged-port need, least-privilege alternative, rollback)
- `resource_contract` (CPU, memory, fd, process, disk, inode, network limits and observed signals)
- `observability_contract` (journald/stdout/syslog, metrics, alerts, runbook commands)
- `decision_record` (chosen change, alternatives rejected, placement rationale)
- `validation_commands` (systemctl, journalctl, ps, ss, lsof, cat /proc, container inspect, tests, or not-run disclosure)
- `validation_freshness` (commands or validators rerun after the final material unit/package/runtime/path/permission/config edit; stale output rejected or named)
- `what_evidence_proves` and `what_evidence_does_not_prove` (covered host, runtime, service, container, resource, resolver, log, permission, and limits)
- `tool_permission_boundary` (read-only vs state-mutating command, sandbox, privilege, host mutation, network behavior, and rollback)
- `memory_graph_execution_record` (repository graph, project memory, old incident note, runbook, previous command output, or trajectory evidence accepted, rejected, stale, partial, or not used)
- `rollback_plan` (service config restore, package rollback, permission revert, resolver/config restore)
- `residual_risk` (unverified distro, container runtime, host policy, kernel, or production load)

# Evidence Contract

Close a Linux Systems Usage Record only when these answers are concrete: **boundaries inspected** across distro, kernel, init system, runtime, cgroup, user/group, filesystem, service manager, process tree, resolver, logs, privilege, package or rollout path, and rollback owner; direct source/config/command/log/probe evidence accepted or rejected; repository graph, project memory, old incident notes, runbooks, and execution trajectory used only as selectors unless rerun against current source or target runtime; validation evidence names command/test/validator/report/artifact, output summary, exit code or not-run status, and freshness after the final material edit; what evidence proves and does not prove for host, container runtime, kernel policy, cgroup pressure, DNS behavior, permissions, and production load; reuse and placement rationale for units, scripts, paths, limits, mounts, and hardening changes; behavior preservation, rollback or cleanup path, residual risk owner, and next gate.

# Quality Gate

1. Target Linux environment and container/host boundary are identified.
2. Service manager behavior is explicit: restart, timeout, user, group, working directory, environment, limits, and hardening.
3. Signal, shutdown, reload, and child cleanup behavior is defined and validated or disclosed.
4. File paths, ownership, permissions, temp files, sockets, and secret handling are safe.
5. DNS resolver behavior covers `/etc/hosts`, `/etc/resolv.conf`, systemd-resolved, search domains, and ndots when name resolution is in scope.
6. sudo/root boundary, privileged ports, Linux capabilities, SELinux/AppArmor, and seccomp assumptions are stated where relevant.
7. Resource limits and saturation signals are mapped to observability.
8. Logs reach the intended sink with redaction, logrotate or journald retention expectations, and disk-full behavior.
9. Rollout and rollback are safe for package/service changes.
10. Validation covers at least the changed unit, package, runtime, path, permission, resolver, or resource boundary with command output, exit code, report/artifact, or a not-run disclosure.
11. Tool permission boundary is explicit for state-mutating commands, privileged execution, host writes, cleanup, package actions, service restarts, and rollback.
12. Graph, memory, previous logs, old incident notes, and prior command output are freshness-checked and cannot substitute for current source/runtime evidence.
13. Residual risk names unverified host, kernel, runtime, security module, service manager, resolver, or production-load behavior.

# Used By

reliability-observability-gate, delivery-release-gate, security-privacy-gate, backend-change-builder, ai-code-review-refactor

# Handoff

Hand off to `low-level-systems-extension` for kernel/driver/native ABI work, `containerization` for image/runtime packaging, `shell-cli-professional-usage` for scripts, `secret-configuration-security` for secret files, and `delivery-release-gate` for production service rollout.

# Completion Criteria

Linux-system work is complete when the target runtime is identified, service/process/filesystem/resource behavior is explicit, commands or tests prove the critical path, privileges are minimized, logs and alerts are wired, and unverified host/runtime differences are owned.
