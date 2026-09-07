# IoT Embedded Extension Checklist

Close triggered device and field-operation decisions.

## Lifecycle

- Prove update recovery through image validation, atomic activation, last-known-good boot, power-loss behavior, mixed-fleet compatibility, rollback, and offline recovery.
- Map provisioning, operation, update, reset, retirement, transfer, and loss to authority and credential, binding, protected-state, retained-data, and cloud outcomes.
- Define buffering, retry identity/budget, duplicates/reordering, command expiry, reconnect, reconciliation, and behavior without network recovery.
- Bind firmware/SBOM identity, vulnerabilities, support lifecycle, protocol/command versions, authentication, deprecation, and unsupported-message recovery to releases.
- Define clock trust, drift, no-RTC startup, resynchronization, monotonic time, expiry, and reboot/offline ordering.
- Derive compute, memory, endurance, power, bandwidth, thermal, and real-time budgets plus overload/exhaustion behavior from limits.

## Safety And Identity

- Treat timing evidence as a path bound across interrupts, interference, locking, priority, and scheduling, with observed maxima sampled and unsupported conditions residual.
- Bind physical-impact safe state, emergency action, local override, notification, command rejection, reset, and containment to hazard evidence.
- Map identity, attestation, integrity, clone detection, command authority, credential rotation and revocation, tamper, duplicates, and attestation-loss recovery across affected trust boundaries.
- Bind manufacturing identity, secret injection/derivation, custody, audit, rework, transfer, and invalid credential recovery to its trust chain.
- Select authorization or disablement for production debug from threat/service evidence, including re-enable authority, traceability, secret-exposure behavior, and supported revisions in scope.
- For unsafe old firmware, bind downgrade/recovery to trusted version authority and protected-state behavior under brownout, replacement, reset, and service.
- Stranding/unsafe-boot risk requires boot-loop detection evidence, recovery authority, a bootable, serviceable, or safe target, and behavior when its image or connectivity is unavailable.

## Evidence

- Use simulator, HIL, degraded-network, power-loss, rollback, and fault-injection runs as samples, not worst-case timing proof.
- Monitor fleet health, firmware, boot loops, credentials, telemetry lag, commands, resources, update, connectivity, and safety with bounded labels, alert ownership, and field-recovery action.
