---
name: payment-trading-extension
description: Adds professional product rules for payments, subscriptions, billing, invoices, refunds, trading, ledgers, balances, and financial workflows requiring idempotency, auditability, reconciliation, state modeling, and server-side truth.
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
---

## Mission
Extend ChangeForge product and code change analysis with financial engineering discipline for payment correctness, ledger consistency, regulatory compliance (PCI DSS, AML/KYC), idempotency guarantees, reconciliation integrity, double-entry accounting invariants, and trading system reliability — ensuring that financial changes cannot produce double charges, silent ledger drift, unauthorized access to payment instruments, or regulatory exposure.

## Trigger Signals
- Any change to payment processing flows: checkout, card capture, 3D Secure, payment intent creation.
- Subscription or billing engine changes: plan activation, renewal, proration, cancellation, entitlement grants.
- Refund, chargeback, or reversal handling.
- Ledger entry creation, balance adjustment, or financial statement aggregation.
- Trading or order management: order creation, execution, settlement, position calculation, risk limit enforcement.
- Webhook handling for payment provider events (Stripe, Braintree, Adyen, PayPal).
- KYC/AML compliance flow changes: identity verification, sanctions screening, transaction monitoring.
- Reconciliation reports or financial audit trail generation.
- Tax calculation, invoice generation, or currency conversion logic.
- Payout, disbursement, or withdrawal processing.

## Do Not Use When
- The change is display-only: pricing copy, plan comparison UI, or invoice PDF formatting with no ledger, state machine, or payment API involvement.
- The change is a non-financial account settings update with no billing, entitlement, or payment instrument impact.

## Non-Negotiable Rules
- **Server-side confirmation is the only authoritative payment signal**: a frontend `success` callback or client-side redirect is not a payment confirmation — server must receive provider webhook or API confirmation before granting entitlement, updating ledger, or fulfilling an order.
- **Every payment-mutating operation must use an idempotency key**: payment provider retry without an idempotency key causes duplicate charges — Stripe idempotency keys, Braintree unique transaction tokens, and internal idempotency keys for internal ledger mutations are mandatory.
- **Raw card data (PAN, CVV) must never touch application servers**: PCI DSS Requirement 3 prohibits storing CVV after authorization; PAN storage requires PCI Level 1 audit — use tokenization exclusively (Stripe Elements, Braintree Drop-In); application servers must never log, store, or transmit raw card data.
- **Financial state machines must be explicit and exhaustive**: a payment that can be in states `pending`, `authorized`, `captured`, `settled`, `refunded`, `disputed`, `failed` must have all valid state transitions documented and enforced — invalid state transitions (e.g., refund of a failed payment) must be rejected with a meaningful error.
- **Ledger entries are immutable after creation**: do not UPDATE ledger records — ledger corrections are new offsetting entries (debit to correct a credit error); this maintains a complete audit trail with no gaps.
- **Double-entry bookkeeping invariant**: for every credit entry, there must be a corresponding debit entry in the same amount — the sum of all debits must equal the sum of all credits at all times; reconciliation validates this invariant.
- **Webhook signatures must be verified before processing**: a payment provider webhook without HMAC-SHA256 signature verification is an unauthenticated POST endpoint that can be called by any attacker to forge payment events.
- **Financial arithmetic must use fixed-point or decimal arithmetic, never floating-point**: `0.1 + 0.2 === 0.30000000000000004` in IEEE 754 floating-point — use `Decimal`, `BigDecimal`, or integer arithmetic in the smallest currency unit (cents, paise) for all financial calculations.

## Industry Benchmarks
- **PCI DSS v4.0 (Payment Card Industry Data Security Standard)**: 12 requirements covering network security, cardholder data protection, access control, monitoring, and testing. Level 1 compliance required for merchants processing > 6M transactions/year. SAQ-A eligibility requires complete offload of card data processing to a PCI-certified provider.
- **3D Secure 2.0 (EMV 3DS)**: Frictionless and challenge flows, device fingerprinting, issuer authentication. Reduces chargeback liability shift to issuer. Required for EU Strong Customer Authentication (SCA) under PSD2.
- **Double-Entry Bookkeeping (Pacioli, 1494 — foundational accounting)**: Every transaction has equal debits and credits. The accounting invariant that prevents ledger drift. Implement at the data model level, not just the application logic level.
- **Stripe Idempotency Keys (Stripe API Design Guide)**: Idempotency keys are stored for 24 hours; retrying with the same key returns the original response without re-executing. Pattern required for all payment-mutating API calls.
- **Reconciliation Best Practices (Stripe, Adyen documentation)**: Daily settlement reconciliation; match internal ledger entries against provider settlement reports; automated alerting on reconciliation gaps above threshold.
- **High-Frequency Trading Latency Requirements**: Co-location strategies, kernel bypass networking (DPDK, RDMA), order management system (OMS) latency < 10µs, FIX protocol message handling. Apply for trading system changes.
- **AML/KYC Regulatory Requirements (FATF recommendations, FinCEN)**: Customer Due Diligence (CDD), Suspicious Activity Report (SAR) filing thresholds, transaction monitoring, sanctions list screening (OFAC SDN list). Required for money transmission licenses.
- **FCA / SEC Reporting Obligations**: Trade reporting to regulatory bodies (EMIR, MiFID II, Dodd-Frank), position limits, margin requirements. Apply for regulated trading platform changes.

### Payment Operation Idempotency Requirements

| Operation | Idempotency Mechanism | Duplicate Handling |
|---|---|---|
| Create payment intent | Provider idempotency key (UUID) | Return existing intent if key exists |
| Capture authorized payment | Internal capture idempotency key | Return existing capture result |
| Create refund | Idempotency key per refund request | Block duplicate refunds for same charge |
| Webhook processing | Store processed event ID; skip duplicates | Deduplicate by provider event ID before state mutation |
| Ledger credit entry | Unique entry ID; upsert with conflict-do-nothing | Never create duplicate ledger entries |
| Subscription renewal | Renewal idempotency key per period | One renewal per billing period |

## Domain Risk Model
- **Double charge from retry without idempotency key**: a network timeout causes the payment service to retry a charge creation without an idempotency key — two charges are created; the user is billed twice.
- **Entitlement granted before provider confirmation**: a frontend success callback triggers entitlement grant before the webhook confirms payment capture — the user gains access; the capture fails; revenue is lost.
- **Ledger drift from mutable entries**: a bug allows ledger entries to be updated in-place — the audit trail is destroyed; the balance calculation is wrong; reconciliation fails; regulatory reporting is inaccurate.
- **Double-entry violation causes balance corruption**: a refund is created as a single debit entry without the corresponding credit — the account balance is incorrect; the accounting invariant is violated.
- **Floating-point currency arithmetic causes rounding errors**: `$1.005 * 2 = 2.01` in floating-point but `2.0099999...` — cumulative rounding errors across thousands of transactions create reconciliation gaps.
- **Webhook replay attack forges payment events**: an attacker captures a legitimate webhook payload and replays it — without signature verification and idempotency, the payment event is processed twice.
- **Refund issued for fraudulent chargeback creates net loss**: a chargeback is filed after a refund is already issued — the merchant loses both the original transaction amount and the chargeback fee (double loss).
- **Raw PAN logged during debugging**: a developer adds a debug log statement that includes the payment method object — raw card numbers appear in application logs; PCI DSS Requirement 3.3 violation; mandatory breach notification.

## Linked Foundation Capabilities
- idempotency-retry-design
- state-machine-modeling
- transaction-consistency
- domain-event-modeling
- permission-boundary-modeling
- authentication-authorization
- data-model-design
- logging-error-handling
- observability
- contract-testing

## Linked Professional Skills
- backend-change-builder
- data-api-contract-changer
- integration-change-builder
- data-middleware-change-builder
- security-privacy-gate
- reliability-observability-gate
- quality-test-gate
- change-documentation-gate

## Critical Details
- **Payment state machine testing requires all invalid transition tests**: it is not enough to test the happy path — a refund attempted from `failed` state, a capture attempted from `refunded` state, and a double-capture must all return the correct error response.
- **Settlement timing and cut-off times are business-critical**: payment processors settle on T+1 or T+2 depending on card type; cut-off times vary (e.g., Stripe settles transactions captured before midnight UTC) — financial reports that ignore settlement timing produce incorrect revenue recognition.
- **Proration logic is complex and error-prone**: upgrading/downgrading a subscription mid-cycle requires calculating the pro-rata credit and the new charge correctly — test with mid-cycle upgrades, downgrades, cancellations, and grace period edge cases.
- **High-frequency trading position calculations must be lock-free or use serialized order books**: a trading system that calculates position under concurrent order execution without proper synchronization produces incorrect position values; risk limits based on incorrect positions allow limit violations.
- **Currency conversion must use a snapshot exchange rate, not a live rate**: financial reports that apply different exchange rates to the same historical transaction each time they are run produce different results — store the exchange rate at transaction time as an immutable record.
- **Soft delete is insufficient for financial records**: `deleted_at` timestamps on payment records hide them from queries but they still exist — use immutable audit log patterns; financial records must be retained per jurisdiction (typically 7 years).

### Anti-Examples

| Financial Pattern | Problem | Corrected Approach |
|---|---|---|
| Grant entitlement on frontend `paymentSuccess` callback | Frontend success ≠ capture confirmed; entitlement without payment | Grant only after server receives `payment_intent.succeeded` webhook with signature verification |
| `balance = balance + amount` (UPDATE ledger row) | Mutable ledger destroys audit trail | Insert new ledger entry (immutable); calculate balance as `SUM(credits) - SUM(debits)` |
| `0.1 + 0.2 === 0.3` for financial comparison | IEEE 754 floating-point imprecision | Use integer arithmetic in cents: `10 + 20 === 30` (cents) |
| Create Stripe charge without idempotency key | Network retry creates duplicate charge | `stripe.charges.create({...}, {idempotencyKey: uuid})` |
| Accept webhook without signature verification | Attacker forges payment events | Verify `Stripe-Signature` header with `stripe.webhooks.constructEvent()` |

## Failure Modes
- **Double charge on retry**: payment API called twice due to network timeout without idempotency key — user charged twice; chargeback risk; customer support escalation.
- **False entitlement from frontend success**: payment fails after frontend redirect; entitlement was already granted; subscription activated for non-paying user.
- **Ledger drift discovered in audit**: UPDATE-based ledger allows balance to be corrected without creating an offsetting entry; annual audit discovers a $50K balance discrepancy with no audit trail.
- **Floating-point rounding gap**: 50K invoices each with a $0.001 rounding error accumulate to a $50 discrepancy; reconciliation report flags a gap; investigation takes 3 days.
- **PAN in application log**: debug statement logs payment method JSON including raw card number; PCI breach notification required; regulatory fine; card network audit.
- **Refund + chargeback double loss**: customer disputes a charge after a refund was issued; merchant loses $150 (original transaction) + $15 (chargeback fee) + $150 (refund already issued) = $315 total.

## Output Contract
Return financial change assessment with:
- **Payment state machine**: all states, valid transitions, and invalid transitions with error responses.
- **Idempotency design**: idempotency key strategy for every payment-mutating operation.
- **Ledger impact**: double-entry entries for each financial event, balance impact, and reconciliation test.
- **Provider integration safety**: webhook signature verification, event deduplication, settlement timing.
- **PCI DSS compliance**: cardholder data flow, tokenization confirmation, PAN exclusion from logs.
- **Audit trail requirements**: immutable ledger record requirements, retention period, admin action logging.
- **Reconciliation plan**: reconciliation frequency, matching criteria, alert thresholds for gaps.
- **Financial arithmetic**: decimal/fixed-point arithmetic confirmation, currency and rounding rules.
- **Block/pass decision** with required conditions for approval.

## Quality Gate
1. Payment state machine is complete with all invalid transitions tested and returning correct errors.
2. Every payment-mutating operation uses an idempotency key; duplicate operations are tested.
3. Entitlement is granted only after server-side confirmation (not frontend callback).
4. Ledger entries are immutable; no UPDATE on financial records; balance computed from SUM.
5. Double-entry invariant verified: every debit has a corresponding credit in the same amount.
6. Webhook signature verification is implemented; replay attack test passes.
7. Raw card data (PAN, CVV) is confirmed absent from application code, logs, and databases.
8. All financial arithmetic uses fixed-point or integer (cents) arithmetic — no floating-point.
9. Daily reconciliation between internal ledger and provider settlement report is implemented.
10. Financial records have documented retention period (jurisdiction-appropriate, typically 7 years).

## Handoff
- **security-privacy-gate** — for PCI DSS compliance, webhook signature, access control to payment data, and PAN exclusion from logs.
- **backend-change-builder** — for idempotency key implementation, payment state machine, and ledger entry creation.
- **integration-change-builder** — for payment provider webhook handling, retry policy, and settlement reconciliation.
- **quality-test-gate** — for payment state machine test coverage, duplicate charge tests, reconciliation gap tests.
- **reliability-observability-gate** — for payment success rate SLI, reconciliation gap alerting, and settlement monitoring.

## Completion Criteria
The financial change is approved when the payment state machine covers all invalid transitions, every payment-mutating operation has an idempotency key, entitlement is gated on server-side confirmation, ledger entries are immutable with double-entry correctness, webhook signatures are verified with replay protection, raw card data is confirmed absent from all application paths, financial arithmetic uses fixed-point representation, and daily reconciliation against provider settlement is implemented.
