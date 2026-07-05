# Cpp Toolchain And ABI Patterns

Use this reference when C/C++ review depends on compiler flags, CMake/package-manager behavior, exported headers, symbol visibility, ABI/FFI compatibility, generated bindings, dependency scanning, or cross-platform release evidence.

## Toolchain And ABI Decision Map

| Surface | Required decision | Evidence | Escalate when |
| --- | --- | --- | --- |
| Language standard | C/C++ standard, allowed legacy exception, and target compiler support | Build preset or CI matrix naming standard and compilers | C++17 or older is used for new code without platform reason |
| Warning policy | Warnings-as-errors, extra warning set, and justified suppressions | Compiler command, config, or report path | Suppressions hide conversion, shadowing, lifetime, or non-virtual-dtor findings |
| Static analysis | clang-tidy/IWYU profile, enabled check families, suppression owner | Report path and exit code | Findings touch ownership, UB, security, or public headers |
| Sanitizer lanes | ASan, UBSan, TSan, MSan applicability and lane separation | CI job, command, report, and skipped-lane reason | TSan is skipped for threaded code or dependencies block MSan silently |
| Build system | Target-based CMake/Bazel ownership, presets, PUBLIC/PRIVATE/INTERFACE dependency direction | Build files, presets, and dependency graph | Global include/link flags or transitive includes decide behavior |
| Package manager | vcpkg/Conan manifest, lock/baseline, license/CVE/provenance scan | Manifest diff, OSV/CVE Binary Tool report | Native dependency adds parser/crypto/networking surface |
| Exported header | Source compatibility, binary compatibility, visibility, inline/template policy | Header diff, symbol list, `abi-dumper`/`abidiff` when available | Public structs/classes/vtables/exceptions change |
| FFI boundary | `extern "C"`, JNI/N-API/Python extension, calling convention, ownership, error translation | Boundary wrapper, generated diff, no-exception-across-boundary test | Exception, allocator, ownership, or thread attachment crosses language boundary |
| Cross-platform path | OS/compiler/architecture matrix, endian/alignment/path/encoding assumptions | Matrix result or explicit not-run targets | Behavior depends on Windows/Linux/macOS, ARM/x86, or compiler-specific extensions |

## ABI Compatibility Classes

- **Header-only/source-compatible:** consumers rebuild from source; still preserve names, templates, macros, and inline behavior or document migration.
- **Shared-library binary-compatible:** public layout, vtables, symbol names, calling convention, exception types, allocator ownership, and visibility remain compatible.
- **Breaking ABI:** public struct/class layout, virtual method order, exported function signature, exception boundary, or allocator ownership changes; require version bump, migration note, and rollback plan.
- **FFI-compatible:** C layout, ownership and deallocation API, error code/status representation, encoding, alignment, and thread attachment are explicit and tested at the foreign boundary.

## Review Shortcuts To Reject

- "It compiles locally" as proof for compiler, sanitizer, ABI, or platform compatibility.
- Using a unit test as ABI proof without symbol/layout diff or generated binding check.
- Letting C++ exceptions escape `extern "C"` or foreign runtimes.
- Public headers depending on transitive includes or global compile definitions.
- Package-manager update without lock/baseline, license, provenance, and vulnerability evidence.
- Suppressing clang-tidy, compiler warnings, sanitizer reports, or static-analysis findings without owner, scope, and expiration.

## Handoff Evidence Shape

```yaml
cpp_toolchain_abi_decision:
  language_standard: ""
  compiler_matrix:
    - compiler: ""
      version: ""
      status: ""
  build_system:
    source: ""
    dependency_direction: ""
    rejected_global_state: ""
  abi_policy:
    class: header_only | source_compatible | binary_compatible | breaking | ffi_compatible
    exported_symbols_or_headers: []
    versioning_decision: ""
  validation:
    - command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
