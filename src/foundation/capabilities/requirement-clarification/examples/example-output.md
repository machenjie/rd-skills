# Example Output

```markdown
## Clarification Record

mode_selected: authority decision gap with evidence freshness check

request_summary:
Exclude accounts closed before the selected reporting period from the account export.

boundaries_inspected:
- Request ticket and finance comment thread.
- Export route and export query.
- Existing export tests.
- Project memory note claiming inactive accounts are excluded.
- Not inspected: production export telemetry and downstream finance reconciliation job.

source_evidence:
- Verified: current export includes inactive accounts when they match the report filter.
- Verified: request asks to exclude accounts closed before the selected reporting period.
- Stakeholder claim: product says inactive accounts are not needed in ordinary exports.

graph_memory_trajectory_judgment:
- Rejected: project memory claim that inactive accounts are already excluded; current query includes them.
- Not verified: downstream reconciliation dependence on row count.

blocking_unknowns:
- BU1: Must closed accounts remain visible for regulated audit exports?
  - Category: compliance/data retention
  - Owner: compliance owner
  - Decision needed: include, exclude, or add export mode split
  - Why blocking: answer changes data visibility and retention behavior
  - Downstream gate: security-privacy-gate or data-api-contract-changer
- BU2: Does finance reconciliation depend on current row counts?
  - Category: external consumer/compatibility
  - Owner: finance systems owner
  - Decision needed: compatible change, versioned export, or coordinated rollout
  - Why blocking: answer changes consumer contract
  - Downstream gate: consumer-impact-analysis

non_blocking_unknowns:
- NU1: Final filter label text.
  - Safe default: use existing copy key with placeholder text.
  - Isolation: i18n string only; no API or CSV column name depends on it.
  - Follow-up owner: product/UX.
  - Validation: copy key review before release.

safe_engineering_assumptions:
- Existing export permissions remain unchanged; this change introduces no new actor or resource.

explicit_stakeholder_assumptions:
- Product says ordinary exports do not need inactive accounts; not verified against compliance exports.

unsafe_assumptions_rejected:
- Not assuming inactive accounts can be removed from all exports without compliance approval.
- Not assuming finance reconciliation ignores row count changes.

proceed_block_decision:
- Status: PARTIAL PROCEED.
- Can implement now: read-only investigation and tests documenting current behavior.
- Must wait: behavior-changing query, API/export contract update, and release plan.
- Forbidden artifacts: no new export mode, CSV column, feature flag, migration, or hidden filter until BU1/BU2 are resolved.

changed_clarification_to_validation_map:
- BU1 -> compliance owner response and privacy/data-retention review.
- BU2 -> finance owner response and consumer compatibility check.
- NU1 -> copy key review only.
- Memory rejection -> current query inspection recorded in ticket.

handoff_boundaries:
- Hand off to requirement-structuring after BU1 and BU2 are resolved.
- Hand off to data-api-contract-changer if export contract changes.

evidence_limits:
- Production telemetry and reconciliation job behavior were not inspected; finance owner owns that residual risk.
```
