# Code Clarity Maintainability Checklist

Use this checklist for concrete clarity reviews, split/merge decisions, comment cleanup, and test readability checks. Keep the answer bounded to the changed paths and load heavier references only when the risk signals require them.

- Name the public entry point, the normal path, and the first branch that obscures it.
- Separate validation, denial, retry, fallback, logging, mapping, mutation, and external I/O only when the separation makes side effects easier to see.
- Prefer guard clauses, named policy predicates, or direct extraction before introducing strategy, registry, inheritance, or configuration structures.
- For every repeated condition, boolean flag, `mode`, `kind`, magic string, or magic number, name the policy owner or route to signature review.
- For a long function, state whether it is a real orchestration boundary or a mixed-responsibility block that needs extraction.
- For every file split or merge, record owner boundary, files a maintainer must open, import/export impact, public/test boundary, and next-change location.
- Reject one-function files, trivial helper files, pass-through glue, and micro-file sprawl unless they protect a real independent boundary.
- Reject broad file merges that hide side effects, public behavior, dependency direction, or test ownership.
- Keep comments only for contract, invariant, compatibility, security, performance, fallback, external-system quirk, or regression context.
- Prefer behavior-named tests with public assertions; reject private helper assertions or mock-call-only proof unless the seam limitation is explicit.
- State the deletion path for temporary flags, compatibility branches, obsolete fallback code, wrappers, or deprecated APIs.
- Close with command/review evidence, what it proves, what it does not prove, freshness, and residual risk.
