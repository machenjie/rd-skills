# IoT Embedded Extension Checklist

- Device lifecycle covers provisioned, activated, operating, degraded, updating, rolled back, decommissioned, replaced, and lost states.
- Connectivity behavior covers offline buffering, retry, duplicate delivery, command expiry, reconnect, and cloud sync.
- Firmware updates include staged rollout, compatibility matrix, rollback, power-loss handling, and bricking prevention.
- Protocol contracts include version, schema, required fields, ordering, idempotency, authentication, and deprecation plan.
- Time sync handles clock drift, monotonic time, event ordering, and delayed telemetry.
- Resource budgets cover CPU, memory, storage, battery, bandwidth, and real-time constraints.
- Physical safety covers fail-safe state, emergency stop, local override, operator notification, and unsafe command rejection.
- Security covers device identity, provisioning secrets, firmware integrity, command authorization, and tamper signals.
- Tests include simulator, hardware-in-the-loop, degraded network, power loss, and rollback validation where applicable.
- Monitoring covers fleet health, firmware version, telemetry lag, command failure, resource pressure, and safety events.
