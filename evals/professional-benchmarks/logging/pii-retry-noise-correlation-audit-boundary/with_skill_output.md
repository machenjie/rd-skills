# Logging contract decision

Selected `logging-design-gate` with `logging-error-handling`, `observability`, and `secret-configuration-security`.

The design is blocked because raw webhook body exposes PII and credentials, intermediate retry errors create false incidents, missing correlation breaks causal reconstruction, per-item hot-path logging creates unbounded volume, and audit and diagnostic records need different integrity and retention.

Required proof is a field-classification and redaction negative test, a terminal-versus-intermediate retry logging test, correlation propagation across ingress queue and handler, a representative log volume and cardinality estimate, and an audit sink access retention and immutability check.

The accepted handoff must contain an approved logging field schema, an event severity and sampling policy, an audit boundary and diagnostic boundary, and a validation result and residual risk. Intermediate attempts should be summarized below incident severity, terminal outcomes should carry the shared correlation value, hot-path detail should be bounded or aggregated, and the audit stream should have its own minimal schema and control surface.
