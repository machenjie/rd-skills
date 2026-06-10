Selected stage: refactoring.
Selected professional skill: ai-code-review-refactor.
Selected capabilities: refactoring, implementation-structure-design, code-clarity-maintainability, code-review.

Hidden risks: hidden behavior change during supposedly behavior-preserving refactor; public API or error semantics changed without evidence; deletion path not proven safe.

Inspected boundaries: callers of `OrderService.applyPromotion`, public return contract, exception mapping, promotion policy ownership, deleted helper references, imports, and behavior-preserving tests.

Evidence required: behavior preservation test evidence; public API and error semantics diff review; deletion path caller scan and rollback evidence.

Output obligations covered: behavior preservation evidence; compatibility statement; residual behavior-change risk owner.

Validation command: `python3 -m pytest tests/orders/test_promotion_policy.py` (not run in fixture; expected outcome is characterization coverage for null-return, empty-array, and validation-error branches).
What evidence proves: covered callers still observe the same return shape and exception semantics after the move.
What evidence does not prove: dynamic reflection paths, unscanned downstream packages, or performance side effects.

Residual risk: one indirect caller package still needs owner confirmation; owner: ai-code-review-refactor.
Next gate: quality-test-gate before merge.
