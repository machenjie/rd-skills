# Example Output

## Input Scenario

A containerized worker runs under systemd and is being OOM-killed after a deploy. The unit also fails to pass the expected environment file.

## Selected Capability

`linux-systems-professional-usage`

## Decision Record

- Runtime surface: systemd-managed container worker on Linux with cgroup v2.
- Environment evidence: unit file and container runtime limits inspected; service user is `worker`.
- Decision: declare `EnvironmentFile`, set `TimeoutStopSec`, align memory limit with worker budget, and add journald fields for OOM diagnosis.
- Rejected shortcut: raising host memory without cgroup evidence would not fix the container limit.

## Evidence Checklist

- systemd unit settings inspected.
- cgroup memory limit and OOM event path checked.
- Environment file path and permissions reviewed.
- Signal shutdown path covered.
- Logs mapped to journald query.

## Validation Commands

```
systemctl cat worker.service
systemctl show worker.service -p User -p EnvironmentFiles -p TimeoutStopUSec
journalctl -u worker.service --since "1 hour ago"
cat /sys/fs/cgroup/worker.slice/memory.max
```

## Residual Risk

Production traffic memory skew was not reproduced locally. Owner: SRE. Follow-up trigger: OOM metric or restart-loop alert after rollout.

## Handoff Summary

The failure was treated as cgroup/service configuration, not generic application memory. The fix requires release validation on the target host class.
