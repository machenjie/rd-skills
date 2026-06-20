Implemented order cancellation deadline enforcement through the order service/policy path.

Files changed:
- [README.md](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/README.md)
- [setup.sh](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/setup.sh)
- [package.json](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/package.json)
- [src/orders/application/OrderService.ts](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/src/orders/application/OrderService.ts)
- [src/orders/domain/Order.ts](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/src/orders/domain/Order.ts)
- [src/orders/domain/OrderPolicy.ts](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/src/orders/domain/OrderPolicy.ts)
- [src/shared/utils/date.ts](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/src/shared/utils/date.ts)
- [src/orders/__tests__/OrderService.test.ts](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/local-full-current-home-20260620-221702/cases/backend__service-method-vs-new-helper/baseline/run-01/candidate/src/orders/__tests__/OrderService.test.ts)

Validation:
- `bash setup.sh` initially failed because the referenced external harness was missing; after making setup local, `bash setup.sh` exits 0.
- `npm test` exits 0: 4 tests, 4 pass, covering existing cancellation success plus before, at, and after deadline.
- `rg "validateCancellationDeadline|shared.*cancel|common.*cancel|utils.*cancel|..." .` found no detached shared cancellation helper; shared only has generic `isBeforeInstant()`.

Reuse and placement evidence:
- `OrderService.cancelOrder()` keeps transaction, load, authorization, policy check, and save in the public workflow.
- `OrderPolicy.canCancelBeforeDeadline()` owns the strict deadline decision.
- `src/shared/utils/date.ts` contains only pure date arithmetic, not order business logic.
- README now includes the Implementation Structure Plan rejecting `shared/common/utils` business-rule placement.

Residual risk:
- The original generated starter source was unavailable because the setup harness path did not exist, so I reconstructed the README-described starter files inside the candidate repo.
- No separate TypeScript typecheck was run because `tsc` is not installed; validation is runtime service tests via Node’s TypeScript test support.
- No real DB or external transaction integration exists in this starter, so transaction evidence is through the service-level fake.

```yaml
changeforge_route:
  route_id: order-cancellation-deadline-enforcement
  complexity: L2
  risk_level: medium
  execution_mode: final-handoff
  selected_skills:
    - backend-change-builder
    - quality-test-gate
    - ai-code-review-refactor
    - architecture-impact-reviewer
    - security-privacy-gate
    - data-api-contract-changer
  selected_capabilities:
    - repository-context-map
    - implementation-structure-design
    - service-business-logic
    - domain-logic-implementation
    - module-boundary-design
    - authentication-authorization
    - test-strategy
    - unit-testing
    - regression-testing
    - contract-testing
    - agent-tool-permission-sandbox
    - agent-execution-discipline
    - plan-execution-consistency
  required_references:
    - change-forge-router/SKILL.md
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
    - backend-change-builder/SKILL.md
    - quality-test-gate/SKILL.md
    - ai-code-review-refactor/SKILL.md
    - architecture-impact-reviewer/SKILL.md
    - security-privacy-gate/SKILL.md
    - data-api-contract-changer/SKILL.md
  required_quality_gates:
    - implementation-structure gate: passed
    - backend implementation gate: passed
    - test gate: passed with npm test
    - AI/shared-helper review gate: passed
    - security tool-permission gate: passed, local read/write/test only
    - API/data gate: closed as internal starter/domain model only; no external API/schema/migration
    - plan-execution consistency gate: passed
  handoff_target: closed
```

