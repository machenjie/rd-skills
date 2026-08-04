# Language Idiom Enforcement Checklist

- Identify the selected language, repository-local conventions, and applicable standard-library and established ecosystem conventions.
- Review error handling, type modeling, resource ownership, and module boundaries.
- Check concurrency style and lifecycle management.
- Detect hallucinated APIs and copied patterns from other languages.
- Verify formatter, linter, and static checks.
- Document justified deviations.
- Link language-specific usage capability when applicable.

## Comment Syntax And Clarity Handoff

- When current repository or toolchain authority requires documentation for a changed public API, use its language-standard format: godoc, rustdoc, JSDoc, Javadoc/KDoc, Python docstrings, or the project C++ convention.
- Apply only repository-required public contract fields and examples; do not invent universal comment coverage from a generic style guide.
- Add class, object, or non-exported function comments only when current repository authority requires them and a non-obvious contract, invariant, compatibility, or operational reason remains after naming or extraction.
- Route whether naming, extraction, or a comment best exposes that semantic obligation to `code-clarity-maintainability`; this Skill owns language syntax and enforced public-surface form.
- Test names describe behavior; complex tests explain scenario, regression reason, edge case, or production bug; fixtures and golden files explain the contract they represent.
- Under current repository authority, inline comments preserve a non-obvious business, compatibility, state, concurrency, transaction, performance, external-system, security, fallback, or algorithmic reason.
- Reject or delete comments that repeat assignments, simple conditionals, framework mechanics, or every line of code, or that are stale, redundant, misleading, decorative, banners, or noise.
- Prefer renaming, extraction, or simplification before using a comment to explain confusing code.
