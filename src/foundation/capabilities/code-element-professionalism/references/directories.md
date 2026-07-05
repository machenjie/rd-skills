# Directories

This is a bridge reference. Use it only when a directory-level default, initialization statement, or local file pattern exposes an element hazard.

## Bridge Signals

- Directory-level config/default files conflate missing, false, zero, empty, tenant-specific, and environment-specific values.
- Multiple files repeat the same unsafe sentinel, magic constant, hidden assignment, broad catch, or event-before-commit statement pattern.
- A directory initializer or index file performs side effects at import/load time.
- Local helper files hide element risks that belong to an owning module or service.

## Handoff

- Route directory boundaries, public facade, internal module graph, and file placement to `implementation-structure-design` or `module-boundary-design`.
- Route same-pattern scans and behavior-preserving cleanup to `refactoring` when multiple files need local element repairs.
- Route cross-boundary side effects to `data-side-effect-flow-tracing`.

