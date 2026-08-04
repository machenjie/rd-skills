# Generator And Plugin Contracts

**Load when:** Generated authority, clean bootstrap, compiler protocol, host API, diagnostics, fixes, or version compatibility can change the decision.

**Do not load when:** No repository generator or compiler, linter, or formatter plugin behavior changes.

**Required by:** `task-agent`

**Required output:** `boundary-decision`, `selected-approach`, `proof-limit`

Official sources were accessed on 2026-07-26.

## One Decision

Select one generator or plugin contract that rebuilds from authoritative inputs and remains compatible with the supported consumer set.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Editable authority | Name schemas, templates, source, generator code, flags, versions, and the sole editable owner | Generated output receives a manual fix that regeneration erases |
| Bootstrap graph | Trace how a clean checkout obtains or builds the generator before generated inputs are needed | The generator requires its own absent or stale output |
| Input identity | Declare files, transitive data, toolchain, plugin protocol, options, locale, ordering, and platform facts | Equal declared inputs produce different output |
| Output contract | Define destinations, ownership markers, stable ordering, formatting, stale-file deletion, and partial-write recovery | Old or half-written output remains consumer-visible |
| Plugin compatibility | Bind host API, ABI or protocol, supported versions, loading mode, option schema, and rejection behavior | Unit tests pass while the supported host refuses or misloads the plugin |
| Diagnostics and fixes | Preserve stable rule identity, location, severity, message contract, fix applicability, and idempotence | A fix corrupts syntax, changes semantics, or oscillates on rerun |
| Drift evidence | Regenerate from a clean state and compare semantic or byte output according to repository policy | Generation succeeds but checked-in or packaged output differs |

## Decision Rules

- Make generation deterministic before relying on a drift check.
- Break bootstrap cycles with an existing trusted bootstrap artifact or an independently buildable minimal stage.
- Reject silent host-version fallback.
- Exercise plugin loading through the real supported host boundary.
- Keep source-to-output provenance visible without embedding secrets or machine-local paths.

## Primary Sources

- [Go code generation](https://go.dev/blog/generate)
- [Protocol Buffers compiler plugin API](https://protobuf.dev/reference/cpp/api-docs/google.protobuf.compiler.plugin/)
- [LLVM pass plugins](https://llvm.org/docs/WritingAnLLVMNewPMPass.html)
- [Clang plugins](https://clang.llvm.org/docs/ClangPlugins.html)
- [ESLint custom rules](https://eslint.org/docs/latest/extend/custom-rules)
- [ESLint plugins](https://eslint.org/docs/latest/extend/plugins)
- [Prettier plugins](https://prettier.io/docs/plugins)

## Proof Limits

These rolling pages do not establish repository tool versions, supported host ranges, bootstrap availability, deterministic output, diagnostic compatibility, or packaged plugin loading. Validate the selected versions through current repository entrypoints and representative consumers.
