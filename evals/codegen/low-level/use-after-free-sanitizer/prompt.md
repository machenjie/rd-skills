# Benchmark Prompt

## Task

Implement a focused change to repair a native memory ownership bug and prove the fix with sanitizer backed tests.

## Context

The starter repo represents a C compatible parser exposes buffers across an FFI boundary. In its initial state, the starter behavior frees a buffer while a caller can still read it through an exported pointer. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Buffer ownership is explicit across allocation, transfer, and release.
- Use after free is eliminated under address sanitizer.
- FFI callers receive a stable release contract.
- Regression tests cover normal parse, error parse, and double release denial.

## Constraints

- The API documents who owns every pointer and when it is valid.
- Tests run with sanitizer flags or an equivalent memory safety tool.
- Error paths release resources exactly once.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
