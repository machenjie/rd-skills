Selected stage: code-review.
Selected professional skill: frontend-change-builder.
Selected capabilities: typescript-professional-usage.

Hidden risks: TypeScript any at API boundary; runtime validation missing for external data; nullable state hidden by cast.

Inspected boundaries: fetch response, runtime schema, nullable status state, generated client or DTO type, async error path, and UI error state.

Evidence required: runtime schema validation evidence; type boundary and nullable state evidence; typecheck or generated client validation.

Output obligations covered: TypeScript type boundary evidence; validation evidence for runtime schema; what evidence proves and does not prove; residual API boundary risk owner.

Validation command: `npm run typecheck && npm test -- accounts-response-schema.test.ts` (not run in fixture; expected outcome is runtime schema and nullable-state test output).
What evidence proves: the inspected API response is validated at runtime before TypeScript code trusts it.
What evidence does not prove: production API behavior for all consumers, browser matrix, or downstream SDK compatibility.

Residual risk: backend contract drift still needs contract-testing; owner: data-api-contract-changer.
Next gate: contract-testing if the API schema changed.
