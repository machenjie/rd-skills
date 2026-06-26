# Example Output

```markdown
## Input Validation Contract

mode_selected: identifier/object scope with validation error contract

boundaries_inspected:
- POST /accounts/{account_id}/invitations route, request DTO, invitation service, account repository, validator tests, and prior project memory about tenant-scoped invitations.
- Not inspected: mobile generated client and production telemetry; compatibility risk remains with API owner.

source_evidence:
- Route accepts `account_id`, `email`, and `role`.
- Service can query account membership by authenticated actor tenant.
- Existing test covers happy path only.

graph_memory_trajectory_judgment:
- Accepted: repository graph shows one invitation route and one service call path.
- Rejected: prior memory claimed frontend validation was sufficient; server validator was not present.
- Not verified: deployed mobile payloads.

input_sources:
- `account_id`: path parameter, untrusted client reference.
- `email`: request body, untrusted user input.
- `role`: request body, security-meaningful enum.

schema_constraints:
- `account_id`: UUID format, required.
- `email`: required string, trimmed, Unicode NFC normalized, max 254 chars, email grammar.
- `role`: enum `viewer`, `editor`, `billing_admin`.
- Unknown request fields: reject with `VALIDATION_UNKNOWN_FIELD`.

identifier_and_authority_checks:
- `account_id` must exist and belong to authenticated actor tenant.
- Actor must be account admin.
- `billing_admin` invite requires account owner approval.

error_contract:
- 400/422 validation problem with stable code, field path, and safe message.
- Wrong tenant returns 404-style safe denial.
- Response and logs do not echo full email for denied account scope and do not expose regex internals.

changed_validation_to_test_map:
- Invalid UUID -> 400.
- Oversized email -> 422.
- Unknown field `is_admin` -> 400.
- Invalid role -> 422.
- Wrong-tenant account id -> safe 404.
- `billing_admin` without owner approval -> 403 or domain-specific validation code per error catalog.

reuse_and_placement_rationale:
- Reuse existing request DTO and service-layer account lookup.
- Reject frontend-only validation and raw body mapping because direct API calls bypass the UI.

behavior_preservation:
- Existing valid viewer/editor invites remain accepted.
- New `billing_admin` branch is additive but gated by owner approval.

validation_evidence:
- Required before completion: DTO validator negative tests and service wrong-tenant test.

handoff_boundaries:
- Hand off public error code names to `error-code-design`.
- Hand off role/approval policy details to `permission-boundary-modeling`.

evidence_limits:
- Mobile generated client and production telemetry were not inspected.
```
