# Linux Systems Evidence Patterns

## Required Evidence

- Environment: distro, kernel, architecture, init, cgroup version, container/runtime, filesystem, and user.
- Service: unit file or supervisor config, restart policy, timeouts, env files, limits, and hardening.
- Process: PID tree, signal handling, child reaping, readiness, sockets, and fd limits.
- Filesystem: path ownership, permissions, mounts, temp directories, logs, and secrets.
- Observability: log sink, metrics, alert threshold, and runbook command.

## Tool Permission Boundary

Classify commands as read-only (`systemctl status`, `journalctl`, `ps`, `ss`, `lsof`, `cat /proc`, `stat`) or state-mutating (`systemctl restart`, package install/remove, sysctl write, chmod/chown, mount, kill`). State the sandbox and rollback for state-mutating commands.

## Handoff Shape

```
Linux Systems Usage Record
- Runtime surface:
- Environment evidence:
- Service/process contract:
- Filesystem/resource contract:
- Validation:
- Residual risk:
```

## Blocking Conditions

Block completion when a service runs as root without justification, shutdown behavior is unknown, resource limits are not mapped, secret files are broadly readable, or a package/service mutation lacks rollback.
