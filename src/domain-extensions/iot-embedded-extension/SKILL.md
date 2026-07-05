---
name: iot-embedded-extension
description: "Use this domain extension when a selected professional skill handles professional product rules for device, firmware, edge, protocol, hardware interaction, embedded, and IoT changes involving lifecycle, connectivity loss, rollback, compatibility, time sync, resource limits, and physical safety. Do not use it for keyword-only, documentation-only, or UI-only mentions without domain behavior, data, risk, validation, or release impact."
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
metadata:
  changeforge.profile: full
  changeforge.skill_type: domain-extension
  changeforge.domain: iot-embedded
---

## Domain Scope
Extend ChangeForge product and code change analysis with embedded systems and IoT engineering discipline for constrained resource management, firmware update safety, protocol selection, physical safety boundary protection, hardware interaction correctness, and operational resilience in disconnected and hostile environments — ensuring that device changes cannot brick deployed hardware, introduce silent data corruption, or create physical safety hazards.

## Mission
Own the IoT/embedded domain addendum for a selected professional owner skill: device-risk signals, blocking hardware/firmware rules, validation addenda, and residual-risk ownership. Non-owned implementation, security, reliability, release, and test decisions remain with the primary owner or gate. Expected output is a domain decision addendum that prevents bricked fleets, unsafe actuator output, protocol incompatibility, and untestable field failures.

## When To Use
Use when a strong IoT/embedded signal can change a product, code, validation, release, or residual-risk decision. Treat strong signals as device behavior, firmware state, hardware interaction, fleet rollout, field diagnosis, or safety evidence, not as keywords. Skip keyword-only, docs-only, fixture-only, or UI-only mentions unless domain behavior, data, validation, release, or compliance posture can change.

## Strong Domain Signals
- Any change to firmware, bootloader, or low-level device driver code.
- OTA (Over-the-Air) update mechanism additions or modifications.
- Protocol changes: MQTT, CoAP, LWM2M, LoRaWAN, Zigbee, BLE, CAN bus, Modbus.
- RTOS task scheduling changes, interrupt service routine modifications, or bare-metal timing changes.
- Hardware abstraction layer (HAL) changes, GPIO configuration, SPI/I2C/UART driver changes.
- Power management changes: sleep modes, wake-up sources, battery life optimization.
- Edge computing logic changes: on-device inference, local data filtering, edge-to-cloud sync.
- Security changes: secure boot configuration, TLS mutual auth certificate rotation, device provisioning.
- Safety-critical control loop changes: motor control, actuator control, sensor fusion, failsafe logic.
- Fleet management changes: device provisioning, registration, decommissioning, remote configuration.

## Weak Signals That Are Not Enough

Do not load this extension only because a path, label, button, fixture, variable, title, or documentation paragraph contains a domain word. Do not load it for copy, styling, formatting, or generic refactors unless domain behavior, domain data, domain risk, validation, release evidence, or compliance posture can change.

## Do Not Use When
- The change is a pure cloud/backend change with no device firmware, protocol handler, or device management involvement.
- The change affects only the developer SDK or simulation environment with no physical device deployment.

## Required Professional Owner Skill

This extension must compose with one primary professional owner skill; it never replaces that owner or closes engineering work alone unless the user requested domain-only analysis.

- security-privacy-gate
- reliability-observability-gate
- quality-test-gate
- delivery-release-gate
- backend-change-builder

## Selection Rules
- If OTA, secure boot, watchdog, ISR, flash write, or safety output behavior can change, require a domain addendum before approval.
- When hardware-in-the-loop, power-loss, rollback, or fleet telemetry evidence is missing, treat domain approval as a blocking pass decision and route validation to `quality-test-gate`.
- When device identity, firmware signing, certificate rotation, or privileged device access changes, escalate to `security-privacy-gate` before implementation closure.
- Skip this extension when the primary owner confirms no device behavior, physical safety, protocol, rollout, or fleet-operational boundary can change.

## Tradeoff Priorities
- Physical safety before firmware convenience.
- Rollbackability before rollout speed.
- Hardware-enforced failsafe before software-only control.
- Field diagnosability before minimal telemetry.

## Domain-Specific Non-Negotiable Rules
- **OTA updates require A/B partition scheme with rollback**: a firmware update that cannot roll back to the previous known-good version can permanently brick a deployed device — A/B partition is non-negotiable for production OTA.
- **Firmware images must be cryptographically signed**: unsigned firmware allows an attacker or corrupted update server to push arbitrary code to physical devices — use secure boot chain with certificate pinning or hash verification.
- **Watchdog timer must be enabled and correctly stroked**: an embedded system without a hardware watchdog that silently enters a hung state requires physical intervention — watchdog must be configured to reset the device after a missed stroke interval.
- **Safety-critical failsafe must be hardware-enforced, not software-only**: software can fail silently (watchdog not stroked, interrupt missed, stack overflow) — physical safety outputs (emergency stop, valve close, actuator disable) must have hardware-level enforcement independent of application firmware.
- **Memory allocation in interrupt context is forbidden**: dynamic memory allocation (`malloc`/`new`) in an ISR can block indefinitely or cause heap corruption — use static allocation or pre-allocated pools for interrupt-safe operation.
- **TLS mutual authentication is required for cloud connectivity on security-critical devices**: a device that accepts a cloud connection without validating the server certificate is vulnerable to man-in-the-middle attacks — pin certificates; reject connections on validation failure.
- **Flash write endurance limits must be respected**: NAND flash has limited write cycles (typically 100K–1M per block) — logging directly to flash at high frequency will exhaust flash endurance in weeks; use RAM buffers, wear leveling, and batched writes.
- **Protocol selection must match device constraint profile**: a constrained device (< 64KB RAM, < 100kbps link) cannot sustain HTTPS/WebSocket — use CoAP over DTLS or MQTT over TLS with QoS 1; profile the memory and bandwidth footprint before selecting a protocol.

## Domain Risk Escalation

- Escalate to `security-privacy-gate` for custody, secrets, PII, permissions, abuse, prompt/security, device safety, or privileged access risk.
- Escalate to `data-api-contract-changer` for domain DTOs, events, schemas, SDKs, public APIs, or compatibility changes.
- Escalate to `reliability-observability-gate` for retries, replay, reconciliation, freshness, fallback, SLO, or incident visibility.
- Escalate to `delivery-release-gate` for rollout, rollback, migration, compliance evidence, irreversible production change, or operational readiness.
- Escalate to `quality-test-gate` when domain golden cases, regression proof, or validation evidence is missing.

## Domain Reference Loading Policy

Do not load all domain references by default. Load `references/checklist.md` only after a primary professional owner is selected and a strong domain signal proves the checklist can change a domain rule, validation requirement, release decision, or residual-risk addendum. Do not load domain references for keyword-only mentions, display-only copy, or unrelated refactors.

## Industry Benchmarks
- **MISRA C:2012 / MISRA C++:2008**: Motor Industry Software Reliability Association coding standards. Mandatory for safety-critical embedded C/C++ (automotive, medical, industrial). Prohibits undefined behavior, dynamic allocation in safety code, and unbounded loops.
- **CERT C Coding Standard (SEI)**: Secure C coding guidelines covering memory safety, integer overflow, format string vulnerabilities, and signal handling. Apply for all embedded C development.
- **IEC 62443 (Industrial Cybersecurity)**: Security levels (SL0–SL4) for industrial control systems. SL2 (protection against intentional violation using simple means) is the baseline for connected industrial IoT.
- **NIST SP 800-213 (IoT Cybersecurity)**: Federal baseline for IoT device cybersecurity. Device identity, software update authentication, secure communication, and logical access control.
- **MQTT 5.0 Specification (OASIS)**: Quality of Service levels (0=at most once, 1=at least once, 2=exactly once), retained messages, will messages for disconnect notification, session persistence. Choose QoS level explicitly based on payload criticality.
- **FOTA (Firmware OTA) Best Practices (AWS IoT / Azure IoT Hub)**: Staged rollout (1% → 10% → 100%), pre-update health check, post-update validation, automatic rollback on health check failure, update version tracking.
- **ARM TrustZone / Secure Enclave**: Hardware-enforced security boundary between trusted (TEE) and untrusted (REE) execution environments. Use for key storage, secure boot, and cryptographic operations on supported MCUs.
- **RTOS Design Patterns (FreeRTOS, Zephyr)**: Task priority inversion (use priority inheritance mutex), stack overflow detection (RTOS stack watermark), semaphore for resource protection, event group for multi-task synchronization.

### Protocol Selection Matrix

| Device Constraint | Connectivity | Recommended Protocol | Reason |
|---|---|---|---|
| < 64KB RAM, intermittent cellular | Low-bandwidth, high-latency | MQTT over TLS (QoS 1) | Binary, low overhead, broker handles reliability |
| Ultra-constrained (< 10KB RAM) | UDP/IP | CoAP over DTLS | UDP-based, request/response, < 4-byte header |
| Long-range, low-power (battery) | LoRaWAN | LoRaWAN Class A/C | < 50 bytes/message, sub-GHz, km range |
| Industrial sensor network | RS-485 mesh | Modbus RTU | Simple, proven, deterministic timing |
| Short-range consumer device | Bluetooth 5.x | BLE GATT | Low energy, 2.4GHz, standard profile ecosystem |
| Safety-critical real-time bus | CAN bus | CANopen / SAE J1939 | Deterministic, fault-tolerant, automotive-grade |

## Domain Risk Model
- **OTA update bricks device fleet**: a firmware update without A/B partition has a bug causing boot loop — all deployed devices are permanently bricked; requires physical recall or on-site service.
- **Unsigned firmware accepted**: an attacker compromises the OTA server or performs a MITM attack — arbitrary firmware is pushed to the device; the attacker gains complete device control.
- **Watchdog not stroked causes hung device**: a software deadlock causes the main loop to stall — without a watchdog, the device stays in a hung state indefinitely; the user experiences the device as unresponsive.
- **Safety output controlled purely in software**: a fire suppression valve is controlled by an application-layer command — a stack overflow or firmware crash leaves the valve in the wrong state; physical damage or injury results.
- **Flash endurance exhausted by frequent logging**: debug logging writes to flash 1000 times per second — a 100K-cycle flash block is exhausted in 27 hours; the device starts experiencing write failures.
- **TLS certificate expired on device fleet**: device certificates expire simultaneously on a fleet of 10,000 devices; devices cannot connect to cloud; mass outage requires physical or manual certificate rotation.
- **Integer overflow in sensor calculation**: a temperature sensor returns a value larger than the type's maximum — an unchecked cast wraps the value to negative; a heating control loop incorrectly reduces heat instead of triggering a safety cut-off.
- **Stack overflow in ISR corrupts heap**: an ISR function allocates on the stack beyond the configured stack size — it silently corrupts adjacent memory; the device behaves erratically until a restart.

## Linked Foundation Capabilities
- threat-modeling
- authentication-security
- test-strategy
- regression-testing
- observability
- logging-error-handling
- backup-recovery
- error-code-design
- concurrency-control
- performance-budgeting

## Critical Details
- **Stack size analysis is mandatory for RTOS tasks**: each RTOS task has a fixed stack; use the RTOS stack watermark API (FreeRTOS `uxTaskGetStackHighWaterMark`) to measure stack usage under load — at least 20% headroom is required.
- **Floating-point operations are forbidden on cores without FPU**: on Cortex-M0/M0+ without a hardware FPU, soft-float library calls are expensive (100s of cycles) and may introduce timing violations in real-time tasks — use fixed-point arithmetic instead.
- **Time synchronization is critical for distributed sensor networks**: events from multiple devices without synchronized clocks cannot be correlated — use NTP, PTP (IEEE 1588), or GPS-synchronized timestamps; log clock drift.
- **Power brownout during flash write corrupts firmware**: a partial flash write during a power interruption produces a corrupted firmware image — use a double-buffered write with validation hash; never overwrite the current running image until the new image is verified.
- **OTA delta updates reduce bandwidth cost**: a full firmware image may be 512KB — for a cellular-connected device, full OTA costs bandwidth budget; use binary diff (bsdiff, janpatch) to generate delta patches of < 10KB.
- **Device identity provisioning at manufacturing time**: device certificates and keys injected post-manufacturing are less secure than keys injected at a Hardware Security Module (HSM) during manufacturing — define the provisioning flow before the device ships.

### Anti-Examples

| IoT/Embedded Pattern | Problem | Corrected Approach |
|---|---|---|
| Single firmware partition OTA | Update failure bricks device | A/B partition: write new image to inactive partition, validate, swap |
| No watchdog timer | Software hang requires physical reset | Hardware watchdog with 5s interval; stroked in main loop; independent of application logic |
| `malloc()` inside ISR | Heap corruption, blocking behavior | Pre-allocate buffer pool at boot; use pointer from pool in ISR |
| Flash write in tight loop (100 Hz) | Flash endurance exhausted in hours | Buffer in RAM; batch write at 1 Hz or on significant change threshold |
| Safety output state managed in app memory | App crash leaves output in dangerous state | Hardware relay with fail-safe default (spring-return to safe state) |

## Failure Modes
Report each failure mode with condition, consequence, detection, prevention or repair, and evidence; narrative risk alone is not enough for domain closure.

- **Bricked device fleet from failed OTA**: firmware update pushed without A/B partition or validation — all 50,000 devices boot-loop; physical field service required at $500/device; $25M remediation cost.
- **Man-in-the-middle firmware injection**: OTA server is compromised; unsigned firmware accepted — attacker pushes malicious firmware that exfiltrates sensor data or manipulates actuators.
- **Safety actuator stuck in active state after crash**: application firmware crash leaves a valve in open state; hardware failsafe not implemented; physical damage results.
- **Certificate rotation causes mass device disconnect**: fleet certificates expire; devices cannot verify server TLS; all devices go offline simultaneously; no automated certificate rotation was implemented.
- **Flash endurance failure causes data corruption**: high-frequency logging to flash exhausts write cycles in a production deployment — flash starts returning write errors; logged data is lost; device eventually fails to boot.
- **Integer overflow in control loop causes unsafe output**: sensor value exceeds variable range; wraps to negative; PID controller drives actuator in the wrong direction; physical damage or injury results.

## Domain Output Addendum
Return IoT/embedded change assessment with:
- **Selected mode and professional decision**: selected owner skill, domain addendum mode, approved/blocked/not-verified decision, and the device behavior under review.
- **Inspected boundaries**: firmware, boot, protocol, control-loop, power-loss, hardware, cloud/fleet, and release boundaries read or explicitly skipped.
- **Evidence collected / validation status**: hardware-in-the-loop tests, rollback rehearsal, resource measurements, and telemetry checks with current pass/fail/not-run status.
- **Evidence limits, residual risk, and next gate**: untested device classes, field rollout limits, owner, next gate, and rollback threshold.
- **OTA update safety**: A/B partition confirmation, firmware signing verification, staged rollout plan, rollback procedure.
- **Safety-critical analysis**: failsafe logic review, hardware enforcement confirmation, watchdog configuration.
- **Protocol selection justification**: memory and bandwidth footprint, QoS level selection, connection resilience.
- **Resource constraint analysis**: stack sizing, flash write frequency, RAM allocation, power budget.
- **Security review**: device identity, TLS certificate management, secure boot chain, credential storage.
- **Observability plan**: device health telemetry, connectivity status, firmware version tracking, error rate.
- **Fleet impact**: staged rollout percentage, health check criteria, automatic rollback thresholds.
- **Block/pass decision** with required conditions for approval.

## Evidence Contract
Close an IoT/embedded change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`), because the loss path is bricked fleets and physical safety:
- **Basis**: the OTA safety rule, resource-limit budget, or safety-critical failsafe the change rests on.
- **Files and boundaries inspected**: the firmware update path, control loop, and protocol layer read, with the secure-boot chain and the power-loss/recovery boundary confirmed.
- **Placement rationale**: why the A/B partition, watchdog, and failsafe logic live where they do, and that no integer-overflow or resource exhaustion can drive an unsafe actuator output.
- **Validation commands**: the OTA rollback rehearsal, power-loss recovery test, resource-budget measurement, and clock-sync check run, each with its outcome.
- **Residual risk**: the connectivity-loss, protocol-compatibility, field-diagnosis, or hardware-fault path that remains, with the named owner and the staged-rollout rollback threshold.
- **What evidence proves**: only the tested firmware image, device class, protocol path, rollback path, and telemetry boundary meet the stated gate.
- **What evidence does not prove**: untested hardware revisions, field network conditions, manufacturing variance, future certificate rotation, or unmeasured physical faults.
- **Behavior preservation**: existing boot, rollback, protocol compatibility, field diagnostics, and safety defaults are preserved or explicitly changed.
- **Next gate**: unresolved firmware signing, fleet rollout, hardware-in-the-loop, safety, or telemetry gaps route to the named owner before release.

## Domain Quality Gate
1. OTA update uses A/B partition scheme with validated rollback procedure tested on hardware.
2. Firmware images are cryptographically signed and verified during boot (secure boot chain).
3. Watchdog timer is enabled, correctly stroked, and tested to reset the device on failure.
4. Safety-critical outputs have hardware-enforced failsafe independent of application firmware.
5. No dynamic memory allocation in interrupt service routines.
6. TLS mutual authentication is configured with certificate validation and pinning.
7. Flash write frequency is within endurance limits; batched write strategy is implemented.
8. Stack size for all RTOS tasks is measured under load with ≥ 20% headroom.
9. Protocol selection is profiled for device memory and bandwidth constraints.
10. Fleet rollout uses staged percentage with automatic rollback on health check failure.

## Handoff
Return this domain addendum to the primary professional owner; do not approve IoT/embedded work from this extension alone. Hand off security blockers to `security-privacy-gate`, release blockers to `delivery-release-gate`, reliability blockers to `reliability-observability-gate`, and missing hardware validation to `quality-test-gate` with the residual-risk owner and next evidence gate.

## Return / Escalate
- **security-privacy-gate** — for device identity, firmware signing, TLS cert management, and MITM attack surface.
- **reliability-observability-gate** — for device health SLI, connectivity uptime, firmware version SLO, and error rate alerting.
- **quality-test-gate** — for hardware-in-the-loop test requirements, OTA rollback test, and safety test obligations.
- **delivery-release-gate** — for staged OTA rollout configuration and fleet rollout monitoring.
- **backend-change-builder** — for device management API, device shadow/twin, and cloud telemetry ingestion.

## Completion Criteria
The IoT/embedded change is approved when OTA uses A/B partition with tested rollback, firmware is signed with verified secure boot, watchdog is configured, safety outputs have hardware-enforced failsafe, no dynamic allocation in ISRs, TLS mutual auth is configured, flash write frequency is within endurance limits, RTOS stack sizes are validated, and fleet rollout uses staged deployment with automatic rollback.
