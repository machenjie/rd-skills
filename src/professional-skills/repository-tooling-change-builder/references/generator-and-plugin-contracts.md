# Generator And Plugin Contracts

**Load when:** Generated authority, clean bootstrap, compiler protocol, host API, diagnostics, fixes, or version compatibility can change the decision.

**Do not load when:** No repository generator or compiler, linter, or formatter plugin behavior changes.

**Required by:** `task-agent`

**Required output:** `boundary-decision`, `selected-approach`, `proof-limit`

Sources accessed 2026-07-26.

## Decision Rules

- Name schemas, templates, source, generator code, flags, versions, and the sole editable owner.
- Prove a clean checkout can obtain or build the generator without its own absent output.
- Break bootstrap cycles only with an existing trusted artifact or independently buildable stage.
- Include transitive data, toolchain, protocol, options, locale, order, and platform in input identity.
- Require deterministic output for equal declared inputs.
- Define destinations, ownership markers, stable order and format, stale deletion, and partial-write recovery.
- Regenerate cleanly and compare semantic or byte output under repository policy.
- Bind plugin host API, ABI/protocol, versions, loading, options, and rejection.
- Reject silent fallback.
- Preserve diagnostic identity, location, severity, message, fix applicability, and idempotence.
- Test the real host.
- Keep source-to-output provenance free of secrets and machine-local paths.

## Primary Sources

- [Go](https://go.dev/blog/generate); [Protobuf](https://protobuf.dev/reference/cpp/api-docs/google.protobuf.compiler.plugin/); [LLVM](https://llvm.org/docs/WritingAnLLVMNewPMPass.html); [Clang](https://clang.llvm.org/docs/ClangPlugins.html); [ESLint rules](https://eslint.org/docs/latest/extend/custom-rules), [plugins](https://eslint.org/docs/latest/extend/plugins); [Prettier](https://prettier.io/docs/plugins).

## Proof Limits

Sources do not prove repository versions, supported hosts, bootstrap, deterministic output, diagnostics, or packaged loading. Validate selected versions through current entrypoints and consumers.
