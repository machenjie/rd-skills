# Extensibility Design Checklist

- Name the known variation that requires an extension point.
- Define invariant behavior that extensions cannot change.
- Define extension contract, inputs, outputs, errors, and lifecycle.
- Define owner, allowed implementers, and review process.
- Define validation, authorization, audit, and security constraints.
- Define observability for extension execution and failure.
- Define compatibility and deprecation policy.
- Limit configuration combinations and test the supported matrix.
- Reject speculative abstraction when current variation is insufficient.
- Record current source, graph, generated artifact, prior-task evidence, and execution evidence freshness.
- For each extension point, map variation proof, owner, and compatibility validation.
- Add invariant, security, failure, or performance tests only when those risks are triggered.
- State unverified risk and the recommended next step.
- State what the extensibility plan does not prove, including uninspected implementers, stale roadmap claims, production traffic, and unavailable sandbox evidence.
