# Payment Trading Extension Checklist

This checklist groups custody evidence with financial-state, execution, and reconciliation decisions.

## Custody Authority

- Classify the payment custody model.
- Identify the provider, exchange, custody, ledger, settlement, revocation, and finality roles that determine authority.
- Bind confirmation, entitlement, fulfillment, position, and balance changes to authoritative server-side events or state determined by those roles.

## Approved Raw-Card Custody Evidence

- Record current applicable PCI scope, accountable owner, proof gaps, and retention, storage, display, and logging evidence for approved raw-card custody.
- Use that record as control evidence without asserting certification.
- Prove approved raw-card custody retains no CVV or other sensitive authentication data after authorization unless current governing PCI requirements permit a documented issuing exception.
- Prove that control evidence protects stored PAN.
- Prove that control evidence masks displayed PAN.
- Cover logs, traces, errors, and ordinary artifacts in PAN discovery and control evidence.

## Non-Custodial Boundary

- Prove that non-custodial controls keep PAN, CVV, payment secrets, and equivalent sensitive values outside application storage.
- Prove that non-custodial controls keep those sensitive values outside ordinary artifacts.
- Prove that non-custodial controls keep those sensitive values out of logs, traces, and errors.
- Record tokenization or provider-boundary proof and named gaps for non-custodial flows.

## Financial State, Execution, and Reconciliation

- Select duplicate controls for each retryable financial effect from defined business uniqueness, retry, unknown-result, concurrent-submission, result-reuse, provider, venue, workflow, and persistence guarantees.
- Model owned payment and ledger transitions across authorization, capture, settlement, failure, cancellation, refund, dispute, reversal, expiry, adjustment, and reconciliation. The model names transition authority, stale-event behavior, and compensation limits.
- Model execution across acknowledgement, rejection, partial fill, fill, cancel, and cancel-replace. Race handling preserves executed quantity and prevents terminated quantity from reopening after fill-versus-cancel or replace-versus-late-report.
- Correlate client order or request identity with venue order, execution, fill, and correction identity. Reconciliation covers primary-session and drop-copy differences, duplicates, gaps, reordering, session resets, sequence restarts, and snapshot or authoritative-query recovery.
- Gate price-sensitive execution on market-data authority, freshness, sequence continuity, venue and instrument status, halt or auction state, and snapshot recovery. Derive fat-finger, price-collar, slippage, and unavailable-evidence behavior from current risk policy.
- Apply venue/product contracts for tick size, lot size, quantity and notional bounds, fee and funding semantics, price and quantity scale, precision, and rounding. The contract governs validation, execution, persistence, reporting, and reconciliation boundaries.
- Authenticate and attribute inbound provider or venue events under the current protocol. The contract covers replay identity, ordering or reorder behavior, version compatibility, credential ownership, and audit evidence without prescribing one signature scheme.
- Derive balancing, correction, reversal, and append-versus-update behavior from accounting ownership and storage guarantees. The result preserves financial history without imposing ledger semantics on pure orchestration.
- Define applicable available, pending, reserved, held, settled, negative, disputed, margin, and collateral balances. Their transition events and authoritative sources govern delayed or corrected execution.
- Make currency exponent, conversion, tax, settlement calendar, cutoff, time zone, clock source and skew, provider or exchange timestamp, and business-date rules explicit at ingestion, ordering, accounting, reporting, and reconciliation boundaries.
- Derive refund, adjustment, payout, trading override, self-trade prevention, pre-trade limit, and kill-switch authority from current risk policy. The policy governs stale input, fail-safe behavior, activation, recovery, user impact, and tamper evidence.
- For leveraged products, model collateral, maintenance margin, margin call, liquidation, insurance or loss allocation, and auto-deleveraging states. Authoritative risk inputs bind triggers and position priority; outcomes cover partial execution, halt, stale price, appeal, and reconciliation.
- Reconcile applicable orders, executions, fills, positions, balances, ledgers, statements, settlements, fees, funding, and corporate actions. Apply relevant lifecycle adjustments and define break classification, correction authority, replay windows, and unresolved-owner escalation.
- Monitor selected duplicate effects, report gaps, reordering, stale market data, price or limit rejection, kill-switch activation, and balance or position drift. The monitored set includes settlement breaks, failed reversals, and aged reconciliation exceptions; telemetry has bounded labels and sensitive fields.
