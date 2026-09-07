# Frontend Quality and Validation Evidence

Use this evidence-pattern Reference only for the named frontend-quality-and-validation-evidence decision.

## Evidence Contract

Record each loading, empty, success, error, validation, disabled, permission-denied, timeout, or partial state with its component or route, visible behavior, validator or test, artifact, result, proof, non-proof, and owner.

- Exercise public behavior through accessible queries; do not make private hooks, CSS selectors, snapshots, or mock counts the primary proof.
- Bind cache, render, bundle, Core Web Vitals, request fan-out, memory cleanup, reliability, and performance claims to measurement or an explicit not-run risk.
- Reject snapshot-only interactive proof and claims that a frontend merely "feels fast."

Return current evidence, validation plan, proof limits, and residual risk.
