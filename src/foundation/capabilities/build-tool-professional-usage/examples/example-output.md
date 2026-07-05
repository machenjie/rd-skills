# Example Output

## Input Scenario

A Bazel build fails in CI after adding generated gRPC code. It passes locally because another target exposes the protobuf runtime transitively.

## Selected Capability

`build-tool-professional-usage`

## Decision Record

- Build surface: Bazel Java target `//services/user:user_service`.
- Graph boundary: generated sources from `user.proto`; protobuf runtime was used but not declared by the consuming target.
- Decision: add the direct dependency to the target and keep generated output derived from `user.proto`.
- Rejected shortcut: disabling strict deps would hide the graph defect and make remote execution unreliable.

## Evidence Checklist

- BUILD file and proto generator config inspected.
- Direct dependency declared instead of relying on transitive exposure.
- Generated output policy recorded.
- Affected target and consumer tests selected.
- Remote-cache nondeterminism risk not introduced.

## Validation Commands

```
bazel build //services/user:user_service --strict_java_deps=error
bazel test //services/user:all
bazel run //tools:check_proto_drift
```

## Residual Risk

Remote execution was not run in this workspace. Owner: build maintainer. Follow-up trigger: CI remote-execution failure.

## Handoff Summary

Fixed the declared build graph rather than weakening strict-dependency enforcement. Generated output remains derived from the proto source and is covered by drift validation.
