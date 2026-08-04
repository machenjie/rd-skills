---
name: linux-systems-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when Linux processes, signals, files, permissions, cgroups, namespaces, kernel, or host runtime changes; skip non-Linux work."
---

# linux-systems-professional-usage

## Registry Trigger

**Use when**

- Linux systemd systemd-resolved journald cgroup namespace procfs sysfs signal handling daemon pid file PID 1 ulimit file descriptor socket permission sudo root capability seccomp service restart
- distro kernel init container runtime cgroup v2 unit file EnvironmentFile TimeoutStopSec User Group WorkingDirectory OOM fd exhaustion resolver /etc/hosts /etc/resolv.conf search domain ndots mount tmpfs logrotate privileged port SELinux AppArmor

**Do not use when**

- no task-local linux systems professional usage decision is required

## Skill Role

Verify Linux runtime behavior against the actual process, supervisor, permission, filesystem, cgroup, namespace, container, and host boundary.

## High-Value Rules

- Inspect the target distribution, kernel, init or supervisor, runtime, architecture, filesystem, user, cgroup, namespace, and package boundary only where they can change the decision.
- For supervised services, define only affected identity, working state, configuration, restart/stop behavior, resources, hardening, and log destination from current policy.
- When termination, reload, or child processes are affected, define signal ownership, cleanup, drain, escalation, and observable completion from the caller and supervisor contracts.
- Validate path, ownership, permission, umask, temporary-file, socket, and lock behavior where concurrent start, restart, or multiple users can change safety.
- Distinguish host from container evidence for process identity, cgroups, DNS, mounts, capabilities, security policy, and persistence; reject an environment diagnosis without representative command evidence.
- Derive CPU, memory, descriptor, process, disk, inode, and network limits from observed load, failure consequence, and current budget, then verify the relevant exhaustion path.
- Select logging and privilege controls from the deployed sink and required behavior; minimize authority without breaking the proven runtime contract.

## Anti-Patterns

- A container entry process that does not forward signals or reap children can hang shutdown and leak processes.
- Supervisor restart can hide a crash loop unless readiness, backoff, and failure evidence remain visible.
- Overlay, network, temporary, labeled, or read-only filesystems can invalidate local path and lock assumptions.
- Resolver, cgroup, and security-module behavior differs across hosts; application code alone cannot prove it.

## Stop Conditions

Escalate privilege, secret, public-socket, or security-module changes; restart, saturation, or shutdown risk; package, kernel, or host rollout; and kernel/driver/ABI/native-memory/syscall work to their specialist owners.

## Output Contract

- Return a Linux Systems Record: runtime/environment evidence; service, process, filesystem, permission, resource, and observability contracts; decisions, validation, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | service supervision sandboxing path or container mechanisms remain undecided | target platform policy selects one supported Linux mechanism | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects process signals filesystem privileges resources or service lifecycle | no Linux runtime or host boundary changes | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | environment service permission or resource claims need representative proof | current target artifacts and commands prove each affected claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
