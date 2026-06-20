Implemented the refactor in the candidate repo.

**Files Changed**
- [orders/order.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/structure__object-method-encapsulation-placement/baseline/run-01/candidate/orders/order.py): `Order`, `CancellationWindow`, lifecycle/value behavior.
- [orders/cancellation_service.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/structure__object-method-encapsulation-placement/baseline/run-01/candidate/orders/cancellation_service.py): orchestration only.
- [orders/payment_adapter.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/structure__object-method-encapsulation-placement/baseline/run-01/candidate/orders/payment_adapter.py): provider refund boundary.
- [tests/orders/test_cancellation_service.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/structure__object-method-encapsulation-placement/baseline/run-01/candidate/tests/orders/test_cancellation_service.py): public behavior tests.
- [docs/order_cancellation_structure_plan.md](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/structure__object-method-encapsulation-placement/baseline/run-01/candidate/docs/order_cancellation_structure_plan.md): implementation structure plan, object candidates, placement rationale.

**Validation**
- `python3 -B -m unittest discover -s tests -t .` -> `Ran 6 tests`, `OK`.
- `python3 -B -m unittest tests.orders.test_cancellation_service` -> `Ran 6 tests`, `OK`.
- Boundary scan confirmed private helpers are not exported:
  `exported_private=[]` for service and adapter helpers.
- Import scan confirmed `orders/order.py` imports only stdlib modules.
- `python3 -m pytest --version` could not run: pytest is not installed.

**Placement Evidence**
- `CancellationWindow` owns timing invariants and deadline/refund-hold math.
- `Order` owns lifecycle state and `cancel`.
- `OrderCancellationService` keeps orchestration, clock use, and decision flow.
- Provider refund call remains private inside `payment_adapter`.
- Rejected helper-bag/shared-utils placement because the repo had no reusable code surface beyond the README-specified layout.

```yaml
changeforge_route:
  route_id: order-cancellation-encapsulation-refactor
  selected_skills:
    - domain-impact-modeler
    - backend-change-builder
    - integration-change-builder
    - quality-test-gate
    - security-privacy-gate
    - data-api-contract-changer
    - reliability-observability-gate
    - ai-code-review-refactor
  selected_capabilities:
    - implementation-structure-design
    - module-boundary-design
    - test-strategy
    - agent-tool-permission-sandbox
    - plan-execution-consistency
    - agent-execution-discipline
  required_quality_gates:
    - public behavior tests
    - private helper non-export check
    - domain/value no infrastructure import check
    - payment adapter side-effect boundary check
```

Residual risk: the original scattered helper source was absent from the starter copy, so this is a clean implementation matching the README/task contract rather than a literal move diff. Rollback is deleting the untracked `orders/`, `tests/`, and `docs/` additions; no tracked starter files were modified.