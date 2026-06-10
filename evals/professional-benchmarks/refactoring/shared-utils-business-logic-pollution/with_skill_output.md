Selected stage: refactoring.
Selected professional skill: ai-code-review-refactor.
Selected capabilities: implementation-structure-design, module-boundary-design, code-clarity-maintainability, refactoring.

Hidden risks: business logic pollution in shared/common/utils; unclear owner for tenant and invoice rules; hidden behavior change during refactor.
Inspected boundaries: current callers, owning domain module, shared utility policy, public behavior tests, and deletion path for duplicated code.
Reuse/placement rationale: tenant and invoice rules stay in an owning domain/service boundary; generic utilities are rejected because they would hide business ownership.
Evidence required: reuse ladder and rejected placement alternatives; owning module or domain boundary decision; behavior-preserving regression tests and deletion path.
Output obligations: severity-classified structure finding; reuse and placement rationale evidence; validation evidence for behavior preservation.
Validation command: not verified; fixture describes expected agent output only.
What evidence proves: placement is justified and behavior preservation is required.
What evidence does not prove: all callers have been scanned in a real repository.
Residual risk: one indirect caller may still need an integration test.
Next gate: quality-test-gate.
