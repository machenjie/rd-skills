# Linux Systems Benchmarks And Patterns

## Benchmarks

- systemd service, unit, timer, socket activation, and sandboxing documentation.
- Linux man-pages for signals, procfs, capabilities, namespaces, cgroups, limits, sockets, and permissions.
- CIS Linux Benchmarks for host hardening.
- Container runtime guidance for PID 1, cgroups, capabilities, seccomp, and read-only filesystems.
- FHS path conventions for state, cache, config, logs, and runtime files.

## Pattern Matrix

| Surface | Required pattern | Evidence |
| --- | --- | --- |
| systemd service | user/group, restart, timeout, hardening | unit file and `systemctl show` |
| container shutdown | signal forwarding and child reaping | SIGTERM test or runtime config |
| cgroup limits | CPU/memory/fd/process budget | cgroup files or container inspect |
| permissions | least privilege and explicit ownership | `stat`, unit user, install script |
| logs | single intended sink and redaction | journald/stdout/syslog sample |
| package script | idempotent upgrade and rollback | install/remove dry run or test |

## systemd Review

Review `ExecStart`, `User`, `Group`, `WorkingDirectory`, `EnvironmentFile`, `Restart`, `RestartSec`, `StartLimitBurst`, `TimeoutStopSec`, `KillSignal`, `LimitNOFILE`, `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem`, `ReadWritePaths`, and logging settings.

## Container Host Review

Verify PID 1 behavior, cgroup version, memory and CPU limits, DNS resolver, mounted paths, writable directories, capabilities, seccomp/AppArmor/SELinux profile, and graceful stop timeout.
