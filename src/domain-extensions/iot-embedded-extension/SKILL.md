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

- Make field updates recoverable through validated images, atomic activation, last-known-good boot, power-loss behavior, mixed-fleet compatibility, rollback, and offline recovery.
- Authenticate firmware and commands against the device trust boundary, including integrity, origin, anti-rollback, credential rotation or revocation, and recovery from lost authority.
- Derive timing bounds from current hardware, scheduling, and interference evidence.
- Treat observed maxima as corroboration, not proof of worst-case timing.
- Derive physical safe states from current fleet and hazard evidence.
- Close triggered identity, endurance, protocol, connectivity, and resource risks through the checklist, with a named detection and field-recovery owner.

## High-Value Gotchas

- Power, connectivity, reset, wear, or reconnect behavior can defeat an otherwise valid update or safety mechanism.

## Execution Checklist

1. Name the triggered risk, invariant, owner, hardware/fleet scope, and recovery boundary.
2. Apply the checklist; report mechanism, evidence, proof limit, release consequence, and residual risk.

## Stop / Escalation Conditions

- Stop when a triggered physical, update, timing, resource, identity, or command-authority risk lacks its governing evidence or recovery guarantee.
- Escalate possible injury, fleet bricking, credential lockout, irreversible actuation, or unsupported hardware assumptions.

## Output Contract

- For every triggered device risk, state owner/scope, mechanism, compatibility/recovery, budget/safe state, validation, proof limit, detection owner, release consequence, and residual risk.
- Hand firmware, identity, attestation, production-debug, or command-authority changes to `threat-modeling`; include changed security graph, reachable abuse paths, control placement, bypass analysis, and detection evidence.
- Generic recovery evidence does not close security risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | device firmware provisioning connectivity update or safety behavior needs domain risk closure | the task is protocol documentation or a cloud API with no device or firmware behavior | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
