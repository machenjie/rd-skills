# Trading Order Execution and Identity

Use this Reference only for the named order-execution and identity decision.

## Decision Rules

- Model execution across acknowledgement, rejection, partial fill, fill, cancel, and cancel-replace. Race handling preserves executed quantity and prevents terminated quantity from reopening after fill-versus-cancel or replace-versus-late-report.
- Correlate client order or request identity with venue order, execution, fill, and correction identity. Reconciliation covers primary-session and drop-copy differences, duplicates, gaps, reordering, session resets, sequence restarts, and snapshot or authoritative-query recovery.
