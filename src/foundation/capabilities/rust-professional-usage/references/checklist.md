# Rust Professional Usage Checklist

- Model ownership and lifetimes instead of cloning to escape design pressure.
- Use `Result` and typed errors across recoverable boundaries.
- Avoid panic across library or FFI boundaries.
- Justify trait abstractions with real variation.
- Make async runtime choice explicit.
- Document every `unsafe` safety invariant.
- Run fmt, clippy, tests, and relevant fuzz/property checks.
- Review Cargo dependencies and feature flags.
