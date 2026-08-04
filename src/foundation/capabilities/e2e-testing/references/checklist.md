# E2E Testing Checklist

- State the critical journey, role, tenant, starting state, deployed boundaries, and why lower-level proof is insufficient.
- Include triggered negative, recovery, version-skew, and permission branches rather than a universal journey catalog.
- Assert the user/business outcome, authoritative durable state, and forbidden side effects.
- Use semantic selectors and readiness signals with a bounded consequence-derived observation window.
- Own data, sessions, sandbox use, setup, and cleanup for success, failure, timeout, and cancellation.
- Diagnose flakes by signature; keep rerun and quarantine evidence separate from a passing result.
- Select environment and browser/device coverage from changed behavior, usage, support policy, and risk.
- Record the fresh command/result or planned proof, artifacts actually used, uncovered combinations, and residual owner.
