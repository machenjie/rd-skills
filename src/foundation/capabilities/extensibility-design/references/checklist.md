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
