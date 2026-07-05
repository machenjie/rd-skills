# Example Output

```markdown
## Service Split Assessment

mode_selected:
- Split justification and boundary readiness.

decision:
- Deferred; strengthen module boundary and data contract first.

boundaries_inspected:
- Invoice module, checkout caller, invoice/order tables, planned API contract, deploy pipeline, observability, and release path.

proposed_boundary:
- Invoice generation service would own invoice creation and PDF rendering.

split_force_scorecard:
- Independent scaling: credible but not current.
- Independent deployment: not possible because checkout and invoicing still release together.
- Fault isolation: useful, but retry and reconciliation are not designed.
- Team ownership: same team owns both sides.
- Simpler alternative: in-process invoice module with public facade.

readiness_matrix:
- Shared invoice and order tables.
- No stable invoice API contract.
- No degraded checkout behavior if invoice generation is unavailable.
- No consumer-driven contract test in CI.

validation_evidence:
- Not verified by executable command yet; assessment is design-stage only.

next_gate:
- `module-boundary-design` for in-process boundary, then `api-contract-design` and `transaction-consistency` before reassessing extraction.

residual_risk:
- Current evidence does not prove production latency, unknown consumers, or data migration reversibility.
```
