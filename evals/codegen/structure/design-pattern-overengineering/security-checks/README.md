# Security Checks

## Threat Surface

The simple discount rule is low security risk, but speculative public APIs can
create accidental extension points that bypass validation later.

## Required Checks

- Reject a public provider or registry that accepts unvalidated discount code.
- Reject hidden side effects in factories or strategy constructors.
- Verify public behavior tests still exercise the validated discount path.

## Rejection Cases

- Reject a public interface with no current consumer.
- Reject a factory that hides side effects.
- Reject a strategy registry that bypasses the owner module.
