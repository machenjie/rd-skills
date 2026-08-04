# IoT Embedded Extension Checklist

- Model reachable device lifecycle across provisioning, activation, operation, degradation, update, rollback, reset, decommission, replacement, loss, and ownership transfer. Assign transition authority and reset or retirement outcomes for credentials, binding, protected state, retained data, and cloud authorization.
- Define offline buffering, retry identity and budget, duplicate or reordered delivery, command expiry, reconnect, cloud reconciliation, and behavior when connectivity-dependent recovery is unavailable.
- Define update compatibility, image validation, write and activation boundaries, staged exposure, rollback, and recovery. Bootloader and flash guarantees determine storage and activation controls.
- Track third-party firmware component and SBOM identity, vulnerabilities, and support lifecycle across fleet releases.
- Version protocol schema and command semantics; define required fields, ordering, duplicate behavior, authentication, deprecation, mixed-fleet compatibility, and recovery from partial or unsupported messages.
- Define trusted wall-clock sources, drift bounds, no-RTC startup semantics, resynchronization discontinuities, monotonic-time uses, expiry behavior, and event ordering across reboot and offline intervals.
- Derive CPU, memory, storage endurance, battery, bandwidth, thermal, and real-time budgets together with overload and exhaustion behavior from component limits and representative workloads.

Timing proof uses a defensible upper-bound method across reachable paths, interrupts, interference, locking, priority, and scheduling. Observed maxima are corroboration; unsupported conditions remain residual risk.
- For material physical impact, define safe state, emergency action, local override, notification, command rejection, reset behavior, and fault containment. Current hazard analysis supplies the governing evidence.
- Map device identity, attestation, firmware integrity, clone detection, command authority, credential rotation and revocation, tamper signals, and duplicate-identity outcomes across affected trust boundaries. The map includes attestation-loss recovery across device, edge, network, and cloud.
- For manufacturing and first boot, define identity issuance, binding, secret injection or derivation, trust-chain rotation, custody, and audit evidence. The lifecycle covers rework, duplicates, ownership transfer, and recovery from lost, expired, or invalid initial credentials.
- Choose disablement or authenticated authorization for production JTAG, UART, SWD, or comparable debug paths from serviceability and threat evidence. Production evidence covers configuration, re-enable authority, traceability, secret-exposure behavior, and supported revisions in scope.
- When older firmware violates security, data, safety, or compatibility, define trusted version authority and downgrade or recovery policy. Protected-state evidence covers monotonic counters or equivalent mechanisms under brownout, replacement, factory reset, and service recovery.
- When boot failure can strand a device or energize unsafe state, define boot-loop detection evidence, recovery authority, and a bootable, serviceable, or safe target. The recovery contract covers behavior when its image or required connectivity is unavailable.
- Use risk-selected simulator, HIL, degraded-network, power-loss, rollback, and fault-injection runs as sampled corroboration across representative hardware revisions rather than worst-case timing evidence.
- Monitor the selected fleet-health, firmware, boot-loop, credential, telemetry-lag, command, resource, update, connectivity, and safety signals; define bounded labels, alert ownership, and field-recovery action.
