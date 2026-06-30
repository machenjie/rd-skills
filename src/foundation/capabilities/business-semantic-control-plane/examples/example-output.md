# Example Output

```yaml
business_semantic_control_record:
  mode_selected: rule authority mapping
  stage_fit: DDD plus testing
  triggers:
    - hidden SQL rule
    - missing business golden case
  scope: order cancellation rule for marketplace orders only
  objects:
    - object_id: OBJ.ORDER
      name: Order
      evidence_class: FACT
      source: current_source
  rules:
    - rule_id: ORDER.CANCEL.AFTER_SHIP_DENIED
      owner: Order aggregate
      enforcement_layer: domain
      reason_codes: [ORDER_ALREADY_SHIPPED]
      tests: [tests/domain/test_order_cancel.py::test_shipped_order_cannot_cancel]
  workflows:
    - workflow_id: ORDER_LIFECYCLE
      allowed: [PENDING->CANCELLED]
      forbidden: [SHIPPED->CANCELLED]
  memory:
    accepted: []
    rejected: []
    stale: [mem_prior_cancel_rule]
    not_verified: []
  graph:
    selected_edges: [rule_enforced_by]
    evidence_limit: graph selects files, source confirms facts
  golden_cases:
    - shipped-order-cannot-cancel
  validation:
    - tests/domain/test_order_cancel.py::test_shipped_order_cannot_cancel
  selected_references:
    - references/capabilities/135-business-semantic-control-plane.md
  skipped_references:
    - payment-trading-extension: no payment/refund behavior changed
  evidence_limits:
    - no owner review was available
  residual_risk:
    - admin support tool writer path not inspected
  handoff: quality-test-gate for golden case coverage
```
