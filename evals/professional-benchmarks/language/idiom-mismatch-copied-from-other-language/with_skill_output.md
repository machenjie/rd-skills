Selected stage: code-review.
Selected professional skill: backend-change-builder.
Selected capabilities: language-idiom-enforcement.

Hidden risks: idiom mismatch copied from other language; invented abstraction ignores repository convention; framework-incorrect naming or file layout.

Inspected boundaries: TypeScript service module layout, `OrderPolicy` deadline method, DTO naming, import path convention, test file convention, and framework handler naming.

Evidence required: repository naming and module convention evidence; formatter linter typecheck evidence; existing policy boundary inspected.

Output obligations covered: language idiom and repository convention evidence; anti-pattern rejected with replacement boundary; what evidence proves and does not prove; residual idiom risk owner.

Validation command: `npm run lint && npm run typecheck && npm test -- order-deadline` (not run in fixture; expected outcome is pass after replacing the Java-style abstraction with the repository's TypeScript module pattern).
What evidence proves: the reviewed surface follows local TypeScript naming, module placement, and policy-boundary convention.
What evidence does not prove: all repository naming rules, unrelated framework handlers, or runtime performance.

Residual risk: naming choices in sibling deadline flows still need same-pattern scan; owner: backend team maintainer.
Next gate: quality-test-gate after the policy-boundary unit test is attached.
