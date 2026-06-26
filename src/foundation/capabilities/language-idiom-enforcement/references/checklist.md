# Language Idiom Enforcement Checklist

- Identify the selected language and repository-local conventions.
- Review error handling, type modeling, resource ownership, and module boundaries.
- Check concurrency style and lifecycle management.
- Prefer standard library and established ecosystem conventions.
- Detect hallucinated APIs and copied patterns from other languages.
- Verify formatter, linter, and static checks.
- Document justified deviations.
- Link language-specific usage capability when applicable.

## Comment Quality Checklist

- Public/exported APIs use the language-standard doc format: godoc starts with the exported identifier; Rust uses rustdoc `///`; TypeScript uses JSDoc; Java/Kotlin use Javadoc/KDoc; Python uses docstrings; C++ follows project Doxygen/local convention.
- Public comments state behavior, parameter contracts, return value, error/exception/result behavior, side effects, concurrency expectations, and examples for non-trivial APIs.
- Class/object comments are required when the type owns state, lifecycle, invariants, external resources, concurrency, transactions, or domain rules.
- Non-exported function comments are required only when the function is reused across files, encodes a business rule, handles compatibility, performs retries, has concurrency behavior, mutates persistent state, or has surprising edge cases.
- Test names describe behavior; complex tests explain scenario, regression reason, edge case, or production bug; fixtures and golden files explain the contract they represent.
- Inline comments explain why: business rule authority, compatibility branch, state transition, locking reason, idempotency/retry decision, transaction boundary, performance tradeoff, external API quirk, security validation, fallback, or non-obvious algorithm.
- Reject comments that repeat assignments, simple conditionals, framework mechanics, or every line of code.
- Prefer renaming, extraction, or simplification before using a comment to explain confusing code.
- Delete stale, redundant, misleading, decorative, banner, or noise comments.
