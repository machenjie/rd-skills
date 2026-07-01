# Cpp Professional Usage Checklist

## Source And Boundary

- Identify changed `.c`, `.cc`, `.cpp`, `.h`, `.hpp`, generated binding, build, package, and exported-header paths.
- Classify mode: ownership/lifetime, UB/bounds, ABI/FFI, concurrency/atomics, toolchain/portability, or mixed native review.
- Record repository graph, project memory, prior report, and execution-trajectory claims accepted, rejected, stale, or not verified.

## Native Safety

- Use RAII for every owned resource; map allocation/acquisition, owner, move/copy policy, deleter, and cleanup-on-error path.
- Remove or block undefined behavior: signed overflow, out-of-bounds access, strict aliasing, invalid alignment, null dereference, vptr misuse, uninitialized read, data race.
- Avoid raw owning pointers unless justified, contained, and covered by owner/deleter evidence; prefer stack, `std::unique_ptr`, or scoped handle wrappers.
- Document thread safety, lock order, callback lifetime, cancellation behavior, and memory ordering where relevant.
- Review parser, packet, file, C-string, and size-calculation code against untrusted or variable-length input with sanitizer/fuzz evidence.

## Toolchain, ABI, And Validation

- State ABI compatibility policy for public/native boundaries, exported headers, virtual classes, `extern "C"`, JNI/N-API/Python extensions, and generated bindings.
- Keep exception or error-code model consistent; catch and translate exceptions before FFI/ABI boundaries.
- Review build flags, CMake/Bazel target ownership, CMake presets, compiler matrix, package-manager manifests, target platforms, and native dependencies.
- Run or explicitly disclose ASan, UBSan, TSan, MSan, clang-tidy/IWYU, fuzz, stress, package CVE, ABI diff, and benchmark checks proportional to the touched risk.
- Map each changed native path to command, exit code or not-run status, report/artifact path, what evidence proves, what it does not prove, residual risk, owner, and next gate.
