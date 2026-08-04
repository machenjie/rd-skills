# OTA Release Review

Primary Professional Skill: `delivery-release-gate`  
Selected Domain Skill: `iot-embedded-extension`

## Hidden risks

- brownout during image activation can leave no bootable slot
- automatic rollback can loop forever when credential recovery requires network access
- expired device credentials can make fallback recovery unreachable

## Required evidence

- power-cut fault injection across write activation and first boot
- boot-attempt and last-known-good recovery trace
- offline credential-loss recovery exercise on representative hardware

## Handoff

- go or no-go rollout verdict
- boot rollback and credential recovery state machine
- fleet stop signals proof limits and residual owner

Verdict: no-go until activation is power-loss safe, health confirmation is durable, boot attempts terminate in a known recoverable state, credential repair has a field-usable path, and cohort-level pause and rollback authority are named.
