# Fully Dressed Use Case Template

Load this reference when drafting a complete actor-goal use case, reviewing an output for professional completeness, or converting a goal-level requirement into an acceptance-testable behavioral contract. Do not load it for pure routing decisions, minor wording cleanup, or cases where the `SKILL.md` output contract and checklist are sufficient.

```markdown
Use Case ID: UC-014
Use Case Name: Customer Subscribes to Pro Plan
Primary Actor: Customer (authenticated)
Secondary Actors: Payment Gateway (Stripe), Email Service
Goal: Customer pays for and activates a Pro subscription that gives access to Pro features
Scope: Subscription Management bounded context

Stakeholder Interests:
  - Customer: wants to pay once and gain access immediately
  - Business: wants payment confirmed before granting access
  - Compliance: wants payment record retained for 7 years

Preconditions:
  - Customer is authenticated and email-verified
  - Customer does not already have an active Pro subscription
  - Pro plan exists and is available for purchase (not discontinued)
  - Payment method is on file OR customer provides one during the flow

Trigger: Customer clicks "Upgrade to Pro" and confirms the purchase

Main Success Path:
  1. System presents the Pro plan with price, features, and billing cycle
  2. Customer confirms payment with existing payment method (or adds new one)
  3. System creates a pending subscription record (state: PENDING)
  4. System charges the customer's payment method via Payment Gateway
  5. Payment Gateway returns success with transaction ID
  6. System transitions subscription to ACTIVE state; grants Pro entitlements
  7. System publishes subscription.activated event
  8. Email Service sends activation confirmation to customer

Alternate Paths:
  A. Customer adds a new payment method (at step 2):
     A1. Customer enters card details; system tokenizes via Payment Gateway
     A2. Token stored; flow continues at step 3
  B. Customer applies a discount coupon (at step 2):
     B1. System validates coupon (CouponValidationRule-009)
     B2. Price adjusted; customer confirms adjusted price; flow continues at step 3

Failure Paths:
  F1. Payment gateway returns DECLINED:
      - Subscription record moved to FAILED state
      - Customer notified with decline reason (per PaymentDeclineMessageRule-003)
      - Customer offered option to update payment method and retry
      - Retry allowed up to 3 times within 24 hours
  F2. Payment gateway timeout (> 10s):
      - Subscription record remains in PENDING state
      - Background job polls transaction status every 60s for up to 30min
      - If resolved: proceed as main path step 5-8
      - If unresolved after 30min: subscription moved to FAILED; support alert triggered
  F3. Email service unavailable:
      - Subscription activation completes; entitlements granted (not blocked by email)
      - Email delivery retried by Email Service with exponential backoff
      - Not a failure exit; email is a best-effort side effect

Postconditions (Success):
  - Subscription record exists in ACTIVE state for customer/plan combination
  - Pro entitlements are active (checked on every authenticated request)
  - Payment record exists with transaction ID and amount
  - subscription.activated event is published to billing topic
  - Activation email delivered or queued for delivery

Postconditions (Failure F1):
  - Subscription record exists in FAILED state
  - No payment charge has been applied
  - Customer can retry with new payment method

Business Rules Referenced:
  - CouponValidationRule-009
  - PaymentDeclineMessageRule-003
  - SubscriptionUniquenessRule-001 (only one active Pro subscription per customer)

Acceptance Trace: AC-042, AC-043, AC-044, AC-045 (failure paths)
```
