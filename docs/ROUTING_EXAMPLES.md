# Routing Examples

These examples show minimal sufficient routing. Add skills only when the change surface, risk, or missing information requires them.

## 1. Small Local Bug Fix

Request: "Fix a null label in one settings component."

- Level: L1.
- Professional path: `change-forge-router` only if classification is unclear, then `frontend-change-builder` or `ai-code-review-refactor`.
- Foundation capabilities: `regression-testing`, `frontend-testing` when the component has behavior worth covering.
- Domain extension: none.
- Gates: focused unit/component test or manual reproduction; no release gate unless deployment is requested.
- Evidence: changed file list, failing/passing reproduction, skipped checks.

## 2. Login API Change

Request: "Add a new login response field for MFA enrollment status."

- Level: L3, or L4 if clients are external or backwards compatibility is uncertain.
- Professional path: `change-intake-compiler`, `change-impact-analyzer`, `data-api-contract-changer`, `backend-change-builder`, `security-privacy-gate`, `quality-test-gate`, `change-documentation-gate`.
- Foundation capabilities: `api-contract-design`, `authentication-authorization`, `authentication-security`, `dto-schema-design`, `contract-testing`, `version-compatibility`.
- Domain extension: none unless the product domain adds extra constraints.
- Gates: backward-compatible schema, auth review, contract tests, client migration note.
- Evidence: API diff, tests, compatibility decision, docs update.

## 3. Frontend Form Change

Request: "Add validation and error states to a checkout address form."

- Level: L2 or L3 depending on checkout criticality.
- Professional path: `change-intake-compiler`, `experience-impact-modeler`, `frontend-change-builder`, `quality-test-gate`.
- Foundation capabilities: `form-validation-design`, `interaction-state-modeling`, `design-system-rules`, `frontend-api-integration`, `frontend-testing`.
- Domain extension: `payment-trading-extension` if payment authorization or settlement can be affected.
- Gates: accessible labels and errors, validation parity with API, regression coverage for edge cases.
- Evidence: screenshots or UI observations, tests, changed validation rules.

## 4. Database Migration With API Compatibility

Request: "Split `customer_name` into first and last name without breaking existing API clients."

- Level: L4, or L5 when production data volume, rollback, or compliance risk is high.
- Professional path: `change-intake-compiler`, `change-impact-analyzer`, `architecture-impact-reviewer`, `data-api-contract-changer`, `data-middleware-change-builder`, `backend-change-builder`, `quality-test-gate`, `reliability-observability-gate`, `delivery-release-gate`, `change-documentation-gate`.
- Foundation capabilities: `data-migration-design`, `relational-database`, `transaction-consistency`, `repository-persistence`, `api-contract-design`, `version-compatibility`, `integration-testing`, `release-rollback`.
- Domain extension: none unless product domain signals apply.
- Gates: expand-contract migration, backfill plan, read/write compatibility, rollback plan, monitoring.
- Evidence: migration script review, compatibility tests, deployment sequence, rollback note.

## 5. Web3, Payment, Or AI High-Risk Change

Request: "Use an AI agent to approve wallet-based subscription payments."

- Level: L5.
- Professional path: `change-intake-compiler`, `domain-impact-modeler`, `architecture-impact-reviewer`, `data-api-contract-changer`, `integration-change-builder`, `backend-change-builder`, `security-privacy-gate`, `reliability-observability-gate`, `quality-test-gate`, `delivery-release-gate`, `change-documentation-gate`, `ai-code-review-refactor`.
- Foundation capabilities: `threat-modeling`, `permission-boundary-modeling`, `secret-configuration-security`, `idempotency-retry-design`, `transaction-consistency`, `observability`, `contract-testing`, `release-rollback`.
- Domain extension: `web3-product-extension`, `payment-trading-extension`, and `ai-product-extension` when all three signals are real.
- Gates: explicit risk escalation, human approval, threat model, deterministic payment state machine, wallet/key boundary review, AI side-effect controls, rollback and audit trail.
- Evidence: approval record, threat model summary, test matrix, auditability notes, release blockers.
