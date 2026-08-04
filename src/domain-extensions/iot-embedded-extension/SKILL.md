---
name: iot-embedded-extension
description: "For analysis/task/review agents using a Professional Skill on devices, firmware, edge protocols, updates, or safety; not for work without device, firmware, or physical impact."
---

# iot-embedded-extension

## Role

Invoke this focused Layer 3 Domain Skill for device and field-operation
decisions. Give `analysis-agent`, `task-agent`, and `review-agent` device-timing,
update, identity, recovery, and physical-safety constraints for firmware and
field operations.

## When To Use

- device, firmware, edge protocol, sensor, actuator, constrained runtime, or field update behavior

## Do Not Use

- cloud or desktop work with no device, firmware, or physical-world impact
- protocol documentation or cloud-only APIs without device or firmware behavior

## Required Inputs

- hardware capability, boot and update path, timing, power, protocol, and field-service boundary
- hazard analysis, trust boundary, fleet diversity, recovery options, and representative evidence

## Professional Decision Rules

- **Make updates recoverable**: prove atomic activation, last-known-good boot, power-loss behavior, compatibility, fleet rollback, and offline field recovery.
- **Authenticate firmware**: bind integrity, origin, anti-rollback policy, and signing-key rotation to the update trust boundary and device capability.
- **Bound hang recovery**: detect failure and enter a known state without creating unsafe reset or boot-loop behavior.
- **Contain hazardous actuation**: derive safe state and fault independence from the current hazard analysis and safety case.
- **Bound timing-sensitive work**: compare measured deadlines with a defensible upper bound covering reachable paths, execution, allocation, locking, interrupts, cache or bus interference, and scheduling.
- **State timing proof limits**: classify observed maxima as corroboration and disclose upper-bound assumptions, unsupported conditions, and residual deadline risk.
- **Protect fleet identity**: prove peer and device authentication, confidentiality, credential rotation, expiry recovery, revocation, and service-tool authority.
- **Measure endurance and protocol behavior**: derive write lifetime, memory, bandwidth, power, buffering, and reconnect behavior from representative devices and workloads.

## High-Value Gotchas

- power loss between image write and activation leaves no bootable version
- fleet credential expiry requires unavailable connectivity for recovery
- reset recovery re-energizes an unsafe actuator
- debug writes exhaust flash before expected service life
- reconnect storms overload devices and cloud endpoints

## Execution Checklist

1. Identify each triggered device risk, its governing invariant and owner, affected hardware and fleet scope, and recovery boundary.
2. Select controls from the update or identity trust boundary, hardware, hazard evidence, fleet operations, and bounded resource use.
3. Prove fault, power-loss, mixed-fleet compatibility, rollback, timing and resource budgets, and safe-state behavior with evidence matched to each obligation.
4. Name proof limits, detection and field-recovery ownership, release consequence, and residual risk.

## Stop / Escalation Conditions

- Stop when a triggered physical-safety risk lacks its hazard analysis, or a triggered update or boot risk lacks its boot, recovery, compatibility, or field-rollback guarantee.
- Stop when a triggered timing or resource risk lacks its hardware limit or defensible timing upper-bound method.
- Stop when a triggered firmware, identity, attestation, production-debug, or command-authority risk lacks its identity or update trust boundary.
- Escalate possible injury, fleet bricking, credential lockout, irreversible actuation, or unsupported hardware assumptions.

## Output Contract

- For every triggered device risk, state the governing invariant and owner, affected hardware and fleet scope, and selected mechanism or trust boundary.
- For that risk, report compatibility and rollback behavior, timing or resource budget, safe-state behavior, validation artifact and proof limit, monitoring or detection owner, release consequence, and residual risk.
- Hand firmware, identity, attestation, production-debug, or command-authority changes to `threat-modeling`; include changed security graph, reachable abuse paths, control placement, bypass analysis, and detection evidence.
- Generic recovery evidence does not close security risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | device firmware provisioning connectivity update or safety behavior needs domain risk closure | the task is protocol documentation or a cloud API with no device or firmware behavior | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
