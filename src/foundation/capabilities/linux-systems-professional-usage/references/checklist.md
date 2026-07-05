# Linux Systems Professional Usage Checklist

- Identify the runtime surface: distro, kernel, init system, architecture, package manager, container runtime, cgroup version, namespace boundary, user/group, filesystem, and host policy.
- Record the service contract: unit or supervisor, `User`, `Group`, `WorkingDirectory`, `EnvironmentFile`, `Restart`, `TimeoutStopSec`, `KillSignal`, `Limit*`, hardening options, and log sink.
- Record the process contract: PID 1 behavior, signals, child reaping, pid/socket files, readiness, graceful shutdown, reload behavior, and timeout escalation.
- Record filesystem and permission behavior: paths, ownership, modes, umask, temp directories, mounts, sockets, secrets, log files, rotation, retention, and disk-full behavior.
- Record resource behavior: CPU, memory, file descriptors, process/thread count, disk, inode, network, cgroup limits, saturation signals, and alert/runbook coverage.
- Trace resolver behavior when in scope: `/etc/hosts`, `/etc/resolv.conf`, systemd-resolved, search domains, `ndots`, split DNS, and resolver command output.
- Review privilege and security boundaries: sudo/root, capabilities, seccomp, SELinux/AppArmor, privileged ports, setuid/setgid, public sockets, writable directories, and least-privilege alternatives.
- Classify commands as read-only inspection, state-mutating service action, package action, host configuration change, cleanup/delete, privileged command, or rollback command before execution.
- Validate with the smallest command, test, log slice, or artifact that can fail for the changed Linux runtime boundary, then state what it proves and does not prove.
- Treat repository graph, project memory, old incident notes, previous command output, and runbooks as selectors only until current source, config, host, or representative runtime evidence confirms them.
