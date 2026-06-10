Selected stage: testing.
Selected professional skill: quality-test-gate.
Selected capabilities: e2e-testing, unit-testing.

Hidden risks: E2E test used for unit-level bug; slow browser test hides cheaper unit coverage; test layer selection inverted for local logic.

Inspected boundaries: currency formatter helper, checkout journey, browser fixture setup, flake surface, unit regression path, and any remaining user journey risk.

Evidence required: layer justification; unit-level regression evidence; E2E residual journey risk.

Output obligations covered: layer justification evidence; validation evidence for narrowest sufficient layer; what evidence proves and does not prove; residual journey risk owner.

Validation command: `npm test -- currency-format.test.ts` (not run in fixture; expected outcome is focused regression output for 1.005 rounding).
What evidence proves: the local formatter recurrence path is covered at the cheapest deterministic layer.
What evidence does not prove: checkout browser wiring, payment confirmation, or all locales.

Residual risk: checkout display may still need one existing journey smoke test; owner: quality-test-gate.
Next gate: e2e-testing only if the assembled checkout journey itself changed.
