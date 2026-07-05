# Example Output

## IoT Embedded Domain Findings
- Blocking: firmware rollout needs rollback and power-loss recovery behavior before field deployment.
- Connectivity requirement: cloud commands must expire and be idempotent so stale commands cannot execute after reconnect.
- Safety requirement: actuator defaults to fail-safe state on lost sensor input, watchdog reset, or authorization failure.

## Verification
- Hardware-in-the-loop update test with interrupted power and rollback.
- Protocol compatibility test across current and previous firmware.
- Fleet monitoring for update failures, command latency, telemetry gaps, resource pressure, and safety events.
