Selected stage: testing.
Selected professional skill: quality-test-gate.
Selected capabilities: unit-testing.

Hidden risks: over-mocked private helper hides behavior; private helper assertion freezes implementation; unit boundary not protected by observable assertions.

Inspected boundaries: `OrderService.cancelOrder`, refund-window rule, public cancellation result, emitted domain event, denied case, and order-domain fixture owner.

Evidence required: unit boundary and dependencies excluded; behavior-oriented assertions; mock boundary and fixture ownership.

Output obligations covered: unit boundary evidence; validation evidence for observable behavior; what evidence proves and does not prove; residual integration risk owner.

Validation command: `python3 -m pytest tests/orders/test_cancel_order.py` (not run in fixture; expected outcome is observable cancellation, denied, and refund-window assertions).
What evidence proves: the isolated order cancellation behavior is correct for the covered inputs.
What evidence does not prove: repository wiring, transaction behavior, browser flow, or external refund provider behavior.

Residual risk: integration wiring remains untested; owner: quality-test-gate.
Next gate: integration-testing if repository or transaction behavior changes.
